#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q364 — SMA200 の上下による順張りと TSMOM(L=60) の相対比較。TREND7 D1 で
封印前の前後半とも年単位 t≥2 を取る合図形式はどちらか（SMA 系 vs 差分系）。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, sma_pos, TREND7  # noqa: E402

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
        return "支持: TSMOM(L=60) が前後半とも年単位 t≥2 かつ bp_net>0。SMA200 の値は summary で比較"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: TSMOM(L=60) 自体が全期間 t<1 または pre/post とも t<1。SMA200 の値を summary で確認"
    return "未確定"


SPEC = Spec(
    qid="Q364",
    question="TREND7 D1 で TSMOM(L=60) と SMA200 の上下による順張りは、封印前の前後半で年単位 t≥2 を取る合図形式がどちらか",
    hypothesis="2 設定を並べる: (1) tsmom(L=60)、(2) sma_pos(n=200)。段階1コスト後の年単位 bp を pre/post 2 本（×2 設定）で比較。main_param=TSMOM(L=60)",
    reject_if="main（TSMOM）が pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定。SMA200 の値は summary で記述比較",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"method": "tsmom", "L": 60}, {"method": "sma", "n": 200}], main_param=0, n_tests=2, warmup=200,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=220,
    discarded="SMA クロス（SMA50/SMA200 のゴールデンクロス）、EMA 版（SMA と大差ない見込み）",
    delegation="なし",
    source="戦略台帳 S01、Faber (2007) 'A Quantitative Approach to Tactical Asset Allocation' の SMA10 ルール、Moskowitz et al. (2012)",
    measure="TSMOM の年単位 bp・t（判定）、SMA200 の年単位 bp・t（記述）、2 合図の相関と露出",
    null_desc="合図の循環シフト（min_shift=220）B=500 → main=TSMOM の年単位 bp の帰無",
    prior_art="Faber (2007) は SMA10（月次）、Moskowitz et al. (2012) は差分型。両者の等価性に関する議論は Zakamulin (2014)",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    close = df["close"].values
    if p.get("method") == "sma":
        return sma_pos(close, int(p["n"]))
    return tsmom_pos(close, int(p["L"]))


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
