# -*- coding: utf-8 -*-
"""Q540: S21 の固定した数値の面（SL の ATR 倍率 K × 時間切れ H）。事前登録_q540.md。Q534 E1 と同じ流れを K・H だけ変えて回す。
使い方: python3 run_q540.py DATA_DIR OUT_DIR K H"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
DATA, OUT, KK, HH = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
K.K_ATR, K.H = KK, HH
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z
import kensho_s21_reopen_q534 as E
os.makedirs(OUT, exist_ok=True); t00 = time.time()
dataw = {}
for s in J.SYMS15:
    o = J.make(K.load(DATA, s), s); Rw, Xw = Z.labels_wk(o["d"], s)
    dataw[s] = dict(o, R=Rw, X=Xw, _sr=E.since_reopen(o["d"]))
TR, DY = [], []
for Y in E.YEARS:
    s0, s1 = W.TS(Y), W.TS(Y + 1)
    mw, _ = Q.train_window(dataw, s0, None)
    Pw = K.predict(mw, dataw, s0 - Q.WARM, s1); PPw = J.apply_thr(dataw, Pw, J.thr_series(dataw, Pw), s0)
    tr = K.run_policy(dataw, E.block(PPw, dataw, 1), 0.0).assign(fold=Y)
    TR.append(tr); DY.append(K.daily(tr, s0, s1, 1.0))
    print(f"K={KK} H={HH} {Y}: n={len(tr)} R={tr['R'].mean():.4f} | {time.time()-t00:.0f}s", flush=True)
tr = pd.concat(TR); p = pd.concat(DY).groupby(level=0).sum()
st = Z.stats(tr, p, len(E.YEARS)); st.update(K=KK, H=HH, elapsed_s=round(time.time() - t00))
tag = f"K{KK}_H{HH}"
tr.to_csv(os.path.join(OUT, f"trades_q540_{tag}.csv.gz"), index=False, compression="gzip")
json.dump(st, open(os.path.join(OUT, f"stats_q540_{tag}.json"), "w"), ensure_ascii=False, indent=1, default=str)
print("RESULT", json.dumps({k: st[k] for k in ("K", "H", "n", "mean_R", "t", "total_R", "max_dd_R", "pos_years")}), flush=True)
