# -*- coding: utf-8 -*-
"""Q560: Q559 の続き — 標的をコスト抜きにしても、RF の学習外 AUC 地図で「四半期の難しさの散らばり」は残るか（事前登録_q560.md）。
事前登録 事前登録_q560.md と同一・変更禁止。Q559 との違いは標的の定義だけ。

【出典】Q559（平均 AUC 0.527・D_q z 3.7 Holm p 0.006・D_sym z 0.7・ρ 0.47。事後の気づき: 特徴量重要度 1 位が spr_R＝コストの予測が AUC の一部）。
【仮説】Q559 で見えた「四半期で難しさが違う」は、スプレッド（コスト）の時変の言い換えではなく、方向の予測しやすさの時変である。
  → コスト抜きの標的でも D_q は帰無より大きいまま。平均 AUC は 0.527 より下がる（コスト分が抜ける）。
【データ】Q559 と同じ 15 銘柄 H1・2013Q1〜2025Q3・2025-10-01 以降は読まない。
【定義】標的 y = 1[ 買い RR1.0 がコスト抜きで勝つ ]: bid の始値 P で入り、SL = P − 1.5×ATR24、TP = P + 1.5×ATR24、判定は bid の高値安値、
  ギャップは始値で約定、時間切れ 120 本は bid 終値、保有コスト・スプレッドなし。特徴量 = `K.features` の 22 列（spr_R も残す・Q559 と同一）。
  モデル・学習の切り方・評価四半期・帰無・B は Q559 と同一。
【測るもの】Q559 と同じ: セル AUC・D_sym・D_q・ρ。記述: 平均 AUC（Q559 の 0.527 との差）・spr_R の重要度順位。
【帰無】標的の銘柄内循環シフト（≥120 本・スコアはそのまま）B=500。
【判定（事前固定・変更禁止・多重比較 3 本〔D_sym・D_q・ρ〕に Holm）】
- 支持（局面の難しさはコストの言い換えではない）: D_q が Holm 後 p < 0.05。
- 棄却（Q559 の D_q はコストの時変だった）: D_q が補正前 p ≥ 0.05。
- 未確定: それ以外（補正前 p<0.05 だが Holm 後 ≥0.05）。D_sym・ρ は記述（Q559 と並べる）。
【捨てた案】spr_R を特徴量から抜く版（標的がコスト抜きなら spr_R にコストの情報は無いので、残したほうが「方向の情報を持つか」が分かる）・
  売り側の標的・RR1.5/2.0 — の 3 つ。
【知識の締め切り】Claude はおよそ 2026-06。評価期間はすべて締め切り前。地図なので採用判断はない。
【委託の確かめ方】`result_q560.json` の `judgement` は機械判定。解釈は実行者。Q559 の `cells_q559.csv` とセルごとに並べて見る。
【実装】Q559 のスクリプトの複製で、標的を作る `labels_nocost` を足し `build` だけ替えた。ほかは同一。

使い方: python3 kensho_s21_rf_difficulty_nocost_q560.py DATA_DIR OUT_DIR [--smoke] [--B 500] [--step 3] [--n_estimators 300] [--no-oob]
"""
import argparse, json, os, pickle, sys, time
import numpy as np, pandas as pd
from scipy import stats as sps
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kensho_s21_h1_ml_rr_q515 as K

QID = "Q560"
UTC = lambda s: pd.Timestamp(s, tz="UTC")
EVAL0, EVAL1 = UTC("2013-01-01"), UTC("2025-10-01")   # 評価四半期の始まり・終わり（終端は含まない）
TARGET_ACTION = 0                                      # K.ACTIONS[0] = (買い, RR 1.0)
BLOCK = K.H                                            # 120 本（ラベル地平＝重なりの長さ）
MIN_TRAIN_ROWS = 20000                                 # これ未満の四半期は飛ばす（記録する）
RF_PARAMS = dict(n_estimators=300, min_samples_leaf=500, max_features="sqrt", bootstrap=True, oob_score=True, n_jobs=-1)
SEED = 20261028
TESTS = ["D_sym", "D_q", "rho_half"]


def _compat_tz_to_numpy():
    """pandas 2.3 で tz つき Series.to_numpy() が object になり K.labels が落ちる環境への回避（Q555 と同じ・値は変わらない）。"""
    if str(pd.Series(pd.to_datetime(["2020-01-01"], utc=True)).to_numpy().dtype) != "object":
        return
    orig = pd.Series.to_numpy

    def to_numpy(self, *args, **kw):
        if not args and not kw and isinstance(self.dtype, pd.DatetimeTZDtype):
            return self.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
        return orig(self, *args, **kw)
    pd.Series.to_numpy = to_numpy


# ---------------- データ ----------------
def _smoke_ohlc(rng, sym, n=9000, start="2015-01-01"):
    """合成 H1（smoke 用・判定に使わない）。弱いトレンドの持続を入れて AUC が 0.5 からわずかに動くようにする。"""
    t = pd.date_range(start, periods=n, freq="h", tz="UTC")
    drift = np.zeros(n); eps = rng.normal(0, 1e-3, n)
    for i in range(1, n):
        drift[i] = 0.9 * drift[i - 1] + 0.1 * eps[i]
    r = eps + 0.5 * drift
    c = 1.2 * np.exp(np.cumsum(r)); o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 4e-4, n))); l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 4e-4, n)))
    spr = 1e-4 * c
    d = pd.DataFrame(dict(time=t, open=o, high=h, low=l, close=c, volume=np.exp(rng.normal(3, 1, n))))
    for k, v in dict(open=o, high=h, low=l, close=c).items():
        d[f"ask_{k}"] = v + spr
    d["spr"] = spr
    return d


def load_sym(data_dir, sym, smoke, rng):
    if smoke:
        return _smoke_ohlc(rng, sym)
    return K.load(data_dir, sym)


def labels_nocost(d):
    """買い RR1.0・コスト抜きの R（bid 始値で入り・SL/TP とも bid・保有コストなし）。K.labels の行動 0 と同じ手順でコストだけ外す。"""
    n = len(d)
    bo, bh, bl, bc = (d[c].to_numpy(float) for c in ["open", "high", "low", "close"])
    tr = np.maximum(bh - bl, np.maximum(np.abs(bh - np.r_[bc[0], bc[:-1]]), np.abs(bl - np.r_[bc[0], bc[:-1]])))
    atr = pd.Series(tr).rolling(24, min_periods=24).mean().to_numpy()
    D = K.K_ATR * atr; H = K.H
    R = np.full(n, np.nan)
    idx = np.where(np.isfinite(D) & (np.arange(n) + H < n))[0]; e = idx + 1
    Dv = D[idx]; P = bo[e]; SL = P - Dv; TP = P + Dv
    exitp = np.full(len(idx), np.nan); open_ = np.ones(len(idx), bool)
    for k in range(H):
        j = e + k; o, lo, hi = bo[j], bl[j], bh[j]
        gap = open_ & (o <= SL); sl = open_ & ~gap & (lo <= SL); tp = open_ & ~gap & ~sl & (hi >= TP)
        exitp[gap] = o[gap]; exitp[sl] = SL[sl]; exitp[tp] = TP[tp]
        open_ &= ~(gap | sl | tp)
        if not open_.any():
            break
    exitp[open_] = bc[e + H - 1][open_]
    R[idx] = (exitp - P) / Dv
    return R


def build(data_dir, syms, smoke, rng, end_excl):
    out = {}
    for s in syms:
        t0 = time.time()
        d = load_sym(data_dir, s, smoke, rng)
        d = d[d["time"] < end_excl].reset_index(drop=True)     # 2025-10-01 以降は読まない
        R, X, D = K.labels(d, s)
        F = K.features(d, D, s)
        Rn = labels_nocost(d)                                    # Q560: 標的だけコスト抜き
        y = (Rn > 0).astype(float); y[~np.isfinite(Rn)] = np.nan
        out[s] = dict(time=d["time"].reset_index(drop=True), y=y, X=X, F=F, ok=np.isfinite(R).all(1))
        print(f"  {s}: {len(d)} 本, {time.time()-t0:.1f}s", flush=True)
    return out


def quarters(first, last_excl):
    out = []; q = first
    while q < last_excl:
        out.append(q); q = q + pd.DateOffset(months=3)
    return out


def qlabel(ts):
    return f"{ts.year}-Q{(ts.month - 1) // 3 + 1}"


# ---------------- 学習・予測 ----------------
def train_rows(data, end, step):
    """end より前に決済まで終わる行だけ（S21 の embargo と同じ）。"""
    Xs, Ys, tags = [], [], []
    e = end.tz_convert(None).to_datetime64()
    for s, o in data.items():
        t = o["time"]; n = len(t); tn = t.dt.tz_convert(None).to_numpy()
        xmax = o["X"].max(1)
        ok = o["ok"] & (xmax >= 0) & (tn[np.clip(xmax, 0, n - 1)] < e)
        sel = np.where(ok)[0][::step]
        Xs.append(o["F"].iloc[sel]); Ys.append(o["y"][sel]); tags.append((np.repeat(s, len(sel)), sel))
    tag_sym = np.concatenate([t[0] for t in tags]); tag_idx = np.concatenate([t[1] for t in tags]).astype(int)
    return pd.concat(Xs), np.concatenate(Ys), (tag_sym, tag_idx)


def fit_rf(Xtr, ytr, params, seed):
    from sklearn.ensemble import RandomForestClassifier
    m = RandomForestClassifier(random_state=seed, **params)
    m.fit(Xtr.fillna(-999.0), ytr.astype(int))
    return m


def predict_q(m, data, s0, s1):
    P = {}
    for s, o in data.items():
        t = o["time"]
        msk = ((t >= s0) & (t < s1)).to_numpy() & o["ok"]
        idx = np.where(msk)[0]
        pr = m.predict_proba(o["F"].iloc[idx].fillna(-999.0))[:, 1] if len(idx) else np.zeros(0)
        P[s] = (idx, pr)
    return P


# ---------------- 物差し ----------------
def auc(y, s):
    """Mann–Whitney の AUC（同順位は平均順位）。片方のクラスが無ければ nan。"""
    y = np.asarray(y, int); s = np.asarray(s, float)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = sps.rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def block_boot_ci(y, s, B, rng, block=BLOCK):
    n = len(y)
    if n < 2 * block:
        return (np.nan, np.nan)
    nb = int(np.ceil(n / block)); vals = np.empty(B)
    for b in range(B):
        st = rng.integers(0, n, nb)
        ii = (st[:, None] + np.arange(block)[None, :]).ravel() % n
        ii = ii[:n]
        vals[b] = auc(y[ii], s[ii])
    return (float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5)))


def circ_shift_labels(y, rng, minoff=BLOCK):
    n = len(y)
    if n <= 2 * minoff:
        return y
    u = rng.integers(minoff, n - minoff)
    return np.roll(y, u)


def axis_stats(tab, qs):
    """tab: DataFrame(sym, q, y, s)。返り値: (D_sym, D_q, rho_half, per_sym AUC, per_q AUC, mean AUC)。"""
    per_sym = tab.groupby("sym").apply(lambda g: auc(g["y"].to_numpy(), g["s"].to_numpy()), include_groups=False)
    per_q = tab.groupby("q").apply(lambda g: auc(g["y"].to_numpy(), g["s"].to_numpy()), include_groups=False)
    half = len(qs) // 2
    first, second = set(qs[:half]), set(qs[half:])
    cell = tab.groupby(["sym", "q"]).apply(lambda g: auc(g["y"].to_numpy(), g["s"].to_numpy()), include_groups=False).unstack("q")
    a1 = cell[[c for c in cell.columns if c in first]].mean(axis=1); a2 = cell[[c for c in cell.columns if c in second]].mean(axis=1)
    rho = float(sps.spearmanr(a1, a2, nan_policy="omit").statistic) if len(a1) >= 3 else np.nan
    return dict(D_sym=float(np.nanstd(per_sym, ddof=1)), D_q=float(np.nanstd(per_q, ddof=1)), rho_half=rho,
                per_sym=per_sym, per_q=per_q, mean_auc=auc(tab["y"].to_numpy(), tab["s"].to_numpy()))


def holm(p):
    p = np.asarray(p, float); m = len(p); order = np.argsort(p); adj = np.empty(m)
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, (m - k) * p[i]); adj[i] = min(1.0, run)
    return adj


def judge(p_raw, p_holm, rho):
    """Q560 の規則: D_q（TESTS[1]）だけで 3 分岐。D_sym・ρ は記述。"""
    if p_holm[1] < 0.05:
        return "支持（局面の難しさはコストの言い換えではない）"
    if p_raw[1] >= 0.05:
        return "棄却（Q559 の D_q はコストの時変だった）"
    return "未確定"


# ---------------- 本体 ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("out")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=500)
    ap.add_argument("--step", type=int, default=3); ap.add_argument("--n_estimators", type=int, default=RF_PARAMS["n_estimators"])
    ap.add_argument("--no-oob", action="store_true")
    a = ap.parse_args()
    _compat_tz_to_numpy()
    rng = np.random.default_rng(SEED)
    params = dict(RF_PARAMS, n_estimators=a.n_estimators)
    if a.smoke:
        syms = ["EURUSD", "US500"]; qs = quarters(UTC("2015-10-01"), UTC("2016-04-01")); params = dict(params, n_estimators=20, min_samples_leaf=50)
        tag = "smoke_"
    else:
        syms = list(K.SYMS); qs = quarters(EVAL0, EVAL1); tag = ""
    assert qs[-1] + pd.DateOffset(months=3) <= EVAL1 or a.smoke
    resdir = os.path.join(a.out, "results"); pkldir = os.path.join(a.out, f"{tag}q560"); os.makedirs(resdir, exist_ok=True); os.makedirs(pkldir, exist_ok=True)
    t00 = time.time()
    print("ラベル・特徴量", flush=True)
    data = build(a.data, syms, a.smoke, rng, EVAL1 if not a.smoke else UTC("2030-01-01"))
    cols = list(next(iter(data.values()))["F"].columns)
    res = dict(qid=QID, run_at=time.strftime("%Y-%m-%d %H:%M"), smoke=a.smoke, syms=syms, n_features=len(cols), features=cols,
               rf_params={k: (v if not isinstance(v, (np.integer,)) else int(v)) for k, v in params.items()}, step=a.step, B=a.B,
               target="y=1[買い RR1.0 がコスト抜きで勝つ]（labels_nocost）", quarters=[qlabel(q) for q in qs], skipped=[], n_train_rows={})

    # 1) 四半期ごとに拡大窓で学習 → 学習外予測（続きから）
    rows = []
    for q in qs:
        s0, s1 = q, q + pd.DateOffset(months=3); ql = qlabel(q); pk = os.path.join(pkldir, f"{ql}.pkl")
        if os.path.exists(pk):
            with open(pk, "rb") as f:
                P, ntr = pickle.load(f)
            print(f"  {ql}: 保存済み（学習 {ntr} 行）", flush=True)
        else:
            t0 = time.time()
            Xtr, ytr, _ = train_rows(data, s0, a.step)
            ntr = len(Xtr)
            if ntr < (500 if a.smoke else MIN_TRAIN_ROWS) or len(np.unique(ytr)) < 2:
                res["skipped"].append(dict(q=ql, n_train=int(ntr))); print(f"  {ql}: 学習行 {ntr} で飛ばす", flush=True); continue
            m = fit_rf(Xtr, ytr, params, SEED + len(rows))
            P = predict_q(m, data, s0, s1)
            with open(pk, "wb") as f:
                pickle.dump((P, ntr), f)
            print(f"  {ql}: 学習 {ntr} 行・{time.time()-t0:.0f}s", flush=True)
        res["n_train_rows"][ql] = int(ntr)
        for s, (idx, pr) in P.items():
            if len(idx):
                rows.append(pd.DataFrame(dict(sym=s, q=ql, i=idx, y=data[s]["y"][idx], s=pr)))
    tab = pd.concat(rows, ignore_index=True); tab = tab[np.isfinite(tab["y"])].reset_index(drop=True)
    tab["y"] = tab["y"].astype(int)
    qs_done = [qlabel(q) for q in qs if qlabel(q) in set(tab["q"])]

    # 2) セルの AUC と区間
    cells = []
    for (s, ql), g in tab.groupby(["sym", "q"], sort=False):
        y, sc = g["y"].to_numpy(), g["s"].to_numpy()
        lo, hi = block_boot_ci(y, sc, a.B, rng)
        cells.append(dict(sym=s, q=ql, n=len(g), base_rate=float(y.mean()), auc=auc(y, sc), ci_lo=lo, ci_hi=hi))
    cells = pd.DataFrame(cells); cells.to_csv(os.path.join(resdir, f"{tag}cells_q560.csv"), index=False)

    # 3) 軸の統計と帰無（標的の銘柄内循環シフト・スコアはそのまま）
    obs = axis_stats(tab, qs_done)
    null = {k: np.empty(a.B) for k in TESTS}; null_mean = np.empty(a.B)
    tab_n = tab.copy()
    for b in range(a.B):
        ys = []
        for s, g in tab.groupby("sym", sort=False):
            ys.append(pd.Series(circ_shift_labels(g["y"].to_numpy(), rng), index=g.index))
        tab_n["y"] = pd.concat(ys).reindex(tab.index).to_numpy()
        st = axis_stats(tab_n, qs_done)
        for k in TESTS:
            null[k][b] = st[k]
        null_mean[b] = st["mean_auc"]
        if (b + 1) % 50 == 0:
            print(f"  帰無 {b+1}/{a.B}", flush=True)
    stat = {}
    for k in TESTS:
        o = obs[k]; nv = null[k][np.isfinite(null[k])]
        if not np.isfinite(o) or len(nv) < 2:
            stat[k] = dict(obs=None, null_mean=None, null_sd=None, z=None, p_raw=1.0); continue
        p = float((1 + (nv >= o).sum()) / (len(nv) + 1))
        stat[k] = dict(obs=float(o), null_mean=float(nv.mean()), null_sd=float(nv.std(ddof=1)),
                       z=float((o - nv.mean()) / nv.std(ddof=1)) if nv.std() > 0 else None, p_raw=p)
    p_raw = [stat[k]["p_raw"] for k in TESTS]; p_h = holm(p_raw)
    for k, ph in zip(TESTS, p_h):
        stat[k]["p_holm"] = float(ph)
    res["stats"] = stat
    res["mean_auc"] = dict(obs=obs["mean_auc"], null_mean=float(null_mean.mean()), null_sd=float(null_mean.std(ddof=1)),
                           z=float((obs["mean_auc"] - null_mean.mean()) / null_mean.std(ddof=1)))
    res["per_sym_auc"] = {k: float(v) for k, v in obs["per_sym"].items()}
    res["per_q_auc"] = {k: float(v) for k, v in obs["per_q"].items()}
    pq = obs["per_q"].to_numpy(float)
    res["per_q_lag1_autocorr"] = float(np.corrcoef(pq[:-1], pq[1:])[0, 1]) if len(pq) > 3 else None
    cls = {s: K.CLASS[s] for s in syms}
    res["auc_by_class"] = {str(c): auc(tab.loc[tab["sym"].map(cls) == c, "y"], tab.loc[tab["sym"].map(cls) == c, "s"]) for c in sorted(set(cls.values()))}
    res["judgement"] = judge(p_raw, p_h, obs["rho_half"] if np.isfinite(obs["rho_half"]) else -1.0)
    res["machine_verdict"] = res["judgement"]

    # 4) 副（判定外）: 最終学習（〜EVAL1）の OOB 地図と学習外地図の対応・特徴量重要度
    if not a.no_oob:
        t0 = time.time()
        end_all = qs[-1] + pd.DateOffset(months=3)
        Xtr, ytr, tg = train_rows(data, end_all, a.step)
        m = fit_rf(Xtr, ytr, params, SEED + 999)
        oob = m.oob_decision_function_[:, 1]
        syms_tr, idx_tr = tg
        tq = np.array([qlabel(data[s]["time"].iloc[i]) for s, i in zip(syms_tr, idx_tr)])
        oobtab = pd.DataFrame(dict(sym=syms_tr, q=tq, y=ytr.astype(int), s=oob)); oobtab = oobtab[np.isfinite(oobtab["s"])]
        oobcells = oobtab.groupby(["sym", "q"]).apply(lambda g: auc(g["y"].to_numpy(), g["s"].to_numpy()), include_groups=False).rename("auc_oob").reset_index()
        oobcells.to_csv(os.path.join(resdir, f"{tag}cells_oob_q560.csv"), index=False)
        mg = cells.merge(oobcells, on=["sym", "q"], how="inner").dropna(subset=["auc", "auc_oob"])
        res["oob"] = dict(n_train=int(len(Xtr)), oob_auc_all=auc(oobtab["y"], oobtab["s"]), n_common_cells=int(len(mg)),
                          spearman_oob_vs_oot=float(sps.spearmanr(mg["auc"], mg["auc_oob"]).statistic) if len(mg) >= 3 else None,
                          importance_top10={c: float(v) for c, v in sorted(zip(cols, m.feature_importances_), key=lambda x: -x[1])[:10]},
                          sec=round(time.time() - t0))
    res["sec_total"] = round(time.time() - t00)
    with open(os.path.join(resdir, f"{tag}result_q560.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(dict(judgement=res["judgement"], stats=stat, mean_auc=res["mean_auc"], per_sym=res["per_sym_auc"]), ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
