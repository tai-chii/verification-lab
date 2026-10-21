#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q383 S04 前提: 翌 k 日（k∈{1,5,20}）リターンのリッジ予測は地平線で IC・コスト後損益が変わるか（S04a/c の k=5 の妥当性）。
事前登録の正本は SPEC。土台を直接使う型（_s04_common/s04ml.py の direction_experiment）。
【出典】[[検証/_基盤/戦略台帳]] S04／知見 [[過去リターンとMA乖離と実現ボラだけを入力にした木モデルの12時間先予測は…信号がない]]（短い地平線は信号なし）／Moskowitz・Ooi・Pedersen 2012（12 か月までの持続）
【仮説】k=1 は信号がなく（IC≈0）、k=5・20 は IC が正で、コスト後損益は k=20 が最も高い（回転が少ない）。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。学習 4 年固定長・embargo=max(10,k)。評価 2012〜2024-06。特徴量 all・ridge α=1・clip。
【定義】試行 3 本 = k∈{1, 5, 20}。main（事前固定）= k=5（Q378 と同じ）。日次 IC の nw_t の lag は k。
【測るもの】3 本の IC（年ごと・日次 nw_t lag=k）、規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe・gross_median）。
【帰無】main のラベル並べ替え B=20。各 k の IC の年単位 t。
【判定（事前固定・変更禁止）】支持（k=5 でよい）: k=5 の IC 年単位 t≥2 かつ k=5 の規程モード mean_bp が 3 本の中で最大か 2 位。棄却（k=5 は不適）: k=5 の IC 年単位 t<1、または k=5 の mean_bp が 3 本で最小かつ最大との差が 1bp 超。ほか → 未確定。
【捨てた案の数】1（k=10・60 を足す＝試行を増やさない）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04_target_horizon_q383.py（リッジだけ・数分）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec  # noqa: E402
import s04ml as M  # noqa: E402

KS = [1, 5, 20]
GRID = [{"fset": "all", "model": ("ridge", 1.0), "rule": "clip", "k": k, "train_years": 4, "embargo": max(10, k)} for k in KS]
MAIN_IDX = KS.index(5)

SPEC = Spec(
    qid="Q383",
    question="翌 k 日（k∈{1,5,20}）リターンのリッジ予測は地平線で IC・コスト後損益が変わるか（embargo=k・3 試行・S04a/c の k=5 の妥当性）",
    hypothesis="k=1 は IC≈0、k=5・20 は IC>0、コスト後損益は k=20 が最も高い。k=5 は IC 年単位 t≥2 で損益も上位",
    reject_if="支持（k=5 でよい）: k=5 の IC 年単位 t≥2 かつ k=5 の規程モード mean_bp が 3 本中 1〜2 位。棄却（k=5 は不適）: k=5 の IC 年単位 t<1、または k=5 の mean_bp が 3 本で最小かつ最大との差が 1bp 超。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{k: (str(v) if k == "model" else v) for k, v in g.items()} for g in GRID], main_param=MAIN_IDX, n_tests=1, warmup=250, B=20, null_kind="none", start="2008-01-01",
    discarded="1（k=10・60）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04／知見 Q135 系（短い地平線は信号なし）／Moskowitz・Ooi・Pedersen 2012",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="3 本の IC（年ごと・日次 nw_t lag=k）と規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe・gross_median）",
    null_desc="main（k=5）のラベル並べ替え B=20。各 k の IC の年単位 t",
    prior_art="WebSearch 2026-10-22「forecast horizon 1-day 5-day 20-day return predictability machine learning cross-asset futures information coefficient」: 5 日 IC を使った LLM 特徴の研究（arXiv 2604.10996）、VIX 先物の翌日予測（PLOS One 2024）。多資産 D1 で 1/5/20 日の地平線を同じ特徴量で比べた研究は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 10 本目（S04 前提）", designer="Fable", coder="Fable",
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    out = M.direction_experiment(dfs, R, COST, GRID, MAIN_IDX, args, rng)
    names = list(out["trials_detail"])
    by_k = {k: out["trials_detail"][n] for k, n in zip(KS, names)}
    bps = {k: d["fintokei"]["mean_bp"] for k, d in by_k.items()}
    cmp = {"ic_t_year_by_k": {k: d["ic"]["t_year"] for k, d in by_k.items()}, "ic_all_by_k": {k: d["ic"]["ic_all"] for k, d in by_k.items()}, "mean_bp_by_k": bps,
           "rank_of_k5": (sorted([v for v in bps.values() if v is not None], reverse=True).index(bps[5]) + 1) if bps[5] is not None and all(v is not None for v in bps.values()) else None}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), **out, "comparison_horizon": cmp,
           "multiple_comparisons": "判定は k=5 の 1 本（IC 年単位 t と 3 本中の順位）", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(cmp)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(c):
    t5 = c["ic_t_year_by_k"].get(5); r = c["rank_of_k5"]; bps = c["mean_bp_by_k"]
    if t5 is None or r is None:
        return "未確定: 計算できない（評価期間の不足）"
    if t5 < 1 or (r == 3 and max(bps.values()) - bps[5] > 1.0):
        return "棄却（k=5 は不適）: IC 年単位 t<1 か、損益が最下位で最大との差 1bp 超"
    if t5 >= 2 and r <= 2:
        return "支持（k=5 でよい）: IC 年単位 t≥2 かつ損益が 3 本中 1〜2 位"
    return "未確定"


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run)
