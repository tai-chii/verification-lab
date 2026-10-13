#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runner の見本（判定には使わない・QID は EXAMPLE）: 日足 15 銘柄の時系列モメンタム L=60/120 を段階1コストで。
検証スクリプトが書くのは Spec・strategy（・必要なら judge）だけ。流れは fe_core.Runner が持つ。
実行: python3 kensho_example_tsmom_runner.py --smoke --B 5 ／ python3 kensho_example_tsmom_runner.py --B 200
"""
import os
import sys

import numpy as np  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))  # 本番の検証フォルダ（financial-engineering/<実験>/）からは "..", "..", "tools"
from fe_core import Spec, Runner, tsmom_pos, SYMS  # noqa: E402

SPEC = Spec(
    qid="EXAMPLE",
    question="日足 15 銘柄の時系列モメンタム（L=60）はコスト後に前後半とも正か（Runner の見本）",
    hypothesis="pos[t]=sign(close[t]−close[t−L])。all15 の年単位平均 bp（段階1コスト後）が前後半とも >0",
    reject_if="全期間の z<1 → 棄却。前後半とも bp>0 かつ Holm 後 p<0.05 → 支持。ほか → 未確定",
    syms=list(SYMS), kind="D1_fromH1",
    params=[{"L": 60}, {"L": 120}], main_param=0, n_tests=2, warmup=120,
    B=200, null_kind="circ_shift", null_min_shift=120,
    discarded="0（見本）", delegation="見本のため無し",
)


def strategy(df, p, sym):
    """合図: t の終値で決めた ±1/0 をそのまま返す（shift しない。pnl_bp が 1 本ずらす）。"""
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    Runner(SPEC, strategy, here=HERE).execute()
