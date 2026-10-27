# -*- coding: utf-8 -*-
"""Q547: S21（Q534 E1 の流れ）を LightGBM の種だけ変えて WF 11 年を回す（事前登録_q547.md）。
使い方: python3 run_q547.py DATA_DIR OUT_DIR SEED [SEED ...]"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z
import kensho_s21_reopen_q534 as E

DATA, OUT = sys.argv[1], sys.argv[2]; SEEDS = [int(x) for x in sys.argv[3:]]; os.makedirs(OUT, exist_ok=True); t00 = time.time()
dataw = {}
for s in J.SYMS15:
    o = J.make(K.load(DATA, s), s); Rw, Xw = Z.labels_wk(o["d"], s)
    dataw[s] = dict(o, R=Rw, X=Xw, _sr=E.since_reopen(o["d"]))
print(f"データ準備 済 {time.time()-t00:.0f}s", flush=True)
for sd in SEEDS:
    K.SEED = sd; TR, DY = [], []
    for Y in E.YEARS:
        s0, s1 = W.TS(Y), W.TS(Y + 1)
        m, _ = Q.train_window(dataw, s0, None)
        P = K.predict(m, dataw, s0 - Q.WARM, s1); PP = J.apply_thr(dataw, P, J.thr_series(dataw, P), s0)
        tr = K.run_policy(dataw, E.block(PP, dataw, 1), 0.0).assign(fold=Y)
        TR.append(tr); DY.append(K.daily(tr, s0, s1, 1.0))
        print(f"seed={sd} {Y}: n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f} | {time.time()-t00:.0f}s", flush=True)
    tr = pd.concat(TR); p = pd.concat(DY).groupby(level=0).sum()
    st = Z.stats(tr, p, len(E.YEARS)); st["seed"] = sd
    tr.to_csv(os.path.join(OUT, f"trades_q547_seed{sd}.csv.gz"), index=False, compression="gzip")
    json.dump(st, open(os.path.join(OUT, f"stats_q547_seed{sd}.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("RESULT", json.dumps({k: st[k] for k in ("seed", "n", "mean_R", "t", "total_R", "max_dd_R", "pos_years")}), flush=True)
print("done", round(time.time() - t00), flush=True)
