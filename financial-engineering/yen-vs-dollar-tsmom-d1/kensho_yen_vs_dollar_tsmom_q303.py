#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q303: FX8 日足の TSMOM60 で円の組 3 本の純損益はドルの組 5 本を上回るか（円の組の 4 時間足の知見の日足版）
================================================================================
事前登録の正本は下の SPEC（fe_core の Spec を事前登録の入れ物として使う「土台を直接使う型」）。
種: ローカル LLM（qwen3:8b）のアイデア 2026-10-15「円の組（FX8）のD1足順張りはドルの組（FX8）を上回るか」を Opus が選別・設計。
実行: python3 kensho_yen_vs_dollar_tsmom_q303.py（帰無は組ラベルの全 56 通りで乱数なし）／ --smoke ／ --readme ／ --idea-row
"""
import datetime as _dt
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (Spec, FX8, SPLIT_YEAR, parse_args, write_result, syms_available, health, load_d1,  # noqa: E402
                     tsmom_pos, cost_bp_oneway, pnl_bp, tstat, fmt)
from fe_core.readme import render_readme, render_idea_row  # noqa: E402

L = 60
YEN = ["USDJPY", "EURJPY", "GBPJPY"]
DOLLAR = ["EURUSD", "GBPUSD", "AUDUSD", "USDCHF", "USDCAD"]

SPEC = Spec(
    qid="Q303",
    question="FX8 日足の TSMOM60 で円の組 3 本の純損益はドルの組 5 本を上回るか（円の組の 4 時間足の知見の日足版・組ラベルの全 56 通り帰無）",
    hypothesis="pos[t]=sign(close[t]−close[t−60])（t の終値で決め t+1 から保有）。D = 円の組 3 本の等加重の日次純損益 − ドルの組 5 本の等加重の日次純損益 [bp]、"
               "年ごとの平均を年で平均したもの。D は前後半とも >0 で、8 銘柄から 3 本を『円の組』と呼ぶ全 56 通りの中で上位 5% に入る",
    reject_if="支持: 前半（2008–2016）・後半（2017–2026-06）とも D>0 かつ 正確な p（56 通りのうち D 以上の割合）≤0.05。"
              "棄却: 全期間の D が 56 通りの中央値以下（p>0.5）。それ以外 → 未確定。（前後半の両方を要求する交差なので Holm はかけない）",
    syms=list(FX8), kind="D1_fromH1", params=[{"L": L}], n_tests=2, warmup=L, B=56, null_kind="none",
    discarded="約3: H4 で再確認（既知見の繰り返し）、L の掃引 20/120（判定は 1 本に固定）、通貨強度でのグループ分け（Q291 系と重なる）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2008-02〜2026-06 で締め切り前。規則は固定で相場観は使わない",
    delegation="設計とコードは Opus（2026-10-16）。実行と記録は Sonnet（怪しければ escalate）。結論ではなく JSON のパス・D・正確な p・年ごとの表を返させ、本体が確かめる",
    source="知見「円の組の4時間足に順張りの効きは見えない」・[[ブログZenn2026-3_4時間足の順張りは円の組で再現しドルの組では再現しない]]、"
           "知見「6通貨のドル因子に日足順張りを当てても個別ペアの順張りより強くならず」。種: ローカル LLM アイデア 2026-10-15",
    data="FX8 D1_fromH1（2008-02〜2026-06）。円の組 = USDJPY・EURJPY・GBPJPY、ドルの組 = EURUSD・GBPUSD・AUDUSD・USDCHF・USDCAD（USDJPY は円の組に入れる）",
    measure="D（円の組 − ドルの組、年単位の日平均 bp、段階1コスト後）と年単位 t、各組の純損益・粗利・Sharpe。記述: L=20/120 の D",
    null_desc="8 銘柄から 3 本を円の組とする全 56 通りで D を計算し、実際の D の正確な順位 p（乱数なし）",
    prior_art="WebSearch 2026-10-16・standard・検索語 \"time series momentum yen crosses versus dollar pairs daily FX trend following performance comparison\"。"
              "見つかったもの: CXO Advisory の通貨モメンタム検定、Deutsche Bank 2007 の FX モメンタム資料、QuantInsti の主要通貨のトレンドフォロー（ブログ）。"
              "未確認: 円クロスとドルストレートの順張りの差を、組ラベルの正確な並べ替え帰無で前後半に分けて測った研究は見当たらない（条件の穴）",
    batch="4案一括生成（ローカル LLM アイデアの選別 2026-10-16）", designer="Opus", coder="Claude（Opus）",
    settings={"L_main": L, "L_sub": [20, 120], "yen": YEN, "dollar": DOLLAR, "split_year": SPLIT_YEAR},
)


def sym_daily(dfs, Lx):
    """銘柄ごとの日次の純損益・粗利 [bp]（index=日付）。gap 行は除く。"""
    net, gross = {}, {}
    for s, d in dfs.items():
        c = d["close"].values.astype(float)
        pos = tsmom_pos(c, Lx)
        n = pnl_bp(pos, c, cost_bp_oneway(s, c)); g = pnl_bp(pos, c, np.zeros(len(c)))
        n[: Lx + 1] = np.nan; g[: Lx + 1] = np.nan
        if "gap" in d:
            n = np.where(d["gap"].values, np.nan, n); g = np.where(d["gap"].values, np.nan, g)
        idx = pd.to_datetime(d["time"].values)
        net[s] = pd.Series(n, index=idx); gross[s] = pd.Series(g, index=idx)
    return pd.concat(net, axis=1).sort_index(), pd.concat(gross, axis=1).sort_index()


def yearly_D(tab, yen, dol, y0, y1):
    d = tab[(tab.index.year >= y0) & (tab.index.year < y1)]
    diff = d[yen].mean(axis=1, skipna=True) - d[dol].mean(axis=1, skipna=True)
    by = diff.groupby(diff.index.year).mean().dropna()
    return by


def period_stats(tab, yen, dol, y0, y1):
    by = yearly_D(tab, yen, dol, y0, y1)
    return {"D": float(by.mean()) if len(by) else np.nan, "t": tstat(by.values), "n_years": int(len(by))}


def run(args, rng):
    syms, missing = syms_available(SPEC.syms, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="H1_dukascopy")
    dfs = {s: load_d1(s, args.smoke, rng) for s in syms}
    yen = [s for s in YEN if s in syms]; dol = [s for s in DOLLAR if s in syms]
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "main": {}, "sub": {}}
    if len(yen) != 3 or len(dol) != 5:
        res["machine_verdict"] = "未確定: 銘柄が欠けて組がそろわない"; return res
    net, gross = sym_daily(dfs, L)
    combos = list(itertools.combinations(syms, 3))
    for pn, (y0, y1) in periods.items():
        obs = period_stats(net, yen, dol, y0, y1)
        null = []
        for cmb in combos:
            a = list(cmb); b = [s for s in syms if s not in a]
            null.append(period_stats(net, a, b, y0, y1)["D"])
        null = np.array(null, float)
        p_exact = float(np.mean(null >= obs["D"] - 1e-12))
        sub_g = period_stats(gross, yen, dol, y0, y1)
        dd = net[(net.index.year >= y0) & (net.index.year < y1)]
        res["main"][pn] = {"D_net_bp": fmt(obs["D"]), "t_year": fmt(obs["t"]), "n_years": obs["n_years"], "p_exact": fmt(p_exact),
                           "n_combos": len(combos), "null_median": fmt(float(np.median(null))), "null_max": fmt(float(null.max())),
                           "D_gross_bp": fmt(sub_g["D"]),
                           "yen_net_bp": fmt(float(dd[yen].mean(axis=1).mean())), "dollar_net_bp": fmt(float(dd[dol].mean(axis=1).mean())),
                           "per_sym_net_bp": {s: fmt(float(dd[s].mean())) for s in syms}}
    for Lx in (20, 120):
        n2, _ = sym_daily(dfs, Lx)
        res["sub"][f"L{Lx}"] = {pn: {k: fmt(v) if isinstance(v, float) else v for k, v in period_stats(n2, yen, dol, y0, y1).items()}
                                for pn, (y0, y1) in periods.items()}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    res["multiple_comparisons"] = "判定は L=60 の前後半 2 本の交差（両方を要求）。L=20/120・粗利・銘柄別は記述"
    yr = yearly_D(net, yen, dol, 0, 9999).rename("D_net_bp").reset_index().rename(columns={"index": "year"})
    return res, {"year_D": yr}


def judge(res):
    m = res["main"]
    try:
        pre, post, al = m["pre"], m["post"], m["all"]
        if None in (pre["D_net_bp"], post["D_net_bp"], al["p_exact"]):
            raise KeyError
    except KeyError:
        return "未確定: 計算できない"
    if pre["D_net_bp"] > 0 and post["D_net_bp"] > 0 and pre["p_exact"] <= 0.05 and post["p_exact"] <= 0.05:
        return "支持: 前後半とも D>0 かつ 56 通り中の正確な p≤0.05"
    if al["p_exact"] > 0.5:
        return "棄却: 全期間の D が 56 通りの中央値以下"
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
        json.dump({"qid": SPEC.qid, "registered": ts, "seed": args.seed, **SPEC.as_dict()}, fh, ensure_ascii=False, indent=1)
    out_ = run(args, rng)
    res, csvs = out_ if isinstance(out_, tuple) else (out_, None)
    write_result(SPEC.qid, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
