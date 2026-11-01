# -*- coding: utf-8 -*-
"""Q611 S42 FX の 21 ペアの共和分の平均回帰。事前登録: 事前登録_q611.md（変更禁止）。売買の規則は Q605 と同じ関数。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_s42_fx_pairs_q611.py [--smoke]"""
import argparse, datetime, itertools, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, "..")
sys.path[:0] = [os.path.join(FE, "s37-index-pairs-q605"), os.path.join(FE, "_fx_rates_common"), os.path.join(FE, "s21-real-swap-q592"), os.path.join(FE, "..", "tools")]
import kensho_s37_index_pairs_q605 as P
import fxrates as FX
import kensho_s21_real_swap_q592 as C
from fe_core import load_d1
from fe_core.metrics import nw_t
from composite_gate import gate
PAIRS = {"EURUSD": 1, "GBPUSD": 1, "AUDUSD": 1, "NZDUSD": 1, "USDJPY": -1, "USDCHF": -1, "USDCAD": -1}; SYMS = list(PAIRS)
SPLIT = pd.Timestamp("2017-01-01"); B, MIN_SHIFT, WIN, SEED = 200, 120, P.WIN, 20261101; EUR = {"EURUSD", "GBPUSD", "USDCHF"}; OCE = {"AUDUSD", "NZDUSD"}


def load(smoke, rng):
    if smoke:
        idx = pd.bdate_range("2010-01-01", "2024-06-28"); n = len(idx); o = {}
        f = np.cumsum(rng.normal(0, 3e-3, (n, 2)), axis=0)
        for i, s in enumerate(SYMS):
            r = np.cumsum(rng.normal(0, 3e-3, n)) * .5 + f[:, i % 2]; c = pd.Series(np.exp(r * PAIRS[s]), index=idx); o[s] = pd.DataFrame(dict(open=c.shift(1).fillna(1.0), close=c))
        return o, {s: pd.Series(dtype=float) for s in SYMS}
    o = {}; rel = {}
    for s in SYMS:
        o[s] = load_d1(s).set_index("time")[["open", "close"]]; o[s].index = pd.DatetimeIndex(o[s].index).tz_localize(None).normalize(); o[s] = o[s][o[s].index >= "2010-01-01"]; o[s] = o[s][~o[s].index.duplicated()]
        rel[s] = FX.duka_rel(s)
    return o, rel


def cum_swap(s, D, T):
    axis = pd.date_range(D.min(), D.max()); wd = axis.weekday.to_numpy(); w = np.where(wd >= 5, 0.0, np.where(wd == 2, 3.0, 1.0)); ax = axis.to_numpy("datetime64[D]").astype(np.int64); days = D.to_numpy("datetime64[D]").astype(np.int64); out = {}
    for dr in (1, -1):
        c = np.r_[0.0, np.cumsum(C.annual(s, np.full(len(ax), dr), ax, T) / 365 * w)]; out[dr] = c[days - ax[0]]
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args(); rng = np.random.default_rng(SEED); px, rel = load(a.smoke, rng)
    D = px[SYMS[0]].index
    for s in SYMS[1:]: D = D.intersection(px[s].index)
    V, O, CS, SW = {}, {}, {}, {}; T = C.rate_table()
    for s in SYMS:
        x = px[s].reindex(D); V[s] = np.log(x["close"].to_numpy(float)) * PAIRS[s]; O[s] = np.exp(np.log(x["open"].to_numpy(float)) * PAIRS[s]); du = rel[s].reindex(D, method="ffill").to_numpy(float) if len(rel[s]) else np.zeros(len(D)); CS[s] = np.maximum(C.XMREL[s], np.nan_to_num(du)); SW[s] = cum_swap(s, D, T)
    n = len(D); dv = D.to_numpy()
    def pnl(p, q, e, x, dr, bt):
        wa, wb = 1 / (1 + bt), bt / (1 + bt); ra, rb = O[p][x] / O[p][e] - 1, O[q][x] / O[q][e] - 1; g = dr * (wa * ra - wb * rb); sp = wa * CS[p][e] + wb * CS[q][e]; dr = np.asarray(dr); e = np.asarray(e); x = np.asarray(x)
        def leg(s, d):                # d は通貨の価値の向き。銘柄の向きは d × PAIRS[s]
            dp = d * PAIRS[s]; return np.where(dp > 0, SW[s][1][x] - SW[s][1][e], SW[s][-1][x] - SW[s][-1][e])
        return g, wa * leg(p, dr) + wb * leg(q, -dr), sp
    rows = []
    for p, q in itertools.combinations(SYMS, 2):
        rows += P.trades(p, q, p, q, dv, None, None, V[p], V[q])
    t = pd.DataFrame(rows, columns=["a", "b", "e", "x", "dr", "beta", "why"]); print("件数", len(t), flush=True)
    for k in ("gross", "sw", "sp"): t[k] = 0.0
    Y = {}
    for k, g_ in t.groupby(["a", "b"]):
        e, x, dr, bt = g_["e"].to_numpy(), g_["x"].to_numpy(), g_["dr"].to_numpy(), g_["beta"].to_numpy(); g, sw, sp = pnl(k[0], k[1], e, x, dr, bt); t.loc[g_.index, "gross"] = g; t.loc[g_.index, "sw"] = sw; t.loc[g_.index, "sp"] = sp; Y[k] = (e, x - e, dr, bt)
    t["R"] = t["gross"] + t["sw"] - t["sp"]; t["ed"] = dv[t["e"].to_numpy()]; t["xd"] = dv[t["x"].to_numpy()]; xd = pd.DatetimeIndex(t["xd"]); t["xd"] = xd + pd.to_timedelta(np.where(xd.weekday == 6, 1, np.where(xd.weekday == 5, 2, 0)), unit="D"); idx = pd.bdate_range(t["xd"].min(), t["xd"].max()); dl = t.groupby("xd")["R"].sum().reindex(idx, fill_value=0.0) / 21; assert abs(dl.sum() * 21 - t["R"].sum()) < 1e-9
    pf = lambda r: float(r[r > 0].sum() / -r[r < 0].sum()); a_, b_ = t[t["ed"] < SPLIT], t[t["ed"] >= SPLIT]; obs = float(t["R"].mean()); null = np.empty(B if not a.smoke else 50)
    for i in range(len(null)):
        tot, m = 0.0, 0
        for k, (e, h, dr, bt) in Y.items():
            L = n - WIN - 1 - h.max() - 1; sh = rng.integers(MIN_SHIFT, max(L - MIN_SHIFT, MIN_SHIFT + 1)); e2 = WIN + (e - WIN + sh) % L; g2, s2, c2 = pnl(k[0], k[1], e2, e2 + h, dr, bt); tot += (g2 + s2 - c2).sum(); m += len(e)
        null[i] = tot / m
    z = float((obs - null.mean()) / null.std(ddof=1)); tt = float(nw_t(dl.to_numpy()))
    print(dict(n=len(t), mean_bp=round(obs * 1e4, 2), gross_bp=round(t["gross"].mean() * 1e4, 2), sw_bp=round(t["sw"].mean() * 1e4, 2), sp_bp=round(t["sp"].mean() * 1e4, 2), pf=round(pf(t["R"]), 3), nw=round(tt, 2), h1=round(a_["R"].mean() * 1e4, 2), h2=round(b_["R"].mean() * 1e4, 2), null=round(null.mean() * 1e4, 2), sd=round(null.std(ddof=1) * 1e4, 2), z=round(z, 2)), flush=True)
    if a.smoke: print("smoke: 保存しない"); return
    cg = gate(dl, "S42"); cs = cg["合成Sharpe"]; cor_ok = all(v <= 0.15 for v in cg["相関"].values()); c_ok = cor_ok and cg["単体Sharpe"]["全"] >= 0.5 and cs["全"][1] >= cs["全"][0] and cs["後"][1] >= cs["後"][0]; ck = dict(PF=pf(t["R"]) >= 1.05, t=tt >= 1.5, 前後半=a_["R"].mean() > 0 and b_["R"].mean() > 0, 帰無=z >= 1.5, composite=bool(c_ok))
    t["型"] = [("オセアニア" if r.a in OCE and r.b in OCE else "欧州" if r.a in EUR and r.b in EUR else "他") for r in t.itertuples()]; sp = t.groupby(["a", "b"])["R"].agg(["count", "mean"]).reset_index().sort_values("mean")
    res = dict(qid="Q611", strategy="S42", 件数=int(len(t)), 年件数=float(len(t) / ((pd.Timestamp(t["xd"].max()) - pd.Timestamp(t["ed"].min())).days / 365.25)), mean_bp=obs * 1e4, コスト前_bp=float(t["gross"].mean() * 1e4), スワップ_bp=float(t["sw"].mean() * 1e4), スプレッド_bp=float(t["sp"].mean() * 1e4), PF=pf(t["R"]), NW_t=tt, 前半_bp=float(a_["R"].mean() * 1e4), 後半_bp=float(b_["R"].mean() * 1e4), 帰無=dict(z=z, mean_bp=float(null.mean() * 1e4), sd_bp=float(null.std(ddof=1) * 1e4)), 勝率=float((t["R"] > 0).mean()), 平均保有本=float((t["x"] - t["e"]).mean()), 出口=t.groupby("why")["R"].agg(["count", "mean"]).round(5).to_dict("index"), スプレッド2倍_bp=float((t["R"] - t["sp"]).mean() * 1e4), 型=t.groupby("型")["R"].agg(["count", "mean"]).round(5).to_dict("index"), ペア下位=sp.head(4).round(5).to_dict("records"), ペア上位=sp.tail(4).round(5).to_dict("records"), composite=cg, 関門=ck, 判定="フォワード候補" if all(ck.values()) else "棄却", generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    t.to_csv(os.path.join(HERE, "results", "trades_q611.csv"), index=False); dl.rename("S42").to_csv(os.path.join(HERE, "results", "daily_q611.csv"))
    json.dump(res, open(os.path.join(HERE, "results", "result_q611.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float); print(json.dumps({k: v for k, v in res.items() if k != "composite"}, ensure_ascii=False, default=float)); print(cg["期間"], cg["単体Sharpe"], cg["相関"], cg["合成Sharpe"])


if __name__ == "__main__":
    main()
