# -*- coding: utf-8 -*-
"""Q530: S21 最終形の売買制限（1 銘柄同時 1 本・1 銘柄週 10 回）を外すと何が変わるか。事前登録_q530.md。
同じモデル・同じ予測・同じ閾値に 3 通りの制限を当てる（WF 2014-10〜2023-09・15 銘柄・R 単位・H1 判定）。
使い方: python3 kensho_s21_nocap_q530.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J

VARIANTS = {"A_現行": dict(one=True, cap=10), "B_週上限なし": dict(one=True, cap=None), "C_上限なし": dict(one=False, cap=None)}


def run_policy_v(data, P, one, cap):
    rows = []
    for s, (idx, pr) in P.items():
        o = data[s]; t = o["time"]
        week = (t.dt.tz_convert(None).dt.to_period("W-SUN")).to_numpy()
        busy_until = -1; wk = None; cnt = 0
        best = pr.argmax(1) if len(pr) else np.array([], int); bv = pr.max(1) if len(pr) else np.array([])
        for k, i in enumerate(idx):
            if week[i] != wk:
                wk = week[i]; cnt = 0
            if bv[k] <= 0.0 or (one and i < busy_until) or (cap is not None and cnt >= cap):
                continue
            a = best[k]; x = o["X"][i, a]
            rows.append((s, i, t.iloc[i + 1], t.iloc[x], int(a), o["R"][i, a], bv[k], str(wk)))
            busy_until = max(busy_until, x); cnt += 1
    return pd.DataFrame(rows, columns=["sym", "i", "entry", "exit", "a", "R", "pred", "week"])


def concurrency(tr):
    ev = pd.concat([pd.DataFrame({"t": tr["entry"], "d": 1}), pd.DataFrame({"t": tr["exit"], "d": -1})])
    ev = ev.sort_values(["t", "d"])  # 同時刻は決済を先に
    c = ev["d"].cumsum().to_numpy()
    same = 0
    for s, g in tr.groupby("sym"):
        e = pd.concat([pd.DataFrame({"t": g["entry"], "d": 1}), pd.DataFrame({"t": g["exit"], "d": -1})]).sort_values(["t", "d"])
        same = max(same, int(e["d"].cumsum().max()))
    # 時間加重の平均本数
    tt = ev["t"].to_numpy(); dur = np.diff(tt).astype("timedelta64[s]").astype(float)
    avg = float((c[:-1] * dur).sum() / dur.sum()) if dur.sum() > 0 else 0.0
    return dict(max_all=int(c.max()), p99_all=float(np.percentile(c, 99)), avg_all_time_weighted=round(avg, 2), max_same_sym=same)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = {s: J.make(K.load(a.data, s), s) for s in J.SYMS15}
    print("データ準備 済", flush=True)
    TR = {v: [] for v in VARIANTS}; DY = {v: [] for v in VARIANTS}
    for Y in W.YEARS:
        t0 = time.time(); s0, s1 = W.TS(Y), W.TS(Y + 1)
        models, ntr = Q.train_window(data, s0, None)
        P = K.predict(models, data, s0 - Q.WARM, s1)
        PP = J.apply_thr(data, P, J.thr_series(data, P), s0)
        msg = []
        for v, kw in VARIANTS.items():
            tr = run_policy_v(data, PP, **kw).assign(fold=Y)
            TR[v].append(tr); DY[v].append(K.daily(tr, s0, s1, 1.0))
            msg.append(f"{v} n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f}")
        print(f"{Y}: " + " | ".join(msg) + f" | {time.time()-t0:.0f}s", flush=True)
    res = dict(qid="Q530", run_at=time.strftime("%Y-%m-%d %H:%M"), note="R 単位・H1 判定（同じ足で両方は損切り）・WF 9 年は 7 回目の利用＝参考")
    for v in VARIANTS:
        tr = pd.concat(TR[v]); p = pd.concat(DY[v])
        tr.to_csv(os.path.join(a.out, f"trades_q530_{v}.csv"), index=False)
        yrs = {int(Y): float(g["R"].sum()) for Y, g in tr.groupby("fold")}
        dd = K.maxdd(p.to_numpy()); ann = p.sum() / 9
        res[v] = dict(n=int(len(tr)), mean_R=float(tr["R"].mean()), win=float((tr["R"] > 0).mean()), t=K.tstat(p),
                      total_R=float(p.sum()), annual_R=float(ann), max_dd_R=float(dd), annual_R_per_dd=float(ann / -dd) if dd < 0 else None,
                      worst_day_R=float(p.min()), sd_daily_R=float(p.std()), pos_years=sum(1 for x in yrs.values() if x > 0), years_R=yrs,
                      conc=concurrency(tr), groups=Q.group_stats(tr))
        print(v, json.dumps({k: res[v][k] for k in ["n", "mean_R", "t", "annual_R", "max_dd_R", "annual_R_per_dd", "worst_day_R", "pos_years", "conc"]}, ensure_ascii=False), flush=True)
    json.dump(res, open(os.path.join(a.out, "result_q530.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
