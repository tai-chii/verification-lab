# -*- coding: utf-8 -*-
"""Q593 CFTC 建玉の横断（A 水準・B 変化の逆張り）。事前登録: 事前登録_q593.md（変更禁止）。
【判定】フォワード候補: PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または全期間平均 ≤ 0。それ以外: 未確定。
【多重比較】判定は 2 本。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_cot_q593.py [--B 500]"""
import argparse, datetime, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(FE, "..", "tools"))
from fe_core import load_d1
import composite_gate as G

COT = os.path.join(WS, "作業層", "大容量", "cot", "cot_legacy.parquet"); RATES = os.path.join(WS, "検証", "_データ", "raw", "rates"); D1S = os.path.join(WS, "検証", "_データ", "raw", "D1")
REAL = json.load(open(os.path.join(FE, "fx-traprepeat-q591", "results", "swap_real_q591.json"), encoding="utf-8"))["実スワップの換算"]
CT = json.load(open(os.path.join(FE, "fx-traprepeat-q591", "results", "cost_table.json"), encoding="utf-8"))
MAP = {"EURUSD": ("099741", 1), "GBPUSD": ("096742", 1), "AUDUSD": ("232741", 1), "NZDUSD": ("112741", 1), "USDJPY": ("097741", -1), "USDCHF": ("092741", -1), "USDCAD": ("090741", -1),
       "US500": ("13874A", 1), "USTECH": ("209742", 1), "US30": ("124603", 1), "JPN225": ("240741", 1), "XAUUSD": ("088691", 1), "XAGUSD": ("084691", 1), "XPTUSD": ("076651", 1), "XPDUSD": ("075651", 1), "WTI": ("067651", 1), "NATGAS": ("023651", 1)}
GROUP = {**{s: "FX" for s in list(MAP)[:7]}, **{s: "指数" for s in ("US500", "USTECH", "US30", "JPN225")}, **{s: "金属" for s in ("XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD")}, "WTI": "エネルギー", "NATGAS": "エネルギー"}
CFD = {"US500": ("US500", "USD"), "USTECH": ("USTECH", "USD"), "US30": ("US500", "USD"), "JPN225": ("JPN225", "JPY"), "XAUUSD": ("XAUUSD", "USD"), "XAGUSD": ("XAUUSD", "USD"), "XPTUSD": ("XAUUSD", "USD"), "XPDUSD": ("XAUUSD", "USD")}
EVAL, SPLIT = pd.Timestamp("2012-01-01"), pd.Timestamp("2017-01-01"); WIN, MINW = 156, 104


def rate_table():
    T = {}
    for c in ("USD", "JPY", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF"):
        d = pd.read_csv(os.path.join(RATES, f"policy_{c}.csv"), parse_dates=["date"]).dropna().sort_values("date")
        T[c] = pd.Series(d["policy_rate_pct"].to_numpy(float) / 100, index=pd.DatetimeIndex(d["date"]))
    return T


def swap_rates(idx, T):
    """銘柄ごとの（買い, 売り）の年率。index は日次"""
    L, S = {}, {}
    rr = lambda c: T[c].reindex(T[c].index.union(idx)).ffill().reindex(idx).shift(1).bfill()
    for s in MAP:
        if s in ("WTI", "NATGAS"): L[s], S[s] = pd.Series(-0.04, idx), pd.Series(-0.01, idx); continue
        if s in CFD:
            k = REAL[CFD[s][0]]; d = rr(CFD[s][1]) - k["rate_now"]; L[s], S[s] = k["long"] - d, k["short"] + d; continue
        k = REAL[s]; d = rr(s[:3]) - rr(s[3:6]); L[s], S[s] = d - k["m_long"], -d - k["m_short"]
    return pd.DataFrame(L), pd.DataFrame(S)


def rel_spread():
    rel = {}
    for s in MAP:
        if s in CT["rel"]: rel[s] = CT["rel"][s]; continue
        q = pd.read_csv(os.path.join(D1S, f"spread_{s}.csv"), parse_dates=["time"])   # 封印済み: 次の行で time < 2024-07-01
        q = q[(q["time"] >= "2021-01-01") & (q["time"] < "2024-07-01")]
        rel[s] = float(np.median(q["spread"].to_numpy(float) / q["bid_close"].to_numpy(float))) * CT["xm_over_duka"]
    return rel


def signals():
    d = pd.read_parquet(COT); codes = {v[0]: k for k, v in MAP.items()}; d = d[d["code"].isin(codes)].copy(); d["sym"] = d["code"].map(codes)
    d["net"] = (d["nc_l"] - d["nc_s"]) / d["oi"]; N = d.pivot(index="date", columns="sym", values="net").sort_index()
    N = N[N.index < pd.Timestamp("2024-06-15")]                                                                              # 封印済み: 使う日が封印の前に収まるように切る
    za = (N - N.rolling(WIN, min_periods=MINW).mean()) / N.rolling(WIN, min_periods=MINW).std()
    dn = N.diff(); zb = -dn / dn.rolling(WIN, min_periods=MINW).std()
    return dict(A=za, B=zb)


def weights(Z, vol, idx, mult, shift=0):
    """週の信号 → 日次のウェイト（銘柄の向きのまま）。shift は帰無用（週を循環）。apply=火曜+6 日以降の最初の営業日の終値から"""
    W = pd.DataFrame(0.0, index=idx, columns=Z.columns); dates = Z.index; n = len(dates); arr = Z.to_numpy(); ap = idx.searchsorted(dates + pd.Timedelta(days=6)); out = []
    for i in range(n):
        if ap[i] >= len(idx): continue
        z = arr[(i - shift) % n]; v = vol.iloc[ap[i]].reindex(Z.columns).to_numpy(); ok = np.isfinite(z) & np.isfinite(v) & (v > 0)
        if ok.sum() < 10: out.append((ap[i], None)); continue
        ord_ = np.argsort(z[ok]); names = np.where(ok)[0]; q = int(ok.sum()) // 3; lo, hi = names[ord_[:q]], names[ord_[-q:]]; w = np.zeros(len(z))
        w[hi] = (1 / v[hi]) / (1 / v[hi]).sum() * 0.5; w[lo] = -(1 / v[lo]) / (1 / v[lo]).sum() * 0.5
        out.append((ap[i], w * mult))
    W = np.zeros((len(idx), Z.shape[1])); cur = np.zeros(Z.shape[1]); k = 0; out.sort(key=lambda x: x[0])
    for t in range(len(idx)):
        while k < len(out) and out[k][0] == t:
            cur = np.zeros(Z.shape[1]) if out[k][1] is None else out[k][1]; k += 1
        W[t] = cur                                                                                                            # t の終値で持ち替え → t+1 の損益から
    return pd.DataFrame(W, index=idx, columns=Z.columns)


def pnl(W, R, SL, SR, rel, nights):
    Wl = W.shift(1).fillna(0.0).to_numpy(); r = R.to_numpy(); price = np.nansum(Wl * np.nan_to_num(r), axis=1)
    swap = (np.clip(Wl, 0, None) * SL.to_numpy() + np.clip(-Wl, 0, None) * SR.to_numpy()).sum(axis=1) / 365 * nights
    dw = np.abs(W.diff().fillna(0.0).to_numpy()); cost = (dw * rel / 2).sum(axis=1)
    return pd.DataFrame({"price": price, "swap": swap, "cost": cost}, index=W.index), dw.sum(axis=1)


def nw(x, lag=21):
    x = np.asarray(x, float); e = x - x.mean(); n = len(x); s = e @ e
    for k in range(1, lag + 1): s += 2 * (1 - k / (lag + 1)) * (e[:-k] @ e[k:])
    return float(x.mean() / np.sqrt(s / n / n))


def ty(x):
    y = x.groupby(x.index.year).sum(); return float(y.mean() / y.std(ddof=1) * np.sqrt(len(y))) if len(y) >= 3 else float("nan")


def stats(x):
    x = x[x.index >= EVAL]; a, b = x[x.index < SPLIT], x[x.index >= SPLIT]; p = x[x > 0].sum(); n = -x[x < 0].sum(); eq = x.cumsum()
    return dict(mean_bp=1e4 * float(x.mean()), t_nw=nw(x), sharpe=float(x.mean() / x.std() * np.sqrt(252)), pf=float(p / n), h1_bp=1e4 * float(a.mean()), h2_bp=1e4 * float(b.mean()), h1_ty=ty(a), h2_ty=ty(b),
                maxdd_pct=100 * float((eq - eq.cummax()).min()), by_year_pct={str(y): round(100 * float(v), 2) for y, v in x.groupby(x.index.year).sum().items()})


def verdict(s, z, c):
    if s["pf"] >= 1.05 and s["t_nw"] >= 1.5 and s["h1_bp"] > 0 and s["h2_bp"] > 0 and z >= 1.5 and c["関門"]["通過"]: return "フォワード候補"
    if z < 1 or s["mean_bp"] <= 0: return "棄却"
    return "未確定"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=500); ap.add_argument("--seed", type=int, default=20261101); a = ap.parse_args()
    px = {s: load_d1(s).assign(d=lambda x: pd.to_datetime(x["time"]).dt.tz_localize(None).dt.normalize()).groupby("d")["close"].last() for s in MAP}
    C = pd.DataFrame(px).sort_index(); C = C[C.index.dayofweek < 5]; idx = C.index
    R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5); vol = R.rolling(60, min_periods=45).std()
    T = rate_table(); SL, SR = swap_rates(idx, T); cols = list(MAP); rel = np.array([rel_spread()[s] for s in cols]); nights = np.r_[1, np.diff(idx.values).astype("timedelta64[D]").astype(int)]
    Sg = signals(); mult = np.array([MAP[s][1] for s in cols], float); rng = np.random.default_rng(a.seed); res = dict(qid="Q593", cols=cols, spreads_bp={s: round(1e4 * float(v), 2) for s, v in zip(cols, rel)}, 期間=[str(idx.min().date()), str(idx.max().date())], B=a.B, sig={}); keep = {}
    for k, Z in Sg.items():
        Z = Z.reindex(columns=cols); W = weights(Z, vol, idx, mult); d, tv = pnl(W, R[cols], SL[cols], SR[cols], rel, nights); net = d["price"] + d["swap"] - d["cost"]; st = stats(net); mask = net.index >= EVAL
        n = len(Z); vals = []
        for i in range(a.B):
            s_ = int(rng.integers(26, n - 26)); Wn = weights(Z, vol, idx, mult, shift=s_); dn, _ = pnl(Wn, R[cols], SL[cols], SR[cols], rel, nights); vals.append(float((dn["price"] + dn["swap"] - dn["cost"])[mask].mean()))
            if (i + 1) % 100 == 0: print(k, "帰無", i + 1, "/", a.B, flush=True)
        vals = np.array(vals); z = float((net[mask].mean() - vals.mean()) / vals.std()); c = G.gate(net[mask], f"COT {k}")
        look, _ = pnl(weights(Z.shift(-1), vol, idx, mult), R[cols], SL[cols], SR[cols], rel, nights)
        grp = {}
        for g in ("FX", "指数", "金属", "エネルギー"):
            cc = [s for s in cols if GROUP[s] == g]; grp[g] = 1e4 * float((W[cc].shift(1).fillna(0).to_numpy() * np.nan_to_num(R[cc].to_numpy()))[mask].sum(axis=1).mean())
        res["sig"][k] = dict(stats=st, null=dict(B=a.B, null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(vals.std()), z=z, p=float((vals >= net[mask].mean()).mean())), composite=c, verdict=verdict(st, z, c),
                             コスト前スワップ前_bp=1e4 * float(d["price"][mask].mean()), コスト_bp=1e4 * float(d["cost"][mask].mean()), スワップ_bp=1e4 * float(d["swap"][mask].mean()), 片道回転_年=float(tv[mask].mean() * 252), 銘柄群_値動きbp=grp,
                             先読みあり_平均bp=1e4 * float((look["price"] + look["swap"] - look["cost"])[mask].mean()), 平均銘柄数=float((W.abs() > 0).sum(axis=1)[mask].mean()))
        keep[k] = net; r = res["sig"][k]; print(k, r["verdict"], {q: round(st[q], 3) for q in ("mean_bp", "t_nw", "sharpe", "pf", "h1_bp", "h2_bp", "h1_ty", "h2_ty", "maxdd_pct")}, "z", round(z, 2), "前", round(r["コスト前スワップ前_bp"], 3), "コスト", round(r["コスト_bp"], 3), "スワップ", round(r["スワップ_bp"], 3), "群", {g: round(v, 3) for g, v in grp.items()}, "先読み", round(r["先読みあり_平均bp"], 3), flush=True)
        print("  composite", c["単体Sharpe"], c["相関"], c["合成Sharpe"], c["関門"], flush=True)
        print("  年別", st["by_year_pct"], flush=True)
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); json.dump(res, open(os.path.join(HERE, "results", "result_q593.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float); pd.DataFrame(keep).to_csv(os.path.join(HERE, "results", "daily_q593.csv"))


if __name__ == "__main__":
    main()
