#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q362 — TREND7 D1 TSMOM(L=60) のコスト分岐点。段階1コストの {0, 0.5, 1, 2, 3}倍で
純損益がゼロを跨ぐ倍率を測る。本番で許される最大コストの目安（戦略台帳 S01 の判定基準）。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, TREND7, pnl_bp  # noqa: E402

SEAL_END = "2024-07-01"


class SealedRunner(Runner):
    def _load(self, sym, smoke, rng):
        df = super()._load(sym, smoke, rng)
        return df[df["time"] < pd.Timestamp(SEAL_END)].reset_index(drop=True)

    def _cells(self, dfs, rng, null=False):
        """コストを param ごとに倍率で変える。pnl_gross は共通（倍率 0 と同じ）。"""
        frames = []
        for sym, df in dfs.items():
            c = df["close"].values
            cb_unit = self._cost(sym, c)  # 片道の bp
            zero = np.zeros(len(c))
            for i, p in enumerate(self.spec.params):
                pos = np.asarray(self.strategy(df, p, sym), float)
                if len(pos) != len(c):
                    raise ValueError(f"strategy の返り値の長さが違う: {sym} {len(pos)} != {len(c)}")
                if null:
                    pos = self._null_pos(rng, pos, df, p, sym)
                mult = float(p.get("cost_mult", 1.0))
                cb = cb_unit * mult
                g = pnl_bp(pos, c, zero)
                n = pnl_bp(pos, c, cb)
                if self.spec.warmup:
                    g[: self.spec.warmup + 1] = np.nan
                    n[: self.spec.warmup + 1] = np.nan
                frames.append(pd.DataFrame({"time": df["time"].values, "year": df["year"].values, "sym": sym, "param": i,
                                            "gap": df["gap"].values if "gap" in df else False,
                                            "pnl_gross": g, "pnl_net": n, "exp": np.abs(np.r_[0.0, pos[:-1]])}))
        return pd.concat(frames, ignore_index=True)


def breakeven_judge(res, spec):
    s = res["summary"]
    # main_group = "all"（syms != SYMS）
    labels = {0: "0x", 1: "0.5x", 2: "1x", 3: "2x", 4: "3x"}
    rows = []
    for i, lab in labels.items():
        a = s.get(f"p{i}_all_all")
        if a and a.get("bp_net") is not None:
            rows.append((lab, a["bp_net"], a.get("t_year")))
    if not rows:
        return "未確定: 統計が計算できない"
    pos_mults = [lab for lab, bp, t in rows if bp > 0]
    if "3x" in pos_mults:
        return "支持: 3× 段階1コストでも全期間 bp_net>0（本番のコスト余裕が大きい）"
    if "2x" in pos_mults:
        return "支持（限定）: 2× 段階1コストでも bp_net>0。3× では消える"
    if "1x" in pos_mults:
        return "未確定: 段階1コストでは bp_net>0 だが 2× で消える（本番のコスト許容がきつい）"
    return "棄却: 段階1コストで既に bp_net≤0（本件は商用化のコスト許容が無い）"


SPEC = Spec(
    qid="Q362",
    question="TREND7 D1 TSMOM(L=60) は段階1コストの何倍までコスト後に正か（本番で許されるコストの余裕）",
    hypothesis="同じ合図規則でコストを {0, 0.5, 1, 2, 3}× 段階1 の 5 本に広げ、全期間の bp_net の正負を見る。main_param=1×（段階1そのもの）",
    reject_if="3× でも bp>0 → 支持（余裕大）。2× で bp>0・3× で bp≤0 → 支持（限定）。1× で bp>0・2× で bp≤0 → 未確定（きつい）。1× で bp≤0 → 棄却",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 60, "cost_mult": 0.0}, {"L": 60, "cost_mult": 0.5}, {"L": 60, "cost_mult": 1.0},
            {"L": 60, "cost_mult": 2.0}, {"L": 60, "cost_mult": 3.0}],
    main_param=2, n_tests=2, warmup=60,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=120,
    discarded="コスト 5× 以上（現実のスプレッド拡大の目安を超える）",
    delegation="なし",
    source="戦略台帳 S01『粗利が保守的コストの 2 倍を超えない案は切る』、_基盤/CLAUDE.md のコスト 2 段階",
    measure="5 水準の全期間 bp_net・t、ゼロ跨ぎの倍率、取引回数、年単位の値動き",
    null_desc="合図の循環シフト（min_shift=120）B=500 → main=1× の年単位 bp の帰無。帰無は main でのみ計算（コスト倍率は帰無と独立）",
    prior_art="Hurst et al. (2017) は TSMOM のコスト余裕を 2〜4× とした。本件は TREND7 封印前の実測",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    return tsmom_pos(df["close"].values, int(p["L"]))


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=breakeven_judge, here=HERE).execute()
