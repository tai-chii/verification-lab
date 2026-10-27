# -*- coding: utf-8 -*-
"""Q533: 週末をまたいで持たない（市場が 24 時間以上止まる直前の H1 足の終値で決済）。事前登録_q533.md。
使い方: python3 kensho_s21_noweekend_q533.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J

YEARS = list(range(2014, 2025))
BREAK_H = 24


def cut_index(d):
    """各足 j について、j 以降で最初の「次の足まで 24 時間以上空く足」の index。"""
    t = d["time"].to_numpy(); n = len(t)
    gap = np.r_[(t[1:] - t[:-1]) / np.timedelta64(1, "h") >= BREAK_H, True]
    cut = np.empty(n, int); nxt = n - 1
    for j in range(n - 1, -1, -1):
        if gap[j]:
            nxt = j
        cut[j] = nxt
    return cut


def labels_wk(d, sym):
    """K.labels と同じ。ただし週末前の足（cut）の終値で強制決済。"""
    n = len(d); H = K.H
    bo, bh, bl, bc = (d[c].to_numpy(float) for c in ["open", "high", "low", "close"])
    ao, ah, al, ac = (d[f"ask_{c}"].to_numpy(float) for c in ["open", "high", "low", "close"])
    tr = np.maximum(bh - bl, np.maximum(np.abs(bh - np.r_[bc[0], bc[:-1]]), np.abs(bl - np.r_[bc[0], bc[:-1]])))
    atr = pd.Series(tr).rolling(24, min_periods=24).mean().to_numpy()
    D = K.K_ATR * atr
    R = np.full((n, len(K.ACTIONS)), np.nan); X = np.full((n, len(K.ACTIONS)), -1, int)
    idx = np.where(np.isfinite(D) & (np.arange(n) + H < n))[0]; e = idx + 1
    cut = cut_index(d)[e]
    tt = d["time"].to_numpy()
    nforced = 0
    for a, (dr, rr) in enumerate(K.ACTIONS):
        Dv = D[idx]; P = ao[e] if dr == 1 else bo[e]
        SL = P - dr * Dv; TP = P + dr * rr * Dv
        exitp = np.full(len(idx), np.nan); exitj = np.full(len(idx), -1); open_ = np.ones(len(idx), bool)
        for k in range(H):
            j = e + k
            if dr == 1:
                o, lo, hi = bo[j], bl[j], bh[j]
                gap = open_ & (o <= SL); sl = open_ & ~gap & (lo <= SL); tp = open_ & ~gap & ~sl & (hi >= TP)
            else:
                o, lo, hi = ao[j], al[j], ah[j]
                gap = open_ & (o >= SL); sl = open_ & ~gap & (hi >= SL); tp = open_ & ~gap & ~sl & (lo <= TP)
            exitp[gap] = o[gap]; exitp[sl] = SL[sl]; exitp[tp] = TP[tp]
            hit = gap | sl | tp; exitj[hit] = j[hit]; open_ &= ~hit
            fc = open_ & (j == cut)  # 週末前の足の終値で決済
            if fc.any():
                cl = bc[j] if dr == 1 else ac[j]
                exitp[fc] = cl[fc]; exitj[fc] = j[fc]; open_ &= ~fc
                if a == 0:
                    nforced += int(fc.sum())
            if not open_.any():
                break
        jt = e + H - 1; last = bc[jt] if dr == 1 else ac[jt]
        exitp[open_] = last[open_]; exitj[open_] = jt[open_]
        held_h = (tt[exitj] - tt[e]) / np.timedelta64(1, "h")
        hold_R = K.HOLD_RATE[K.CLASS[sym]] / 8760 * held_h * P / Dv
        R[idx, a] = dr * (exitp - P) / Dv - hold_R; X[idx, a] = exitj
    return R, X


def daily(tr, s0, s1):
    return K.daily(tr, s0, s1, 1.0)


def stats(tr, p, years):
    yrs = {int(Y): round(float(g["R"].sum()), 1) for Y, g in tr.groupby("fold")}
    dd = K.maxdd(p.to_numpy()); ann = tr["R"].sum() / years
    return dict(n=int(len(tr)), mean_R=float(tr["R"].mean()), win=float((tr["R"] > 0).mean()), t=K.tstat(p), total_R=float(tr["R"].sum()),
                max_dd_R=float(dd), annual_R_per_dd=float(ann / -dd), worst_day_R=float(p.min()), pos_years=sum(1 for v in yrs.values() if v > 0),
                years_R=yrs, mean_hold_h=float(((pd.to_datetime(tr["exit"], utc=True) - pd.to_datetime(tr["entry"], utc=True)).dt.total_seconds() / 3600).mean()))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = {s: J.make(K.load(a.data, s), s) for s in J.SYMS15}
    dataw = {}
    for s, o in data.items():
        Rw, Xw = labels_wk(o["d"], s)
        dataw[s] = dict(o, R=Rw, X=Xw)
    print("データ準備 済", flush=True)
    TR = {k: [] for k in ["A", "D1", "D2"]}; DY = {k: [] for k in TR}
    for Y in YEARS:
        t0 = time.time(); s0, s1 = W.TS(Y), W.TS(Y + 1)
        m, _ = Q.train_window(data, s0, None)
        P = K.predict(m, data, s0 - Q.WARM, s1); PP = J.apply_thr(data, P, J.thr_series(data, P), s0)
        mw, _ = Q.train_window(dataw, s0, None)
        Pw = K.predict(mw, dataw, s0 - Q.WARM, s1); PPw = J.apply_thr(dataw, Pw, J.thr_series(dataw, Pw), s0)
        msg = []
        for k, dd_, pp in [("A", data, PP), ("D1", dataw, PP), ("D2", dataw, PPw)]:
            tr = K.run_policy(dd_, pp, 0.0).assign(fold=Y)
            TR[k].append(tr); DY[k].append(daily(tr, s0, s1))
            msg.append(f"{k} n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f}")
        print(f"{Y}: " + " | ".join(msg) + f" | {time.time()-t0:.0f}s", flush=True)
    res = dict(qid="Q533", run_at=time.strftime("%Y-%m-%d %H:%M"), note="R 単位・H1 判定・2014-10〜2025-09・参考")
    lab = {"A": "現行（週末も持つ）", "D1": "同じモデル・週末前に決済", "D2": "週末前決済で学習し直し・週末前に決済"}
    for k in TR:
        tr = pd.concat(TR[k]); p = pd.concat(DY[k]).groupby(level=0).sum()
        tr.to_csv(os.path.join(a.out, f"trades_q533_{k}.csv"), index=False)
        wd = pd.to_datetime(tr["exit"], utc=True).dt.weekday
        res[k] = dict(label=lab[k], **stats(tr, p, 11), weekend_exits=int((wd >= 5).sum()), weekend_exit_R=round(float(tr.loc[wd >= 5, "R"].sum()), 1))
        print(k, json.dumps({x: res[k][x] for x in ["label", "n", "mean_R", "t", "total_R", "max_dd_R", "annual_R_per_dd", "worst_day_R", "pos_years", "mean_hold_h", "weekend_exits", "weekend_exit_R"]}, ensure_ascii=False), flush=True)
    A = res["A"]; best = max(["D1", "D2"], key=lambda k: res[k]["t"])
    B = res[best]
    res["verdict"] = (f"週末前に決済を推す（{best}）" if (B["t"] > A["t"] and B["annual_R_per_dd"] > A["annual_R_per_dd"])
                      else ("現行のまま（週末も持つ）" if (B["t"] < A["t"] and B["annual_R_per_dd"] < A["annual_R_per_dd"]) else "差は無い"))
    print("判定", res["verdict"], flush=True)
    json.dump(res, open(os.path.join(a.out, "result_q533.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
