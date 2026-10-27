# -*- coding: utf-8 -*-
"""Q534: Q533 D2 ＋ 週明け（24 時間以上空いたあと）の再開直後 N 本では入らない。事前登録_q534.md。
使い方: python3 kensho_s21_reopen_q534.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z

YEARS = list(range(2014, 2025))


def since_reopen(d):
    """各足が再開から何本目か（再開の足 = 0）。再開 = 前の足から 24 時間以上空いた足。"""
    t = d["time"].to_numpy(); n = len(t)
    re = np.r_[True, (t[1:] - t[:-1]) / np.timedelta64(1, "h") >= Z.BREAK_H]
    k = np.zeros(n, int); c = 10**6
    for j in range(n):
        c = 0 if re[j] else c + 1; k[j] = c
    return k


def block(PP, data, nblock):
    if nblock == 0:
        return PP
    out = {}
    for s, (idx, pr) in PP.items():
        sr = data[s]["_sr"]; keep = sr[np.minimum(idx + 1, len(sr) - 1)] >= nblock  # 入る足 = i+1
        out[s] = (idx[keep], pr[keep])
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    dataw = {}
    for s in J.SYMS15:
        o = J.make(K.load(a.data, s), s); Rw, Xw = Z.labels_wk(o["d"], s)
        dataw[s] = dict(o, R=Rw, X=Xw, _sr=since_reopen(o["d"]))
    print("データ準備 済", flush=True)
    V = {"D2": 0, "E1": 1, "E2": 2}
    TR = {k: [] for k in V}; DY = {k: [] for k in V}
    for Y in YEARS:
        t0 = time.time(); s0, s1 = W.TS(Y), W.TS(Y + 1)
        mw, _ = Q.train_window(dataw, s0, None)
        Pw = K.predict(mw, dataw, s0 - Q.WARM, s1); PPw = J.apply_thr(dataw, Pw, J.thr_series(dataw, Pw), s0)
        msg = []
        for k, nb in V.items():
            tr = K.run_policy(dataw, block(PPw, dataw, nb), 0.0).assign(fold=Y)
            TR[k].append(tr); DY[k].append(K.daily(tr, s0, s1, 1.0))
            msg.append(f"{k} n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f}")
        print(f"{Y}: " + " | ".join(msg) + f" | {time.time()-t0:.0f}s", flush=True)
    res = dict(qid="Q534", run_at=time.strftime("%Y-%m-%d %H:%M"), note="R 単位・H1 判定・2014-10〜2025-09・参考")
    for k in V:
        tr = pd.concat(TR[k]); p = pd.concat(DY[k]).groupby(level=0).sum()
        tr.to_csv(os.path.join(a.out, f"trades_q534_{k}.csv"), index=False)
        wd = pd.to_datetime(tr["exit"], utc=True).dt.weekday
        res[k] = dict(block_bars=V[k], **Z.stats(tr, p, 11), weekend_exits=int((wd >= 5).sum()), weekend_exit_R=round(float(tr.loc[wd >= 5, "R"].sum()), 1))
        print(k, json.dumps({x: res[k][x] for x in ["block_bars", "n", "mean_R", "t", "total_R", "max_dd_R", "annual_R_per_dd", "worst_day_R", "pos_years", "weekend_exits", "weekend_exit_R"]}, ensure_ascii=False), flush=True)
    base = res["D2"]; best = max(["E1", "E2"], key=lambda k: res[k]["t"]); B = res[best]
    res["verdict"] = (f"再開直後は入らないを推す（{best}）" if (B["t"] > base["t"] and B["annual_R_per_dd"] > base["annual_R_per_dd"]) else "差は無い・足さない")
    print("判定", res["verdict"], flush=True)
    json.dump(res, open(os.path.join(a.out, "result_q534.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
