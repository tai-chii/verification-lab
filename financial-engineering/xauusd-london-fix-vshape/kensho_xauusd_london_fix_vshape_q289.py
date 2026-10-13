#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q289: WM/Reuters 4pm fix（16:00 UTC）周辺の XAUUSD に V 字はあるか（Krohn 2024 の XAUUSD H1 移植）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-14「XAUUSD の 16:00 UTC 周辺の V 字」の行（Q289・10案一括生成 ターミナル版）。
- [[Krohn2024-1_ドルはフィキシングに向けて上がりその後に下がり一日の中でW字になる]]。
- 先行研究チェック（WebSearch 2026-10-14・英語・"XAUUSD gold London fix 16:00 UTC intraday V-shape fixing exchange rate behaviour empirical"）:
  見つかったもの: arxiv 1501.07778 Evans「Foreign Exchange Market Microstructure and the WM/Reuters 4pm Fix」(FX の 4pm fix 周辺のボラ上昇)。
  未確認: XAUUSD H1 で WM/Reuters 4pm fix の前 1 時間（UTC 15 時台）と後 1 時間（UTC 16 時台）のリターン差 D=pre−post を
  符号並べ替え帰無 B=1000 と年単位 t・前後半分割で判定する実証は未確認（移植）。
- 関連の自検証: Q268（ECB 14:15 CET fix・FX6 H1）、Q229（月末フィキシングのドル効果）、Q056（ロンドン fix の V 字 2020 以降弱い）。

【仮説（測る前に固定）】
H: XAUUSD H1 で WM/Reuters 4pm fix 時刻（UTC 16:00）の前 1 時間のリターン pre と後 1 時間のリターン post の差 D=pre−post>0。
金はドル建てなのでドル上昇で金価格は下がる。Krohn の「fix に向けてドルが上がる」が本当なら、金は fix 前にマイナス、fix 後にプラスで D<0 が予想される。
事前登録では両側ではなく pre−post>0 を H とし、符号は結果の記述に残す（主張の移植の忠実性のため、ドルの D>0 と同じ方向で測る＝金では D<0 を予想するが、片側ではなく z の大きさで判定）。

【データ】XAUUSD H1_dukascopy（2008〜2026-06）。`検証/学問/金融工学/作業/FX/システムトレード/data_XAUUSD_H1_dukascopy.csv`。無ければ JSON の missing に書く。

【定義（1 通りに固定）】
- UTC で解釈。pre_hour=15、post_hour=16。対照 ctl_pre=10、ctl_post=11。
- 日次リターン [bp]（close→close、各時間足の ret×1e4）。日ごとに dow<5（土日除外）、UTC 日付でピボット。
- 期間: 全期間、前半 year<2017、後半 year≥2017。

【測るもの】
D [bp] の年単位 t（全期間・前半・後半）、pre と post それぞれの平均。|z| で判定するが片側確率も記す。

【帰無】
日ごとに D の符号を並べ替え（B=1000）→ D の帰無分布 → z（両側）と perm_p（両側 side="two"）。

【判定（事前固定・変更禁止）】
- 支持: 前後半とも |D| の平均が有意（|z|≥2）かつ pre と post の符号が逆（V 字 or 逆 V 字が維持される）。
- 棄却: 全期間 |z|<1 → fix 周辺の構造は見えない。
- それ以外 → 未確定。
多重比較: 判定は D の前後半 2 本（Holm で補正）。対照（10 時台 − 11 時台）は記述。

【捨てた案の数】約3: (i) M15（XAUUSD の M15 は yahoo のみで dukascopy なし）、(ii) BTC（24 時間取引で fix 無関係）、(iii) XAGUSD 単独（金より流動性が低く別仮説）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。
WM/Reuters fix の時刻（UTC 16:00、英 BST 中は UTC 15:00 に変動）は知識から記載・実行者が原典と照合。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

【実装】自己完結・決定的（乱数は帰無の並べ替えのみ seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_xauusd_london_fix_vshape_q289.py（B=1000、約 1 分）
      python3 kensho_xauusd_london_fix_vshape_q289.py --smoke --B 5（経路確認）
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q289"
DEFAULT_B = 1000
START = "2008-01-01"
SYM = "XAUUSD"
KIND = "H1_dukascopy"
PRE_HOUR, POST_HOUR = 15, 16  # UTC
CTL_PRE, CTL_POST = 10, 11


def run(args, rng):
    hres = health([SYM], kind=KIND, bar="H1")
    if hres["failed"]:
        return {"question": "XAUUSD の 16:00 UTC 周辺に V 字はあるか", "missing": [], "data_health": hres,
                "summary": {}, "machine_verdict": "未確定: データ読み込み失敗", "settings": {},
                "multiple_comparisons": "判定は D の前後半 2 本"}, None
    missing = [SYM] if SYM in hres["no_data"] and not args.smoke else []
    if missing:
        return {"question": "XAUUSD の 16:00 UTC 周辺に V 字はあるか", "missing": missing, "data_health": hres,
                "summary": {}, "machine_verdict": "未確定: 計算できない", "settings": {},
                "multiple_comparisons": ""}, None

    df = load_h1(SYM, args.smoke, rng, n=140000, start=START)
    df = df[df["time"] >= pd.Timestamp(START)]
    df["ret_bp"] = df["ret"].values * 1e4
    df["date"] = pd.DatetimeIndex(df["time"]).normalize()
    df["dow"] = pd.DatetimeIndex(df["time"]).dayofweek
    df = df[df["dow"] < 5]

    piv = df.pivot_table(index="date", columns="hour", values="ret_bp", aggfunc="first")
    for h in [PRE_HOUR, POST_HOUR, CTL_PRE, CTL_POST]:
        if h not in piv.columns:
            piv[h] = np.nan
    day = pd.DataFrame({"date": piv.index, "pre": piv[PRE_HOUR].values, "post": piv[POST_HOUR].values,
                        "ctl_pre": piv[CTL_PRE].values, "ctl_post": piv[CTL_POST].values})
    day = day.dropna(subset=["pre", "post"]).reset_index(drop=True)
    day["D"] = day["pre"] - day["post"]
    day["D_ctl"] = day["ctl_pre"] - day["ctl_post"]
    day["year"] = pd.DatetimeIndex(day["date"]).year

    if day.empty:
        return {"question": "XAUUSD の 16:00 UTC 周辺に V 字はあるか", "missing": missing, "data_health": hres,
                "summary": {}, "machine_verdict": "未確定: 計算できない", "settings": {},
                "multiple_comparisons": ""}, None

    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    Dv = day["D"].values
    yrs = day["year"].values
    uy, yi = np.unique(yrs, return_inverse=True)
    null = {p: [] for p in periods}
    for b in range(args.B):
        sg = rng.choice([-1.0, 1.0], size=len(Dv))
        ym = np.bincount(yi, weights=sg * Dv) / np.bincount(yi)
        for p, (y0, y1) in periods.items():
            m = (uy >= y0) & (uy < y1)
            null[p].append(ym[m].mean() if m.any() else np.nan)

    def block(sub, col, cpre="pre", cpost="post"):
        out = {}
        for p, (y0, y1) in periods.items():
            st = by_year_stats(sub, col, y0=y0, y1=y1)
            pm = sub[(sub["year"] >= y0) & (sub["year"] < y1)]
            out[p] = {"n_years": st["n_years"], "n_days": int(len(pm)), f"{col}_bp": f(st["mean"]), "t": f(st["t"]),
                      "pre_bp": f(pm[cpre].mean()) if len(pm) else None, "post_bp": f(pm[cpost].mean()) if len(pm) else None}
        return out

    summary = {"whole_sample": block(day, "D")}
    perm_ps = {}
    for p in periods:
        obs = by_year_stats(day, "D", y0=periods[p][0], y1=periods[p][1])["mean"]
        z, pct = z_of(obs, null[p])
        summary["whole_sample"][p]["z"] = f(z)
        summary["whole_sample"][p]["pct"] = f(pct)
        pp = perm_p(obs, null[p], side="two")
        summary["whole_sample"][p]["perm_p_two"] = f(pp)
        perm_ps[p] = pp
    summary["control_10h_minus_11h"] = block(day.dropna(subset=["D_ctl"]), "D_ctl", "ctl_pre", "ctl_post")

    # Holm 補正: 判定は D の前後半 2 本
    p_pre = perm_ps["pre"] if perm_ps["pre"] is not None and not np.isnan(perm_ps["pre"]) else 1.0
    p_post = perm_ps["post"] if perm_ps["post"] is not None and not np.isnan(perm_ps["post"]) else 1.0
    adj = holm([p_pre, p_post])
    summary["holm_adj_p"] = {"pre": f(adj[0]), "post": f(adj[1])}

    w = summary["whole_sample"]
    def _sign(x):
        return 1 if x is not None and x > 0 else (-1 if x is not None and x < 0 else 0)
    pre_z = w["pre"]["z"]
    post_z = w["post"]["z"]
    all_z = w["all"]["z"]
    verdict = "未確定"
    try:
        if any(v is None for v in [pre_z, post_z, all_z]):
            verdict = "未確定: 計算できない"
        elif abs(pre_z) >= 2 and abs(post_z) >= 2 and _sign(w["pre"]["pre_bp"]) != _sign(w["pre"]["post_bp"]) and _sign(w["post"]["pre_bp"]) != _sign(w["post"]["post_bp"]):
            verdict = "支持: 前後半とも |z|≥2 かつ pre と post の符号が逆"
        elif abs(all_z) < 1:
            verdict = "棄却: 全期間 |z|<1"
    except Exception as e:  # noqa: BLE001
        verdict = f"未確定: 判定計算失敗 ({e})"

    res = {"question": "XAUUSD H1 で 16:00 UTC 周辺に pre−post の構造（V 字）はあるか",
           "settings": {"sym": SYM, "tz": "UTC", "pre_hour": PRE_HOUR, "post_hour": POST_HOUR,
                        "control": f"{CTL_PRE} 時台 − {CTL_POST} 時台", "start": START, "split_year": SPLIT_YEAR,
                        "B": args.B, "null": "日ごとに D の符号並べ替え → 年単位平均", "side": "two",
                        "verdict_basis": "判定は D の前後半 2 本（Holm で補正）。対照・|z| と符号。"},
           "missing": missing, "data_health": hres, "summary": summary, "machine_verdict": verdict,
           "multiple_comparisons": "判定は D の前後半 2 本（Holm で補正）。対照は記述。"}
    return res, {"daily": day}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
