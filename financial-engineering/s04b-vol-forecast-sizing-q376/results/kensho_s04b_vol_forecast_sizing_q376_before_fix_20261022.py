#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q376 S04b: 翌 5 日の実現ボラを予測して size_weights の σ に渡すと、S07 TSMOM60 の規程モードで最大下落が浅くなるか。
事前登録の正本は SPEC。土台を直接使う型（fe_core.ml + risk、共通部 _s04_common/s04ml.py）。
【出典】[[検証/_基盤/戦略台帳]] S04b／知見 [[日足順張りの建玉を直前60日の実現ボラの逆数で規模調整すると年ごとのシャープが約0.09上がる]]（Q205）／
  知見 [[核の12特徴量を使った木モデルは24時間先の実現ボラを持続基準線より良く当てるが、過去1日1週1か月の実現分散だけの線形HAR-RVには13年中12年で負ける]]／Corsi 2009 HAR-RV
【仮説】(1) 翌 5 日実現分散 RV5[t+1..t+5] の予測は QLIKE で σ60 の素朴予測より小さい（HAR が最有力）。(2) 予測 σ̂ を size_weights の σ に渡した S07 TSMOM60 の規程モード損益は、σ60 版より最大下落が浅くシャープが高い。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。年次ウォークフォワード（学習 4 年固定長・embargo 10）。評価 2012〜2024-06。
【定義】予測器 5 本 = {σ20 素朴, σ60 素朴, HAR（log vol_5/vol_20/vol_60 のリッジ α=1）, ridge 全特徴 α=1, gbm 全特徴 d3 i200}。目的＝log(RV5)。σ̂=exp(予測)/√5 を日次 σ に直す。
  main（事前固定）= HAR。σ̂ は学習年（評価前）は σ60 で埋め、評価期間だけ σ̂。
【測るもの】予測器ごとの QLIKE（全体・年ごと）、σ60 との損失差の年単位 t と日次 nw_t（lag=5、Diebold–Mariano 型）。
  サイジング: 予測器ごとの S07 TSMOM60 規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe）と σ60 版（RULES_FINTOKEI 既定）との差。
【帰無】(1) DM 型: 損失差の日次 nw_t。(2) サイジング: σ̂ の列を銘柄ごとに年内で並べ替えた（日付との対応を壊す）σ̂_perm で同じ損益 B 回 → max_dd・Sharpe の帰無分布。
【判定（事前固定・変更禁止）】支持: HAR の QLIKE 損失差（σ60−HAR）が年単位 t≥2 かつ nw_t≥2、かつ HAR サイジングの max_dd が σ60 版より浅く Sharpe が高く、帰無（σ̂ 並べ替え）の max_dd より浅い側 5% 以内。
  棄却: HAR の QLIKE が σ60 に勝たない（損失差 t<0）、または HAR サイジングの max_dd が σ60 版より深い。ほか → 未確定。
【捨てた案の数】2（Parkinson レンジを足す＝Q171 系で既出、地平線 k=20＝Q383 の型で後に）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04b_vol_forecast_sizing_q376.py（--B 50 既定）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, parse_args, write_result, tsmom_pos, TrialLog, null_summary, qlike, nw_t, tstat, fmt, perm_within, render_readme, render_idea_row, sanitize  # noqa: E402
import s04ml as M  # noqa: E402

K = 5
TRAIN_YEARS = 4
EMBARGO = 10
FEAT_KW = {"vol_W": (5, 20, 60)}
PREDICTORS = ["naive20", "naive60", "har", "ridge_all", "gbm_all"]
MAIN = "har"

SPEC = Spec(
    qid="Q376",
    question="48 銘柄 D1 の翌 5 日実現ボラ予測（σ20・σ60・HAR・リッジ全特徴・GBM 全特徴）は QLIKE で σ60 に勝ち、σ̂ を size_weights に渡すと S07 TSMOM60 の規程モードで最大下落が浅くシャープが上がるか",
    hypothesis="main=HAR（log vol_5/20/60 のリッジ）の log(RV5) 予測は QLIKE で σ60 素朴予測に勝ち、σ̂ を size_weights の σ に渡した S07 TSMOM60 規程モードは σ60 版より max_dd が浅く Sharpe が高い",
    reject_if="支持: HAR の QLIKE 損失差（σ60−HAR）が年単位 t≥2 かつ nw_t≥2、かつ HAR サイジングの max_dd が σ60 版より浅く Sharpe が高く、σ̂ 並べ替え帰無の max_dd より浅い側 5% 以内。棄却: HAR の QLIKE が σ60 に勝たない（損失差 t<0）、または HAR サイジングの max_dd が σ60 版より深い。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{"predictor": p} for p in PREDICTORS], main_param=PREDICTORS.index(MAIN), n_tests=2, warmup=250, B=50, null_kind="none", start="2008-01-01",
    discarded="2（Parkinson レンジ・k=20）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04b／知見 Q205（ボラ・ターゲティング）／知見 Q171 系（HAR-RV は木に勝つ）／Corsi 2009 HAR-RV",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="予測器 5 本の QLIKE（全体・年）、σ60 との損失差の年単位 t・nw_t（lag=5）。各 σ̂ で S07 TSMOM60 の規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe）と σ60 版との差",
    null_desc="(1) DM 型: 損失差の日次 nw_t。(2) σ̂ を銘柄ごとに年内で並べ替えた σ̂_perm で同じ損益 B=50 回 → max_dd・Sharpe の帰無分布",
    prior_art="WebSearch 2026-10-22「machine learning realized volatility forecast volatility targeting trend following drawdown HAR comparison QLIKE」: HARd to Beat（arXiv 2406.08041・1455 株で ML は HAR に勝てない）、Fed 2025 サーベイ、HARNet。予測を size_weights に渡して順張りの最大下落を測る研究は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 3 本目（S04b 本体）", designer="Fable", coder="Fable",
)


def _rv_target(df, k=K):
    r = df["ret"].astype(float)
    rv = pd.Series([np.nan] * len(r)); rv.index = pd.to_datetime(df["time"])
    r2 = (r ** 2).to_numpy()
    fwd = np.array([np.mean(r2[i + 1:i + 1 + k]) if i + k < len(r2) else np.nan for i in range(len(r2))])
    rv[:] = np.log(np.where(fwd > 0, fwd, np.nan))
    return rv


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    X, y, meta = M.build_panel(dfs, _rv_target, FEAT_KW)
    eval_start = M.eval_start_of(meta, TRAIN_YEARS)
    Y = M.target_wide(dfs, _rv_target)  # log RV5（分散・日次平均）
    RV = np.exp(Y)
    sig60 = R.rolling(60, min_periods=30).std(); sig20 = R.rolling(20, min_periods=10).std()
    pos = pd.DataFrame({s: pd.Series(tsmom_pos(df["close"].values, 60), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()
    base = M.eval_portfolio(pos, R, COST, eval_start)  # σ60 版（既定）
    log = TrialLog(max_trials=50); trials = {}; s2 = {}
    Xl = X.copy()
    for c in ("vol_5", "vol_20", "vol_60"):
        Xl[c] = np.log(Xl[c].replace(0, np.nan))
    ok = Xl[["vol_5", "vol_20", "vol_60"]].notna().all(axis=1).to_numpy()
    for name in PREDICTORS:
        if name == "naive20":
            s2[name] = sig20 ** 2
        elif name == "naive60":
            s2[name] = sig60 ** 2
        elif name == "har":
            pr = M.wf_predict(Xl.iloc[ok], y.iloc[ok], meta.iloc[ok].reset_index(drop=True), ("ridge", 1.0), ["vol_5", "vol_20", "vol_60"], TRAIN_YEARS, EMBARGO)
            s2[name] = np.exp(pr)
        elif name == "ridge_all":
            s2[name] = np.exp(M.wf_predict(Xl.iloc[ok], y.iloc[ok], meta.iloc[ok].reset_index(drop=True), ("ridge", 1.0), list(Xl.columns), TRAIN_YEARS, EMBARGO))
        elif name == "gbm_all":
            s2[name] = np.exp(M.wf_predict(X, y, meta, ("gbm", {"max_depth": 3, "max_iter": 200}), list(X.columns), TRAIN_YEARS, EMBARGO))
        p2 = s2[name].reindex(index=R.index, columns=R.columns)
        ev = RV.reindex_like(p2)
        m = (p2.index >= eval_start) & (p2.index < M.SEAL)
        # QLIKE（銘柄ごとに計算して平均。水準の違う銘柄を混ぜない）
        ql = {s: qlike(p2.loc[m, s].to_numpy(), ev.loc[m, s].to_numpy()) for s in R.columns}
        ql_mean = float(np.nanmean(list(ql.values())))
        # 損失差 vs σ60（日次・銘柄平均 → nw_t、年単位 t）
        l_this = (p2.loc[m] / ev.loc[m] - np.log(p2.loc[m] / ev.loc[m]) - 1); l_base = (sig60.loc[m] ** 2 / ev.loc[m] - np.log(sig60.loc[m] ** 2 / ev.loc[m]) - 1)
        diff = (l_base - l_this).mean(axis=1).dropna()
        yr = diff.groupby(diff.index.year).mean()
        # サイジング: σ̂（評価前は σ60 で埋める）
        sigma_used = sig60.copy(); sigma_used[m] = p2.loc[m].pow(0.5).where(p2.loc[m].notna(), sig60.loc[m])
        evp = M.eval_portfolio(pos, R, COST, eval_start, sigma=sigma_used)
        log.add({"predictor": name}, ql_mean)
        trials[name] = {"qlike_mean": fmt(ql_mean), "loss_diff_vs_sig60_mean": fmt(diff.mean()), "loss_diff_nw_t": fmt(nw_t(diff.to_numpy(), lag=K)) if len(diff) > 10 else None,
                        "loss_diff_year_t": fmt(tstat(yr.to_numpy())) if len(yr) > 1 else None, "loss_diff_years": {int(k): fmt(v) for k, v in yr.items()},
                        "sizing_fintokei": {k: v for k, v in evp["fintokei"].items() if k not in ("years", "rules")}, "sizing_gate": evp["gate"],
                        "dd_diff_vs_sig60": fmt((evp["fintokei"]["max_dd"] or np.nan) - (base["fintokei"]["max_dd"] or np.nan)),
                        "sharpe_diff_vs_sig60": fmt((evp["fintokei"]["sharpe"] or np.nan) - (base["fintokei"]["sharpe"] or np.nan))}
        if name == MAIN:
            main_sigma = sigma_used; main_ev = evp
    # 帰無 (2): main の σ̂ を銘柄ごとに年内で並べ替え
    null_dd, null_sh = [], []
    yrs = main_sigma.index.year.to_numpy()
    for b in range(args.B):
        sp = main_sigma.copy()
        for s in sp.columns:
            sp[s] = perm_within(rng, sp[s].to_numpy(), yrs)
        evn = M.eval_portfolio(pos, R, COST, eval_start, sigma=sp)
        null_dd.append(evn["fintokei"]["max_dd"]); null_sh.append(evn["fintokei"]["sharpe"])
    nd = np.array([v if v is not None else np.nan for v in null_dd], float); nsh = np.array([v if v is not None else np.nan for v in null_sh], float)
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), "eval_start": str(eval_start.date()), "k": K,
           "main_name": MAIN, "main": trials[MAIN], "baseline_sig60": M.strip_ports(base),
           "null_sigma_perm": {"B": int(np.isfinite(nd).sum()), "max_dd": null_summary(main_ev["fintokei"]["max_dd"], nd) if np.isfinite(nd).sum() >= 2 else None,
                               "frac_null_dd_shallower": fmt(np.nanmean(nd >= (main_ev["fintokei"]["max_dd"] or np.nan))) if np.isfinite(nd).sum() else None,
                               "sharpe": null_summary(main_ev["fintokei"]["sharpe"], nsh) if np.isfinite(nsh).sum() >= 2 else None},
           **log.to_json(), "trials_detail": trials, "multiple_comparisons": "判定は main=HAR の 2 本（QLIKE 損失差・サイジングの max_dd）。ほか 4 予測器は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(res):
    m = res["main"]; b = res["baseline_sig60"]["fintokei"]; nl = res["null_sigma_perm"]
    if m["loss_diff_year_t"] is None or m["sizing_fintokei"]["max_dd"] is None or b["max_dd"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if m["loss_diff_year_t"] < 0 or m["sizing_fintokei"]["max_dd"] < b["max_dd"]:
        return "棄却: HAR の QLIKE が σ60 に勝たない、または HAR サイジングの max_dd が σ60 版より深い"
    shallow = nl.get("frac_null_dd_shallower") if (nl.get("B") or 0) >= 20 else None  # B<20 では支持を出さない
    if (m["loss_diff_year_t"] >= 2 and (m["loss_diff_nw_t"] or 0) >= 2 and m["sizing_fintokei"]["max_dd"] > b["max_dd"]
            and (m["sizing_fintokei"]["sharpe"] or -9) > (b["sharpe"] or 9) and shallow is not None and shallow <= 0.05):
        return "支持: HAR は QLIKE で σ60 に勝ち（t≥2・nw_t≥2）、サイジングで max_dd が浅く Sharpe が高く、σ̂ 並べ替え帰無より浅い側 5% 以内"
    return "未確定"


if __name__ == "__main__":
    script = os.path.basename(__file__)
    if "--readme" in sys.argv:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）")); print("wrote README.md"); sys.exit(0)
    if "--idea-row" in sys.argv:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE))); sys.exit(0)
    args = parse_args(default_B=SPEC.B)
    if not args.smoke:
        M.data_guard(SPEC.qid, HERE)
    else:
        args.B = min(args.B, 2)
    rng = np.random.default_rng(args.seed)
    res = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    print("machine_verdict:", res["machine_verdict"])
    print(write_result(SPEC.qid, sanitize(res), args.smoke, here=HERE))
