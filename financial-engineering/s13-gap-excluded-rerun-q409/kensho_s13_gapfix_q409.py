#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q409 S13 見直し: Q400（月替わり）・Q402（FOMC 偶数週）を、データの穴を跨ぐ足（前の足から 168h 超・load_d1 の gap 列）の合図を 0 にして再計算する。

計画（測る前に固定・2026-10-22 Opus）:
- 問い: Q400・Q402 の判定は穴跨ぎ足（US500/USTECH 2011-09-22〜2012-01-16、NLD25 2016〜17 の 5 区間など）を除いても変わらないか。
- 変えるのは 1 点だけ: 足 j が gap（前の足から 168h 超）なら pos[j−1]=0（その足のリターンを取らない）。等金額・規程モード・帰無（循環シフトの後にも同じ足を 0）すべてに効かせる。
- 変えないもの: 元の SPEC（仮説・期間・設定・main・n_tests=2・B=500・seed・判定規則 judge_gate の 3 分岐）。元の strategy をそのまま import して包む。
- 判定規則（元と同じ）: 支持＝規程モードの前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額の全期間 z≥2。棄却＝等金額の全期間 z<1 または規程モード t_all<0。ほか未確定。
- 事前登録からの変更点: 穴跨ぎ足の除外（事後に見つかったデータの欠陥の修正。判定規則は変えない）。捨てた案: 1（穴の銘柄・年を丸ごと落とす＝情報を捨てすぎる）。
- 知識の締め切り: およそ 2026-06。委託: なし（Opus が実行・解釈）。
実行: python3 kensho_s13_gapfix_q409.py --target q400|q402 [--B 500]
"""
import dataclasses
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(FE, "..", "tools"))
sys.path.insert(0, os.path.join(FE, "_s1x_common"))
from fe_core import circ_shift  # noqa: E402
import s1x as X  # noqa: E402

TARGETS = {
    "q400": os.path.join(FE, "s13-idx13-turn-of-month-q400", "kensho_s13_idx13_tom_q400.py"),
    "q402": os.path.join(FE, "s13-idx13-fomc-cycle-even-weeks-q402", "kensho_s13_fomc_cycle_q402.py"),
}


def _import(path, name):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


def _gap_zero(pos, df):
    """足 j が gap なら pos[j−1]=0。"""
    pos = np.asarray(pos, float).copy()
    if "gap" in df:
        g = np.flatnonzero(df["gap"].values)
        g = g[g >= 1]
        pos[g - 1] = 0.0
    return pos


def main():
    av = sys.argv[1:]
    tgt = av[av.index("--target") + 1] if "--target" in av else None
    if tgt not in TARGETS:
        sys.exit("--target q400|q402 を指定")
    del sys.argv[sys.argv.index("--target"):sys.argv.index("--target") + 2]
    m = _import(TARGETS[tgt], f"orig_{tgt}")
    spec = dataclasses.replace(
        m.SPEC, qid=f"Q409_{tgt.upper()}",
        question="[Q409 見直し: 穴跨ぎ足（前の足から 168h 超）の合図を 0] " + m.SPEC.question,
        delegation="なし（Opus が実行・解釈）",
        settings={**m.SPEC.settings, "gap_rule": "足 j が gap（dt_prev_h>168）なら pos[j−1]=0。帰無は循環シフトの後に同じ規則", "orig_qid": m.SPEC.qid},
    )

    def strategy(df, p, sym):
        return _gap_zero(m.strategy(df, p, sym), df)

    def null(rng, pos, df, p, sym):
        return _gap_zero(circ_shift(rng, pos, min_shift=spec.null_min_shift), df)

    extra = m.make_extra(spec) if hasattr(m, "make_extra") else None
    holder = getattr(m, "RUNNER", None)
    X.run_main(spec, strategy, HERE, min_syms=10, null=null, summarize_extra=extra, runner_holder=holder)


if __name__ == "__main__":
    main()
