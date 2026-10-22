#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q413 S14 前提: 15 銘柄の日次 tick 出来高 z は高値安値レンジ z と冗長か（Spearman）、σ20 とレンジを条件づけても翌 5 日の |ret| を予測するか（出来高に OHLC 以外の情報があるか）。

【出典】[[検証/_基盤/戦略台帳]] 新 S14（出来高）の前提／Blume・Easley・O'Hara 1994 JF（出来高は価格と別の情報を持つ）／Clark 1973・Tauchen・Pitts 1983（混合分布仮説: 出来高とボラは同じ情報到着で動く＝冗長の側）／Parkinson 1980（レンジはボラの効率的な推定量。手元 Q222 系で確定）
【仮説】混合分布仮説が強く成り立つなら tick 出来高の z はレンジ z とほぼ同じ情報（相関 ≥0.8）で、S14 の出来高ゲート（Q411）・加重（Q412）は実現ボラ族（S04b・XAUUSD 高ボラの知見）の言い換えになる。出来高に独立な情報があるなら、レンジ z と σ20 z を取り除いた出来高 z の残差が翌 5 日の |ret|（対数）を正に予測する。
【データ】15 銘柄 all15 の H1_dukascopy を UTC 0 時区切りで日足に束ねる（h1_to_d1。volume＝tick 出来高の日次合計。FX8 2008〜、油/指数 2011-09〜、BTC 2017〜）。封印 time<2024-07-01。出来高 0 の日は欠測（値動きのない足を除いた後の H1 では EURUSD 全年 0%・US500 2012〜17 に 2〜18%）。
【定義】vz＝log 出来高の 250 日 z（t を含む）。rz＝log(high/low) の 250 日 z。sz＝log σ20（直近 20 日 ret の標準偏差）の 250 日 z。y＝log(mean |ret| over t+1..t+5)。残差 e＝vz − (a + b·rz + c·sz) を銘柄ごとに全期間の OLS で（記述。売買ではないので先読みの問題はない）。
【測るもの】(1) 銘柄ごとの Spearman(vz, rz) と中央値。(2) 生 IC＝Spearman(vz, y)、部分 IC＝Spearman(e, y) を銘柄×年で計り、年の中で銘柄平均 → 年単位 t（全期間・前半 <2017・後半 ≥2017）。(3) 出来高 0 の日の割合（銘柄×年。データの質）。
【帰無】vz を年の中で並べ替え（perm_within・銘柄ごと独立・B=500）→ 部分 IC の全期間平均の帰無分布 → z・perm_p。y は重なり（5 日）があるので日次 t は使わず年単位。
【判定（事前固定・変更禁止）】支持（出来高に独立な情報がある）: Spearman(vz, rz) の中央値 <0.6 かつ 部分 IC の年単位 t≥2 が前後半とも かつ 帰無 z≥2。棄却（冗長）: Spearman(vz, rz) の中央値 ≥0.8、または部分 IC の全期間 年単位 t<0。ほか → 未確定。判定は部分 IC の pre/post の 2 本（Holm m=2）。
【捨てた案の数】3（翌 1 日の |ret| を目的＝ノイズが大きい／出来高の水準そのもの（z でない）＝銘柄間で桁が違う／翌 5 日の符号つき ret＝方向は S04c で OHLCV 特徴量に信号が無いと出ている）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）。
【実装】fe_core（load_h1・h1_to_d1・spearman・by_year_stats・perm_within・null_summary・holm・write_result）＋ _s14_common/s14.py の volume_z。--smoke --B 5 で経路確認。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s14_common"))
from fe_core import (SYMS, SPLIT_YEAR, load_h1, h1_to_d1, syms_available, health, spearman, tstat, perm_within,  # noqa: E402
                     null_summary, holm, parse_args, write_result, fmt)
import s14 as S14  # noqa: E402

QID = "Q413"
SEAL = S14.SEAL
K = 5


def _z(x, window=250, min_periods=120):
    s = pd.Series(np.asarray(x, float))
    return ((s - s.rolling(window, min_periods=min_periods).mean()) / s.rolling(window, min_periods=min_periods).std(ddof=1)).values


def _ols_resid(y, X):
    m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    A = np.c_[np.ones(m.sum()), X[m]]
    beta, *_ = np.linalg.lstsq(A, y[m], rcond=None)
    e = np.full(len(y), np.nan); e[m] = y[m] - A @ beta
    return e, beta


def _yearly(df, col):
    """銘柄×年の IC → 年の中で銘柄平均 → 年単位 t（全期間・前半・後半）。"""
    out = {}
    for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}.items():
        d = df[(df["year"] >= y0) & (df["year"] < y1)].dropna(subset=[col])
        yr = d.groupby("year")[col].mean()
        out[pn] = {"n_years": int(len(yr)), "mean": fmt(yr.mean()) if len(yr) else None, "t": fmt(tstat(yr.values)), "_mean": float(yr.mean()) if len(yr) else np.nan}
    return out


def run(args, rng):
    syms, missing = syms_available(SYMS, kind="H1_dukascopy", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="H1_dukascopy")
    if args.smoke:
        syms = syms[:4]
    per = {}; rows = []; frames = {}
    for s in syms:
        d = h1_to_d1(load_h1(s, args.smoke, rng), 0)
        d = d[d["time"] < SEAL].reset_index(drop=True)
        vz = S14.volume_z(d["volume"].values)
        rz = _z(np.log(d["high"].values / d["low"].values))
        sig20 = pd.Series(d["ret"].values).rolling(20, min_periods=20).std(ddof=1)
        sz = _z(np.log(sig20.replace(0, np.nan).values))
        ab = pd.Series(d["ret"].values).abs()
        y = np.log(ab.shift(-1).rolling(K, min_periods=K).mean().shift(-(K - 1)).replace(0, np.nan).values)   # t+1..t+K の平均 |ret|
        e, beta = _ols_resid(vz, np.c_[rz, sz])
        per[s] = {"spearman_vz_rz": fmt(spearman(vz, rz)), "spearman_vz_sz": fmt(spearman(vz, sz)), "beta_rz": fmt(beta[1]) if len(beta) > 1 else None,
                  "ic_raw": fmt(spearman(vz, y)), "ic_partial": fmt(spearman(e, y)), "n": int(np.isfinite(vz).sum()),
                  "zero_volume_frac_by_year": {int(yy): fmt(float((d["volume"].values[d["year"].values == yy] <= 0).mean())) for yy in np.unique(d["year"].values)}}
        f = pd.DataFrame({"year": d["year"].values, "vz": vz, "e": e, "y": y, "sym": s})
        frames[s] = f
        for yy, g in f.groupby("year"):
            if g["y"].notna().sum() >= 60:
                rows.append({"sym": s, "year": int(yy), "ic_raw": spearman(g["vz"].values, g["y"].values), "ic_partial": spearman(g["e"].values, g["y"].values)})
    ic = pd.DataFrame(rows)
    yr_raw = _yearly(ic, "ic_raw"); yr_par = _yearly(ic, "ic_partial")
    med_corr = float(np.nanmedian([v["spearman_vz_rz"] for v in per.values() if v["spearman_vz_rz"] is not None]))
    # 帰無: vz（と残差 e）を年の中で並べ替え → 部分 IC の全期間平均（年単位）
    null_all, null_pre, null_post = [], [], []
    for b in range(args.B):
        nrows = []
        for s, f in frames.items():
            ep = perm_within(rng, f["e"].values, f["year"].values)
            for yy, g_idx in f.groupby("year").groups.items():
                gi = np.asarray(list(g_idx)); yv = f["y"].values[gi]
                if np.isfinite(yv).sum() >= 60:
                    nrows.append({"year": int(yy), "v": spearman(ep[gi], yv)})
        nd = pd.DataFrame(nrows)
        for lst, (y0, y1) in zip((null_all, null_pre, null_post), ((0, 9999), (0, SPLIT_YEAR), (SPLIT_YEAR, 9999))):
            sub = nd[(nd["year"] >= y0) & (nd["year"] < y1)].groupby("year")["v"].mean()
            lst.append(float(sub.mean()) if len(sub) else np.nan)
    ns = {pn: null_summary(yr_par[pn]["_mean"], lst) for pn, lst in (("all", null_all), ("pre", null_pre), ("post", null_post))} if args.B > 0 else {}
    p_holm = holm([ns["pre"]["p_perm"], ns["post"]["p_perm"]]) if ns else [None, None]
    for pn in yr_raw: yr_raw[pn].pop("_mean"); yr_par[pn].pop("_mean")
    # 判定（事前固定）
    t_pre, t_post, t_all = yr_par["pre"]["t"], yr_par["post"]["t"], yr_par["all"]["t"]
    z_all = ns["all"]["z"] if ns else None
    if med_corr >= 0.8 or (t_all is not None and t_all < 0):
        verdict = "棄却: 出来高 z はレンジ z と冗長（中央値 ≥0.8）か、部分 IC の年単位 t<0"
    elif med_corr < 0.6 and t_pre is not None and t_post is not None and t_pre >= 2 and t_post >= 2 and z_all is not None and z_all >= 2:
        verdict = "支持: 出来高 z に OHLC と独立な情報（部分 IC 前後半 t≥2・z≥2・冗長度 <0.6）"
    else:
        verdict = "未確定"
    if dh and (dh["failed"] or dh["gaps"]):
        verdict += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return {"question": __doc__.splitlines()[0].split(": ", 1)[-1], "syms": syms, "missing": missing, "data_health": dh, "seal": str(SEAL.date()),
            "median_spearman_vz_rz": fmt(med_corr), "per_sym": per, "ic_raw_yearly": yr_raw, "ic_partial_yearly": yr_par,
            "null": ns, "p_holm_pre_post": [fmt(p) for p in p_holm], "B": args.B, "n_tests": 2,
            "machine_verdict": verdict, "settings": {"K": K, "z_window": 250, "split_year": SPLIT_YEAR}}, {"ic_sym_year": ic}


if __name__ == "__main__":
    args = parse_args(default_B=500)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    print("machine_verdict:", res["machine_verdict"])
    write_result(QID, res, args.smoke, csvs, here=HERE)
