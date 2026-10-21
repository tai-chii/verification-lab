#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q378 S04c 本体: 48 銘柄プールの翌 5 日リターン予測（リッジ→GBM・格子 36・PBO）は規程モードで S07 本体とゼロをコスト後に上回るか。
事前登録の正本は SPEC。土台を直接使う型（fe_core.ml + risk、共通部 _s04_common/s04ml.py の direction_experiment）。
【出典】[[検証/_基盤/戦略台帳]] S04c／主張カード [[Bailey2017-1_期間内の最良が期間外で中央値より下になる割合でバックテストの過剰適合の確率を測れる]]／[[Arnott2019-1_試した数と選ばなかった設定を数えないと2シグマは基準にならない]]
【仮説】48 銘柄を 1 つのモデルで学習した翌 5 日リターンの予測（特徴量 mom/vol/range/dow・t まで）を規模に変換した規程モード損益が、同じ評価期間の S07 等リスク TSMOM60 とゼロをコスト後に上回る。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01 で panel を切る。年次ウォークフォワード（学習 4 年固定長・embargo 10≥k）。評価 2012〜2024-06。
【定義】格子 = 特徴量 {mom, mom+vol+range, all} × モデル {ridge α=1, ridge α=100, gbm d2 i200, gbm d3 i200} × 変換 {sign, clip, kelly} = 36 試行（TrialLog max 50）。main（事前固定）= (all, ridge α=1, clip)。
【測るもの】main の規程モード（前半 2012〜16・後半 2017〜24-06 の年単位 t・mean_bp・max_dd・worst_day・stops・Sharpe）、S07・ゼロの同じ鍵、IC（順位相関・年ごと・日次 nw_t）、36 試行の TrialLog、PBO（CSCV S=8）。
【帰無】ラベル並べ替え（学習窓の目的変数を年内で並べ替えて学習し直す）B=20 → main の規程モード mean_bp の帰無分布 → z・perm_p。
【判定（事前固定・変更禁止）】支持: main が前後半とも mean_bp で S07 本体を上回り（かつ >0）、t_pre≥2 かつ t_post≥2、max_dd≥−6%、perm_p<0.05、PBO<0.5。棄却: main が前後半のどちらかで S07 本体を上回らない、または帰無 z<1。ほか → 未確定。
【捨てた案の数】3（xsec 族を足す＝fe_core に無い、目的変数を σ60 で割る＝Q380 系に回す、ニューラルネット＝格子が膨らむ）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行。n_trials=36・pbo・B を JSON で確認）
【実装】python3 kensho_s04c_pooled_direction_q378.py（GBM 24 試行分 × 13 年で数十分）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec  # noqa: E402
import s04ml as M  # noqa: E402

FEATURE_SETS = ["mom", "mom+vol+range", "all"]
MODELS = [("ridge", 1.0), ("ridge", 100.0), ("gbm", {"max_depth": 2, "max_iter": 200}), ("gbm", {"max_depth": 3, "max_iter": 200})]
RULES = ["sign", "clip", "kelly"]
GRID = [{"fset": f, "model": m, "rule": r, "k": 5, "train_years": 4} for f in FEATURE_SETS for m in MODELS for r in RULES]
MAIN_IDX = FEATURE_SETS.index("all") * 12 + 0 * 3 + RULES.index("clip")

SPEC = Spec(
    qid="Q378",
    question="48 銘柄プールの翌 5 日リターン予測（リッジ→GBM・特徴量 3 組・変換 3 通り・格子 36・PBO）は規程モードの封印前の前後半で S07 本体とゼロをコスト後に上回り年単位 t≥2 か",
    hypothesis="48 銘柄プールの翌 5 日リターン予測（mom/vol/range/dow・t まで）を clip 変換した main=(all, ridge α=1, clip) の規程モード損益が、評価期間（2012〜2024-06）の前後半とも S07 等リスク TSMOM60 とゼロをコスト後に上回る",
    reject_if="支持: main が前後半とも mean_bp で S07 本体を上回り（かつ >0）、t_pre≥2 かつ t_post≥2、max_dd≥−6%、ラベル並べ替え perm_p<0.05、PBO<0.5。棄却: main が前後半のどちらかで S07 本体を上回らない、または帰無 z<1。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{k: (str(v) if k == "model" else v) for k, v in g.items()} for g in GRID], main_param=MAIN_IDX, n_tests=2, warmup=250, B=20, null_kind="none", start="2008-01-01",
    discarded="3（xsec 族・σ60 で割った目的・NN）", delegation="なし（Fable 設計 → Sonnet 実行。n_trials=36・pbo・B を JSON で確認）",
    source="[[検証/_基盤/戦略台帳]] S04c／[[Bailey2017-1_期間内の最良が期間外で中央値より下になる割合でバックテストの過剰適合の確率を測れる]]／[[Arnott2019-1_試した数と選ばなかった設定を数えないと2シグマは基準にならない]]",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="main の規程モード前後半の年単位 t・mean_bp・max_dd・worst_day・stops・Sharpe。S07・ゼロの同じ鍵。IC（年ごと・日次 nw_t）。36 試行の TrialLog・PBO",
    null_desc="ラベル並べ替え（学習窓の目的変数を年内で並べ替えて学習し直す）B=20 → main の規程モード mean_bp の帰無分布 → z・perm_p",
    prior_art="WebSearch 2026-10-22「pooled cross-asset machine learning return prediction futures ridge gradient boosting walk-forward trend following benchmark」: arXiv 2607.00475（16 先物のパラメトリック方策・AI は単純規則に勝つか）、Wang・Zhang 2024 JFM（22 商品・LightGBM 月次）。48 銘柄 D1 プール×リッジ→GBM×規程モード×TSMOM ベースラインの追試は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 5 本目（S04c 本体）", designer="Fable", coder="Fable",
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    out = M.direction_experiment(dfs, R, COST, GRID, MAIN_IDX, args, rng)
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), **out,
           "multiple_comparisons": f"判定は main 1 本（規程モード・前後半）。格子 {out['n_trials']} 試行は TrialLog と PBO で数える", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = M.judge_vs_s07(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run)
