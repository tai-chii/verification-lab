import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K, kensho_s21_walkforward_q518 as W, kensho_s21d_relthr_wf_q519 as Q, kensho_s21f_newjpy_q524 as J, kensho_s21_noweekend_q533 as Z, kensho_s21_reopen_q534 as E
t=time.time(); dataw={}
for s in J.SYMS15:
    o=J.make(K.load(sys.argv[1],s),s); Rw,Xw=Z.labels_wk(o["d"],s); dataw[s]=dict(o,R=Rw,X=Xw,_sr=E.since_reopen(o["d"]))
print("prep",time.time()-t,flush=True); K.SEED=1; Y=2014; s0,s1=W.TS(Y),W.TS(Y+1)
m,_=Q.train_window(dataw,s0,None); P=K.predict(m,dataw,s0-Q.WARM,s1); PP=J.apply_thr(dataw,P,J.thr_series(dataw,P),s0)
tr=K.run_policy(dataw,E.block(PP,dataw,1),0.0); print(f"2014 n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f} (Q547 seed1: n=2387 R=0.0666 sum=159)", time.time()-t)
