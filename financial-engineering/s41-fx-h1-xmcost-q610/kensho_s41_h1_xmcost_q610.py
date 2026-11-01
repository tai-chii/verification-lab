# -*- coding: utf-8 -*-
"""Q610 S41: S21 の H1（E1 の数値のまま）を FX 10 本で、XM の実スプレッド・実スワップで学習し評価する。事前登録: 事前登録_q610.md（変更禁止）。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_s41_h1_xmcost_q610.py [--smoke]"""
import argparse, datetime, json, os, sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, "..")
sys.path[:0] = [os.path.join(FE, "s35-fx-h4-ml-q602"), os.path.join(FE, "s21-h1-ml-rr-weekcap-q515"), os.path.join(FE, "..", "..", "_データ", "fetch")]
import kensho_s35_fx_h4_q602 as P                                  # K.SYMS を FX 10 本に・保有コスト 0 にする
K, W, Q, C = P.K, P.W, P.Q, P.C
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z
import kensho_s21_reopen_q534 as E
from fe_core.data import SEAL_END
from fe_core.metrics import nw_t
from composite_gate import gate
SPLIT = P.SPLIT; POST21 = pd.Timestamp("2021-01-01", tz="UTC"); YEN = ("USDJPY", "EURJPY", "GBPJPY")


def build(T, syms):
    out = {}
    for s in syms:
        t0 = time.time(); d = K.load(P.H1, s); d = d[d["time"] < pd.Timestamp(SEAL_END, tz="UTC")].reset_index(drop=True)  # 封印済み: SEAL_END で切る
        spr0 = (d["ask_close"] - d["close"]).clip(lower=0); spr = np.maximum(spr0, C.XMREL[s] * d["close"]).shift(1).bfill()
        for c in ("open", "high", "low", "close"): d[f"ask_{c}"] = d[c] + spr
        d["spr"] = spr; R, X = Z.labels_wk(d, s); bh, bl, bc = (d[c].to_numpy(float) for c in ("high", "low", "close")); pc = np.r_[bc[0], bc[:-1]]
        D = K.K_ATR * pd.Series(np.maximum(bh - bl, np.maximum(np.abs(bh - pc), np.abs(bl - pc)))).rolling(24, min_periods=24).mean().to_numpy()
        F = pd.concat([K.features(d, D, s).reset_index(drop=True), J.M.mtf_feats(d, D).reset_index(drop=True)], axis=1).drop(columns=["vol_ratio"])
        Pa = [d["ask_open"].to_numpy(float) if dr == 1 else d["open"].to_numpy(float) for dr, _ in K.ACTIONS]; S = P.swap_R(d, s, X, D, T, Pa); c_spr = spr.to_numpy() / D
        out[s] = dict(time=d["time"].reset_index(drop=True), R=R + S, X=X, F=F, S=S, gross=R.copy(), cR=c_spr, D=D, spr=spr.to_numpy(), n=len(d), d=d, _sr=E.since_reopen(d))
        print(f"  {s}: H1 {len(d)} 本・spr/D 中央 {np.nanmedian(c_spr):.3f}・{time.time()-t0:.0f}s", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args(); syms = P.SYMS[:2] if a.smoke else P.SYMS; years = W.YEARS[-1:] if a.smoke else W.YEARS
    T = C.rate_table(); print("ラベル・特徴量", flush=True); data = build(T, syms); ts = []
    for Y in years:
        t0 = time.time(); s0, s1 = W.TS(Y), W.TS(Y + 1); m, ntr = Q.train_window(data, s0, None); Pr = K.predict(m, data, s0 - Q.WARM, s1); PP = J.apply_thr(data, Pr, J.thr_series(data, Pr), s0)
        tr = K.run_policy(data, E.block(PP, data, 1), 0.0).assign(fold=Y); ts.append(tr); print(f"{Y}: 学習 {ntr} 行・{len(tr)} 件・平均 {tr['R'].mean():+.4f}R・{time.time()-t0:.0f}s", flush=True)
    t = pd.concat(ts, ignore_index=True)
    for k in ("sw", "gross", "cost", "hh"): t[k] = 0.0
    for s, g in t.groupby("sym"):
        o = data[s]; i = g["i"].to_numpy(); ac = g["a"].to_numpy(); x = o["X"][i, ac]; t.loc[g.index, "sw"] = o["S"][i, ac]; t.loc[g.index, "gross"] = o["gross"][i, ac]; t.loc[g.index, "cost"] = o["cR"][i + 1]
        tn = o["time"].dt.tz_convert(None).to_numpy(); t.loc[g.index, "hh"] = (tn[x] - tn[i + 1]) / np.timedelta64(1, "h")
    t["dr"] = t["a"].map(lambda q: K.ACTIONS[q][0]); t["rr"] = t["a"].map(lambda q: K.ACTIONS[q][1]); et = pd.to_datetime(t["entry"], utc=True); ex = pd.to_datetime(t["exit"], utc=True); dow = ex.dt.dayofweek
    t["xd"] = (ex + pd.to_timedelta(np.where(dow >= 5, 7 - dow, 0), unit="D")).dt.tz_localize(None).dt.normalize(); idx = pd.bdate_range(W.TS(years[0]).tz_localize(None), t["xd"].max())
    al = P.ev(t["R"], t["xd"], idx); a_, b_ = t[et < SPLIT], t[et >= SPLIT]; z, nm, ns = K.null_z(data, t, B=20 if a.smoke else 200); dl = t.groupby("xd")["R"].sum().reindex(idx, fill_value=0.0)
    print({k: round(v, 4) if isinstance(v, float) else v for k, v in al.items()}, "前後半", round(a_["R"].mean(), 4) if len(a_) else None, round(b_["R"].mean(), 4), "z", round(z, 2), flush=True)
    if a.smoke: print("smoke: 保存しない"); return
    t.drop(columns=[]).to_csv(os.path.join(HERE, "results", "trades_q610.csv"), index=False); dl.rename("S41").to_csv(os.path.join(HERE, "results", "daily_q610.csv")); cg = gate(dl, "S41"); cs = cg["合成Sharpe"]; cor = cg["相関"]
    cor_ok = all(v <= 0.15 for v in cor.values()); c_ok = cor_ok and cg["単体Sharpe"]["全"] >= 0.5 and cs["全"][1] >= cs["全"][0] and cs["後"][1] >= cs["後"][0]; ck = dict(PF=al["pf"] >= 1.05, t=al["t_nw"] >= 1.5, 前後半=a_["R"].mean() > 0 and b_["R"].mean() > 0, 帰無=z >= 1.5, composite=bool(c_ok))
    only_s21 = all(v <= 0.15 for k, v in cor.items() if "S21" not in k) and cor["S21 H1 ML"] > 0.15 and cg["単体Sharpe"]["全"] >= 0.5
    vd = "フォワード候補" if all(ck.values()) else "S21 の FX の置き換え候補" if all(ck[k] for k in ("PF", "t", "前後半", "帰無")) and only_s21 else "棄却"
    jp = t["sym"].isin(YEN); p21 = et >= POST21; pf = lambda r: float(r[r > 0].sum() / -r[r < 0].sum())
    res = dict(qid="Q610", strategy="S41", 全体=al, 前半_mean_R=float(a_["R"].mean()), 後半_mean_R=float(b_["R"].mean()), 帰無=dict(z=z, mean=nm, sd=ns), 値動き_R=float(t["gross"].mean()), スプレッド_R=float(t["cost"].mean()), スワップ_R=float(t["sw"].mean()), コスト前_mean_R=float((t["R"] + t["cost"] - t["sw"]).mean()), 平均保有時間=float(t["hh"].mean()), スプレッド2倍_mean_R=float((t["R"] - t["cost"]).mean()), スプレッド2倍_PF=pf(t["R"] - t["cost"]),
               円3本=dict(n=int(jp.sum()), R=float(t.loc[jp, "R"].mean()), R_2021=float(t.loc[jp & p21, "R"].mean())), 主要7本=dict(n=int((~jp).sum()), R=float(t.loc[~jp, "R"].mean()), R_2021=float(t.loc[~jp & p21, "R"].mean())), 全_2021以降_R=float(t.loc[p21, "R"].mean()), RR={str(k): dict(n=int(len(g)), R=float(g["R"].mean())) for k, g in t.groupby("rr")}, 銘柄={k: dict(n=int(len(g)), R=float(g["R"].mean())) for k, g in t.groupby("sym")}, 年={int(k): dict(n=int(len(g)), R=float(g["R"].mean())) for k, g in t.groupby("fold")}, composite=cg, 関門=ck, 判定=vd, generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    json.dump(res, open(os.path.join(HERE, "results", "result_q610.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float); print(json.dumps({k: v for k, v in res.items() if k != "composite"}, ensure_ascii=False, default=float)); print(cg["期間"], cg["単体Sharpe"], cg["相関"], cg["合成Sharpe"]); print("done", flush=True)


if __name__ == "__main__":
    main()
