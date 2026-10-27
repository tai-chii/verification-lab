# -*- coding: utf-8 -*-
"""Q518: S21（Q515 の方策）を学習期間内でウォークフォワード。事前登録_q518.md。
使い方: python3 kensho_s21_walkforward_q518.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K

YEARS = list(range(2014, 2023))  # 評価年 = Y-10-01〜(Y+1)-10-01
IDX = ["US500", "USTECH", "GER40", "JPN225"]
TS = lambda y: pd.Timestamp(f"{y}-10-01", tz="UTC")


def pick_theta(data, models, start, end):
    P = K.predict(models, data, start, end); grid = []
    for th in K.THETAS:
        tr = K.run_policy(data, P, th); p = K.daily(tr, start, end, 1.0)
        grid.append(dict(theta=th, n=len(tr), t=K.tstat(p), sd=float(p.std())))
    cand = [x for x in grid if x["n"] >= 200] or grid
    b = max(cand, key=lambda x: x["t"])
    return b["theta"], (min(K.R_CAP, K.SIGMA_TARGET / b["sd"]) if b["sd"] > 0 else K.R_CAP), grid


def rolling_q_policy(data, P, window_days=20, q=0.90):
    """V4: 閾値＝直近 20 営業日（判断時刻より前）の全銘柄プールの予測最大値の 90 パーセンタイル。"""
    rows = []
    for s, (idx, pr) in P.items():
        t = data[s]["time"].iloc[idx].dt.tz_convert(None).to_numpy(); rows.append(pd.DataFrame({"t": t, "v": pr.max(1)}))
    allv = pd.concat(rows).sort_values("t").set_index("t")["v"]
    thr = allv.rolling(f"{int(window_days*1.4)}D", closed="left").quantile(q)
    thr = thr.groupby(level=0).first()
    out = {}
    for s, (idx, pr) in P.items():
        t = data[s]["time"].iloc[idx].dt.tz_convert(None)
        th = thr.reindex(t.to_numpy()).to_numpy()
        th = np.where(np.isfinite(th), th, np.inf)
        out[s] = (idx, pr - th[:, None])
    return out


def index_ret_daily(data_dir, start, end):
    rs = []
    for s in IDX:
        d = K.load(data_dir, s)
        d = d[(d["time"] >= start) & (d["time"] < end)]
        c = d.set_index(d["time"].dt.tz_convert(None))["close"].resample("D").last().dropna()
        rs.append(c.pct_change().rename(s))
    return pd.concat(rs, axis=1).mean(axis=1, skipna=True)


def nw_alpha_t(y, x, lag=5):
    X = np.column_stack([np.ones(len(x)), x]); b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X @ b
    n = len(y); XtX_inv = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, lag + 1):
        w = 1 - l / (lag + 1); G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None]); S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return float(b[0] / np.sqrt(V[0, 0])), float(b[1])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("ラベル・特徴量", flush=True); data = K.build(a.data)
    res = dict(qid="Q518", run_at=time.strftime("%Y-%m-%d %H:%M"), folds=[])
    daily_all, daily_v2, daily_v4, trades_all = [], [], [], []
    for Y in YEARS:
        t0 = time.time(); s0, s1, si = TS(Y), TS(Y + 1), TS(Y - 1)
        m_in, _ = K.train_models(data, si)
        theta, r, grid = pick_theta(data, m_in, si, s0)
        models, ntr = K.train_models(data, s0)
        P = K.predict(models, data, s0, s1)
        tr = K.run_policy(data, P, theta).assign(fold=Y, r=r)
        p1 = K.daily(tr, s0, s1, r)
        trv2 = tr[~tr["sym"].isin(IDX)]
        Pv2 = {s: v for s, v in P.items() if s not in IDX}
        tr2 = K.run_policy(data, Pv2, theta); p2 = K.daily(tr2, s0, s1, r)
        tr4 = K.run_policy(data, rolling_q_policy(data, P), 0.0); p4 = K.daily(tr4, s0, s1, r)
        dirn = tr["a"].map(lambda x: "買" if K.ACTIONS[x][0] == 1 else "売")
        f = dict(year=f"{Y}-10〜{Y+1}-09", n_train=ntr, theta=theta, r=r, inner_grid=grid,
                 V1=K.summarize(tr, s0, s1, r), V2_exidx=K.summarize(tr2, s0, s1, r), V4_rollq=K.summarize(tr4, s0, s1, r),
                 V3_dir=tr.assign(d=dirn).groupby("d")["R"].agg(["count", "mean"]).round(4).to_dict("index"),
                 idx_share=float(tr["sym"].isin(IDX).mean()) if len(tr) else None, sec=round(time.time() - t0))
        res["folds"].append(f); daily_all.append(p1); daily_v2.append(p2); daily_v4.append(p4); trades_all.append(tr)
        print(f"{f['year']}: θ={theta} r={r:.5f} | V1 n={f['V1']['n_trades']} R={f['V1']['mean_R']} t={f['V1']['t_daily']:.2f} | "
              f"V2 t={f['V2_exidx']['t_daily']:.2f} | V4 t={f['V4_rollq']['t_daily']:.2f} | {f['sec']}s", flush=True)
    P1, P2, P4 = pd.concat(daily_all), pd.concat(daily_v2), pd.concat(daily_v4)
    TR = pd.concat(trades_all); TR.to_csv(os.path.join(a.out, "trades_wf_q518.csv"), index=False)
    ir = index_ret_daily(a.data, TS(YEARS[0]), TS(YEARS[-1] + 1))
    j = pd.concat([P1.rename("p"), ir.rename("m")], axis=1).dropna()
    at, beta = nw_alpha_t(j["p"].to_numpy(), j["m"].to_numpy())
    pos_years = sum(1 for f in res["folds"] if f["V1"]["mean_daily_pct"] > 0)
    z, nm, ns = K.null_z(data, TR, B=200)
    crit = dict(t_ge_2=K.tstat(P1) >= 2, pos_years_ge_6=pos_years >= 6, alpha_t_ge_2=at >= 2)
    nsat = sum(crit.values())
    verdict = "支持" if nsat == 3 else ("棄却" if nsat <= 1 else "未確定")
    res["pooled"] = dict(
        V1=dict(t=K.tstat(P1), mean_daily_pct=float(P1.mean() * 100), max_dd_pct=float(K.maxdd(P1.to_numpy()) * 100),
                n=int(len(TR)), mean_R=float(TR["R"].mean()), pos_years=pos_years, alpha_t_nw=at, beta_to_idx=beta,
                null=dict(z=z, mean=nm, sd=ns)),
        V2_exidx=dict(t=K.tstat(P2), mean_daily_pct=float(P2.mean() * 100), max_dd_pct=float(K.maxdd(P2.to_numpy()) * 100)),
        V4_rollq=dict(t=K.tstat(P4), mean_daily_pct=float(P4.mean() * 100), max_dd_pct=float(K.maxdd(P4.to_numpy()) * 100)),
        criteria=crit, verdict=verdict)
    json.dump(res, open(os.path.join(a.out, "result_q518.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(res["pooled"], ensure_ascii=False, indent=1), flush=True); print("done", flush=True)


if __name__ == "__main__":
    main()
