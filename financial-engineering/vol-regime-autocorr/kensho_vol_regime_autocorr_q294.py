#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q294: 15 銘柄 D1 の 1 次自己相関は高ボラ月で低ボラ月より高いか（Loubaris2026-3 の 15 銘柄移植）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-14「15 銘柄 D1 の 1 次自己相関は高ボラ月で低ボラ月より高いか」の行（Q294・10案一括生成 ターミナル版）。
- [[Loubaris2026-3_GARCHで分けた高ボラ局面は衝撃の持続性が高い]]。
- 先行研究チェック（WebSearch 2026-10-14・英語・"daily return autocorrelation volatility regime GARCH shock persistence 15 assets cross-section"）:
  見つかったもの: Cont (2001) "Volatility Clustering" (絶対値・二乗の自己相関は長期)、Zivot GARCH 実務ノート（α+β≒0.99 の高持続）。
  未確認: 15 銘柄 D1 で 60 日実現ボラの月中央値で高/低に分けた日次リターンの 1 次自己相関（絶対値ではなく符号つき）の差を、
  循環シフト帰無 B=1000 と Holm 補正 m=15 で判定する実証は未確認（移植）。

【仮説（測る前に固定）】
H: 15 銘柄のうち、ρ_high − ρ_low > 0 かつ Holm 補正後に有意（m=15、α=0.05）な銘柄が ≥ 4 本（15 の 1/4 弱）→ 支持（高ボラ局面で衝撃持続性が高い）。
H0: Holm 補正後の有意本数が ≤ 1 本 → 棄却。2〜3 本 → 未確定。

【データ】15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。
`検証/学問/金融工学/作業/FX/システムトレード/data_<SYM>_D1_fromH1.csv`。無い銘柄は missing に。

【定義（1 通りに固定）】
- 直近 60 日の実現ボラ RV_t = std(ret[t-59..t]、ddof=1)。
- 月単位の RV 平均 RV_m を取り、銘柄内の RV_m の中央値で各月を「high」「low」に 2 分（high: RV_m ≥ median、low: < median）。
- 各月に属する日次 ret[t] と ret[t-1] の pair を集めて、各期間（all / pre year<2017 / post year≥2017）内で高/低別の Pearson 相関 ρ を計算。
- 差: Δρ = ρ_high − ρ_low。

【測るもの】各銘柄の Δρ（全期間・前後半）、Holm 補正後 p、15 銘柄中の有意本数 K。

【帰無】
銘柄内で月のラベル（high/low）を並べ替え（B=1000）→ 各並べ替えで Δρ を再計算 → 観測との z・片側 p_right = (null ≥ obs の割合)。

【判定（事前固定・変更禁止）】
全期間の Δρ の p_right を 15 銘柄分集めて Holm 補正（m=15、α=0.05）: 有意本数 K。
- 支持: K ≥ 4
- 棄却: K ≤ 1
- 未確定: K ∈ {2, 3}
補助情報: 前後半それぞれの Δρ の符号（判定は変えない）。

【捨てた案の数】約4: (i) 絶対値や二乗の自己相関（Cont 2001 と重複）、(ii) GARCH モデル推定（計算重く、Loubaris の H0 の仕様化が増える）、(iii) 3 分位（4 分位数の中間が多い）、(iv) 時間足 H1（Q252 の M15 と重複する領域）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

【実装】自己完結・決定的（乱数は帰無の並べ替えのみ seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_vol_regime_autocorr_q294.py（B=1000、約 2 分）／--smoke --B 5
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q294"
DEFAULT_B = 1000
START = "2008-01-01"


def _corr_lag1(x):
    x = np.asarray(x, dtype=float)
    m = np.isfinite(x)
    x = x[m]
    if len(x) < 10:
        return np.nan
    x0 = x[:-1]
    x1 = x[1:]
    if np.std(x0) == 0 or np.std(x1) == 0:
        return np.nan
    return float(np.corrcoef(x0, x1)[0, 1])


def _delta_rho(df_sym, labels, y0, y1):
    """与えられた月ラベル labels（{ym: 'high'|'low'}）で、期間 [y0, y1) の Δρ = ρ_high − ρ_low を返す。"""
    d = df_sym[(df_sym["year"] >= y0) & (df_sym["year"] < y1)].copy()
    if d.empty:
        return np.nan
    d["ym"] = pd.to_datetime(d["time"]).dt.to_period("M").astype(str)
    d["regime"] = d["ym"].map(labels)
    high = d[d["regime"] == "high"]["ret"].values
    low = d[d["regime"] == "low"]["ret"].values
    r_h = _corr_lag1(high) if len(high) >= 10 else np.nan
    r_l = _corr_lag1(low) if len(low) >= 10 else np.nan
    if np.isnan(r_h) or np.isnan(r_l):
        return np.nan
    return r_h - r_l


def run(args, rng):
    syms = list(SYMS)
    hres = health(syms, kind="D1_fromH1")
    syms_ok, missing = syms_available(syms, kind="D1_fromH1", smoke=args.smoke)
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    results = {}
    p_right_all = []
    deltas_all = []
    for sym in syms_ok:
        df = load_d1(sym, args.smoke, rng)
        df = df[df["time"] >= pd.Timestamp(START)].reset_index(drop=True)
        if len(df) < 120:
            continue
        df["ret"] = df["close"].pct_change().values
        s = pd.Series(df["ret"].values)
        df["rv60"] = s.rolling(60, min_periods=60).std(ddof=1).values
        df["ym"] = pd.to_datetime(df["time"]).dt.to_period("M").astype(str)
        rv_month = df.groupby("ym")["rv60"].mean().dropna()
        if len(rv_month) < 24:
            continue
        median = rv_month.median()
        labels = {ym: ("high" if v >= median else "low") for ym, v in rv_month.items()}
        obs = {p: _delta_rho(df, labels, y0, y1) for p, (y0, y1) in periods.items()}
        # 帰無: 月のラベルを並べ替え
        ym_keys = list(labels.keys())
        ym_vals = np.array([labels[k] for k in ym_keys])
        nulls = {p: [] for p in periods}
        for b in range(args.B):
            shuffled = rng.permutation(ym_vals)
            lab2 = dict(zip(ym_keys, shuffled))
            for p, (y0, y1) in periods.items():
                nulls[p].append(_delta_rho(df, lab2, y0, y1))
        pz = {}
        for p in periods:
            if np.isnan(obs[p]):
                pz[p] = {"delta": None, "z": None, "p_right": None}
                continue
            z, pct = z_of(obs[p], nulls[p])
            pr = perm_p(obs[p], nulls[p], side="greater")
            pz[p] = {"delta": f(obs[p]), "z": f(z), "p_right": f(pr)}
        results[sym] = pz
        p_right_all.append((sym, pz["all"]["p_right"]))
        deltas_all.append((sym, pz["all"]["delta"]))
    # Holm 補正（m=15）
    pvals = [pr if pr is not None else np.nan for _, pr in p_right_all]
    pads = [np.nan] * (len(syms) - len(pvals))
    adj = holm(pvals + pads)[: len(pvals)]
    K = int(sum(1 for a, (_, d) in zip(adj, deltas_all)
                if a is not None and d is not None and not np.isnan(a) and not np.isnan(d) and a < 0.05 and d > 0))
    for i, (sym, _) in enumerate(p_right_all):
        results[sym]["all"]["p_holm"] = f(adj[i])
    if K >= 4:
        verdict = f"支持: K={K}（Holm 補正後に Δρ>0 で有意な銘柄が ≥4 本）"
    elif K <= 1:
        verdict = f"棄却: K={K}（Holm 補正後に有意な銘柄が ≤1 本）"
    else:
        verdict = f"未確定: K={K}"
    res = {"question": "15 銘柄 D1 の 1 次自己相関は高ボラ月で低ボラ月より高いか（Loubaris2026-3 の移植）",
           "settings": {"syms": syms, "window_rv": 60, "regime_split": "monthly RV_median within symbol", "B": args.B,
                        "start": START, "split_year": SPLIT_YEAR, "n_tests": 15, "null": "月ラベルの並べ替え",
                        "verdict_basis": "K = 15 銘柄中、全期間の Δρ>0 かつ Holm 補正後 p<0.05 の銘柄数"},
           "missing": missing, "data_health": hres, "symbols": results, "K": K, "machine_verdict": verdict,
           "multiple_comparisons": "判定は 15 銘柄の全期間 p_right の Holm 補正（m=15）。前後半は記述。"}
    out_df = pd.DataFrame([{"sym": s, "delta_all": d, "p_right_all": pr, "p_holm_all": results[s]["all"]["p_holm"]}
                           for (s, d), (_, pr) in zip(deltas_all, p_right_all)])
    return res, {"symbols": out_df}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
