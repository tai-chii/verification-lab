#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q398 S12: FX22 D1 で政策金利差の 90 暦日変化の符号で持つ（金利モメンタム・スワップ込み）戦略は規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（金利差・スワップ・封印・判定は _s09_common/s09carry.py を再利用。データ源は S09 と同じ政策金利で、族が「水準（キャリー）」から「変化（モメンタム）」に変わる）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s12_rate_momentum_q398.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s09_common"))
from fe_core import Spec  # noqa: E402
import s09carry as S9  # noqa: E402

SPEC = Spec(
    qid="Q398",
    question="FX22 D1 で政策金利差（base − quote）の 90 暦日変化の符号で持つ（金利モメンタム・スワップ込み）戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="中央銀行の利上げ・利下げは連続する（政策サイクル）ので、金利差の「変化」は持続し、為替はその向きにゆっくり動く（Chung・Hong 2007 JAE: 金利差の履歴が為替の方向を予測）。S09 の水準（キャリー）は円の局面に寄ったが、変化の向きは通貨をまたいで入れ替わるので局面依存が薄い。pos = sign(diff[t] − diff[t−D])、変化 0 なら持たない。main D=90、副 D=180",
    reject_if="支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main D=90・スワップ込み）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。スワップ抜き（no_swap）・D=180・銘柄別は記述。S12 の族内試行は Q398・Q399 の 2 本×2 設定＝4",
    syms=list(S9.FX22), kind="D1_fromH1", start=S9.START,
    params=[{"days": 90}, {"days": 180}], main_param=0, n_tests=2, warmup=60, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（変更イベント後 20 日だけ持つ＝イベント型で別 ID／キャリー符号と変化の符号の一致＝S09 は閉じたので合成しない／3 か月金利の変化＝未取得）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S12（金利の変化＝S09 と同じデータ源・別の族）／Chung・Hong 2007 'Model-free evaluation of directional predictability in foreign exchange markets' JAE／Molodtsova・Papell 2009 JIE（テイラールール基礎）／S09 Q389（水準の符号は円の局面に依存）",
    data="FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨）。時刻 t の金利差は t−1 暦日、D 日前の値は t−1−D 暦日に実施中の値。スワップ・マークアップ（年 0.75%）・コストは S09 と同じ",
    measure="等金額: 22 ペアの年単位 bp（スワップ込み net／抜き）・t・束ねた t・Sharpe・最大下落・露出（変化 0 の期間は 0）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（スワップ込み・no_swap）。分解（値動き／スワップ／マークアップ）",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（スワップ込み net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「change in interest rate differential momentum predicts exchange rate returns monetary policy cycle currency strategy \"rate momentum\"」: Chung・Hong 2007（金利差の履歴に方向の予測力）、HHS 'Economic momentum and currency returns'（経済モメンタムがキャリーを包含）、BCB WP 630（金利差の弾力性はレジーム依存）。金利差の変化の符号をそのまま建玉にした日次・スワップ込み・規程つきの判定は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 5 本目（S12・金利モメンタム）", designer="Fable", coder="Fable",
    settings={"seal": str(S9.SEAL.date()), "markup_annual": S9.MARKUP_ANNUAL, "rate_lag_days": S9.RATE_LAG_DAYS, "s12_family_trials": "Q398・Q399 の 2 本×2 設定＝4"},
)


def strategy(df, p, sym):
    """合図: sign(diff[t] − diff[t−D 暦日])。変化なしは 0。shift しない。"""
    smoke = "--smoke" in sys.argv[1:]
    d = df["carry_diff"].values.astype(float)
    d0 = S9.rate_diff(sym, df["time"].values, lag_days=S9.RATE_LAG_DAYS + p["days"], smoke=smoke)
    return np.sign(np.nan_to_num(d - d0))


if __name__ == "__main__":
    S9.main(SPEC, strategy, HERE)
