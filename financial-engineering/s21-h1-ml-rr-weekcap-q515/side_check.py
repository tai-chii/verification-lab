# 副次（判定に使わない）: モデルが選んだ行動はそのまま、時刻だけ同じ銘柄・同じ週の中でランダムにした帰無
import numpy as np, pandas as pd, sys, json
sys.path.insert(0,'.'); import kensho_s21_h1_ml_rr_q515 as K
tr=pd.read_csv('results/trades_val.csv')
data={}
for s in tr.sym.unique():
    d=K.load('data',s); R,X,D=K.labels(d,s)
    wk=d['time'].dt.tz_convert(None).dt.to_period('W-SUN').astype(str).to_numpy()
    data[s]=(R,wk)
rng=np.random.default_rng(1); groups=[]
for (s,w),g in tr.groupby(['sym','week']):
    R,wk=data[s]; cand=np.where((wk==w)&np.isfinite(R).all(1))[0]; groups.append((s,cand,g['a'].to_numpy()))
null=[]
for b in range(500):
    tot=n=0
    for s,cand,acts in groups:
        ii=rng.choice(cand,size=min(len(acts),len(cand)),replace=False); tot+=data[s][0][ii,acts[:len(ii)]].sum(); n+=len(ii)
    null.append(tot/n)
null=np.array(null); obs=tr.R.mean()
print(json.dumps(dict(obs=obs,null_mean=null.mean(),null_sd=null.std(ddof=1),z=(obs-null.mean())/null.std(ddof=1)),ensure_ascii=False))
tr['dir']=np.where(tr.a<3,'買','売'); tr['y']=pd.to_datetime(tr.entry).dt.year
print(tr.groupby('dir').R.agg(['count','mean']).round(3))
print(tr.groupby(tr.sym.isin(['US500','USTECH','GER40','JPN225'])).R.agg(['count','mean']).round(3))
