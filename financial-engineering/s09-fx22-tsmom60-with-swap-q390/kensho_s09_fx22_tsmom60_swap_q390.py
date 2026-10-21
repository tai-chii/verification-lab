#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q390 S09: FX22 D1 の TSMOM60 にスワップ（政策金利差 − 年 0.75% マークアップ）を損益に含めると、S07 のスワップなし（棄却）より規程モードの関門に近づくか。
事前登録の正本は SPEC。Runner 型（金利差・スワップ・封印は _s09_common/s09carry.py。帰無は循環シフト）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s09_fx22_tsmom60_swap_q390.py（本番 B=500）／ --readme
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s09_common"))
from fe_core import Spec, tsmom_pos  # noqa: E402
import s09carry as S9  # noqa: E402

SPEC = Spec(
    qid="Q390",
    question="FX22 D1 の TSMOM60 にスワップ（政策金利差 − 年 0.75% マークアップ）を損益に含めると、S07 のスワップなし（棄却）より規程モードの封印前の前後半 t・最大下落が改善し関門を通るか",
    hypothesis="順張りの建玉は上昇中の通貨＝高金利側に傾きやすい（キャリーと順張りの条件付き相関）ので、同じ合図でもスワップを損益に入れると年単位 t が上がる。S07（Q367・スワップなし）で棄却された FX22 TSMOM60 が、データ源を 1 つ足しただけで関門に届くかを測る。main=L60。副=L120",
    reject_if="支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main L60・スワップ込み）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。あわせて rule_mode.swap.delta_t_pre_swap／delta_t_post_swap（スワップ込み − 抜きの t の差）を必ず書く: 差が前後半とも正なら「スワップはこの合図に加算的」と記述（判定には使わない）。L120・銘柄別は記述。S09 の族内試行は Q389〜Q392 の 4 本×2 設定＝8 本",
    syms=list(S9.FX22), kind="D1_fromH1", start=S9.START,
    params=[{"L": 60}, {"L": 120}], main_param=0, n_tests=2, warmup=120, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="2（L=250 を足す＝S07 Q370 で既出・σ60 ボラ正規化版＝規程モードが同じ規模調整をするので二重）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S09／S07 Q367〜Q371（FX22 を含む 48 銘柄 TSMOM・スワップなし・棄却）／Moskowitz・Ooi・Pedersen 2012 JFE（先物の超過収益＝キャリー込み）／Koijen ほか 2018 'Carry'",
    data="FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨・t−1 暦日の値）。スワップとマークアップ・コストは Q389 と同じ（_s09_common）",
    measure="等金額: 22 ペアの年単位 bp（スワップ込み net／スワップ抜き price_net の両方）・t・束ねた t・Sharpe・最大下落、分解（値動き／スワップ／マークアップ）。規程モード: スワップ込みと no_swap の t_all/t_pre/t_post・max_dd・stops と、その差 delta_t_*",
    null_desc="合図の循環シフト（min_shift=120・B=500。スワップも帰無の合図で計算）→ 等金額の年単位 bp（スワップ込み net）の帰無分布 → z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「time series momentum currencies interest rate differential carry included in returns trend following FX swap points」: Moskowitz ほか 2012 は先物の超過収益（キャリー込み）で TSMOM を測る。Menkhoff・Sarno・Schmeling・Schrimpf 2012 は横断モメンタムとキャリーは別物、Massey 論文はモメンタムとキャリーの収益は連動しないと報告。『スポットの TSMOM 合図にスワップを足すと関門の数字が上がるか』をペア 22・日次・封印つきで測った研究は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=4 の 2 本目（S09・TSMOM 単独＋スワップ）", designer="Fable", coder="Fable",
    settings={"seal": str(S9.SEAL.date()), "markup_annual": S9.MARKUP_ANNUAL, "rate_lag_days": S9.RATE_LAG_DAYS,
              "compare_to": "Q367（wide48 TSMOM60 σ60・スワップなし）の fx22 族別と、本件の no_swap を突き合わせる（コストの置き方は Q384 の実測スプレッドに揃う）",
              "s09_family_trials": "Q389〜Q392 の 4 本×2 設定＝8"},
)


def strategy(df, p, sym):
    """合図: sign(close[t]−close[t−L])。スワップは損益側（CarryRunner）で加わる。shift しない。"""
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    S9.main(SPEC, strategy, HERE)
