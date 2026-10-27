# -*- coding: utf-8 -*-
"""Q515 / S21: H1・15銘柄・ML が「入るか・方向・RR(1.0/1.5/2.0)」を選ぶ。週10回/銘柄・1銘柄1ポジション。
事前登録: 事前登録_q515.md（変更しない）。
使い方: python3 kensho_s21_h1_ml_rr_q515.py --data DIR --out DIR [--open-final]
  --open-final は仮判断に合格したときだけ付ける（付けなくても合格なら自動で開ける設定は持たない＝人が見て付ける）
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
import lightgbm as lgb

SYMS = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP",
        "XAUUSD", "US500", "USTECH", "GER40", "JPN225"]
CLASS = {s: 0 for s in SYMS[:10]}; CLASS["XAUUSD"] = 1
for s in ["US500", "USTECH", "GER40", "JPN225"]: CLASS[s] = 2
HOLD_RATE = {0: 0.01, 1: 0.04, 2: 0.04}  # 年率・名目比
K_ATR, H = 1.5, 120
RRS = [1.0, 1.5, 2.0]
ACTIONS = [(d, rr) for d in (1, -1) for rr in RRS]  # 6
WEEK_CAP = 10
TRAIN_END = pd.Timestamp("2023-10-01", tz="UTC")
INNER_START = pd.Timestamp("2021-10-01", tz="UTC")
VAL_START, VAL_END = TRAIN_END, pd.Timestamp("2025-10-01", tz="UTC")
VAL_MID = pd.Timestamp("2024-10-01", tz="UTC")
TEST_START, TEST_END = VAL_END, pd.Timestamp("2026-10-01", tz="UTC")
THETAS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
SIGMA_TARGET, R_CAP = 0.0025, 0.008
LGB_PARAMS = dict(objective="regression", num_leaves=31, learning_rate=0.03, n_estimators=400,
                  min_child_samples=500, subsample=0.7, subsample_freq=1, colsample_bytree=0.7, verbose=-1, n_jobs=2)
SEED = 20261025


def load(data_dir, sym):
    d = pd.read_parquet(os.path.join(data_dir, f"{sym}.parquet"))
    d = d[d["high"] != d["low"]].reset_index(drop=True)
    sp = (d["ask_close"] - d["close"]).where(d["ask_close"].notna())
    med = sp.rolling(500, min_periods=20).median().bfill().ffill()
    for c in ["open", "high", "low", "close"]:
        a = d[f"ask_{c}"]
        d[f"ask_{c}"] = a.where(a.notna(), d[c] + med)
    d["spr"] = (d["ask_close"] - d["close"]).clip(lower=0)
    return d


def labels(d, sym):
    """R[i, a]: 足 i の終値で決めて i+1 始値で入ったときの R（コスト込み）。X[i, a]: 決済足の index。"""
    n = len(d)
    bo, bh, bl, bc = (d[c].to_numpy(float) for c in ["open", "high", "low", "close"])
    ao, ah, al, ac = (d[f"ask_{c}"].to_numpy(float) for c in ["open", "high", "low", "close"])
    tr = np.maximum(bh - bl, np.maximum(np.abs(bh - np.r_[bc[0], bc[:-1]]), np.abs(bl - np.r_[bc[0], bc[:-1]])))
    atr = pd.Series(tr).rolling(24, min_periods=24).mean().to_numpy()
    D = K_ATR * atr
    R = np.full((n, len(ACTIONS)), np.nan); X = np.full((n, len(ACTIONS)), -1, int)
    valid = np.isfinite(D) & (np.arange(n) + H < n)
    idx = np.where(valid)[0]
    e = idx + 1
    hours = (d["time"].to_numpy()[np.minimum(e + H - 1, n - 1)] - d["time"].to_numpy()[e]) / np.timedelta64(1, "h")
    for a, (dr, rr) in enumerate(ACTIONS):
        Dv = D[idx]
        P = ao[e] if dr == 1 else bo[e]
        SL = P - dr * Dv; TP = P + dr * rr * Dv
        exitp = np.full(len(idx), np.nan); exitj = np.full(len(idx), -1)
        open_ = np.ones(len(idx), bool)
        for k in range(H):
            j = e + k
            if dr == 1:
                o, lo, hi = bo[j], bl[j], bh[j]
                gap = open_ & (o <= SL); sl = open_ & ~gap & (lo <= SL); tp = open_ & ~gap & ~sl & (hi >= TP)
            else:
                o, lo, hi = ao[j], al[j], ah[j]
                gap = open_ & (o >= SL); sl = open_ & ~gap & (hi >= SL); tp = open_ & ~gap & ~sl & (lo <= TP)
            exitp[gap] = o[gap]; exitp[sl] = SL[sl]; exitp[tp] = TP[tp]
            hit = gap | sl | tp
            exitj[hit] = j[hit]; open_ &= ~hit
            if not open_.any():
                break
        jt = e + H - 1
        last = bc[jt] if dr == 1 else ac[jt]
        exitp[open_] = last[open_]; exitj[open_] = jt[open_]
        held_h = (d["time"].to_numpy()[exitj] - d["time"].to_numpy()[e]) / np.timedelta64(1, "h")
        hold_R = HOLD_RATE[CLASS[sym]] / 8760 * held_h * P / Dv
        R[idx, a] = dr * (exitp - P) / Dv - hold_R
        X[idx, a] = exitj
    return R, X, D


def features(d, D, sym):
    c, h, l = d["close"], d["high"], d["low"]
    atr24 = D / K_ATR
    f = {}
    for k in [1, 3, 6, 12, 24, 72, 120, 240, 480]:
        f[f"ret{k}"] = (c - c.shift(k)) / atr24
    for k in [24, 120, 480]:
        f[f"sma{k}"] = (c - c.rolling(k).mean()) / atr24
        hi, lo = h.rolling(k).max(), l.rolling(k).min()
        f[f"pos{k}"] = (c - lo) / (hi - lo)
    tr = pd.Series(atr24)
    f["atr_ratio"] = tr / pd.Series(atr24).rolling(240).mean()
    dlt = c.diff(); up = dlt.clip(lower=0).rolling(14).mean(); dn = (-dlt.clip(upper=0)).rolling(14).mean()
    f["rsi14"] = up / (up + dn)
    f["vol_ratio"] = d["volume"] / d["volume"].rolling(240).mean()
    f["spr_R"] = d["spr"] / D
    f["hour"] = d["time"].dt.hour; f["dow"] = d["time"].dt.dayofweek
    f["cls"] = CLASS[sym]
    return pd.DataFrame(f).replace([np.inf, -np.inf], np.nan)


def build(data_dir):
    out = {}
    for s in SYMS:
        t0 = time.time()
        d = load(data_dir, s)
        R, X, D = labels(d, s)
        F = features(d, D, s)
        out[s] = dict(time=d["time"].reset_index(drop=True), R=R, X=X, F=F)
        print(f"  {s}: {len(d)} 本, {time.time()-t0:.1f}s", flush=True)
    return out


def train_models(data, end, step=3):
    """end より前に決済まで終わる行だけで学習（embargo＝ラベル地平）。"""
    Xs, Ys = [], []
    for s, o in data.items():
        t = o["time"]; n = len(t)
        ok = np.isfinite(o["R"]).all(1)
        # 決済足の時刻 < end
        xmax = o["X"].max(1)
        tx = t.dt.tz_convert(None).to_numpy()[np.clip(xmax, 0, n - 1)]
        ok &= (xmax >= 0) & (tx < end.tz_convert(None).to_datetime64())
        sel = np.where(ok)[0][::step]
        Xs.append(o["F"].iloc[sel]); Ys.append(o["R"][sel])
    Xtr = pd.concat(Xs); Ytr = np.vstack(Ys)
    models = []
    for a in range(len(ACTIONS)):
        m = lgb.LGBMRegressor(random_state=SEED + a, **LGB_PARAMS)
        m.fit(Xtr, np.clip(Ytr[:, a], -3, 3))
        models.append(m)
    return models, len(Xtr)


def predict(models, data, start, end):
    P = {}
    for s, o in data.items():
        t = o["time"]
        m = ((t >= start) & (t < end)).to_numpy() & np.isfinite(o["R"]).all(1)
        idx = np.where(m)[0]
        pr = np.column_stack([mod.predict(o["F"].iloc[idx]) for mod in models]) if len(idx) else np.zeros((0, 6))
        P[s] = (idx, pr)
    return P


def run_policy(data, P, theta):
    """返り値: トレード表（sym, i, entry_time, exit_time, a, R）。"""
    rows = []
    for s, (idx, pr) in P.items():
        o = data[s]; t = o["time"]
        week = (t.dt.tz_convert(None).dt.to_period("W-SUN")).to_numpy()
        busy_until = -1; wk = None; cnt = 0
        best = pr.argmax(1) if len(pr) else np.array([], int); bv = pr.max(1) if len(pr) else np.array([])
        for k, i in enumerate(idx):
            if week[i] != wk:
                wk = week[i]; cnt = 0
            if i < busy_until or cnt >= WEEK_CAP or bv[k] <= theta:
                continue
            a = best[k]
            x = o["X"][i, a]
            rows.append((s, i, t.iloc[i + 1], t.iloc[x], int(a), o["R"][i, a], bv[k], str(wk)))
            busy_until = x; cnt += 1
    return pd.DataFrame(rows, columns=["sym", "i", "entry", "exit", "a", "R", "pred", "week"])


def daily(tr, start, end, r):
    days = pd.bdate_range(start.tz_convert(None).normalize(), (end - pd.Timedelta(days=1)).tz_convert(None).normalize())
    if len(tr) == 0:
        return pd.Series(0.0, index=days)
    d = tr["exit"].dt.tz_convert(None).dt.normalize(); wd = d.dt.weekday
    # 2026-10-25 修正: 土日（日曜の寄り付き）の決済を翌月曜に計上する。以前は平日の表に合わせて落としていた（recompute_daily_fix.py）
    d = d + pd.to_timedelta(np.where(wd == 5, 2, np.where(wd == 6, 1, 0)), unit="D")
    p = tr.assign(day=d).groupby("day")["R"].sum() * r
    return p.reindex(days, fill_value=0.0)


def tstat(x):
    x = np.asarray(x, float); return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std() > 0 else 0.0


def maxdd(p):
    eq = np.cumsum(p); return float((eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min()) if len(p) else 0.0


def null_z(data, tr, B=500, seed=SEED):
    """同じ銘柄・同じ週のエントリー回数を保ち、時刻（その週の足から）・方向・RR をランダムに。"""
    rng = np.random.default_rng(seed)
    obs = tr["R"].mean()
    groups = []
    for (s, wk), g in tr.groupby(["sym", "week"]):
        o = data[s]; t = o["time"]
        wkarr = getattr(data[s], "_wk", None)
        if "_wk" not in o:
            o["_wk"] = (t.dt.tz_convert(None).dt.to_period("W-SUN")).astype(str).to_numpy()
        cand = np.where((o["_wk"] == wk) & np.isfinite(o["R"]).all(1))[0]
        groups.append((s, cand, len(g)))
    null = np.empty(B)
    for b in range(B):
        tot, n = 0.0, 0
        for s, cand, k in groups:
            ii = rng.choice(cand, size=min(k, len(cand)), replace=False)
            aa = rng.integers(0, 6, size=len(ii))
            tot += data[s]["R"][ii, aa].sum(); n += len(ii)
        null[b] = tot / n
    return float((obs - null.mean()) / null.std(ddof=1)), float(null.mean()), float(null.std(ddof=1))


def summarize(tr, start, end, r):
    p = daily(tr, start, end, r)
    return dict(n_trades=int(len(tr)), mean_R=float(tr["R"].mean()) if len(tr) else None,
                win=float((tr["R"] > 0).mean()) if len(tr) else None,
                t_daily=tstat(p), mean_daily_pct=float(p.mean() * 100), sigma_daily_pct=float(p.std() * 100),
                max_dd_pct=float(maxdd(p.to_numpy()) * 100), total_pct=float(p.sum() * 100))


def describe(tr):
    out = {}
    if len(tr) == 0:
        return out
    t = tr.assign(act=tr["a"].map(lambda a: f"{'買' if ACTIONS[a][0]==1 else '売'}RR{ACTIONS[a][1]}"))
    out["by_action"] = t.groupby("act")["R"].agg(["count", "mean"]).round(4).reset_index().to_dict("records")
    out["by_sym"] = t.groupby("sym")["R"].agg(["count", "mean"]).round(4).reset_index().to_dict("records")
    t["dec"] = pd.qcut(t["pred"].rank(method="first"), 5, labels=False)
    out["by_pred_quintile"] = t.groupby("dec")["R"].agg(["count", "mean"]).round(4).reset_index().to_dict("records")
    return out


def simple_baselines(data, start, end):
    res = {}
    for a, (dr, rr) in enumerate(ACTIONS):
        Rs = []
        for s, o in data.items():
            t = o["time"]; m = ((t >= start) & (t < end)).to_numpy() & np.isfinite(o["R"][:, a])
            Rs.append(o["R"][m, a])
        res[f"{'買' if dr==1 else '売'}RR{rr}_全足"] = float(np.concatenate(Rs).mean())
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--open-final", action="store_true"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = dict(qid="Q515", strategy="S21", run_at=time.strftime("%Y-%m-%d %H:%M"))
    print("ラベル・特徴量", flush=True); data = build(a.data)

    # 1) 内側検証で θ と r を決める
    print("内側: 学習 〜2021-09 → 評価 2021-10〜2023-09", flush=True)
    m_in, ntr = train_models(data, INNER_START)
    P_in = predict(m_in, data, INNER_START, TRAIN_END)
    inner = []
    for th in THETAS:
        tr = run_policy(data, P_in, th)
        p = daily(tr, INNER_START, TRAIN_END, 1.0)
        inner.append(dict(theta=th, n=len(tr), mean_R=float(tr["R"].mean()) if len(tr) else None, t=tstat(p), sigma_R_daily=float(p.std())))
    cand = [x for x in inner if x["n"] >= 200] or inner
    pick = max(cand, key=lambda x: x["t"])
    theta = pick["theta"]; r = min(R_CAP, SIGMA_TARGET / pick["sigma_R_daily"]) if pick["sigma_R_daily"] > 0 else R_CAP
    res["inner"] = dict(n_train_rows=ntr, grid=inner, theta=theta, r=r)
    print(json.dumps(res["inner"], ensure_ascii=False, indent=1), flush=True)

    # 2) 学習全体で再学習 → 仮判断
    print("本学習: 〜2023-09 → 仮判断 2023-10〜2025-09", flush=True)
    models, ntr = train_models(data, TRAIN_END)
    P_val = predict(models, data, VAL_START, VAL_END)
    tr = run_policy(data, P_val, theta)
    tr.to_csv(os.path.join(a.out, "trades_val.csv"), index=False)
    s_all = summarize(tr, VAL_START, VAL_END, r)
    y1 = summarize(tr[tr["entry"] < VAL_MID], VAL_START, VAL_MID, r)
    y2 = summarize(tr[tr["entry"] >= VAL_MID], VAL_MID, VAL_END, r)
    z, nm, ns = null_z(data, tr)
    gate = dict(t_ge_2=s_all["t_daily"] >= 2, both_years_pos=(y1["mean_daily_pct"] > 0 and y2["mean_daily_pct"] > 0),
                dd_ok=s_all["max_dd_pct"] >= -6.0, null_z_ge_2=z >= 2)
    passed = all(gate.values())
    res["val"] = dict(n_train_rows=ntr, all=s_all, year1=y1, year2=y2, null=dict(z=z, mean=nm, sd=ns), gate=gate, passed=passed,
                      detail=describe(tr), baselines=simple_baselines(data, VAL_START, VAL_END))
    print(json.dumps({k: res["val"][k] for k in ["all", "year1", "year2", "null", "gate", "passed"]}, ensure_ascii=False, indent=1), flush=True)

    # 3) 最終判断（合格時かつ --open-final のときだけ）
    if passed and a.open_final:
        P_te = predict(models, data, TEST_START, TEST_END)
        tt = run_policy(data, P_te, theta); tt.to_csv(os.path.join(a.out, "trades_test.csv"), index=False)
        st = summarize(tt, TEST_START, TEST_END, r)
        res["test"] = dict(all=st, passed=(st["t_daily"] >= 2 and st["mean_daily_pct"] > 0 and st["max_dd_pct"] >= -6.0), detail=describe(tt))
    else:
        res["test"] = "未開封（仮判断不合格、または --open-final なし）"
    with open(os.path.join(a.out, "result_q515.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print("done", flush=True)


if __name__ == "__main__":
    main()
