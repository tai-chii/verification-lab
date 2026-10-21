import os, sys
import numpy as np, pandas as pd
EXP = sys.argv[1]
sys.path.insert(0, os.path.join(EXP, "..", "..", "tools")); sys.path.insert(0, os.path.join(EXP, "..", "_s04_common")); sys.path.insert(0, EXP)
from fe_core import qlike
import s04ml as M
import kensho_s04b_vol_forecast_sizing_q376 as Q
rng = np.random.default_rng(0)
dfs, missing, dh = M.load_all(Q.SPEC.syms, False, rng, start=Q.SPEC.start)
C, R, COST = M.wide_tables(dfs)
X, y, meta = M.build_panel(dfs, Q._rv_target, Q.FEAT_KW)
es = M.eval_start_of(meta, Q.TRAIN_YEARS)
RV = np.exp(M.target_wide(dfs, Q._rv_target))
sig60 = R.rolling(60, min_periods=30).std()
Xl = X.copy()
for c in ("vol_5","vol_20","vol_60"): Xl[c] = np.log(Xl[c].replace(0, np.nan))
ok = Xl[["vol_5","vol_20","vol_60"]].notna().all(axis=1).to_numpy()
pr = M.wf_predict(Xl.iloc[ok], y.iloc[ok], meta.iloc[ok].reset_index(drop=True), ("ridge",1.0), ["vol_5","vol_20","vol_60"], Q.TRAIN_YEARS, Q.EMBARGO)
p2 = np.exp(pr).reindex(index=R.index, columns=R.columns); ev = RV.reindex_like(p2)
m = (p2.index >= es) & (p2.index < M.SEAL)
# 学習窓の残差から決める補正（前年までの log 残差の分散 → exp(s2/2)）は手間なので、評価窓前の年の比 mean(ev/p2) を使わず、診断として 2 通り
for lab, P in [("sig60", sig60**2), ("har_raw", p2)]:
    P = P.reindex_like(p2); rat = (ev.loc[m]/P.loc[m]).stack()
    print(lab, "QLIKE", round(np.nanmean([qlike(P.loc[m,s].to_numpy(), ev.loc[m,s].to_numpy()) for s in R.columns]),4), "mean(ev/p)", round(rat.mean(),3), "median", round(rat.median(),3))
# 前年までの評価窓外で比を推定（実時間で使える補正）: 年ごとに、その年より前の ev/p2 の平均を掛ける（最初の評価年は学習窓の残差が無いので exp(var/2) を y の残差で）
yrs = p2.index.year
adj = p2.copy()*np.nan
for Y in sorted(set(yrs[m])):
    prior = (yrs < Y) & m
    if prior.sum()==0:
        res = (np.log(ev) - np.log(p2)).loc[yrs==Y-1].stack()  # 不可なら1
        c = 1.0
    else:
        c = float((ev.loc[prior]/p2.loc[prior]).stack().mean())
    adj.loc[yrs==Y] = p2.loc[yrs==Y]*c
mm = m & (yrs > min(yrs[m]))
for lab, P in [("sig60", (sig60**2).reindex_like(p2)), ("har_raw", p2), ("har_adj_realtime", adj)]:
    print("excl_first_year", lab, round(np.nanmean([qlike(P.loc[mm,s].to_numpy(), ev.loc[mm,s].to_numpy()) for s in R.columns]),4))
