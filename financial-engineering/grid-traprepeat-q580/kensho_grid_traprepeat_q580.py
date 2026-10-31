#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q580: トラリピ型の半々グリッドは FX8 の H1 で含み損込み・コスト後に年単位で正か、
              同じ年内でリターンを並べ替えたランダムウォークより良いか（Q579 の次段階）
================================================================================

【出典】
- 計画（事前登録）: Q579 の次段階・taichi「進めてください」（Opus 2026-10-30・設計とコードまで、実行と解釈は未）。アイデア候補.md の Q580 の行。
- 前段: Q579（棄却）。MA 整列での切替の前提は崩れたが、H1 の先 24 本の分散比は局面によらず 1 を下回り（非整列 U −0.034、記述の q=120 で −0.055）、
  「数日スケールでやや戻りやすい」はグリッドに有利な材料として残った。本案はそれがグリッドの損益（含み損込み・コスト後）に届くかを直接測る。
- 理論の背景: 価格がマルチンゲールなら、どんな指値の格子でも含み損込みの期待損益はコスト前で 0（任意抽出定理）。
  主張カード: [[Brock1992-2_買いと売りの差はランダムウォークやGARCHでは説明できない]]（ランダムウォーク帰無との比較の型）。
  関連知見: Q579、「為替の超短期の平均回帰は 2015 年以降の 1 時間足では消えた」、Q149（分散比で有意な年に売買してもコスト後は負）。
- 先行研究チェック（WebSearch 2026-10-30・英語）: 検索語 "grid trading strategy foreign exchange backtest profitability random walk mean reversion academic paper"。
  格子の吸収壁つき確率過程の理論（Virtus Interpress "Bi-directional grid absorption barrier constrained stochastic processes"）、BTC のグリッド＝マーケットメイク（Stevens）、
  個人ブログ・TradingView・MQL5 の FX グリッド。主要 FX で「含み損込み・コスト後」を「年内並べ替えのランダムウォーク」と前後半で比べた実証は見つからない（条件の穴）。ブログ・販売 EA は根拠にしない。

【仮説（測る前に固定）】
H1: 半々グリッドの年ごとの純損益（含み損込み・コスト後）は FX8 で正（前後半とも年単位 t ≥ 2）、かつ同じ年内で H1 リターンを並べ替えた系列で同じグリッドを回した帰無より良い（z ≥ 2）。
H0: 純損益は −コスト 程度で、並べ替えた帰無と区別できない。

【データ】FX8 の H1_dukascopy（2008〜2026-06）。前半 <2017／後半 ≥2017。TREND7 は記述のみ（トラリピは FX の商品なので判定は FX8）。

【定義（1 通りに固定）】
- 年ごとに独立の 1 回: 起点 a = その年の最初の H1 終値（対数価格）。間隔 Δ = k × ATR20(D1) / 前年末の終値（対数単位）、ATR20 は前年最後の日の値（D1 は H1 から 0 時 UTC 区切りで作る）。前年末の ATR が無い年は除く。
- 買いの格子: 水準 L_j = a − jΔ（j=1..N）。価格が L_j 以下になったら L_j で 1 単位買い、L_j+Δ 以上になったら L_j+Δ で決済（利確 1 間隔）。何度でも繰り返す（リピート）。
- 売りの格子: 水準 U_j = a + jΔ（j=1..N）。U_j 以上で売り、U_j−Δ 以下で決済。
- 価格の経路は H1 の終値だけ（足の中の高値安値は使わない。実データと帰無で同じ扱い）。終値で水準をまたいだら水準の価格で約定したとみなす（指値）。
  注意（試走で確認）: 終値だけで約定を判定すると、足の中で水準に触れて戻る動きを取り逃がし、連続の経路より損益が負に偏る。
  合成のランダムウォーク（1 本の σ=0.1%、Δ=0.3%、6000 本、コスト 0）400 年で総損益 −68±12 bp/年（グリッド全体の名目比）。同じ設定で負の自己相関（MA(1) 係数 −0.3）を入れると −19±12 bp。
  帰無も同じ経路の扱いなので z は偏らないが、「純損益 > 0」の t は保守的（支持しにくい）側に偏る。判定はそのまま固定し、記述に「帰無平均との差（excess）」の年単位 t を出す。
- 年末（その年の最後の H1）に建玉をすべて終値で決済（含み損を確定）。年の損益 = 実現益 + 年末の決済損益 − コスト。
- コスト: 1 回の約定ごとに片道コスト（段階 1 の COST_RT/2 を価格比の bp に）。年末の強制決済にもかかる。スワップは入れない（データに無い・限界として記録）。
- 単位: 1 水準あたり 1 単位、損益は「1 単位の名目に対する bp」の合計を総水準数 2N で割った「グリッド全体の名目に対する bp」。
- 主の設定: k = 0.5、N = 20（片側 ±10 ATR）。記述: k ∈ {0.25, 1.0}（N は同じ）。

【帰無】銘柄×年ごとに H1 の対数リターンを年内で並べ替え（起点と年末の価格は同じ・自己相関だけ壊す）× B=300、同じグリッドを回す。
FX8 の全期間の平均純損益（銘柄×年の平均）を帰無分布と比べて z。

【測るもの】
判定: FX8・k=0.5 の年単位の純損益の前後半の t（2 本）と全期間の z（1 本）。
記述（判定外）: 帰無平均との差 excess = net − null_mean の前後半の年単位 t、総損益（コスト前）、往復回数、年末の含み損（強制決済分）の大きさ、銘柄×年の最大下落（含み損込みの H1 評価額）と最悪の年、
k=0.25・1.0、TREND7、銘柄別の z、帰無の平均（＝コストだけ負けるはずの値）との差。

【判定（事前固定・変更禁止）】
- 支持: FX8・k=0.5 で前後半とも純損益の年単位 t ≥ 2、かつ全期間の z ≥ 2。
- 棄却: 前後半とも純損益の年単位 t < 1、かつ全期間の z < 2（儲からず、ランダムウォークより良いとも言えない）。
- 未確定: それ以外（例: z ≥ 2 だがコスト後に正と言えない＝ランダムウォークよりは良いがコストに届かない）。

【多重比較】判定は 3 本の AND。k・群・銘柄別は記述。

【捨てた案の数】約 5: 範囲を過去数年の高安から決める（先読みになりやすい）、足の中の高値安値で約定（帰無の並べ替えと整合しにくい）、
年をまたいで建玉を持ち越す（年の独立性が崩れ t が使えない）、スワップを外部金利から付ける（データ無し）、k と N の格子探索（過学習）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。データの終端も 2026-06。

【委託の確かめ方】設計・コードは Opus（2026-10-30）。実行と解釈は後で /lab（担当 opus）。実行者は JSON のパス・前後半の t・z・machine_verdict を返す。

【実装】自己完結（共通の土台を埋め込み）。格子は水準ごとのヒステリシス（入る／出るの最後の出来事を前方に埋める）でベクトル化。
実行: python3 kensho_grid_traprepeat_q580.py（B=300）／--B 30／--smoke（合成データ・経路確認のみ）
"""

# ============================================================================= 共通の土台（各スクリプトに同じものを埋め込む・自己完結）
import argparse
import datetime as _dt
import itertools
import json
import math
import os
import sys
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # ワークスペース


def _p(*parts):
    """macOS 共有の NFD 名に対応（NFC で無ければ NFD で探す）。"""
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
OUT = os.path.join(HERE, "results")
FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
FX6 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD"]  # ドル建て先進国（Q019・Q054 と同じ）
TREND7 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL", "US500", "USTECH", "BTCUSD"]
SYMS = FX8 + TREND7
CRYPTO = ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "ADAUSD", "BCHUSD", "XLMUSD", "EOSUSD", "LNKUSD", "DOTUSD", "SOLUSD"]
# 往復コスト（価格単位・段階1の保守値。Q136〜Q190 と同じ表）
COST_RT = {"EURUSD": .0002, "GBPUSD": .0002, "AUDUSD": .0002, "USDCHF": .0002, "USDCAD": .0002,
           "USDJPY": .02, "EURJPY": .02, "GBPJPY": .02, "XAUUSD": 0.6,
           "XAGUSD": 0.04, "WTI": 0.06, "UKOIL": 0.06, "US500": 1.0, "USTECH": 3.0, "BTCUSD": 40.0}
CRYPTO_COST_RT_REL = 30e-4  # 暗号資産: 往復 30bp の仮置き（Q152 と同じ）
SPLIT_YEAR = 2017
SEED = 20261010
GROUPS = {"all15": SYMS, "fx8": FX8, "trend7": TREND7}


# ----------------------------------------------------------------------------- データ
def _read(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def load_d1(sym, smoke=False, rng=None):
    """UTC 日足（D1_fromH1）。値動きのない足（high==low）は除く。列: time, open, high, low, close, ret, year"""
    if smoke:
        df = _smoke_ohlc(sym, rng, n=2600, freq="D", start="2015-01-01")
    else:
        df = _read(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    return df


def load_csv(name, smoke=False, rng=None, freq="h", n=20000, start="2015-01-01"):
    """任意の data_<name>.csv（H1/H4/M15/yahoo/ask）。"""
    if smoke:
        return _smoke_ohlc(name, rng, n=n, freq=freq, start=start)
    return _read(os.path.join(DATA_DIR, f"data_{name}.csv"))


SEAL_END = "2024-01-01"  # 封印 time<2024-07-01。年ごとに独立の 1 回なので 2024 年の半端な 1 回は Q581 と同じく外す（2026-10-31 事後の判断で追加）


def load_h1(sym, smoke=False, rng=None, n=60000, start="2015-01-01"):
    """UTC 1時間足（H1_dukascopy）。値動きのない足は除く。列: time, open, high, low, close, volume, ret, year, hour, dow"""
    df = load_csv(f"{sym}_H1_dukascopy", smoke, rng, freq="h", n=n, start=start)
    if not smoke:
        df = df[df["time"] < pd.Timestamp(SEAL_END)]
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    return df


def h1_to_d1(h1, cutoff_hour=0):
    """H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。"""
    t = h1["time"] - pd.Timedelta(hours=cutoff_hour)
    key = t.dt.floor("D")
    g = h1.groupby(key)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum() if "volume" in h1 else g["close"].size(), "nbars": g["close"].size()})
    d.index.name = "time"; d = d.reset_index()
    d = d[(d["high"] != d["low"]) & (d["nbars"] >= 6)].reset_index(drop=True)
    d["ret"] = d["close"].pct_change(); d["year"] = d["time"].dt.year
    return d


def _smoke_ohlc(sym, rng, n, freq, start):
    """合成データ（GBM）。判定には使わない。"""
    rng = rng or np.random.default_rng(SEED)
    t = pd.date_range(start, periods=n, freq=freq)
    r = rng.normal(0.0001, 0.006, n)
    c = 100.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n)))
    v = np.abs(rng.lognormal(8, 0.5, n))
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v})


def exists_sym(sym, kind="D1_fromH1"):
    return os.path.exists(os.path.join(DATA_DIR, f"data_{sym}_{kind}.csv"))


def cost_bp_oneway(sym, close, rel=None):
    """片道コスト [bp]（価格に対する比）。rel を渡せば相対コスト（往復）を使う。"""
    if rel is not None:
        return np.full(len(close), rel / 2 * 1e4)
    return COST_RT[sym] / 2 / np.asarray(close, float) * 1e4


# ----------------------------------------------------------------------------- 合図と損益
def tsmom_pos(close, L):
    c = np.asarray(close, float)
    s = np.zeros(len(c))
    s[L:] = np.sign(c[L:] - c[:-L])
    return s


def sma_pos(close, n):
    c = pd.Series(np.asarray(close, float))
    m = c.rolling(n).mean().values
    s = np.sign(c.values - m)
    s[np.isnan(m)] = 0.0
    return s


def atr(high, low, close, n=20):
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    return pd.Series(tr).rolling(n).mean().values


def rsi(close, n):
    c = pd.Series(np.asarray(close, float))
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).values


def pnl_bp(pos, close, cost_oneway_bp):
    """pos[t] は t の終値で決めて t+1 のリターンに効く。pnl[t+1] = pos[t]*ret[t+1]*1e4 − |pos[t]−pos[t−1]|*片道[bp]。先頭は 0。"""
    c = np.asarray(close, float); pos = np.asarray(pos, float)
    ret = np.zeros(len(c)); ret[1:] = c[1:] / c[:-1] - 1
    held = np.r_[0.0, pos[:-1]]
    prev = np.r_[0.0, held[:-1]]
    cost = np.abs(held - prev) * np.r_[0.0, cost_oneway_bp[:-1]]
    return held * ret * 1e4 - cost


# ----------------------------------------------------------------------------- 統計
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def nw_t(x, lag=5):
    """Newey-West（Bartlett）の t。"""
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan")
    e = x - x.mean()
    s = (e ** 2).sum()
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] * e[:-k]).sum()
    se = math.sqrt(max(s, 1e-300)) / n
    return float(x.mean() / se) if se > 0 else float("nan")


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
    if len(x) < 3:
        return float("nan")
    rx = np.array(pd.Series(x).rank().values, float); ry = np.array(pd.Series(y).rank().values, float)
    rx -= rx.mean(); ry -= ry.mean()
    d = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def max_drawdown(pnl):
    cum = np.cumsum(np.asarray(pnl, float)); peak = np.maximum.accumulate(cum)
    return float((cum - peak).min()) if len(cum) else float("nan")


def sharpe_ann(pnl, per_year=252):
    x = np.asarray(pnl, float); x = x[np.isfinite(x)]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(per_year)) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def qlike(s2_pred, r2):
    """QLIKE 損失（小さいほど良い）。r2: 実現分散、s2_pred: 予測分散。"""
    s2 = np.asarray(s2_pred, float); r2 = np.asarray(r2, float)
    m = np.isfinite(s2) & np.isfinite(r2) & (s2 > 0) & (r2 > 0)
    return float(np.mean(r2[m] / s2[m] - np.log(r2[m] / s2[m]) - 1)) if m.sum() > 2 else float("nan")


def z_of(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null < obs).mean())


def perm_within(rng, x, groups):
    """groups（例: 年）の中で x を並べ替える。"""
    x = np.asarray(x, float).copy(); g = np.asarray(groups)
    for v in np.unique(g):
        idx = np.where(g == v)[0]
        x[idx] = x[rng.permutation(idx)]
    return x


def block_perm(rng, x, block):
    """block 本ごとの塊を並べ替える（塊の中の順序は保つ）。"""
    x = np.asarray(x, float); n = len(x); nb = int(math.ceil(n / block))
    order = rng.permutation(nb)
    out = np.concatenate([x[b * block:(b + 1) * block] for b in order])
    return out[:n]


def circ_shift(rng, x, min_shift=1):
    """循環シフト（合図とリターンの対応を壊し、合図の自己相関は保つ）。"""
    x = np.asarray(x, float); n = len(x)
    k = int(rng.integers(min_shift, max(min_shift + 1, n - min_shift)))
    return np.roll(x, k)


def holm(pvals):
    p = np.asarray(pvals, float); m = len(p); order = np.argsort(p); adj = np.empty(m)
    run = 0.0
    for i, k in enumerate(order):
        run = max(run, (m - i) * p[k]); adj[k] = min(1.0, run)
    return adj


def by_year_stats(df, col, year_col="year", y0=0, y1=9999):
    """年を単位にした平均と t（銘柄は年の中で平均してから）。df: year, sym, col。"""
    d = df[(df[year_col] >= y0) & (df[year_col] < y1)]
    if d.empty:
        return {"n_years": 0, "mean": float("nan"), "t": float("nan")}
    if "sym" in d.columns:
        yr = d.groupby([year_col, "sym"])[col].mean().groupby(level=0).mean()
    else:
        yr = d.groupby(year_col)[col].mean()
    yr = yr.dropna()
    return {"n_years": int(len(yr)), "mean": float(yr.mean()) if len(yr) else float("nan"), "t": tstat(yr.values)}


# ----------------------------------------------------------------------------- 入出力
def parse_args(default_B=300, extra=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=default_B, help="帰無の回数")
    ap.add_argument("--smoke", action="store_true", help="合成データで経路の確認（判定に使わない）")
    ap.add_argument("--seed", type=int, default=SEED)
    if extra:
        extra(ap)
    return ap.parse_args()


def write_result(qid, res, smoke, extra_csv=None):
    os.makedirs(OUT, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    path = os.path.join(OUT, f"{pre}_result_{ts}.json")
    res = {"qid": qid, "smoke": smoke, "generated": ts, **res}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=_json_default)
    print("wrote", os.path.relpath(path, HERE))
    if extra_csv is not None:
        for name, df in extra_csv.items():
            cp = os.path.join(OUT, f"{pre}_{name}_{ts}.csv"); df.to_csv(cp, index=False); print("wrote", os.path.relpath(cp, HERE))
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp, _dt.datetime, _dt.date)):
        return str(o)
    return str(o)


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def syms_available(syms, kind="D1_fromH1", smoke=False):
    if smoke:
        return list(syms), []
    ok = [s for s in syms if exists_sym(s, kind)]
    return ok, [s for s in syms if s not in ok]
# ============================================================================= 共通の土台ここまで


QID = "Q580"
SEED = 20261031
DEFAULT_B = 300
K_MAIN = 0.5
K_DESC = [0.25, 1.0]
N_LEV = 20
ATR_N = 20


def grid_year(lp, a, delta, n_lev, cost_bp, want_curve=False):
    """1 年分の格子。lp: 対数終値の配列（年内）。返り値: 純損益・総損益・往復回数・年末決済損益（いずれも 1 単位 bp の合計）・最大下落。"""
    T = len(lp)
    gross_real = 0.0; trips = 0; fills = 0; end_mtm = 0.0
    eq = np.zeros(T) if want_curve else None
    for side in (+1, -1):  # +1 買い格子（起点の下）、−1 売り格子（起点の上）
        for j in range(1, n_lev + 1):
            if side == 1:
                L = a - j * delta; tp = L + delta
                ev = np.where(lp <= L, 1.0, np.where(lp >= tp, -1.0, np.nan))
            else:
                L = a + j * delta; tp = L - delta
                ev = np.where(lp >= L, 1.0, np.where(lp <= tp, -1.0, np.nan))
            idx = np.where(np.isnan(ev), 0, np.arange(T))
            idx = np.maximum.accumulate(idx)
            st = ev[idx]  # 最後の出来事を前方に埋める（先頭が NaN なら建玉なし）
            st = np.where(np.isnan(st), -1.0, st)  # 1=建玉あり
            on = (st == 1.0).astype(np.int8)
            d = np.diff(np.r_[0, on])
            n_open = int((d == 1).sum()); n_close = int((d == -1).sum())
            trips += n_close; fills += n_open + n_close
            gross_real += n_close * delta * 1e4
            if on[-1]:
                m = side * (lp[-1] - L) * 1e4
                end_mtm += m; fills += 1  # 年末の強制決済
            if want_curve:
                cum_close = np.cumsum(d == -1) * delta * 1e4
                unreal = on * side * (lp - L) * 1e4
                cum_fill = np.cumsum(np.abs(d)) * cost_bp
                eq += cum_close + unreal - cum_fill
    cost = fills * cost_bp
    gross = gross_real + end_mtm
    net = gross - cost
    mdd = float("nan")
    if want_curve:
        mdd = max_drawdown(np.r_[0.0, np.diff(eq)])  # 含み損込みの評価額（年末の強制決済コストは除く・記述用）
    return net, gross, trips, end_mtm, mdd


def year_episodes(sym, h1, d1):
    """年ごとの (year, lp, a, delta_per_k, cost_bp)。"""
    d1 = d1.copy()
    d1["atr"] = atr(d1["high"].values, d1["low"].values, d1["close"].values, ATR_N)
    eps = []
    for y in sorted(h1["year"].unique()):
        prev = d1[d1["time"] < pd.Timestamp(f"{y}-01-01")]
        if prev.empty or not np.isfinite(prev["atr"].iloc[-1]):
            continue
        hy = h1[h1["year"] == y]
        if len(hy) < 1000:
            continue
        lp = np.log(hy["close"].values.astype(float))
        dk = float(prev["atr"].iloc[-1] / prev["close"].iloc[-1])
        cost_bp = float(cost_bp_oneway(sym, np.array([prev["close"].iloc[-1]]))[0]) if sym in COST_RT else CRYPTO_COST_RT_REL / 2 * 1e4
        eps.append((int(y), lp, lp[0], dk, cost_bp))
    return eps


def perm_path(rng, lp):
    r = np.diff(lp)
    return lp[0] + np.r_[0.0, np.cumsum(rng.permutation(r))]


def run_group(data, k, rng, B, want_null):
    rows = []; null_sum = {}
    for s, (h1, d1) in data.items():
        for (y, lp, a, dk, cb) in year_episodes(s, h1, d1):
            delta = k * dk
            net, gross, trips, endm, mdd = grid_year(lp, a, delta, N_LEV, cb, want_curve=True)
            row = {"sym": s, "year": y, "net": net / (2 * N_LEV), "gross": gross / (2 * N_LEV), "trips": trips,
                   "end_mtm": endm / (2 * N_LEV), "mdd": mdd / (2 * N_LEV), "delta_bp": delta * 1e4, "cost_bp_oneway": cb}
            if want_null:
                nv = np.empty(B)
                for b in range(B):
                    nv[b] = grid_year(perm_path(rng, lp), a, delta, N_LEV, cb)[0] / (2 * N_LEV)
                row["null_mean"] = float(nv.mean())
                null_sum[(s, y)] = nv
            rows.append(row)
    return pd.DataFrame(rows), null_sum


def half_stats(cells, col, syms):
    d = cells[cells["sym"].isin(syms)]
    return {"full": by_year_stats(d, col), "pre": by_year_stats(d, col, y1=SPLIT_YEAR), "post": by_year_stats(d, col, y0=SPLIT_YEAR)}


def agg_z(cells, null_sum, syms, B):
    d = cells[cells["sym"].isin(syms)]
    keys = [(s, y) for s, y in zip(d["sym"], d["year"]) if (s, y) in null_sum]
    if not keys:
        return float("nan"), float("nan"), float("nan")
    obs = float(np.mean([d[(d["sym"] == s) & (d["year"] == y)]["net"].iloc[0] for s, y in keys]))
    nm = np.mean(np.vstack([null_sum[k] for k in keys]), axis=0)
    z, p = z_of(obs, nm)
    return obs, z, float(nm.mean())


def machine_verdict(H, z):
    tp, tq = H["pre"]["t"], H["post"]["t"]
    parts = {"net_pre_t": f(tp), "net_post_t": f(tq), "z": f(z)}
    if np.isfinite(tp) and np.isfinite(tq) and tp >= 2 and tq >= 2 and np.isfinite(z) and z >= 2:
        return "支持", parts
    if np.isfinite(tp) and np.isfinite(tq) and tp < 1 and tq < 1 and (not np.isfinite(z) or z < 2):
        return "棄却", parts
    return "未確定", parts


def run(args, rng):
    allsyms = FX8 + TREND7
    syms, missing = syms_available(allsyms, kind="H1_dukascopy", smoke=args.smoke)
    data = {}
    for s in syms:
        h1 = load_h1(s, args.smoke, rng)
        d1 = h1_to_d1(h1, 0)
        data[s] = (h1, d1)
    fx = {s: v for s, v in data.items() if s in FX8}
    tr = {s: v for s, v in data.items() if s in TREND7}

    cells, nulls = run_group(fx, K_MAIN, rng, args.B, True)
    fx_syms = list(fx)
    cells["excess"] = cells["net"] - cells["null_mean"]
    H = half_stats(cells, "net", fx_syms)
    obs, z, null_mean = agg_z(cells, nulls, fx_syms, args.B)
    verdict, parts = machine_verdict(H, z)

    per_sym = []
    for s in fx_syms:
        o, zs, nm = agg_z(cells, nulls, [s], args.B)
        c = cells[cells["sym"] == s]
        per_sym.append({"sym": s, "net_mean": f(o), "z": f(zs), "null_mean": f(nm), "gross_mean": f(c["gross"].mean()),
                        "trips_per_year": f(c["trips"].mean(), 1), "end_mtm_mean": f(c["end_mtm"].mean()),
                        "worst_year_net": f(c["net"].min()), "worst_mdd": f(c["mdd"].min()), "delta_bp_mean": f(c["delta_bp"].mean(), 1)})

    desc = {}
    for k in K_DESC:
        ck, _ = run_group(fx, k, rng, 0, False)
        desc[f"fx8_k{k}"] = {"net": half_stats(ck, "net", fx_syms), "gross": half_stats(ck, "gross", fx_syms),
                             "trips_mean": f(ck["trips"].mean(), 1), "worst_mdd": f(ck["mdd"].min())}
    if tr:
        ct, _ = run_group(tr, K_MAIN, rng, 0, False)
        desc["trend7_k0.5"] = {"net": half_stats(ct, "net", list(tr)), "gross": half_stats(ct, "gross", list(tr)),
                               "trips_mean": f(ct["trips"].mean(), 1), "worst_mdd": f(ct["mdd"].min())}

    res = {
        "config": {"seal_end": SEAL_END, "syms_fx8": fx_syms, "syms_trend7": list(tr), "missing": missing, "B": args.B, "k_main": K_MAIN, "k_desc": K_DESC,
                   "n_levels_per_side": N_LEV, "atr_n": ATR_N, "split_year": SPLIT_YEAR, "seed": args.seed,
                   "unit": "グリッド全体の名目に対する bp（1 水準 1 単位の bp 合計 ÷ 2N）"},
        "main_fx8_k0.5": {"net": H, "excess_over_null_desc": half_stats(cells, "excess", fx_syms), "gross": half_stats(cells, "gross", fx_syms), "end_mtm": half_stats(cells, "end_mtm", fx_syms),
                          "obs_net_full_mean": f(obs), "z": f(z), "null_mean": f(null_mean)},
        "machine_verdict": verdict, "parts": parts, "n_tests_judged": 3,
        "per_symbol_fx8": per_sym,
        "describe": desc,
        "note": "machine_verdict は事前固定の規則で機械的に付けたもの。解釈は実行者が README の「結果」に書く。スワップは入れていない。",
    }
    return res, {"cells": cells, "symbols": pd.DataFrame(per_sym)}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, extra_csv=csvs)
    print("machine_verdict:", res["machine_verdict"], res["parts"])


if __name__ == "__main__":
    main()
