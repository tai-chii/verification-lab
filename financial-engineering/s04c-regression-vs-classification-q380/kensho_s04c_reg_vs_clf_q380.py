#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q380 S04c 前提: 翌 5 日リターン予測で、回帰目的（ret）と符号分類目的（sign）はどちらが IC・コスト後損益が高いか。
事前登録の正本は SPEC。土台を直接使う型（_s04_common/s04ml.py の direction_experiment）。
【出典】[[検証/_基盤/戦略台帳]] S04c／知見 [[同じ特徴量の木モデルでラベルを同日にすると精度は跳ね翌日では基準率に落ちる]]（Q307 系・向きの精度と損益は別）／arXiv 2607.09426（方向と大きさは別の予測対象）
【仮説】符号分類（p̂−0.5 をスコア）は回帰（予測リターンをスコア）より、小さい動きの雑音を追わない分だけ IC が高く規程モード損益も高い。逆なら「大きさの情報が規模に効く」。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。学習 4 年固定長・embargo 10。評価 2012〜2024-06。特徴量 all・変換 clip。
【定義】試行 4 本 = {ridge 回帰(ret), ridge 符号回帰(sign を線形確率で), gbm d3 回帰(ret), gbm d3 分類(sign・確率)}。main（事前固定）= ridge 回帰（Q378 と同じ）。比較の相手は ridge 符号回帰。
【測るもの】4 本の IC（予測スコアと実現 5 日リターンの順位相関・年ごと・日次 nw_t）、分類は AUC も、規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe）。回帰−分類の年ごと IC 差の年単位 t。
【帰無】main のラベル並べ替え B=20。比較は年ごと IC 差の年単位 t。
【判定（事前固定・変更禁止）】「分類が勝つ」: ridge の分類−回帰の年ごと IC 差が t≥2 かつ前後半とも分類の mean_bp>回帰。「回帰が勝つ」: 逆向きに同条件。どちらでもない → 未確定（差は無いと記述）。
【捨てた案の数】1（三値分類＝閾値が掃引になる）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04c_reg_vs_clf_q380.py。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, tstat, fmt  # noqa: E402
import s04ml as M  # noqa: E402

GRID = [{"fset": "all", "model": ("ridge", 1.0), "rule": "clip", "k": 5, "train_years": 4, "classify": False},
        {"fset": "all", "model": ("ridge", 1.0), "rule": "clip", "k": 5, "train_years": 4, "classify": True},
        {"fset": "all", "model": ("gbm", {"max_depth": 3, "max_iter": 200}), "rule": "clip", "k": 5, "train_years": 4, "classify": False},
        {"fset": "all", "model": ("gbm", {"max_depth": 3, "max_iter": 200}), "rule": "clip", "k": 5, "train_years": 4, "classify": True}]
MAIN_IDX = 0

SPEC = Spec(
    qid="Q380",
    question="翌 5 日リターン予測で回帰目的（ret）と符号分類目的（sign）はどちらが IC・コスト後損益が高いか（リッジ回帰・GBM 回帰・GBM 分類・リッジ符号回帰の 4 試行）",
    hypothesis="符号分類（p̂−0.5 をスコア）は回帰より雑音を追わない分だけ IC が高く規程モード損益も高い。逆なら大きさの情報が規模に効く",
    reject_if="分類が勝つ: ridge の分類−回帰の年ごと IC 差が年単位 t≥2 かつ前後半とも分類の mean_bp>回帰。回帰が勝つ: 逆向きに同条件。どちらでもない → 未確定（差は無いと記述）",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{k: (str(v) if k == "model" else v) for k, v in g.items()} for g in GRID], main_param=MAIN_IDX, n_tests=1, warmup=250, B=20, null_kind="none", start="2008-01-01",
    discarded="1（三値分類）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04c／知見 Q307 系（向きの精度と損益は別）／arXiv 2607.09426",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="4 本の IC（年・日次 nw_t）・分類の AUC・規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe）。ridge の分類−回帰の年ごと IC 差の年単位 t",
    null_desc="main（ridge 回帰）のラベル並べ替え B=20。比較は年ごと IC 差の年単位 t",
    prior_art="WebSearch 2026-10-22「classification versus regression return prediction machine learning trading direction sign profitability comparison」: arXiv 2607.09426（暗号先物・回帰と分類を別々に評価）、Adegboye ほか 2021 ESA（FX の方向転換）。同じ特徴量・同じ変換で両目的を損益まで比べた統制比較は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 7 本目（S04c 前提）", designer="Fable", coder="Fable",
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    out = M.direction_experiment(dfs, R, COST, GRID, MAIN_IDX, args, rng)
    names = list(out["trials_detail"]); reg, clf = out["trials_detail"][names[0]], out["trials_detail"][names[1]]
    yrs = [y for y in sorted(set(reg["ic"]["ic_years"]) & set(clf["ic"]["ic_years"])) if reg["ic"]["ic_years"][y] is not None and clf["ic"]["ic_years"][y] is not None]
    diff = np.array([clf["ic"]["ic_years"][y] - reg["ic"]["ic_years"][y] for y in yrs], float)
    bp = lambda d, h: d["fintokei"][f"mean_bp_{h}"]
    cmp = {"ic_diff_clf_minus_reg_years": {int(y): fmt(v) for y, v in zip(yrs, diff)}, "ic_diff_mean": fmt(diff.mean()) if len(diff) else None, "ic_diff_t_year": fmt(tstat(diff)) if len(diff) > 1 else None,
           "clf_beats_pre": (bp(clf, "pre") > bp(reg, "pre")) if bp(clf, "pre") is not None and bp(reg, "pre") is not None else None,
           "clf_beats_post": (bp(clf, "post") > bp(reg, "post")) if bp(clf, "post") is not None and bp(reg, "post") is not None else None}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), **out, "comparison_ridge_clf_vs_reg": cmp,
           "multiple_comparisons": "判定は ridge の分類−回帰 1 本（両向き）。GBM 2 本は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(cmp)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(c):
    if c["ic_diff_t_year"] is None or c["clf_beats_pre"] is None or c["clf_beats_post"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if c["ic_diff_t_year"] >= 2 and c["clf_beats_pre"] and c["clf_beats_post"]:
        return "支持（分類が勝つ）: 分類−回帰の IC 差 t≥2 かつ前後半とも損益で上回る"
    if c["ic_diff_t_year"] <= -2 and (not c["clf_beats_pre"]) and (not c["clf_beats_post"]):
        return "支持（回帰が勝つ）: 回帰−分類の IC 差 t≥2 かつ前後半とも損益で上回る"
    return "未確定: 差は無い（記述）"


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run)
