#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q304: 暗号資産 11 通貨日足の RSI2 押し目買いはコスト後に前後半とも正か（fe_core Runner 型）。事前登録の正本は SPEC。
種: ローカル LLM（qwen3:8b）のアイデア 2026-10-15「FX8のRSI2押し目買いが0.05%コストでSPYとの差が消える現象は、暗号通貨でも起きるか」を Opus が選別・設計。
実行: python3 kensho_crypto_rsi2_dip_q304.py（B=500）／ --smoke --B 5 ／ --readme ／ --idea-row
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, CRYPTO, rsi  # noqa: E402

SPEC = Spec(
    qid="Q304",
    question="暗号資産 11 通貨日足の RSI2 押し目買い（RSI2<10 かつ終値>SMA200 で買い・終値>SMA5 で手仕舞い）はコスト後に前後半とも正か",
    hypothesis="Connors 型: t の終値で RSI(2)<lo かつ close>SMA200 なら翌日から買い、保有中に close>SMA5 となった日の終値で手仕舞い（空売りなし）。"
               "11 通貨の年単位の日平均純損益 [bp]（往復 30bp）が前半（〜2021）・後半（2022〜）とも >0 で、合図の循環シフト帰無より高い",
    reject_if="既定の 3 分岐: main（lo=10）の前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05（循環シフト帰無の perm_p）→ 支持。"
              "全期間の z<1 → 棄却。それ以外 → 未確定",
    syms=list(CRYPTO), kind="H1→D1", cutoff_hour=0,
    params=[{"lo": 10}, {"lo": 5}, {"lo": 20}], main_param=0, n_tests=2, warmup=200, per_year=365,
    B=500, split_year=2022, null_kind="circ_shift", null_min_shift=60,
    discarded="約4: 手仕舞いを RSI2>70 にする版（Q271 型・掃引を増やさないため記述にも入れない）、SMA200 フィルタなし、高ボラ局面限定（Q271 の続きで別案）、H4 版",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2017-05〜2026-09（2026-07 以降は締め切り後）。規則は固定で相場観は使わない",
    delegation="設計とコードは Opus（2026-10-16）。実行と記録は Sonnet（怪しければ escalate）。結論ではなく JSON のパス・前後半の bp・z・p_holm を返させ、本体が確かめる",
    source="[[ブログQuanterLab2026-1_SP500のRSI2押し目買いの20日後の上昇はほとんどが市場全体の分]]、[[ブログQuanterLab2026-2_RSI2押し目買いは片道0.05パーセントのコストでSPYとの差が消えた]]、"
           "知見 Q271（US500・USTECH の RSI2 押し目買い）、知見「暗号資産の1時間足の逆張りの粗利は直前24本の実現ボラで前後半とも予測できるが…保守的なコストで赤字」。種: ローカル LLM アイデア 2026-10-15",
    data="暗号資産 11 通貨 H1_dukascopy → h1_to_d1（UTC 0 時区切り・週末込み）。前半（〜2021）は実質 6 通貨",
    measure="年単位の日平均純損益 bp（コスト 0 と往復 30bp）、年単位 t、束ねた t、Sharpe（365 日）、最大下落、露出。記述: lo=5/20",
    null_desc="通貨ごとに合図列を循環シフト（min_shift=60）B 回 → 束の年単位 bp の帰無分布 → z・perm_p・Holm（前後半 2 本）",
    prior_art="WebSearch 2026-10-16・standard・検索語 \"Connors RSI(2) mean reversion strategy cryptocurrency daily backtest bitcoin altcoins transaction costs\"。"
              "見つかったもの: ProRealCode の RSI-2 戦略、Substack の RSI2 バックテスト、TradingView の Connors RSI（いずれもブログ・株価指数中心）。"
              "未確認: 暗号資産の複数通貨で RSI2 押し目買いをコスト込み・前後半・合図の循環シフト帰無で測った研究は見当たらない（移植）。ブログは根拠にしない",
    batch="4案一括生成（ローカル LLM アイデアの選別 2026-10-16）", designer="Opus", coder="Claude（Opus）",
)


def strategy(df, p, sym):
    """t の終値で決めた 0/1 を返す（shift しない。pnl_bp が 1 本ずらす）。"""
    c = df["close"].values.astype(float)
    r2 = rsi(c, 2)
    s200 = pd.Series(c).rolling(200).mean().values
    s5 = pd.Series(c).rolling(5).mean().values
    pos = np.zeros(len(c)); hold = 0.0
    for t in range(len(c)):
        if hold == 0.0:
            if not (np.isnan(r2[t]) or np.isnan(s200[t])) and r2[t] < p["lo"] and c[t] > s200[t]:
                hold = 1.0
        else:
            if not np.isnan(s5[t]) and c[t] > s5[t]:
                hold = 0.0
        pos[t] = hold
    return pos


if __name__ == "__main__":
    if "--smoke" in sys.argv:  # 合成データは 2015〜2021-11 しか無いので、経路確認のときだけ分割年を 2019 にして後半の経路も通す（本番は 2022 のまま）
        SPEC.split_year = 2019
    Runner(SPEC, strategy, here=HERE).execute()
