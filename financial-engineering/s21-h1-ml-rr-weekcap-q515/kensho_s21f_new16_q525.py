# -*- coding: utf-8 -*-
"""Q525: S21f のモデル（15 銘柄で学習）を、学習に使っていない 16 銘柄（FX クロス 8・指数 5・商品 3）に当てる。事前登録_q525.md。
使い方: python3 kensho_s21f_new16_q525.py --h1 DIR --m1zip DIR --m1pq DIR --d1 DIR(data_*_D1_fromH1.csv, spread_*.csv) --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J

GROUPS = {"FXクロス": ["EURAUD", "EURCAD", "EURCHF", "GBPAUD", "GBPCAD", "GBPCHF", "AUDNZD", "AUDCAD"],
          "指数": ["UK100", "FRA40", "EUSTX50", "AUS200", "HKG33"],
          "商品": ["WTI", "BRENT", "XAGUSD"]}
NEW = [s for g in GROUPS.values() for s in g]
G_OF = {s: g for g, ss in GROUPS.items() for s in ss}
for s in GROUPS["FXクロス"]: K.CLASS[s] = 0
for s in GROUPS["商品"]: K.CLASS[s] = 1
for s in GROUPS["指数"]: K.CLASS[s] = 2
YEARS = J.YEARS


def level_ratio(h, d1_dir, sym):
    d1 = pd.read_csv(os.path.join(d1_dir, f"data_{sym}_D1_fromH1.csv"), parse_dates=["time"])
    hd = h.set_index(h["time"].dt.tz_convert(None))["close"].resample("D").last().dropna()
    j = pd.concat([hd.rename("hd"), d1.set_index("time")["close"].rename("dk")], axis=1).dropna()
    return float((j["hd"] / j["dk"]).median()), len(j)


def main():
    ap = argparse.ArgumentParser()
    for x in ["h1", "m1zip", "m1pq", "d1", "out"]:
        ap.add_argument(f"--{x}", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    print("15 銘柄", flush=True)
    data15 = {s: J.make(K.load(a.h1, s), s) for s in J.SYMS15}
    dataN, info = {}, {}
    for s in NEW:
        m1 = J.m1_from_zips(os.path.join(a.m1zip, s))
        h = J.h1_new(s, m1, a.d1)
        ratio, nj = level_ratio(h, a.d1, s)
        if not (0.9 <= ratio <= 1.1):          # 水準がずれている → スプレッドを比で換算（事前登録どおり）
            sp = h["spread"] * ratio
            for c in ["open", "high", "low", "close"]:
                h[f"ask_{c}"] = h[c] + sp
            h["spread"] = sp
        dataN[s] = J.make(h, s)
        del m1
        info[s] = dict(h1=len(h), start=str(h.time.min()), level_ratio=round(ratio, 4), n_days=nj,
                       spr_R=round(float(np.nanmedian(dataN[s]["d"]["spread"].to_numpy() / dataN[s]["D"])), 4))
        print(f"  {s}: {info[s]}", flush=True)
    folds, trN = [], []
    for Y in YEARS:
        t0 = time.time(); s0, s1, si = W.TS(Y), W.TS(Y + 1), W.TS(Y - 1)
        m_in, _ = Q.train_window(data15, si, None)
        P_in = K.predict(m_in, data15, si - Q.WARM, s0)
        tri = K.run_policy(data15, J.apply_thr(data15, P_in, J.thr_series(data15, P_in), si), 0.0)
        pi = K.daily(tri, si, s0, 1.0); r = min(K.R_CAP, K.SIGMA_TARGET / pi.std()) if pi.std() > 0 else K.R_CAP
        models, _ = Q.train_window(data15, s0, None)
        P15 = K.predict(models, data15, s0 - Q.WARM, s1); PN = K.predict(models, dataN, s0 - Q.WARM, s1)
        thr = J.thr_series(data15, P15)
        tr = K.run_policy(dataN, J.apply_thr(dataN, PN, thr, s0), 0.0).assign(fold=Y, r=r)
        tr["R_m1"] = tr["R"].astype(float)   # 先着判定はループの後で 1 銘柄ずつ
        tr["grp"] = tr["sym"].map(G_OF)
        f = dict(year=f"{Y}-10〜{Y+1}-09", r=r, n=len(tr), R=float(tr["R"].mean()) if len(tr) else None,
                 by_grp=tr.groupby("grp")["R"].agg(["count", "mean"]).round(4).to_dict("index"), sec=round(time.time() - t0))
        folds.append(f); trN.append(tr)
        print(f"{f['year']}: 16銘柄 n={f['n']} R={f['R']:.4f} | " + " ".join(f"{g}:{v['count']}件 {v['mean']:+.3f}" for g, v in f["by_grp"].items()) + f" | {f['sec']}s", flush=True)
    T = pd.concat(trN).reset_index(drop=True); parts = []
    for s in NEW:                          # 1 分足を 1 銘柄ずつ読み直して先着判定（メモリ節約）
        sub = T[T["sym"] == s].drop(columns=["R_m1"])
        m1 = J.m1_from_zips(os.path.join(a.m1zip, s))
        parts.append(J.resolve(sub, dataN, {s: (m1["time"].dt.tz_convert(None).to_numpy(), m1)})); del m1
    T = pd.concat(parts); T.to_csv(os.path.join(a.out, "trades_q525_new16.csv"), index=False)

    def judge(TT):
        if len(TT) == 0:
            return dict(n=0)
        p = pd.concat([K.daily(g.assign(R=g["R_m1"]), W.TS(Y), W.TS(Y + 1), g["r"].iloc[0]) for Y, g in TT.groupby("fold")])
        yr = [K.daily(g.assign(R=g["R_m1"]), W.TS(Y), W.TS(Y + 1), g["r"].iloc[0]).mean() for Y, g in TT.groupby("fold")]
        pos = int(sum(1 for v in yr if v > 0)); t = K.tstat(p); m = float(TT["R_m1"].mean())
        v = "支持" if (t >= 2 and m > 0 and pos >= 7) else ("棄却" if m <= 0 else "未確定")
        return dict(n=int(len(TT)), mean_R=m, win=float((TT["R_m1"] > 0).mean()), t=t, pos_years=pos, n_years=len(yr),
                    max_dd_pct=float(K.maxdd(p.to_numpy()) * 100), total_pct=float(p.sum() * 100), verdict=v)
    tot = judge(T); grp = {g: judge(T[T["grp"] == g]) for g in GROUPS}
    z, nm, ns = K.null_z(dataN, T.assign(R=T["R_m1"]), B=200)
    unc = {}
    for s in NEW:
        o = dataN[s]; t = o["time"]; m = ((t >= W.TS(YEARS[0])) & (t < W.TS(YEARS[-1] + 1))).to_numpy() & np.isfinite(o["R"]).all(1)
        unc[s] = round(float(np.nanmean(o["R"][m])), 4)
    bysym = T.groupby("sym")["R_m1"].agg(["count", "mean"]).round(4).reset_index().to_dict("records")
    adopt = [g for g in GROUPS if tot.get("verdict") == "支持" and grp[g].get("mean_R", -1) > 0]
    res = dict(qid="Q525", run_at=time.strftime("%Y-%m-%d %H:%M"), info=info, folds=folds, total=tot, groups=grp,
               null=dict(z=z, mean=nm, sd=ns), unconditional_R=unc, by_sym=bysym, amb=T["amb"].value_counts().to_dict(),
               adopt_groups_for_final=adopt)
    json.dump(res, open(os.path.join(a.out, "result_q525.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: res[k] for k in ["total", "groups", "null", "by_sym", "unconditional_R", "adopt_groups_for_final"]}, ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
