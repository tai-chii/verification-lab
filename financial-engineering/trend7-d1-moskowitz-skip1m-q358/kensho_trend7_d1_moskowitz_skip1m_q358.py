#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q358 — Moskowitz 原著の 12m-1m（直近 1 か月を飛ばす）で TREND7 の D1 TSMOM が
封印前の前後半で年単位 t≥2 を取れるか。原著に忠実な設定の移植。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, TREND7  # noqa: E402

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
        return "支持: 12m-1m スキップは前後半とも年単位 t≥2 かつ bp_net>0"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: 全期間 t<1 または pre/post とも t<1"
    return "未確定"


SPEC = Spec(
    qid="Q358",
    question="Moskowitz 原著の 12m-1m（L=252、skip=21）TSMOM は、TREND7 D1 で封印前の前後半とも年単位 t≥2 で正か",
    hypothesis="pos[t]=sign(close[t−21]−close[t−252]) を TREND7 に等重みで適用。段階1コスト後の年単位 bp が pre/post とも t≥2 で正",
    reject_if="pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 252, "skip": 21}], main_param=0, n_tests=2, warmup=252,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=260,
    discarded="複数の skip 幅や、原著の月足頻度を飛ばした案（D1 で近似する）",
    delegation="なし",
    source="Moskowitz, Ooi & Pedersen (2012) JFE Table 2 — 12m-1m のクロスセクション平均が TSMOM の基準。戦略台帳 S01",
    measure="TREND7 の年単位 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出",
    null_desc="合図の循環シフト（min_shift=260）B=500 → 年単位 bp の帰無",
    prior_art="原著 Moskowitz et al. (2012) の 12m-1m 設定。Baltas & Kosowski (2013) も同じスキップで複数頻度に拡張",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    """pos[t]=sign(close[t-skip]-close[t-L])。shift しない（pnl_bp がずらす）。"""
    close = df["close"].values
    L, skip = int(p["L"]), int(p["skip"])
    n = len(close)
    s = np.zeros(n)
    if n > L:
        s[L:] = np.sign(close[L - skip:n - skip] - close[:n - L])
    return s


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
