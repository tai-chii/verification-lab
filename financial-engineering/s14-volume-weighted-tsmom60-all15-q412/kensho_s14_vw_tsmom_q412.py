#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q412 S14: 15 銘柄 H1→D1 の出来高加重 TSMOM60（Σ ret·v/v̄ の符号）は素の TSMOM60 より規程モードの前後半 t≥2・最大下落 −6% 以内に近づくか。
事前登録の正本は SPEC。Runner 型（封印・全設定の規程モードは _s1x_common/s1x.py、出来高は _s14_common/s14.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s14_vw_tsmom_q412.py（本番 B=500）／ --readme
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
    qid="Q412",
    question="15 銘柄 H1→D1 の出来高加重 TSMOM60（直近 60 日の Σ ret_i × v_i/v̄_250 の符号）は素の TSMOM60 より規程モードの前後半 t≥2・最大下落 −6% 以内に近づくか",
    hypothesis="Blume・Easley・O'Hara 1994 の読み替え: 出来高の多い日の値動きは情報を含み、少ない日の値動きはノイズ。素の TSMOM60 は全日を等重みで足す（close[t]−close[t−60]）が、出来高で重み付けすると「参加の多い日の向き」を合図にできる。株式の文献（Lee・Swaminathan 2000）は横断・銘柄単位の出来高で、時系列・日単位の重み付けは手元では未検証。Q411（ゲート）と違い露出は変えずに合図の向きだけ変えるので、改善が出れば合図の質の差になる",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）で出来高加重（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ 出来高加重の t_all が素の TSMOM60（param 1）より高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの出来高加重の t_all が素の TSMOM60 以下。ほか → 未確定。合図の一致率（extra）は記述。S14 の族内試行は Q411（2）・Q412（2）・Q413（1）＝5",
    syms=list(SYMS), kind="H1→D1", cutoff_hour=0, start="2008-01-01",
    params=[{"L": 60, "vw": True}, {"L": 60, "vw": False}], main_param=0, n_tests=2, warmup=250, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（重みを √v にする＝事前に 1 通りに固定／L を 20・120 でも掃引＝S01 で L 選択は効かなかった／VWAP との位置＝MA 位置型は S01 Q364 で差が無かった）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S14（出来高）／Blume・Easley・O'Hara 1994 JF／Lee・Swaminathan 2000 JF／Moskowitz・Ooi・Pedersen 2012 'Time series momentum' JFE（素の TSMOM）／Q411（ゲート版）",
    data="15 銘柄 all15 の H1_dukascopy を UTC 0 時区切りで日足に束ねる（h1_to_d1。volume＝tick 出来高の日次合計。封印 time<2024-07-01）。出来高の無い区間は重み 1（素の TSMOM と同じ）。コスト: Runner の既定（COST_RT）",
    measure="等金額: 15 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（両設定＝rule_mode.params）。extra: 銘柄ごとの出来高加重と素の合図の一致率・回転（符号変化の回数）の比",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「volume-weighted time series momentum futures currencies paper」: Moskowitz・Ooi・Pedersen 2012（出来高は合図に使っていない）、TradingView の出来高加重 TSI 指標（根拠にしない）。出来高で日次リターンを重み付けた TSMOM の判定は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 2 本目（S14・出来高加重 TSMOM）", designer="Fable", coder="Fable",
    settings={"seal": str(S14.SEAL.date()), "vw_norm": 250, "s14_family_trials": "Q411（2）・Q412（2）・Q413（1）＝5"},
)
RUNNER = {"obj": None}


def strategy(df, p, sym):
    """合図: vw なら出来高加重 TSMOM60、そうでなければ素の TSMOM60。shift しない。"""
    if p["vw"]:
        return S14.vw_tsmom_pos(df["close"].values, df["volume"].values, p["L"], SPEC.settings["vw_norm"])
    return tsmom_pos(df["close"].values, p["L"]).astype(float)


def judge(res, spec):
    """3 分岐（事前固定）。支持: main が規程 gate 通過・t_all が素の TSMOM より高い・等金額 z≥2。棄却: z<1 または main の t_all ≤ 素の TSMOM。ほか → 未確定。"""
    m = res.get("main", {}); rm = res.get("rule_mode", {}); f = rm.get("fintokei", {}); gate = rm.get("gate", {})
    z = (m.get("all") or {}).get("z"); params = rm.get("params") or []
    if z is None or f.get("t_all") is None or len(params) < 2:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    g0 = params[0]["fintokei"]; g1 = params[1]["fintokei"]
    if z < 1 or (g0["t_all"] is not None and g1["t_all"] is not None and g0["t_all"] <= g1["t_all"]):
        return "棄却: 等金額の全期間 z<1 または 出来高加重の t_all が素の TSMOM60 以下"
    if gate.get("pass") and z >= 2 and g0["t_all"] > g1["t_all"]:
        return "支持: 出来高加重が規程モードで前後半 t≥2・max_dd≥−6%、素の TSMOM60 より t_all 高く、等金額 z≥2"
    return "未確定"


def extra(cells, spec):
    r = RUNNER["obj"]; out = {"agreement": {}, "turnover_ratio_vw_over_plain": {}}
    if r is None:
        return out
    for s, df in r.loaded.items():
        a = strategy(df, spec.params[0], s); b = strategy(df, spec.params[1], s)
        m = (a != 0) & (b != 0)
        out["agreement"][s] = fmt(float(np.mean(a[m] == b[m]))) if m.any() else None
        ta = float(np.abs(np.diff(a)).sum()); tb = float(np.abs(np.diff(b)).sum())
        out["turnover_ratio_vw_over_plain"][s] = fmt(ta / tb) if tb > 0 else None
    return out


if __name__ == "__main__":
    S14.run_main(SPEC, strategy, HERE, min_syms=12, judge=judge, summarize_extra=extra, runner_holder=RUNNER)
