#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検証キュー Q293: 15 銘柄 D1 のボリンジャー平均回帰（+2σ 売り・−2σ 買い、SMA20 戻りで決済）はコスト後に残るか（Coakley2016-2 の D1 移植・Runner 型）
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
    qid="Q293",
    question="15 銘柄 D1 のボリンジャー平均回帰（+2σ 売り・−2σ 買い、SMA20 戻りで決済）は all15 の年単位平均 bp（コスト後）が前後半とも正か（Coakley2016-2 の D1 移植）",
    hypothesis=("Bollinger(20, 2σ) の mean-reversion（終値が上バンドを超えたら −1、下バンドを割ったら +1、SMA20 戻りで 0）は、"
                "all15 の年単位平均 bp（コスト後）が前後半とも >0。"),
    reject_if=("支持: 前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05。棄却: 全期間 z<1。ほか: 未確定。多重比較は pre/post の 2 本（Holm で m=2）。"),
    syms=list(SYMS), kind="D1_fromH1",
    params=[{"n": 20, "k": 2.0}], main_param=0, n_tests=2, warmup=20, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=60,
    discarded="約4: (i) 窓 10 日・50 日（Coakley の既定 20 日に揃える）、(ii) 1.5σ・3σ（Coakley の 2σ に揃える）、(iii) 順張り版（Bollinger breakout は別仮説）、(iv) FX のみ（Coakley は FX22 通貨だが手元は 15 銘柄パネル）。",
    delegation="設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。",
    source=("[[Coakley2016-2_ボリンジャーとRSIのルールはFX22通貨で補正後も両期間に残った]]。"
            "関連: 知見「先進国通貨の日足テクニカルは2016年以降も補正後に有意なルールが0本」(Hsu 系)。"),
    data="15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。",
    measure="all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。",
    null_desc="合図の循環シフト（min_shift=60）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。",
    prior_art=("WebSearch 2026-10-14・英語・\"Bollinger Bands mean reversion daily FX 15 assets cross-section Holm correction\"。"
               "見つかったもの: 実務ブログの Bollinger mean reversion 解説（Interactive Brokers、Luxalgo など）。"
               "未確認: 15 銘柄 D1 でボリンジャー 20・2σ の mean-reversion を循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。"),
    batch="10案一括生成（ターミナル版 2026-10-14）",
    designer="Claude Opus 4.7（自動運転）", coder="Claude Opus 4.7（自動運転）",
    settings={"window": 20, "k_sigma": 2.0, "exit_rule": "close crosses SMA20 (state machine)"},
)


def strategy(df, p, sym):
    """mean-reversion: 終値が上バンドを超えたら pos=-1、下バンドを割ったら +1、SMA20 戻りで 0。state machine で保有を維持。"""
    close = df["close"].values
    n = p["n"]
    k = p["k"]
    s = pd.Series(close)
    ma = s.rolling(n, min_periods=n).mean().values
    sd = s.rolling(n, min_periods=n).std(ddof=1).values
    upper = ma + k * sd
    lower = ma - k * sd
    pos = np.zeros(len(close), dtype=float)
    state = 0.0
    for i in range(len(close)):
        if np.isnan(ma[i]) or np.isnan(sd[i]) or sd[i] == 0:
            state = 0.0
            pos[i] = 0.0
            continue
        if state == 0.0:
            if close[i] > upper[i]:
                state = -1.0
            elif close[i] < lower[i]:
                state = 1.0
        elif state == 1.0 and close[i] >= ma[i]:
            state = 0.0
        elif state == -1.0 and close[i] <= ma[i]:
            state = 0.0
        pos[i] = state
    return pos


if __name__ == "__main__":
    Runner(SPEC, strategy, here=HERE).execute()
