# -*- coding: utf-8 -*-
"""Q537: S23 の頑健性の確認（窓の面・循環シフト帰無の帯・コスト 2 倍／3 倍）。事前登録_q537.md。S23 の規則は変えない。
run_q529.py の daily_series・backtest・tsmom・combine をそのまま使う（同じ足・執行・コスト）。
使い方: python3 run_q537.py --h1 DIR --out DIR"""
import argparse, json, os
import numpy as np, pandas as pd
import run_q529 as Q
import crypto_core as C

GRID = [10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150, 180, 250]
DEV = (pd.Timestamp("2018-01-01"), pd.Timestamp("2025-10-01"))
FIN = (pd.Timestamp("2025-10-01"), pd.Timestamp("2026-10-01"))
B = 200


def st(p, win):
    p = p[(p.index >= win[0]) & (p.index < win[1])]
    eq = (1 + p).cumprod(); dd = float((eq / eq.cummax() - 1).min())
    sh = float(p.mean() / p.std() * np.sqrt(252)) if p.std() > 0 else 0.0
    return dict(sharpe=sh, max_dd=dd, cagr=float(eq.iloc[-1] ** (252 / len(p)) - 1), total=float(eq.iloc[-1] - 1), t=C.tstat(p))


def run_cell(bs, L, mult, rng, null=True):
    half = {c: Q.HALF[c] * mult for c in bs}
    pos = {c: Q.tsmom(bs[c], L) for c in bs}
    p = Q.combine([Q.backtest(bs[c], pos[c], half[c]) for c in bs])
    out = {"dev": st(p, DEV), "final": st(p, FIN)}
    m = (bs["BTC"].index >= DEV[0]) & (bs["BTC"].index < DEV[1])
    out["in_market"] = {c: float(pos[c][(bs[c].index >= DEV[0]) & (bs[c].index < DEV[1])].mean()) for c in bs}
    if null:
        ns = []
        for _ in range(B):
            parts = []
            for c in ["BTC", "ETH"]:
                n = len(pos[c]); s = rng.integers(30, n - 30)
                parts.append(Q.backtest(bs[c], np.roll(pos[c], s), half[c]))
            ns.append(st(Q.combine(parts), DEV)["sharpe"])
        ns = np.array(ns)
        out["null"] = {"q05": float(np.quantile(ns, .05)), "q50": float(np.median(ns)), "q95": float(np.quantile(ns, .95)),
                       "mean": float(ns.mean()), "sd": float(ns.std(ddof=1)), "z": float((out["dev"]["sharpe"] - ns.mean()) / ns.std(ddof=1))}
    return out, p


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h1", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    bs = {c: Q.daily_series(a.h1, c) for c in ["BTC", "ETH"]}
    for c in bs:
        bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
    rng = np.random.default_rng(C.SEED + 537)
    res = {"grid": GRID, "B": B, "dev": [str(DEV[0].date()), str(DEV[1].date())], "final_describe_only": [str(FIN[0].date()), str(FIN[1].date())], "cells": {}, "buy_hold": {}}
    for mult in (1, 2, 3):
        half = {c: Q.HALF[c] * mult for c in bs}
        bh = Q.combine([Q.backtest(bs[c], np.ones(len(bs[c])), half[c]) for c in bs])
        res["buy_hold"][f"x{mult}"] = {"dev": st(bh, DEV), "final": st(bh, FIN)}
        res["cells"][f"x{mult}"] = {}
        for L in GRID:
            o, _ = run_cell(bs, L, mult, rng, null=(mult == 1))
            res["cells"][f"x{mult}"][L] = o
    # 再現の確認
    c60 = res["cells"]["x1"][60]["dev"]; res["reproduce_q529"] = {"sharpe": c60["sharpe"], "max_dd": c60["max_dd"], "expected": {"sharpe": 0.8822, "max_dd": -0.6135}}
    # 判定
    bh1 = res["buy_hold"]["x1"]["dev"]; cells = res["cells"]["x1"]
    n_sh = sum(cells[L]["dev"]["sharpe"] > bh1["sharpe"] for L in GRID); n_dd = sum(cells[L]["dev"]["max_dd"] > bh1["max_dd"] for L in GRID)
    q1 = "台地" if (n_sh >= 10 and n_dd >= 10) else ("尖り" if (n_sh <= 6 or n_dd <= 6) else "中間")
    n_band = sum(cells[L]["dev"]["sharpe"] > cells[L]["null"]["q95"] for L in GRID)
    q2 = "時刻に意味がある" if n_band >= 7 else ("利益の源は保有の量（β）で時刻の当たりではない" if n_band <= 3 else "どちらとも言えない")
    q3 = {}
    for mult in (2, 3):
        bhm = res["buy_hold"][f"x{mult}"]["dev"]; c = res["cells"][f"x{mult}"][60]["dev"]
        q3[f"x{mult}"] = bool(c["sharpe"] > bhm["sharpe"] and c["max_dd"] > bhm["max_dd"])
    res["verdict"] = {"q1_plateau": {"n_sharpe_gt_bh": int(n_sh), "n_dd_shallower": int(n_dd), "answer": q1},
                      "q2_band": {"n_above_null95": int(n_band), "answer": q2}, "q3_cost": q3}
    json.dump(res, open(os.path.join(a.out, "result_q537.json"), "w"), ensure_ascii=False, indent=1, default=str)
    rows = []
    for mult in (1, 2, 3):
        for L in GRID:
            o = res["cells"][f"x{mult}"][L]
            rows.append({"cost_mult": mult, "L": L, "sharpe": o["dev"]["sharpe"], "max_dd": o["dev"]["max_dd"], "cagr": o["dev"]["cagr"], "t": o["dev"]["t"],
                         "in_btc": o["in_market"]["BTC"], "in_eth": o["in_market"]["ETH"],
                         "null_q05": o.get("null", {}).get("q05"), "null_q50": o.get("null", {}).get("q50"), "null_q95": o.get("null", {}).get("q95"), "null_z": o.get("null", {}).get("z"),
                         "final_sharpe": o["final"]["sharpe"], "final_max_dd": o["final"]["max_dd"], "final_total": o["final"]["total"],
                         "bh_sharpe": res["buy_hold"][f"x{mult}"]["dev"]["sharpe"], "bh_max_dd": res["buy_hold"][f"x{mult}"]["dev"]["max_dd"]})
    pd.DataFrame(rows).to_csv(os.path.join(a.out, "surface_q537.csv"), index=False)
    print(json.dumps({"reproduce": res["reproduce_q529"], "verdict": res["verdict"], "bh": {k: {x: round(v["dev"][x], 3) for x in ("sharpe", "max_dd")} for k, v in res["buy_hold"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
