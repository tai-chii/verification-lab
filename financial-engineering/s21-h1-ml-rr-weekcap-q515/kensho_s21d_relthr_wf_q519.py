# -*- coding: utf-8 -*-
"""Q519: 相対閾値（直近 28 暦日の全銘柄プール予測最大値の 90 パーセンタイル）＋ r 再設定、学習窓 2 通りのウォークフォワード。
事前登録_q519.md。使い方: python3 kensho_s21d_relthr_wf_q519.py --data DIR --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W

YEARS = W.YEARS; IDX = W.IDX; TS = W.TS
WARM = pd.Timedelta(days=30)
YEN = ["USDJPY", "EURJPY", "GBPJPY"]


def train_window(data, end, start=None, step=3):
    Xs, Ys = [], []
    for s, o in data.items():
        t = o["time"]; n = len(t); tn = t.dt.tz_convert(None).to_numpy()
        ok = np.isfinite(o["R"]).all(1)
        xmax = o["X"].max(1)
        ok &= (xmax >= 0) & (tn[np.clip(xmax, 0, n - 1)] < end.tz_convert(None).to_datetime64())
        if start is not None:
            ok &= tn >= start.tz_convert(None).to_datetime64()
        sel = np.where(ok)[0][::step]
        Xs.append(o["F"].iloc[sel]); Ys.append(o["R"][sel])
    Xtr = pd.concat(Xs); Ytr = np.vstack(Ys); models = []
    for a in range(len(K.ACTIONS)):
        m = lgb.LGBMRegressor(random_state=K.SEED + a, **K.LGB_PARAMS); m.fit(Xtr, np.clip(Ytr[:, a], -3, 3)); models.append(m)
    return models, len(Xtr)


def rel_policy_trades(data, models, s0, s1):
    """s0−30 日から予測して閾値を作り、s0〜s1 だけで売買。"""
    P = K.predict(models, data, s0 - WARM, s1)
    PP = W.rolling_q_policy(data, P)  # pr − 閾値（直前 28 暦日・closed=left）
    out = {}
    for s, (idx, pr) in PP.items():
        keep = (data[s]["time"].iloc[idx] >= s0).to_numpy()
        out[s] = (idx[keep], pr[keep])
    return K.run_policy(data, out, 0.0)


def group_stats(tr):
    g = tr["sym"].map(lambda s: "円絡み" if s in YEN else ("指数" if s in IDX else ("金" if s == "XAUUSD" else "円以外FX")))
    o = {}
    for k, x in tr.groupby(g)["R"]:
        o[k] = dict(n=int(len(x)), mean_R=round(float(x.mean()), 4), t=round(float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))), 2))
    return o


def run_window(data, a, label, years_back):
    folds, daily, trades = [], [], []
    for Y in YEARS:
        t0 = time.time(); s0, s1, si = TS(Y), TS(Y + 1), TS(Y - 1)
        st_in = None if years_back is None else si - pd.DateOffset(years=years_back)
        st = None if years_back is None else s0 - pd.DateOffset(years=years_back)
        m_in, _ = train_window(data, si, st_in)
        tri = rel_policy_trades(data, m_in, si, s0); pi = K.daily(tri, si, s0, 1.0)
        r = min(K.R_CAP, K.SIGMA_TARGET / pi.std()) if pi.std() > 0 else K.R_CAP
        models, ntr = train_window(data, s0, st)
        tr = rel_policy_trades(data, models, s0, s1).assign(fold=Y, r=r, window=label)
        p = K.daily(tr, s0, s1, r)
        f = dict(year=f"{Y}-10〜{Y+1}-09", n_train=ntr, r=r, inner=dict(n=len(tri), t=K.tstat(pi)),
                 V=K.summarize(tr, s0, s1, r), groups=group_stats(tr), sec=round(time.time() - t0))
        folds.append(f); daily.append(p); trades.append(tr)
        print(f"[{label}] {f['year']}: r={r:.5f} n={f['V']['n_trades']} R={f['V']['mean_R']:.4f} t={f['V']['t_daily']:.2f} "
              f"dd={f['V']['max_dd_pct']:.2f} | 内側 n={len(tri)} t={K.tstat(pi):.2f} | {f['sec']}s", flush=True)
    P = pd.concat(daily); TR = pd.concat(trades)
    TR.to_csv(os.path.join(a.out, f"trades_q519_{label}.csv"), index=False)
    ir = W.index_ret_daily(a.data, TS(YEARS[0]), TS(YEARS[-1] + 1))
    j = pd.concat([P.rename("p"), ir.rename("m")], axis=1).dropna()
    at, beta = W.nw_alpha_t(j["p"].to_numpy(), j["m"].to_numpy())
    pos = sum(1 for f in folds if f["V"]["mean_daily_pct"] > 0)
    z, nm, ns = K.null_z(data, TR, B=200)
    late = float(np.mean([f["V"]["mean_daily_pct"] for f in folds if int(f["year"][:4]) >= 2018]))
    crit = dict(t_ge_2=K.tstat(P) >= 2, pos_years_ge_6=pos >= 6, alpha_t_ge_2=at >= 2, dd_ok=K.maxdd(P.to_numpy()) * 100 >= -6.0)
    nsat = sum(crit.values())
    return dict(folds=folds, pooled=dict(t=K.tstat(P), mean_daily_pct=float(P.mean() * 100), max_dd_pct=float(K.maxdd(P.to_numpy()) * 100),
                total_pct=float(P.sum() * 100), n=int(len(TR)), mean_R=float(TR["R"].mean()), pos_years=pos, alpha_t_nw=at, beta=beta,
                null=dict(z=z, mean=nm, sd=ns), late_2018_22_mean_daily_pct=late, groups=group_stats(TR), criteria=crit,
                verdict=("支持" if nsat == 4 else ("未確定" if nsat == 3 else "棄却"))))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("ラベル・特徴量", flush=True); data = K.build(a.data)
    res = dict(qid="Q519", run_at=time.strftime("%Y-%m-%d %H:%M"))
    for label, yb in [("W-exp", None), ("W-5y", 5)]:
        res[label] = run_window(data, a, label, yb)
        print(label, json.dumps(res[label]["pooled"], ensure_ascii=False), flush=True)
        json.dump(res, open(os.path.join(a.out, "result_q519.json"), "w"), ensure_ascii=False, indent=1, default=str)
    res["verdict"] = res["W-exp"]["pooled"]["verdict"]
    json.dump(res, open(os.path.join(a.out, "result_q519.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("verdict", res["verdict"]); print("done", flush=True)


if __name__ == "__main__":
    main()
