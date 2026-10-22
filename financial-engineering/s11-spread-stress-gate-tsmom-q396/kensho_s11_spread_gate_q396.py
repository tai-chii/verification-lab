#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q396 S11: 48 銘柄 D1 の TSMOM60 に実測スプレッドの z（250 日）>2 の日は休む流動性ゲートを足すと、ゲートなしより規程モードの最大下落が浅く前後半の t が高いか。
事前登録の正本は SPEC。Runner 型（封印・全設定の規程モード・スプレッドは _s1x_common/s1x.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s11_spread_gate_q396.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec, tsmom_pos  # noqa: E402
import s1x as X  # noqa: E402

SPEC = Spec(
    qid="Q396",
    question="48 銘柄 D1 の TSMOM60 に実測スプレッドの z（250 日）>2 の日は休む流動性ゲートを足すと、ゲートなし（S07 本体と同じ合図）より規程モードの最大下落が浅く前後半の t が高いか",
    hypothesis="Brunnermeier・Pedersen 2009: 資金流動性と市場流動性は危機で同時に枯れ、スプレッドの急拡大はその印。スプレッドは実運用で判断時点に見える定量データ（入力基準で明示的に可）で OHLCV に無い情報を持つ。スプレッド（往復・価格比）の当日値を直近 250 日の平均・標準偏差で z 化し、z>2 の日は建玉 0、ほかは TSMOM60。ゲートなし（param 1）との差が問い。合図は S07 本体と同じなので粗利は小さいが、下落（−95%）が流動性の枯れた日に集中しているなら max_dd と t が上がる",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）でゲートあり（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ ゲートあり の max_dd がゲートなし（param 1）より浅く t_all も高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードのゲートありの t_all がゲートなし以下（ゲートが効かない）。ほか → 未確定。銘柄別・ゲート日の割合は記述。S11 の族内試行は Q396（2 設定）・Q397（1 本）＝3",
    syms=list(X.WIDE48), kind="D1_fromH1", start="2010-01-01",
    params=[{"L": 60, "gate": 2.0}, {"L": 60, "gate": None}], main_param=0, n_tests=2, warmup=250, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（z の閾値を 1〜3 で掃引＝2 に固定／建玉を 1/(1+z) で連続に縮める＝規程モードは符号しか受けないので主設定にしない／5 日平均の z＝当日値の方が「今の枯れ」を見る）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S11（スプレッド＝入力基準で明示的に可のデータ源）／Brunnermeier・Pedersen 2009 'Market liquidity and funding liquidity' RFS／BIS WP 1229（スプレッドの歪度の上昇）／S07 Q367（48 銘柄 TSMOM60 本体: 規程モード max_dd −95%）",
    data="48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ _データ/raw/D1/spread_<sym>.csv（日次 bid/ask 終値から往復スプレッド／価格比）。スプレッドの無い銘柄は z=NaN でゲートが掛からない（extra に記録）。コスト: Runner の既定（COST_RT／スプレッド中央値／暗号 30 bp）",
    measure="等金額: 48 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（ゲートで下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（ゲートあり・なしの両設定＝rule_mode.params）。extra: 銘柄ごとのゲート日の割合、スプレッドの無い銘柄",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「bid-ask spread widening liquidity stress filter trend following exposure futures FX drawdown reduction study」: BIS WP 1229（流動性の脆弱性・スプレッド歪度と収益の侵食の模擬）、FEDS Notes 2020（3 月の Treasury・FX のスプレッド拡大）。スプレッド z を順張りの建玉ゲートにした判定は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 3 本目（S11・スプレッドゲート）", designer="Fable", coder="Fable",
    settings={"seal": str(X.SEAL.date()), "z_window": 250, "z_min_periods": 120, "s11_family_trials": "Q396（2 設定）・Q397（1 本）＝3"},
)
RUNNER = {"obj": None}
_Z = {}


def _z(df, sym):
    r = RUNNER["obj"]; smoke = bool(r and r.smoke)
    key = (sym, smoke, len(df))
    if key not in _Z:
        sp, src = X.spread_rel_daily(sym, df["time"].values, smoke=smoke, rng=(r.rng if r else None))
        _Z[key] = (X.rolling_z(sp, 250, 120), src)
    return _Z[key]


def strategy(df, p, sym):
    """合図: TSMOM60。gate が None でなければ スプレッド z>gate の日は 0。shift しない。"""
    pos = tsmom_pos(df["close"].values, p["L"]).astype(float)
    if p["gate"] is None:
        return pos
    z, _ = _z(df, sym)
    return np.where(np.nan_to_num(z, nan=0.0) > p["gate"], 0.0, pos)


def judge(res, spec):
    """3 分岐（事前固定）。支持: main が規程 gate 通過・max_dd と t_all がゲートなしより良い・等金額 z≥2。棄却: z<1 または main の t_all ≤ ゲートなし。ほか → 未確定。"""
    m = res.get("main", {}); rm = res.get("rule_mode", {}); f = rm.get("fintokei", {}); gate = rm.get("gate", {})
    z = (m.get("all") or {}).get("z"); params = rm.get("params") or []
    if z is None or f.get("t_all") is None or len(params) < 2:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    g0 = params[0]["fintokei"]; g1 = params[1]["fintokei"]
    if z < 1 or (g0["t_all"] is not None and g1["t_all"] is not None and g0["t_all"] <= g1["t_all"]):
        return "棄却: 等金額の全期間 z<1 または ゲートありの t_all がゲートなし以下"
    if gate.get("pass") and z >= 2 and g0["max_dd"] > g1["max_dd"] and g0["t_all"] > g1["t_all"]:
        return "支持: ゲートありが規程モードで前後半 t≥2・max_dd≥−6%、ゲートなしより max_dd 浅く t_all 高く、等金額 z≥2"
    return "未確定"


def make_extra(spec):
    def _extra(cells, sp):
        from fe_core import fmt
        r = RUNNER["obj"]; out = {"gated_frac": {}, "no_spread": []}
        if r is None:
            return out
        for s, df in r.loaded.items():
            z, src = _z(df, s)
            if src == "none":
                out["no_spread"].append(s)
            out["gated_frac"][s] = fmt(float(np.mean(np.nan_to_num(z, nan=0.0) > 2.0)))
        return out
    return _extra


if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=40, judge=judge, summarize_extra=make_extra(SPEC), runner_holder=RUNNER)
