import sys, os, numpy as np, pandas as pd; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"run_q565.py")).read()
ns={"__file__":os.path.abspath(__file__)}; exec(src.split("DATA, OUT =")[0], ns)
for s in ["EURUSD","US500","USDJPY"]:
    d=K.load(sys.argv[1],s); rng=np.random.default_rng(1); so=pd.Series(rng.choice([-1.,1.],size=len(d)),index=pd.Index(d["time"]))
    d2=ns["synth"](d,so); c=ns["check"](d,d2)
    bad=((d2.high<d2[["open","close"]].max(1)-1e-12)|(d2.low>d2[["open","close"]].min(1)+1e-12)).sum()
    print(s,{k:round(v,4) for k,v in c.items()},"nan",int(d2[["open","high","low","close","ask_close"]].isna().sum().sum()),"bad_hl",int(bad),
          "px",round(d.close.iloc[-1],3),"->",round(d2.close.iloc[-1],3),"spr_med",round((d.spr/d.close).median()*1e4,3),round((d2.spr/d2.close).median()*1e4,3))
