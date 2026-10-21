#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q387 S04b 補正版（予測）: 翌 5 日実現分散を水準で学習する HAR-RV（銘柄別）は、較正を満たした上で QLIKE で σ60 に勝つか。
事前登録の正本は SPEC。土台を直接使う型（fe_core.ml の walk_forward/ridge・qlike、共通部 _s04_common/volfc.py・s04ml.py）。
【出典】[[検証/_基盤/戦略台帳]] S04b／Q376（log-HAR は中央値予測で実現/予測 2.29・QLIKE で σ60 に負け）／Corsi 2009 HAR-RV／Duan 1983 smearing／
  知見 [[核の12特徴量を使った木モデルは24時間先の実現ボラを持続基準線より良く当てるが、過去1日1週1か月の実現分散だけの線形HAR-RVには13年中12年で負ける]]
【仮説】Q376 の敗因は log→exp の中央値偏り。水準で学習する HAR-RV（銘柄別）は較正（実現/予測の平均 0.8〜1.25）を満たし、QLIKE で σ60 に勝つ（損失差の年単位 t≥2・nw_t≥2）。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。年次ウォークフォワード（学習 4 年固定長・embargo 10）。評価 2012〜2024-06。
【定義】予測器 5 本（volfc.PREDICTORS）。main = har_level_persym。下限 0.1×σ60²。
【測るもの】予測器ごとの QLIKE（銘柄平均）、σ60 との損失差（日次 nw_t lag=5・年単位 t・年ごと）、較正（実現/予測の平均・中央値）。
【帰無】Diebold–Mariano 型: 損失差の日次 nw_t（lag=5）。年単位 t を併記。
【判定（事前固定・変更禁止）】支持: main の較正 OK かつ損失差（σ60−main）の年単位 t≥2 かつ nw_t≥2。棄却: main の較正が範囲外（偏りが残る）または損失差の年単位 t<0。ほか → 未確定。
【捨てた案の数】3（QLIKE を直接最小化する推定＝numpy だけでは重い・Parkinson レンジ＝Q171 系で既出・GBM 水準＝Q376 で負け）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04b_vol_forecast_calibrated_q387.py（帰無は解析的なので B 不要・--B は無視）。--smoke で合成 3 銘柄。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, TrialLog, fmt  # noqa: E402
import s04ml as M  # noqa: E402
import volfc as V  # noqa: E402

SPEC = Spec(
    qid="Q387",
    question="48 銘柄 D1 の翌 5 日実現分散の予測を水準で学習する HAR-RV（銘柄別・Corsi 原型）・プール水準 HAR・EWMA λ0.94・log-HAR スミアリング補正は、較正（実現/予測の平均 0.8〜1.25）を満たした上で QLIKE で σ60 に勝つか（Q376 の中央値偏りの再設計）",
    hypothesis="main=har_level_persym は較正を満たし、QLIKE の損失差（σ60−main）が年単位 t≥2 かつ nw_t≥2。Q376 の log-HAR（較正 2.29）はスミアリングで較正が直るが QLIKE では水準版に劣る",
    reject_if="支持: main の較正 OK（実現/予測の銘柄平均 0.8〜1.25）かつ損失差（σ60−main）の年単位 t≥2 かつ nw_t（lag 5）≥2。棄却: main の較正が範囲外、または損失差の年単位 t<0。ほか → 未確定。他 4 予測器は記述（TrialLog 5）",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{"predictor": p} for p in V.PREDICTORS], main_param=V.PREDICTORS.index(V.MAIN), n_tests=2, warmup=250, B=0, null_kind="none", start="2008-01-01",
    discarded="3（QLIKE 直接最小化・Parkinson レンジ・GBM 水準）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04b／Q376（log-HAR の中央値偏り）／Corsi 2009 HAR-RV／Duan 1983 smearing／知見 Q171 系（線形 HAR-RV は木に勝つ）",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。目的＝翌 5 日の r² 平均（水準・gap 行の ret はそのまま）。評価は各銘柄のウォークフォワード評価窓（2012〜2024-06）だけ",
    measure="予測器 5 本の QLIKE（銘柄ごと→平均）、σ60 との損失差の日次 nw_t（lag=5）・年単位 t・年ごと、較正（実現/予測の銘柄平均・中央値）",
    null_desc="Diebold–Mariano 型: 損失差の日次 nw_t（lag=5）。並べ替え帰無は使わない（B=0）",
    prior_art="WebSearch 2026-10-22「HAR-RV log transformation retransformation bias QLIKE forecast evaluation levels versus log smearing realized volatility」: Clements・Preve 2021「A Practical Guide to harnessing the HAR volatility model」（推定法・変換・QLIKE の比較）、arXiv 2609.21587 Rough HAR（log モデルを対数正規補正で戻す）、arXiv 2208.12264（変換の偏り）。水準・スミアリング・中央値の 3 つを同じ 48 銘柄・5 日先・QLIKE で並べ、較正を関門にした比較は未確認",
    batch="/lab-plan ターミナル版 2026-10-22・N=4 の 3 本目（S04b 補正版・予測）", designer="Fable", coder="Fable",
    settings={"seal": str(V.SEAL.date()), "k": V.K, "train_years": V.TRAIN_YEARS, "embargo": V.EMBARGO, "floor_mult": V.FLOOR_MULT, "calib_range": V.CALIB_RANGE, "main": V.MAIN},
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    RV = V.rv_wide(dfs).reindex(index=R.index, columns=R.columns)
    preds, info, sig60sq = V.predict_all(dfs, R)
    eval_start = pd.Timestamp(f"{min(pd.to_datetime(df['time']).min().year for df in dfs.values()) + V.TRAIN_YEARS}-01-01")
    mask = V.eval_mask(R.index, eval_start)
    # 評価窓を揃える: main（ウォークフォワード）の予測がある行だけで全予測器を比べる
    common = preds[V.MAIN].notna()
    log = TrialLog(max_trials=50); trials = {}
    for name in V.PREDICTORS:
        p = preds[name].where(common)
        ev = V.evaluate(p, RV, sig60sq, mask)
        ev["info"] = info[name]
        log.add({"predictor": name}, ev["qlike_mean"] if ev["qlike_mean"] is not None else np.nan)
        trials[name] = ev
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), "eval_start": str(eval_start.date()), "seal": str(V.SEAL.date()),
           "main_name": V.MAIN, "main": trials[V.MAIN], **log.to_json(), "trials_detail": trials,
           "multiple_comparisons": "判定は main=har_level_persym の 2 本（年単位 t・nw_t）＋較正の前提。ほか 4 予測器は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(res):
    m = res["main"]
    if m["loss_diff_year_t"] is None or m["calib_mean_ratio"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if not m["calib_ok"]:
        return f"棄却: main の較正が範囲外（実現/予測の平均 {m['calib_mean_ratio']}・偏りが残る）"
    if m["loss_diff_year_t"] < 0:
        return "棄却: main の QLIKE 損失差（σ60−main）の年単位 t<0"
    if m["loss_diff_year_t"] >= 2 and (m["loss_diff_nw_t"] or 0) >= 2:
        return "支持: main は較正 OK かつ QLIKE で σ60 に勝つ（年単位 t≥2・nw_t≥2）"
    return "未確定"


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run, script_kind="土台を直接使う型（fe_core.ml walk_forward/ridge・qlike・_s04_common/volfc.py）")
