# -*- coding: utf-8 -*-
"""Q612 S43 8 通貨の週次の横断 ML。事前登録: 事前登録_q612.md（変更禁止）。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_s43_fx_xsec_ml_q612.py [--smoke] [--plant]"""
import argparse, datetime, json, os, sys
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, "..")
sys.path[:0] = [os.path.join(FE, "_fx_rates_common"), os.path.join(FE, "s21-real-swap-q592"), os.path.join(FE, "..", "tools")]
import fxrates as FX
import kensho_s21_real_swap_q592 as C
from fe_core import load_d1
from fe_core.metrics import nw_t
from composite_gate import gate
PAIR = {"EUR": ("EURUSD", 1), "GBP": ("GBPUSD", 1), "AUD": ("AUDUSD", 1), "NZD": ("NZDUSD", 1), "JPY": ("USDJPY", -1), "CHF": ("USDCHF", -1), "CAD": ("USDCAD", -1)}
CCY = ["USD"] + list(PAIR); LGB = dict(objective="regression", learning_rate=0.03, n_estimators=300, num_leaves=31, min_child_samples=200, verbose=-1, n_jobs=4); SEEDS = (1, 2, 3); FIRST, SPLIT, B, SEED = 2015, pd.Timestamp("2020-01-01"), 200, 20261101
FEATS = ["r5", "r20", "r60", "r120", "r250", "v20", "v60", "rate", "drate", "hi250"]


def load(smoke, rng):
    if smoke:
        idx = pd.bdate_range("2010-01-01", "2024-06-28"); n = len(idx); O, CL = {}, {}
        for c in PAIR:
            r = rng.normal(0, 5e-3, n); CL[c] = np.cumsum(r); O[c] = np.r_[0.0, CL[c][:-1]]
        return idx, pd.DataFrame(O, index=idx), pd.DataFrame(CL, index=idx), {c: pd.Series(dtype=float) for c in PAIR}
    O, CL, rel = {}, {}, {}
    for c, (s, sg) in PAIR.items():
        d = load_d1(s).set_index("time")[["open", "close"]]; d.index = pd.DatetimeIndex(d.index).tz_localize(None).normalize(); d = d[~d.index.duplicated()]; d = d[d.index >= "2009-06-01"]; O[c] = np.log(d["open"]) * sg; CL[c] = np.log(d["close"]) * sg; rel[c] = FX.duka_rel(s)
    O, CL = pd.DataFrame(O).dropna(), pd.DataFrame(CL).dropna(); idx = O.index.intersection(CL.index); return idx, O.loc[idx], CL.loc[idx], rel


def panel(idx, CL, T, plant, rng):
    """週の最後の足ごとに 8 通貨 × 特徴量。"""
    v = CL.copy(); v.insert(0, "USD", 0.0); days = idx.to_numpy("datetime64[D]").astype(np.int64); wk = idx.to_period("W-SUN"); last = np.r_[wk[1:] != wk[:-1], True]; T_ = np.where(last)[0]; T_ = T_[(T_ >= 250) & (T_ < len(idx) - 2)]; F = {}
    rate = pd.DataFrame({c: C.rate(T, c, days) for c in CCY}, index=idx) * 100; r = v.diff()
    for L in (5, 20, 60, 120, 250): F[f"r{L}"] = v - v.shift(L)
    F["v20"], F["v60"] = r.rolling(20).std(), r.rolling(60).std(); F["rate"] = rate; F["drate"] = rate - rate.shift(60); F["hi250"] = v - v.rolling(250).max()
    X = {k: x.sub(x.mean(axis=1), axis=0) for k, x in F.items()}; rows = []
    for i, t in enumerate(T_):
        for c in CCY: rows.append((i, t, c, *[X[k][c].iloc[t] for k in FEATS]))
    return pd.DataFrame(rows, columns=["w", "t", "ccy", *FEATS]), T_


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--plant", action="store_true"); a = ap.parse_args(); rng = np.random.default_rng(SEED); T = C.rate_table()
    idx, O, CL, rel = load(a.smoke, rng); P, W = panel(idx, CL, T, a.plant, rng); nw = len(W); e = W + 1; o = O.copy(); o.insert(0, "USD", 0.0); oa = o[CCY].to_numpy(); fwd = np.vstack([oa[e[i + 1]] - oa[e[i]] for i in range(nw - 1)] + [np.full(8, np.nan)])
    if a.plant:                         # 試験: 翌週の騰落に r20 の順位を混ぜる（ML が拾えるか・先読みが無いか）
        s = P.pivot(index="w", columns="ccy", values="r20")[CCY].to_numpy(); fwd = fwd + 0.002 * np.sign(np.nan_to_num(s))
    fr = fwd - np.nanmean(fwd, axis=1, keepdims=True); P["y"] = pd.DataFrame(fr, columns=CCY).rank(axis=1, pct=True).stack().reindex(pd.MultiIndex.from_arrays([P["w"], P["ccy"]])).to_numpy(); pred = np.full((nw, 8), np.nan); yrs = idx[W].year.to_numpy(); last_w = np.where(yrs < 2100)[0].max(); y_end = int(yrs[last_w])
    for Y in range(FIRST, y_end + 1):
        te = np.where(yrs == Y)[0]; tr = P[(yrs[P["w"].to_numpy()] < Y) & P["y"].notna() & (P["w"] < te.min() - 1)].dropna(subset=FEATS); s = P[P["w"].isin(te)]; ok = s[FEATS].notna().all(axis=1).to_numpy(); p = np.zeros(ok.sum())
        for sd in SEEDS: p += lgb.LGBMRegressor(random_state=sd, **LGB).fit(tr[FEATS].to_numpy(), tr["y"].to_numpy()).predict(s.loc[ok, FEATS].to_numpy())
        for w_, c, v in zip(s.loc[ok, "w"], s.loc[ok, "ccy"], p / len(SEEDS)): pred[w_, CCY.index(c)] = v
        print(Y, "学習", len(tr), flush=True)
    live = np.where(np.isfinite(pred).all(axis=1) & np.isfinite(fwd).all(axis=1))[0]; days = idx[e].to_numpy("datetime64[D]").astype(np.int64); CM = pd.DataFrame({c: np.maximum(C.XMREL[PAIR[c][0]], np.nan_to_num(rel[c].reindex(idx[e], method="ffill").to_numpy(float)) if len(rel[c]) else 0.0) for c in PAIR}, index=range(nw)); ANN = {c: {d: C.annual(PAIR[c][0], np.full(nw, d), days, T) for d in (1, -1)} for c in PAIR}
    def book(sig):
        """sig: 週 × 8。上位 2 買い・下位 2 売り。返り: 週次の gross・spread・swap・回転。"""
        w = np.zeros_like(sig); oo = np.argsort(sig, axis=1); r = np.arange(len(sig))[:, None]; w[r, oo[:, -2:]] = 0.25; w[r, oo[:, :2]] = -0.25; g = (w * fwd[live]).sum(axis=1)
        wp = w[:, 1:]; dw = np.abs(np.diff(np.vstack([np.zeros(7), wp]), axis=0)); c = (dw * CM.iloc[live][list(PAIR)].to_numpy()).sum(axis=1) / 2; sw = np.zeros(len(g))
        for j, x in enumerate(PAIR):
            dp = np.sign(wp[:, j]) * PAIR[x][1]; sw += np.abs(wp[:, j]) * np.where(dp > 0, ANN[x][1][live], ANN[x][-1][live]) * 7 / 365
        return g, c, sw, w
    g, c, sw, w = book(pred[live]); net = g - c + sw; ti = idx[W[live]]; rng2 = np.random.default_rng(SEED); n = len(live); nul = np.empty(50 if a.smoke else B)
    for i in range(len(nul)):
        sh = int(rng2.integers(26, n - 26)); g2, c2, s2, _ = book(np.roll(pred[live], sh, axis=0)); nul[i] = float((g2 - c2 + s2).mean())
    z = float((net.mean() - nul.mean()) / nul.std(ddof=1)); ic = np.array([pd.Series(pred[j]).corr(pd.Series(fr[j]), method="spearman") for j in live])
    hold = pd.Series(0.0, index=idx); opn = oa
    for k, j in enumerate(live):           # 建てた始値から次の始値までを日に割る。コストは建てた日、スワップは均す
        a0, a1 = e[j], e[j + 1]; dd = np.diff(opn[a0:a1 + 1], axis=0); hold.iloc[a0:a1] += dd @ w[k]; hold.iloc[a0] -= c[k]; hold.iloc[a0:a1] += sw[k] / (a1 - a0)
    hd = hold.index; hold.index = hd + pd.to_timedelta(np.where(hd.weekday == 6, 1, np.where(hd.weekday == 5, 2, 0)), unit="D"); hold = hold.groupby(level=0).sum()
    ds = hold.reindex(pd.bdate_range(ti.min(), hold.index.max())).fillna(0.0); assert a.plant or abs(ds.sum() - net.sum()) < 1e-9, (ds.sum(), net.sum()); nwt = float(nw_t(ds.to_numpy())); pos, neg = net[net > 0].sum(), -net[net < 0].sum(); h1, h2 = net[ti < SPLIT], net[ti >= SPLIT]
    st = dict(週=n, mean_bp=1e4 * float(net.mean()), gross_bp=1e4 * float(g.mean()), spread_bp=1e4 * float(c.mean()), swap_bp=1e4 * float(sw.mean()), pf=float(pos / neg), nw_t=nwt, sharpe=float(ds.mean() / ds.std(ddof=1) * np.sqrt(252)), h1_bp=1e4 * float(h1.mean()), h2_bp=1e4 * float(h2.mean()), IC=float(np.nanmean(ic)), IC_t=float(np.nanmean(ic) / np.nanstd(ic, ddof=1) * np.sqrt(len(ic))), 回転=float(np.abs(np.diff(w, axis=0)).sum(axis=1).mean()), 帰無=dict(z=z, mean_bp=1e4 * float(nul.mean()), sd_bp=1e4 * float(nul.std(ddof=1))))
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in st.items()}, flush=True)
    if a.smoke: print("smoke: 保存しない"); return
    cg = gate(ds, "S43"); cs = cg["合成Sharpe"]; cor_ok = all(v <= 0.15 for v in cg["相関"].values()); c_ok = cor_ok and cg["単体Sharpe"]["全"] >= 0.5 and cs["全"][1] >= cs["全"][0] and cs["後"][1] >= cs["後"][0]; ck = dict(PF=st["pf"] >= 1.05, t=nwt >= 1.5, 前後半=st["h1_bp"] > 0 and st["h2_bp"] > 0, 帰無=z >= 1.5, composite=bool(c_ok))
    cmp_ = {}
    for k in ("rate", "r60"):
        sg = P.pivot(index="w", columns="ccy", values=k)[CCY].to_numpy()[live]; g3, c3, s3, _ = book(sg); nt = g3 - c3 + s3; cmp_[k] = dict(mean_bp=1e4 * float(nt.mean()), t=float(nt.mean() / nt.std(ddof=1) * np.sqrt(len(nt))))
    res = dict(qid="Q612", strategy="S43", **st, 比較=cmp_, 年={str(y): round(1e4 * float(v), 1) for y, v in pd.Series(net).groupby(ti.year).sum().items()}, composite=cg, 関門=ck, 判定="フォワード候補" if all(ck.values()) else "棄却", generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    ds.rename("S43").to_csv(os.path.join(HERE, "results", "daily_q612.csv")); json.dump(res, open(os.path.join(HERE, "results", "result_q612.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float); print(json.dumps({k: v for k, v in res.items() if k != "composite"}, ensure_ascii=False, default=float)); print(cg["期間"], cg["単体Sharpe"], cg["相関"], cg["合成Sharpe"])


if __name__ == "__main__":
    main()
