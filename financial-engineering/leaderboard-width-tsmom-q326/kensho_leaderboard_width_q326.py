#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q326: 順張りの参照日数60本の順位表 L(j) は上位ほど悪いか・格子を広げるほど選択の翌年は悪くなるか
================================================================================
【出典】Wang (2026) "How Far Down the Backtest Leaderboard Should You Trust?" §3.2 Proposition 1・Corollary 1（p3〜4）
  主張カード Wang2026BT-1〜3。手元の先行: Q139（selection-optimism-vs-J）・Q171（PBO 0.88・劣化の傾き -0.96）。
  計画はアイデア候補.md 2026-10-19 の行（Q325-C1、接続ログ 2026-10-19）。

【仮説（測る前に固定）】
Q171 の PBO 0.88 から、順位表は上位ほど悪い（Spearman(j, L(j)) > 0）と予想し、Wang の Corollary 1 より
幅を広げるほど選んだものの翌年は悪くなる（D(60) − D(1) < 0）と予想する。

【データ】15銘柄 data_<SYM>_D1_fromH1.csv（Q139 と同じ読み込み・同じコスト段階1）。

【定義（1通り）】
- 候補: TSMOM L ∈ {5,10,…,300}（60本）。日次純損益は Q139 の pnl_matrix と同一。
- セル = (銘柄, 選択年 t)。t と t+1 の両方で 60 本すべてが MIN_DAYS=100 以上定義されるセルだけ。
- 順位 j: 年 t の純損益の降順（j=1 が最良、同点は L の小さい順）。
- L(j) = 順位 j の候補の翌年 t+1 の純損益 [bp/日] のセル平均。年単位: 年ごとに銘柄平均 → 年数で SE。
- 幅 W ∈ {1,2,4,8,16,32,60}: 60 本からランダムに W 本を引き最良を選ぶ。選ばれる順位が j である確率
  w_W(j) = C(60−j, W−1) / C(60, W)（Wang Prop.1 の超幾何の重み）。D(W) = Σ_j w_W(j)·(翌年の順位 j の純損益)。
  報告 Rep(W) = Σ_j w_W(j)·(年 t の順位 j の純損益)、過大 R(W) = Rep(W) − D(W)。
- 判定量: Δ = D(60) − D(1)（= 翌年の順位1 − 翌年の60本平均）、年単位の t。Spearman(j, L(j))（60点）。

【判定（事前固定・変更禁止）】期間: 前半（t<2017）／後半（t≥2017）。全15銘柄。
- 支持（幅が選択を悪くする）: 前後半とも Δ<0 かつ年単位 t ≤ −2、かつ前後半とも Spearman(j,L(j)) > 0。
- 棄却（幅は害さない）: 前後半とも Δ ≥ 0。
- ほかは未確定。R(W) が W で増えることは Q139 で既知なので判定に使わない。
- 記述: W ごとの選ばれた L の加重中央値・年あたり売買回数（BT-3 のコストの経路）。FX8／トレンド7 の内訳。
- 帰無（記述・z）: Q139 と同じ年内並べ替え（翌年の価格の日次リターンを暦年内で並べ替え、選択は実データ）。B=300。

【捨てた案の数】約4: 幅を固定の先頭 W 本にする案（Q139 と同じになる → Wang のランダム部分集合）、
Sharpe で順位を付ける案（純損益の平均が Q139 と揃う）、Δ を W=32 で測る案（60 が Wang の全幅）、
Spearman を上位10順位だけで取る案（事前の行は60点）。
【知識の締め切り】Claude はおよそ 2026-06。データは 2026-07 まで。L(j) の形は特定年の相場観では作れない。
【委託の確かめ方】設計: Opus（Q325-C1）。コードと実行: Opus（本セッション、Q139 のコードを写した）。委託なし。
【事前登録からの変更点】なし。
"""
import argparse, datetime as _dt, json, math, os, unicodedata, warnings
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

def _p(*parts):
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])

DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
OUT = os.path.join(HERE, "results")
FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
TREND7 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL", "US500", "USTECH", "BTCUSD"]
SYMS = FX8 + TREND7
COST_RT = {"EURUSD": .0002, "GBPUSD": .0002, "AUDUSD": .0002, "USDCHF": .0002, "USDCAD": .0002,
           "USDJPY": .02, "EURJPY": .02, "GBPJPY": .02, "XAUUSD": 0.6,
           "XAGUSD": 0.04, "WTI": 0.06, "UKOIL": 0.06, "US500": 1.0, "USTECH": 3.0, "BTCUSD": 40.0}
LS = list(range(5, 305, 5)); NC = len(LS)
WS_ = [1, 2, 4, 8, 16, 32, 60]
MIN_DAYS = 100; SPLIT_YEAR = 2017; SEED = 20261019

def weights(W, N=NC):
    return np.array([math.comb(N - j, W - 1) / math.comb(N, W) for j in range(1, N + 1)])
WGT = {W: weights(W) for W in WS_}

def spearman(x, y):
    x = pd.Series(np.asarray(x, float)).rank().values; y = pd.Series(np.asarray(y, float)).rank().values
    x -= x.mean(); y -= y.mean(); return float((x * y).sum() / math.sqrt((x**2).sum() * (y**2).sum()))

def mean_t(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]; n = len(v)
    if n < 2: return float("nan"), float("nan"), n
    s = v.std(ddof=1); return float(v.mean()), float(v.mean() / (s / math.sqrt(n))) if s > 0 else float("nan"), n

def load_daily(sym):
    d = pd.read_csv(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"), parse_dates=["time"])
    return d[(d.high > d.low) & (d.close > 0)].sort_values("time").drop_duplicates("time").reset_index(drop=True)

def pnl_matrix(c, cost_rt):
    n = len(c); ret = np.zeros(n); ret[1:] = c[1:] / c[:-1] - 1.0
    cost_bp = np.zeros(n); cost_bp[1:] = (cost_rt / 2.0) / c[:-1] * 1e4
    M = np.full((n, NC), np.nan); T = np.zeros((n, NC))
    for j, L in enumerate(LS):
        s = np.full(n, np.nan); s[L:] = np.sign(c[L:] - c[:-L])
        pos_prev = np.concatenate([[np.nan], s[:-1]]); pp = np.where(np.isfinite(pos_prev), pos_prev, 0.0)
        dpos = np.abs(np.diff(np.concatenate([[0.0], pp])))
        pnl = pp * ret * 1e4 - dpos * cost_bp; pnl[:L + 1] = np.nan
        M[:, j] = pnl; T[:, j] = np.where(np.isfinite(pnl), dpos > 0, 0)
    return M, T

def yearly(M, T, years):
    ys = np.unique(years); P = np.full((len(ys), NC), np.nan); TR = np.full((len(ys), NC), np.nan)
    for i, y in enumerate(ys):
        sub = M[years == y]; cnt = np.isfinite(sub).sum(0); ok = cnt >= MIN_DAYS
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning); mu = np.nanmean(sub, 0)
        P[i] = np.where(ok, mu, np.nan); TR[i] = np.where(ok, T[years == y].sum(0), np.nan)
    return ys, P, TR

def shuffled(c, years, rng):
    r = np.zeros(len(c)); r[1:] = np.log(c[1:] / c[:-1]); r2 = r.copy()
    for y in np.unique(years):
        idx = np.flatnonzero(years == y); idx = idx[idx >= 1]
        if len(idx) > 1: r2[idx] = r[rng.permutation(idx)]
    return np.exp(np.log(c[0]) + np.cumsum(r2))

def cells(sym, ys, P, TR, Pn=None):
    Pn = P if Pn is None else Pn; out = []
    for i in range(len(ys) - 1):
        if ys[i + 1] != ys[i] + 1: continue
        if not (np.isfinite(P[i]).all() and np.isfinite(Pn[i + 1]).all()): continue
        order = np.lexsort((np.arange(NC), -P[i]))       # 降順・同点は L の小さい順
        out.append(dict(sym=sym, year=int(ys[i]), ins=P[i][order], oos=Pn[i + 1][order],
                        Lrank=np.array(LS)[order], tr=TR[i][order]))
    return out

def summarize(cl, syms, per):
    g = [c for c in cl if c["sym"] in syms and (per == "全期間" or (per == "前半") == (c["year"] < SPLIT_YEAR))]
    if not g: return None
    yrs = np.array([c["year"] for c in g]); OOS = np.stack([c["oos"] for c in g]); INS = np.stack([c["ins"] for c in g])
    def ymean(v):
        s = pd.Series(v).groupby(yrs).mean(); return s.values
    Lj = OOS.mean(0); Lj_t = [mean_t(ymean(OOS[:, j]))[1] for j in range(NC)]
    res = dict(n_cells=len(g), n_years=int(len(np.unique(yrs))), L_j=Lj.tolist(), L_j_year_t=Lj_t,
               spearman_j_L=spearman(np.arange(1, NC + 1), Lj),
               L_top5=float(Lj[:5].mean()), L_mid=float(Lj[20:40].mean()), L_bottom5=float(Lj[-5:].mean()))
    D = {}
    for W in WS_:
        w = WGT[W]; d = OOS @ w; rep = INS @ w
        Lsel = np.stack([c["Lrank"] for c in g]).ravel(); ww = np.tile(w, len(g)) / len(g)
        o = np.argsort(Lsel); cw = np.cumsum(ww[o]); medL = float(Lsel[o][np.searchsorted(cw, 0.5)])
        TRm = np.stack([c["tr"] for c in g]); trades = float((TRm @ w).mean())
        m, t, ny = mean_t(ymean(d))
        D[W] = dict(D=float(d.mean()), D_year_t=t, Rep=float(rep.mean()), R=float((rep - d).mean()),
                    median_L_selected=medL, trades_per_year=trades)
    delta = OOS[:, 0] - OOS.mean(1)
    dm, dt, ny = mean_t(ymean(delta))
    res.update(D=D, delta=float(delta.mean()), delta_year_mean=dm, delta_year_t=dt)
    return res

def null_delta(cl, syms, per):
    g = [c for c in cl if c["sym"] in syms and (per == "全期間" or (per == "前半") == (c["year"] < SPLIT_YEAR))]
    return float(np.mean([c["oos"][0] - c["oos"].mean() for c in g]))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=300); a = ap.parse_args()
    rng = np.random.default_rng(SEED); obs = []; nulls = [[] for _ in range(a.B)]; used = []; missing = []
    for sym in SYMS:
        try: d = load_daily(sym)
        except FileNotFoundError: missing.append(sym); continue
        used.append(sym); c = d.close.values.astype(float); years = d.time.dt.year.values
        M, T = pnl_matrix(c, COST_RT[sym]); ys, P, TR = yearly(M, T, years)
        obs += cells(sym, ys, P, TR)
        for b in range(a.B):
            c2 = shuffled(c, years, rng); M2, T2 = pnl_matrix(c2, COST_RT[sym]); _, P2, _ = yearly(M2, T2, years)
            nulls[b] += cells(sym, ys, P, TR, P2)
        print(sym, "done", flush=True)
    groups = {"全15": SYMS, "FX8": FX8, "トレンド7": TREND7}; res = {}
    for gn, syms in groups.items():
        for per in ("前半", "後半", "全期間"):
            r = summarize(obs, syms, per)
            nd = [null_delta(n, syms, per) for n in nulls] if a.B else []
            nd = np.array(nd)
            if len(nd) > 9:
                r["null_delta_mean"] = float(nd.mean()); r["null_delta_p2.5_97.5"] = [float(np.percentile(nd, 2.5)), float(np.percentile(nd, 97.5))]
                r["z_delta_vs_null"] = float((r["delta"] - nd.mean()) / nd.std(ddof=1)); r["pct_delta_vs_null"] = float((nd < r["delta"]).mean())
            res[f"{gn}|{per}"] = r
    f, s = res["全15|前半"], res["全15|後半"]
    sup = all(x["delta"] < 0 and x["delta_year_t"] <= -2 and x["spearman_j_L"] > 0 for x in (f, s))
    rej = all(x["delta"] >= 0 for x in (f, s))
    verdict = "支持（幅が選択を悪くする）" if sup else ("棄却（幅は害さない）" if rej else "未確定")
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dict(question="Q326", used=used, missing=missing, B=a.B, weights_check={W: float(WGT[W].sum()) for W in WS_},
               verdict=verdict, by_period={p: dict(delta=res[f"全15|{p}"]["delta"], delta_year_t=res[f"全15|{p}"]["delta_year_t"],
                                                   spearman=res[f"全15|{p}"]["spearman_j_L"]) for p in ("前半", "後半")},
               results=res)
    p = os.path.join(OUT, f"Q326_result_{stamp}.json")
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1, default=float); print("verdict:", verdict); print(p)

if __name__ == "__main__":
    main()
