#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runner の見本（判定には使わない・QID は EXAMPLE）。事前登録の内容は下の SPEC が正本（docstring に重複して書かない）。
実行: --smoke --B 5（経路確認）／ --B 200（本番）／ --readme（README.md を SPEC から生成）
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
    source="知見 Q136（TSMOM の基準）", measure="all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出",
    null_desc="合図の循環シフト（min_shift=120）B 回 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm",
    prior_art="見本のため省略", batch="fe_core Runner の見本（2026-10-13）",
)


def strategy(df, p, sym):
    """合図: t の終値で決めた ±1/0 をそのまま返す（shift しない。pnl_bp が 1 本ずらす）。"""
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    Runner(SPEC, strategy, here=HERE).execute()
