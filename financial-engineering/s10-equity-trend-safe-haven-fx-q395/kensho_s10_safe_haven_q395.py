#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q395 S10: US500 の TSMOM60 符号が負の日は円・フランを買い（USDJPY/USDCHF/AUDJPY/NZDJPY/CADJPY 売り）正の日は逆、のリスクオフ・レジーム戦略は規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（封印・規程モードは _s1x_common/s1x.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s10_safe_haven_q395.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec, load_d1, tsmom_pos  # noqa: E402
import s1x as X  # noqa: E402

PAIRS = ["USDJPY", "USDCHF", "AUDJPY", "NZDJPY", "CADJPY"]   # 円・フランが quote。売り＝円・フラン買い
DRIVER = "US500"

SPEC = Spec(
    qid="Q395",
    question="US500 の TSMOM60 符号が負の日は円・フランを買い（USDJPY/USDCHF/AUDJPY/NZDJPY/CADJPY 売り）正の日は逆、のリスクオフ・レジーム戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="Ranaldo・Söderlind 2010: 株安局面で円・フランは対ドル・対資源国通貨で上がる（安全通貨）。この同時相関が株の順張り状態（US500 の 60 日リターン符号）を通じて翌日以降の為替に持ち越されるなら、他市場の価格（株価指数）を 1 つ足した合図が FX 単独の順張り（S07 FX22 ≈0）より関門に近づく。pos = −sign(US500 close[t] − close[t−L])（全 5 ペア共通）。main L=60、副 L=20",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main L=60）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副 L=20・銘柄別は記述。S10 の族内試行は Q394・Q395 の 2 本×2 設定＝4",
    syms=list(PAIRS), kind="D1_fromH1", start="2010-01-01",
    params=[{"L": 60}, {"L": 20}], main_param=0, n_tests=2, warmup=60, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（VIX を状態変数にする＝手元に無い／US500 の実現ボラ水準で切る＝ボラは S04b で扱い済み／対ドル 7 ペア全部に同じ合図＝安全通貨の論点から外れる）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S10（他市場の価格）／Ranaldo・Söderlind 2010 'Safe haven currencies' Review of Finance／Habib・Stracca 2012 JIE／危機アルファ Q207・Q224（順張りは株安局面で正）",
    data="USDJPY・USDCHF・AUDJPY・NZDJPY・CADJPY の D1_fromH1（2010-01〜・封印 time<2024-07-01。AUDJPY 等 3 本は _データ/raw/D1）。合図の元は US500 の D1_fromH1（同じ UTC 0 時区切り・time で合わせる・先読みなし）。コスト: USDJPY/USDCHF は COST_RT、クロス円 3 本は spread_<sym>.csv の中央値",
    measure="等金額: 5 ペアの年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出。規程モード: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（全設定）。extra: US500 合図が負の日だけ／正の日だけの bp（安全通貨買いの側が効いているか）",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「equity market trend predicts safe haven currency returns JPY CHF daily out-of-sample trading strategy risk-off regime」: 学術は Ranaldo・Söderlind（同時相関）の要約のみ、ほかは市場解説（BNY・Continuum・Saxo）。株の順張り状態を合図にした予測型の D1 戦略の判定は未確認。解説記事は根拠にしない",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 2 本目（S10・安全通貨）", designer="Fable", coder="Fable",
    settings={"seal": str(X.SEAL.date()), "driver": DRIVER, "s10_family_trials": "Q394・Q395 の 2 本×2 設定＝4"},
)
RUNNER = {"obj": None}
_DRV = {}


def _driver_sign(df, L):
    r = RUNNER["obj"]; smoke = bool(r and r.smoke)
    key = (L, smoke)
    if "df" not in _DRV:
        d = load_d1(DRIVER, smoke=smoke, rng=(r.rng if r else None))
        _DRV["df"] = d[d["time"] < X.SEAL].reset_index(drop=True)
    d = _DRV["df"]
    if key not in _DRV:
        _DRV[key] = pd.Series(tsmom_pos(d["close"].values, L), index=pd.to_datetime(d["time"]).values)
    return np.nan_to_num(_DRV[key].reindex(pd.to_datetime(df["time"]).values, method="ffill").values)


def strategy(df, p, sym):
    """合図: −sign(US500 の L 本リターン)。負（株安）→ ペア売り＝円・フラン買い。shift しない。"""
    return -_driver_sign(df, p["L"])


def make_extra(spec):
    def _extra(cells, sp):
        from fe_core import fmt
        m = cells[cells["param"] == sp.main_param].copy()
        out = {}
        for s in sorted(m["sym"].unique()):
            d = m[m["sym"] == s]
            out[s] = {"bp_net": fmt(float(np.nanmean(d["pnl_net"])))}
        return {"per_sym_main": out}
    return _extra


if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=4, extra_required=[DRIVER], summarize_extra=make_extra(SPEC), runner_holder=RUNNER)
