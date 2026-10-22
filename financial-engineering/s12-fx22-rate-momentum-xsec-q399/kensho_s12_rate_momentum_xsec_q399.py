#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q399 S12: FX22 D1 を金利差の 90 暦日変化で順位付け・上位 1/3 買い・下位 1/3 売り（横断金利モメンタム・スワップ込み）は規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（_s09_common/s09carry.py の CarryRunner を再利用。横断の順位は CarryRunner.loaded からパネルを組む＝Q392 と同じ型）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s12_rate_momentum_xsec_q399.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s09_common"))
from fe_core import Spec  # noqa: E402
import s09carry as S9  # noqa: E402

SPEC = Spec(
    qid="Q399",
    question="FX22 D1 を政策金利差の 90 暦日変化で順位付けし上位 1/3 買い・下位 1/3 売り（横断金利モメンタム・スワップ込み）は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="Q398（時系列の符号）は変化 0 のペアを持たず露出が低い。横断なら変化の相対的な大きさで 22 ペアを並べ、最も引き締めに向いた通貨を買い・最も緩和に向いた通貨を売るので、各日に必ず 2/3 の露出を持つ。各日、Δ90 = diff[t] − diff[t−90] で順位付けし上位 ceil(n/3) を +1、下位 ceil(n/3) を −1。main=1/3、副=1/2",
    reject_if="支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main frac 1/3・スワップ込み）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。Q398 との比較・frac 1/2・銘柄別は記述。S12 の族内試行は Q398・Q399 の 2 本×2 設定＝4",
    syms=list(S9.FX22), kind="D1_fromH1", start=S9.START,
    params=[{"frac": 1 / 3, "min_syms": 10, "days": 90}, {"frac": 0.5, "min_syms": 10, "days": 90}], main_param=0, n_tests=2, warmup=60, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="2（通貨レベル 8 通貨の順位をペアに写す＝一意でない／Δ の同順位（変化 0 が多数）を 0 にする＝順位 first で機械的に割る方が事前固定しやすい）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S12／Chung・Hong 2007 JAE／Lustig・Roussanov・Verdelhan 2011 RFS（横断ソートの型）／Q392（横断キャリー・未確定）・Q398（時系列版）",
    data="FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨）。Δ90 は t−1 と t−91 暦日の金利差の差。スワップ・マークアップ・コストは S09 と同じ",
    measure="等金額: 22 ペアの年単位 bp（スワップ込み net／抜き）・t・束ねた t・Sharpe・最大下落・露出（≈2/3）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（スワップ込み・no_swap）。分解",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（スワップ込み net）の帰無分布 → z・perm_p・Holm（m=2）。順位は政策変更のたびに入れ替わるので循環シフトで帰無が作れる（Q392 と違い符号反転は使わない）",
    prior_art="WebSearch 2026-10-22「cross-sectional currency portfolio sorted on change in policy rate differential \"interest rate momentum\" FX returns」: Nomura の調達通貨選択（金利差の変化を併用・報道のみ）、Antolin-Diaz ほか（米国の金利サプライズ感応度でソート）、水準ソートの講義資料。変化でソートした横断ポートフォリオの判定は未確認。報道は根拠にしない",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 6 本目（S12・横断）", designer="Fable", coder="Fable",
    settings={"seal": str(S9.SEAL.date()), "markup_annual": S9.MARKUP_ANNUAL, "rate_lag_days": S9.RATE_LAG_DAYS, "s12_family_trials": "Q398・Q399 の 2 本×2 設定＝4"},
)
RUNNER = {"obj": None}
_PANEL = {}


def _panel(frac, min_syms, days):
    key = (round(frac, 6), min_syms, days, tuple(sorted(RUNNER["obj"].loaded.keys())))
    if key in _PANEL:
        return _PANEL[key]
    smoke = "--smoke" in sys.argv[1:]
    cols = {}
    for s, d in RUNNER["obj"].loaded.items():
        d0 = S9.rate_diff(s, d["time"].values, lag_days=S9.RATE_LAG_DAYS + days, smoke=smoke)
        cols[s] = pd.Series(d["carry_diff"].values - d0, index=pd.to_datetime(d["time"]))
    delta = pd.DataFrame(cols).sort_index()

    def _row(r):
        v = r.dropna(); out = pd.Series(0.0, index=r.index); n = len(v)
        if n < min_syms:
            return out
        k = max(1, int(np.ceil(n * frac))); rk = v.rank(method="first")
        out.loc[v.index[rk > n - k]] = 1.0; out.loc[v.index[rk <= k]] = -1.0
        return out

    _PANEL[key] = delta.apply(_row, axis=1)
    return _PANEL[key]


def strategy(df, p, sym):
    """合図: 横断順位（Δ90 の上位 frac → +1・下位 frac → −1）。shift しない。"""
    panel = _panel(p["frac"], p["min_syms"], p["days"])
    if sym not in panel.columns:
        return np.zeros(len(df))
    return panel[sym].reindex(pd.to_datetime(df["time"]).values).fillna(0.0).values


if __name__ == "__main__":
    av = sys.argv[1:]
    if "--smoke" not in av and "--readme" not in av and "--idea-row" not in av:
        S9.data_guard(SPEC, HERE)
    RUNNER["obj"] = S9.CarryRunner(SPEC, strategy, judge=S9.judge_s09, null=None, summarize_extra=S9.make_extra(SPEC), here=HERE)
    RUNNER["obj"].execute()
