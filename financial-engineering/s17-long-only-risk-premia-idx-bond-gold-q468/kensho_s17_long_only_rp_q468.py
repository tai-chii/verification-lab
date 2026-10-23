#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S17: 多資産ロングオンリー（株価指数 10＋債券 2＋金）の等リスク買い持ち＝リスクプレミアム族。
★C1（2026-10-23・taichi 決定）後の最初の S。関門は規程モード C1（σ 0.25%/日）＋保有コスト（年 4%）込み。
事前登録の正本は SPEC（docstring に重複して書かない）。実行は Sonnet、解釈は事後の判断（Opus）。
実行: --smoke --B 0（経路確認）／ --B 0（本番。帰無は none）／ --hold 0.07（感度・記述のみ）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, by_year_stats, fmt  # noqa: E402

# 銘柄（データの健全性だけで決めた・結果を見ていない。要対応 2026-10-23 / S13 の穴の記録）
IDX10 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "AUS200", "SUI20"]
#   除外: NLD25（2013〜17 に 5 区間の穴）・EUSTX50（2012-08 に 241 日）・HKG33（2013-06 に 154 日）
BOND2 = ["BUND", "UKGILT"]          # 除外: USTBOND（2018-12 に 354 日の穴）。債券は 2016-05／2017-12 開始＝前半はほぼ無い（記述に残す）
GOLD = ["XAUUSD"]
ALL13 = IDX10 + BOND2 + GOLD
HOLD = 0.04   # 保有コスト年率（買い持ちの CFD 金利＋マークアップの近似: 2012〜2024-06 の USD 政策金利平均 約 1.2%＋2.5%。感度 0.07 は記述）

SPEC = Spec(
    qid="Q468",
    question="S17 多資産ロングオンリー（株価指数 10＋債券 2＋金）の等リスク買い持ちは、保有コスト年 4% 込みで C1 関門（規程モード σ0.25%/日・封印前の前後半 t≥2・max_dd −6% 以内）を通るか",
    hypothesis=(
        "pos[t]=+1（常時買い持ち）。規模は規程モード（size_weights: σ60 で 1 銘柄 3σ=1.5% 上限・ポート σ 目標 0.25%/日・レバ 2・日次 −2.5% 停止）が決める。"
        "株式・債券・金のリスクプレミアムは正で、等リスク束は分散で下落が浅くなる（Harvey ほか 2018 のボラ目標、Boyd ほかの株・債券・金）。"
        "封印前（2012-02〜2024-06）の前後半（境 2017）とも規程モード年単位 t≥2、max_dd ≥ −6%"
    ),
    reject_if=(
        "判定は規程モード（rule_set=fintokei_c1・保有コスト 4% 込み）の main_param=0 のみ。"
        "gate.pass（t_pre≥2 かつ t_post≥2 かつ max_dd≥−6%）→ 支持。"
        "規程モード t_all<1 または max_dd<−10% → 棄却。ほか → 未確定。"
        "等金額（RULES_NONE）の数字・params 1〜2（指数のみ／指数＋金）・保有コスト 7% は記述で判定に使わない。"
        "帰無は none（常時買い持ちは循環シフトで変わらないため）。年単位 t が検定"
    ),
    syms=list(ALL13), kind="D1_fromH1",
    params=[{"set": "idx_bond_gold"}, {"set": "idx"}, {"set": "idx_gold"}],
    main_param=0, n_tests=2, warmup=60,
    B=0, null_kind="none", split_year=2017, start="2012-02-01", end="2024-07-01",
    settings={"rule_set": "fintokei_c1", "holding_cost_annual": {s: HOLD for s in ALL13},
              "family": "リスクプレミアム（買い持ち）", "family_trials": 3, "gate": "C1 σ0.25%/日・max_dd −6%・前後半 t≥2"},
    discarded=(
        "3（族内の試行は params の 3 本に固定・掃引しない）。捨てた案: 全 48 銘柄の買い持ち（FX・商品は無条件の正のプレミアムが無い）、"
        "NLD25/EUSTX50/HKG33/USTBOND を含める（穴が年 ±20〜165 bp を作る・S13 の記録）、2010 年開始（US500/USTECH の 2011-12 の穴を跨ぐ）"
    ),
    delegation="なし（Fable 設計 → Sonnet 実行 → Opus 見直し）。実行者は data_health の gaps と year_sym の 2012〜13 を見て穴の混入が無いことだけ点検する",
    source=(
        "[[検証/_基盤/戦略台帳]] S17（2026-10-23・★C1 後の最初の S・族は新規「リスクプレミアム」）／"
        "Harvey・Hoyle・Korgaonkar・Rattray・Sargaison・van Hemert 2018「The Impact of Volatility Targeting」(JPM)／"
        "Boyd ほか「Simple Dynamic Stock/Bond/Gold Portfolios」(Stanford)／Q416・Q428（C1 の通過確率）"
    ),
    data=(
        "13 銘柄 D1（検証/_データ/raw/D1 の IDX10＋BUND・UKGILT、XAUUSD は既存 15 銘柄）。2012-02-01〜2024-06-30（封印は Spec.end で切る・2026-10-23 実装）。"
        "債券 2 本は 2016-05／2017-12 開始なので前半はほぼ指数＋金だけ（記述に残す）"
    ),
    measure=(
        "規程モード C1 の年単位 t（all/pre/post）・mean_bp・σ・max_dd・worst_day・stops（判定）。"
        "等金額の年単位 bp・t・Sharpe（記述）。extra: 族別（idx/bond/gold）の年単位 bp と t、保有コスト 7% は --hold 0.07 で別 JSON"
    ),
    null_desc="none。常時 +1 の合図は循環シフトで不変なので帰無分布を作らない。検定は年単位 t（pre 5 年・post 7.5 年）",
    prior_art=(
        "WebSearch 2026-10-23「multi-asset long-only risk parity equity bond gold volatility targeting Sharpe ratio 2010-2024 evidence」: "
        "Harvey ほか 2018（ボラ目標は株式・クレジットでシャープを上げ、債券・商品では効果が小さい）、Boyd ほか（株・債券・金の単純な動的配分）。"
        "未確認: CFD の保有コスト込み・プロップの固定最大損失（−6%）の下での通過可否、および 2012〜2024-06 の前後半分割での再現。ブログ（Quantpedia 要約）は根拠にしない"
    ),
    batch="/lab-plan 2026-10-23（Fable・★C1 決定後・N=1）",
    designer="Fable", coder="Fable",
)

SETS = {"idx_bond_gold": set(ALL13), "idx": set(IDX10), "idx_gold": set(IDX10 + GOLD)}


def strategy(df, p, sym):
    """合図: 設定の集合に入る銘柄は常時 +1、入らなければ 0。shift しない（pnl_bp がずらす）。"""
    n = len(df)
    return np.ones(n) if sym in SETS[p["set"]] else np.zeros(n)


def judge(res, spec):
    """事前固定の 3 分岐（SPEC.reject_if と同じ文）。規程モード C1 の main_param のみ。"""
    rm = res.get("rule_mode") or {}
    f = rm.get("fintokei") or {}
    g = rm.get("gate") or {}
    if "error" in rm or not f:
        return "未確定: 規程モードが計算できない（" + str(rm.get("error", ""))[:80] + "）"
    if rm.get("rule_set") != "fintokei_c1":
        return "未確定: rule_set が fintokei_c1 でない（土台の版を確認）"
    if g.get("pass"):
        return "支持: 規程モード C1（σ0.25%・保有コスト 4%）で前後半 t≥2 かつ max_dd≥−6%"
    t_all = f.get("t_all"); dd = f.get("max_dd")
    if (t_all is not None and t_all == t_all and t_all < 1) or (dd is not None and dd == dd and dd < -0.10):
        return f"棄却: 規程モード t_all={fmt(t_all)}<1 または max_dd={fmt(dd)}<−10%"
    return f"未確定: 規程モード t_pre={fmt(f.get('t_pre'))} t_post={fmt(f.get('t_post'))} max_dd={fmt(dd)}（関門の一部のみ未達）"


def summarize_extra(cells, spec):
    """族別（idx/bond/gold）の年単位 bp・t（記述。判定に使わない）。"""
    out = {}
    sy = spec.split_year
    for fam, members in (("idx10", IDX10), ("bond2", BOND2), ("gold", GOLD)):
        for pi, _ in enumerate(spec.params):
            ci = cells[(cells["param"] == pi) & (cells["sym"].isin(members)) & (cells["exp"] > 0)]
            if ci.empty:
                continue
            for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, sy), "post": (sy, 9999)}.items():
                b = by_year_stats(ci, "pnl_net", y0=y0, y1=y1)
                out[f"p{pi}_{fam}_{pn}"] = {"n_years": b["n_years"], "n_syms": int(ci["sym"].nunique()), "bp_net": fmt(b["mean"]), "t_year": fmt(b["t"])}
    out["holding_cost_annual"] = float(spec.settings["holding_cost_annual"][ALL13[0]])
    return out


def _extra(ap):
    ap.add_argument("--hold", type=float, default=None, help="保有コスト年率の上書き（感度・記述のみ。既定 0.04）")


if __name__ == "__main__":
    if "--hold" in sys.argv:
        h = float(sys.argv[sys.argv.index("--hold") + 1])
        SPEC.settings["holding_cost_annual"] = {s: h for s in ALL13}
        SPEC.batch += f"（感度: 保有コスト {h:.2%}・判定に使わない）"
    Runner(SPEC, strategy, judge=judge, summarize_extra=summarize_extra, here=HERE).execute(extra_args=_extra)
