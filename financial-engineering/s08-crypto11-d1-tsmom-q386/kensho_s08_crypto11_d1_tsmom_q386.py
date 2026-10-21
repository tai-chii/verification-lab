#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q386 S08: 暗号資産 11 通貨の D1（H1→D1・週末込み）TSMOM L∈{60,120} は規程モード（暗号版）で封印前の前後半とも t≥2 かつ最大下落 −6% 以内か。
事前登録の正本は SPEC。Runner 型（封印と暗号版の規程モードは _s08_common/s08crypto.py）。BTC/ETH 対 他 9 通貨（alt9）の寄与は extra.subgroups に記述。
実行: --smoke --B 5（経路確認）／ python3 kensho_s08_crypto11_d1_tsmom_q386.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s08_common"))
from fe_core import Spec, tsmom_pos, CRYPTO, CRYPTO_COST_RT_REL  # noqa: E402
import s08crypto as S8  # noqa: E402

SYMS = list(CRYPTO)
ALT9 = [s for s in SYMS if s not in S8.CRYPTO2]
CACHE = {}

SPEC = Spec(
    qid="Q386",
    question="暗号資産 11 通貨の D1（H1→D1・UTC 0 時区切り・週末込み）TSMOM L∈{60,120} は規程モード（暗号版）で封印前の前半（〜2020）・後半（2021〜2024-06）とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="11 通貨の等リスク束（規程モード）でも関門（前後半 t≥2・max_dd≥−6%）を通らない（Q262 の前半 t<2 が規程モードでも残る）。通るなら BTC/ETH の寄与が alt9 より大きい。main=L60。L120 は副",
    reject_if="支持: 規程モード（暗号版・往復 30 bp・split 2021・封印前）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main L60・30 bp）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。実測スプレッド版・L120・alt9／crypto2 の部分群・銘柄別は記述（判定に使わない）。ADA/XLM/LNK は 2021-09〜、DOT/SOL は 2024-03〜で前半に無い（銘柄数が期間で変わる）ことを結果に明記する",
    syms=SYMS, kind="H1→D1", cutoff_hour=0,
    params=[{"L": 60}, {"L": 120}], main_param=0, n_tests=2, warmup=120, per_year=365,
    B=500, split_year=S8.CRYPTO_SPLIT, null_kind="circ_shift", null_min_shift=120,
    cost_rel={s: CRYPTO_COST_RT_REL for s in SYMS},
    discarded="2（L=20＝Q262 で既出・alt9 だけの別 ID＝台帳の 4 本固定に反するので部分群の記述に留める）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S08／Q262（11 通貨 TSMOM 20/60/120・前半 t<2 で「最初から無い」）／知見 [[暗号資産11通貨H1の24本TSMOMはコスト後も前も効き目がほとんどなくNeely2003-3の日中足トレンド消失が暗号でも成り立つ]]（Q290）／Liu・Tsyvinski・Wu 2022",
    data="CRYPTO 11 通貨の H1_dukascopy（BTC 2017-05・ETH 2017-12・XRP/BCH/EOS 2018-05・LTC 2018-09・XLM 2021-05・ADA/LNK 2021-09・DOT/SOL 2024-03〜）を h1_to_d1（UTC 0 時）で日足に。土日を含む。封印 time<2024-07-01（SealedRunner）。コスト main: 往復 30 bp（全銘柄）。副: 実測スプレッド（spread_<sym>.csv は BTC/ETH のみ・他 9 通貨は 30 bp のまま）",
    measure="等金額: 11 通貨の年単位平均 bp（コスト 0／30 bp／実測スプレッド）・年単位 t・束ねた t・Sharpe・最大下落。規程モード（暗号版・split 2021）: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（30 bp と実測スプレッド）。部分群 crypto2／alt9 の同じ統計（記述）",
    null_desc="合図の循環シフト（min_shift=120）B=500 → 等金額の年単位 bp の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「altcoin versus Bitcoin time-series momentum daily returns trend following altcoins empirical study」: Zarattini・Pagani・Barbon 2025「Catching Crypto Trends」（BTC の順張りを全通貨へ拡張・Donchian 束・ボラ規模）、Hong 2017（BTC の 1〜8 週の持続）。alt9 と BTC/ETH を同じ規程モードで分けて比べた日足の研究は未確認",
    batch="/lab-plan ターミナル版 2026-10-22・N=4 の 2 本目（S08・crypto11）", designer="Fable", coder="Fable",
    settings={"seal": str(S8.SEAL.date()), "rules_crypto": S8.RULES_CRYPTO, "subgroups": {"crypto2": S8.CRYPTO2, "alt9": ALT9},
              "note_runner_rule_mode": "Runner 自身の rule_mode は境 2017 固定のため t_pre が出ない。判定は extra.rule_mode_crypto（split 2021）",
              "diff_vs_Q262": "Q262 は境 2022・封印なし（〜2026-09）・規程モードなし・L∈{20,60,120}。本件は境 2021・封印 2024-07・規程モード gate・L∈{60,120}・部分群の記述。Q262 の前半 t=0.57（L60）と本件の前半を並べて書く"},
)


def strategy(df, p, sym):
    """合図: sign(close[t]−close[t−L])。shift しない。df を extra 用に貯める。"""
    CACHE[sym] = df
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    S8.SealedRunner(SPEC, strategy, judge=S8.judge_s08, summarize_extra=S8.make_extra(SPEC, CACHE, strategy, subgroups={"crypto2": S8.CRYPTO2, "alt9": ALT9}), here=HERE).execute()
