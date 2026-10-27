# -*- coding: utf-8 -*-
"""Q521: Q519 本体（W-exp）＋H4・D1 の確定足からの乖離。事前登録_q521.md。
使い方: python3 kensho_s21f_mtf_wf_q521.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q

CUT = pd.Timedelta(hours=2)  # 22:00 UTC を 0 時に揃えるずらし
NEW = ["d1p_hi", "d1p_lo", "d1p_cl", "d1p_rng", "d1p_body", "d0_open", "d0_hi", "d0_lo", "h4p_hi", "h4p_lo", "h4p_cl", "h4p_rng", "h4p_body"]


def mtf_feats(d, D):
    t = d["time"]; atr = pd.Series(D / K.K_ATR, index=d.index)
    c = d["close"]
    out = pd.DataFrame(index=d.index)
    dec = (t + pd.Timedelta(hours=1))
    for name, freq in [("d1", "D"), ("h4", "4h")]:
        g = (t + CUT).dt.floor(freq)
        agg = d.assign(g=g).groupby("g").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), end=("time", "max"))
        agg["end"] = agg["end"] + pd.Timedelta(hours=1)
        agg = agg.reset_index(drop=True).sort_values("end")
        m = pd.merge_asof(pd.DataFrame({"dec": dec, "k": np.arange(len(d))}).sort_values("dec"), agg, left_on="dec", right_on="end",
                          direction="backward").sort_values("k").reset_index(drop=True)
        p = "d1p" if name == "d1" else "h4p"
        out[f"{p}_hi"] = (c.to_numpy() - m["h"].to_numpy()) / atr.to_numpy()
        out[f"{p}_lo"] = (c.to_numpy() - m["l"].to_numpy()) / atr.to_numpy()
        out[f"{p}_cl"] = (c.to_numpy() - m["c"].to_numpy()) / atr.to_numpy()
        out[f"{p}_rng"] = (m["h"] - m["l"]).to_numpy() / atr.to_numpy()
        out[f"{p}_body"] = (m["c"] - m["o"]).to_numpy() / atr.to_numpy()
        if name == "d1":
            gd = d.assign(g=g)
            day_open = gd.groupby("g")["open"].transform("first")
            day_hi = gd.groupby("g")["high"].cummax(); day_lo = gd.groupby("g")["low"].cummin()
            out["d0_open"] = (c - day_open) / atr; out["d0_hi"] = (c - day_hi) / atr; out["d0_lo"] = (c - day_lo) / atr
    return out.replace([np.inf, -np.inf], np.nan)


def build(data_dir):
    out = {}
    for s in K.SYMS:
        d = K.load(data_dir, s); R, X, D = K.labels(d, s); F = K.features(d, D, s)
        F2 = pd.concat([F.reset_index(drop=True), mtf_feats(d, D).reset_index(drop=True)], axis=1)
        out[s] = dict(time=d["time"].reset_index(drop=True), R=R, X=X, F=F2)
        print(f"  {s}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("ラベル・特徴量", flush=True); data = build(a.data)
    res = dict(qid="Q521", run_at=time.strftime("%Y-%m-%d %H:%M"))
    res["W-exp-mtf"] = Q.run_window(data, a, "W-exp-mtf", None)
    p = res["W-exp-mtf"]["pooled"]
    adopt = all(p["criteria"].values()) and p["t"] >= 2.87 + 0.5
    res["adopt"] = bool(adopt)
    # 重要度（最後の年のモデルで）
    models, _ = Q.train_window(data, W.TS(W.YEARS[-1]), None)
    cols = list(next(iter(data.values()))["F"].columns)
    imp = np.mean([m.booster_.feature_importance("gain") for m in models], axis=0)
    rk = pd.Series(imp, index=cols).sort_values(ascending=False)
    res["importance_rank_new"] = {c: int(list(rk.index).index(c)) + 1 for c in NEW}
    res["importance_top10"] = list(rk.index[:10])
    json.dump(res, open(os.path.join(a.out, "result_q521.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(dict(pooled=p, adopt=adopt, importance_top10=res["importance_top10"], new_rank=res["importance_rank_new"]), ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
