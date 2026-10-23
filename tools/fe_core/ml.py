# -*- coding: utf-8 -*-
"""ML の土台（2026-10-21・S04 用）。特徴量は OHLCV の族だけ。モデルは呼び出し側が選ぶ（リッジは numpy、勾配ブースティングは sklearn を遅延 import）。
原則: 目的変数は必ず未来（t+1 以降）、特徴量は t まで。ウォークフォワードは学習窓の終わりと評価窓の始まりの間に embargo を置く。試行は数える。"""
import itertools
import json
import os
import numpy as np
import pandas as pd

FEATURE_FAMILIES = ("mom", "vol", "range", "dow", "xsec")


def make_features(df, mom_L=(5, 20, 60, 120, 250), vol_W=(20, 60), range_N=(20, 60), dow=True):
    """1 銘柄の OHLCV（load_d1 の DataFrame）から、t までの情報だけで作る特徴量の表。
    使う場面: S04 の全案。族（mom/vol/range/dow）の外の特徴量はここに足してから使う（CATALOG に載る）
    入力: df: time/open/high/low/close/ret を持つ DataFrame、各族の窓
    返り値: DataFrame（index=time）。列名は <族>_<窓>。NaN は先頭の窓ぶんだけ
    禁止: 未来の値（shift(-k)）を使わない。終値以外の当日値（high/low）は t の足が確定した後なので使ってよい
    段階: 特徴量
    """
    c = df["close"].astype(float); r = df["ret"].astype(float); out = {}
    for L in mom_L:
        out[f"mom_{L}"] = c / c.shift(L) - 1.0
    for W in vol_W:
        out[f"vol_{W}"] = r.rolling(W).std()
    for N in range_N:
        hi = df["high"].rolling(N).max(); lo = df["low"].rolling(N).min()
        out[f"range_{N}"] = (c - lo) / (hi - lo).replace(0, np.nan)
    if dow:
        d = pd.to_datetime(df["time"]).dt.weekday
        for k in range(5):
            out[f"dow_{k}"] = (d == k).astype(float)
    X = pd.DataFrame(out); X.index = pd.to_datetime(df["time"]); X.index.name = "time"
    # ボラで正規化したモメンタム（単位を銘柄間で揃える）
    for L in mom_L:
        X[f"momz_{L}"] = X[f"mom_{L}"] / (X[f"vol_{vol_W[-1]}"] * np.sqrt(L)).replace(0, np.nan)
    return X


def make_target(df, k=5, kind="ret"):
    """目的変数: t の終値から t+k の終値までのリターン（比）または符号。
    使う場面: 方向予測（S04c）・メタラベリング（S04a。signal と掛ける）
    入力: df、k: 先の本数、kind: "ret" | "sign"
    返り値: Series（index=time）。末尾 k 本は NaN
    禁止: k=1 以外で日次に並べると重なり（overlap）があるので、評価の t 値は nw_t か非重複で
    段階: 目的変数
    """
    c = df["close"].astype(float); y = c.shift(-k) / c - 1.0
    y.index = pd.to_datetime(df["time"])
    return np.sign(y) if kind == "sign" else y


def meta_label(df, signal, k=5):
    """メタラベル: 合図 signal（±1、t で決めたもの）に乗ったときの t→t+k の損益が正なら 1、負なら 0。合図 0 の行は NaN。
    使う場面: S04a。モデルは「乗るか・規模」を学び、方向は合図に従う
    入力: df、signal: 長さ n の ±1/0、k
    返り値: Series（index=time）
    禁止: signal を未来で作らない（tsmom_pos はそのままで可）
    段階: 目的変数
    """
    y = make_target(df, k, "ret") * np.asarray(signal, float)
    lab = (y > 0).astype(float); lab[np.asarray(signal) == 0] = np.nan; lab[y.isna()] = np.nan
    return lab


def panel(frames):
    """銘柄ごとの (X, y) を縦に積む。列 sym を足す。
    使う場面: 多銘柄プール学習（S04c）
    入力: frames: {sym: (X DataFrame, y Series)}
    返り値: (X_all, y_all, meta DataFrame[time, sym])
    禁止: 銘柄ごとの標準化を全期間で行わない（未来を混ぜる）。必要なら学習窓の中で
    段階: 特徴量
    """
    Xs, ys, ms = [], [], []
    for s, (X, y) in frames.items():
        ok = X.notna().all(axis=1) & y.notna()
        Xs.append(X[ok]); ys.append(y[ok]); ms.append(pd.DataFrame({"time": X.index[ok], "sym": s}))
    return pd.concat(Xs), pd.concat(ys), pd.concat(ms, ignore_index=True)


def walk_forward(times, train_years=6, test_years=1, embargo_days=10, start_year=None, end=None):
    """年次ウォークフォワードの (学習 mask, 評価 mask) の列。学習窓は転がす（固定長）。
    使う場面: すべての ML 案。評価は常に未来側
    入力: times: 各行の時刻（DatetimeIndex か Series）、学習年数、評価年数、embargo（学習の終わりと評価の始まりの間に空ける日数。目的変数の k 以上）、start_year、end（封印の始まり。既定 2024-07-01 より前だけ）
    返り値: list of (train_mask, test_mask, test_year)
    禁止: 評価窓を封印（2024-07〜）に入れない。embargo を k 未満にしない
    段階: 分割
    """
    t = pd.to_datetime(pd.Series(np.asarray(times))); end = pd.Timestamp(end or "2024-07-01")
    y0 = start_year or (t.min().year + train_years); out = []
    for ty in range(y0, end.year + 1):
        tr0 = pd.Timestamp(f"{ty - train_years}-01-01"); tr1 = pd.Timestamp(f"{ty}-01-01") - pd.Timedelta(days=embargo_days)
        te0 = pd.Timestamp(f"{ty}-01-01"); te1 = min(pd.Timestamp(f"{ty + test_years}-01-01"), end)
        if te0 >= end: break
        tr = (t >= tr0) & (t < tr1); te = (t >= te0) & (t < te1)
        if tr.sum() > 0 and te.sum() > 0: out.append((tr.to_numpy(), te.to_numpy(), ty))
    return out


def ridge_fit_predict(Xtr, ytr, Xte, alpha=1.0):
    """リッジ回帰（numpy だけ）。学習窓の平均・標準偏差で標準化してから当てはめ、評価窓にも同じ変換。
    使う場面: ML の最初の 1 本。線形で消える信号は非線形でも大抵消える
    入力: 配列、alpha
    返り値: 評価窓の予測（1 次元配列）
    禁止: 標準化を全期間で行わない
    段階: モデル
    """
    Xtr = np.asarray(Xtr, float); Xte = np.asarray(Xte, float); ytr = np.asarray(ytr, float)
    mu = Xtr.mean(0); sd = Xtr.std(0); sd[sd == 0] = 1.0
    A = (Xtr - mu) / sd; B = (Xte - mu) / sd
    A1 = np.c_[np.ones(len(A)), A]; B1 = np.c_[np.ones(len(B)), B]
    I = np.eye(A1.shape[1]); I[0, 0] = 0
    w = np.linalg.solve(A1.T @ A1 + alpha * I, A1.T @ ytr)
    return B1 @ w


def gbm_fit_predict(Xtr, ytr, Xte, classify=False, **kw):
    """勾配ブースティング（sklearn の HistGradientBoosting。無ければ ImportError）。既定は浅く・少なく。
    使う場面: リッジの後。パラメータは格子に入れて数える
    入力: 配列、classify: 分類か、kw: max_depth/learning_rate/max_iter など
    返り値: 評価窓の予測（回帰は値、分類は正クラス確率）
    禁止: 格子を事前宣言せずに増やさない
    段階: モデル
    """
    from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
    p = dict(max_depth=3, learning_rate=0.05, max_iter=200, l2_regularization=1.0, random_state=0); p.update(kw)
    if classify:
        m = HistGradientBoostingClassifier(**p).fit(Xtr, ytr); return m.predict_proba(Xte)[:, 1]
    m = HistGradientBoostingRegressor(**p).fit(Xtr, ytr); return m.predict(Xte)


def pbo_cscv(M, S=8):
    """CSCV の過剰適合確率 PBO。M: (T, N) 日次損益の行列（N 通りの試行）。S ブロックに切り、半分の組合せで IS 最良が OS で中央値未満になる割合。
    使う場面: 1 つの ML 案の格子（N 通り）全体に対して必ず 1 回
    入力: M、S（偶数）
    返り値: dict(pbo, n_combos, N, T)
    禁止: N=1 で呼ばない（格子が 1 なら PBO は定義されない。試行数 1 と記録する）
    段階: 多重比較
    """
    M = np.asarray(M, float); T, N = M.shape
    if N < 2: return dict(pbo=float("nan"), n_combos=0, N=int(N), T=int(T))
    bounds = np.linspace(0, T, S + 1, dtype=int); blocks = [M[bounds[i]:bounds[i + 1]] for i in range(S)]
    def sharpe(x): m = x.mean(0); s = x.std(0, ddof=1); s[s == 0] = np.nan; return m / s
    worse = 0; n = 0
    for cb in itertools.combinations(range(S), S // 2):
        IS = np.vstack([blocks[i] for i in cb]); OS = np.vstack([blocks[i] for i in range(S) if i not in cb])
        si = sharpe(IS); so = sharpe(OS)
        if not np.isfinite(si).any(): continue
        best = int(np.nanargmax(si)); rank = (np.nansum(so < so[best])) / max(1, np.isfinite(so).sum() - 1)
        worse += (rank < 0.5); n += 1
    return dict(pbo=worse / n if n else float("nan"), n_combos=int(n), N=int(N), T=int(T))


class TrialLog:
    """試行の記録。格子の 1 点＝1 試行。上限を超えたら raise（新しい ID で続ける）。
    使う場面: すべての ML 案の run の中。結果 JSON に n_trials と一覧を書く
    入力: max_trials
    返り値: —
    禁止: 上限を黙って引き上げない（spec に書く）
    段階: 多重比較
    """
    def __init__(self, max_trials=50): self.max = max_trials; self.rows = []
    def add(self, params, metric):
        if len(self.rows) >= self.max: raise RuntimeError(f"試行の上限 {self.max} に達した。格子を減らすか新しい戦略 ID で")
        self.rows.append({"params": params, "metric": float(metric)})
    def to_json(self): return {"n_trials": len(self.rows), "max_trials": self.max, "trials": self.rows}
