#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q392 S09: FX22 D1 の横断キャリー（政策金利差で 22 ペアを順位付け・上位 1/3 買い・下位 1/3 売り・スワップ込み）は規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（金利差・スワップ・封印・符号反転帰無は _s09_common/s09carry.py）。
横断の順位は CarryRunner.loaded（Runner.run が全銘柄を読んでから strategy を呼ぶ）からパネルを組む（Q371 と同じ型・二重読みなし）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s09_fx22_carry_xsec_q392.py（本番 B=500）／ --readme
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
    qid="Q392",
    question="FX22 D1 の横断キャリー（政策金利差で 22 ペアを順位付け・上位 1/3 買い・下位 1/3 売り・スワップ込み）は時系列版（符号）より規程モードの封印前の前後半 t≥2 かつ最大下落 −6% 以内を通りやすいか",
    hypothesis="学術のキャリーは横断（金利順に並べて上位を買い下位を売る・Lustig ほか 2011）で、金利差が小さいペアを持たないぶん時系列版（Q389）よりスワップ／値動きの比が高い。各日、金利差（base − quote）で 22 ペアを順位付けし、上位 ceil(n/3) を +1、下位 ceil(n/3) を −1、残り 0。main=1/3。副=1/2（ほぼ時系列版と同じ・差の大きさの参照）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main frac 1/3・スワップ込み）の全期間 z≥2（銘柄ごとの符号反転帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。Q389 との比較は記述。frac 1/2・銘柄別は記述。S09 の族内試行は Q389〜Q392 の 4 本×2 設定＝8 本",
    syms=list(S9.FX22), kind="D1_fromH1", start=S9.START,
    params=[{"frac": 1 / 3, "min_syms": 10}, {"frac": 0.5, "min_syms": 10}], main_param=0, n_tests=2, warmup=60, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="2（通貨レベル（8 通貨を金利順に上位 3・下位 3）でペアに写す＝一意でない／週次・月次リバランス＝キャリー順位は日次でもほぼ動かないので差が出ない）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S09／Lustig・Roussanov・Verdelhan 2011 RFS（金利順ソートのキャリー・ポートフォリオ）／Jurek 2014 JFE（暴落ヘッジ後は 0 と区別できず）／Q389（時系列版）",
    data="FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨・t−1 暦日の値）。スワップ・マークアップ・コストは Q389 と同じ（_s09_common）。横断の順位は当日に金利差のあるペア n≥min_syms で組む",
    measure="等金額: 22 ペアの年単位 bp（スワップ込み net／抜き）・t・束ねた t・Sharpe・最大下落・露出（≈2/3）、分解（値動き／スワップ／マークアップ）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（スワップ込み・no_swap）",
    null_desc="銘柄ごとの符号反転（各ペアの pos に独立な ±1・B=500）→ 等金額の年単位 bp（スワップ込み net）の帰無分布 → z・perm_p・Holm（m=2）。順位は年単位で動かないため循環シフトは使わない（Q389 と同じ理由）",
    prior_art="WebSearch 2026-10-22「cross-sectional carry trade currency portfolios sorted on interest rate differential returns 2010-2024 decline after crisis」: NBER w13812（DB キャリー指数の 2008 の下落）、Jurek（1999〜2008・暴落ヘッジ後は 0）、Nottingham 論文（1990〜2020 五分位キャリー 年 3.8%・危機で −30%）、Nova 論文（2008 後の不採算の検証・結果は要旨に無し）。2010〜2024・ペア 22・日次・プロップ規程・封印つきの判定は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=4 の 4 本目（S09・横断版）", designer="Fable", coder="Fable",
    settings={"seal": str(S9.SEAL.date()), "markup_annual": S9.MARKUP_ANNUAL, "rate_lag_days": S9.RATE_LAG_DAYS,
              "null": "null_signflip（銘柄ごとの符号反転）。Spec.null_kind の circ_shift は使わない（null= で上書き）",
              "s09_family_trials": "Q389〜Q392 の 4 本×2 設定＝8"},
)

RUNNER = {"obj": None}
_PANEL = {}


def _panel(frac, min_syms):
    """全ペアの金利差パネル（行＝日・列＝ペア）→ 横断順位の pos パネル。CarryRunner.loaded から組む（キャッシュ）。"""
    key = (round(frac, 6), min_syms, tuple(sorted(RUNNER["obj"].loaded.keys())))
    if key in _PANEL:
        return _PANEL[key]
    diff = pd.DataFrame({s: pd.Series(d["carry_diff"].values, index=pd.to_datetime(d["time"])) for s, d in RUNNER["obj"].loaded.items()}).sort_index()

    def _row(r):
        v = r.dropna(); out = pd.Series(0.0, index=r.index); n = len(v)
        if n < min_syms:
            return out
        k = max(1, int(np.ceil(n * frac))); rk = v.rank(method="first")
        out.loc[v.index[rk > n - k]] = 1.0; out.loc[v.index[rk <= k]] = -1.0
        return out

    pos = diff.apply(_row, axis=1)
    _PANEL[key] = pos
    return pos


def strategy(df, p, sym):
    """合図: 横断順位（上位 frac → +1・下位 frac → −1）。当日の pos を当日の金利差（t−1 暦日の値）で決める。shift しない。"""
    panel = _panel(p["frac"], p["min_syms"])
    if sym not in panel.columns:
        return np.zeros(len(df))
    return panel[sym].reindex(pd.to_datetime(df["time"]).values).fillna(0.0).values


if __name__ == "__main__":
    av = sys.argv[1:]
    if "--smoke" not in av and "--readme" not in av and "--idea-row" not in av:
        S9.data_guard(SPEC, HERE)
    RUNNER["obj"] = S9.CarryRunner(SPEC, strategy, judge=S9.judge_s09, null=S9.null_signflip, summarize_extra=S9.make_extra(SPEC), here=HERE)
    RUNNER["obj"].execute()
