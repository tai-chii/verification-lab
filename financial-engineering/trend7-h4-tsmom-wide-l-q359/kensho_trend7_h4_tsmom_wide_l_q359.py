#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q359 — H4 の TSMOM lookback を広げて（L ∈ {120,240,480}）、Q261（L=60 不支持）が
短すぎる lookback の問題か、H4 自体が合わないかを切り分ける。TREND7。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, TREND7, load_csv  # noqa: E402
from fe_core.data import _mark_gaps  # noqa: E402

SEAL_END = "2024-07-01"


class SealedRunner(Runner):
    def _load(self, sym, smoke, rng):
        df = load_csv(f"{sym}_H4_dukascopy", smoke, rng, freq="4h", n=20000)
        df = df[df["high"] != df["low"]].reset_index(drop=True)
        df["ret"] = df["close"].pct_change()
        df["year"] = df["time"].dt.year
        df = _mark_gaps(df, "H4")
        if self.spec.start:
            df = df[df["time"] >= pd.Timestamp(self.spec.start)].reset_index(drop=True)
        df = df[df["time"] < pd.Timestamp(SEAL_END)].reset_index(drop=True)
        return df


def s01_judge(res, spec):
    m = res["main"]
    pre, post, allp = m.get("pre"), m.get("post"), m.get("all")
    for d, nm in [(pre, "pre"), (post, "post"), (allp, "all")]:
        if d is None or d.get("t_year") is None:
            return f"未確定: {nm} の統計が計算できない"
    if pre["bp_net"] > 0 and post["bp_net"] > 0 and pre["t_year"] >= 2 and post["t_year"] >= 2:
        return "支持: H4 の広い L でも前後半とも t≥2 かつ bp_net>0"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: 広い L でも全期間 t<1 または pre/post とも t<1（H4 は合わない）"
    return "未確定"


SPEC = Spec(
    qid="Q359",
    question="TREND7 の H4 TSMOM で L を広げる（120/240/480 本 ≒ 20/40/80 日）と、Q261 の L=60（≒10 日）不支持は改善するか",
    hypothesis="pos[t]=sign(close[t]−close[t−L]) を H4 で L=120/240/480 の 3 本に広げ、main_param=L=240 の pre/post 2 本に Holm m=3 を当てる",
    reject_if="main（L=240）が pre・post とも t≥2 かつ bp_net>0 → 支持（lookback 問題）。全期間 t<1 もしくは pre/post とも t<1 → 棄却（H4 の問題）。ほか → 未確定",
    syms=list(TREND7), kind="H1_dukascopy",
    params=[{"L": 120}, {"L": 240}, {"L": 480}], main_param=1, n_tests=3, warmup=480,
    B=500, split_year=2017, start="2012-02-01", per_year=252 * 6,
    null_kind="circ_shift", null_min_shift=500,
    discarded="L=60（Q261 で既に棄却）、L=960（180 日はほぼ日足と同じ）",
    delegation="なし",
    source="知見 Q261（H4 L=60 trend7 不支持）、戦略台帳 S01、Moskowitz et al. (2012)",
    measure="3 本の年単位 bp・t、main の pre/post 2 本の perm_p・Holm、Sharpe・最大下落・露出",
    null_desc="合図の循環シフト（min_shift=500）B=500 → main の年単位 bp の帰無",
    prior_art="Hurst, Ooi & Pedersen (2017) の trend-following は日次〜週次。H4 の TSMOM 単独の実証は乏しい",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 H4_dukascopy（4 時間足）を _load 上書きで直接読む。2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
