#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q310: 月次（約 220 か月）に束ねた 15 銘柄の順張りルール群で、並べ替え帰無の下の WRC・SPA の棄却率は名目 5% を超えるか（Q154 の月次版・Q309-C1）
================================================================================
事前登録の正本は下の SPEC。測る前に固定（2026-10-17・Opus）。ルール群・損益・検定の実装は Q154 のスクリプト（wrc-spa-disagreement）を import して再利用する（変更しない）。

使い方（Mac の 1 回 180 秒の制限のため銘柄を分けて走らせ、最後に束ねる）:
  python3 kensho_wrc_spa_monthly_size_q310.py --part EURUSD,GBPUSD,...   （銘柄ごとの帰無と実データの p を results/parts/ に書く）
  python3 kensho_wrc_spa_monthly_size_q310.py --combine                  （parts を束ねて判定し results/Q310_result_*.json）
  --smoke（合成データ）／ --readme ／ --idea-row
"""
import datetime as _dt
import glob
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "wrc-spa-disagreement"))
import kensho_wrc_spa_disagreement_q154 as Q  # noqa: E402
from fe_core import Spec, SYMS, COST_RT, fmt, write_result, health  # noqa: E402
from fe_core.readme import render_readme, render_idea_row  # noqa: E402

BLOCKS = [3, 6, 12]          # 月
BOOT_B = 499
REPS_PER_SYM = 34            # 15 銘柄 × 34 = 510 組の帰無データ
MU0_PERMS = 20
SEED = 20261017
TESTS = ["p_wrc", "p_spa_consistent", "p_spa_conservative"]

SPEC = Spec(
    qid="Q310",
    question="月次（約 220 か月）に束ねた 15 銘柄の順張りルール群で、並べ替え帰無の下の WRC・SPA の棄却率は名目 5% を超えるか（Q154 の月次版・Q309-C1）",
    hypothesis="Q154 と同じ 180 本（TSMOM 参照日数 5〜300 × 買い／売り／両方）の日次純損益を暦月で合計し、真の差 0 の帰無（日次の対数リターンを全期間で並べ替えて価格を作り直し、"
               "並べ替えの期待値 μ0 で中心化）で WRC・SPA(consistent)・SPA(conservative) を当てると、どれかの検定・ブロック長で 5% 棄却率が名目を明らかに超える",
    reject_if="支持（月次ではサイズが崩れる）: 3 検定 × ブロック長 3・6・12 か月の 9 つのどれかで、510 組の帰無データの 5% 棄却率 ≥ 8%。"
              "棄却: 9 つすべて ≤ 7%。ほか → 未確定。（9 つの率の記述で、個々の率への多重比較の補正はしない。8% は 510 組の二項の 95% 上限 ≈ 6.9% の外）",
    syms=list(SYMS), kind="D1_fromH1", params=[{"block": b} for b in BLOCKS], n_tests=9, B=BOOT_B, null_kind="none",
    discarded="約3: 前後半に分けた月次（各約 108 か月で短すぎる）、週次（Q154 の日次と月次の間で新しさが薄い）、Step-SPA（個々のルールの判定は問わない）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2008〜2026-06 で締め切り前。Hansen 2005 の定義は Q154 の実装（記憶による・arch と中心化を照合済み）",
    delegation="設計・実行・解釈は Opus 本体（2026-10-17）。検定の実装は Q154（Fable 設計・Claude コード）を変えずに使う。委託なし",
    source="[[Jedrzejewska2026-2_評価標本150で依存が強いとWRCとSPAとCPAは名目5パーセントのほぼ3倍の14から17パーセントで誤って棄却した]]、"
           "[[Jedrzejewska2026-1_同じ13モデルの比較でWRCとSPAのconsistentとCPAは棄却しSPAのconservativeだけ棄却せず検定の種類で結論が分かれた]]、知見 Q154（日次ではサイズ 3.1〜3.4%）",
    data="15 銘柄 D1_fromH1（2008〜2026-06）。全ルールが定義される日（t>300）から。日次純損益を暦月で合計",
    measure="(a) 帰無データ 510 組での 3 検定 × 3 ブロック長の 5% 棄却率（サイズ）。(b) 実データの月次で 15 銘柄の 3 つの p と判定の割れ方（記述・Q154 の日次と比較）",
    null_desc=f"銘柄ごとに日次対数リターンを全期間で並べ替え→価格を作り直し→180 本の純損益→月次合計→μ0（{MU0_PERMS} 回の並べ替えの月次平均）で中心化。銘柄ごと {REPS_PER_SYM} 組。ブートストラップは循環ブロック（月）B={BOOT_B}",
    prior_art="WebSearch 2026-10-17・standard・\"size distortion White reality check Hansen SPA small sample monthly returns block bootstrap Monte Carlo trading rules\"。"
              "arXiv 2008.02318（ハイブリッド検定のサイズ）、Hsu・Kuan の再検討、arch の SPA 文書。手元のルール群の月次でのサイズは未確認（条件の穴）",
    batch="単発（接続 Q309 の通過案）", designer="Opus", coder="Claude（Opus）",
    settings={"blocks_month": BLOCKS, "boot_B": BOOT_B, "reps_per_sym": REPS_PER_SYM, "mu0_perms": MU0_PERMS, "seed": SEED},
)


def monthly(D, months):
    """D: n×K の日次純損益、months: 長さ n の 'YYYY-MM' → 月数×K の合計。"""
    return pd.DataFrame(D).groupby(months).sum().values


def tests_block(M, rng, l, B=BOOT_B):
    n = M.shape[0]; nb = int(math.ceil(n / l))
    starts = rng.integers(0, n, size=(B, nb))
    S = Q.block_sums(M, l)
    Dstar = S[starts].sum(axis=1) / (nb * l)
    return Q.tests_from_boot(M.mean(axis=0), Dstar, n)


def load(sym, smoke, rng):
    if smoke:
        t = pd.date_range("2008-02-01", periods=4600, freq="B")
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.007, len(t))))
        return t.values, c
    return Q.load_daily(sym)


def part(syms, smoke):
    os.makedirs(os.path.join(HERE, "results", "parts"), exist_ok=True)
    for s in syms:
        rng = np.random.default_rng(SEED + SYMS.index(s) if s in SYMS else SEED)
        t, c = load(s, smoke, rng)
        cost = COST_RT.get(s, 0.0)
        idx = np.arange(Q.LMAX + 1, len(c))
        months = pd.to_datetime(t[idx]).strftime("%Y-%m").values
        D = Q.rule_pnl_matrix(c, cost)[idx]
        Mobs = monthly(D, months)
        obs = {l: {k: v for k, v in tests_block(Mobs, rng, l).items() if k in TESTS} for l in BLOCKS}
        # μ0（帰無の期待月次平均）
        mu0 = np.zeros(D.shape[1])
        for _ in range(MU0_PERMS):
            mu0 += monthly(Q.permuted_pnl(c, cost, idx, rng), months).mean(axis=0)
        mu0 /= MU0_PERMS
        null = {l: {k: [] for k in TESTS} for l in BLOCKS}
        for _ in range(REPS_PER_SYM):
            M0 = monthly(Q.permuted_pnl(c, cost, idx, rng), months) - mu0[None, :]
            for l in BLOCKS:
                r = tests_block(M0, rng, l)
                for k in TESTS:
                    null[l][k].append(r[k])
        rec = {"sym": s, "n_months": int(Mobs.shape[0]), "obs": obs, "null": null, "smoke": bool(smoke)}
        pre = "smoke_" if smoke else ""
        with open(os.path.join(HERE, "results", "parts", f"{pre}Q310_part_{s}.json"), "w") as fh:
            json.dump(rec, fh)
        print("part", s, Mobs.shape)


def combine(smoke):
    pre = "smoke_" if smoke else ""
    fs = sorted(glob.glob(os.path.join(HERE, "results", "parts", f"{pre}Q310_part_*.json")))
    recs = [json.load(open(f)) for f in fs]
    got = [r["sym"] for r in recs]; missing = [s for s in SYMS if s not in got] if not smoke else []
    size = {}
    for l in BLOCKS:
        for k in TESTS:
            ps = np.concatenate([np.array(r["null"][str(l)][k]) for r in recs])
            size[f"L{l}_{k}"] = {"rate": fmt(float((ps < 0.05).mean())), "n": int(len(ps)), "rate_10pct": fmt(float((ps < 0.10).mean()))}
    obs = {}
    for l in BLOCKS:
        rows = {r["sym"]: r["obs"][str(l)] for r in recs}
        dec = {s: tuple(v[k] < 0.05 for k in TESTS) for s, v in rows.items()}
        split = sum(1 for d in dec.values() if len(set(d)) > 1)
        obs[f"L{l}"] = {"n_syms": len(rows), "n_split": split, "n_reject": {k: int(sum(v[k] < 0.05 for v in rows.values())) for k in TESTS},
                        "p": {s: {k: fmt(v[k]) for k in TESTS} for s, v in rows.items()}}
    rates = [v["rate"] for v in size.values()]
    if any(r is None for r in rates) or not rates:
        verdict = "未確定: 計算できない"
    elif max(rates) >= 0.08:
        worst = max(size.items(), key=lambda kv: kv[1]["rate"])
        verdict = f"支持: 月次で名目を超える（最大 {worst[0]} の棄却率 {worst[1]['rate']:.3f}）"
    elif max(rates) <= 0.07:
        verdict = f"棄却: 9 つすべて 7% 以下（最大 {max(rates):.3f}）"
    else:
        verdict = "未確定"
    dh = None if smoke else health([r["sym"] for r in recs], kind="H1_dukascopy")
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "size": size, "observed_monthly": obs,
           "n_months": {r["sym"]: r["n_months"] for r in recs}, "machine_verdict": verdict,
           "multiple_comparisons": "9 つの棄却率の記述（検定 3 × ブロック長 3）。判定は最大値の閾値"}
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    write_result(SPEC.qid, res, smoke, here=HERE)
    print("machine_verdict:", res["machine_verdict"])


def main():
    av = sys.argv[1:]; script = os.path.basename(__file__)
    if "--readme" in av:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型（Q154 の実装を再利用）"))
        print("wrote README.md"); return
    if "--idea-row" in av:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE))); return
    smoke = "--smoke" in av
    if "--part" in av:
        syms = av[av.index("--part") + 1].split(",")
        if not smoke:
            ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            sp = os.path.join(HERE, "results", f"Q310_spec_{ts}.json")
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            if not glob.glob(os.path.join(HERE, "results", "Q310_spec_*.json")):
                json.dump({"qid": SPEC.qid, "registered": ts, **SPEC.as_dict()}, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        part(syms, smoke); return
    if "--combine" in av:
        combine(smoke); return
    print(__doc__)


if __name__ == "__main__":
    main()
