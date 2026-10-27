# -*- coding: utf-8 -*-
"""Q517 / S21c: Q515 の設計を M15・EURUSD/USDJPY で（簡易版）。事前登録_q517.md。
使い方: python3 kensho_s21c_m15_2sym_q517.py --m15 DIR(data_*_M15_dukascopy.csv) --h1 DIR(*.parquet) --out DIR [--open-final]"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K

K.SYMS = ["EURUSD", "USDJPY"]
TZ = "UTC"
INNER_START = pd.Timestamp("2022-07-15", tz=TZ); TRAIN_END = pd.Timestamp("2023-07-15", tz=TZ)
VAL_START, VAL_MID, VAL_END = TRAIN_END, pd.Timestamp("2024-07-15", tz=TZ), pd.Timestamp("2025-07-15", tz=TZ)
TEST_START, TEST_END = VAL_END, pd.Timestamp("2026-07-15", tz=TZ)


def load_m15(m15_dir, h1_dir, sym):
    d = pd.read_csv(os.path.join(m15_dir, f"data_{sym}_M15_dukascopy.csv"), parse_dates=["time"])
    d["time"] = d["time"].dt.tz_localize(TZ)
    d = d[d["high"] != d["low"]].sort_values("time").reset_index(drop=True)
    h1 = pd.read_parquet(os.path.join(h1_dir, f"{sym}.parquet"))[["time", "ask_close", "close"]]
    h1["spr"] = (h1["ask_close"] - h1["close"]).clip(lower=0)
    d["hour"] = d["time"].dt.floor("h")
    d = d.merge(h1[["time", "spr"]].rename(columns={"time": "hour"}), on="hour", how="left")
    d["spr"] = d["spr"].fillna(d["spr"].rolling(500, min_periods=1).median()).bfill()
    for c in ["open", "high", "low", "close"]:
        d[f"ask_{c}"] = d[c] + d["spr"]
    return d.drop(columns=["hour"])


def build(m15_dir, h1_dir):
    out = {}
    for s in K.SYMS:
        d = load_m15(m15_dir, h1_dir, s); R, X, D = K.labels(d, s); F = K.features(d, D, s)
        out[s] = dict(time=d["time"].reset_index(drop=True), R=R, X=X, F=F)
        print(f"  {s}: {len(d)} 本  spr_R 中央 {np.nanmedian(d['spr']/D):.3f}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--m15", required=True); ap.add_argument("--h1", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--open-final", action="store_true"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = dict(qid="Q517", strategy="S21c", run_at=time.strftime("%Y-%m-%d %H:%M"))
    data = build(a.m15, a.h1)
    m_in, ntr = K.train_models(data, INNER_START)
    P_in = K.predict(m_in, data, INNER_START, TRAIN_END); inner = []
    for th in K.THETAS:
        tr = K.run_policy(data, P_in, th); p = K.daily(tr, INNER_START, TRAIN_END, 1.0)
        inner.append(dict(theta=th, n=len(tr), mean_R=float(tr["R"].mean()) if len(tr) else None, t=K.tstat(p), sigma_R_daily=float(p.std())))
    cand = [x for x in inner if x["n"] >= 200] or inner
    pick = max(cand, key=lambda x: x["t"]); theta = pick["theta"]
    r = min(K.R_CAP, K.SIGMA_TARGET / pick["sigma_R_daily"]) if pick["sigma_R_daily"] > 0 else K.R_CAP
    res["inner"] = dict(n_train_rows=ntr, grid=inner, theta=theta, r=r)
    print(json.dumps(res["inner"], ensure_ascii=False), flush=True)
    models, ntr = K.train_models(data, TRAIN_END)
    P = K.predict(models, data, VAL_START, VAL_END)
    tr = K.run_policy(data, P, theta); tr.to_csv(os.path.join(a.out, "trades_val_q517.csv"), index=False)
    s_all = K.summarize(tr, VAL_START, VAL_END, r)
    y1 = K.summarize(tr[tr["entry"] < VAL_MID], VAL_START, VAL_MID, r); y2 = K.summarize(tr[tr["entry"] >= VAL_MID], VAL_MID, VAL_END, r)
    z, nm, ns = K.null_z(data, tr)
    gate = dict(t_ge_2=s_all["t_daily"] >= 2, both_years_pos=(y1["mean_daily_pct"] > 0 and y2["mean_daily_pct"] > 0),
                dd_ok=s_all["max_dd_pct"] >= -6.0, null_z_ge_2=z >= 2)
    res["val"] = dict(n_train_rows=ntr, all=s_all, year1=y1, year2=y2, null=dict(z=z, mean=nm, sd=ns), gate=gate,
                      passed=all(gate.values()), detail=K.describe(tr), baselines=K.simple_baselines(data, VAL_START, VAL_END))
    print(json.dumps({k: res["val"][k] for k in ["all", "year1", "year2", "null", "gate", "passed", "baselines"]}, ensure_ascii=False, indent=1), flush=True)
    if res["val"]["passed"] and a.open_final:
        tt = K.run_policy(data, K.predict(models, data, TEST_START, TEST_END), theta)
        tt.to_csv(os.path.join(a.out, "trades_test_q517.csv"), index=False)
        st = K.summarize(tt, TEST_START, TEST_END, r)
        res["test"] = dict(all=st, passed=(st["t_daily"] >= 2 and st["mean_daily_pct"] > 0 and st["max_dd_pct"] >= -6.0))
    else:
        res["test"] = "未開封"
    json.dump(res, open(os.path.join(a.out, "result_q517.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
