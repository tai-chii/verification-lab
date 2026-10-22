#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q411 S14: 15 銘柄 H1→D1 の TSMOM60 を tick 出来高の増加（V20/V250 ≥ 1）の日だけ持つゲートは、ゲートなしより規程モードの前後半 t と最大下落を改善するか。
事前登録の正本は SPEC。Runner 型（封印・全設定の規程モードは _s1x_common/s1x.py、出来高は _s14_common/s14.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s14_volume_gate_q411.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s14_common"))
from fe_core import Spec, tsmom_pos, SYMS, fmt  # noqa: E402
import s14 as S14  # noqa: E402

SPEC = Spec(
    qid="Q411",
    question="15 銘柄 H1→D1 の TSMOM60 を tick 出来高の増加（V20/V250 ≥ 1）の日だけ持つゲートは、ゲートなしより規程モードの前後半 t と最大下落を改善するか",
    hypothesis="Blume・Easley・O'Hara 1994: 出来高は価格の合図の質（情報の精度）を伝える。Lee・Swaminathan 2000: 株式では出来高の多い銘柄のモメンタムが強く長く続く。OHLCV の V は主目的の入力なのに手元では 48 銘柄の体系的な検証が 1 本も無い（Q235 の出来高確認ブレイクは H1、CGW 型の反転は 15 銘柄で棄却）。参加が増えている（20 日平均出来高 ≥ 250 日平均）ときの順張りだけ持てば、順張りの負け（参加の薄い往来相場）を避けられる。合図は TSMOM60 で S01 と同じなので粗利の増加は見込まず、下落と t の改善が問い。出来高の無い区間（比が NaN）はゲートを掛けない（素の TSMOM60）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）でゲートあり（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ ゲートあり の max_dd がゲートなし（param 1）より浅く t_all も高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードのゲートありの t_all がゲートなし以下（ゲートが効かない）。ほか → 未確定。銘柄別・ゲート日の割合は記述。S14 の族内試行は Q411（2 設定）・Q412（2 設定）・Q413（前提 1 本）＝5",
    syms=list(SYMS), kind="H1→D1", cutoff_hour=0, start="2008-01-01",
    params=[{"L": 60, "gate": 1.0}, {"L": 60, "gate": None}], main_param=0, n_tests=2, warmup=250, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（出来高 z>0 のゲート＝比の方が水準の違いに頑健／比の閾値 0.8〜1.2 の掃引＝1.0 に固定／出来高の多い日だけ建て直す＝回転が増えてコストで死ぬ）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S14（出来高＝OHLCV の V。入力基準で明示的に可）／Blume・Easley・O'Hara 1994 'Market statistics and technical analysis: the role of volume' JF／Lee・Swaminathan 2000 'Price momentum and trading volume' JF／S01 Q355（trend7 TSMOM60 本体）",
    data="15 銘柄 all15 の H1_dukascopy を UTC 0 時区切りで日足に束ねる（h1_to_d1。volume＝H1 の tick 出来高の合計。FX8 2008〜・油/指数 2011-09〜・BTC 2017〜。封印 time<2024-07-01）。出来高の無い日（0）は欠測。コスト: Runner の既定（COST_RT）",
    measure="等金額: 15 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（ゲートで下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（ゲートあり・なしの両設定＝rule_mode.params）。extra: 銘柄ごとのゲート日の割合（比<1 の日）と出来高の無い日の割合",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「tick volume confirmation time series momentum trend following FX futures volume filter study」: 学術研究は見つからず（TradingView の指標説明のみ＝根拠にしない）。出来高を TSMOM の建玉ゲートにした判定は未確認。Lee・Swaminathan 2000 は株式横断・実出来高で、tick 出来高・時系列は条件の穴",
    batch="/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 1 本目（S14・出来高ゲート）", designer="Fable", coder="Fable",
    settings={"seal": str(S14.SEAL.date()), "ratio_short": 20, "ratio_long": 250, "s14_family_trials": "Q411（2）・Q412（2）・Q413（1）＝5"},
)
RUNNER = {"obj": None}
_R = {}


def _ratio(df, sym):
    key = (sym, len(df))
    if key not in _R:
        _R[key] = S14.volume_ratio(df["volume"].values, SPEC.settings["ratio_short"], SPEC.settings["ratio_long"])
    return _R[key]


def strategy(df, p, sym):
    """合図: TSMOM60。gate が None でなければ V20/V250 < gate の日は 0（比が NaN の日はゲートなし）。shift しない。"""
    pos = tsmom_pos(df["close"].values, p["L"]).astype(float)
    if p["gate"] is None:
        return pos
    r = _ratio(df, sym)
    return np.where(np.isnan(r) | (r >= p["gate"]), pos, 0.0)


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


def extra(cells, spec):
    r = RUNNER["obj"]; out = {"gated_frac": {}, "no_volume_frac": {}}
    if r is None:
        return out
    for s, df in r.loaded.items():
        rt = _ratio(df, s)
        out["gated_frac"][s] = fmt(float(np.mean(np.nan_to_num(rt, nan=9.9) < 1.0)))
        out["no_volume_frac"][s] = fmt(float(np.mean(df["volume"].values <= 0)))
    return out


if __name__ == "__main__":
    S14.run_main(SPEC, strategy, HERE, min_syms=12, judge=judge, summarize_extra=extra, runner_holder=RUNNER)
