# -*- coding: utf-8 -*-
"""Q531: XAUUSD を取引する bot — 15 銘柄で学習 vs XAUUSD だけで学習。事前登録_q531.md。
使い方: python3 kensho_s21_xau_q531.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J

YEARS = list(range(2014, 2025))
X = "XAUUSD"


def daily(tr, s0, s1):
    """決済日に計上。土日の決済は翌月曜に寄せる（K.daily は土日を落としていた）。"""
    days = pd.bdate_range(s0.tz_convert(None).normalize(), (s1 - pd.Timedelta(days=1)).tz_convert(None).normalize() + pd.Timedelta(days=3))
    if len(tr) == 0:
        return pd.Series(0.0, index=days)
    d = tr["exit"].dt.tz_convert(None).dt.normalize(); wd = d.dt.weekday
    d = d + pd.to_timedelta(np.where(wd == 5, 2, np.where(wd == 6, 1, 0)), unit="D")
    return tr.assign(day=d).groupby("day")["R"].sum().reindex(days, fill_value=0.0)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = {s: J.make(K.load(a.data, s), s) for s in J.SYMS15}
    dX = {X: data[X]}
    print("データ準備 済", flush=True)
    TR = {k: [] for k in "ABC"}; DY = {k: [] for k in "ABC"}
    for Y in YEARS:
        t0 = time.time(); s0, s1 = W.TS(Y), W.TS(Y + 1)
        m15, n15 = Q.train_window(data, s0, None)
        mX, nX = Q.train_window(dX, s0, None)
        P15 = K.predict(m15, data, s0 - Q.WARM, s1)
        PX15 = {X: P15[X]}
        PXX = K.predict(mX, dX, s0 - Q.WARM, s1)
        sets = {"A": J.apply_thr(dX, PX15, J.thr_series(data, P15), s0),
                "B": J.apply_thr(dX, PX15, J.thr_series(dX, PX15), s0),
                "C": J.apply_thr(dX, PXX, J.thr_series(dX, PXX), s0)}
        msg = []
        for k, PP in sets.items():
            tr = K.run_policy(dX, PP, 0.0).assign(fold=Y)
            TR[k].append(tr); DY[k].append(daily(tr, s0, s1))
            msg.append(f"{k} n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.1f}")
        print(f"{Y}: 学習行 15={n15} X={nX} | " + " | ".join(msg) + f" | {time.time()-t0:.0f}s", flush=True)
    res = dict(qid="Q531", run_at=time.strftime("%Y-%m-%d %H:%M"), note="R 単位・H1 判定・2014-10〜2025-09・参考")
    lab = {"A": "15銘柄で学習・閾値15銘柄", "B": "15銘柄で学習・閾値XAUのみ", "C": "XAUのみで学習・閾値XAUのみ"}
    for k in "ABC":
        tr = pd.concat(TR[k]); p = pd.concat(DY[k]); p = p.groupby(level=0).sum()
        tr.to_csv(os.path.join(a.out, f"trades_q531_{k}.csv"), index=False)
        yrs = {int(Y): round(float(g["R"].sum()), 1) for Y, g in tr.groupby("fold")}
        res[k] = dict(label=lab[k], n=int(len(tr)), mean_R=float(tr["R"].mean()), win=float((tr["R"] > 0).mean()), t=K.tstat(p),
                      total_R=float(tr["R"].sum()), max_dd_R=float(K.maxdd(p.to_numpy())), pos_years=sum(1 for v in yrs.values() if v > 0),
                      years_R=yrs)
        print(k, json.dumps({x: res[k][x] for x in ["label", "n", "mean_R", "t", "total_R", "max_dd_R", "pos_years", "years_R"]}, ensure_ascii=False), flush=True)
    c, b = res["C"], res["B"]
    res["verdict"] = "XAUのみで学習を推す" if (c["t"] > b["t"] and c["mean_R"] > b["mean_R"]) else ("15銘柄で学習を推す" if (c["t"] < b["t"] and c["mean_R"] < b["mean_R"]) else "差は無い")
    print("判定", res["verdict"], flush=True)
    json.dump(res, open(os.path.join(a.out, "result_q531.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
