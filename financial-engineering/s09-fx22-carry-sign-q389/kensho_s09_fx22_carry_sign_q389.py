#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q389 S09: FX22 D1 のキャリー単独（政策金利差の符号で高金利通貨を買う・スワップ込み）は規程モードで封印前の前後半とも t≥2 かつ最大下落 −6% 以内か。
事前登録の正本は SPEC。Runner 型（金利差・スワップ・封印・符号反転帰無は _s09_common/s09carry.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s09_fx22_carry_sign_q389.py（本番 B=500）／ --readme
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
    qid="Q389",
    question="FX22 D1 のキャリー単独（政策金利差の符号で高金利通貨を買う・スワップ＝金利差 − 年 0.75% マークアップを損益に含む）は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="OHLCV だけの D1 順張りは FX22 で粗利 ≈0（S07）。FX で最も頑健な要因キャリー（高金利通貨の買い持ち）は OHLCV から出ないので、政策金利差の符号 sign(i_base − i_quote) をそのまま建玉にすると、値動き＋スワップの総収益がコスト（スプレッド＋マークアップ）後に正で、規程モードの関門を通る。main=帯なし（band 0）。副=|金利差|≤0.5pp は持たない（band 0.5）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main band 0・スワップ込み）の全期間 z≥2（銘柄ごとの符号反転帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。スワップ抜き（no_swap）・band 0.5・銘柄別は記述（判定に使わない）。S09 の族内試行は Q389〜Q392 の 4 本×2 設定＝8 本と数える",
    syms=list(S9.FX22), kind="D1_fromH1", start=S9.START,
    params=[{"band": 0.0}, {"band": 0.5}], main_param=0, n_tests=2, warmup=60, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（3 か月金利・フォワードポイントを源にする＝未取得／通貨レベルで上位 3・下位 3 を組む＝ペアへの写像が一意でない／マークアップを 0.5〜1% で掃引＝固定して感度は事後に記述）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S09（入力基準の改定 2026-10-22・最初に足すデータ源＝キャリー）／Koijen・Moskowitz・Pedersen・Vrugt 2018 'Carry' JFE／Lustig・Roussanov・Verdelhan 2011 RFS／Burnside・Eichenbaum・Rebelo 2011（NBER w16942）／S07 Q367（FX22 スワップなし TSMOM 棄却）",
    data="FX22（8 通貨の 22 ペア）の D1_fromH1（2010-01〜・封印 time<2024-07-01）。政策金利: 検証/_データ/raw/rates/policy_<CCY>.csv（BIS WS_CBPOL・実施日ベース・8 通貨）。時刻 t の金利差は t−1 暦日に実施中の値。スワップ: held×金利差×暦日数/365（週末またぎ 3 日）、マークアップ年 0.75% は常に払う。コスト: FX8 は COST_RT（往復 2 pips）、14 クロスは spread_<sym>.csv の中央値（Runner の既定）",
    measure="等金額: 22 ペアの年単位平均 bp（gross＝値動き＋金利差／net＝−スプレッド−マークアップ）・年単位 t・束ねた t・Sharpe・最大下落、値動き／スワップ／マークアップの分解（extra.decomposition_main）。規程モード: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（スワップ込みと no_swap の両方）",
    null_desc="銘柄ごとの符号反転（各ペアの pos に独立な ±1・B=500。金利差の向きは総収益の向きを知らない、が帰無）→ 等金額の年単位 bp の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）。循環シフトは符号が年単位で動かないキャリーでは帰無が観測と一致しうるため使わない",
    prior_art="WebSearch 2026-10-22「currency carry trade sign of policy rate differential daily rebalancing G10 pairs transaction costs returns after 2010 out-of-sample」: Georges 2014 の G10 金利差戦略の再現（bsic.it・2011 以降に効かなくなった）、Jurek 2014（暴落リスクが超過収益の約 1/3）、NTU 論文（上位 3・下位 3 の G10 キャリーの標本外）、Reuters 2026-05（先進国キャリーは金融危機後に稼いでいないという Citi の談）。22 ペア・ペア単位の符号・日次・プロップ規程・封印つきの判定は未確認。ブログ（bsic）は根拠にしない",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=4 の 1 本目（S09・キャリー単独）", designer="Fable", coder="Fable",
    settings={"seal": str(S9.SEAL.date()), "markup_annual": S9.MARKUP_ANNUAL, "rate_lag_days": S9.RATE_LAG_DAYS, "rates_dir": "検証/_データ/raw/rates",
              "null": "null_signflip（銘柄ごとの符号反転）。Spec.null_kind の circ_shift は使わない（null= で上書き）",
              "note_cost": "FX8 は COST_RT の往復 2 pips（保守値）、14 クロスは実測スプレッド中央値。混在は Runner の既定（Q384 と同じ）。結果に銘柄別コストを書く",
              "s09_family_trials": "Q389〜Q392 の 4 本×2 設定＝8"},
)


def strategy(df, p, sym):
    """合図: sign(金利差)。|金利差| ≤ band なら 0。金利差は t−1 暦日時点の値（df['carry_diff']）。shift しない。"""
    d = np.nan_to_num(df["carry_diff"].values.astype(float))
    pos = np.sign(d)
    if p["band"] > 0:
        pos = np.where(np.abs(d) <= p["band"], 0.0, pos)
    return pos


if __name__ == "__main__":
    S9.main(SPEC, strategy, HERE, null=S9.null_signflip)
