#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q305: TREND7 日足の買い持ちを直前 20 日実現ボラの逆数で規模調整するとシャープは同じ重み分布の循環シフトより高いか（Moreira–Muir の CFD 移植）
================================================================================
事前登録の正本は下の SPEC（fe_core の Spec を事前登録の入れ物として使う「土台を直接使う型」）。
種: ローカル LLM（qwen3:8b）のアイデア 2026-10-15「ボラティリティターゲティングは TREND7 D1 で買い持ちをリターン・シャープレシオで上回るか」を Opus が選別・設計。
実行: python3 kensho_vol_managed_bh_q305.py（B=1000）／ --smoke --B 5 ／ --readme ／ --idea-row
"""
import datetime as _dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (Spec, TREND7, SPLIT_YEAR, parse_args, write_result, syms_available, health, load_d1,  # noqa: E402
                     cost_bp_oneway, pnl_bp, sharpe_ann, max_drawdown, fmt, z_of)
from fe_core.readme import render_readme, render_idea_row  # noqa: E402

WIN = 20
CAP = 2.0
MIN_HIST = 250       # 目標ボラ（拡大窓の中央値）を作るのに要る σ の本数
MIN_SHIFT = 60
REBAL = 5            # 重みの更新間隔（本）

SPEC = Spec(
    qid="Q305",
    question="TREND7 日足の買い持ちを直前 20 日実現ボラの逆数で規模調整するとシャープは同じ重み分布の循環シフトより高いか（Moreira–Muir の CFD 移植）",
    hypothesis="w[t]=min(σ̃[t]/σ20[t], 2)。σ20 は t までの 20 日の日次リターンの標準偏差、σ̃ は t までの σ20 の拡大窓の中央値（先読みなし）。"
               "重みは 5 本ごとに更新し間は持ち続ける。t の終値で決め t+1 から保有（買いのみ）。7 銘柄の等加重束の年率シャープ（段階1コスト後）は、前後半とも買い持ちより高く、"
               "銘柄ごとに w を循環シフトした（重みの分布と平均を保つ）帰無のシャープより z≥2 で高い",
    reject_if="支持: 前半（〜2016。助走 270 日の後から）・後半（2017–2026-06）とも Sharpe_調整 > Sharpe_買い持ち かつ 帰無に対する z≥2。"
              "棄却: 全期間の z<1。それ以外 → 未確定。（前後半の両方を要求する交差なので Holm はかけない）",
    syms=list(TREND7), kind="D1_fromH1", params=[{"win": WIN, "cap": CAP}], n_tests=2, warmup=MIN_HIST + WIN, B=1000,
    null_kind="circ_shift", null_min_shift=MIN_SHIFT,
    discarded="約4: σ²（分散）の逆数（Moreira–Muir 原典。上限に張り付きやすいので σ に）、窓 60 日（Q205 と同じで新しさが無い）、FX8 も含める（買い持ちの向きが恣意的）、Parkinson σ（Q207 系と重なる）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2008〜2026-06（油・指数は 2011-09〜）で締め切り前。規則は固定で相場観は使わない",
    delegation="設計とコードは Opus（2026-10-16）。実行と記録は Sonnet（怪しければ escalate）。結論ではなく JSON のパス・前後半の Sharpe 3 本（調整・買い持ち・帰無中央値）と z を返させ、本体が確かめる",
    source="Moreira・Muir 2017「Volatility-Managed Portfolios」（J. Finance）、Cederburg ほか 2020（JFE・標本外では多くが勝てない）、[[ブログQuanterLab2026b-2_SPY全期間ではボラティリティターゲティングが買い持ちをわずかに上回り200日線は最大下落を抑える]]、"
           "知見「日足順張りの建玉を直前60日の実現ボラの逆数で規模調整すると年ごとのシャープが約0.09上がる」（Q205・順張りの方）、"
           "知見「下落の速さでは200日線とボラティリティターゲティングの優劣が分かれず併用はほぼ常に浅い」。種: ローカル LLM アイデア 2026-10-15",
    data="TREND7 D1_fromH1（XAUUSD・XAGUSD 2008〜、WTI・UKOIL・US500・USTECH 2011-09〜、BTCUSD 2017〜、いずれも 2026-06 まで）。油・指数の 2011-09〜2012-01 の空白（gap 行）は損益から除く",
    measure="等加重束の年率シャープ（252）を調整・買い持ち・帰無で前後半に。記述: 銘柄ごとのシャープ差、最大下落、平均の重み、売買回転",
    null_desc=f"銘柄ごと・期間ごとに w 列を循環シフト（k∈[{MIN_SHIFT}, n−{MIN_SHIFT}]）B 回 → 束のシャープの帰無分布 → z",
    prior_art="WebSearch 2026-10-16・standard・検索語 \"volatility-managed portfolios commodities equity index futures bitcoin buy and hold Sharpe out-of-sample Moreira Muir replication\"。"
              "見つかったもの: Cederburg・O'Doherty・Wang・Yan 2020（JFE・103 系列の標本外で多くが勝てない）、Strathclyde の商品先物のボラ管理（Journal of Futures Markets 2021）、Lehigh の COWY 論文。"
              "未確認: 金・銀・原油・株価指数 CFD・BTC の 7 銘柄束で、重みの分布を保つ循環シフト帰無に対してタイミングの価値を前後半で測った形は見当たらない（移植）",
    batch="4案一括生成（ローカル LLM アイデアの選別 2026-10-16）", designer="Opus", coder="Claude（Opus）",
    settings={"win": WIN, "cap": CAP, "min_hist": MIN_HIST, "rebal": REBAL, "split_year": SPLIT_YEAR, "per_year": 252,
              "cost": "COST_RT（TREND7 として。BTCUSD は 40USD 固定＝価格水準で bp が変わる）"},
)


def weights(d):
    r = d["ret"].astype(float)
    if "gap" in d:
        r = r.where(~d["gap"].astype(bool))
    s20 = r.rolling(WIN, min_periods=WIN).std()
    tgt = s20.expanding(min_periods=MIN_HIST).median()
    w = np.minimum(tgt / s20, CAP).fillna(0.0).values
    # 重みの更新は REBAL 本ごと（その間は直前の値を持ち続ける。毎日の小さな売買コストを避ける）
    keep = np.arange(len(w)) % REBAL == 0
    w = pd.Series(np.where(keep, w, np.nan)).ffill().fillna(0.0).values
    return w


def sym_pnl(d, s, w, gross=False):
    c = d["close"].values.astype(float)
    n = pnl_bp(w, c, np.zeros(len(c)) if gross else cost_bp_oneway(s, c))
    if "gap" in d:
        n = np.where(d["gap"].values, np.nan, n)
    return n


def basket_sharpe(tab, y0, y1):
    d = tab[(tab.index.year >= y0) & (tab.index.year < y1)]
    pool = d.mean(axis=1, skipna=True).dropna().values
    return sharpe_ann(pool, 252), pool


def run(args, rng):
    syms, missing = syms_available(SPEC.syms, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="H1_dukascopy")
    dfs = {}; W = {}
    for s in syms:
        d = load_d1(s, args.smoke, rng).reset_index(drop=True)
        w = weights(d)
        first = int(np.argmax(w > 0)) if (w > 0).any() else len(w)
        d = d.iloc[first:].reset_index(drop=True); w = w[first:]
        dfs[s] = d; W[s] = w
    idx = {s: pd.to_datetime(dfs[s]["time"].values) for s in syms}
    obs = pd.concat({s: pd.Series(sym_pnl(dfs[s], s, W[s]), index=idx[s]) for s in syms}, axis=1).sort_index()
    bh = pd.concat({s: pd.Series(sym_pnl(dfs[s], s, np.where(W[s] > 0, 1.0, 0.0)), index=idx[s]) for s in syms}, axis=1).sort_index()
    gro = pd.concat({s: pd.Series(sym_pnl(dfs[s], s, W[s], gross=True), index=idx[s]) for s in syms}, axis=1).sort_index()
    U = obs.index; UY = U.year.values; POS = {s: U.get_indexer(idx[s]) for s in syms}  # 帰無の高速化用
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "main": {}}
    for pn, (y0, y1) in periods.items():
        sh, pool = basket_sharpe(obs, y0, y1)
        shg, _ = basket_sharpe(gro, y0, y1)
        shb, poolb = basket_sharpe(bh, y0, y1)
        null = []
        for _ in range(args.B):
            # 高速化（2026-10-17・計算は元と同一: 日付の和集合の行列に入れて銘柄平均 → 期間で切る → 全欠損の行を落とす）
            arr = np.full((len(U), len(syms)), np.nan)
            for j, s in enumerate(syms):
                yrs = idx[s].year; m = (yrs >= y0) & (yrs < y1); ii = np.where(m)[0]; w2 = W[s].copy(); n = len(ii)
                if n > 2 * MIN_SHIFT:
                    k = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT + 1)); w2[ii] = np.roll(W[s][ii], k)
                arr[POS[s], j] = sym_pnl(dfs[s], s, w2)
            sub = arr[(UY >= y0) & (UY < y1)]
            ok = ~np.all(np.isnan(sub), axis=1)
            null.append(sharpe_ann(np.nanmean(sub[ok], axis=1), 252))
        z, pct = z_of(sh, np.array(null, float)) if null else (None, None)
        dsub = obs[(obs.index.year >= y0) & (obs.index.year < y1)]; bsub = bh[(bh.index.year >= y0) & (bh.index.year < y1)]
        res["main"][pn] = {"sharpe_vm": fmt(sh), "sharpe_vm_gross": fmt(shg), "sharpe_bh": fmt(shb), "z": fmt(z), "pct": fmt(pct),
                           "null_median": fmt(float(np.median(null))) if null else None, "null_B": len(null),
                           "mdd_vm_bp": fmt(max_drawdown(pool)), "mdd_bh_bp": fmt(max_drawdown(poolb)), "n_days": int(len(pool)),
                           "per_sym_sharpe": {s: {"vm": fmt(sharpe_ann(dsub[s].dropna().values, 252)),
                                                  "bh": fmt(sharpe_ann(bsub[s].dropna().values, 252))} for s in syms}}
    res["weights"] = {s: {"mean": fmt(float(W[s].mean())), "share_at_cap": fmt(float(np.mean(W[s] >= CAP - 1e-9))),
                          "turnover_per_day": fmt(float(np.mean(np.abs(np.diff(W[s])))))} for s in syms}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    res["multiple_comparisons"] = "判定は前後半 2 本の交差（両方を要求）。銘柄別・最大下落は記述"
    return res


def judge(res):
    m = res["main"]
    vals = [m.get(k, {}).get(x) for k in ("pre", "post") for x in ("sharpe_vm", "sharpe_bh", "z")] + [m.get("all", {}).get("z")]
    if any(v is None for v in vals):
        return "未確定: 計算できない（期間・銘柄の不足か帰無の退化）"
    if all(m[k]["sharpe_vm"] > m[k]["sharpe_bh"] and m[k]["z"] >= 2 for k in ("pre", "post")):
        return "支持: 前後半とも調整後シャープが買い持ちより高く、帰無に対し z≥2"
    if m["all"]["z"] < 1:
        return "棄却: 全期間の z<1（調整の効きは重みの分布で説明でき、ボラのタイミングの価値は見えない）"
    return "未確定"


def main():
    av = sys.argv[1:]; script = os.path.basename(__file__)
    if "--readme" in av:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型"))
        print("wrote README.md"); return
    if "--idea-row" in av:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE)).replace("fe_core Runner 型", "fe_core 土台を直接使う型")); return
    args = parse_args(default_B=SPEC.B)
    rng = np.random.default_rng(args.seed)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{SPEC.qid}" if args.smoke else SPEC.qid
    with open(os.path.join(out, f"{pre}_spec_{ts}.json"), "w", encoding="utf-8") as fh:
        json.dump({"qid": SPEC.qid, "registered": ts, "B": args.B, "seed": args.seed, **SPEC.as_dict()}, fh, ensure_ascii=False, indent=1)
    res = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    write_result(SPEC.qid, res, args.smoke, here=HERE)
    print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
