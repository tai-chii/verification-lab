#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q295: 15 銘柄 H1 のクラスター t（時刻束ね）は naive パネル t より 30% 以上縮むか（GarciaArano2026-3 の H1 移植・Q175 の H1 版）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-14「15 銘柄 H1 のクラスター t（時刻束ね）は naive パネル t より 30% 以上縮むか」の行（Q295・10案一括生成 ターミナル版）。
- [[GarciaArano2026-3_クラスター標準誤差を使う銘柄数が増えるとtの縮みは小さくなる]]。
- 関連: 知見 Q175（15銘柄 D1 TSMOM60 の cluster_t / naive_t 比は約 0.6〜0.8）。
- 先行研究チェック（WebSearch 2026-10-14・英語・"intraday hourly panel cluster standard errors shrinkage momentum 15 assets daily vs hourly"）:
  見つかったもの: Petersen (2009) "Estimating Standard Errors in Finance Panel Data Sets"、Thompson (2011) 2-way clustering、Driscoll-Kraay (1998)。
  未確認: 15 銘柄 H1 の TSMOM24 で時刻束ねの cluster_t を naive_t と比較し、縮み率 r=cluster_t/naive_t を 15 本の銘柄別に Holm 補正で判定する実証は未確認（移植）。

【仮説（測る前に固定）】
H: 15 銘柄 H1 の TSMOM24 損益 [bp]（コスト0）で、r = cluster_t_time / naive_t_pooled の中央値 ≤ 0.70（30% 以上の縮み）→ 支持。
H0: r の中央値 ≥ 0.95（ほとんど縮まない）→ 棄却。0.70 < r < 0.95 → 未確定。

【データ】
15 銘柄（SYMS = FX8 + TREND7）H1_dukascopy、2008〜2026-06。
（`検証/学問/金融工学/作業/FX/システムトレード/data_<SYM>_H1_dukascopy.csv`。無い銘柄は missing に。）

【定義（1 通りに固定）】
- 合図: TSMOM24（24 時間前との比較の符号）。
- 損益 bp: pnl_bp(pos, close, cost=0)（コスト 0 で t 値の縮みだけを測る）。
- naive_t = tstat(全銘柄×全時刻の bp を 1 本に並べたもの、ddof=1)。
- cluster_t = cluster_t(df, "bp", by="time", lag=5).t（同じ時刻の bp を平均してから nw_t）。
- r = cluster_t / naive_t（符号を含む）。

【測るもの】
銘柄プールの r（全期間・前後半）、15 銘柄の r 分布（箱ひげの中央値・分位）、r≤0.70 の銘柄数 K。

【帰無】
銘柄内で時刻 index を循環シフト（min_shift=72、B=500）→ 各シフトで cluster_t と naive_t を計算 → r の帰無分布 → z・perm_p（side="less"）。

【判定（事前固定・変更禁止）】
全期間の銘柄プール（15 本の bp を結合）の r の p_left を Holm 補正（m=15）: 有意本数 K。
- 支持: 15 銘柄プール r ≤ 0.70 かつ Holm 補正後 p<0.05
- 棄却: 15 銘柄プール r ≥ 0.95
- 未確定: ほか
補助情報: 前後半の r、銘柄別の r。

【捨てた案の数】
約4: (i) D1（Q175 と重複）、(ii) H4（情報量が中途半端）、(iii) 2-way クラスタリング（Thompson 2011・実装が重い）、(iv) ブートストラップでの縮み（循環シフトの方が時系列構造を保つ）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

【実装】自己完結・決定的（乱数は帰無の循環シフトのみ seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_cluster_t_h1_shrinkage_q295.py（B=500、約 3 分）／--smoke --B 5
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q295"
DEFAULT_B = 500
START = "2008-01-01"
KIND = "H1_dukascopy"
L = 24  # TSMOM の lookback（1 日分の H1）


def _tsmom_bp(df, sym):
    """TSMOM24 の bp（コスト 0）を返す。"""
    close = df["close"].values
    pos = tsmom_pos(close, L)
    cost = np.zeros(len(close))
    return pnl_bp(pos, close, cost)


def _r_ratio(df_pool):
    """df_pool: 列 time, sym, bp を持つ long DataFrame。r = cluster_t_time / naive_t_pooled を返す。"""
    x = df_pool["bp"].values
    x = x[np.isfinite(x)]
    nt = tstat(x)
    ct = cluster_t(df_pool, "bp", by="time", lag=5)["t"]
    if nt is None or np.isnan(nt) or nt == 0 or ct is None or np.isnan(ct):
        return np.nan
    return float(ct / nt)


def run(args, rng):
    syms = list(SYMS)
    hres = health(syms, kind=KIND)
    syms_ok, missing = syms_available(syms, kind=KIND, smoke=args.smoke)
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    sym_data = {}  # sym -> df (time, year, bp)
    for sym in syms_ok:
        df = load_h1(sym, args.smoke, rng, n=120000, start=START)
        df = df[df["time"] >= pd.Timestamp(START)].reset_index(drop=True)
        if len(df) < 2 * L:
            continue
        bp = _tsmom_bp(df, sym)
        sym_data[sym] = pd.DataFrame({"time": df["time"].values, "year": df["year"].values,
                                      "sym": sym, "bp": bp})
    if len(sym_data) == 0:
        return {"error": "no data", "missing": missing, "data_health": hres}, {}
    # プール（全銘柄結合）
    pool = pd.concat(sym_data.values(), axis=0, ignore_index=True)
    obs_r = {}
    for p, (y0, y1) in periods.items():
        d = pool[(pool["year"] >= y0) & (pool["year"] < y1)]
        obs_r[p] = _r_ratio(d) if len(d) >= 100 else np.nan
    # 帰無: 各銘柄で bp を循環シフト（時刻との対応だけ壊す）、再度プール
    nulls = {p: [] for p in periods}
    for b in range(args.B):
        shifted = []
        for sym, d in sym_data.items():
            if len(d) < 10 * 72:
                shifted.append(d)
                continue
            bp_shift = circ_shift(rng, d["bp"].values, min_shift=72)
            d2 = d.copy()
            d2["bp"] = bp_shift
            shifted.append(d2)
        pool2 = pd.concat(shifted, axis=0, ignore_index=True)
        for p, (y0, y1) in periods.items():
            d = pool2[(pool2["year"] >= y0) & (pool2["year"] < y1)]
            nulls[p].append(_r_ratio(d) if len(d) >= 100 else np.nan)
    # z と p_left（r が小さいほど良い＝縮む）
    pz = {}
    for p in periods:
        if np.isnan(obs_r[p]):
            pz[p] = {"r": None, "z": None, "p_left": None}
            continue
        z, pct = z_of(obs_r[p], nulls[p])
        pl = perm_p(obs_r[p], nulls[p], side="less")
        pz[p] = {"r": f(obs_r[p]), "z": f(z), "p_left": f(pl)}
    # 銘柄別の r（記述）
    sym_r = {}
    for sym, d in sym_data.items():
        rr = {}
        for p, (y0, y1) in periods.items():
            dd = d[(d["year"] >= y0) & (d["year"] < y1)]
            if len(dd) < 100:
                rr[p] = None
                continue
            x = dd["bp"].values
            x = x[np.isfinite(x)]
            nt_s = tstat(x)
            ct_s = cluster_t(dd, "bp", by="time", lag=5)["t"]
            if nt_s is None or np.isnan(nt_s) or nt_s == 0 or ct_s is None or np.isnan(ct_s):
                rr[p] = None
            else:
                rr[p] = f(ct_s / nt_s)
        sym_r[sym] = rr
    r_all_syms = [sym_r[s]["all"] for s in sym_r if sym_r[s]["all"] is not None]
    r_median = f(np.median(r_all_syms)) if r_all_syms else None
    K_tight = int(sum(1 for v in r_all_syms if v <= 0.70))
    # 判定
    r_pool = obs_r.get("all")
    p_pool = pz["all"]["p_left"]
    if r_pool is not None and not np.isnan(r_pool) and p_pool is not None and not np.isnan(p_pool) and r_pool <= 0.70 and p_pool < 0.05:
        verdict = f"支持: プール r={f(r_pool)} ≤0.70 かつ p_left={f(p_pool)}<0.05"
    elif r_pool is not None and not np.isnan(r_pool) and r_pool >= 0.95:
        verdict = f"棄却: プール r={f(r_pool)} ≥0.95（縮まない）"
    else:
        verdict = f"未確定: プール r={f(r_pool)}（0.70 < r < 0.95 もしくは p>=0.05）"
    res = {"question": "15 銘柄 H1 のクラスター t（時刻束ね）は naive パネル t より 30% 以上縮むか（GarciaArano2026-3 の H1 移植）",
           "settings": {"syms": syms, "lookback": L, "B": args.B, "start": START, "split_year": SPLIT_YEAR,
                        "n_tests": 15, "null": "銘柄内の bp を循環シフト（min_shift=72）",
                        "verdict_basis": "プール r ≤ 0.70 かつ p_left < 0.05 で支持、r ≥ 0.95 で棄却"},
           "missing": missing, "data_health": hres,
           "pool_r_by_period": pz, "sym_r": sym_r, "r_median_all_syms": r_median,
           "K_tight_syms_r_le_070": K_tight,
           "machine_verdict": verdict,
           "multiple_comparisons": "判定はプール r 1 本。銘柄別の r は記述統計。"}
    out_df = pd.DataFrame([{"sym": s, "r_all": sym_r[s]["all"], "r_pre": sym_r[s]["pre"], "r_post": sym_r[s]["post"]}
                           for s in sym_r])
    return res, {"sym_r": out_df}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
