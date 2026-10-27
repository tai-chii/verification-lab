import numpy as np, pandas as pd, sys
sys.path.insert(0,'.')
import kensho_s21_h1_ml_rr_q515 as K
for s in ["USDJPY","US500"]:
    d=K.load("data",s); R,X,D=K.labels(d,s)
    rng=np.random.default_rng(1); bad=0
    bo,bh,bl,bc=[d[c].to_numpy() for c in ["open","high","low","close"]]
    ao,ah,al,ac=[d["ask_"+c].to_numpy() for c in ["open","high","low","close"]]
    t=d["time"].to_numpy()
    for i in rng.choice(np.where(np.isfinite(R).all(1))[0],300,replace=False):
        for a,(dr,rr) in enumerate(K.ACTIONS):
            e=i+1; P=ao[e] if dr==1 else bo[e]; Dv=D[i]; SL=P-dr*Dv; TP=P+dr*rr*Dv; ex=None
            for j in range(e,e+K.H):
                if dr==1:
                    if bo[j]<=SL: ex=(bo[j],j);break
                    if bl[j]<=SL: ex=(SL,j);break
                    if bh[j]>=TP: ex=(TP,j);break
                else:
                    if ao[j]>=SL: ex=(ao[j],j);break
                    if ah[j]>=SL: ex=(SL,j);break
                    if al[j]<=TP: ex=(TP,j);break
            if ex is None: j=e+K.H-1; ex=((bc[j] if dr==1 else ac[j]),j)
            hold=K.HOLD_RATE[K.CLASS[s]]/8760*((t[ex[1]]-t[e])/np.timedelta64(1,'h'))*P/Dv
            r=dr*(ex[0]-P)/Dv-hold
            if abs(r-R[i,a])>1e-9 or ex[1]!=X[i,a]: bad+=1
    m=np.nanmean(R,0); print(s,"不一致",bad,"/1800","全足平均R",np.round(m,3),"spr_R中央",np.nanmedian(d["spr"]/D).round(3))
