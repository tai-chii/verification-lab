# -*- coding: utf-8 -*-
"""Q524: S21f（Q521 の設計・vol_ratio 抜き）を 15 銘柄で学習し、学習に使っていない円クロス 4 本で当たるかを見る。事前登録_q524.md。
使い方: python3 kensho_s21f_newjpy_q524.py --h1 DIR(15 銘柄 parquet) --m1zip DIR(銘柄ごとの HistData zip) --m1pq DIR(15 銘柄の <sym>_M1.parquet) --spread DIR(spread_<sym>.csv) --out DIR"""
import argparse, glob, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_mtf_wf_q521 as M
import kensho_s21_m1_resolve_q523 as R
import convert_histdata_m15 as CV

SYMS15 = list(K.SYMS)
NEW = ["AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"]
for s in NEW:
    K.CLASS[s] = 0
YEARS = list(range(2014, 2025))        # 2014-10〜2025-09 の 11 年


def m1_from_zips(zdir):
    zs = sorted(glob.glob(os.path.join(zdir, "*.zip")))
    m = pd.concat([CV.read_zip(z) for z in zs]).drop_duplicates("time").sort_values("time").reset_index(drop=True)
    m["time"] = m["time"].dt.tz_localize("UTC")
    return m


def h1_new(sym, m1, spread_dir):
    g = m1.set_index("time").resample("h")
    h = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "nmin": g["close"].count()}).dropna(subset=["open"])
    h = h[h["nmin"] >= 10].drop(columns="nmin").reset_index()
    sp = pd.read_csv(os.path.join(spread_dir, f"spread_{sym}.csv"), parse_dates=["time"])[["time", "spread"]]
    sp["time"] = sp["time"].dt.tz_localize("UTC") + pd.Timedelta(days=1)       # その日の値は翌日から使う（判断時点まで）
    sp["spr"] = sp["spread"].where(sp["spread"] > 0).rolling(20, min_periods=1).median()
    h = pd.merge_asof(h.sort_values("time"), sp[["time", "spr"]].dropna(), on="time", direction="backward")
    h["spr"] = h["spr"].bfill()
    for c in ["open", "high", "low", "close"]:
        h[f"ask_{c}"] = h[c] + h["spr"]
    h["volume"] = np.nan; h["spread"] = h["spr"]
    return h.drop(columns="spr")


def make(d, s):
    d = d[d["high"] != d["low"]].reset_index(drop=True)
    if "spr" not in d:
        d["spr"] = (d["ask_close"] - d["close"]).clip(lower=0)
    R_, X, D = K.labels(d, s)
    F = pd.concat([K.features(d, D, s).reset_index(drop=True), M.mtf_feats(d, D).reset_index(drop=True)], axis=1).drop(columns=["vol_ratio"])
    return dict(time=d["time"].reset_index(drop=True), R=R_, X=X, F=F, d=d, D=D)


def thr_series(data, P, window_days=20, q=0.90):
    rows = [pd.DataFrame({"t": data[s]["time"].iloc[idx].dt.tz_convert(None).to_numpy(), "v": pr.max(1)}) for s, (idx, pr) in P.items()]
    allv = pd.concat(rows).sort_values("t").set_index("t")["v"]
    return allv.rolling(f"{int(window_days*1.4)}D", closed="left").quantile(q).groupby(level=0).first()


def apply_thr(data, P, thr, s0):
    out = {}
    for s, (idx, pr) in P.items():
        t = data[s]["time"].iloc[idx].dt.tz_convert(None)
        th = thr.reindex(t.to_numpy(), method="ffill").to_numpy()
        th = np.where(np.isfinite(th), th, np.inf)
        keep = (data[s]["time"].iloc[idx] >= s0).to_numpy()
        out[s] = (idx[keep], (pr - th[:, None])[keep])
    return out


def resolve(tr, data, m1map):
    """Q523 と同じ方法で、決済足が SL・TP 両方に触れた取引を 1 分足で先着判定。"""
    tr = tr.copy(); tr["R_m1"] = tr["R"].astype(float); tr["amb"] = ""
    for k in range(len(tr)):
        row = tr.iloc[k]; s = row["sym"]; o = data[s]; d, D = o["d"], o["D"]; dr, rr = K.ACTIONS[int(row["a"])]; i = int(row["i"]); e = i + 1
        j = int(o["X"][i, int(row["a"])])
        bo, bh, bl = d["open"].to_numpy(), d["high"].to_numpy(), d["low"].to_numpy()
        ao, ah, al = d["ask_open"].to_numpy(), d["ask_high"].to_numpy(), d["ask_low"].to_numpy()
        P = ao[e] if dr == 1 else bo[e]; Dv = D[i]; SL = P - dr * Dv; TP = P + dr * rr * Dv
        if dr == 1:
            both = (bl[j] <= SL) and (bh[j] >= TP) and not (bo[j] <= SL); o_ref = bo[j]
        else:
            both = (ah[j] >= SL) and (al[j] <= TP) and not (ao[j] >= SL); o_ref = ao[j]
        if not both:
            continue
        m = m1map.get(s)
        res = None
        if m is not None:
            h0 = d["time"].iloc[j].tz_convert(None).to_datetime64(); mt = m[0]
            res = R.first_hit_m1(m[1].iloc[np.searchsorted(mt, h0):np.searchsorted(mt, h0 + np.timedelta64(1, "h"))], dr, SL - o_ref, TP - o_ref)
        tr.iat[k, tr.columns.get_loc("amb")] = res or "判定不能"
        if res == "TP":
            tr.iat[k, tr.columns.get_loc("R_m1")] = rr + (row["R"] + 1.0)
    return tr


def main():
    ap = argparse.ArgumentParser()
    for x in ["h1", "m1zip", "m1pq", "spread", "out"]:
        ap.add_argument(f"--{x}", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    print("15 銘柄", flush=True)
    data15 = {s: make(K.load(a.h1, s), s) for s in SYMS15}
    print("新しい 4 本", flush=True)
    data4, m1map = {}, {}
    for s in NEW:
        m1 = m1_from_zips(os.path.join(a.m1zip, s))
        h = h1_new(s, m1, a.spread)
        data4[s] = make(h, s)
        m1map[s] = (m1["time"].dt.tz_convert(None).to_numpy(), m1)
        print(f"  {s}: H1 {len(h):,} 本 {h.time.min()}〜{h.time.max()}  spr_R 中央 {np.nanmedian(h['spread']/data4[s]['D']):.3f}", flush=True)
    folds, tr4_all, tr15_all = [], [], []
    for Y in YEARS:
        t0 = time.time(); s0, s1, si = W.TS(Y), W.TS(Y + 1), W.TS(Y - 1)
        m_in, _ = Q.train_window(data15, si, None)
        P_in = K.predict(m_in, data15, si - Q.WARM, s0)
        tri = K.run_policy(data15, apply_thr(data15, P_in, thr_series(data15, P_in), si), 0.0)
        pi = K.daily(tri, si, s0, 1.0); r = min(K.R_CAP, K.SIGMA_TARGET / pi.std()) if pi.std() > 0 else K.R_CAP
        models, ntr = Q.train_window(data15, s0, None)
        P15 = K.predict(models, data15, s0 - Q.WARM, s1); P4 = K.predict(models, data4, s0 - Q.WARM, s1)
        thr = thr_series(data15, P15)
        tr15 = K.run_policy(data15, apply_thr(data15, P15, thr, s0), 0.0).assign(fold=Y, r=r, R_m1=np.nan)
        tr4 = resolve(K.run_policy(data4, apply_thr(data4, P4, thr, s0), 0.0), data4, m1map).assign(fold=Y, r=r)
        p4 = K.daily(tr4.assign(R=tr4["R_m1"]), s0, s1, r)
        f = dict(year=f"{Y}-10〜{Y+1}-09", r=r, n4=len(tr4), R4=float(tr4["R_m1"].mean()) if len(tr4) else None, t4=K.tstat(p4),
                 mean4_pct=float(p4.mean() * 100), n15=len(tr15), R15=float(tr15["R"].mean()), sec=round(time.time() - t0))
        folds.append(f); tr4_all.append(tr4); tr15_all.append(tr15)
        print(f"{f['year']}: 新4本 n={f['n4']} R={f['R4']:.4f} t={f['t4']:.2f} | 15銘柄 n={f['n15']} R={f['R15']:.4f} | {f['sec']}s", flush=True)
    T4 = pd.concat(tr4_all); T15 = pd.concat(tr15_all).reset_index(drop=True)
    del m1map
    parts = []
    for s in SYMS15:      # 15 銘柄側の先着判定は 1 銘柄ずつ（メモリ節約）
        sub = T15[T15["sym"] == s]
        p = os.path.join(a.m1pq, f"{s}_M1.parquet")
        mm = {}
        if os.path.exists(p):
            m = pd.read_parquet(p, columns=["time", "open", "high", "low", "close"])
            mm[s] = (m["time"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(), m)
        parts.append(resolve(sub.drop(columns=["R_m1"]), data15, mm)); del mm
    T15 = pd.concat(parts)
    T4.to_csv(os.path.join(a.out, "trades_q524_new4.csv"), index=False); T15.to_csv(os.path.join(a.out, "trades_q524_15.csv"), index=False)
    def pooled(T):
        p = pd.concat([K.daily(g.assign(R=g["R_m1"]), W.TS(Y), W.TS(Y + 1), g["r"].iloc[0]) for Y, g in T.groupby("fold")])
        return dict(n=int(len(T)), mean_R=float(T["R_m1"].mean()), win=float((T["R_m1"] > 0).mean()), t=K.tstat(p),
                    max_dd_pct=float(K.maxdd(p.to_numpy()) * 100), total_pct=float(p.sum() * 100))
    P4s, P15s = pooled(T4), pooled(T15)
    pos = sum(1 for f in folds if f["mean4_pct"] > 0)
    z, nm, ns = K.null_z(data4, T4.assign(R=T4["R_m1"]), B=200)
    unc = {}
    for s in NEW:
        o = data4[s]; t = o["time"]; m = ((t >= W.TS(YEARS[0])) & (t < W.TS(YEARS[-1] + 1))).to_numpy() & np.isfinite(o["R"]).all(1)
        unc[s] = float(np.nanmean(o["R"][m]))
    bysym = T4.groupby("sym")["R_m1"].agg(["count", "mean"]).round(4).reset_index().to_dict("records")
    verdict = "支持" if (P4s["t"] >= 2 and P4s["mean_R"] > 0 and pos >= 7) else ("棄却" if P4s["mean_R"] <= 0 else "未確定")
    res = dict(qid="Q524", run_at=time.strftime("%Y-%m-%d %H:%M"), folds=folds, new4=P4s, pos_years=pos, null=dict(z=z, mean=nm, sd=ns),
               unconditional_R=unc, by_sym=bysym, s15_same_model=P15s,
               amb_new4=T4["amb"].value_counts().to_dict(), verdict=verdict)
    json.dump(res, open(os.path.join(a.out, "result_q524.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: res[k] for k in ["new4", "pos_years", "null", "unconditional_R", "by_sym", "s15_same_model", "amb_new4", "verdict"]},
                     ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
