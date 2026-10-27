# -*- coding: utf-8 -*-
"""Q516 / S21b: 日足 ZigZag++（Depth 12・確定日のみ）の向きにだけ H1 で入る。週の回数上限なし。
事前登録: 事前登録_q516.md。Q515 のコード（kensho_s21_h1_ml_rr_q515.py）を部品として使う。
使い方: python3 kensho_s21b_d1zigzag_h1_q516.py --data DIR --out DIR [--open-final]"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K

K.WEEK_CAP = 10 ** 9  # 上限なし
DEPTH = 12
CUT_H = 22  # 日の区切り（UTC）


def daily_zigzag(d):
    t = d["time"]
    day = (t + pd.Timedelta(hours=24 - CUT_H)).dt.floor("D")
    g = d.assign(day=day).groupby("day")
    D1 = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                       "nbars": g.size(), "end": g["time"].max() + pd.Timedelta(hours=1)})
    D1 = D1[D1["nbars"] >= 4].reset_index(drop=True)
    h, l, c = D1["high"].to_numpy(), D1["low"].to_numpy(), D1["close"].to_numpy()
    pc = np.r_[c[0], c[:-1]]
    atr = pd.Series(np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))).rolling(14).mean().to_numpy()
    hh = pd.Series(h).rolling(DEPTH).max().to_numpy(); ll = pd.Series(l).rolling(DEPTH).min().to_numpy()
    n = len(D1); dirn = np.zeros(n); since = np.zeros(n); leg = np.full(n, np.nan); struct = np.zeros(n)
    pivH = [np.nan, np.nan]; pivL = [np.nan, np.nan]; cur, ext, start, start_px = 0, np.nan, 0, np.nan
    for i in range(n):
        up = np.isfinite(hh[i]) and h[i] >= hh[i]; dn = np.isfinite(ll[i]) and l[i] <= ll[i]
        if up and not dn and cur != 1:
            if cur == -1: pivL = [pivL[1], ext]
            start_px = ext if cur == -1 else ll[i]
            cur, ext, start = 1, h[i], i
        elif dn and not up and cur != -1:
            if cur == 1: pivH = [pivH[1], ext]
            start_px = ext if cur == 1 else hh[i]
            cur, ext, start = -1, l[i], i
        elif cur == 1: ext = max(ext, h[i])
        elif cur == -1: ext = min(ext, l[i])
        dirn[i] = cur; since[i] = i - start
        if cur != 0 and np.isfinite(atr[i]): leg[i] = (c[i] - start_px) / atr[i]
        if np.isfinite(pivH).all() and np.isfinite(pivL).all():
            struct[i] = (1 if pivH[1] > pivH[0] else -1) + (1 if pivL[1] > pivL[0] else -1)
    return pd.DataFrame({"end": D1["end"], "d1_zz_dir": dirn, "d1_zz_since": since, "d1_zz_leg_atr": leg, "d1_zz_struct": struct})


def attach(d, F):
    Z = daily_zigzag(d)
    dec = pd.DataFrame({"dec": d["time"] + pd.Timedelta(hours=1), "k": np.arange(len(d))})
    m = pd.merge_asof(dec.sort_values("dec"), Z.sort_values("end"), left_on="dec", right_on="end", direction="backward")
    m = m.sort_values("k").reset_index(drop=True)
    cols = ["d1_zz_dir", "d1_zz_since", "d1_zz_leg_atr", "d1_zz_struct"]
    F2 = pd.concat([F.reset_index(drop=True), m[cols]], axis=1)
    return F2, m["d1_zz_dir"].fillna(0).to_numpy()


def build(data_dir):
    out = {}
    for s in K.SYMS:
        d = K.load(data_dir, s); R, X, D = K.labels(d, s); F = K.features(d, D, s)
        F2, zdir = attach(d, F)
        out[s] = dict(time=d["time"].reset_index(drop=True), R=R, X=X, F=F2, zdir=zdir)
        print(f"  {s}", flush=True)
    return out


def mask(data, P):
    """日足 ZigZag の向きと逆の行動・向き未定の足は選べなくする。"""
    out = {}
    dirs = np.array([a[0] for a in K.ACTIONS])
    for s, (idx, pr) in P.items():
        z = data[s]["zdir"][idx]
        ok = dirs[None, :] == z[:, None]
        out[s] = (idx, np.where(ok, pr, -9.0))
    return out


def null_keep_dir(data, tr, B=500, seed=K.SEED):
    rng = np.random.default_rng(seed); groups = []
    for (s, wk), g in tr.groupby(["sym", "week"]):
        o = data[s]
        if "_wk" not in o:
            o["_wk"] = o["time"].dt.tz_convert(None).dt.to_period("W-SUN").astype(str).to_numpy()
        cand = np.where((o["_wk"] == wk) & np.isfinite(o["R"]).all(1) & (o["zdir"] != 0))[0]
        groups.append((s, cand, len(g)))
    null = np.empty(B)
    for b in range(B):
        tot = n = 0
        for s, cand, k in groups:
            ii = rng.choice(cand, size=min(k, len(cand)), replace=False)
            z = data[s]["zdir"][ii]; rr = rng.integers(0, 3, size=len(ii))
            aa = np.where(z == 1, rr, 3 + rr)
            tot += data[s]["R"][ii, aa].sum(); n += len(ii)
        null[b] = tot / n
    obs = tr["R"].mean()
    return dict(z=float((obs - null.mean()) / null.std(ddof=1)), mean=float(null.mean()), sd=float(null.std(ddof=1)))


def follow_baseline(data, start, end):
    Rs = []
    for s, o in data.items():
        t = o["time"]; m = ((t >= start) & (t < end)).to_numpy() & np.isfinite(o["R"]).all(1) & (o["zdir"] != 0)
        z = o["zdir"][m]; Rs.append(np.where(z == 1, o["R"][m, 1], o["R"][m, 4]))
    return float(np.concatenate(Rs).mean())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--open-final", action="store_true"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    res = dict(qid="Q516", strategy="S21b", run_at=time.strftime("%Y-%m-%d %H:%M"))
    print("ラベル・特徴量", flush=True); data = build(a.data)

    print("内側", flush=True)
    m_in, ntr = K.train_models(data, K.INNER_START)
    P_in = mask(data, K.predict(m_in, data, K.INNER_START, K.TRAIN_END))
    inner = []
    for th in K.THETAS:
        tr = K.run_policy(data, P_in, th); p = K.daily(tr, K.INNER_START, K.TRAIN_END, 1.0)
        inner.append(dict(theta=th, n=len(tr), mean_R=float(tr["R"].mean()) if len(tr) else None, t=K.tstat(p), sigma_R_daily=float(p.std())))
    cand = [x for x in inner if x["n"] >= 200] or inner
    pick = max(cand, key=lambda x: x["t"]); theta = pick["theta"]
    r = min(K.R_CAP, K.SIGMA_TARGET / pick["sigma_R_daily"]) if pick["sigma_R_daily"] > 0 else K.R_CAP
    res["inner"] = dict(n_train_rows=ntr, grid=inner, theta=theta, r=r)
    print(json.dumps(res["inner"], ensure_ascii=False), flush=True)

    print("本学習 → 仮判断", flush=True)
    models, ntr = K.train_models(data, K.TRAIN_END)
    P_val = mask(data, K.predict(models, data, K.VAL_START, K.VAL_END))
    tr = K.run_policy(data, P_val, theta); tr.to_csv(os.path.join(a.out, "trades_val_q516.csv"), index=False)
    s_all = K.summarize(tr, K.VAL_START, K.VAL_END, r)
    y1 = K.summarize(tr[tr["entry"] < K.VAL_MID], K.VAL_START, K.VAL_MID, r)
    y2 = K.summarize(tr[tr["entry"] >= K.VAL_MID], K.VAL_MID, K.VAL_END, r)
    z, nm, ns = K.null_z(data, tr)
    gate = dict(t_ge_2=s_all["t_daily"] >= 2, both_years_pos=(y1["mean_daily_pct"] > 0 and y2["mean_daily_pct"] > 0),
                dd_ok=s_all["max_dd_pct"] >= -6.0, null_z_ge_2=z >= 2)
    passed = all(gate.values())
    res["val"] = dict(n_train_rows=ntr, all=s_all, year1=y1, year2=y2, null=dict(z=z, mean=nm, sd=ns), gate=gate, passed=passed,
                      side_null_keep_d1dir=null_keep_dir(data, tr), detail=K.describe(tr),
                      side_follow_d1zz_rr15_allbars=follow_baseline(data, K.VAL_START, K.VAL_END))
    print(json.dumps({k: res["val"][k] for k in ["all", "year1", "year2", "null", "side_null_keep_d1dir", "side_follow_d1zz_rr15_allbars", "gate", "passed"]}, ensure_ascii=False, indent=1), flush=True)

    if passed and a.open_final:
        P_te = mask(data, K.predict(models, data, K.TEST_START, K.TEST_END))
        tt = K.run_policy(data, P_te, theta); tt.to_csv(os.path.join(a.out, "trades_test_q516.csv"), index=False)
        st = K.summarize(tt, K.TEST_START, K.TEST_END, r)
        res["test"] = dict(all=st, passed=(st["t_daily"] >= 2 and st["mean_daily_pct"] > 0 and st["max_dd_pct"] >= -6.0), detail=K.describe(tt))
    else:
        res["test"] = "未開封（仮判断不合格、または --open-final なし）"
    json.dump(res, open(os.path.join(a.out, "result_q516.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
