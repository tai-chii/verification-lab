# -*- coding: utf-8 -*-
"""Q527: S21 最終形の最終判定（2025-10〜2026-09・1 回だけ）。事前登録_q527.md。
使い方: python3 kensho_s21_final_q527.py --h1 DIR --m1zip DIR --m1pq DIR --spread DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J

K.SIGMA_TARGET = 0.0022
T = lambda s: pd.Timestamp(s, tz="UTC")
S0, S1, SI = T("2025-10-01"), T("2026-10-01"), T("2024-10-01")
YEN = ["USDJPY", "EURJPY", "GBPJPY"] + J.NEW
IDX = ["US500", "USTECH", "GER40", "JPN225"]
GRP = lambda s: "円絡み" if s in YEN else ("指数" if s in IDX else ("金" if s == "XAUUSD" else "円以外FX"))


def main():
    ap = argparse.ArgumentParser()
    for x in ["h1", "m1zip", "m1pq", "spread", "out"]:
        ap.add_argument(f"--{x}", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    data15 = {s: J.make(K.load(a.h1, s), s) for s in J.SYMS15}
    data4 = {}
    for s in J.NEW:
        m1 = J.m1_from_zips(os.path.join(a.m1zip, s)); data4[s] = J.make(J.h1_new(s, m1, a.spread), s); del m1
    print("データ準備 済", flush=True)
    # r: 内側 2024-10〜2025-09（15 銘柄・同じ方策）
    m_in, _ = Q.train_window(data15, SI, None)
    P_in = K.predict(m_in, data15, SI - Q.WARM, S0)
    tri = K.run_policy(data15, J.apply_thr(data15, P_in, J.thr_series(data15, P_in), SI), 0.0)
    pi = K.daily(tri, SI, S0, 1.0); r = min(K.R_CAP, K.SIGMA_TARGET / pi.std())
    # 本番モデル（2025-09-30 まで）→ 最終 1 年
    models, ntr = Q.train_window(data15, S0, None)
    P15 = K.predict(models, data15, S0 - Q.WARM, S1); P4 = K.predict(models, data4, S0 - Q.WARM, S1)
    thr = J.thr_series(data15, P15)
    tr15 = K.run_policy(data15, J.apply_thr(data15, P15, thr, S0), 0.0)
    tr4 = K.run_policy(data4, J.apply_thr(data4, P4, thr, S0), 0.0)
    print(f"r={r:.5f} 学習行={ntr} 取引 15:{len(tr15)} 円クロス4:{len(tr4)}", flush=True)
    # 1 分足で先着判定（1 銘柄ずつ）
    parts = []
    for s in J.SYMS15:
        p = os.path.join(a.m1pq, f"{s}_M1.parquet"); sub = tr15[tr15["sym"] == s]
        m = pd.read_parquet(p, columns=["time", "open", "high", "low", "close"]) if os.path.exists(p) else None
        mm = {s: (m["time"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(), m)} if m is not None else {}
        parts.append(J.resolve(sub, data15, mm)); del m
    for s in J.NEW:
        m1 = J.m1_from_zips(os.path.join(a.m1zip, s)); sub = tr4[tr4["sym"] == s]
        parts.append(J.resolve(sub, data4, {s: (m1["time"].dt.tz_convert(None).to_numpy(), m1)})); del m1
    TR = pd.concat([x for x in parts if len(x)]).assign(r=r); TR["grp"] = TR["sym"].map(GRP)
    for c in ["entry", "exit"]:
        TR[c] = pd.to_datetime(TR[c], utc=True)
    TR.to_csv(os.path.join(a.out, "trades_final_q527.csv"), index=False)

    def stat(X):
        p = K.daily(X.assign(R=X["R_m1"]), S0, S1, r)
        return dict(n=int(len(X)), mean_R=float(X["R_m1"].mean()) if len(X) else None, win=float((X["R_m1"] > 0).mean()) if len(X) else None,
                    t=K.tstat(p), mean_daily_pct=float(p.mean() * 100), max_dd_pct=float(K.maxdd(p.to_numpy()) * 100), total_pct=float(p.sum() * 100))
    allS = stat(TR)
    gate = dict(t_ge_2=allS["t"] >= 2, mean_pos=allS["mean_daily_pct"] > 0, dd_ok=allS["max_dd_pct"] >= -6.0)
    alld = {**data15, **data4}
    z, nm, ns = K.null_z(alld, TR.assign(R=TR["R_m1"]), B=500)
    res = dict(qid="Q527", run_at=time.strftime("%Y-%m-%d %H:%M"), r=r, sigma_target=K.SIGMA_TARGET, inner=dict(n=len(tri), t=K.tstat(pi)),
               all19=allS, gate=gate, passed=all(gate.values()), null=dict(z=z, mean=nm, sd=ns),
               only15=stat(TR[TR["sym"].isin(J.SYMS15)]), only_new4=stat(TR[TR["sym"].isin(J.NEW)]),
               groups={g: stat(x) for g, x in TR.groupby("grp")},
               by_sym=TR.groupby("sym")["R_m1"].agg(["count", "mean"]).round(4).reset_index().to_dict("records"),
               by_month=TR.assign(m=pd.to_datetime(TR["exit"], utc=True).dt.strftime("%Y-%m")).groupby("m")["R_m1"].agg(["count", "sum"]).round(3).reset_index().to_dict("records"),
               amb=TR["amb"].value_counts().to_dict())
    json.dump(res, open(os.path.join(a.out, "result_q527.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: res[k] for k in ["r", "all19", "gate", "passed", "null", "only15", "only_new4", "groups"]}, ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
