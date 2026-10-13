#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q297: US500 / USTECH H1 の日中モメンタム（初動 1 時間 → 終盤 1 時間）は 2016 以降に減衰したか（GarciaArano2026-2 の指数 H1 移植）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-14「US500 / USTECH H1 の日中モメンタム（初動 1 時間 → 終盤 1 時間）は 2016 以降に減衰したか」の行（Q297・10案一括生成 ターミナル版）。
- [[GarciaArano2026-2_米国株の日中モメンタム戦略は2016年以降に大幅に減衰した]]（Gao-Han-Li-Zhou 2018 の日中モメンタムが post-2016 に消失）。
- 関連: 知見 Q113（US500 の初動→終盤モメンタムは FX より強い）。
- 先行研究チェック（WebSearch 2026-10-14・英語・"intraday momentum first hour last hour SPY QQQ post-2016 decay index futures hourly"）:
  見つかったもの: Gao-Han-Li-Zhou (2018) "Market Intraday Momentum" JFE、Zarattini-Grego-Barbon-Pagano (2024) "Intraday Momentum in US Stocks: Trading or Not Trading?" SSRN。
  未確認: US500 / USTECH H1 で初動 1 時間 → 終盤 1 時間 の予測性を 2016 境界で比較し、符号並べ替え帰無で判定する実証は未確認（移植）。

【仮説（測る前に固定）】
H: pre（2011-09〜2016-12）の初動→終盤の相関と、post（2017-01〜2026-06）の相関で、
   r_pre − r_post > 0（post で減衰）かつ両期間とも |z|≥1.5 → 支持。
H0: r_pre − r_post の z<1 → 棄却。ほか → 未確定。

【データ】
US500・USTECH H1_dukascopy（2011-09〜2026-06）。
初動 1 時間: 14:00 UTC（NY 9:30 の近傍、14:30 の始まりは丸めで 14:00）。
終盤 1 時間: 20:00 UTC（NY 15:00〜16:00 の最後の 1 時間）。
（これらは SPY のレギュラー時間を H1 の UTC 時間足にざっくり当てたもので、実際の 9:30-10:30 や 15:00-16:00 と数十分ずれる可能性があるが、年度横断で同じ時刻を使うので比較は内部整合）。

【定義（1 通りに固定）】
- 初動 ret_open = log(close(14:00 UTC) / open(14:00 UTC)) を 1 日 1 値。
- 終盤 ret_close = log(close(20:00 UTC) / open(20:00 UTC)) を 1 日 1 値。
- 相関 r = Pearson(ret_open, ret_close)（銘柄別に全期間・前後半）。
- 差 Δ = r_pre − r_post（銘柄別・2 本）。

【測るもの】
r（全期間・前後半）、Δ、符号並べ替え B=1000 の p、2 銘柄分で Holm m=2。

【帰無】
銘柄内で日ごとに ret_open と ret_close のペアをシャッフル（ret_close の順序を並べ替え）→ 各並べ替えで Δ を再計算 → 観測との z・片側 p_right（side="greater"、post で減衰を示す向き）。

【判定（事前固定・変更禁止）】
Δ（r_pre − r_post）の p_right を 2 銘柄分 Holm 補正（m=2、α=0.05）:
- 支持: 2 銘柄とも Δ>0 かつ Holm 補正後 p<0.05
- 棄却: 全期間の |z_Δ|<1
- 未確定: ほか
補助情報: r_pre・r_post の符号。

【捨てた案の数】
約4: (i) FX（指数での議論が主）、(ii) H4 で統合（情報が薄い）、(iii) クローズのみ（Zarattini は open-to-close）、(iv) 全銘柄 15 でやる（指数以外の XAU などは別仮説）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

【実装】自己完結・決定的（乱数は帰無の並べ替えのみ seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_intraday_momentum_indices_decay_q297.py（B=1000、約 1 分）／--smoke --B 5
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q297"
DEFAULT_B = 1000
START = "2011-09-01"
KIND = "H1_dukascopy"
INDICES = ["US500", "USTECH"]
OPEN_HOUR = 14  # UTC（NY 9:30 の近傍を H1 の 14:00〜14:59 に丸める）
CLOSE_HOUR = 20  # UTC（NY 15:00〜16:00）


def _daily_bars(df, hour):
    """df は H1。hour の 1 時間だけ抜き、1 日 1 行の DataFrame（date, open, close, year）を返す。"""
    d = df.copy()
    d["dt"] = pd.to_datetime(d["time"])
    d = d[d["dt"].dt.hour == hour].reset_index(drop=True)
    d["date"] = d["dt"].dt.date
    return d[["date", "open", "close", "year"]]


def _corr(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]; y = y[m]
    if len(x) < 10 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def run(args, rng):
    syms = list(INDICES)
    hres = health(syms, kind=KIND)
    syms_ok, missing = syms_available(syms, kind=KIND, smoke=args.smoke)
    results = {}
    delta_list = []  # (sym, delta_obs, p_right)
    for sym in syms_ok:
        df = load_h1(sym, args.smoke, rng, n=120000, start=START)
        df = df[df["time"] >= pd.Timestamp(START)].reset_index(drop=True)
        if len(df) < 2000:
            continue
        open_bars = _daily_bars(df, OPEN_HOUR)
        close_bars = _daily_bars(df, CLOSE_HOUR)
        merged = pd.merge(open_bars, close_bars, on="date", suffixes=("_o", "_c"))
        if len(merged) < 100:
            continue
        merged["ret_open"] = np.log(merged["close_o"] / merged["open_o"])
        merged["ret_close"] = np.log(merged["close_c"] / merged["open_c"])
        merged["year"] = merged["year_o"]
        pre = merged[merged["year"] < SPLIT_YEAR]
        post = merged[merged["year"] >= SPLIT_YEAR]
        r_all = _corr(merged["ret_open"].values, merged["ret_close"].values)
        r_pre = _corr(pre["ret_open"].values, pre["ret_close"].values) if len(pre) >= 10 else np.nan
        r_post = _corr(post["ret_open"].values, post["ret_close"].values) if len(post) >= 10 else np.nan
        delta = r_pre - r_post if (not np.isnan(r_pre) and not np.isnan(r_post)) else np.nan
        # 帰無: ret_close をシャッフル
        nulls = []
        rc_all = merged["ret_close"].values
        ro_all = merged["ret_open"].values
        year_all = merged["year"].values
        for b in range(args.B):
            rc_perm = rng.permutation(rc_all)
            mask_pre = year_all < SPLIT_YEAR
            mask_post = year_all >= SPLIT_YEAR
            rp = _corr(ro_all[mask_pre], rc_perm[mask_pre]) if mask_pre.sum() >= 10 else np.nan
            rq = _corr(ro_all[mask_post], rc_perm[mask_post]) if mask_post.sum() >= 10 else np.nan
            nulls.append(rp - rq if (not np.isnan(rp) and not np.isnan(rq)) else np.nan)
        if np.isnan(delta):
            results[sym] = {"r_all": f(r_all), "r_pre": f(r_pre), "r_post": f(r_post),
                            "delta": None, "z": None, "p_right": None}
            delta_list.append((sym, np.nan, np.nan))
            continue
        z, pct = z_of(delta, nulls)
        pr = perm_p(delta, nulls, side="greater")
        results[sym] = {"r_all": f(r_all), "r_pre": f(r_pre), "r_post": f(r_post),
                        "delta": f(delta), "z": f(z), "p_right": f(pr)}
        delta_list.append((sym, delta, pr))
    # Holm 補正（m=2）
    pvals = [pr if not np.isnan(pr) else np.nan for _, _, pr in delta_list]
    adj = holm(pvals)
    for i, (sym, _, _) in enumerate(delta_list):
        results[sym]["p_holm"] = f(adj[i])
    sig_count = sum(1 for i, (sym, d, _) in enumerate(delta_list)
                    if adj[i] is not None and d is not None and not np.isnan(adj[i]) and not np.isnan(d) and adj[i] < 0.05 and d > 0)
    z_pool = [results[s]["z"] for s in results if results[s]["z"] is not None]
    max_abs_z = max([abs(z) for z in z_pool]) if z_pool else 0
    if sig_count == 2:
        verdict = f"支持: 2 銘柄とも Δ>0 かつ Holm 補正後 p<0.05（指数で日中モメンタムが post 減衰）"
    elif max_abs_z < 1:
        verdict = f"棄却: 全銘柄で |z_Δ|<1（{f(max_abs_z)}）"
    else:
        verdict = f"未確定: Holm 有意本数={sig_count}, max|z|={f(max_abs_z)}"
    res = {"question": "US500 / USTECH H1 の日中モメンタム（初動 → 終盤）は 2016 以降に減衰したか（GarciaArano2026-2 の指数 H1 移植）",
           "settings": {"syms": syms, "start": START, "split_year": SPLIT_YEAR,
                        "open_hour_utc": OPEN_HOUR, "close_hour_utc": CLOSE_HOUR,
                        "B": args.B, "n_tests": 2, "null": "ret_close のシャッフル",
                        "verdict_basis": "2 銘柄とも Δ=r_pre−r_post>0 かつ Holm 補正後 p<0.05 → 支持"},
           "missing": missing, "data_health": hres, "symbols": results,
           "machine_verdict": verdict,
           "multiple_comparisons": "判定は 2 銘柄の Δ p_right の Holm 補正（m=2）。前後半 r は記述。"}
    out_df = pd.DataFrame([{"sym": s, **results[s]} for s in results])
    return res, {"symbols": out_df}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
