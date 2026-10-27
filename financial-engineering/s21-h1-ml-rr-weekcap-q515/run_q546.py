# -*- coding: utf-8 -*-
"""Q546: S21 の凍結モデルは学習し直さずに何年もつか（事前登録_q546.md）。Q534 E1 と同じ流れで、起点 A で 1 回学習したモデルを
A, A+1, A+2 年度に当てる（古さ 1・2・3 年目）。使い方: python3 run_q546.py DATA_DIR OUT_DIR"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z
import kensho_s21_reopen_q534 as E

DATA, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True); t00 = time.time()
ANCHORS = list(range(2014, 2025)); AGES = (1, 2, 3); LAST = 2024
dataw = {}
for s in J.SYMS15:
    o = J.make(K.load(DATA, s), s); Rw, Xw = Z.labels_wk(o["d"], s)
    dataw[s] = dict(o, R=Rw, X=Xw, _sr=E.since_reopen(o["d"]))
print(f"データ準備 済 {time.time()-t00:.0f}s", flush=True)
TR = []
for A in ANCHORS:
    m, _ = Q.train_window(dataw, W.TS(A), None)
    for a in AGES:
        Y = A + a - 1
        if Y > LAST:
            continue
        s0, s1 = W.TS(Y), W.TS(Y + 1)
        P = K.predict(m, dataw, s0 - Q.WARM, s1); PP = J.apply_thr(dataw, P, J.thr_series(dataw, P), s0)
        tr = K.run_policy(dataw, E.block(PP, dataw, 1), 0.0).assign(fold=Y, anchor=A, age=a)
        TR.append(tr)
        print(f"A={A} Y={Y} age={a}: n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f} | {time.time()-t00:.0f}s", flush=True)
    pd.concat(TR).to_csv(os.path.join(OUT, "trades_q546.csv.gz"), index=False, compression="gzip")
tr = pd.concat(TR); tr.to_csv(os.path.join(OUT, "trades_q546.csv.gz"), index=False, compression="gzip")
print("done", round(time.time() - t00), flush=True)
