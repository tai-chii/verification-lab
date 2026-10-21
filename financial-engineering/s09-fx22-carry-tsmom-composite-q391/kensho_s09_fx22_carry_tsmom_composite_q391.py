#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q391 S09: FX22 D1 でキャリー符号と TSMOM60 符号が一致したときだけ持つ合成（副: スワップ込み総収益指数の TSMOM60）は規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（金利差・スワップ・封印は _s09_common/s09carry.py。帰無は循環シフト）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s09_fx22_carry_tsmom_composite_q391.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s09_common"))
from fe_core import Spec, tsmom_pos  # noqa: E402
import s09carry as S9  # noqa: E402

SPEC = Spec(
    qid="Q391",
    question="FX22 D1 でキャリー符号と TSMOM60 符号が一致したときだけ持つ合成（副: スワップ込み総収益指数の TSMOM60）は、キャリー単独・TSMOM 単独より規程モードの封印前の前後半 t≥2 かつ最大下落 −6% 以内を通りやすいか",
    hypothesis="キャリーの弱点は高金利通貨の急落（暴落リスク）で、順張りの弱点はスワップを払う向きの建玉。両者の符号が一致するときだけ持てば、暴落局面（順張りが売りに転じる）でキャリーの買いを外し、順張りの売りがスワップを払う局面も外れる。合成の規程モードの t と max_dd は Q389・Q390 の main より良い。main=一致ゲート（agree）。副=総収益指数（close×Π(1+金利差·日数/365)）の TSMOM60（tr_mom・Moskowitz 流の超過収益モメンタム）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main agree・スワップ込み）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。Q389・Q390 との比較（t_pre/t_post/max_dd）は記述であり判定に使わない。tr_mom・銘柄別は記述。S09 の族内試行は Q389〜Q392 の 4 本×2 設定＝8 本",
    syms=list(S9.FX22), kind="D1_fromH1", start=S9.START,
    params=[{"mode": "agree", "L": 60}, {"mode": "tr_mom", "L": 60}], main_param=0, n_tests=2, warmup=120, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（z スコアの和（連続値）＝規模の学習は S04 の枠／不一致のときキャリー側に従う＝Q389 とほぼ同じ／L を 60・120 で掃引＝族内の本数を増やさない）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S09／Q389（キャリー単独）・Q390（TSMOM＋スワップ）／Koijen ほか 2018 'Carry'／Burnside・Eichenbaum・Rebelo 2011 NBER w16942（キャリーとモメンタムの組合せ）／Moskowitz・Ooi・Pedersen 2012（超過収益の TSMOM）",
    data="FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨・t−1 暦日の値）。スワップ・マークアップ・コストは Q389 と同じ（_s09_common）",
    measure="等金額: 22 ペアの年単位 bp（スワップ込み net／抜き）・t・束ねた t・Sharpe・最大下落・露出（一致ゲートは露出が下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（スワップ込み・no_swap）",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（スワップ込み net）の帰無分布 → z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「combining carry and momentum currency strategy agreement filter carry-adjusted momentum total return FX」: Menkhoff ほか 2012（横断モメンタムはキャリーと性質が別）、Alpha Architect の要約（キャリーの直近 3 か月が正のときモメンタムとの相関 0.356・負のとき −0.62）、Burnside ほか 2011（月次のキャリーとモメンタムのポートフォリオ）。符号一致ゲート・総収益指数の TSMOM をペア 22・日次・プロップ規程で測った研究は未確認。Alpha Architect はブログなので根拠にしない",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=4 の 3 本目（S09・合成）", designer="Fable", coder="Fable",
    settings={"seal": str(S9.SEAL.date()), "markup_annual": S9.MARKUP_ANNUAL, "rate_lag_days": S9.RATE_LAG_DAYS,
              "agree": "pos = sign(diff) if sign(diff)==sign(tsmom60) else 0", "tr_mom": "tsmom_pos(total_return_close, 60)",
              "s09_family_trials": "Q389〜Q392 の 4 本×2 設定＝8"},
)


def strategy(df, p, sym):
    """agree: キャリー符号と TSMOM(L) 符号が一致したときだけその向き。tr_mom: スワップ込み総収益指数の TSMOM(L)。shift しない。"""
    c = df["close"].values; d = np.nan_to_num(df["carry_diff"].values.astype(float))
    if p["mode"] == "agree":
        m = tsmom_pos(c, p["L"]); k = np.sign(d)
        return np.where(m == k, m, 0.0)
    if p["mode"] == "tr_mom":
        return tsmom_pos(S9.total_return_close(c, d, df["dt_prev_h"].values), p["L"])
    raise ValueError(p["mode"])


if __name__ == "__main__":
    S9.main(SPEC, strategy, HERE)
