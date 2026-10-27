# -*- coding: utf-8 -*-
"""Q548: S23 の優位は少数の上昇局面に頼っているか（事前登録_q548.md）。run_q529.py をそのまま使う。
使い方: python3 run_q548.py --h1 DIR --out DIR"""
import argparse, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "s22-crypto-ml-fintokei-q528"))
import types; sys.modules.setdefault("lightgbm", types.ModuleType("lightgbm"))  # crypto_core が読むだけで、ここでは使わない
import run_q529 as Q

DEV = (pd.Timestamp("2018-01-01"), pd.Timestamp("2025-10-01"))


def st(p):
    p = p[(p.index >= DEV[0]) & (p.index < DEV[1])]
    eq = (1 + p).cumprod()
    return dict(sharpe=round(float(p.mean() / p.std() * np.sqrt(252)), 3), max_dd=round(float((eq / eq.cummax() - 1).min()), 3), total=round(float(eq.iloc[-1] - 1), 3))


ap = argparse.ArgumentParser(); ap.add_argument("--h1", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
bs = {c: Q.daily_series(a.h1, c) for c in ["BTC", "ETH"]}
for c in bs:
    bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
pos = {c: Q.tsmom(bs[c], 60) for c in bs}
s23 = {c: Q.backtest(bs[c], pos[c], Q.HALF[c]) for c in bs}
bh = {c: Q.backtest(bs[c], np.ones(len(bs[c])), Q.HALF[c]) for c in bs}
res = {"reproduce": dict(s23=st(Q.combine(list(s23.values()))), buy_hold=st(Q.combine(list(bh.values()))))}
# 保有区間（pos[t]=1 の日 t の損益は s23 の t の行。backtest は pos[t] を exec_t→exec_{t+1} に当てる）
eps = []
for c in bs:
    idx = bs[c].index; p = pos[c]; inwin = (idx >= DEV[0]) & (idx < DEV[1])
    k = 0
    while k < len(p):
        if p[k] == 1:
            j = k
            while j + 1 < len(p) and p[j + 1] == 1:
                j += 1
            days = idx[k:j + 2]  # 降りる日のコストまで含める
            days = days[(days >= DEV[0]) & (days < DEV[1])]
            if len(days):
                eps.append(dict(coin=c, start=str(idx[k].date()), end=str(idx[min(j + 1, len(idx) - 1)].date()), n_days=int(j - k + 1),
                                pnl=float(s23[c].loc[days].sum()), days=days))
            k = j + 1
        else:
            k += 1
eps.sort(key=lambda e: -e["pnl"]); tot = sum(e["pnl"] for e in eps)
res["episodes"] = dict(n=len(eps), mean_days=round(float(np.mean([e["n_days"] for e in eps])), 1), total_pnl_sum=round(tot, 3),
                       top10=[{k: (round(v, 3) if isinstance(v, float) else v) for k, v in e.items() if k != "days"} for e in eps[:10]])
for k in (1, 3, 5):
    res["episodes"][f"top{k}_share"] = round(sum(e["pnl"] for e in eps[:k]) / tot, 3)
    a_, b_ = {c: s23[c].copy() for c in bs}, {c: bh[c].copy() for c in bs}
    for e in eps[:k]:
        a_[e["coin"]].loc[e["days"]] = 0.0; b_[e["coin"]].loc[e["days"]] = 0.0
    res[f"drop_top{k}"] = dict(s23=st(Q.combine(list(a_.values()))), buy_hold=st(Q.combine(list(b_.values()))))
d = lambda k: res[f"drop_top{k}"]
r3 = d(3)["s23"]["sharpe"] > d(3)["buy_hold"]["sharpe"] and d(3)["s23"]["max_dd"] > d(3)["buy_hold"]["max_dd"]
r1 = d(1)["s23"]["sharpe"] <= d(1)["buy_hold"]["sharpe"]
res["verdict"] = "偏りに頑健" if r3 else ("偏る" if r1 else "中間")
cs, cb = Q.combine(list(s23.values())), Q.combine(list(bh.values()))
res["by_year_sharpe"] = {int(y): dict(s23=round(float(g.mean() / g.std() * np.sqrt(252)), 2), buy_hold=round(float(cb.loc[g.index].mean() / cb.loc[g.index].std() * np.sqrt(252)), 2))
                         for y, g in cs[(cs.index >= DEV[0]) & (cs.index < DEV[1])].groupby(cs[(cs.index >= DEV[0]) & (cs.index < DEV[1])].index.year)}
json.dump(res, open(os.path.join(a.out, "result_q548.json"), "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
