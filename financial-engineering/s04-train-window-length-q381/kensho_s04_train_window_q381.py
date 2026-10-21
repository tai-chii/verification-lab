#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q381 S04 前提: 学習窓（4／6／10 年の固定長と拡張）で、48 銘柄プールのリッジ方向予測の年次 IC とコスト後損益は変わるか。
事前登録の正本は SPEC。土台を直接使う型（_s04_common/s04ml.py の direction_experiment）。S04a/c で事前固定した「4 年固定長」の妥当性を測る。
【出典】[[検証/_基盤/戦略台帳]] S04／知見 [[順張りの参照日数を候補J個から選ぶと翌年までの楽観はJとともに増えて…]]（Q326 系・選ぶほど楽観）／Zhang ほか 2024 arXiv 2406.08041「HARd to Beat」（学習窓と再推定頻度が結果を決める）
【仮説】学習窓を長くするほど IC は安定するが（年ごとの IC の分散が小さい）、平均 IC と規程モード損益は変わらない＝窓の長さは「選ぶ」対象ではなく事前に固定してよい。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。embargo 10。特徴量 all・ridge α=1・clip。評価は各試行の最初の評価年〜2024-06（窓が長いほど評価が短い。比較は共通の年 2018〜2024-06 でも行う）。
【定義】試行 6 本 = 固定長 {4, 6, 10} 年 × {固定長, 拡張}（拡張は最初の評価年が同じで学習が過去全部）。main（事前固定）= 4 年固定長（Q378 と同じ）。
【測るもの】6 本の年ごと IC（平均・標準偏差・年単位 t）、規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe）。共通の評価年（2018〜2024-06）に揃えた IC 平均と mean_bp。
【帰無】main のラベル並べ替え B=20。比較は共通年の IC の試行間の幅（最大−最小）と、年ごとの IC の順位相関（窓の長さと IC の単調性）。
【判定（事前固定・変更禁止）】支持（窓の長さは効かない）: 共通年の年平均 IC の最大−最小が 0.02 未満 かつ 共通年の mean_bp の符号が 6 本で揃う。
  棄却（窓の長さが効く）: 共通年の年平均 IC の最大−最小が 0.05 以上、または mean_bp の符号が割れる。ほか → 未確定。
【捨てた案の数】1（再推定頻度＝月次。年次で固定）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04_train_window_q381.py（リッジだけ・数分）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, fmt  # noqa: E402
import s04ml as M  # noqa: E402

GRID = [{"fset": "all", "model": ("ridge", 1.0), "rule": "clip", "k": 5, "train_years": ty, "expanding": ex} for ty in (4, 6, 10) for ex in (False, True)]
MAIN_IDX = 0
COMMON_FROM = 2018

SPEC = Spec(
    qid="Q381",
    question="学習窓（4／6／10 年の固定長と拡張）で 48 銘柄プールのリッジ方向予測の年次 IC とコスト後損益は変わるか（6 試行・事前固定 4 年固定長の妥当性）",
    hypothesis="学習窓を長くするほど年ごとの IC の分散は小さくなるが、共通の評価年（2018〜2024-06）の平均 IC と規程モード損益は変わらない＝窓の長さは事前に固定してよい",
    reject_if="支持（窓は効かない）: 共通年の年平均 IC の最大−最小が 0.02 未満 かつ 共通年 mean_bp の符号が 6 本で揃う。棄却（窓が効く）: 最大−最小が 0.05 以上、または mean_bp の符号が割れる。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{k: (str(v) if k == "model" else v) for k, v in g.items()} for g in GRID], main_param=MAIN_IDX, n_tests=1, warmup=250, B=20, null_kind="none", start="2008-01-01",
    discarded="1（再推定頻度）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04／知見 Q326 系／Zhang ほか 2024 arXiv 2406.08041 HARd to Beat",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="6 本の年ごと IC（平均・標準偏差・年単位 t）と規程モード。共通年 2018〜2024-06 の IC 平均と mean_bp の幅",
    null_desc="main（4 年固定長）のラベル並べ替え B=20。比較は共通年の試行間の IC の幅と mean_bp の符号",
    prior_art="WebSearch 2026-10-22「rolling versus expanding training window length walk-forward machine learning return prediction stability」: arXiv 2601.08896（NEPSE・XGBoost・両方式）、解説記事多数。多資産 D1 のリッジ方向予測で窓の長さの感度を年次 IC で測った研究は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 8 本目（S04 前提）", designer="Fable", coder="Fable",
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    out = M.direction_experiment(dfs, R, COST, GRID, MAIN_IDX, args, rng)
    common = {}
    for name, d in out["trials_detail"].items():
        ics = [v for y, v in d["ic"]["ic_years"].items() if int(y) >= COMMON_FROM and v is not None]
        # 年ごとの bp は mean_bp_post（2017〜）で代用し、共通年（2018〜）は IC で見る
        common[name] = {"ic_common_mean": fmt(np.mean(ics)) if ics else None, "ic_common_sd": fmt(np.std(ics, ddof=1)) if len(ics) > 1 else None,
                        "ic_year_sd_all": fmt(np.std([v for v in d["ic"]["ic_years"].values() if v is not None], ddof=1)) if len(d["ic"]["ic_years"]) > 1 else None,
                        "mean_bp_post": d["fintokei"]["mean_bp_post"]}
    icm = [v["ic_common_mean"] for v in common.values() if v["ic_common_mean"] is not None]
    bpp = [v["mean_bp_post"] for v in common.values() if v["mean_bp_post"] is not None]
    cmp = {"ic_common_range": fmt(max(icm) - min(icm)) if len(icm) == len(GRID) else None, "bp_post_signs_agree": (all(b > 0 for b in bpp) or all(b < 0 for b in bpp)) if len(bpp) == len(GRID) else None,
           "common_from": COMMON_FROM, "per_trial": common}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), **out, "comparison_windows": cmp,
           "multiple_comparisons": "判定は共通年の IC の幅と mean_bp の符号（1 本）。6 試行は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(cmp)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(c):
    if c["ic_common_range"] is None or c["bp_post_signs_agree"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if c["ic_common_range"] >= 0.05 or not c["bp_post_signs_agree"]:
        return "棄却（窓の長さが効く）: 共通年 IC の幅≥0.05 か mean_bp の符号が割れる"
    if c["ic_common_range"] < 0.02 and c["bp_post_signs_agree"]:
        return "支持（窓の長さは効かない）: 共通年 IC の幅<0.02 かつ mean_bp の符号が揃う"
    return "未確定"


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run)
