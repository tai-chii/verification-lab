#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q361 — TREND7 D1 TSMOM(L=60) の収益を long-only と short-only に分解し、
どちらが bp>0 の担い手かを封印前で確かめる（long-only で足りるなら本番の信用売り不要）。
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


def side_judge(res, spec):
    """main_param=long（index 0）の pre/post が t≥2 かつ bp>0 なら『支持（long だけで足りる）』。
    短のみ param の pre/post の値は summary から拾って参考記述する。"""
    m = res["main"]
    pre, post, allp = m.get("pre"), m.get("post"), m.get("all")
    for d, nm in [(pre, "pre"), (post, "post"), (allp, "all")]:
        if d is None or d.get("t_year") is None:
            return f"未確定: {nm} の統計が計算できない"
    if pre["bp_net"] > 0 and post["bp_net"] > 0 and pre["t_year"] >= 2 and post["t_year"] >= 2:
        return "支持: long-only で前後半とも年単位 t≥2 かつ bp_net>0（本番は buy だけで足りる方向）"
    if allp["t_year"] < 1 or (pre["t_year"] < 1 and post["t_year"] < 1):
        return "棄却: long-only は全期間 t<1 または pre/post とも t<1（short が担い手の可能性）"
    return "未確定"


SPEC = Spec(
    qid="Q361",
    question="TREND7 D1 TSMOM(L=60) を long-only と short-only に分けると、どちらが bp>0 を担うか（long-only で足りるか）",
    hypothesis="合図を long（+1 のみ、−はゼロ）／short（−1 のみ、+はゼロ）／both（Q355 と同じ）の 3 設定で比べる。main_param=long。Holm m=2 の判定対象は long の pre/post",
    reject_if="long が pre・post とも t≥2 かつ bp_net>0 → 支持（long-only で足りる）。long が全期間 t<1 もしくは pre/post とも t<1 → 棄却（short が担い手候補）。ほか → 未確定",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 60, "side": "long"}, {"L": 60, "side": "short"}, {"L": 60, "side": "both"}],
    main_param=0, n_tests=2, warmup=60,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=120,
    discarded="long/short の非対称な閾値（+1 と −1 で L を変える）",
    delegation="なし",
    source="戦略台帳 S01、知見 Q207/Q224（下落相場での危機アルファ=short の寄与）、Moskowitz et al. (2012) の long/short 分解",
    measure="3 設定（long/short/both）の年単位 bp・t、各期間の bp と Sharpe、露出の違い",
    null_desc="合図の循環シフト（min_shift=120）B=500 → long の年単位 bp の帰無",
    prior_art="Moskowitz et al. (2012) Table 3 は long/short の寄与を分解。株式では short が公表後に減衰する例が多い（Mclean & Pontiff 2016）",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    raw = tsmom_pos(df["close"].values, int(p["L"]))
    side = p.get("side", "both")
    if side == "long":
        return np.where(raw > 0, raw, 0.0)
    if side == "short":
        return np.where(raw < 0, raw, 0.0)
    return raw


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=side_judge, here=HERE).execute()
