#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検証キュー Q296: 15 銘柄 D1 の月曜ギャップ逆張り（金→月のギャップと逆方向に月曜のみ ±1）はコスト後に残るか（Dao2016-2 の 15 銘柄移植・Runner 型）
事前登録の正本は SPEC（docstring は要点のみ）。README は `python3 <script> --readme` で生成。
実行: --smoke --B 5（経路確認）／ --B 500（本番）
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, SYMS  # noqa: E402

SPEC = Spec(
    qid="Q296",
    question="15 銘柄 D1 の月曜ギャップ逆張り（金曜終値→月曜始値のギャップと逆方向に月曜のみ ±1、火曜以降 0）は all15 の年単位平均 bp（コスト後）が前後半とも正か（Dao2016-2 の 15 銘柄移植）",
    hypothesis=("金→月のギャップ（gap = open_mon − close_fri）が正なら月曜に −1、負なら +1、ギャップがなければ 0。"
                "月曜のみ保有し、火曜に 0 に戻す。all15 の年単位平均 bp（コスト後）が前後半とも >0。"),
    reject_if=("支持: 前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05。棄却: 全期間 z<1。ほか: 未確定。多重比較は pre/post の 2 本（Holm で m=2）。"),
    syms=list(SYMS), kind="D1_fromH1",
    params=[{"mode": "gap_reversal"}], main_param=0, n_tests=2, warmup=5, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=20,
    discarded="約4: (i) 木→金のギャップ（週末要因が入らない）、(ii) 順張り版（月曜ギャップは逆張りが Dao の主）、(iii) 保有を 1 週間に延長（別仮説）、(iv) FX のみ（Dao は 15 市場だが手元 15 銘柄パネルで統一）。",
    delegation="設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。",
    source=("[[Dao2016-2_週末ギャップは月曜に逆張りで利益が出る]]。"
            "関連: 知見「FX8の日足で月曜のモメンタムは火〜金より弱く符号が反転する傾向」(Q180 系)。"),
    data="15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。",
    measure="all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。",
    null_desc="合図の循環シフト（min_shift=20）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。",
    prior_art=("WebSearch 2026-10-14・英語・\"weekend gap reversal Monday open close Friday mean reversion 15 markets daily cross-section\"。"
               "見つかったもの: Dao の月曜効果、Chen 2016 Monday return reversal、Lakonishok-Smidt 1988 day-of-week。"
               "未確認: 15 銘柄 D1 で金→月のギャップ逆張り（月曜のみ保有）を循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。"),
    batch="10案一括生成（ターミナル版 2026-10-14）",
    designer="Claude Opus 4.7（自動運転）", coder="Claude Opus 4.7（自動運転）",
    settings={"hold_days": 1, "entry_dow": "monday", "signal_source": "gap = open_mon - close_fri"},
)


def strategy(df, p, sym):
    """月曜（dow=0）の始値 vs 金曜終値のギャップ逆張り。dow は time から計算。保有は 1 日だけ。"""
    close = df["close"].values
    open_ = df["open"].values
    time = pd.to_datetime(df["time"])
    dow = time.dt.dayofweek.values  # 月=0
    pos = np.zeros(len(close), dtype=float)
    # t の pos は t の終値で決める。pnl_bp が ret[t+1] に当てる。
    # 月曜 t の open と直近の非月曜 t-k の close の差（通常は金曜）でギャップを測り、t の pos を決める。
    for t in range(1, len(close)):
        if dow[t] != 0:
            continue
        # t-1 が直近の営業日（金曜であることが多いが祝日ならその前）
        gap = open_[t] - close[t - 1]
        if gap > 0:
            pos[t] = -1.0
        elif gap < 0:
            pos[t] = +1.0
        # pos[t]=±1 のまま。pnl_bp が ret[t+1]（= 月曜→火曜）に当てる。火曜のタイミングで pos[t+1]=0 なので |diff|=1 のコストが入り、翌日 pos=0 で保有は終わる
    return pos


if __name__ == "__main__":
    Runner(SPEC, strategy, here=HERE).execute()
