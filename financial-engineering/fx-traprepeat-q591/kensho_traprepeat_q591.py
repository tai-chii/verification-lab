# -*- coding: utf-8 -*-
"""Q591 MT5 の銘柄のトラリピ 3 型（F1 レンジ通貨ペアの半々・F2 スワップの片側・F3 トレンド方向の片側）。事前登録: 事前登録_q591.md（変更禁止）。
【判定】フォワード候補: PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または全期間平均 ≤ 0。それ以外: 未確定。
【多重比較】トラリピ・グリッドの族で 5 本目。判定は 3 本。
使い方（Mac）: 作業層/venv_grid/bin/python kensho_traprepeat_q591.py [--smoke] [--B 200]"""
import argparse, datetime, glob, json, os, sys, time
import numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(FE, "..", "tools"))
import composite_gate as G
XM = glob.glob(os.path.join(WS, "作業層", "大容量", "market_data_xm", "mt5_data", "*"))[0]
RATES = os.path.join(WS, "検証", "_データ", "raw", "rates")
START, SEAL = pd.Timestamp("2010-01-01", tz="UTC"), pd.Timestamp("2024-07-01", tz="UTC")
EVAL, SPLIT = "2011-01-01", "2017-01-01"
FX14 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"]
CR5 = ["AUDNZD", "AUDCAD", "NZDCAD", "EURCHF", "CADCHF"]; CFD5 = ["XAUUSD", "US500", "USTECH", "GER40", "JPN225"]
FAM = {"F1": ["AUDNZD", "AUDCAD", "NZDCAD", "EURCHF", "CADCHF", "EURGBP"], "F2": FX14 + CR5, "F3": FX14 + CR5 + CFD5}
K, N, L, MARKUP, ATRW, SMAW, LAM = 1.0, 10, 60, 0.0075, 20, 250, 0.97
DAY, H2 = 86400 * 10**9, 2 * 3600 * 10**9


def digits(x):
    s = x[-2000:]
    for d in range(0, 7):
        if np.all(np.abs(s * 10**d - np.round(s * 10**d)) < 1e-6): return d      # 2026-10-31 修正: allclose の相対許容差で指数の桁を 1 少なく判定していた
    return 5


LEGS = {"AUDNZD": ("AUDUSD", "NZDUSD", -1), "AUDCAD": ("AUDUSD", "USDCAD", 1), "NZDCAD": ("NZDUSD", "USDCAD", 1), "EURCHF": ("EURUSD", "USDCHF", 1), "CADCHF": ("USDCHF", "USDCAD", -1), "EURGBP_SYN": ("EURUSD", "GBPUSD", -1)}


def read_xm(s):
    d = pd.read_parquet(os.path.join(XM, "H1", f"{s}.parquet"), columns=["time", "open", "high", "low", "close"])
    return d[(d["time"] >= START) & (d["time"] < SEAL)].sort_values("time").drop_duplicates("time").reset_index(drop=True)   # 封印済み: time < SEAL


def pack(s, d):
    t = d["time"].dt.tz_convert(None).to_numpy().astype("datetime64[ns]").astype(np.int64)
    return dict(sym=s, o=d["open"].to_numpy(float), h=d["high"].to_numpy(float), l=d["low"].to_numpy(float), c=d["close"].to_numpy(float), tday=(t + H2) // DAY)


def load_sym(s):
    if s not in LEGS: return pack(s, read_xm(s))
    a, b, e = LEGS[s]; m = read_xm(a).merge(read_xm(b), on="time", suffixes=("_a", "_b")).sort_values("time").reset_index(drop=True)
    o = m["open_a"] * m["open_b"] ** e; c = m["close_a"] * m["close_b"] ** e       # 足の中の高安は合成できない → 実体だけ（保守的）
    return pack(s, pd.DataFrame({"time": m["time"], "open": o, "close": c, "high": np.maximum(o, c), "low": np.minimum(o, c)}))


def duka_rel(s):
    q = pd.read_csv(os.path.join(WS, "検証", "_データ", "raw", "D1", f"spread_{s}.csv"), parse_dates=["time"])   # 封印済み: 次の行で time < 2024-07-01
    q = q[(q["time"] >= "2021-01-01") & (q["time"] < "2024-07-01")]   # 封印済み: time < 2024-07-01
    return float(np.median(q["spread"].to_numpy(float) / q["bid_close"].to_numpy(float)))


def cost_table():
    p = os.path.join(HERE, "results", "cost_table.json")
    if os.path.exists(p): return json.load(open(p, encoding="utf-8"))
    A = pd.Timestamp("2021-01-01", tz="UTC"); rel = {}; ratio = []
    for s in FX14 + CFD5:
        m = pd.read_parquet(os.path.join(XM, "M1", f"{s}.parquet"), columns=["time", "close", "spread"])
        m = m[(m["time"] >= A) & (m["time"] < SEAL)]   # 封印済み: time < SEAL
        d = digits(m["close"].to_numpy(float)); rel[s] = float(np.median(m["spread"].to_numpy(float) * 10.0**-d / m["close"].to_numpy(float)))
        f = os.path.join(WS, "検証", "_データ", "raw", "D1", f"spread_{s}.csv")
        if s in FX14 and os.path.exists(f): ratio.append(rel[s] / duka_rel(s))
    mult = float(np.median(ratio)); legsum = lambda s: rel[LEGS[s][0]] + rel[LEGS[s][1]]
    for s in ("AUDNZD", "AUDCAD", "EURCHF"): rel[s] = duka_rel(s) * mult
    r = float(np.median([rel[s] / legsum(s) for s in ("AUDNZD", "AUDCAD", "EURCHF")]))
    for s in ("NZDCAD", "CADCHF"): rel[s] = legsum(s) * r
    rel["EURGBP_SYN"] = rel["EURGBP"]
    out = dict(rel=rel, xm_over_duka=mult, n_ratio=len(ratio), cross_over_legs=r, digits_note="XM の spread は銘柄の最小桁の整数")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); return out


def rate_series():
    R = {}
    for f in glob.glob(os.path.join(RATES, "policy_*.csv")):
        c = os.path.basename(f)[7:10]; d = pd.read_csv(f, parse_dates=["date"]).dropna().sort_values("date")
        R[c] = (d["date"].to_numpy().astype("datetime64[D]").astype(np.int64), d["policy_rate_pct"].to_numpy(float) / 100.0)
    return R


def rate_at(R, c, days):
    x, y = R[c]; i = np.searchsorted(x, days - 1, side="right") - 1      # t−1 暦日までの値
    return y[np.clip(i, 0, len(y) - 1)]


@njit(cache=True)
def daily(bar, D, o, h, l, c):
    dO = np.full(D, np.nan); dH = np.full(D, -np.inf); dL = np.full(D, np.inf); dC = np.full(D, np.nan)
    for i in range(len(bar)):
        d = bar[i]
        if np.isnan(dO[d]): dO[d] = o[i]
        if h[i] > dH[d]: dH[d] = h[i]
        if l[i] < dL[d]: dL[d] = l[i]
        dC[d] = c[i]
    return dO, dH, dL, dC


@njit(cache=True)
def sim(o, h, l, c, bar, D, mode, reset, atr, anc, k, Nn, touch, crel, swl, sws, nights):
    """mode[d]: +1 買いのみ・−1 売りのみ・2 半々・0 持たない。戻り値: 日次の累積（コスト前の値動き・コスト・スワップ）・約定回数・保有本数の日平均"""
    M = 2 * Nn + 2
    act = np.zeros(M, np.bool_); sd = np.zeros(M, np.int8); lv = np.zeros(M, np.int64); en = np.zeros(M); ob = np.zeros(M, np.int64)
    eqg = np.zeros(D); cumc = np.zeros(D); cums = np.zeros(D); hold = np.zeros(D)
    real = 0.0; cost = 0.0; swp = 0.0; A = 0.0; st = 0.0; ref = 1.0; cur = 0; pd_ = -1; nf = 0; cnt = 0; ndone = np.zeros(M, np.int64)
    for b in range(len(o)):
        d = bar[b]
        if d != pd_:
            if pd_ >= 0:
                for j in range(M):
                    if act[j]: swp += (swl[d] if sd[j] > 0 else sws[d]) * nights[d]
            m = int(mode[d])
            if reset[d] or m != cur:
                for j in range(M):
                    if act[j]:
                        real += sd[j] * (o[b] - en[j]) / ref; cost += crel * o[b] / 2 / ref; act[j] = False; nf += 1
                cnt = 0; cur = 0
                base = anc[d] if m == 2 else o[b]
                if m != 0 and atr[d] > 0 and base == base:
                    cur = m; A = base; st = k * atr[d]; ref = o[b]
            pd_ = d
        if cur != 0:
            nd = 0
            for j in range(M):          # 利確（同じ足で建てたものは対象外）
                if act[j] and ob[j] < b:
                    if sd[j] > 0:
                        tp = A + (lv[j] + 1) * st
                        if h[b] >= tp:
                            px = max(tp, o[b]); real += (px - en[j]) / ref; cost += crel * px / 2 / ref; act[j] = False; cnt -= 1; nf += 1; ndone[nd] = lv[j]; nd += 1
                    else:
                        tp = A + (lv[j] - 1) * st
                        if l[b] <= tp:
                            px = min(tp, o[b]); real += (en[j] - px) / ref; cost += crel * px / 2 / ref; act[j] = False; cnt -= 1; nf += 1; ndone[nd] = lv[j]; nd += 1
            if cur == 2:
                for q in range(1, Nn + 1):
                    for s_ in (1, -1):
                        ll = -q * s_; p = A + ll * st
                        if l[b] <= p <= h[b]:
                            f = False
                            for j in range(M):
                                if act[j] and lv[j] == ll: f = True
                            for j in range(nd):
                                if ndone[j] == ll: f = True
                            if not f:
                                for j in range(M):
                                    if not act[j]:
                                        act[j] = True; sd[j] = s_; lv[j] = ll; en[j] = p; ob[j] = b; cost += crel * p / 2 / ref; cnt += 1; nf += 1; break
            else:
                pc = c[b - 1] if b > 0 and bar[b - 1] == d else o[b]
                pc = max(pc, o[b]) if cur > 0 else min(pc, o[b])
                ll = int(np.floor((pc - A) / st + 1e-12)) if cur > 0 else int(np.ceil((pc - A) / st - 1e-12))
                while cnt < Nn:
                    p = A + ll * st
                    if (cur > 0 and p < l[b]) or (cur < 0 and p > h[b]): break
                    f = False
                    for j in range(M):
                        if act[j] and lv[j] == ll: f = True
                    for j in range(nd):
                        if ndone[j] == ll: f = True
                    if not f:
                        e = min(p, o[b]) if cur > 0 else max(p, o[b])
                        for j in range(M):
                            if not act[j]:
                                act[j] = True; sd[j] = cur; lv[j] = ll; en[j] = e; ob[j] = b; cost += crel * e / 2 / ref; cnt += 1; nf += 1; break
                    ll += -1 if cur > 0 else 1
        if b == len(o) - 1 or bar[b + 1] != d:
            un = 0.0
            for j in range(M):
                if act[j]: un += sd[j] * (c[b] - en[j]) / ref
            eqg[d] = real + un; cumc[d] = cost; cums[d] = swp; hold[d] = cnt
    return eqg, cumc, cums, nf, hold


def prep(x, days_all=None):
    days, bar = np.unique(x["tday"], return_inverse=True); D = len(days); bar = bar.astype(np.int64)
    dO, dH, dL, dC = daily(bar, D, x["o"], x["h"], x["l"], x["c"])
    pc = np.r_[np.nan, dC[:-1]]; tr = np.nanmax(np.c_[dH - dL, np.abs(dH - pc), np.abs(dL - pc)], axis=1)
    atr = pd.Series(tr).rolling(ATRW, min_periods=ATRW).mean().shift(1).to_numpy()
    sma = pd.Series(dC).rolling(SMAW, min_periods=SMAW).mean().shift(1).to_numpy()
    c1 = pd.Series(dC).shift(1); trend = np.sign((c1 - c1.shift(L)).to_numpy()); trend = np.nan_to_num(trend).astype(np.int64)
    yr = (days.astype("datetime64[D]").astype("datetime64[Y]").astype(np.int64)); reset = np.r_[False, yr[1:] != yr[:-1]]
    nights = np.r_[1, np.diff(days)].astype(np.int64)
    return dict(days=days, bar=bar, D=D, atr=atr, sma=sma, trend=trend, reset=reset, nights=nights)


def swaps(s, days, R):
    if s in CFD5: return np.full(len(days), -0.04), np.full(len(days), -0.01)
    b, q = rate_at(R, s[:3], days), rate_at(R, s[3:6], days)
    return b - q - MARKUP, q - b - MARKUP


def run(fam, x, p, swl, sws, crel, k=K):
    D = p["D"]; none = np.zeros(D, bool)
    if fam == "F1": mode = np.full(D, 2, np.int64); mode[~(p["sma"] > 0)] = 0; reset = p["reset"]
    elif fam == "F2": mode = np.where(swl > 0, 1, np.where(sws > 0, -1, 0)).astype(np.int64); reset = p["reset"]
    else: mode = p["trend"]; reset = none
    return sim(x["o"], x["h"], x["l"], x["c"], p["bar"], D, mode, reset, p["atr"], p["sma"], k, N, fam == "F1", crel, swl / 365.0, sws / 365.0, p["nights"])


def to_df(res, days):
    eqg, cc, cs, nf, hold = res; idx = pd.DatetimeIndex(days.astype("datetime64[D]"))
    return pd.DataFrame({"g": eqg, "c": cc, "s": cs}, index=idx).diff().fillna(0.0) / N, nf, pd.Series(hold, index=idx)


def nw(x, lag=21):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); e = x - x.mean(); s = e @ e
    for k in range(1, lag + 1): s += 2 * (1 - k / (lag + 1)) * (e[:-k] @ e[k:])
    return float(x.mean() / np.sqrt(s / n / n)) if s > 0 else float("nan")


def ty(x, md=120):
    g = x.groupby(x.index.year); y = g.sum()[g.size() >= md]
    return float(y.mean() / y.std(ddof=1) * np.sqrt(len(y))) if len(y) >= 3 and y.std(ddof=1) > 0 else float("nan")


def stats(x):
    x = x[x.index >= EVAL]; a, b = x[x.index < SPLIT], x[x.index >= SPLIT]; eq = x.cumsum(); p = x[x > 0].sum(); n = -x[x < 0].sum()
    return dict(mean_bp=1e4 * float(x.mean()), t_nw=nw(x), sharpe=float(x.mean() / x.std() * np.sqrt(252)), pf=float(p / n) if n > 0 else float("nan"), h1_bp=1e4 * float(a.mean()), h2_bp=1e4 * float(b.mean()),
                h1_ty=ty(a), h2_ty=ty(b), maxdd_pct=100 * float((eq - eq.cummax()).min()), worst_year_pct=100 * float(x.groupby(x.index.year).sum().min()), by_year_pct={str(y): round(100 * float(v), 2) for y, v in x.groupby(x.index.year).sum().items()})


def fam_series(fam, data, R, ct, k=K, cm=1.0):
    fr = {}; nf = 0; hold = []
    for s in FAM[fam]:
        x, p = data[s]; swl, sws = swaps(s, p["days"], R)
        d, n_, h = to_df(run(fam, x, p, swl, sws, ct["rel"][s] * cm, k), p["days"])
        fr[s] = d; nf += n_; hold.append(h)
    g = pd.DataFrame({s: v["g"] for s, v in fr.items()}); c = pd.DataFrame({s: v["c"] for s, v in fr.items()}); w = pd.DataFrame({s: v["s"] for s, v in fr.items()})
    return pd.DataFrame({"gross": g.mean(axis=1), "cost": c.mean(axis=1), "swap": w.mean(axis=1)}), g, nf, pd.concat(hold, axis=1, sort=True).mean(axis=1), c, w


def synth(x, rng, sig):
    o, h, l, c = x["o"], x["h"], x["l"], x["c"]; r = np.r_[0.0, np.diff(np.log(c))]
    # 2026-10-31 修正: 値動きのほぼ無い足で σ が極端に小さくなり z が暴れて偽の系列が発散した（F2・F3 の帰無が 6,718bp・−inf）→ σ に下限（銘柄の中央値の 1/4）・±8σ で切る
    sig = np.maximum(sig, 0.25 * np.median(sig))
    z = np.clip(r / sig, -8, 8); up = np.clip((h - np.maximum(o, c)) / c / sig, 0, 8); dn = np.clip((np.minimum(o, c) - l) / c / sig, 0, 8)
    yr = x["yr"]; rr = r.copy(); u2, d2 = up.copy(), dn.copy()
    for y in np.unique(yr):
        i = np.where(yr == y)[0]; pm = rng.permutation(len(i)); a = z[i][pm] * sig[i]; rr[i] = a + (r[i].sum() - a.sum()) / len(i); u2[i] = up[i][pm]; d2[i] = dn[i][pm]
    c2 = c[0] * np.exp(np.cumsum(rr)); o2 = np.r_[o[0], c2[:-1]]
    return dict(sym=x["sym"], o=o2, c=c2, h=np.maximum(o2, c2) * (1 + u2 * sig), l=np.minimum(o2, c2) * (1 - d2 * sig), tday=x["tday"], yr=yr)


def add_sig(x):
    r = np.r_[0.0, np.diff(np.log(x["c"]))]; v = pd.Series(r ** 2).ewm(alpha=1 - LAM, adjust=False).mean().shift(1).bfill().to_numpy()
    x["sig"] = np.sqrt(np.maximum(v, 1e-12)); x["yr"] = (x["tday"].astype("datetime64[D]").astype("datetime64[Y]").astype(np.int64)); return x


def tsmom(data, R, ct):
    out = {}
    for s in FAM["F3"]:
        x, p = data[s]; dO, dH, dL, dC = daily(p["bar"], p["D"], x["o"], x["h"], x["l"], x["c"]); pos = p["trend"].astype(float)
        ret = np.r_[0.0, dC[1:] / dC[:-1] - 1]; swl, sws = swaps(s, p["days"], R)
        pnl = pos * ret + np.where(pos > 0, swl, np.where(pos < 0, sws, 0.0)) / 365 * p["nights"] - np.abs(np.r_[0.0, np.diff(pos)]) * ct["rel"][s] / 2
        out[s] = pd.Series(pnl, index=pd.DatetimeIndex(p["days"].astype("datetime64[D]")))
    return pd.DataFrame(out).mean(axis=1)


def verdict(s, z, c):
    if s["pf"] >= 1.05 and s["t_nw"] >= 1.5 and s["h1_bp"] > 0 and s["h2_bp"] > 0 and z >= 1.5 and c["関門"]["通過"]: return "フォワード候補"
    if z < 1 or s["mean_bp"] <= 0: return "棄却"
    return "未確定"


def smoke():
    """本物の連続経路（算術の酔歩を 1 足 20 刻み）から OHLC を作る。経路と無関係にヒゲを足すと嘘の有利が入るので使わない（2026-10-31 に確認）。"""
    rng = np.random.default_rng(1); out = {}
    for fam in ("F1", "F2", "F3"):
        ms = []; ms2 = []
        for r_ in range(40):
            n = 12000; st = 20; w = 100.0 + np.cumsum(rng.normal(0, 0.03, n * st)); w = np.maximum(w, 20.0).reshape(n, st)
            c = w[:, -1]; o = np.r_[100.0, c[:-1]]; h = np.maximum(w.max(axis=1), o); l = np.minimum(w.min(axis=1), o)
            x = dict(sym="SYN", o=o, c=c, h=h, l=l, tday=(np.arange(n) // 24) + 14000)
            p = prep(x); sw = np.zeros(p["D"])
            lg, sh = (np.full(p["D"], 1e-12), np.full(p["D"], -1.0)) if fam == "F2" else (sw, sw)
            d, nf, hd = to_df(run(fam, x, p, lg, sh, 0.0), p["days"]); ms.append(1e4 * d["g"].iloc[300:].mean())
        ms = np.array(ms); out[fam] = dict(mean_bp=round(float(ms.mean()), 3), se=round(float(ms.std(ddof=1) / np.sqrt(len(ms))), 3))
    print("算術の酔歩・本物の経路・コスト 0・スワップ 0 の平均 bp/日（0 に近いはず）:", out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=200); ap.add_argument("--seed", type=int, default=20261031); a = ap.parse_args()
    if a.smoke: smoke(); return
    t0 = time.time(); ct = cost_table(); R = rate_series(); data = {}
    for s in sorted(set(sum(FAM.values(), []))):
        x = add_sig(load_sym(s)); data[s] = (x, prep(x))
    res = dict(qid="Q591", config=dict(K=K, N=N, L=L, markup=MARKUP, atr=ATRW, sma=SMAW, seal=str(SEAL.date()), eval=EVAL, split=SPLIT), xm_over_duka=ct["xm_over_duka"], rel_spread_bp={k: round(1e4 * v, 2) for k, v in ct["rel"].items()}, fam={})
    rng = np.random.default_rng(a.seed); days = {}
    xs = add_sig(load_sym("EURGBP_SYN")); ps = prep(xs); rx, px = data["EURGBP"]
    fs, _, _ = to_df(run("F1", xs, ps, *swaps("EURGBP", ps["days"], R), ct["rel"]["EURGBP"]), ps["days"]); fr_, _, _ = to_df(run("F1", rx, px, *swaps("EURGBP", px["days"], R), ct["rel"]["EURGBP"]), px["days"])
    a1 = (fs["g"] - fs["c"] + fs["s"]); a2 = (fr_["g"] - fr_["c"] + fr_["s"]); ix = a1.index.intersection(a2.index); ix = ix[ix >= EVAL]
    res["合成の確かめ_EURGBP"] = dict(corr=float(a1[ix].corr(a2[ix])), synth_bp=1e4 * float(a1[ix].mean()), real_bp=1e4 * float(a2[ix].mean()), n=int(len(ix)))
    print("EURGBP 合成の確かめ", res["合成の確かめ_EURGBP"], flush=True)
    print("コスト bp", {k: round(1e4 * v, 2) for k, v in ct["rel"].items()}, "XM/Duka", round(ct["xm_over_duka"], 2), "クロス/組", round(ct["cross_over_legs"], 2), flush=True)
    for fam in FAM:
        S, g, nf, hold, c_, w_ = fam_series(fam, data, R, ct); net = S["gross"] - S["cost"] + S["swap"]
        st = stats(net); yrs = (net[net.index >= EVAL].index[-1] - pd.Timestamp(EVAL)).days / 365.25
        dec = dict(stats=st, cost_before_bp=1e4 * float(S["gross"][S.index >= EVAL].mean()), no_swap=stats(S["gross"] - S["cost"]), gross_swap=stats(S["gross"] + S["swap"]), swap_bp=1e4 * float(S["swap"][S.index >= EVAL].mean()), cost_bp=1e4 * float(S["cost"][S.index >= EVAL].mean()),
                   fills_per_year=nf / yrs, hold_mean=float(hold[hold.index >= EVAL].mean()), by_sym_bp={s: round(1e4 * float((g[s] - c_[s] + w_[s])[g.index >= EVAL].mean()), 3) for s in g})
        dec["cost_quarter"] = stats(S["gross"] - S["cost"] / 4 + S["swap"])
        dec["k"] = {str(k): {q: stats(v["gross"] - v["cost"] + v["swap"])[q] for q in ("mean_bp", "t_nw", "sharpe", "pf")} for k, v in ((k, fam_series(fam, data, R, ct, k)[0]) for k in (0.5, 2.0))}
        dec["composite"] = G.gate(net[net.index >= EVAL], fam)
        vals = []
        for i in range(a.B):
            fr = []
            for s in FAM[fam]:
                x = synth(data[s][0], rng, data[s][0]["sig"]); p = prep(x); swl, sws = swaps(s, p["days"], R)
                d, _, _ = to_df(run(fam, x, p, swl, sws, ct["rel"][s]), p["days"]); fr.append(d["g"] - d["c"] + d["s"])
            m = pd.concat(fr, axis=1, sort=True).mean(axis=1); vals.append(float(m[m.index >= EVAL].mean()))
            if (i + 1) % 25 == 0: print(datetime.datetime.now().strftime("%H:%M:%S"), fam, "帰無", i + 1, "/", a.B, flush=True)
        vals = np.array(vals); obs = float(net[net.index >= EVAL].mean()); dec["null"] = dict(B=a.B, null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(vals.std()), z=float((obs - vals.mean()) / vals.std()), p=float((vals >= obs).mean()))
        dec["verdict"] = verdict(st, dec["null"]["z"], dec["composite"]); res["fam"][fam] = dec; days[fam] = net
        json.dump(res, open(os.path.join(HERE, "results", "result_q591.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
        print(fam, "判定", dec["verdict"], {k: round(st[k], 3) for k in ("mean_bp", "t_nw", "sharpe", "pf", "h1_bp", "h2_bp", "maxdd_pct")}, "z", round(dec["null"]["z"], 2), flush=True)
    tm = tsmom(data, R, ct); res["tsmom60_ref"] = dict(stats=stats(tm), corr_F3=float(tm[tm.index >= EVAL].corr(days["F3"].reindex(tm.index)[tm.index >= EVAL])))
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); res["elapsed_s"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(HERE, "results", "result_q591.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    pd.DataFrame(days).to_csv(os.path.join(HERE, "results", "daily_q591.csv"))


if __name__ == "__main__":
    main()
