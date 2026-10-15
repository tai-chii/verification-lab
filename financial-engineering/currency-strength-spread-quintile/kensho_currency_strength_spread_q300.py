#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q300: 7 通貨の強度ランキングの最強−最弱スプレッド（4H・L=30 本・ボラ正規化）の上位五分位は、
翌 6 本（1 日）の合成リターンがコスト後に継続か反転か（L×N の 9 通り・循環シフト帰無・前後半 Holm）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-15 の Q300 の行（3案一括生成 通貨強度 第1弾）。
- 背景: taichi と ChatGPT の壁打ち（2026-10-15）「通貨強度の Top × Bottom のスプレッドが大きいとき、その後スプレッドは拡大するか」。
  Fable の整理: これは Menkhoff-Sarno-Schmeling-Schrimpf (2012, JFE) の通貨クロスセクション・モメンタムを 4H へ移したもの。
  短期では反転が優勢という先行知見があるので、符号は決めずに「条件付き期待値がゼロと違うか」だけを測る。
- 関連: 知見 Q218（横断モメンタム 15 銘柄・日足）・Q208（ドル因子の順張り）・「為替の4時間足のMAクロスは…運と区別できず」・
  [[Neely2003-3_為替のトレンドは週次月次では強いが日中足にはない]]。前提の整合性は Q299。
- 先行研究チェック（WebSearch 2026-10-15・英語・"cross-sectional currency momentum intraday hourly 4-hour long strongest short weakest currency reversal study"）:
  見つかったもの: Menkhoff ほか (2012) Currency Momentum Strategies（月次）、Aalto 修論 "Momentary loss: The disappearance of cross-sectional currency momentum"
  （公表後の消失）、Krohn-Mueller-Whelan (2018) FX Premia Around the Clock（日中の通貨プレミア）。
  未確認: 7 通貨の 4H 強度ランキングで最強−最弱スプレッドの分位別に翌 1 日の条件付き期待値を循環シフト帰無で判定した実証は未確認（移植: 月次 → 4H）。

【仮説（測る前に固定）】
H（両側）: 主設定（L=30 本・N=6 本・スプレッド上位五分位 Q5）で、最強通貨買い・最弱通貨売りの合成リターン（段階1コスト後・bp）の
   年単位平均が、前後半とも同符号で、循環シフト帰無に対し Holm 補正後 p<0.05。
   正なら「継続」（弱いものがさらに弱くなる）、負なら「反転」。
H0: 全期間の |z|<1。

【データ】
FX8 H1_dukascopy（2008〜2026-06）→ 8 本の時刻を内部結合 → UTC の 4 時間境界（足の開始時刻が 3,7,11,15,19,23 時＝終値が 4 の倍数の時刻）の行だけを
4H の観測点にする（週末・欠損で 4 時間境界に足が無ければその境界は飛ばす）。

【定義（1 通りに固定）】
- 対数価格 P_c（対ドル・USD=0）。4H 行で L 行前からの差 r_c(L)。ボラ正規化: 各対ドルペアの 4H 対数リターンの直前 120 行の std × sqrt(L) で割る。
  7 通貨で中心化 → 強度 s_c。クロス 2 本は使わない（Q299 の前提: 冗長）。
- 最強 top = argmax s、最弱 bot = argmin s。スプレッド sp = s_top − s_bot。
- 分位: sp を直前 500 行（先読みなし）の分布で順位づけ、五分位 q∈{1..5}（≥80 点で q=5）。
- 先行リターン（bp）: fwd = [(P_top[t+N] − P_top[t]) − (P_bot[t+N] − P_bot[t])] × 1e4（合成: 最強を買い最弱を売る）。
- コスト: 必要な脚ごとに COST_RT の往復（価格比 bp、t 時点の終値）。USD が top か bot なら 1 脚、ほかは 2 脚（クロスを直接使わない保守値）。
  net = fwd − cost。
- 掃引: L∈{6,30,120}（1/5/20 営業日相当）× N∈{1,6,24} の 9 通り × 分位 5。主設定は L=30・N=6・q=5。
- 重なり: N>1 の先行窓は重なる。判定は年単位（年ごとの平均の t）で、束ねた t は参考（NW ラグ=N）。

【測るもの】
各 (L,N,q) の net の平均 bp・年単位 t・件数、q と fwd の Spearman（単調性）、無条件（全 q）の平均。主設定の前後半の z・perm_p・Holm。

【帰無】
(top, bot, q) のラベル列を時間軸で循環シフト（min_shift=500 行）して、同じ規則で net を再計算 → B=500 → 主設定・q=5 の年単位 bp の分布。
両側 perm_p（side="two"）。

【判定（事前固定・変更禁止）】
主設定（L=30・N=6・q=5）の年単位 bp_net について:
- 支持（継続）: pre・post とも bp_net>0 かつ Holm 補正後 p<0.05（m=2）。
- 支持（反転）: pre・post とも bp_net<0 かつ Holm 補正後 p<0.05（m=2）。
- 棄却: 全期間の |z|<1。
- 未確定: ほか（符号が前後半で割れる場合を含む）。
ほかの 8 通りの (L,N) と q=1..4 は記述（多重比較の本数は宣言 2 本、ほかは判定に使わない）。

【捨てた案の数】
約5: (i) 事後の分位（年内順位。先読みになる）、(ii) 2 対 1 ルール（USD・EUR・JPY の 3 通貨のみ。ランキングの特殊ケース）、(iii) Core/Satellite の区別（検証できる仮説になっていない）、
(iv) クロスを含む最小二乗（Q299 で冗長なら同じ）、(v) ML（条件付き期待値が無ければ乗せる意味がない）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。規則は固定で相場観は使わない。

【委託の確かめ方】設計は Fable、コードは Fable（クラウド側で --smoke --B 5 のみ）、実行と解釈は後の /lab（Opus）。委託なし。

【実装】自己完結・決定的（乱数は帰無の循環シフトのみ seed 固定）。依存: python3 + numpy/pandas。土台は fe_core（直接使う型）。
実行: python3 kensho_currency_strength_spread_q300.py（B=500・数分）／--smoke --B 5
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q300"
KIND = "H1_dukascopy"
START = "2008-01-01"
DEFAULT_B = 500
LS = [6, 30, 120]          # 4H 本
NS = [1, 6, 24]            # 4H 本
MAIN_L, MAIN_N, MAIN_Q = 30, 6, 5
VOL_WIN = 120              # 4H リターンの std の窓（≒20 営業日）
RANK_WIN = 500             # 分位の参照窓（行）
MIN_SHIFT = 500
CURS = ["USD", "EUR", "GBP", "AUD", "JPY", "CHF", "CAD"]
PAIRS = {"EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"), "AUDUSD": ("AUD", "USD"), "USDJPY": ("USD", "JPY"),
         "USDCHF": ("USD", "CHF"), "USDCAD": ("USD", "CAD"), "EURJPY": ("EUR", "JPY"), "GBPJPY": ("GBP", "JPY")}
STRAIGHTS = [p for p in PAIRS if "USD" in PAIRS[p]]
PAIR_OF = {(PAIRS[p][1] if PAIRS[p][0] == "USD" else PAIRS[p][0]): p for p in STRAIGHTS}  # 通貨 → 対ドルペア


# ---------------------------------------------------------------------------- 通貨強度（Q299〜Q301 で同じ定義）
def align_closes(dfs, syms):
    out = None
    for s in syms:
        d = dfs[s][["time", "close"]].rename(columns={"close": s})
        out = d if out is None else out.merge(d, on="time", how="inner")
    return out.reset_index(drop=True)


def usd_log_prices(tbl):
    """対ドル対数価格 P（T×7、USD=0）と、通貨ごとの対ドルペアの終値（コスト用）。"""
    T = len(tbl)
    P = np.zeros((T, len(CURS))); close = {}
    for p in STRAIGHTS:
        b, q = PAIRS[p]
        lp = np.log(tbl[p].values.astype(float))
        if b == "USD":
            P[:, CURS.index(q)] = -lp; close[q] = tbl[p].values.astype(float)
        else:
            P[:, CURS.index(b)] = lp; close[b] = tbl[p].values.astype(float)
    return P, close


def strength(P, L, vol_win=VOL_WIN):
    """ボラ正規化した L 行リターンの通貨強度（7 通貨で中心化）。USD 列は 0 からの中心化なので 0 でない。"""
    T, K = P.shape
    r = np.full((T, K), np.nan); r[L:] = P[L:] - P[:-L]
    r1 = np.full((T, K), np.nan); r1[1:] = np.diff(P, axis=0)
    sd = pd.DataFrame(r1).rolling(vol_win, min_periods=vol_win // 2).std().values * np.sqrt(L)
    sd[:, CURS.index("USD")] = 1.0  # USD は 0 のまま
    z = r / sd
    ok = np.isfinite(z).all(axis=1)
    out = np.full_like(z, np.nan)
    out[ok] = z[ok] - z[ok].mean(axis=1, keepdims=True)
    return out


def trailing_quintile(x, win=RANK_WIN):
    """x[t] を直前 win 個（t を含まない）に対する百分位で 1..5 に。参照が win/2 未満なら NaN。"""
    s = pd.Series(x)
    out = np.full(len(x), np.nan)
    arr = s.values
    for t in range(len(x)):
        lo = max(0, t - win); ref = arr[lo:t]; ref = ref[np.isfinite(ref)]
        if len(ref) < win // 2 or not np.isfinite(arr[t]):
            continue
        pct = (ref < arr[t]).mean()
        out[t] = min(5, int(pct * 5) + 1)
    return out


def cost_matrix(close, T):
    """C[t, c] = 通貨 c の対ドルペアの往復コスト（bp）。USD 列は 0。"""
    C = np.zeros((T, len(CURS)))
    for cur, p in PAIR_OF.items():
        C[:, CURS.index(cur)] = COST_RT[p] / close[cur] * 1e4
    return C


def forward_net(P, C, top, bot, N):
    """各観測 t の合成先行リターン（bp）とコスト（bp）。top/bot は通貨の添字配列（無効は -1）。ベクトル化。"""
    T = P.shape[0]
    t = np.arange(T)
    ok = (top >= 0) & (bot >= 0) & (t + N < T)
    fwd = np.full(T, np.nan); cost = np.full(T, np.nan)
    tt = t[ok]; a = top[ok]; b = bot[ok]
    fwd[ok] = ((P[tt + N, a] - P[tt, a]) - (P[tt + N, b] - P[tt, b])) * 1e4
    cost[ok] = C[tt, a] + C[tt, b]
    return fwd, cost


def run(args, rng):
    syms = list(PAIRS)
    hres = None if args.smoke else health(syms, kind=KIND)
    ok, missing = syms_available(syms, kind=KIND, smoke=args.smoke)
    if any(s not in ok for s in STRAIGHTS):
        return {"question": "通貨強度スプレッドの五分位（Q300）", "missing": missing, "data_health": hres,
                "machine_verdict": "未確定: 対ドル 6 本が揃わない（missing を見る）"}, {}
    dfs = {s: load_h1(s, args.smoke, rng, n=30000, start="2015-01-01") for s in STRAIGHTS}
    tbl = align_closes(dfs, STRAIGHTS)
    tbl = tbl[tbl["time"] >= pd.Timestamp(START)].reset_index(drop=True)
    # 4H 境界: 足の開始時刻 hour % 4 == 3（終値が 4 の倍数の時刻）
    h4 = tbl[tbl["time"].dt.hour % 4 == 3].reset_index(drop=True)
    year = h4["time"].dt.year.values
    P, close = usd_log_prices(h4)
    T = len(h4)
    C = cost_matrix(close, T)
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    rows = []; main_cells = None
    for L in LS:
        S = strength(P, L)
        valid = np.isfinite(S).all(axis=1)
        top = np.where(valid, np.nanargmax(np.where(valid[:, None], S, -np.inf), axis=1), -1)
        bot = np.where(valid, np.nanargmin(np.where(valid[:, None], S, np.inf), axis=1), -1)
        sp = np.where(valid, S[np.arange(T), np.clip(top, 0, None)] - S[np.arange(T), np.clip(bot, 0, None)], np.nan)
        q = trailing_quintile(sp)
        for N in NS:
            fwd, cost = forward_net(P, C, top, bot, N)
            net = fwd - cost
            d = pd.DataFrame({"year": year, "q": q, "fwd": fwd, "net": net, "sp": sp})
            d = d[np.isfinite(d["net"]) & np.isfinite(d["q"])]
            for pn, (y0, y1) in periods.items():
                dd = d[(d["year"] >= y0) & (d["year"] < y1)]
                if dd.empty:
                    continue
                rho = spearman(dd["q"].values, dd["fwd"].values)
                for qq in [1, 2, 3, 4, 5, 0]:
                    e = dd if qq == 0 else dd[dd["q"] == qq]
                    if e.empty:
                        continue
                    st = by_year_stats(e, "net", y0=y0, y1=y1)
                    sg = by_year_stats(e, "fwd", y0=y0, y1=y1)
                    rows.append({"L": L, "N": N, "q": qq, "period": pn, "n": int(len(e)), "bp_gross": fmt(sg["mean"]), "bp_net": fmt(st["mean"]),
                                 "t_year": fmt(st["t"]), "n_years": st["n_years"], "years_dropped": st["years_dropped"],
                                 "t_cluster_nw": fmt(nw_t(e["net"].values, lag=N)), "spearman_q_fwd": fmt(rho),
                                 "mean_spread": fmt(e["sp"].mean())})
            if L == MAIN_L and N == MAIN_N:
                main_cells = {"top": top, "bot": bot, "q": q, "N": N}
    df = pd.DataFrame(rows)
    # ---------------------------------------------------------------- 帰無（主設定）
    main = {}
    obs_by_p = {}
    for pn in periods:
        r = df[(df["L"] == MAIN_L) & (df["N"] == MAIN_N) & (df["q"] == MAIN_Q) & (df["period"] == pn)]
        obs_by_p[pn] = float(r["bp_net"].iloc[0]) if len(r) and r["bp_net"].iloc[0] is not None else np.nan
    null = {pn: [] for pn in periods}
    if main_cells is not None and args.B > 0:
        top, bot, q, N = main_cells["top"], main_cells["bot"], main_cells["q"], main_cells["N"]
        lab = np.column_stack([top, bot, q])
        for b in range(args.B):
            k = int(rng.integers(MIN_SHIFT, max(MIN_SHIFT + 1, T - MIN_SHIFT + 1)))
            sh = np.roll(lab, k, axis=0)
            fwd, cost = forward_net(P, C, sh[:, 0].astype(int), sh[:, 1].astype(int), N)
            net = fwd - cost
            d = pd.DataFrame({"year": year, "q": sh[:, 2], "net": net})
            d = d[np.isfinite(d["net"]) & (d["q"] == MAIN_Q)]
            for pn, (y0, y1) in periods.items():
                null[pn].append(by_year_stats(d, "net", y0=y0, y1=y1)["mean"])
    pv = {}
    for pn in periods:
        ns = null_summary(obs_by_p[pn], null[pn]) if null[pn] else {"z": None, "pct": None, "p_perm": None, "degenerate": None, "B": 0, "q025": None, "q975": None}
        p2 = perm_p(obs_by_p[pn], null[pn], side="two") if null[pn] else np.nan
        main[pn] = {"bp_net": fmt(obs_by_p[pn]), "z": fmt(ns["z"]), "pct": fmt(ns["pct"]), "p_perm_two": fmt(p2),
                    "null_degenerate": ns["degenerate"], "null_q025": fmt(ns.get("q025")), "null_q975": fmt(ns.get("q975")), "B": ns["B"]}
        if pn in ("pre", "post"):
            pv[pn] = p2
    adj = holm([pv.get("pre", np.nan), pv.get("post", np.nan)])
    main["pre"]["p_holm"] = fmt(adj[0]); main["post"]["p_holm"] = fmt(adj[1])
    # ---------------------------------------------------------------- 判定
    pre, post, al = main["pre"], main["post"], main["all"]
    vals = [pre["bp_net"], post["bp_net"], pre["p_holm"], post["p_holm"], al["z"]]
    if any(v is None for v in vals):
        verdict = "未確定: 計算できない（期間・件数の不足か帰無の退化）"
    elif pre["bp_net"] > 0 and post["bp_net"] > 0 and pre["p_holm"] < 0.05 and post["p_holm"] < 0.05:
        verdict = "支持（継続）: 主設定 q=5 の年単位 bp_net が前後半とも >0 かつ Holm 補正後 p<0.05"
    elif pre["bp_net"] < 0 and post["bp_net"] < 0 and pre["p_holm"] < 0.05 and post["p_holm"] < 0.05:
        verdict = "支持（反転）: 主設定 q=5 の年単位 bp_net が前後半とも <0 かつ Holm 補正後 p<0.05"
    elif abs(al["z"]) < 1:
        verdict = f"棄却: 全期間の |z|={abs(al['z']):.2f} < 1"
    else:
        verdict = "未確定"
    res = {"question": "7 通貨の強度ランキングの最強−最弱スプレッド上位五分位は翌 1 日の合成リターンがコスト後に継続か反転か",
           "settings": {"syms": STRAIGHTS, "start": START, "split_year": SPLIT_YEAR, "L_bars_4h": LS, "N_bars_4h": NS,
                        "main": {"L": MAIN_L, "N": MAIN_N, "q": MAIN_Q}, "vol_win": VOL_WIN, "rank_win": RANK_WIN,
                        "n_rows_4h": int(T), "B": args.B, "n_tests": 2, "null": f"(top,bot,q) ラベルの循環シフト min_shift={MIN_SHIFT}",
                        "cost": "COST_RT 往復・USD 以外の脚ごと（最大 2 脚）",
                        "verdict_basis": "主設定 q=5 の年単位 bp_net: 前後半同符号かつ Holm p<0.05 → 支持（継続／反転）、全期間 |z|<1 → 棄却"},
           "missing": missing, "data_health": hres, "main": main,
           "grid": {f"L{r['L']}_N{r['N']}_q{r['q']}_{r['period']}": {k: v for k, v in r.items() if k not in ("L", "N", "q", "period")} for r in rows},
           "machine_verdict": verdict,
           "multiple_comparisons": "判定は主設定（L=30・N=6・q=5）の前後半 2 本（Holm m=2）。ほかの 8 (L,N) × q=0..5 は記述。"}
    if hres and (hres["failed"] or hres["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res, {"grid": df}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
