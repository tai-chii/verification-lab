#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q388 S04b 補正版（サイジング）: 水準 HAR-RV（銘柄別）の σ̂ を size_weights の σ に渡した S07 TSMOM60 の規程モードは、σ60 版より最大下落が浅く Sharpe が高いか。
事前登録の正本は SPEC。土台を直接使う型（fe_core.risk・ml、共通部 _s04_common/volfc.py・s04ml.py）。
【出典】[[検証/_基盤/戦略台帳]] S04b／Q376（偏った σ̂ でサイジング未判定）／Q377（保留・本件の結果待ち）／知見 Q205（ボラ・ターゲティング）／Harvey ほか 2018 The Impact of Volatility Targeting
【仮説】較正された σ̂（実現/予測の平均 0.8〜1.25）を規程モードの σ に渡すと、σ60 版より max_dd が浅く Sharpe が高い。偏りが無ければ「予測の情報」だけが効く。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。σ̂ = sqrt(har_level_persym の予測分散)（学習 4 年固定長・embargo 10・下限 0.1×σ60²）。評価窓（2012〜2024-06）以外は σ60。
【定義】試行 2 本 = {σ60（RULES_FINTOKEI 既定）, σ̂_HAR 水準}。main = σ̂。合図 = S07 TSMOM60 の符号。コストは s04ml.WIDE48_COST_REL。
【測るもの】2 本の規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe・gross_median）、σ̂−σ60 の max_dd 差・Sharpe 差。前提として Q387 と同じ較正・QLIKE 損失差。
【帰無】σ̂ を銘柄ごとに年内で並べ替えた σ̂_perm で同じ損益 B=50 回 → max_dd・Sharpe の帰無分布（予測の情報と「規模の揺れ」を分ける）。
【判定（事前固定・変更禁止）】棄却: σ̂ の較正が範囲外、または QLIKE 損失差（σ60−σ̂）の年単位 t<0（予測の前提が落ちる）、または σ̂ 版の max_dd が σ60 版より深い。
  支持: 前提 OK かつ σ̂ 版の max_dd が σ60 版より浅く Sharpe が高く、帰無の max_dd より浅い側 5% 以内（B≥20）。ほか → 未確定。
【捨てた案の数】2（非対称 max(σ̂,σ60)＝Q377 が保留で持っている・σ̂ を port_vol_window 側にも使う＝規程の天井を動かすので不可）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04b_vol_sizing_calibrated_q388.py（--B 50 既定）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, tsmom_pos, TrialLog, null_summary, fmt, perm_within  # noqa: E402
import s04ml as M  # noqa: E402
import volfc as V  # noqa: E402

SPEC = Spec(
    qid="Q388",
    question="水準 HAR-RV（銘柄別 OLS）の σ̂ を size_weights の σ に渡した S07 TSMOM60 の規程モードは、σ60 版より最大下落が浅く Sharpe が高いか（較正を前提条件とし σ̂ 並べ替え帰無で判定。Q376 の偏りを除いた再判定・Q377 の前提）",
    hypothesis="較正された σ̂（har_level_persym）を規程モードの σ に渡すと、σ60 版より max_dd が浅く Sharpe が高く、σ̂ を年内で並べ替えた帰無より浅い",
    reject_if="棄却: σ̂ の較正が範囲外（実現/予測の銘柄平均 0.8〜1.25 の外）、または QLIKE 損失差（σ60−σ̂）の年単位 t<0、または σ̂ 版の max_dd が σ60 版より深い。支持: 前提 OK かつ σ̂ 版の max_dd が σ60 版より浅く Sharpe が高く、σ̂ 並べ替え帰無の max_dd より浅い側 5% 以内（B≥20）。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{"sigma": "sig60"}, {"sigma": "har_level_persym"}], main_param=1, n_tests=2, warmup=250, B=50, null_kind="block_perm", start="2008-01-01",
    discarded="2（非対称版＝Q377・port_vol_window 側）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04b／Q376／Q377（保留）／知見 [[日足順張りの建玉を直前60日の実現ボラの逆数で規模調整すると年ごとのシャープが約0.09上がる]]（Q205）／Harvey・Hoyle・Korgaonkar・Rattray・Sargaison・Van Hemert 2018",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: s04ml.WIDE48_COST_REL（COST_RT に無い 34 銘柄は知識から記載・実行者が spread_<sym>.csv と照合）",
    measure="σ60 版と σ̂ 版の規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe・gross_median）、差、較正・QLIKE 損失差（前提）",
    null_desc="σ̂ を銘柄ごとに年内で並べ替えた σ̂_perm で同じ損益 B=50 回 → max_dd・Sharpe の帰無分布。帰無の max_dd より浅い側の割合",
    prior_art="WebSearch 2026-10-22「volatility forecast HAR-RV volatility targeting trend following drawdown reduction realized volatility sizing multi-asset」: Harvey ほか 2018（60 資産超でボラ目標は極端な損失の確率を下げる・推定器は半減期 20 日の EWMA）、Quantpedia のまとめ。HAR-RV の予測を規程モード（1 銘柄上限・日次停止）の σ に渡して最大下落を測った研究は未確認",
    batch="/lab-plan ターミナル版 2026-10-22・N=4 の 4 本目（S04b 補正版・サイジング）", designer="Fable", coder="Fable",
    settings={"seal": str(V.SEAL.date()), "k": V.K, "train_years": V.TRAIN_YEARS, "embargo": V.EMBARGO, "floor_mult": V.FLOOR_MULT, "calib_range": V.CALIB_RANGE, "sigma_main": V.MAIN},
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    RV = V.rv_wide(dfs).reindex(index=R.index, columns=R.columns)
    preds, info, sig60sq = V.predict_all(dfs, R, which=["naive60", V.MAIN])
    eval_start = pd.Timestamp(f"{min(pd.to_datetime(df['time']).min().year for df in dfs.values()) + V.TRAIN_YEARS}-01-01")
    mask = V.eval_mask(R.index, eval_start)
    pred = preds[V.MAIN]
    premise = V.evaluate(pred, RV, sig60sq, mask); premise["info"] = info[V.MAIN]
    sig60 = np.sqrt(sig60sq)
    pos = pd.DataFrame({s: pd.Series(tsmom_pos(df["close"].values, 60), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()
    base = M.eval_portfolio(pos, R, COST, eval_start)
    sigma_hat = sig60.copy(); sigma_hat[mask] = np.sqrt(pred.loc[mask]).where(pred.loc[mask].notna(), sig60.loc[mask])
    main_ev = M.eval_portfolio(pos, R, COST, eval_start, sigma=sigma_hat)
    log = TrialLog(max_trials=50)
    log.add({"sigma": "sig60"}, base["fintokei"]["max_dd"] or np.nan); log.add({"sigma": V.MAIN}, main_ev["fintokei"]["max_dd"] or np.nan)
    null_dd, null_sh = [], []
    yrs = sigma_hat.index.year.to_numpy()
    for b in range(args.B):
        sp = sigma_hat.copy()
        for s in sp.columns:
            sp[s] = perm_within(rng, sp[s].to_numpy(), yrs)
        evn = M.eval_portfolio(pos, R, COST, eval_start, sigma=sp)
        null_dd.append(evn["fintokei"]["max_dd"]); null_sh.append(evn["fintokei"]["sharpe"])
    nd = np.array([v if v is not None else np.nan for v in null_dd], float); nsh = np.array([v if v is not None else np.nan for v in null_sh], float)
    obs_dd = main_ev["fintokei"]["max_dd"]
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), "eval_start": str(eval_start.date()), "seal": str(V.SEAL.date()),
           "premise": premise, "baseline_sig60": M.strip_ports(base), "main": M.strip_ports(main_ev),
           "diff_vs_sig60": {"max_dd": fmt((obs_dd or np.nan) - (base["fintokei"]["max_dd"] or np.nan)), "sharpe": fmt((main_ev["fintokei"]["sharpe"] or np.nan) - (base["fintokei"]["sharpe"] or np.nan)),
                             "mean_bp": fmt((main_ev["fintokei"]["mean_bp"] or np.nan) - (base["fintokei"]["mean_bp"] or np.nan))},
           "null_sigma_perm": {"B": int(np.isfinite(nd).sum()), "max_dd": null_summary(obs_dd if obs_dd is not None else np.nan, nd) if np.isfinite(nd).sum() >= 2 else None,
                               "frac_null_dd_shallower": fmt(float(np.nanmean(nd >= (obs_dd if obs_dd is not None else np.nan)))) if np.isfinite(nd).sum() else None,
                               "sharpe": null_summary(main_ev["fintokei"]["sharpe"] if main_ev["fintokei"]["sharpe"] is not None else np.nan, nsh) if np.isfinite(nsh).sum() >= 2 else None},
           **log.to_json(), "multiple_comparisons": "判定は main=σ̂ の 2 本（max_dd・Sharpe）＋前提（較正・QLIKE）。σ60 版は基準", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(res):
    pr = res["premise"]; m = res["main"]["fintokei"]; b = res["baseline_sig60"]["fintokei"]; nl = res["null_sigma_perm"]
    if pr["calib_mean_ratio"] is None or pr["loss_diff_year_t"] is None or m["max_dd"] is None or b["max_dd"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if not pr["calib_ok"]:
        return f"棄却: σ̂ の較正が範囲外（実現/予測の平均 {pr['calib_mean_ratio']}）"
    if pr["loss_diff_year_t"] < 0:
        return "棄却: QLIKE 損失差（σ60−σ̂）の年単位 t<0（予測の前提が落ちる）"
    if m["max_dd"] < b["max_dd"]:
        return "棄却: σ̂ 版の max_dd が σ60 版より深い"
    shallow = nl.get("frac_null_dd_shallower") if (nl.get("B") or 0) >= 20 else None
    if m["max_dd"] > b["max_dd"] and (m["sharpe"] or -9) > (b["sharpe"] or 9) and shallow is not None and shallow <= 0.05:
        return "支持: 前提 OK・σ̂ 版は max_dd が浅く Sharpe が高く、σ̂ 並べ替え帰無より浅い側 5% 以内"
    return "未確定"


if __name__ == "__main__":
    M.ml_main(SPEC, HERE, run, script_kind="土台を直接使う型（fe_core.risk・ml・_s04_common/volfc.py）")
