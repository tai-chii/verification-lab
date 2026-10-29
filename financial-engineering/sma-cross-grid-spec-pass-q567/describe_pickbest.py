"""Q567 の記述（事前登録の判定には使わない）: 指標ごとに前半（<2017）で最良の組を銘柄ごとに選び、全期間回した等ウェイトの資産推移。
比較: 190 組の等ウェイト、全期間の Sharpe で選んだ後知恵。出力 results/Q567_pickbest_curves.csv・_pairs.csv"""
import importlib.util, numpy as np, pandas as pd
spec=importlib.util.spec_from_file_location("q", "kensho_sma_cross_grid_q567.py"); q=importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
rng=np.random.default_rng(q.SEED)
RULES={"sharpe":"max","calmar":"max","pf":"max","winrate":"max","bp_per_bar":"max","mdd":"min"}
curves=[]; picks=[]
for tf in ("D1","H4"):
    py=q.TFS[tf]["per_year"]; port={k:[] for k in list(RULES)+["ew190","hind_sharpe"]}
    for s in q.SYMS:
        if not q.exists_sym(s, q.TFS[tf]["kind"]): continue
        df=q.load_tf(s,tf,False,rng); c=df["close"].values; cb=q.cost_bp_oneway(s,c); w=q.weight_vec(df); P=q.pos_matrix(c)
        R=q.r_eq_matrix(P,c,w,cb); PB=q.pnl_bp_matrix(P,c,cb); hv=q.halves(df)
        if hv["pre"].sum()<q.WARMUP+50 or hv["post"].sum()<q.WARMUP+50: continue
        pre=q.metrics_block(R[hv["pre"]],PB[hv["pre"]],P[hv["pre"]],df["month"].values[hv["pre"]],py)
        al=q.metrics_block(R,PB,P,df["month"].values,py,light=True)
        t=pd.to_datetime(df["time"].values)
        for k,how in RULES.items():
            v=np.nan_to_num(pre[k], nan=(-1e9 if how=="max" else 1e9)); j=int(np.argmax(v) if how=="max" else np.argmin(v))
            port[k].append(pd.Series(R[:,j],index=t,name=s)); picks.append({"tf":tf,"rule":k,"sym":s,"S":q.PAIRS[j][0],"L":q.PAIRS[j][1],"pre_value":float(pre[k][j])})
        port["ew190"].append(pd.Series(R.mean(1),index=t,name=s))
        j=int(np.nanargmax(al["sharpe"])); port["hind_sharpe"].append(pd.Series(R[:,j],index=t,name=s))
        picks.append({"tf":tf,"rule":"hind_sharpe","sym":s,"S":q.PAIRS[j][0],"L":q.PAIRS[j][1],"pre_value":float(al["sharpe"][j])})
    for k,lst in port.items():
        m=pd.concat(lst,axis=1).fillna(0.0).mean(1)
        m=np.log1p(m).groupby(m.index.normalize()).sum().pipe(np.expm1)
        curves.append(pd.DataFrame({"tf":tf,"rule":k,"date":m.index,"r":m.values}))
pd.concat(curves).to_csv("results/Q567_pickbest_curves.csv",index=False); pd.DataFrame(picks).to_csv("results/Q567_pickbest_pairs.csv",index=False)
print("ok")
