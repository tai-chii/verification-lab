# -*- coding: utf-8 -*-
"""Q546 の集計（事前登録_q546.md の判定）。使い方: python3 analyze_q546.py OUT_DIR TRADES_Q534_E1"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W

OUT, E1 = sys.argv[1], sys.argv[2]
tr = pd.read_csv(os.path.join(OUT, "trades_q546.csv.gz"), parse_dates=["entry", "exit"])
YS = list(range(2016, 2025))
res = {"compare_years": "2016-10〜2025-09（9 年）"}

# a=1 の再現（Q534 E1 の保存済み売買）
e1 = pd.read_csv(E1, parse_dates=["entry", "exit"])
rep = {}
for Y in range(2014, 2025):
    a = tr[(tr.age == 1) & (tr.fold == Y)]; b = e1[e1.fold == Y]
    rep[Y] = dict(n_new=int(len(a)), n_e1=int(len(b)), R_new=round(float(a.R.mean()), 4), R_e1=round(float(b.R.mean()), 4))
res["reproduce_age1_vs_q534E1"] = rep

def daily_all(t):
    return pd.concat([K.daily(t[t.fold == Y], W.TS(Y), W.TS(Y + 1), 1.0) for Y in YS]).groupby(level=0).sum()

for a in (1, 2, 3):
    t = tr[(tr.age == a) & tr.fold.isin(YS)]; p = daily_all(t)
    yrs = {int(Y): round(float(g.R.sum()), 1) for Y, g in t.groupby("fold")}
    res[f"age{a}"] = dict(n=int(len(t)), mean_R=round(float(t.R.mean()), 4), total_R=round(float(t.R.sum()), 1), t=round(K.tstat(p), 2),
                         max_dd_R=round(float(K.maxdd(p.to_numpy())), 1), pos_years=sum(v > 0 for v in yrs.values()), years_R=yrs)
for a in (2, 3):
    d = np.array([tr[(tr.age == a) & (tr.fold == Y)].R.mean() - tr[(tr.age == 1) & (tr.fold == Y)].R.mean() for Y in YS])
    res[f"delta_age{a}_vs_1"] = dict(mean=round(float(d.mean()), 4), t=round(K.tstat(d), 2), by_year=[round(float(x), 4) for x in d])
    res[f"ratio_age{a}"] = round(res[f"age{a}"]["total_R"] / res["age1"]["total_R"], 3)
a3, r3 = res["age3"], res["ratio_age3"]
res["verdict"] = "3 年もつ" if (a3["t"] >= 2 and r3 >= 0.5) else ("劣化する" if r3 < 0.5 else "中間")
json.dump(res, open(os.path.join(OUT, "result_q546.json"), "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
