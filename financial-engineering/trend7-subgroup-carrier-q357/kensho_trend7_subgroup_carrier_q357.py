#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q357 — TREND7 の中で収益源を担っているのは商品（XAU/XAG/WTI/UKOIL）か、
株価指数＋BTC（US500/USTECH/BTCUSD）か。D1 TSMOM(L=60)で両部分群の年単位 bp を比べる。
実行: --smoke --B 5／--B 500／--readme"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, TREND7, by_year_stats, fmt  # noqa: E402

SEAL_END = "2024-07-01"
COMMODITIES4 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL"]
EQUITY_BTC3 = ["US500", "USTECH", "BTCUSD"]


class SealedRunner(Runner):
    def _load(self, sym, smoke, rng):
        df = super()._load(sym, smoke, rng)
        return df[df["time"] < pd.Timestamp(SEAL_END)].reset_index(drop=True)


def extra_subgroups(cells, spec):
    out = {}
    periods = {"all": (0, 9999), "pre": (0, spec.split_year), "post": (spec.split_year, 9999)}
    for name, grp in [("commodities4", COMMODITIES4), ("equity_btc3", EQUITY_BTC3)]:
        for pn, (y0, y1) in periods.items():
            d = cells[(cells["sym"].isin(grp)) & (cells["year"] >= y0) & (cells["year"] < y1) & (cells["param"] == spec.main_param)]
            if d.empty:
                continue
            bys = by_year_stats(d, "pnl_net", y0=y0, y1=y1)
            byg = by_year_stats(d, "pnl_gross", y0=y0, y1=y1)
            out[f"{name}_{pn}"] = {"n_years": bys["n_years"], "bp_net": fmt(bys["mean"]), "t_year_net": fmt(bys["t"]),
                                   "bp_gross": fmt(byg["mean"]), "t_year_gross": fmt(byg["t"])}
    return out


def carrier_judge(res, spec):
    e = res.get("extra", {})
    c_all = e.get("commodities4_all", {})
    k_all = e.get("equity_btc3_all", {})
    if not c_all or not k_all or c_all.get("bp_net") is None or k_all.get("bp_net") is None:
        return "未確定: 部分群の統計が計算できない"
    if c_all["bp_net"] > 0 and (c_all.get("t_year_net") or 0) >= 2 and (k_all.get("bp_net") or 0) <= 0:
        return "支持: 商品 4 が担い手（商品は年単位 t≥2・bp>0、株＋BTC は bp≤0）"
    if k_all["bp_net"] > 0 and (k_all.get("t_year_net") or 0) >= 2 and (c_all.get("bp_net") or 0) <= 0:
        return "支持: 株＋BTC 3 が担い手（株＋BTC は年単位 t≥2・bp>0、商品は bp≤0）"
    if c_all["bp_net"] > 0 and k_all["bp_net"] > 0:
        return "未確定: 両部分群とも bp>0（担い手の切り分けは強くはできない）"
    return "棄却: どちらも bp>0 かつ t≥2 を満たさない"


SPEC = Spec(
    qid="Q357",
    question="TREND7 D1 TSMOM(L=60) の収益は商品 4（XAU/XAG/WTI/UKOIL）と株＋BTC 3（US500/USTECH/BTC）のどちらが担うか",
    hypothesis="同じ合図規則で TREND7 全体と 2 部分群の年単位 bp を比べる。担い手は『部分群 A は t≥2 かつ bp>0、部分群 B は bp≤0』のとき特定できる",
    reject_if="どちらか一方が t≥2 かつ bp>0 で他方が bp≤0 → その群が担い手として支持。両方が bp>0 → 未確定（分散源）。両方が bp≤0 → 棄却。n_tests=2 の Holm で主判定は TREND7 全体",
    syms=list(TREND7), kind="D1_fromH1",
    params=[{"L": 60}], main_param=0, n_tests=2, warmup=60,
    B=500, split_year=2017, start="2012-02-01",
    null_kind="circ_shift", null_min_shift=120,
    discarded="FX8 や全部位分割（4+3+8）は本件の 2 群分割と目的が違うため別案（Q355／既存の Q230）",
    delegation="なし",
    source="戦略台帳 S01、知見 Q230（all15 で片方 t<2）・Q261（trend7 の H4 不支持）",
    measure="TREND7 全体の年単位 bp・t・Sharpe、2 部分群の年単位 bp・t（コスト 0／段階1）、期間別の割れ方",
    null_desc="合図の循環シフト（min_shift=120）B=500 → 全体と部分群の年単位 bp の帰無",
    prior_art="Hurst, Ooi & Pedersen (2017) は商品・指数・金利・為替で TSMOM が効くとした。本件は商品 vs 指数＋BTC の切り分け",
    batch="/lab-plan 10 案一括（2026-10-20）",
    data="TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）",
)


def strategy(df, p, sym):
    return tsmom_pos(df["close"].values, p["L"])


if __name__ == "__main__":
    SealedRunner(SPEC, strategy, judge=carrier_judge, summarize_extra=extra_subgroups, here=HERE).execute()
