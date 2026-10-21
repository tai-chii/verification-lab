#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q377 S04b 派生: 予測ボラを「上振れだけ」使う非対称サイジング（σ_used = max(σ̂_HAR, σ60)）は、対称版・σ60 版より最大下落が浅いか。
事前登録の正本は SPEC。土台を直接使う型（fe_core.ml + risk、共通部 _s04_common/s04ml.py）。
【出典】[[検証/_基盤/戦略台帳]] S04b／Bongaerts・Kang・van Dijk 2020 FAJ「Conditional Volatility Targeting」（対称なボラ目標は下落を深くすることがある）／知見 Q205
【仮説】Fintokei の固定最大損失の下では、ボラ予測の価値は「レバを上げる」側ではなく「下げる」側にある。σ_used=max(σ̂, σ60)（予測が実現より高いときだけ規模を落とす）は、
  対称版（σ_used=σ̂）と σ60 版より S07 TSMOM60 の規程モードで max_dd が浅く、Sharpe を落とさない。
【データ】wide48 D1_fromH1（2008-01〜）。封印 time<2024-07-01。HAR（log vol_5/20/60 のリッジ α=1・学習 4 年固定長・embargo 10）。評価 2012〜2024-06。
【定義】試行 3 本 = {σ60（既定）, 対称 σ̂_HAR, 非対称 max(σ̂_HAR, σ60)}。main（事前固定）= 非対称。
【測るもの】3 本の規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe・gross_median）。非対称−σ60 の max_dd 差・Sharpe 差。
【帰無】σ̂ を銘柄ごとに年内で並べ替えた σ̂_perm で非対称版を B 回 → max_dd・Sharpe の帰無分布（予測の「情報」でなく「規模を落とす回数」の効果を分ける）。
【判定（事前固定・変更禁止）】支持: 非対称の max_dd が σ60 版より浅く、Sharpe が σ60 版の 0.9 倍以上、かつ帰無の max_dd より浅い側 5% 以内。
  棄却: 非対称の max_dd が σ60 版より深い、または Sharpe が σ60 版の 0.9 倍未満。ほか → 未確定。
【捨てた案の数】1（閾値 σ̂/σ60>1.2 のときだけ落とす段階版。閾値が掃引になるので連続版だけ）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04b_asymmetric_sizing_q377.py（--B 100 既定・リッジだけ）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, parse_args, write_result, tsmom_pos, TrialLog, null_summary, fmt, perm_within, render_readme, render_idea_row, sanitize  # noqa: E402
import s04ml as M  # noqa: E402

K = 5
TRAIN_YEARS = 4
EMBARGO = 10
VARIANTS = ["sig60", "symmetric", "asymmetric"]
MAIN = "asymmetric"

SPEC = Spec(
    qid="Q377",
    question="予測ボラを上振れだけ使う非対称サイジング（σ_used=max(σ̂_HAR, σ60)）は対称版・σ60 版より S07 TSMOM60 の規程モードで最大下落が浅く、シャープを落とさないか",
    hypothesis="固定最大損失の下ではボラ予測の価値は規模を落とす側にある。非対称 σ_used=max(σ̂_HAR, σ60) は σ60 版より max_dd が浅く Sharpe は 0.9 倍以上を保つ",
    reject_if="支持: 非対称の max_dd が σ60 版より浅く、Sharpe が σ60 版の 0.9 倍以上、かつ σ̂ 並べ替え帰無の max_dd より浅い側 5% 以内。棄却: 非対称の max_dd が σ60 版より深い、または Sharpe が σ60 版の 0.9 倍未満。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{"variant": v} for v in VARIANTS], main_param=VARIANTS.index(MAIN), n_tests=1, warmup=250, B=100, null_kind="none", start="2008-01-01",
    discarded="1（閾値つきの段階版）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04b／Bongaerts・Kang・van Dijk 2020 FAJ Conditional Volatility Targeting／知見 Q205",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="3 本（σ60・対称・非対称）の規程モード t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe・gross_median。非対称−σ60 の max_dd 差・Sharpe 比",
    null_desc="σ̂_HAR を銘柄ごとに年内で並べ替えて非対称版を B=100 回 → max_dd・Sharpe の帰無分布",
    prior_art="WebSearch 2026-10-22「asymmetric volatility targeting only de-leverage when forecast volatility rises trend following drawdown」: Bongaerts ほか 2020（条件つきボラ目標で最大下落 54→20%）、Fanous 2026 arXiv 2605.09123（非対称ボラ管理の枠組み）。「予測>実現のときだけ落とす」規則を順張り×固定最大損失で測った研究は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 4 本目（S04b 派生）", designer="Fable", coder="Fable",
)


def _rv_target(df, k=K):
    r2 = (df["ret"].astype(float) ** 2).to_numpy()
    fwd = np.array([np.mean(r2[i + 1:i + 1 + k]) if i + k < len(r2) else np.nan for i in range(len(r2))])
    out = pd.Series(np.log(np.where(fwd > 0, fwd, np.nan))); out.index = pd.to_datetime(df["time"])
    return out


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    X, y, meta = M.build_panel(dfs, _rv_target, {"vol_W": (5, 20, 60)})
    eval_start = M.eval_start_of(meta, TRAIN_YEARS)
    Xl = X.copy()
    for c in ("vol_5", "vol_20", "vol_60"):
        Xl[c] = np.log(Xl[c].replace(0, np.nan))
    ok = Xl[["vol_5", "vol_20", "vol_60"]].notna().all(axis=1).to_numpy()
    pr = M.wf_predict(Xl.iloc[ok], y.iloc[ok], meta.iloc[ok].reset_index(drop=True), ("ridge", 1.0), ["vol_5", "vol_20", "vol_60"], TRAIN_YEARS, EMBARGO)
    sig_hat = np.exp(pr).pow(0.5).reindex(index=R.index, columns=R.columns)
    sig60 = R.rolling(60, min_periods=30).std()
    m = (R.index >= eval_start) & (R.index < M.SEAL)
    pos = pd.DataFrame({s: pd.Series(tsmom_pos(df["close"].values, 60), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()

    def sigma_of(variant, sh):
        s = sig60.copy()
        if variant == "symmetric":
            s[m] = sh.loc[m].where(sh.loc[m].notna(), sig60.loc[m])
        elif variant == "asymmetric":
            s[m] = np.maximum(sh.loc[m].fillna(sig60.loc[m]), sig60.loc[m])
        return s

    log = TrialLog(max_trials=50); trials = {}; evs = {}
    for v in VARIANTS:
        ev = M.eval_portfolio(pos, R, COST, eval_start, sigma=sigma_of(v, sig_hat))
        evs[v] = ev; log.add({"variant": v}, ev["fintokei"]["max_dd"] or 0.0)
        trials[v] = {"fintokei": {k: vv for k, vv in ev["fintokei"].items() if k not in ("years", "rules")}, "gate": ev["gate"], "none_mean_bp": ev["none"]["mean_bp"]}
    frac_cut = fmt(float((sig_hat.loc[m] > sig60.loc[m]).mean().mean()))
    null_dd, null_sh = [], []
    yrs = sig_hat.index.year.to_numpy()
    for b in range(args.B):
        sp = sig_hat.copy()
        for s in sp.columns:
            sp[s] = perm_within(rng, sp[s].to_numpy(), yrs)
        evn = M.eval_portfolio(pos, R, COST, eval_start, sigma=sigma_of("asymmetric", sp))
        null_dd.append(evn["fintokei"]["max_dd"]); null_sh.append(evn["fintokei"]["sharpe"])
    nd = np.array([v if v is not None else np.nan for v in null_dd], float); nsh = np.array([v if v is not None else np.nan for v in null_sh], float)
    main = evs[MAIN]["fintokei"]; base = evs["sig60"]["fintokei"]
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), "eval_start": str(eval_start.date()),
           "main_name": MAIN, "main": trials[MAIN], "baseline_sig60": trials["sig60"], "symmetric": trials["symmetric"], "frac_days_forecast_above_sig60": frac_cut,
           "dd_diff_vs_sig60": fmt((main["max_dd"] or np.nan) - (base["max_dd"] or np.nan)), "sharpe_ratio_vs_sig60": fmt((main["sharpe"] or np.nan) / (base["sharpe"] or np.nan)) if base["sharpe"] else None,
           "null_sigma_perm": {"B": int(np.isfinite(nd).sum()), "max_dd": null_summary(main["max_dd"], nd) if np.isfinite(nd).sum() >= 2 else None,
                               "frac_null_dd_shallower": fmt(np.nanmean(nd >= (main["max_dd"] or np.nan))) if np.isfinite(nd).sum() else None,
                               "sharpe": null_summary(main["sharpe"], nsh) if np.isfinite(nsh).sum() >= 2 else None},
           **log.to_json(), "trials_detail": trials, "multiple_comparisons": "判定は main=非対称 1 本（max_dd と Sharpe 比）。対称版は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(res):
    m = res["main"]["fintokei"]; b = res["baseline_sig60"]["fintokei"]
    shallow = res["null_sigma_perm"].get("frac_null_dd_shallower") if (res["null_sigma_perm"].get("B") or 0) >= 20 else None  # B<20 では支持を出さない
    if m["max_dd"] is None or b["max_dd"] is None or m["sharpe"] is None or b["sharpe"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    ratio = m["sharpe"] / b["sharpe"] if b["sharpe"] > 0 else (1.0 if m["sharpe"] >= b["sharpe"] else 0.0)
    if m["max_dd"] < b["max_dd"] or ratio < 0.9:
        return "棄却: 非対称の max_dd が σ60 版より深い、または Sharpe が 0.9 倍未満"
    if m["max_dd"] > b["max_dd"] and ratio >= 0.9 and shallow is not None and shallow <= 0.05:
        return "支持: 非対称は σ60 版より max_dd が浅く Sharpe 0.9 倍以上、帰無より浅い側 5% 以内"
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
