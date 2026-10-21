#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q379 S04c 前提: 翌 5 日リターン予測で、48 銘柄プール学習は銘柄別学習より IC・コスト後損益が高いか。
事前登録の正本は SPEC。土台を直接使う型（_s04_common/s04ml.py の direction_experiment）。
【出典】[[検証/_基盤/戦略台帳]] S04c／Guijarro-Ordonez・Pelger・Zanotti 2023「Maximally Machine-Learnable Portfolios」（銘柄別回帰の限界・プールの利点）／arXiv 2607.00475（資産クラス間はほぼ無相関＝単一のプール規則は難しい）
【仮説】プール学習（48 銘柄 1 モデル）は銘柄別学習（銘柄ごとに同じ型）より、評価期間の IC が高く規程モード損益も高い（データが 48 倍になる利点が、銘柄間の構造の違いの害を上回る）。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。学習 4 年固定長・embargo 10。評価 2012〜2024-06。変換は clip に固定・特徴量は all。
【定義】試行 4 本 = {ridge α=1, gbm d3 i200} × {プール, 銘柄別}。main（事前固定）= ridge・プール（Q378 の main と同じ）。比較の相手は ridge・銘柄別。
【測るもの】4 本の IC（全体・年ごと・日次 nw_t）、規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe）。プール−銘柄別の年ごとの IC 差の t（年単位）。
【帰無】main のラベル並べ替え B=20（direction_experiment 共通）。比較はプール−銘柄別の年ごと IC 差の年単位 t。
【判定（事前固定・変更禁止）】支持（プールが勝つ）: ridge のプール−銘柄別の年ごと IC 差が年単位 t≥2 かつ 規程モードの mean_bp が前後半ともプール>銘柄別。
  棄却（プールは勝たない）: IC 差の t≤0、または前後半とも銘柄別>プール。ほか → 未確定。
【捨てた案の数】1（資産クラス別プール fx22/idx13/cmd8。4 群×2 で試行が倍になるので後に）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04c_pooled_vs_persym_q379.py。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, tstat, fmt  # noqa: E402
import s04ml as M  # noqa: E402

GRID = [{"fset": "all", "model": ("ridge", 1.0), "rule": "clip", "k": 5, "train_years": 4, "per_sym": False},
        {"fset": "all", "model": ("ridge", 1.0), "rule": "clip", "k": 5, "train_years": 4, "per_sym": True},
        {"fset": "all", "model": ("gbm", {"max_depth": 3, "max_iter": 200}), "rule": "clip", "k": 5, "train_years": 4, "per_sym": False},
        {"fset": "all", "model": ("gbm", {"max_depth": 3, "max_iter": 200}), "rule": "clip", "k": 5, "train_years": 4, "per_sym": True}]
MAIN_IDX = 0

SPEC = Spec(
    qid="Q379",
    question="翌 5 日リターン予測で 48 銘柄プール学習は銘柄別学習より IC・コスト後損益が高いか（リッジ・GBM × プール／銘柄別の 4 試行）",
    hypothesis="プール学習（48 銘柄 1 モデル）は銘柄別学習より評価期間の IC が高く、規程モード損益も高い",
    reject_if="支持（プールが勝つ）: ridge のプール−銘柄別の年ごと IC 差が年単位 t≥2 かつ規程モード mean_bp が前後半ともプール>銘柄別。棄却（プールは勝たない）: IC 差の t≤0、または前後半とも銘柄別>プール。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{k: (str(v) if k == "model" else v) for k, v in g.items()} for g in GRID], main_param=MAIN_IDX, n_tests=1, warmup=250, B=20, null_kind="none", start="2008-01-01",
    discarded="1（資産クラス別プール）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04c／Guijarro-Ordonez・Pelger・Zanotti 2023 Maximally Machine-Learnable Portfolios／arXiv 2607.00475",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="4 本の IC（全体・年・日次 nw_t）と規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe）。プール−銘柄別の年ごと IC 差の年単位 t",
    null_desc="main（ridge・プール）のラベル並べ替え B=20。比較はプール−銘柄別の年ごと IC 差の年単位 t",
    prior_art="WebSearch 2026-10-22「pooled versus asset-specific models return prediction panel machine learning futures currencies」: Guijarro-Ordonez ほか 2023（株でプールの利点）、arXiv 2607.00475（先物横断・クラス間無相関）。先物・為替 48 銘柄でプールと銘柄別を同じ特徴量で直接比べた研究は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 6 本目（S04c 前提）", designer="Fable", coder="Fable",
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    out = M.direction_experiment(dfs, R, COST, GRID, MAIN_IDX, args, rng)
    names = list(out["trials_detail"])
    pool, per = out["trials_detail"][names[0]], out["trials_detail"][names[1]]
    yrs = sorted(set(pool["ic"]["ic_years"]) & set(per["ic"]["ic_years"]))
    diff = np.array([pool["ic"]["ic_years"][y] - per["ic"]["ic_years"][y] for y in yrs if pool["ic"]["ic_years"][y] is not None and per["ic"]["ic_years"][y] is not None], float)
    cmp = {"ic_diff_years": {int(y): fmt(pool["ic"]["ic_years"][y] - per["ic"]["ic_years"][y]) for y in yrs}, "ic_diff_mean": fmt(diff.mean()) if len(diff) else None,
           "ic_diff_t_year": fmt(tstat(diff)) if len(diff) > 1 else None,
           "pool_beats_pre": (pool["fintokei"]["mean_bp_pre"] or -9) > (per["fintokei"]["mean_bp_pre"] or -9) if pool["fintokei"]["mean_bp_pre"] is not None and per["fintokei"]["mean_bp_pre"] is not None else None,
           "pool_beats_post": (pool["fintokei"]["mean_bp_post"] or -9) > (per["fintokei"]["mean_bp_post"] or -9) if pool["fintokei"]["mean_bp_post"] is not None and per["fintokei"]["mean_bp_post"] is not None else None}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), **out, "comparison_ridge_pool_vs_persym": cmp,
           "multiple_comparisons": "判定は ridge のプール−銘柄別 1 本（IC 差の年単位 t と前後半の mean_bp）。GBM 2 本は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(cmp)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(c):
    if c["ic_diff_t_year"] is None or c["pool_beats_pre"] is None or c["pool_beats_post"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if c["ic_diff_t_year"] <= 0 or (not c["pool_beats_pre"] and not c["pool_beats_post"]):
        return "棄却: プールは銘柄別に勝たない（IC 差 t≤0 か前後半とも損益で下回る）"
    if c["ic_diff_t_year"] >= 2 and c["pool_beats_pre"] and c["pool_beats_post"]:
        return "支持: プールが IC 差 t≥2 かつ前後半とも損益で銘柄別を上回る"
    return "未確定"


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run)
