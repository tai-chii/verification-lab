#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q363 — Baltas-Kosowski 型のアンサンブル: TREND7 D1 で L ∈ {20,60,120,250} の
TSMOM 符号を等重み平均し、L=60 の単発（Q355）に対する分散低減・Sharpe 改善を測る。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, TREND7  # noqa: E402

SEAL_END = "2024-07-01"


class SealedRunner(Runner):
    def _load(self, sym, smoke, rng):
        df = super()._load(sym, smoke, rng)
        return df[df["time"] < pd.Timestamp(SEAL_END)].reset_index(drop=True)


def s01_judge(res, spec):
    m = res["main"]
    pre, post, allp = m.get("pre"), m.get("post"), m.get("all")
    for d, nm in [(pre, "pre"), (post, "post"), (allp, "all")]:
        if d is None or d.get("t_year") is None:
            return f"未確定: {nm} の統計が計算できない"
    if pre["bp_net"] > 0 and post["bp_net"] > 0 and pre["t_year"] >= 2 and post["t_year"] >= 2:
        return "支持: アンサンブルで前後半とも年単位 t≥2 かつ bp_net>0（単発より頑健）"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: アンサンブルでも全期間 t<1 または pre/post とも t<1"
    return "未確定"


SPEC = Spec(
    qid="Q363",
    question="TREND7 D1 で TSMOM 符号の等重みアンサンブル（L=20/60/120/250 の平均）は、単発 L=60 と比べて封印前の前後半で年単位 t≥2 を取りやすいか",
    hypothesis="pos[t] = mean( sign(close[t]-close[t-L]) for L in {20,60,120,250} )。連続値（-1〜1）で等重み平均。段階1コスト後の年単位 bp が pre/post とも t≥2",
    reject_if="pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"Ls": [20, 60, 120, 250]}], main_param=0, n_tests=2, warmup=250,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=260,
    discarded="重みを lookback 長で変える（短期を重く／長期を重く）、符号ではなく z-score の平均",
    delegation="なし",
    source="Baltas & Kosowski (2013) 'Momentum Strategies in Futures Markets and Trend-following Funds' — 複数頻度の平均。戦略台帳 S01",
    measure="アンサンブルの年単位 bp・t・Sharpe、L=60 単発（Q355）に対する差、露出と取引回数",
    null_desc="合図の循環シフト（min_shift=260）B=500 → 年単位 bp の帰無",
    prior_art="Baltas & Kosowski (2013) は複数の lookback の平均で Sharpe が単発より高いと報告。Hurst et al. (2017) も同系統",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    """pos[t] = mean( sign(close[t]-close[t-L]) ). 連続値（-1〜1）。shift しない。"""
    close = df["close"].values
    Ls = [int(L) for L in p["Ls"]]
    stack = np.stack([tsmom_pos(close, L) for L in Ls], axis=0)
    return stack.mean(axis=0)


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
