#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q284: 月末前4日の前倒し山は FX8 の日足に残っているか（Q283-C1・Girgin 2026 の pre-TOM 前倒しを FX に移植）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-13 「月末前4日の前倒し山は FX8 の日足に残っているか」の行（Q283-C1）。
- 接続ログ 2026-10-13・Q283-C1（移植）: Girgin2026-1_有名な4日は平凡で最強は月末前の4営業日 を FX8 に移植。
  先行研究チェック済（2026-10-13、関連: Krohn2024-1 ドルフィキシング W 字、Melvin・Prins 2015 月末日ドル効果、Aydoğan・Booth 2003 Turkish lira TOM。
  「主要通貨 D1 で月末からの営業日オフセット (−6〜+3) ごとの日平均リターンに前倒し山があるか」の実証は見つからない）。
- 関連の自検証: Q181（SPX/US500/USTECH で古典窓 C={−1,+1,+2,+3} と前倒し窓 S={−4,−3,−2} の DiD → 棄却）。

【仮説（測る前に固定）】
H1（Girgin 2026 のブログ主張の移植）: FX8 の D1 で、月末からの営業日オフセット k ∈ {−6..−1, +1..+3} の日平均リターンが、
前半 (≤2016)・後半 (≥2017) のどちらでも「同じ k で」月内ランダム帰無の上位 5% に入る → 前倒し山が FX8 でも成立。
H0: どのオフセットも帰無上位 5% に入らない、または上位 5% に入るオフセットが前後半で一致しない（＝ FX8 日足には前倒し山は見えない）。

【データ】FX8（EURUSD・GBPUSD・AUDUSD・USDJPY・USDCHF・USDCAD・EURJPY・GBPJPY）D1_fromH1、2008-01〜2026-06（EURJPY は 2026-03 まで）。
Dukascopy 由来（手元の `検証/学問/金融工学/作業/FX/システムトレード/data_<SYM>_D1_fromH1.csv`）。価格のみ・コスト0 の粗利段階1。

【定義（1通りに固定）】
- 各日の k（月末からの営業日位置）: 月の最初の 3 営業日を +1, +2, +3、月の最終営業日を −1、その前を −2, −3, ... とする。
  Q181 と同じ規則（_positions 関数）だが、+3 までで打ち切らず k ∈ {−6..−1, +1..+3} の 9 点を対象とする（アイデア候補の「10 点」は内部カウントの食い違い。
  数学的には月内に k=0 の営業日はなく、9 点が正。事前登録からの変更点としてここに明記）。
- 日次リターン [bp]（終値→終値、% × 1e4）。
- FX8 プール平均: 各 (期間, オフセット) について、FX8 の 8 本の pair-level 平均リターンの単純平均（等ウェイト。pair-day の数の違いを均す）。
- 期間: 前半 year < 2017、後半 year ≥ 2017。
- 帰無: 各 (pair, ym) の中で位置ラベル win（k の値そのもの）を並べ替える（B=1000）。各並べ替えで FX8 プール平均を再計算し、オフセットごとの帰無分布を作る。
- 片側 p 値: p_right = (null >= observed の割合)。「ランダム上位 5%」= p_right < 0.05。

【判定（事前固定・変更禁止）】
- 支持: 前後半とも「p_right < 0.05 のオフセットが 1 点以上」存在し、かつ 両期間で共通するオフセットが 1 点以上。
- 棄却: どちらかの期間で p_right < 0.05 のオフセットが 0 点、または 両期間に共通するオフセットが 0 点。
- 未確定: 上の二分法で分類できる想定（アイデア候補の棄却条件は上の棄却の否定＝支持と同値）。
補助情報: Girgin の主張する pre-TOM 窓 S={−4,−3,−2} に属するオフセットが共通集合に入るかを別途記録する（判定自体は変えない）。

【捨てた案の数】約4: (i) 月末の位置を暦日で取る案 → 営業日で（Q181 と揃える）、(ii) pair-day の等ウェイト案 → pair の等ウェイト（pair ごとの n の差を均す）、
(iii) 通貨ごとに判定して多数決の案 → FX8 プールで単一判定（アイデア候補の文面）、(iv) 配当調整 → FX は配当なしなので無関係。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06（EURJPY は 2026-03）。締め切り後の独立標本は無い。
Girgin 2026 のブログは 2026-09 時点のスライド窓で、本検証の期間とほぼ重なる（独立標本ではない。これは FX8 への「移植」であって Girgin の SPY 標本の再利用ではない点で、独立標本の懸念は小さい）。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体。委託なし。

【実装】自己完結。実行: python3 kensho_turn_of_month_shift_fx8_q284.py（B=1000、1 分前後）。--B 100 で短縮・--smoke で経路確認（判定不可）。
"""

# ============================================================================= 共通の土台
import argparse
import datetime as _dt
import json
import math
import os
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def _p(*parts):
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
OUT = os.path.join(HERE, "results")
FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
SPLIT_YEAR = 2017
SEED = 20261013
OFFSETS = [-6, -5, -4, -3, -2, -1, 1, 2, 3]
PRE_TOM_WIN = {-4, -3, -2}  # Girgin の pre-TOM 窓（判定を変えないための参考情報）


def _read(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def load_d1(sym):
    df = _read(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 1e4  # [bp]
    df["year"] = df["time"].dt.year
    df["ym"] = df["time"].dt.year * 100 + df["time"].dt.month
    return df.dropna(subset=["ret"]).reset_index(drop=True)


def _smoke_ohlc(sym, rng, n=4800, start="2008-01-01"):
    t = pd.bdate_range(start, periods=n)
    r = rng.normal(0.0, 0.006, n)
    c = 1.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.001, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.001, n)))
    df = pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c})
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 1e4
    df["year"] = df["time"].dt.year
    df["ym"] = df["time"].dt.year * 100 + df["time"].dt.month
    return df.dropna(subset=["ret"]).reset_index(drop=True)


def assign_k(df):
    """月末からの営業日オフセット k を付ける。先頭 3 本は +1,+2,+3、その他は末尾基準の負数。"""
    d = df.copy()
    d["k_from_start"] = d.groupby("ym").cumcount() + 1
    d["k_from_end"] = -(d.groupby("ym").cumcount(ascending=False) + 1)
    d["k"] = np.where(d["k_from_start"] <= 3, d["k_from_start"], d["k_from_end"])
    return d


def period_mean_by_k(d, period_mask):
    """特定期間の各オフセットの平均リターン [bp] を Series で返す（OFFSETS に揃える・欠損は NaN）。"""
    sub = d[period_mask]
    g = sub.groupby("k")["ret"].mean()
    return pd.Series({k: g.get(k, np.nan) for k in OFFSETS})


def fx8_pooled(per_pair_means):
    """per_pair_means: {sym: Series(index=OFFSETS)} → FX8 プール（単純平均・NaN は 0 本として除外）."""
    df = pd.DataFrame(per_pair_means).T  # rows: sym, cols: OFFSETS
    return df.mean(axis=0, skipna=True)


def permute_within_ym(rng, k_vals, ym_vals):
    """各 ym の中で k を並べ替える（多重集合は保つ）."""
    out = np.asarray(k_vals).copy()
    g = np.asarray(ym_vals)
    for v in np.unique(g):
        idx = np.where(g == v)[0]
        out[idx] = out[rng.permutation(idx)]
    return out


def run(args, rng):
    smoke = args.smoke
    B = args.B

    data = {}
    missing = []
    for sym in FX8:
        path = os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv")
        if smoke:
            df = _smoke_ohlc(sym, rng)
        elif not os.path.exists(path):
            missing.append(sym)
            continue
        else:
            df = load_d1(sym)
        d = assign_k(df)
        data[sym] = d
        print(f"{sym}: n={len(d)}, {d['time'].min().date()} 〜 {d['time'].max().date()}")

    if not data:
        return {"error": "no data"}, None

    # ----- 観測
    obs_pre_per_pair, obs_post_per_pair = {}, {}
    n_pre_per_pair, n_post_per_pair = {}, {}
    for sym, d in data.items():
        pre_mask = d["year"] < SPLIT_YEAR
        post_mask = d["year"] >= SPLIT_YEAR
        obs_pre_per_pair[sym] = period_mean_by_k(d, pre_mask)
        obs_post_per_pair[sym] = period_mean_by_k(d, post_mask)
        n_pre_per_pair[sym] = int(pre_mask.sum())
        n_post_per_pair[sym] = int(post_mask.sum())

    obs_pre = fx8_pooled(obs_pre_per_pair)  # Series(index=OFFSETS)
    obs_post = fx8_pooled(obs_post_per_pair)

    # ----- 帰無
    null_pre = {k: np.empty(B) for k in OFFSETS}
    null_post = {k: np.empty(B) for k in OFFSETS}

    for b in range(B):
        pre_per_pair = {}
        post_per_pair = {}
        for sym, d in data.items():
            kp = permute_within_ym(rng, d["k"].values, d["ym"].values)
            dd = d.assign(k=kp)
            pre_per_pair[sym] = period_mean_by_k(dd, dd["year"] < SPLIT_YEAR)
            post_per_pair[sym] = period_mean_by_k(dd, dd["year"] >= SPLIT_YEAR)
        pre_pool = fx8_pooled(pre_per_pair)
        post_pool = fx8_pooled(post_per_pair)
        for k in OFFSETS:
            null_pre[k][b] = pre_pool.get(k, np.nan)
            null_post[k][b] = post_pool.get(k, np.nan)
        if (b + 1) % max(1, B // 10) == 0:
            print(f"  perm {b+1}/{B}")

    # ----- p 値・z
    rows = []
    top5_pre, top5_post = [], []
    for k in OFFSETS:
        o_pre = float(obs_pre[k]) if np.isfinite(obs_pre[k]) else np.nan
        o_post = float(obs_post[k]) if np.isfinite(obs_post[k]) else np.nan
        np_pre = null_pre[k][np.isfinite(null_pre[k])]
        np_post = null_post[k][np.isfinite(null_post[k])]
        p_right_pre = float((np_pre >= o_pre).mean()) if (len(np_pre) and np.isfinite(o_pre)) else np.nan
        p_right_post = float((np_post >= o_post).mean()) if (len(np_post) and np.isfinite(o_post)) else np.nan
        z_pre = (o_pre - np_pre.mean()) / np_pre.std(ddof=1) if (len(np_pre) >= 3 and np_pre.std(ddof=1) > 0) else np.nan
        z_post = (o_post - np_post.mean()) / np_post.std(ddof=1) if (len(np_post) >= 3 and np_post.std(ddof=1) > 0) else np.nan
        if np.isfinite(p_right_pre) and p_right_pre < 0.05:
            top5_pre.append(k)
        if np.isfinite(p_right_post) and p_right_post < 0.05:
            top5_post.append(k)
        rows.append({
            "k": k,
            "obs_pre_bp": round(o_pre, 3) if np.isfinite(o_pre) else None,
            "obs_post_bp": round(o_post, 3) if np.isfinite(o_post) else None,
            "null_mean_pre_bp": round(float(np_pre.mean()), 3) if len(np_pre) else None,
            "null_mean_post_bp": round(float(np_post.mean()), 3) if len(np_post) else None,
            "z_pre": round(float(z_pre), 3) if np.isfinite(z_pre) else None,
            "z_post": round(float(z_post), 3) if np.isfinite(z_post) else None,
            "p_right_pre": round(p_right_pre, 4) if np.isfinite(p_right_pre) else None,
            "p_right_post": round(p_right_post, 4) if np.isfinite(p_right_post) else None,
            "top5_pre": (np.isfinite(p_right_pre) and p_right_pre < 0.05),
            "top5_post": (np.isfinite(p_right_post) and p_right_post < 0.05),
        })

    overlap = sorted(set(top5_pre) & set(top5_post))
    overlap_in_pretom = sorted(set(overlap) & PRE_TOM_WIN)

    if len(top5_pre) >= 1 and len(top5_post) >= 1 and len(overlap) >= 1:
        verdict = "支持: 前倒し山（共通する上位5%オフセットあり）"
    else:
        if len(top5_pre) == 0 or len(top5_post) == 0:
            verdict = "棄却: どちらかの期間で上位5%オフセットが0点"
        else:
            verdict = "棄却: 前後半で上位5%オフセットが一致しない"

    # 共通集合が Girgin の pre-TOM 窓 S={−4,−3,−2} を含むかの併記（判定を変えない）
    pretom_note = {
        "pre_tom_window": sorted(list(PRE_TOM_WIN)),
        "overlap_in_pre_tom_window": overlap_in_pretom,
        "support_pre_tom": verdict.startswith("支持") and len(overlap_in_pretom) >= 1,
    }

    res = {
        "question": "月末前4日の前倒し山は FX8 の日足（D1_fromH1、2008-01〜2026-06）に残っているか（Girgin 2026 ブログの FX 移植）",
        "settings": {
            "symbols": FX8,
            "split_year": SPLIT_YEAR,
            "offsets": OFFSETS,
            "B": B,
            "seed": args.seed,
            "pooling": "FX8 の単純平均（pair 単位の等ウェイト）",
            "null": "各 (pair, ym) の中で k ラベルを並べ替え",
            "p_rule": "p_right < 0.05 を上位5%とみなす",
        },
        "missing": missing,
        "n_pre_per_pair": n_pre_per_pair,
        "n_post_per_pair": n_post_per_pair,
        "per_offset": rows,
        "top5_pre_offsets": top5_pre,
        "top5_post_offsets": top5_post,
        "overlap_offsets": overlap,
        "machine_verdict": verdict,
        "pre_tom_check": pretom_note,
        "pre_registered_deviation": (
            "アイデア候補の「−6〜+3、計10点」は内部カウントの食い違い。"
            "営業日の k=0 は存在しないため 9 点（{−6..−1, +1..+3}）で実装。判定規則そのものは変えていない。"
        ),
        "data_range_note": (
            "EURJPY は 2026-03-31 までで他ペア（2026-06-30）より短い。pair ごとの n は n_pre_per_pair/n_post_per_pair を参照。"
        ),
    }

    # CSV（per_offset を書き出す）
    cells = pd.DataFrame(rows)
    return res, {"cells": cells}


def write_result(qid, res, smoke, extra_csv=None):
    os.makedirs(OUT, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    path = os.path.join(OUT, f"{pre}_result_{ts}.json")
    out_res = {"qid": qid, "smoke": smoke, "generated": ts, **res}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out_res, f, ensure_ascii=False, indent=1, default=_json_default)
    print("wrote", os.path.relpath(path, HERE))
    if extra_csv is not None:
        for name, df in extra_csv.items():
            cp = os.path.join(OUT, f"{pre}_{name}_{ts}.csv")
            df.to_csv(cp, index=False)
            print("wrote", os.path.relpath(cp, HERE))
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp, _dt.datetime, _dt.date)):
        return str(o)
    return str(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=1000)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result("Q284", res, args.smoke, csvs)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
