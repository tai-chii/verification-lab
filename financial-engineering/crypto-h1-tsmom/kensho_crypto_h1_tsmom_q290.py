#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検証キュー Q290: 暗号資産 11 通貨 H1 の 24 本 TSMOM はコスト後に残るか（Neely2003-3 の暗号 H1 移植・Runner 型）
事前登録の正本は SPEC（docstring は要点のみ）。README は `python3 <script> --readme` で生成。
実行: --smoke --B 5（経路確認）／ --B 500（本番）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, CRYPTO  # noqa: E402

SPEC = Spec(
    qid="Q290",
    question="暗号資産 11 通貨 H1 の 24 本 TSMOM（L=24）はコスト後に前後半とも正か（Neely2003-3 の暗号 H1 移植）",
    hypothesis="pos[t]=sign(close[t]−close[t−24])。CRYPTO 11 通貨の年単位平均 bp（段階1コスト・CRYPTO_COST_RT_REL=30bp）が前後半とも >0。",
    reject_if=("支持: 前後半とも bp_net>0 かつ Holm 補正後 p<0.05。棄却: 全期間 z<1。ほか: 未確定。"
               "多重比較は main_param=0 の pre/post の 2 本（Holm で m=2）。"),
    syms=list(CRYPTO), kind="H1_dukascopy",
    params=[{"L": 24}, {"L": 72}], main_param=0, n_tests=2, warmup=24, per_year=24 * 365,
    B=500, split_year=2022, null_kind="circ_shift", null_min_shift=72,
    discarded="約3: (i) L=12（半日・保有が短すぎてコストに負ける）、(ii) H4（Q262 の D1 と中間でメッセージが薄い）、(iii) BTC 単独。",
    delegation="設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。",
    source=("[[Neely2003-3_為替のトレンドは週次月次では強いが日中足にはない]]。関連: 知見「暗号資産11通貨の日足順張りは2022以降もコスト後に残るか」(Q262)・"
            "[[Farag2024-1_暗号資産の5分足の流動性供給の見返りはボラや暴落リスクで期間外でも予測できた]]。"),
    data="暗号資産 11 通貨（CRYPTO = BTCUSD・ETHUSD・XRPUSD・LTCUSD・ADAUSD・BCHUSD・XLMUSD・EOSUSD・LNKUSD・DOTUSD・SOLUSD）H1_dukascopy、2017〜2026-09。",
    measure="CRYPTO プール（全銘柄等加重）の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。",
    null_desc="合図の循環シフト（min_shift=72）B=500 → CRYPTO プールの年単位 bp の帰無分布 → z・perm_p・Holm。",
    prior_art=("WebSearch 2026-10-14・英語・\"cryptocurrency hourly time series momentum TSMOM 24-bar lookback empirical 11 pairs\"。"
               "見つかったもの: TSMOM in cryptocurrency markets (Zenodo 19671502, SSRN 4825389) ― 日次 TSMOM の pre/post ETF 期間比較、volume-weighted TSMOM。"
               "未確認: 11 通貨 H1 の L=24 TSMOM で、循環シフト帰無 B=500 と Holm 補正で判定する実証は未確認（移植）。"),
    batch="10案一括生成（ターミナル版 2026-10-14）",
    designer="Claude Opus 4.7（自動運転）", coder="Claude Opus 4.7（自動運転）",
    settings={"split_year_note": "暗号資産は 2017〜なので前後半を 2022 で分ける（Q262 と同じ）。"},
)


def strategy(df, p, sym):
    """合図: t の終値で決めた ±1/0 をそのまま返す（shift しない。pnl_bp が 1 本ずらす）。"""
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    Runner(SPEC, strategy, here=HERE).execute()
