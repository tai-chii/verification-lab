# -*- coding: utf-8 -*-
"""Q695: S21 の D1/H4 の区切りを 22:00 UTC 固定から NY 17:00（夏時間追従）に変えると WF の成績は良くなるか。事前登録_q695.md（変更しない）。
【出典】taichi 2026-11-09 深夜の S21 コード読み合わせ（アイデア候補 2026-11-09・Q695）。Q521 の mtf_feats は CUT=2h 固定 → 米の夏時間の間、日曜 21:00 UTC の足 1 本が 1 つの「日」になる。
【仮説】NY 17:00 で日を切ると、夏の月曜の d1p_*（前日からの乖離）が金曜のセッション全体からの乖離になり、WF の t が上がり、月曜の夏／冬の平均 R の差が縮む。
【データ】Dukascopy H1 15 銘柄（作業層/大容量/market_data/H1・Q533 と同じ）。2014-10〜2025-09 の 11 年・年 1 回学習。最終 1 年（2025-10〜）は封印のまま。
【定義】A: Q533 D2（週末前決済で学習・mtf の区切り 22:00 UTC 固定）。B: 同じ設計で mtf_feats の日・H4 の区切りだけ NY の壁時計 17:00（夏 21:00 UTC・冬 22:00 UTC、H4 は NY 17/21/01/05/09/13）。
【測るもの】日次 t・平均 R・合計 R・最大下落 R・年 R÷最大下落・プラスの年、月曜（entry が UTC 月曜）の平均 R の夏／冬の差、日次差（B−A）の t、最後の年のモデルでの d1p_*/h4p_* の重要度順位。
【判定（事前固定・変更禁止）】支持: t_B > t_A かつ |月曜 夏−冬|_B < |月曜 夏−冬|_A かつ (年R÷最大下落)_B ≥ (年R÷最大下落)_A。未確定: 前 2 つは満たすが 年R÷最大下落 が B < A。棄却: それ以外。
【扱い】支持でもフォワード中の S21 は変えない。採用は運用規程 §4 の 10-01 学習し直し（別 ID で凍結）でのみ。参考扱い（何度も使った期間）。
【捨てた案の数】0。【知識の締め切り】Fable 2026-06。【委託の確かめ方】results/result_q695.json・run_q695.log・trades_q695_{A,B}.csv・--check。
使い方: python kensho_s21_nycut_q695.py --data DIR --out DIR [--check]（lightgbm・pyarrow。venv_forward の python。所要 20〜30 分）"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
Q515 = os.path.join(HERE, "..", "s21-h1-ml-rr-weekcap-q515")
sys.path.insert(0, Q515)
sys.path.insert(1, os.path.join(HERE, "..", "..", "..", "_データ", "fetch"))   # Q533 → Q524 → convert_histdata_m15（検証/_データ/fetch）
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_mtf_wf_q521 as M
import kensho_s21_noweekend_q533 as N

QID = "Q695"
YEARS = list(range(2014, 2025))          # 評価年 Y-10-01〜Y+1-10-01（Q533 と同じ 11 年）
SYMS15 = list(K.SYMS)
NY = "America/New_York"; SHIFT = pd.Timedelta(hours=7)   # NY 17:00 を 0 時に揃える
MTF = ["d1p_hi", "d1p_lo", "d1p_cl", "d1p_rng", "d1p_body", "d0_open", "d0_hi", "d0_lo", "h4p_hi", "h4p_lo", "h4p_cl", "h4p_rng", "h4p_body"]


# ---- Q524 の thr_series / apply_thr（同じ式。Q524 本体は HistData の変換モジュールを import するので写した）
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


# ---- B の mtf_feats（M.mtf_feats と同じ式・区切りだけ NY 17:00）
def ny_key(t, freq):
    """足の時刻（UTC）→ NY の壁時計を 7 時間ずらして floor した区切りの鍵（naive）。夏時間込み。"""
    wall = t.dt.tz_convert(NY).dt.tz_localize(None) + SHIFT
    return wall.dt.floor(freq)


def mtf_feats_ny(d, D):
    t = d["time"]; atr = pd.Series(D / K.K_ATR, index=d.index); c = d["close"]
    out = pd.DataFrame(index=d.index); dec = t + pd.Timedelta(hours=1)
    for name, freq in [("d1", "D"), ("h4", "4h")]:
        g = ny_key(t, freq)
        agg = d.assign(g=g).groupby("g").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), end=("time", "max"))
        agg["end"] = agg["end"] + pd.Timedelta(hours=1)
        agg = agg.reset_index(drop=True).sort_values("end")
        m = pd.merge_asof(pd.DataFrame({"dec": dec, "k": np.arange(len(d))}).sort_values("dec"), agg, left_on="dec", right_on="end",
                          direction="backward").sort_values("k").reset_index(drop=True)
        p = "d1p" if name == "d1" else "h4p"
        out[f"{p}_hi"] = (c.to_numpy() - m["h"].to_numpy()) / atr.to_numpy()
        out[f"{p}_lo"] = (c.to_numpy() - m["l"].to_numpy()) / atr.to_numpy()
        out[f"{p}_cl"] = (c.to_numpy() - m["c"].to_numpy()) / atr.to_numpy()
        out[f"{p}_rng"] = (m["h"] - m["l"]).to_numpy() / atr.to_numpy()
        out[f"{p}_body"] = (m["c"] - m["o"]).to_numpy() / atr.to_numpy()
        if name == "d1":
            gd = d.assign(g=g)
            day_open = gd.groupby("g")["open"].transform("first")
            day_hi = gd.groupby("g")["high"].cummax(); day_lo = gd.groupby("g")["low"].cummin()
            out["d0_open"] = (c - day_open) / atr; out["d0_hi"] = (c - day_hi) / atr; out["d0_lo"] = (c - day_lo) / atr
    return out.replace([np.inf, -np.inf], np.nan)


def atr_D(d):
    bh, bl, bc = (d[c].to_numpy(float) for c in ["high", "low", "close"])
    tr = np.maximum(bh - bl, np.maximum(np.abs(bh - np.r_[bc[0], bc[:-1]]), np.abs(bl - np.r_[bc[0], bc[:-1]])))
    return K.K_ATR * pd.Series(tr).rolling(24, min_periods=24).mean().to_numpy()


def make(d, s, mtf):
    """Q524 の make と同じ（vol_ratio 抜き）。ラベルは Q533 の labels_wk（週末前決済）。mtf だけ差し替え可。"""
    d = d[d["high"] != d["low"]].reset_index(drop=True)
    if "spr" not in d:
        d["spr"] = (d["ask_close"] - d["close"]).clip(lower=0)
    D = atr_D(d)
    F = pd.concat([K.features(d, D, s).reset_index(drop=True), mtf(d, D).reset_index(drop=True)], axis=1).drop(columns=["vol_ratio"])
    Rw, Xw = N.labels_wk(d, s)
    return dict(time=d["time"].reset_index(drop=True), R=Rw, X=Xw, F=F, d=d, D=D)


def monday_split(tr):
    """入った足が UTC 月曜の取引を、入った時刻に NY が夏時間なら夏、そうでなければ冬。平均 R と件数、差。火〜金も参考に。"""
    ent = pd.to_datetime(tr["entry"], utc=True)
    wd = ent.dt.weekday.to_numpy()
    summer = ent.dt.tz_convert(NY).map(lambda x: x.utcoffset().total_seconds() == -4 * 3600).to_numpy()
    out = {}
    for label, mask in [("月曜", wd == 0), ("火〜金", (wd >= 1) & (wd <= 4))]:
        s_ = tr["R"].to_numpy()[mask & summer]; w_ = tr["R"].to_numpy()[mask & ~summer]
        ms, mw = (float(s_.mean()) if len(s_) else np.nan), (float(w_.mean()) if len(w_) else np.nan)
        out[label] = dict(夏_n=int(len(s_)), 夏_mean_R=ms, 冬_n=int(len(w_)), 冬_mean_R=mw, 差=float(abs(ms - mw)) if np.isfinite(ms) and np.isfinite(mw) else None)
    return out


def check(a):
    """--check: EURUSD の夏・冬の週明けで、A（22:00 固定）と B（NY 17:00）の日の鍵がどう違うかを印字する（結果は読まない）。"""
    d = K.load(a.data, "EURUSD"); t = d["time"]
    ga = (t + M.CUT).dt.floor("D"); gb = ny_key(t, "D")
    for lab, start in [("夏（2025-07-06 日）", "2025-07-06 19:00"), ("冬（2025-01-12 日）", "2025-01-12 19:00"), ("切り替え週（2025-03-09 日）", "2025-03-09 19:00")]:
        s = pd.Timestamp(start, tz="UTC"); m = (t >= s) & (t < s + pd.Timedelta(hours=10))
        print(f"--- {lab}: 足の時刻 UTC | A の日の鍵 | B の日の鍵")
        for tt, x, y in zip(t[m], ga[m], gb[m]):
            print(f"  {tt:%a %m-%d %H:%M} | {x:%m-%d} | {y:%m-%d}")
    # 夏の月曜に「前日」が日曜の 1 本になっている割合（A）と B の様子
    for lab, g in [("A", ga), ("B", gb)]:
        n_per_day = d.assign(g=g).groupby("g").size()
        one = n_per_day[n_per_day == 1]
        print(f"{lab}: 1 本だけの「日」 {len(one)} 個（全 {len(n_per_day)} 日）。例: {list(one.index[:3])}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    if a.check:
        check(a); return
    os.makedirs(a.out, exist_ok=True); t0 = time.time()
    data = {}
    for s in SYMS15:
        raw = K.load(a.data, s)
        data[("A", s)] = make(raw, s, M.mtf_feats); data[("B", s)] = make(raw, s, mtf_feats_ny)
        print(f"  {s}: {len(raw)} 本 {time.time()-t0:.0f}s", flush=True)
    DATA = {k: {s: data[(k, s)] for s in SYMS15} for k in ("A", "B")}
    # mtf の列が A と B でどれだけ違うか（記述）
    diffcols = {}
    for c in MTF:
        xa = pd.concat([DATA["A"][s]["F"][c] for s in SYMS15]); xb = pd.concat([DATA["B"][s]["F"][c] for s in SYMS15])
        diffcols[c] = float((xa.to_numpy() != xb.to_numpy()).mean())
    print("A≠B の行の割合（mtf 列）", json.dumps({k: round(v, 3) for k, v in diffcols.items()}), flush=True)
    TR = {k: [] for k in ("A", "B")}; DY = {k: [] for k in TR}; IMP = {}
    for Y in YEARS:
        t1 = time.time(); s0, s1 = W.TS(Y), W.TS(Y + 1); msg = []
        for k in ("A", "B"):
            dd_ = DATA[k]
            m, _ = Q.train_window(dd_, s0, None)
            P = K.predict(m, dd_, s0 - Q.WARM, s1); PP = apply_thr(dd_, P, thr_series(dd_, P), s0)
            tr = K.run_policy(dd_, PP, 0.0).assign(fold=Y)
            TR[k].append(tr); DY[k].append(N.daily(tr, s0, s1))
            msg.append(f"{k} n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f}")
            if Y == YEARS[-1]:
                cols = list(dd_[SYMS15[0]]["F"].columns)
                imp = np.mean([mm.booster_.feature_importance("gain") for mm in m], axis=0)
                rk = pd.Series(imp, index=cols).sort_values(ascending=False)
                IMP[k] = dict(rank_mtf={c: int(list(rk.index).index(c)) + 1 for c in MTF}, top10=list(rk.index[:10]))
        print(f"{Y}: " + " | ".join(msg) + f" | {time.time()-t1:.0f}s", flush=True)
    res = dict(qid=QID, run_at=time.strftime("%Y-%m-%d %H:%M"), note="R 単位・H1 判定・2014-10〜2025-09・Q533 D2 と同じ設計・参考", years=YEARS, mtf_diff_share=diffcols)
    lab = {"A": "Q533 D2（区切り 22:00 UTC 固定）", "B": "同じ設計・区切り NY 17:00（夏 21:00・冬 22:00 UTC）"}
    P = {}
    for k in TR:
        tr = pd.concat(TR[k]); p = pd.concat(DY[k]).groupby(level=0).sum(); P[k] = p
        tr.to_csv(os.path.join(a.out, f"trades_q695_{k}.csv"), index=False)
        res[k] = dict(label=lab[k], **N.stats(tr, p, 11), weekday_summer_winter=monday_split(tr), importance=IMP.get(k))
        print(k, json.dumps({x: res[k][x] for x in ["label", "n", "mean_R", "t", "total_R", "max_dd_R", "annual_R_per_dd", "pos_years"]}, ensure_ascii=False), flush=True)
        print("  月曜 夏／冬", json.dumps(res[k]["weekday_summer_winter"], ensure_ascii=False), flush=True)
    j = pd.concat([P["A"].rename("A"), P["B"].rename("B")], axis=1).fillna(0.0)
    res["daily_diff_B_minus_A"] = dict(t=K.tstat((j["B"] - j["A"]).to_numpy()), mean_R=float((j["B"] - j["A"]).mean()), n_days=int(len(j)))
    A, B = res["A"], res["B"]
    gA = A["weekday_summer_winter"]["月曜"]["差"]; gB = B["weekday_summer_winter"]["月曜"]["差"]
    c1 = B["t"] > A["t"]; c2 = (gA is not None and gB is not None and gB < gA); c3 = B["annual_R_per_dd"] >= A["annual_R_per_dd"]
    res["criteria"] = dict(t_B_gt_A=bool(c1), monday_gap_shrinks=bool(c2), annR_per_dd_B_ge_A=bool(c3))
    res["machine_verdict"] = "支持" if (c1 and c2 and c3) else ("未確定" if (c1 and c2) else "棄却")
    res["sec"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(a.out, f"result_{QID.lower()}.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("日次差 B−A", json.dumps(res["daily_diff_B_minus_A"]), "| 判定", res["criteria"], res["machine_verdict"], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
