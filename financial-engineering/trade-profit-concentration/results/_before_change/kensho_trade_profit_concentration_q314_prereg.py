#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q314: 順張りの利益は少数の取引に集中するか — 最良 1 取引の総利益比を、同じ取引数・保有期間で入る時期だけランダムにした帰無と比べる（Q313-C1）
================================================================================
事前登録の正本は下の SPEC。測る前に固定（2026-10-17・Opus）。
実行: python3 kensho_trade_profit_concentration_q314.py（B=500）／ --smoke --B 5 ／ --readme ／ --idea-row
"""
import datetime as _dt
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (Spec, SYMS, COST_RT, parse_args, write_result, syms_available, health, load_d1, load_h1,  # noqa: E402
                     tsmom_pos, sma_pos, fmt)
from fe_core.readme import render_readme, render_idea_row  # noqa: E402

CELLS = {"D1": {"tsmom": 60, "sma": 50}, "H1": {"tsmom": 24, "sma": 50}}

SPEC = Spec(
    qid="Q314",
    question="順張りの利益は少数の取引に集中するか: 最良 1 取引の総利益比を、同じ取引数・保有期間で入る時期だけランダムにした帰無と比べる（Q313-C1・ブログの 91% は普通か異常か）",
    hypothesis="15 銘柄 × 2 規則（TSMOM・SMA、常に ±1）× 2 足（日足 D1: TSMOM60・SMA50／H1: TSMOM24・SMA50）で、取引（同じ向きの連続）ごとの純損益を出し、"
               "S1 = 最良 1 取引 ÷ 勝ち取引の合計（総利益）を測る。帰無は取引の『保有本数と向き』の組を並べ替えて時間軸に敷き直す（取引数・保有期間の分布・露出は同じ、入る時期だけランダム）。"
               "順張りは帰無より少数の大勝ちに集中する（S1 の帰無百分位が高い）",
    reject_if="足ごとに 30 セル（15 銘柄 × 2 規則）の『S1 の帰無百分位』を集計。支持: D1 か H1 のどちらかで、百分位の平均 ≥ 0.75 かつ 0.5 超のセル数の符号検定（片側）p<0.05。"
              "棄却: D1・H1 の両方で百分位の平均 < 0.6。ほか → 未確定。（2 つの足のどちらかを要求するので、符号検定の p は 2 倍して読む＝Bonferroni）",
    syms=list(SYMS), kind="D1_fromH1 と H1_dukascopy", params=[{"freq": f, "rule": r, "n": n} for f, d in CELLS.items() for r, n in d.items()],
    n_tests=2, B=500, null_kind="none",
    discarded="約3: ボリンジャー併用（ブログの規則は非公開で再現できない）、15 分足（XAUUSD の M15 は yahoo で別ソース）、総利益を『純損益』にする定義（合計が負のとき比が定義できない）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2008〜2026-06 で締め切り前。規則は固定で相場観は使わない",
    delegation="設計・コード・実行・解釈は Opus 本体（2026-10-17）。委託なし",
    source="[[ブログZenn2026hiro-2_XAUUSD15分足のトレンド規則は利益の91パーセントが1取引で残り116取引は1.11Rだけだった]]、知見 Q230（日次の上位 1% への集中は帰無よりむしろ低い）",
    data="15 銘柄 D1_fromH1（2008〜2026-06）と H1_dukascopy（同）。gap 行はリターン 0 扱い",
    measure="セルごとの S1・最良除外後の合計 R_ex・取引数、S1 の帰無百分位。足ごとに百分位の平均・符号検定。記述: R_ex<0 の割合、XAUUSD の値",
    null_desc="取引の（保有本数, 向き）の列をランダムに並べ替えて先頭から敷き直す B 回 → 同じ損益計算で S1 の帰無分布 → 実際の百分位（帰無 < 実際 の割合 + 同順位の半分）",
    prior_art="WebSearch 2026-10-17・standard・\"trend following profits concentrated in few trades share of total profit largest trade versus random entry test outlier dependence\"。"
              "Zarattini・Pagani・Wilcox（株の順張りは少数の大勝ち頼み）、TradingView『Largest winner as % of gross profit』、MQL5 のブログ。帰無との比較は未確認",
    batch="単発（接続 Q313 の通過案）", designer="Opus", coder="Claude（Opus）",
    settings={"cells": CELLS, "cost": "段階1 COST_RT（片道）を取引ごとに入りと出で 2 回"},
)


def trades_from_pos(pos):
    """pos: ±1/0（t の終値で決定）。保有は t+1 から。返り値: 各取引の (開始の足, 本数, 向き)。"""
    hold = np.r_[0.0, pos[:-1]]
    out = []; i = 0; n = len(hold)
    while i < n:
        if hold[i] == 0:
            i += 1; continue
        j = i
        while j + 1 < n and hold[j + 1] == hold[i]:
            j += 1
        out.append((i, j - i + 1, int(hold[i]))); i = j + 1
    return out


def trade_pnls(cum, starts, lens, dirs, cost2):
    """cum: 0 始まりの累積リターン [bp]（長さ n+1）。各取引の純損益 = 向き × 区間の和 − 往復コスト。"""
    s = np.asarray(starts); l = np.asarray(lens); d = np.asarray(dirs)
    return d * (cum[s + l] - cum[s]) - cost2


def s1(p):
    g = p[p > 0].sum()
    return (p.max() / g) if g > 0 else np.nan


def cell(df, sym, rule, n, rng, B):
    c = df["close"].values.astype(float)
    r = np.r_[0.0, c[1:] / c[:-1] - 1] * 1e4
    if "gap" in df:
        r = np.where(df["gap"].values, 0.0, r)
    cum = np.r_[0.0, np.cumsum(r)]
    pos = tsmom_pos(c, n) if rule == "tsmom" else sma_pos(c, n)
    tr = trades_from_pos(pos)
    if len(tr) < 10:
        return None
    st, ln, dr = map(np.array, zip(*tr))
    cost2 = 2 * (COST_RT.get(sym, 0.0) / 2) / np.median(c) * 1e4
    p = trade_pnls(cum, st, ln, dr, cost2)
    obs = s1(p); best = p.max(); tot = p.sum()
    first = st[0]; total_len = ln.sum()
    null = []
    for _ in range(B):
        k = rng.permutation(len(ln))
        l2, d2 = ln[k], dr[k]
        s2 = first + np.r_[0, np.cumsum(l2)[:-1]]
        null.append(s1(trade_pnls(cum, s2, l2, d2, cost2)))
    null = np.array(null); null = null[np.isfinite(null)]
    pct = float((null < obs).mean() + 0.5 * (null == obs).mean()) if len(null) and np.isfinite(obs) else np.nan
    return {"n_trades": int(len(p)), "S1": fmt(obs), "best_bp": fmt(best), "total_bp": fmt(tot), "R_ex_bp": fmt(tot - best),
            "null_S1_median": fmt(float(np.median(null))) if len(null) else None, "pct": fmt(pct), "mean_len": fmt(float(ln.mean())),
            "covered_bars": int(total_len)}


def sign_p(k, n):
    """片側の二項（p=0.5）: P(X ≥ k)。"""
    return float(sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def run(args, rng):
    syms, missing = syms_available(SPEC.syms, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="H1_dukascopy")
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "cells": {}, "summary": {}}
    for freq, rules in CELLS.items():
        pcts = []
        for s in syms:
            df = load_d1(s, args.smoke, rng) if freq == "D1" else load_h1(s, args.smoke, rng)
            for rule, n in rules.items():
                out = cell(df.reset_index(drop=True), s, rule, n, rng, args.B)
                res["cells"][f"{freq}|{rule}|{s}"] = out
                if out and out["pct"] is not None:
                    pcts.append(out["pct"])
        pcts = np.array(pcts, float)
        k = int((pcts > 0.5).sum())
        rex = [v["R_ex_bp"] for kk, v in res["cells"].items() if kk.startswith(freq) and v]
        res["summary"][freq] = {"n_cells": int(len(pcts)), "pct_mean": fmt(float(pcts.mean())) if len(pcts) else None, "n_above_half": k,
                                "sign_p_one_sided": fmt(sign_p(k, len(pcts))) if len(pcts) else None,
                                "share_R_ex_negative": fmt(float(np.mean([x < 0 for x in rex]))) if rex else None,
                                "S1_median": fmt(float(np.nanmedian([v["S1"] for kk, v in res["cells"].items() if kk.startswith(freq) and v and v["S1"] is not None])))}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    res["multiple_comparisons"] = "足 2 つのどちらかで支持 → 符号検定の p を 2 倍して 0.05 と比べる（Bonferroni）。セル別は記述"
    return res


def judge(res):
    sm = res["summary"]
    if any(sm[f]["pct_mean"] is None for f in CELLS):
        return "未確定: 計算できない"
    sup = [f for f in CELLS if sm[f]["pct_mean"] >= 0.75 and min(1.0, 2 * sm[f]["sign_p_one_sided"]) < 0.05]
    if sup:
        return f"支持: {','.join(sup)} で S1 の帰無百分位の平均 ≥ 0.75 かつ符号検定（×2）p<0.05"
    if all(sm[f]["pct_mean"] < 0.6 for f in CELLS):
        return "棄却: D1・H1 とも S1 の帰無百分位の平均 < 0.6（順張りの利益の集中はランダムな時期と変わらない）"
    return "未確定"


def main():
    av = sys.argv[1:]; script = os.path.basename(__file__)
    if "--readme" in av:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型"))
        print("wrote README.md"); return
    if "--idea-row" in av:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE))); return
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
