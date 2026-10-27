# -*- coding: utf-8 -*-
"""Q553 用: Q534 E1 と同じ流れで 2025 年度（2025-10〜2026-09）だけを回す（記述用）。"""
import os, sys, time
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K, kensho_s21_walkforward_q518 as W, kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J, kensho_s21_noweekend_q533 as Z, kensho_s21_reopen_q534 as E
DATA, OUT = sys.argv[1], sys.argv[2]; t0 = time.time(); dataw = {}
for s in J.SYMS15:
    o = J.make(K.load(DATA, s), s); Rw, Xw = Z.labels_wk(o["d"], s); dataw[s] = dict(o, R=Rw, X=Xw, _sr=E.since_reopen(o["d"]))
Y = 2025; s0, s1 = W.TS(Y), W.TS(Y + 1)
m, _ = Q.train_window(dataw, s0, None)
P = K.predict(m, dataw, s0 - Q.WARM, s1); PP = J.apply_thr(dataw, P, J.thr_series(dataw, P), s0)
tr = K.run_policy(dataw, E.block(PP, dataw, 1), 0.0).assign(fold=Y)
tr.to_csv(os.path.join(OUT, "trades_q553_fold2025.csv"), index=False); print("n", len(tr), "R", round(tr.R.mean(), 4), "sum", round(tr.R.sum(), 1), round(time.time() - t0), "s")
