#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q356 — S01 の lookback 感度。TREND7 D1 TSMOM の L ∈ {20,60,120,250} で、
Holm 補正後も main（L=60）が封印前の前後半で t≥2 を保てるか。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np  # noqa: F401
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
        return "支持: main（L=60）が前後半とも年単位 t≥2 かつ bp_net>0（Holm m=4 補正後も残れば頑健）"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: main の全期間 t<1 または pre/post とも t<1"
    return "未確定: 片方のみ t≥2 または全期間 t が 1〜2"


SPEC = Spec(
    qid="Q356",
    question="TREND7 D1 TSMOM の L ∈ {20,60,120,250} の掃引で、main（L=60）は Holm m=4 補正後も封印前の前後半で t≥2 を保つか（S01 の lookback 頑健性）",
    hypothesis="同じ合図規則で L を 20/60/120/250 の 4 本に広げ、main_param=L=60 の pre/post 2 本に Holm m=4 を当てる。L=60 が結果を見てからの選択でないことを示す目的で、全 4 本の年単位 t を併記",
    reject_if="main（L=60）が pre・post とも t≥2 かつ bp_net>0 → 支持（頑健）。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 20}, {"L": 60}, {"L": 120}, {"L": 250}], main_param=1, n_tests=4, warmup=250,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=260,
    discarded="L=10・L=500 を事前の文献範囲外として捨てた（Moskowitz 系の典型は 1〜12 か月）",
    delegation="なし",
    source="戦略台帳 S01、Moskowitz ほか (2012) の表3（1〜12m lookback の広がり）、Q355 の本体",
    measure="4 本の年単位 bp・t、main の pre/post 2 本の perm_p・Holm、L × 期間の表",
    null_desc="合図の循環シフト（min_shift=260）B=500 → main の年単位 bp の帰無分布 → Holm 補正",
    prior_art="Moskowitz et al. (2012) は 1〜12m（約 20〜250 日）で広く効くことを示した。本件は TREND7・封印前への移植",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
