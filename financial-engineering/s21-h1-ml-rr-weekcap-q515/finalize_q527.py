# Q527 の集計だけをやり直す（取引表 trades_final_q527.csv は確定済み・作り直さない）。集計コードの不具合（空の表を連結して日付列が文字列になった）の修正
import sys, json, os, time
import numpy as np, pandas as pd
sys.argv = [sys.argv[0]]
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21f_newjpy_q524 as J
import kensho_s21_final_q527 as F
TR = pd.read_csv("results/trades_final_q527.csv")
for c in ["entry", "exit"]:
    TR[c] = pd.to_datetime(TR[c], utc=True)
r = float(TR["r"].iloc[0]); S0, S1 = F.S0, F.S1
data15 = {s: J.make(K.load("data", s), s) for s in J.SYMS15}
data4 = {}
for s in J.NEW:
    m1 = J.m1_from_zips(os.path.join("m1", s)); data4[s] = J.make(J.h1_new(s, m1, "d1"), s); del m1
def stat(X):
    p = K.daily(X.assign(R=X["R_m1"]), S0, S1, r)
    return dict(n=int(len(X)), mean_R=float(X["R_m1"].mean()) if len(X) else None, win=float((X["R_m1"] > 0).mean()) if len(X) else None,
                t=K.tstat(p), mean_daily_pct=float(p.mean() * 100), max_dd_pct=float(K.maxdd(p.to_numpy()) * 100), total_pct=float(p.sum() * 100))
allS = stat(TR)
gate = dict(t_ge_2=allS["t"] >= 2, mean_pos=allS["mean_daily_pct"] > 0, dd_ok=allS["max_dd_pct"] >= -6.0)
z, nm, ns = K.null_z({**data15, **data4}, TR.assign(R=TR["R_m1"]), B=500)
res = dict(qid="Q527", run_at=time.strftime("%Y-%m-%d %H:%M"), r=r, sigma_target=0.0022,
           all19=allS, gate=gate, passed=all(gate.values()), null=dict(z=z, mean=nm, sd=ns),
           only15=stat(TR[TR["sym"].isin(J.SYMS15)]), only_new4=stat(TR[TR["sym"].isin(J.NEW)]),
           groups={g: stat(x) for g, x in TR.groupby("grp")},
           by_sym=TR.groupby("sym")["R_m1"].agg(["count", "mean"]).round(4).reset_index().to_dict("records"),
           by_month=TR.assign(m=TR["exit"].dt.strftime("%Y-%m")).groupby("m")["R_m1"].agg(["count", "sum"]).round(3).reset_index().to_dict("records"),
           amb=TR["amb"].fillna("").value_counts().to_dict(),
           note="取引は kensho_s21_final_q527.py の 1 回目の実行で確定。集計だけ finalize_q527.py でやり直した（日付列の型の不具合）")
json.dump(res, open("results/result_q527.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: res[k] for k in ["r", "all19", "gate", "passed", "null", "only15", "only_new4", "groups", "by_sym", "by_month", "amb"]}, ensure_ascii=False, indent=1))
