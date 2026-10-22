#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q414 S15: 対ドル 7 ペアの FOMC 日ドル売りを「米政策金利が直近 365 暦日に上がった」局面だけに限ると、独立標本の第 1 サイクル（2015-12〜2019-07）でも規程モードの t≥2 か（境 2020）。
事前登録の正本は SPEC。Runner 型（封印・全設定の規程モード・FOMC の暦は _s1x_common/s1x.py、利上げ局面は _s14_common/s14.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s15_fomc_dollar_hiking_q414.py（本番 B=500）／ --fomc-csv <path>（暦の差し替え）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s14_common"))
from fe_core import Spec, fmt  # noqa: E402
import s14 as S14  # noqa: E402
X = S14.X

SPEC = Spec(
    qid="Q414",
    question="対ドル 7 ペア（EURUSD・GBPUSD・AUDUSD・NZDUSD・USDJPY・USDCHF・USDCAD）の FOMC 定例発表日ドル売り（当日の足 1 本）を「米政策金利が直近 365 暦日に 1 回以上上がった」局面だけに限ると、Q403 で見えた後半（2022〜24）とは独立な第 1 サイクル（2015-12〜2019-07）でも規程モードの年単位 t≥2 か（前後半の境は 2020）",
    hypothesis="Q403/Q410（S13）の事後の観察: FOMC 日のドル売りの収益は 2022〜24 の利上げ局面 20 回に集中していた（前半 t 0.09・後半 2.98）。これは結果を見た後の条件なので、S13 は「再開するなら『利上げ局面』を事前に定義した別 ID で」として閉じた。本案はその別 ID。局面の定義は政策金利（ポイントインタイム・t−1 暦日まで）だけで事前に固定し、**判定の重心を 2022〜24 を見る前の独立標本（第 1 サイクル 2015-12-17〜2019-07-31 の約 29 会合）に置く**ため、前後半の境を 2020 にする。機構の候補: 利上げ局面では会合前にドル買いが積み上がり、発表で「織り込み済み・ハト派的な利上げ」として巻き戻される（2023-03・05 の市況解説が典型）。局面外の会合は 0（持たない）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2020）で局面限定（main）が前後半（第 1 サイクル／第 2 サイクル）とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0、または **前半（第 1 サイクル）の発表単位の平均 bp（extra.event_mean_bp_pre）が 0 以下**（2022〜24 にだけ効くなら局面の定義では説明できない）。ほか → 未確定。局面外の会合（param 1 との差）・発表単位の平均は記述。前半の局面内の会合は約 29 回・年 4 本（2016〜2019）なので年単位 t の検出力は低い（by_year_stats の「年数 5 未満は記述」に準ずる注意を書く）。S15 の族内試行は Q414（2）・Q415（2）＝4。S13 の 8 試行の続きとして数える",
    syms=list(X.USD7), kind="D1_fromH1", start="2010-01-01",
    params=[{"regime": "us_hike_365"}, {"regime": None}], main_param=0, n_tests=2, warmup=5, per_year=252,
    B=500, split_year=2020, null_kind="circ_shift", null_min_shift=60,
    discarded="3（局面の窓 180／365／730 日の掃引＝365 に固定（会合 8 回分）／「利上げ中」を FF 金利の 90 日変化>0 にする＝S12 の金利モメンタムと同じ族になるので避けた／前後半の境を 2017 のまま＝第 1 サイクルが分断されるので 2020 に）",
    delegation="なし（Fable 設計 → Sonnet 実行）。FOMC の暦は知識から記載（s1x.FOMC_DATES）。Q401・Q402 で 2010〜26 年は federalreserve.gov と照合済み・一致。--fomc-csv で差し替え可",
    source="[[検証/_基盤/戦略台帳]] 新 S15（利上げ局面の事前定義。S13 の閉じ方「再開するなら利上げ局面を事前に定義した別 ID で」に答える）／Q403・Q410（FOMC 日ドル売り: 後半のみ）／Mueller・Tahbaz-Salehi・Vedolin 2017 'Exchange rates and monetary policy uncertainty' JF／政策金利 `_データ/raw/rates/policy_USD.csv`（BIS）",
    data="対ドル 7 ペアの D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ FOMC 定例発表日（s1x.FOMC_DATES・知識から記載・照合済み）＋ 米政策金利（_データ/raw/rates/policy_USD.csv・実施日ベース・t−1 暦日まで）。局面＝直近 365 暦日に上げが 1 回以上。コスト: Runner の既定（COST_RT）",
    measure="等金額: 7 ペアの年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出。規程モード: t_all/t_pre/t_post（境 2020）・max_dd・worst_day・stops（局面限定・全会合の両設定＝rule_mode.params）。extra: 局面内の会合数（前半／後半）、発表単位の平均 bp と t（局面内・局面外・前半・後半）",
    null_desc="合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）。注意: Q403 で等金額 z は発表日の値動きの大きさを拾って過大になった。判定の主は規程モードの t と発表単位の平均",
    prior_art="WebSearch 2026-10-22「dollar depreciation on FOMC announcement days during Fed hiking cycle exchange rate reaction monetary tightening regime study」: 学術の事象研究は見つからず、市況解説（2022-06・2023-03・2023-05 の『ハト派的利上げでドル下落』）のみ＝根拠にしない。利上げ局面に限った FOMC 日のドルの平均反応と、独立なサイクルでの確認は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 4 本目（S15・FOMC 日ドル売り×利上げ局面）", designer="Fable", coder="Fable",
    settings={"seal": str(S14.SEAL.date()), "regime_window_days": 365, "rate_lag_days": 1, "cycle1": "2015-12-17〜2019-07-31（境 2020 の前半）", "cycle2": "2022-03-17〜封印（後半）", "s15_family_trials": "Q414（2）・Q415（2）＝4（S13 の 8 の続き）"},
)
RUNNER = {"obj": None}
_REG = {}


def _regime(df, sym):
    r = RUNNER["obj"]; smoke = bool(r and r.smoke)
    key = (sym, smoke, len(df))
    if key not in _REG:
        _REG[key] = S14.hike_within("USD", df["time"].values, SPEC.settings["regime_window_days"], SPEC.settings["rate_lag_days"], smoke=smoke, rng=(r.rng if r else None))
    return _REG[key]


def strategy(df, p, sym):
    """合図: FOMC 発表日の足 1 本をドル売り（USD がクォートなら +1、ベースなら −1）。regime が None でなければ局面外の会合は 0。shift しない。"""
    pos = X.hold_bars_pos(df, X.fomc_day_index(df), (0,)) * (1.0 if X.USD_IS_QUOTE[sym] else -1.0)
    if p["regime"] is None:
        return pos
    return np.where(_regime(df, sym), pos, 0.0)


def judge(res, spec):
    """3 分岐（事前固定）: s1x.judge_gate ＋「前半（第 1 サイクル）の発表単位の平均 bp が 0 以下なら棄却」。"""
    base = X.judge_gate(res, spec)
    ev = (res.get("extra") or {}).get("event_mean_bp", {}).get("regime_pre")
    if ev is not None and ev <= 0 and not base.startswith("棄却"):
        return "棄却: 第 1 サイクル（前半）の局面内の発表単位の平均 bp が 0 以下（2022〜24 だけの効果）"
    return base


def extra(cells, spec):
    """発表単位の平均 bp（net）: param 0（局面内）と param 1−0（局面外）、前半（<2020）／後半。"""
    out = {"n_events": {}, "event_mean_bp": {}, "event_t": {}}
    c = cells[cells["exp"] > 0].copy()
    for name, pi in (("regime", 0), ("all", 1)):
        d = c[c["param"] == pi]
        for pn, m in (("pre", d["year"] < spec.split_year), ("post", d["year"] >= spec.split_year), ("all", d["year"] > 0)):
            dd = d[m].groupby("time")["pnl_net"].mean()   # 発表日ごとに 7 ペア平均 → 1 標本
            out["n_events"][f"{name}_{pn}"] = int(len(dd))
            out["event_mean_bp"][f"{name}_{pn}"] = fmt(dd.mean()) if len(dd) else None
            out["event_t"][f"{name}_{pn}"] = fmt(dd.mean() / dd.std(ddof=1) * np.sqrt(len(dd))) if len(dd) > 2 and dd.std(ddof=1) > 0 else None
    r = RUNNER["obj"]
    if r is not None and r.loaded:
        s0, df0 = next(iter(r.loaded.items()))
        reg = _regime(df0, s0); yrs = df0["year"].values
        out["regime_days_by_year"] = {int(y): int(reg[yrs == y].sum()) for y in np.unique(yrs)}
    out["fomc_source"] = X.fomc_source()
    return out


if __name__ == "__main__":
    S14.run_main(SPEC, strategy, HERE, min_syms=7, judge=judge, summarize_extra=extra, runner_holder=RUNNER)
