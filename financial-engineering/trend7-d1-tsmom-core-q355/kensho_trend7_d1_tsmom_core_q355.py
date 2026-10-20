#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q355 — 戦略台帳 S01 の中央関門。TREND7 の D1 TSMOM 本体（L=60）が、
封印前（2012-02〜2024-06）の前後半とも年単位 t≥2 で純損益がコスト後に正か。
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
        return "支持: 封印前の前後半とも年単位 t≥2 かつ bp_net>0（S01 ゲート通過）"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: 全期間 t<1 または pre/post とも t<1"
    return "未確定: 前後半片方のみ t≥2 または全期間 t が 1〜2"


SPEC = Spec(
    qid="Q355",
    question="TREND7 の D1 TSMOM 本体（L=60）は、封印前の前後半とも年単位 t≥2 で純損益がコスト後に正か（S01 の中央関門）",
    hypothesis="pos[t]=sign(close[t]−close[t−60]) を TREND7 7 銘柄に等重みで適用。段階1コスト後の年単位平均 bp が pre（2012-16）・post（2017-24.5）とも t≥2 かつ正",
    reject_if="pre・post とも年単位 t≥2 かつ bp_net>0 → 支持（S01 ゲート通過）。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 60}], main_param=0, n_tests=2, warmup=60,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=120,
    discarded="多（S01 までに FX8・all15・短期足など多数の lookback・銘柄群が棄却）",
    delegation="なし（設計 Fable・実行 Sonnet 想定、Opus 見直し）",
    source="戦略台帳 S01（_基盤/戦略台帳.md）、知見 Q230（all15 の D1 TSMOM 前後半片方 t<2）・Q261（trend7 の H4 L=60 不支持）・Q292（trend7 の D1 二周期 支持）・Q207/Q224（危機アルファ正）",
    measure="trend7 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出、前後半の割れ方",
    null_desc="合図の循環シフト（min_shift=120）B=500 回 → trend7 の年単位 bp の帰無分布 → z・perm_p・Holm（pre/post の 2 本）",
    prior_art="Moskowitz, Ooi & Pedersen (2012) 'Time Series Momentum' JFE — 本体の原著（原案は 12m lookback）。本件は 60 日版の TREND7 への移植で、Hurst et al. (2017) の trend-following factor は同系統",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7（XAUUSD/XAGUSD/WTI/UKOIL/US500/USTECH/BTCUSD）D1_fromH1、2012-02-01〜2024-06-30（封印: 2024-07 以降は読まない）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。期間はすべて以前",
)


def strategy(df, p, sym):
    """合図: TSMOM(L=60)。±1/0（shift しない。pnl_bp がずらす）。"""
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
