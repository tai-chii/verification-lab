#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q397 S11 前提: 48 銘柄 D1 で実測スプレッドの 5 日平均 z は翌 5 日の実現ボラ／σ60 の比を予測するか（σ60 に無い情報・年単位 IC の t）。

【出典】[[検証/_基盤/戦略台帳]] 新 S11（スプレッド）／Bollerslev・Melvin 1994 JIE（ボラ → スプレッド）／Q396（スプレッドゲートの前提）／S04b Q387（HAR の σ̂ は σ60 に勝てず）
【仮説】スプレッドはマーケットメイカーの在庫リスクの予想を映す（Bollerslev・Melvin はボラ→スプレッドの向き）。逆向き（スプレッド→将来ボラ）が σ60 を超えて残るなら、
    スプレッドは OHLCV に無いボラ情報を持ち、Q396 のゲートや S04b 型のサイジングの部品になる。x[t]=直近 5 日のスプレッド（往復・価格比）平均を 250 日で z 化、
    y[t]=sqrt(mean(ret[t+1..t+5]^2))／σ60[t]（σ60 は t までの 60 日 ret の標準偏差）。
【データ】48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01・_データ/raw/D1）＋ spread_<sym>.csv。スプレッドの無い銘柄は除いて missing に。
【定義】年ごとに全銘柄の (x, y) を束ねたスピアマン IC を 1 つ出す（年 × 1 本）。参照: x_ref=σ20/σ60（ボラ・モメンタム）の IC を同じ形で並べる。
【測るもの】IC の年単位平均と t（全期間・前半 <2017・後半）、参照 IC、銘柄別 IC（記述）。
【帰無】銘柄ごと・年内で x を並べ替え（perm_within・B=500）→ 年単位 IC 平均の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）。
【判定（事前固定・変更禁止）】支持: 前後半とも IC の年単位 t≥2 かつ Holm 後 p<0.05 かつ IC 平均>0。棄却: 全期間の年単位 t<1 または z<1。ほか → 未確定。
    参照 IC・銘柄別は記述。S11 の族内試行は Q396（2 設定）・Q397（1 本）＝3。
【捨てた案の数】2（y を実現ボラの水準にする＝σ60 と同じ情報を測ってしまう／HAR を対照にする＝Q387 で σ60 に負けたので σ60 で足りる）
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）。
【先行研究】WebSearch 2026-10-22「bid-ask spread predicts future realized volatility FX daily data incremental to GARCH HAR」: Bollerslev・Melvin 1994、Wei 1991、
    Bissoondoyal-Bheenick ほか 2016 はいずれもボラ→スプレッドの向き。スプレッド→将来の相対ボラの予測力の判定は未確認。
【実装】fe_core を直接使う（イベント型と同じ形）。--smoke --B 5 で経路確認。本番 B=500。
"""
import os
import sys
import time as _time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import (parse_args, write_result, load_d1, syms_available, health, spearman, tstat, holm,  # noqa: E402
                     null_summary, perm_within, fmt, GROUPS)
import s1x as X  # noqa: E402

QID = "Q397"
SYMS = list(GROUPS["wide48"])
SPLIT = 2017
K = 5
SPEC = {"qid": QID, "question": "48 銘柄 D1 で実測スプレッドの 5 日平均 z は翌 5 日の実現ボラ／σ60 の比を予測するか",
        "reject_if": "支持: 前後半とも IC の年単位 t≥2 かつ Holm 後 p<0.05 かつ IC 平均>0。棄却: 全期間の年単位 t<1 または z<1。ほか → 未確定",
        "n_tests": 2, "split_year": SPLIT, "seal": str(X.SEAL.date()), "k": K, "z_window": 250, "discarded": 2, "designer": "Fable",
        "batch": "/lab-plan ターミナル版 2026-10-22 夜・N=10 の 4 本目（S11・前提）"}


def build(sym, smoke, rng):
    df = load_d1(sym, smoke=smoke, rng=rng); df = df[df["time"] < X.SEAL].reset_index(drop=True)
    df = df[df["time"] >= pd.Timestamp("2010-01-01")].reset_index(drop=True)
    sp, src = X.spread_rel_daily(sym, df["time"].values, smoke=smoke, rng=rng)
    if src == "none":
        return None
    r = df["ret"].values.astype(float)
    x = X.rolling_z(pd.Series(sp).rolling(5, min_periods=3).mean().values, 250, 120)
    s60 = pd.Series(r).rolling(60, min_periods=40).std(ddof=1).values
    s20 = pd.Series(r).rolling(20, min_periods=15).std(ddof=1).values
    r2 = pd.Series(r ** 2); fut = r2.shift(-1).rolling(K).mean().shift(-(K - 1)).values  # mean(ret[t+1..t+K]^2)
    y = np.sqrt(fut) / s60
    out = pd.DataFrame({"time": df["time"].values, "year": df["year"].values, "sym": sym, "x": x, "y": y, "x_ref": s20 / s60})
    return out.dropna()


def yearly_ic(d, col="x"):
    return d.groupby("year").apply(lambda g: spearman(g[col].values, g["y"].values) if len(g) >= 100 else np.nan).dropna()


def stats(ic):
    return {"all": {"mean": fmt(ic.mean()), "t": fmt(tstat(ic.values)), "n_years": int(len(ic))},
            "pre": {"mean": fmt(ic[ic.index < SPLIT].mean()), "t": fmt(tstat(ic[ic.index < SPLIT].values)), "n_years": int((ic.index < SPLIT).sum())},
            "post": {"mean": fmt(ic[ic.index >= SPLIT].mean()), "t": fmt(tstat(ic[ic.index >= SPLIT].values)), "n_years": int((ic.index >= SPLIT).sum())}}


def run(args, rng):
    t0 = _time.time()
    syms, missing = syms_available(SYMS, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="D1_fromH1")
    frames = []; no_spread = []
    for s in syms:
        d = build(s, args.smoke, rng)
        if d is None:
            no_spread.append(s)
        else:
            frames.append(d)
    pool = pd.concat(frames, ignore_index=True)
    ic = yearly_ic(pool); ic_ref = yearly_ic(pool, "x_ref")
    obs = stats(ic); ref = stats(ic_ref)
    per_sym = {s: fmt(spearman(g["x"].values, g["y"].values)) for s, g in pool.groupby("sym")}
    # 帰無: 銘柄ごと・年内で x を並べ替え
    null = {"all": [], "pre": [], "post": []}
    if args.B > 0:
        for _ in range(args.B):
            xp = pool.groupby("sym", sort=False)["x"].transform(lambda v: perm_within(rng, v.values, pool.loc[v.index, "year"].values))
            tmp = pool.assign(x=xp.values); icn = yearly_ic(tmp)
            null["all"].append(icn.mean()); null["pre"].append(icn[icn.index < SPLIT].mean()); null["post"].append(icn[icn.index >= SPLIT].mean())
    main = {}
    for pn in ("all", "pre", "post"):
        ns = null_summary(ic.mean() if pn == "all" else (ic[ic.index < SPLIT].mean() if pn == "pre" else ic[ic.index >= SPLIT].mean()), null[pn]) if null[pn] else {}
        main[pn] = dict(obs[pn], z=fmt(ns.get("z")), p_perm=fmt(ns.get("p_perm")), null_degenerate=ns.get("degenerate"))
    adj = holm([main["pre"].get("p_perm") if main["pre"].get("p_perm") is not None else np.nan,
                main["post"].get("p_perm") if main["post"].get("p_perm") is not None else np.nan])
    main["pre"]["p_holm"], main["post"]["p_holm"] = fmt(adj[0]), fmt(adj[1])
    # 判定（事前固定）
    ok = lambda v: v is not None and v == v  # noqa: E731
    if not all(ok(main[p]["t"]) for p in ("all", "pre", "post")) or not ok(main["all"]["z"]):
        verdict = "未確定: 計算できない"
    elif main["all"]["t"] < 1 or main["all"]["z"] < 1:
        verdict = "棄却: 全期間の年単位 t<1 または z<1"
    elif (main["pre"]["t"] >= 2 and main["post"]["t"] >= 2 and ok(main["pre"]["p_holm"]) and ok(main["post"]["p_holm"])
          and main["pre"]["p_holm"] < 0.05 and main["post"]["p_holm"] < 0.05 and main["all"]["mean"] > 0):
        verdict = "支持: 前後半とも IC の年単位 t≥2・Holm 後 p<0.05・IC>0"
    else:
        verdict = "未確定"
    res = {"question": SPEC["question"], "spec": SPEC, "missing": missing, "no_spread": no_spread, "data_health": dh, "n_syms_used": int(pool["sym"].nunique()),
           "n_rows": int(len(pool)), "main": main, "ic_by_year": {int(k): fmt(v) for k, v in ic.items()}, "ref_vol_momentum": ref,
           "per_sym_ic": per_sym, "multiple_comparisons": "判定は前後半 2 本（Holm）。参照・銘柄別は記述", "machine_verdict": verdict,
           "elapsed_s": round(_time.time() - t0, 1)}
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


if __name__ == "__main__":
    args = parse_args(default_B=500)
    if not args.smoke:
        ok, _ = syms_available(SYMS, kind="D1_fromH1")
        if len(ok) < 40:
            write_result(QID, {"status": "データ待ち", "n_ok": len(ok)}, smoke=False, here=HERE); print("データ待ち"); sys.exit(2)
    rng = np.random.default_rng(args.seed)
    res = run(args, rng)
    print("machine_verdict:", res["machine_verdict"])
    print(write_result(QID, res, args.smoke, here=HERE))
