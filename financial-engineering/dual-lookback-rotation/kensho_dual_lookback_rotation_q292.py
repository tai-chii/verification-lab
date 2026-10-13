#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検証キュー Q292: 15 銘柄 D1 の二周期ローテーション規則（L=20 と L=120 同符号時のみ ±1）はコスト後に単独 TSMOM60 を上回るか（Korzan2026-1 の移植・Runner 型）
事前登録の正本は SPEC（docstring は要点のみ）。README は `python3 <script> --readme` で生成。
実行: --smoke --B 5（経路確認）／ --B 500（本番）
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, SYMS  # noqa: E402

SPEC = Spec(
    qid="Q292",
    question="15 銘柄 D1 の二周期ローテーション規則（L=20 と L=120 の TSMOM が同符号時のみ ±1）は、単独 TSMOM60 より all15 の年単位平均 bp（コスト後）が高いか（Korzan2026-1 の規則の移植）",
    hypothesis=("二周期ローテーション（params[1]）は単独 TSMOM60（params[0]）より all15 の年単位平均 bp が高く、前後半とも >0。"),
    reject_if=("支持: 二周期版が前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05、かつ単独より bp_net が高い。"
               "棄却: 全期間 z<1。ほか: 未確定。多重比較は main_param=1 の pre/post の 2 本（Holm で m=2）。"),
    syms=list(SYMS), kind="D1_fromH1",
    params=[{"mode": "tsmom60"}, {"mode": "dual20_120"}], main_param=1, n_tests=2, warmup=120, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="約4: (i) L=10 と L=200（Korzan の 2 周期は中短期と中長期）、(ii) 3 周期の多数決（Q217 の 3 指標一致と重複）、(iii) 月単位の判定（D1 と期間が噛み合わない）、(iv) 損失時休む規則（anti-equity-curve Q254 と重複）。",
    delegation="設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。",
    source=("[[Korzan2026-1_凍結した二周期ローテーション規則の取り置き3年検証は年率22.76パーセントシャープ1.43最大DD11.40でベンチマークを上回った]]。"
            "関連: 知見「15銘柄の日足で参照日数20_60_120_250の合図平均は前年までのプールで選んだ最良単一より標本外で前後半とも差のtとzが2未満」(Q253 系)。"),
    data="15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。",
    measure="all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。params[0]（単独 TSMOM60）と params[1]（二周期）を summary で並べる。",
    null_desc="合図の循環シフト（min_shift=120）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。",
    prior_art=("WebSearch 2026-10-14・英語・\"dual lookback rotation rule time-series momentum 20-day 120-day agreement signal\"。"
               "見つかったもの: Faber dual momentum (60/120 ROC rotation)、Moskowitz 2012 blended signals、Pomegra wiki。"
               "未確認: 15 銘柄パネル D1 で L=20 と L=120 の TSMOM 同符号フィルタを単独 TSMOM60 と比較し、循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。"),
    batch="10案一括生成（ターミナル版 2026-10-14）",
    designer="Claude Opus 4.7（自動運転）", coder="Claude Opus 4.7（自動運転）",
    settings={"L_short": 20, "L_long": 120, "L_single": 60},
)


def strategy(df, p, sym):
    """mode="tsmom60": 単独 TSMOM60。mode="dual20_120": TSMOM20 と TSMOM120 が同符号時のみ ±1、不一致は 0。"""
    close = df["close"].values
    if p["mode"] == "tsmom60":
        return tsmom_pos(close, 60)
    s_short = tsmom_pos(close, 20)
    s_long = tsmom_pos(close, 120)
    agree = (s_short == s_long) & (s_short != 0)
    return np.where(agree, s_short.astype(float), 0.0)


if __name__ == "__main__":
    Runner(SPEC, strategy, here=HERE).execute()
