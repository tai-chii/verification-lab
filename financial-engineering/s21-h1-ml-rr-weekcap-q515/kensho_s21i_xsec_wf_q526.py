# -*- coding: utf-8 -*-
"""Q526: Q521 の設計＋同じ時刻の全 15 銘柄の値動き・通貨強弱。事前登録_q526.md。
使い方: python3 kensho_s21i_xsec_wf_q526.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_mtf_wf_q521 as M

FX10 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP"]
CCY = ["USD", "EUR", "JPY", "GBP", "AUD", "NZD", "CAD", "CHF"]
KS = [1, 6, 24]


def xsec_panel(data):
    """時刻 × (銘柄_k) の ATR 正規化リターン表と、通貨強弱。"""
    cols = {}
    for s, o in data.items():
        d = o["_d"]; atr = o["_D"] / K.K_ATR; c = d["close"].to_numpy()
        t = d["time"].dt.tz_convert(None)
        for k in KS:
            r = np.full(len(c), np.nan); r[k:] = (c[k:] - c[:-k]) / atr[k:]
            cols[f"x_{s}_{k}"] = pd.Series(r, index=t)
    P = pd.DataFrame(cols).sort_index()
    P = P[~P.index.duplicated()].ffill()
    for k in [6, 24]:
        acc = {c: [] for c in CCY}
        for p in FX10:
            b, q = p[:3], p[3:]
            acc[b].append(P[f"x_{p}_{k}"]); acc[q].append(-P[f"x_{p}_{k}"])
        for c in CCY:
            P[f"s_{c}_{k}"] = pd.concat(acc[c], axis=1).mean(axis=1)
    return P


def build(data_dir):
    data = {}
    for s in K.SYMS:
        d = K.load(data_dir, s); R, X, D = K.labels(d, s); F = K.features(d, D, s)
        F2 = pd.concat([F.reset_index(drop=True), M.mtf_feats(d, D).reset_index(drop=True)], axis=1)
        data[s] = dict(time=d["time"].reset_index(drop=True), R=R, X=X, F=F2, _d=d, _D=D)
        print(f"  {s}", flush=True)
    P = xsec_panel(data)
    for s, o in data.items():
        t = o["time"].dt.tz_convert(None)
        add = P.reindex(t.to_numpy()).reset_index(drop=True)
        if s in FX10:
            b, q = s[:3], s[3:]
            for k in [6, 24]:
                add[f"own_diff_{k}"] = add[f"s_{b}_{k}"] - add[f"s_{q}_{k}"]
        else:
            for k in [6, 24]:
                add[f"own_diff_{k}"] = np.nan
        o["F"] = pd.concat([o["F"], add], axis=1)
        del o["_d"], o["_D"]
    return data


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("ラベル・特徴量", flush=True); data = build(a.data)
    ncol = next(iter(data.values()))["F"].shape[1]; print(f"特徴量 {ncol} 個", flush=True)
    res = dict(qid="Q526", run_at=time.strftime("%Y-%m-%d %H:%M"), n_features=ncol)
    res["W-exp-xs"] = Q.run_window(data, a, "W-exp-xs", None)
    p = res["W-exp-xs"]["pooled"]
    res["adopt"] = bool(all(p["criteria"].values()) and p["t"] >= 3.70 + 0.5)
    models, _ = Q.train_window(data, W.TS(W.YEARS[-1]), None)
    cols = list(next(iter(data.values()))["F"].columns)
    imp = pd.Series(np.mean([m.booster_.feature_importance("gain") for m in models], axis=0), index=cols).sort_values(ascending=False)
    res["importance_top15"] = list(imp.index[:15])
    newc = [c for c in cols if c.startswith(("x_", "s_", "own_diff"))]
    rank = {c: i + 1 for i, c in enumerate(imp.index)}
    res["new_feature_top10"] = sorted(((rank[c], c) for c in newc))[:10]
    res["new_gain_share"] = float(imp[newc].sum() / imp.sum())
    json.dump(res, open(os.path.join(a.out, "result_q526.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(dict(pooled=p, adopt=res["adopt"], top15=res["importance_top15"], new_top10=res["new_feature_top10"], new_gain_share=res["new_gain_share"]), ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
