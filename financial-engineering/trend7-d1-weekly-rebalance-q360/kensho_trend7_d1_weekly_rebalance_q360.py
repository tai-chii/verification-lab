#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q360 — TREND7 D1 TSMOM(L=60) を週次（月曜のみ）でリバランスし、
日次リバランスの Q355 とコスト・成績がどう違うか比べる。
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
        return "支持: 週次リバランスでも前後半とも年単位 t≥2 かつ bp_net>0"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: 週次リバランスでも全期間 t<1 または pre/post とも t<1"
    return "未確定"


SPEC = Spec(
    qid="Q360",
    question="TREND7 D1 TSMOM(L=60) を週次（月曜のみ）でリバランスしても、封印前の前後半で年単位 t≥2 を保つか（コスト低減の効果）",
    hypothesis="raw[t]=tsmom_pos(L=60) を日次に計算し、各 ISO 週の最初の足で raw をラッチして次の週まで固定。段階1コスト後の年単位 bp が pre/post とも t≥2 で正",
    reject_if="pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 60}], main_param=0, n_tests=2, warmup=70,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=120,
    discarded="月次リバランス（粗すぎて trend の変化に追従できない）、日中リバランス（コストで死ぬ）",
    delegation="なし",
    source="戦略台帳 S01、Moskowitz et al. (2012) は月次。日足で日次より粗いリバランスがコスト低減に効くかの検証",
    measure="週次リバランスの年単位 bp、露出・取引回数、Q355（日次）との bp 差とコスト差",
    null_desc="合図の循環シフト（min_shift=120）B=500 → 年単位 bp の帰無",
    prior_art="Baltas & Kosowski (2013) は週次・月次でも TSMOM が効くとした。本件は TREND7 日足で日次との差を見る",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    """週次リバランス: 各 ISO 週の最初の足で tsmom_pos をラッチして固定。"""
    close = df["close"].values
    raw = tsmom_pos(close, int(p["L"]))
    iso = df["time"].dt.isocalendar()
    week_key = iso["year"].values.astype(np.int64) * 100 + iso["week"].values.astype(np.int64)
    pos = np.zeros(len(df))
    cur_week = -1
    cur = 0.0
    for i in range(len(df)):
        if week_key[i] != cur_week:
            cur = float(raw[i])
            cur_week = int(week_key[i])
        pos[i] = cur
    return pos


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=s01_judge, here=HERE).execute()
