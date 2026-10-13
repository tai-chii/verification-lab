#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q268: ECB 参照レート（14:15 CET）の前後にドルの V 字はあるか（Krohn 2024 のロンドン fix の移植・FX6 H1）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md の Q268 の行（Fable 2026-10-10・30案一括生成 第5弾）。
- [[Krohn2024-1_ドルはフィキシングに向けて上がりその後に下がり一日の中でW字になる]]、知見 Q056（ロンドン fix の V 字は 2020 以降弱い）、ECB 2015-12-07 プレスリリース（2016-07 から 14:15 CET に変更・それ以前 14:30）
- 先行研究チェック（WebSearch 2026-10-10・standard・検索語 "ECB reference rate 14:15 CET fixing exchange rate behaviour around fixing intraday pattern empirical"）:
  見つかったもの: Krohn・Mueller・Whelan「Foreign Exchange Fixings and Returns around the Clock」（WU 2022）、BIS 2022 Mueller スライド、ECB プレスリリース 2015-12-07。
  未確認: ECB fix 周りは論文で触れられるが、手元 H1・FX6・2008–2026 前後半・符号並べ替え帰無で判定する形は未確認（移植）。

【仮説（測る前に固定）】
H: ECB 参照レート時刻の前 1 時間（CET 13 時台）のドル（6 組等加重）は上がり、後 1 時間（14 時台）は下がる: D = pre − post > 0。

【データ】
FX6 H1_dukascopy（2008〜2026-06）。
（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の missing に書く。ネットは使わない）

【定義（1通りに固定）】
CET は Europe/Berlin（夏時間込み）。ドルのリターンは Q229 と同じ符号規則。2016-07-01 以降を主（14:15）、以前は 14:30 で同じ時間帯（副次）。対照: 同じ日の 10 時台 − 11 時台。

【測るもの】
D [bp] の年単位 t（全期間・前半 2008–2016／後半 2017–）、pre と post それぞれの平均。

【帰無】
日ごとの pre/post ラベルを入れ替える（符号並べ替え）B=2000 → D の帰無分布 → z。

【判定（事前固定・変更禁止）】
前後半とも D>0 かつ z≥2 → 支持。全期間 z<1 → 棄却。それ以外 → 未確定。
多重比較: 判定は D の前後半 2 本。対照・時刻変更前は記述。

【捨てた案の数】
約3: 15 分足（EURUSD・USDJPY しか無い）、月末だけ（Q229 と混ざる）、EUR 単独。

【知識の締め切り】
Claude の知識の締め切りはおよそ 2026-06。データは 2026-06（暗号資産は 2026-09）まで。規則は固定で相場観は使わない。
外部の暦（発表日など）を手で書いた箇所は「知識から記載・実行者が原典と照合」。

【委託の確かめ方】
設計は Fable（2026-10-10）、コードは Claude（Fable 5.1 の委託）。実行と解釈は Sonnet／Opus が後で行い、結論でなく JSON のパス・主要な統計量（t・z・前後半）・原典の箇所を返す。
machine_verdict は上の判定規則を機械的に当てたもので、確定／ノイズ／未確定の解釈は実行者が書く。

【実装】自己完結・決定的（乱数は帰無の並べ替えのみ seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_ecb_fix_q268.py            （B=2000・小（B=2000・1 分前後））
      python3 kensho_ecb_fix_q268.py --smoke    （合成データで経路の確認。判定には使わない）
"""
# fe_core 版（2026-10-13）: 共通の土台を tools/fe_core から読む。検証固有の部分は元のスクリプトと同一。
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403  — 雛形と同じ名前（load_h1・by_year_stats・z_of・write_result …）

QID = "Q268"
DEFAULT_B = 2000
START = "2008-01-01"
PAIRS = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "USDJPY": +1, "USDCHF": +1, "USDCAD": +1}  # Q229 と同じ符号規則（ドル高で +）
PRE_HOUR, POST_HOUR = 13, 14          # CET（Europe/Berlin）
CTL_PRE, CTL_POST = 10, 11
CHANGE_DATE = pd.Timestamp("2016-07-01")  # ECB 参照レートの公表時刻が 14:30 → 14:15 に変わった日（知識から記載・実行者が原典と照合）
KIND = "H1_dukascopy"


def usd_hourly(args, rng):
    cols = {}; missing = []
    for s, sgn in PAIRS.items():
        if not args.smoke and not exists_sym(s, KIND):
            missing.append(s); continue
        df = load_h1(s, args.smoke, rng, n=120000, start=START)
        df = df[df["time"] >= pd.Timestamp(START)]
        cols[s] = pd.Series(sgn * df["ret"].values * 1e4, index=df["time"].values)
    usd = pd.concat(cols, axis=1).mean(axis=1, skipna=True).dropna()
    return usd, missing


def run(args, rng):
    usd, missing = usd_hourly(args, rng)
    t = pd.DatetimeIndex(usd.index).tz_localize("UTC").tz_convert("Europe/Berlin")
    d = pd.DataFrame({"usd": usd.values, "date": t.tz_localize(None).normalize(), "hour": t.hour, "dow": t.dayofweek})
    d = d[d["dow"] < 5]
    piv = d.pivot_table(index="date", columns="hour", values="usd", aggfunc="first")
    need = [PRE_HOUR, POST_HOUR, CTL_PRE, CTL_POST]
    for h in need:
        if h not in piv.columns:
            piv[h] = np.nan
    day = pd.DataFrame({"date": piv.index, "pre": piv[PRE_HOUR].values, "post": piv[POST_HOUR].values,
                        "ctl_pre": piv[CTL_PRE].values, "ctl_post": piv[CTL_POST].values})
    day = day.dropna(subset=["pre", "post"]).reset_index(drop=True)
    day["D"] = day["pre"] - day["post"]; day["D_ctl"] = day["ctl_pre"] - day["ctl_post"]
    day["year"] = day["date"].dt.year
    day["regime"] = np.where(day["date"] >= CHANGE_DATE, "main_1415", "before_1430")
    if day.empty:
        return {"question": "ECB 参照レート時刻の前 1 時間のドルは上がり、後 1 時間は下がるか", "missing": missing, "summary": {},
                "machine_verdict": "未確定: 計算できない", "settings": {}, "multiple_comparisons": ""}, None

    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    # 帰無: 日ごとの pre/post ラベルを入れ替える（D の符号並べ替え）→ 年単位平均
    Dv = day["D"].values; yrs = day["year"].values
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
    for p in periods:
        z, pct = z_of(by_year_stats(day, "D", y0=periods[p][0], y1=periods[p][1])["mean"], null[p])
        summary["whole_sample"][p]["z"] = f(z); summary["whole_sample"][p]["pct"] = f(pct)
    summary["main_after_2016_07_01415"] = block(day[day["regime"] == "main_1415"], "D")
    summary["before_2016_07_1430"] = block(day[day["regime"] == "before_1430"], "D")
    summary["control_10h_minus_11h"] = block(day.dropna(subset=["D_ctl"]), "D_ctl", "ctl_pre", "ctl_post")
    w = summary["whole_sample"]
    vals = [w[p][k] for p in ("pre", "post") for k in ("D_bp", "z")] + [w["all"]["z"]]
    if any(v is None for v in vals):
        verdict = "未確定: 計算できない"
    elif all(w[p]["D_bp"] > 0 and w[p]["z"] >= 2 for p in ("pre", "post")):
        verdict = "支持: 前後半とも D>0 かつ z≥2"
    elif w["all"]["z"] < 1:
        verdict = "棄却: 全期間 z<1"
    else:
        verdict = "未確定"
    res = {"question": "ECB 参照レート時刻の前 1 時間（CET 13 時台）のドルは上がり、後 1 時間（14 時台）は下がるか（D=pre−post>0）",
           "settings": {"pairs": PAIRS, "tz": "Europe/Berlin", "pre_hour": PRE_HOUR, "post_hour": POST_HOUR, "control": f"{CTL_PRE} 時台 − {CTL_POST} 時台",
                        "change_date": str(CHANGE_DATE.date()), "start": START, "split_year": SPLIT_YEAR, "B": args.B,
                        "null": "日ごとに pre/post ラベルを入れ替え（D の符号並べ替え）→ 年単位平均",
                        "verdict_basis": "判定は同じ時間帯（13・14 時台）で全標本を 2017 で前後半に分けた whole_sample。主（2016-07-01 以降）・以前・対照は記述。"},
           "missing": missing, "summary": summary, "machine_verdict": verdict,
           "multiple_comparisons": "判定は D の前後半 2 本。対照・時刻変更前は記述。"}
    return res, {"daily": day}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
