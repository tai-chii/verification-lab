#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q299: 通貨強度（対ドル 6 本の L 本リターン平均・7 通貨）は、クロス 2 本（EURJPY・GBPJPY）を足した最小二乗版と
H1 の L=24/120/480 時間で相関 0.99 以上か（クロスは冗長か）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-15「通貨強度（対ドル 6 本の L 本リターン平均・7 通貨）は、クロス 2 本を足した最小二乗版と
  相関 0.99 以上か」の行（Q299・3案一括生成 通貨強度 第1弾）。
- 背景: taichi と ChatGPT の壁打ち（2026-10-15）「10 通貨ペアを通貨強度のセンサーとして使う」案に対し、三角裁定
  （EURJPY ≈ EURUSD × USDJPY）からクロスは対ドルの組み合わせと同じ情報しか持たない（＝情報量を決めるのは通貨の数）という Fable の指摘を、
  手元の H1 で数値として確かめる。Q300・Q301（強度スプレッドの検証）の前提。
- 関連: 知見 Q208（ドル因子の順張り）・Q255（ドル因子を除いた残差の順張り）。
- 先行研究チェック（WebSearch 2026-10-15・英語・"currency strength index triangular arbitrage redundancy cross rates least squares currency factor decomposition intraday"）:
  見つかったもの: Aiba-Hatano ほか (arXiv 2002.02583, 2020) 三角裁定とクロス通貨相関のエージェント模型、実務の「通貨強度メーター」（MQL5 等・根拠にしない）。
  未確認: 対ドル 6 本の平均で作った強度と、クロスを含む 8 本の最小二乗強度の一致度を L 別・前後半で報告した実証は未確認（条件の穴）。

【仮説（測る前に固定）】
H: 7 通貨（USD・EUR・GBP・AUD・JPY・CHF・CAD）の強度を
   (a) 対ドル 6 本の L 時間対数リターンの平均（USD=0 とし 7 通貨で平均 0 に中心化）、
   (b) 8 本（対ドル 6 本＋EURJPY・GBPJPY）の最小二乗（Σs=0 の制約）、
   (c) 強度メーター型（その通貨が絡む全ペアの L 時間対数リターンの平均・符号つき）
   で作ると、(a) と (b) の相関は L=24/120/480 の全部・7 通貨の全部・前後半の両方で 0.99 以上（クロスは冗長）。
H0: どこかで 0.95 未満。

【データ】
FX8 H1_dukascopy（2008〜2026-06）。8 本の H1 の時刻を内部結合（どれかが欠ける足は落とす）。値動きのない足は load_h1 が除く。

【定義（1 通りに固定）】
- 対数価格 p_pair[t] = log(close[t])。L 時間リターン r_pair[t] = p_pair[t] − p_pair[t−L]（結合後の行番号で L 本前。週末をまたぐ本数は数えない）。
- 通貨 c の対ドル対数価格 P_c: EURUSD→P_EUR=+p、USDJPY→P_JPY=−p、ほか同様。P_USD=0。
- (a) s_c = (P_c[t]−P_c[t−L]) − mean_c'(…)（7 通貨で中心化）。
- (b) r = A s + e、A は 8×7 の ±1 行列、制約 Σs=0 を 9 本目の式（係数 1・右辺 0）として付け、擬似逆行列で解く。
- (c) s_c = mean over pairs containing c of (±r_pair)。
- ボラ正規化版: r_pair を直前 480 本の 1 時間対数リターンの標準偏差 × sqrt(L) で割ってから同じ計算（Q300・Q301 と同じ正規化）。生の版と両方出す。
- 三角残差: e_cross = r_EURJPY − (r_EURUSD + r_USDJPY)、同 GBPJPY。std(e_cross)/std(r_cross) を L 別に出す。

【測るもの】
corr((a),(b))・corr((c),(b))・corr((a),(c)) を 通貨 × L × 期間（all/pre/post・分割 2017）で。三角残差の比。

【帰無】
なし（測定の整合性の検証。閾値判定で、並べ替え帰無は使わない。B は未使用）。

【判定（事前固定・変更禁止）】
支持（クロスは冗長）: 生の版で corr((a),(b)) が 7 通貨 × 3 L × pre/post の全 42 セルで ≥ 0.99。
棄却: 42 セルのどこかで < 0.95。
未確定: ほか（0.95 以上 0.99 未満のセルがある）。
補助: ボラ正規化版・(c) の相関・三角残差の比は記述。

【捨てた案の数】
約3: (i) 10 ペア以上（手元のデータは FX8 のみ）、(ii) NZD を含める（データなし）、(iii) 予測力の比較（情報量の差を先に測る方が先）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。規則は固定で相場観は使わない。

【委託の確かめ方】設計は Fable、コードは Fable（クラウド側で --smoke のみ）、実行と解釈は後の /lab（Opus）。委託なし。

【実装】自己完結・決定的（乱数なし）。依存: python3 + numpy/pandas。土台は fe_core（直接使う型）。
実行: python3 kensho_currency_strength_redundancy_q299.py（約 1 分）／--smoke
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q299"
KIND = "H1_dukascopy"
START = "2008-01-01"
LS = [24, 120, 480]        # 時間（H4 換算 6/30/120 本）
VOL_WIN = 480              # 1 時間リターンの標準偏差の窓
CURS = ["USD", "EUR", "GBP", "AUD", "JPY", "CHF", "CAD"]
PAIRS = {"EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"), "AUDUSD": ("AUD", "USD"), "USDJPY": ("USD", "JPY"),
         "USDCHF": ("USD", "CHF"), "USDCAD": ("USD", "CAD"), "EURJPY": ("EUR", "JPY"), "GBPJPY": ("GBP", "JPY")}
STRAIGHTS = [p for p in PAIRS if "USD" in PAIRS[p]]
CROSSES = [p for p in PAIRS if "USD" not in PAIRS[p]]


# ---------------------------------------------------------------------------- 通貨強度（Q299〜Q301 で同じ定義）
def align_closes(dfs, syms):
    """H1 の time を内部結合し、time + 各ペアの close の表を返す。"""
    out = None
    for s in syms:
        d = dfs[s][["time", "close"]].rename(columns={"close": s})
        out = d if out is None else out.merge(d, on="time", how="inner")
    return out.reset_index(drop=True)


def design_matrix(pairs, curs):
    A = np.zeros((len(pairs), len(curs)))
    for i, p in enumerate(pairs):
        b, q = PAIRS[p]
        A[i, curs.index(b)] = 1.0
        A[i, curs.index(q)] = -1.0
    return A


def ls_solver(pairs, curs):
    """r = A s、Σs=0 を 1 本足して擬似逆行列。返り値 M（7×(n_pairs+1)）: s = M @ [r; 0]。"""
    A = design_matrix(pairs, curs)
    Ac = np.vstack([A, np.ones((1, len(curs)))])
    return np.linalg.pinv(Ac)


def pair_returns(tbl, L, normalize):
    """各ペアの L 本リターン（行番号ベース）。normalize なら直前 VOL_WIN 本の 1 時間リターン std × sqrt(L) で割る。"""
    out = {}
    for p in PAIRS:
        lp = np.log(tbl[p].values.astype(float))
        r = np.full(len(lp), np.nan)
        r[L:] = lp[L:] - lp[:-L]
        if normalize:
            r1 = np.r_[np.nan, np.diff(lp)]
            sd = pd.Series(r1).rolling(VOL_WIN, min_periods=VOL_WIN // 2).std().values * np.sqrt(L)
            r = r / sd
        out[p] = r
    return out


def strength_mean_straights(rp):
    """(a) 対ドル 6 本の平均型: s_c = ±r_pair（USD=0）→ 7 通貨で中心化。"""
    T = len(next(iter(rp.values())))
    S = np.zeros((T, len(CURS)))
    for p in STRAIGHTS:
        b, q = PAIRS[p]
        if b == "USD":
            S[:, CURS.index(q)] = -rp[p]
        else:
            S[:, CURS.index(b)] = rp[p]
    return S - np.nanmean(S, axis=1, keepdims=True)


def strength_ls(rp, pairs):
    """(b) 最小二乗型（Σs=0）。"""
    M = ls_solver(pairs, CURS)
    R = np.column_stack([rp[p] for p in pairs] + [np.zeros(len(rp[pairs[0]]))])
    return R @ M.T


def strength_meter(rp):
    """(c) 強度メーター型: 通貨が絡む全ペアの ±r の平均。"""
    T = len(next(iter(rp.values())))
    S = np.zeros((T, len(CURS))); n = np.zeros(len(CURS))
    for p, (b, q) in PAIRS.items():
        S[:, CURS.index(b)] += rp[p]; n[CURS.index(b)] += 1
        S[:, CURS.index(q)] -= rp[p]; n[CURS.index(q)] += 1
    return S / n


def _corr(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 30 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return np.nan
    return float(np.corrcoef(x[m], y[m])[0, 1])


def run(args, rng):
    syms = list(PAIRS)
    hres = None if args.smoke else health(syms, kind=KIND)
    ok, missing = syms_available(syms, kind=KIND, smoke=args.smoke)
    if len(ok) < len(syms):
        return {"question": "通貨強度の整合性（Q299）", "missing": missing, "data_health": hres,
                "machine_verdict": "未確定: 8 ペアが揃わない（missing を見る）"}, {}
    dfs = {s: load_h1(s, args.smoke, rng, n=20000, start="2015-01-01") for s in ok}
    tbl = align_closes(dfs, ok)
    tbl = tbl[tbl["time"] >= pd.Timestamp(START)].reset_index(drop=True)
    year = tbl["time"].dt.year.values
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    rows = []; tri = []
    for norm in (False, True):
        for L in LS:
            rp = pair_returns(tbl, L, norm)
            Sa = strength_mean_straights(rp)
            Sb = strength_ls(rp, list(PAIRS))
            Sc = strength_meter(rp)
            for pn, (y0, y1) in periods.items():
                m = (year >= y0) & (year < y1)
                for ci, c in enumerate(CURS):
                    rows.append({"normalized": norm, "L": L, "period": pn, "cur": c,
                                 "corr_a_b": _corr(Sa[m, ci], Sb[m, ci]), "corr_c_b": _corr(Sc[m, ci], Sb[m, ci]),
                                 "corr_a_c": _corr(Sa[m, ci], Sc[m, ci]),
                                 "rmse_a_b_over_std_b": float(np.nanstd(Sa[m, ci] - Sb[m, ci]) / np.nanstd(Sb[m, ci])) if np.nanstd(Sb[m, ci]) > 0 else np.nan,
                                 "n": int(np.isfinite(Sa[m, ci]).sum())})
            if not norm:
                for cr in CROSSES:
                    b, q = PAIRS[cr]
                    # クロス ≈ 対ドルの差: r_cross − (P_b − P_q)
                    synth = np.zeros(len(tbl))
                    for p in STRAIGHTS:
                        pb, pq = PAIRS[p]
                        if pb == b: synth += rp[p]
                        if pq == b: synth -= rp[p]
                        if pb == q: synth -= rp[p]
                        if pq == q: synth += rp[p]
                    e = rp[cr] - synth
                    for pn, (y0, y1) in periods.items():
                        m = (year >= y0) & (year < y1)
                        tri.append({"cross": cr, "L": L, "period": pn,
                                    "std_resid_over_std_cross": float(np.nanstd(e[m]) / np.nanstd(rp[cr][m])),
                                    "corr_cross_synth": _corr(rp[cr][m], synth[m])})
    df = pd.DataFrame(rows); tdf = pd.DataFrame(tri)
    judge = df[(~df["normalized"]) & (df["period"].isin(["pre", "post"]))]
    cells = judge["corr_a_b"].values
    n_cells = int(len(cells)); n_fin = int(np.isfinite(cells).sum())
    mn = float(np.nanmin(cells)) if n_fin else np.nan
    if n_fin < n_cells or not np.isfinite(mn):
        verdict = f"未確定: 計算できないセルがある（{n_cells - n_fin}/{n_cells}）"
    elif mn >= 0.99:
        verdict = f"支持: 生の版の corr(平均6本, 最小二乗8本) の最小値 {mn:.4f} ≥ 0.99（{n_cells} セル全部）→ クロスは冗長"
    elif mn < 0.95:
        verdict = f"棄却: 最小値 {mn:.4f} < 0.95 のセルあり"
    else:
        verdict = f"未確定: 最小値 {mn:.4f}（0.95 以上 0.99 未満）"
    summary = {}
    for (norm, L, pn), g in df.groupby(["normalized", "L", "period"]):
        summary[f"norm{int(norm)}_L{L}_{pn}"] = {"min_corr_a_b": fmt(g["corr_a_b"].min()), "mean_corr_a_b": fmt(g["corr_a_b"].mean()),
                                                 "min_corr_c_b": fmt(g["corr_c_b"].min()), "mean_corr_c_b": fmt(g["corr_c_b"].mean()),
                                                 "max_rmse_ratio_a_b": fmt(g["rmse_a_b_over_std_b"].max())}
    res = {"question": "通貨強度（対ドル 6 本の平均）はクロス 2 本を足した最小二乗版と相関 0.99 以上か（クロスは冗長か）",
           "settings": {"syms": ok, "start": START, "split_year": SPLIT_YEAR, "L_hours": LS, "vol_win": VOL_WIN, "curs": CURS,
                        "n_rows_joined": int(len(tbl)), "null": "なし（閾値判定）", "n_tests": 0,
                        "verdict_basis": "生の版・7 通貨 × 3 L × pre/post の 42 セルで corr(a,b) ≥ 0.99 → 支持、< 0.95 のセルあり → 棄却"},
           "missing": missing, "data_health": hres, "summary": summary,
           "triangular_residual": tdf.to_dict(orient="records"),
           "judge_cells": {"n": n_cells, "n_finite": n_fin, "min_corr_a_b": fmt(mn)},
           "machine_verdict": verdict,
           "multiple_comparisons": "閾値判定のみ（検定なし）。42 セルの最小値で判定。"}
    if hres and (hres["failed"] or hres["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res, {"cells": df, "triangular": tdf}


def main():
    args = parse_args(default_B=0)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
