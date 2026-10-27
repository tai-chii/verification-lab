# -*- coding: utf-8 -*-
"""Q522: Q521 の設計（σ 目標 0.22%/日）を仮判断（2023-10〜2025-09）にかけ、合格時のみ最終判断（2025-10〜2026-09）も開ける。
事前登録_q522.md。使い方: python3 kensho_s21f_holdout_q522.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_mtf_wf_q521 as M

K.SIGMA_TARGET = 0.0022
T = lambda s: pd.Timestamp(s, tz="UTC")
VAL0, VALM, VAL1 = T("2023-10-01"), T("2024-10-01"), T("2025-10-01")
TEST1 = T("2026-10-01")


def block(data, s0, s1, si):
    m_in, _ = Q.train_window(data, si, None)
    tri = Q.rel_policy_trades(data, m_in, si, s0); pi = K.daily(tri, si, s0, 1.0)
    r = min(K.R_CAP, K.SIGMA_TARGET / pi.std()) if pi.std() > 0 else K.R_CAP
    models, ntr = Q.train_window(data, s0, None)
    tr = Q.rel_policy_trades(data, models, s0, s1).assign(r=r)
    return tr, r, ntr, dict(n=len(tri), t=K.tstat(pi))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("ラベル・特徴量", flush=True); data = M.build(a.data)
    res = dict(qid="Q522", run_at=time.strftime("%Y-%m-%d %H:%M"), sigma_target=K.SIGMA_TARGET)
    tr, r, ntr, inner = block(data, VAL0, VAL1, VAL0 - pd.DateOffset(years=1))
    tr.to_csv(os.path.join(a.out, "trades_val_q522.csv"), index=False)
    s_all = K.summarize(tr, VAL0, VAL1, r)
    y1 = K.summarize(tr[tr["entry"] < VALM], VAL0, VALM, r); y2 = K.summarize(tr[tr["entry"] >= VALM], VALM, VAL1, r)
    z, nm, ns = K.null_z(data, tr, B=500)
    gate = dict(t_ge_2=s_all["t_daily"] >= 2, both_years_pos=(y1["mean_daily_pct"] > 0 and y2["mean_daily_pct"] > 0),
                dd_ok=s_all["max_dd_pct"] >= -6.0, null_z_ge_2=z >= 2)
    passed = all(gate.values())
    res["val"] = dict(r=r, n_train=ntr, inner=inner, all=s_all, year1=y1, year2=y2, null=dict(z=z, mean=nm, sd=ns), gate=gate, passed=passed,
                      groups=Q.group_stats(tr), detail=K.describe(tr))
    print(json.dumps({k: res["val"][k] for k in ["r", "all", "year1", "year2", "null", "gate", "passed"]}, ensure_ascii=False, indent=1), flush=True)
    json.dump(res, open(os.path.join(a.out, "result_q522.json"), "w"), ensure_ascii=False, indent=1, default=str)
    if passed:
        print("仮判断 合格 → 最終判断を開ける", flush=True)
        tt, rt, ntt, inn2 = block(data, VAL1, TEST1, VAL1 - pd.DateOffset(years=1))
        tt.to_csv(os.path.join(a.out, "trades_test_q522.csv"), index=False)
        st = K.summarize(tt, VAL1, TEST1, rt)
        res["test"] = dict(r=rt, n_train=ntt, inner=inn2, all=st, passed=(st["t_daily"] >= 2 and st["mean_daily_pct"] > 0 and st["max_dd_pct"] >= -6.0),
                           groups=Q.group_stats(tt), detail=K.describe(tt))
        print(json.dumps({k: res["test"][k] for k in ["r", "all", "passed"]}, ensure_ascii=False, indent=1), flush=True)
    else:
        res["test"] = "未開封（仮判断不合格）"
    json.dump(res, open(os.path.join(a.out, "result_q522.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
