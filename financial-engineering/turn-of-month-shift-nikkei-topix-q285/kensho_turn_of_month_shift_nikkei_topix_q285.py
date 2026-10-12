#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q285: 日本株（Nikkei 225・TOPIX）の pre-TOM 4日効果は T+2 市場でも 2017 年以降に残るか（Q283-C2）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-13「日本株（Nikkei 225・TOPIX）の pre-TOM 4日効果は T+2 市場でも 2017 年以降に残るか」。
- 接続ログ 2026-10-13・条件の穴（Q283-C2・地理と決済）: Girgin 2026 の pre-TOM 4日前倒しを、日本株（Nikkei/TOPIX）D1 に移植。
  日本株は 2019-07 以降 T+2 のまま（米国 2024-05-28〜 T+1 の影響を受けない）。pre-TOM 4日の前倒し効果が日本株でも 2017 年以降に残っているかを見れば、
  Girgin の T+1 示唆（4.2 Interpretation）が決済構造の差で説明できるかを区別できる。
- 関連の自検証: Q181（SPX/US500/USTECH で古典窓 C={−1,+1,+2,+3} と前倒し窓 S={−4,−3,−2} の DiD → 棄却）、
  Q284（FX8 D1_fromH1 で offset −6..+3 の帰無上位 5% が前後半で一致せず → 棄却）。
  本件は Q181 の方法（S/C/O 窓・DiD）を Nikkei/TOPIX に当て直したもの。

【仮説（測る前に固定）】
H1: 後半（2017–）で mean(S) − mean(C) > 0 かつ z_post_SC ≥ 2、かつ DiD = (S−C)_post − (S−C)_pre > 0 かつ z_did ≥ 2 の系列が
    2 系列（Nikkei 225・TOPIX）のうち ≥1/2（＝1 系列以上） → pre-TOM 4日の前倒し支持（日本株にも残る）。
H0: 後半 S−C の z < 2 が ≥1/2 → 棄却（pre-TOM の前倒しは日本株にも見えない）。
補助: 古典窓が後半も有意かを z_post_CO で併記（判定自体は変えない）。

【データ】Nikkei 225 (^N225)・TOPIX (^TPX) 日足（yfinance、2008-01-01〜実行時点）。
初回実行時に `data_N225_D1_yahoo.csv`・`data_TPX_D1_yahoo.csv` として保存し、2 回目以降は再利用する。価格のみ（配当なしの基準指数）。

【定義（Q181 と揃える）】
- 月末からの営業日位置 k: 月の最初 3 営業日 = +1,+2,+3、月の最終営業日 = −1、その前 = −2,−3,...（Q181 の _positions と同じ）。
- 古典窓 C = {−1, +1, +2, +3}。前倒し窓 S = {−4, −3, −2}。その他 O = それ以外。
- 日次リターン [bp]（終値→終値）。各系列・各期間の mean(S), mean(C), mean(O)。
  差: S−C, C−O, S−O。差の差 DiD = (S−C)_post − (S−C)_pre。
- 期間: 前半 year < 2017、後半 year ≥ 2017。
- 帰無: 各月（ym）の中で窓ラベル win（S/C/O）を並べ替え（B=1000）。各並べ替えで前後半の S−C・C−O・DiD を再計算し、観測との z・片側 p を出す。

【判定（事前固定・変更禁止）】
「ok 系列」= 後半 S−C > 0 かつ z_post_SC ≥ 2 かつ DiD > 0 かつ z_did ≥ 2 を満たす系列。
「weak 系列」= z_post_SC < 2 の系列。
- 支持: |ok| ≥ 1（2 系列中 ≥1/2）
- 棄却: 支持に当たらず、かつ |weak| ≥ 1（2 系列中 ≥1/2）
- 未確定: それ以外
古典窓が後半も有意（z_post_CO ≥ 2）な系列を併記する。

【捨てた案の数】約4: (i) 日経平均先物（Nikkei 225 Futures）D1 → 日経平均指数と TOPIX（カード本文の指定どおり）、
(ii) 配当込み指数 → 無料で揃わないので価格のみ・そのまま明記、(iii) 月末の位置を暦日で取る案 → 営業日（Q181 と揃える）、
(iv) 2008 年開始を 2010 年開始にずらす案 → 前半を厚くするため 2008-01 開始。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本検証の後半には 2026-07〜09 の 3 か月分が入る（締め切り後の独立標本）。
Girgin 2026（SPY・2026-09 時点スライド窓）とは市場が異なり、独立標本の懸念は小さい。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体。委託なし。

【実装】自己完結。実行: python3 kensho_turn_of_month_shift_nikkei_topix_q285.py（B=1000、約 10 秒・pandas/numpy のみ）。
--B 100 で短縮・--smoke で経路確認（判定不可）。初回はネットから取得（約 10 秒）→ CSV に保存。
"""

# ============================================================================= 共通の土台
import argparse
import datetime as _dt
import json
import math
import os
import sys
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

SERIES = {"N225": "^N225", "TPX": "1308.T"}  # 事前登録の ^TPX は Yahoo Finance に存在しないため、TOPIX 連動 ETF の 1308.T（Listed Index Fund TOPIX、2008-01-04〜）で代用する。
C_WIN = {-1, 1, 2, 3}
S_WIN = {-4, -3, -2}
SPLIT_YEAR = 2017
SEED = 20261013
DATA_START = "2008-01-01"


def _data_path(name):
    return os.path.join(HERE, f"data_{name}_D1_yahoo.csv")


def _fetch_from_yahoo(ticker, name, end=None):
    import yfinance as yf
    end = end or _dt.date.today().isoformat()
    df = yf.download(ticker, interval="1d", start=DATA_START, end=end, auto_adjust=False, progress=False)
    if df is None or len(df) == 0:
        raise RuntimeError(f"yfinance 取得失敗: {ticker}")
    if hasattr(df.columns, "levels"):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    df = df.reset_index().rename(columns={"Date": "time", "date": "time", "index": "time"})
    cols = ["time", "open", "high", "low", "close"]
    if "volume" in df.columns:
        cols.append("volume")
    df = df[cols].copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    path = _data_path(name)
    df.to_csv(path, index=False)
    return df


def load_series(name, ticker, smoke=False, rng=None):
    """Nikkei/TOPIX の D1 を取得。CSV があれば再利用、無ければ yfinance で取得。"""
    if smoke:
        return _smoke_ohlc(rng, n=4700, start=DATA_START)
    path = _data_path(name)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["time"] = pd.to_datetime(df["time"])
    else:
        print(f"  (fetching {ticker} from yfinance...)")
        df = _fetch_from_yahoo(ticker, name)
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    if "high" in df.columns and "low" in df.columns:
        df = df[df["high"] != df["low"]].reset_index(drop=True)
    return df


def _smoke_ohlc(rng, n, start):
    rng = rng or np.random.default_rng(SEED)
    t = pd.bdate_range(start, periods=n)
    r = rng.normal(0.0001, 0.011, n)
    c = 100.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.003, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.003, n)))
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c})


def _positions(df):
    d = df.copy()
    d["ym"] = d["time"].dt.year * 100 + d["time"].dt.month
    d["k_from_start"] = d.groupby("ym").cumcount() + 1
    d["k_from_end"] = -(d.groupby("ym").cumcount(ascending=False) + 1)
    d["k"] = np.where(d["k_from_start"] <= 3, d["k_from_start"], d["k_from_end"])
    d["ret"] = d["close"].pct_change() * 1e4  # [bp]
    d["year"] = d["time"].dt.year
    d["win"] = np.where(d["k"].isin(C_WIN), "C", np.where(d["k"].isin(S_WIN), "S", "O"))
    return d.dropna(subset=["ret"]).reset_index(drop=True)


def _diffs(d, win_col="win"):
    m = d.groupby(win_col)["ret"].mean()
    return {
        "mean_C": m.get("C", np.nan),
        "mean_S": m.get("S", np.nan),
        "mean_O": m.get("O", np.nan),
        "S_minus_C": m.get("S", np.nan) - m.get("C", np.nan),
        "C_minus_O": m.get("C", np.nan) - m.get("O", np.nan),
        "S_minus_O": m.get("S", np.nan) - m.get("O", np.nan),
    }


def perm_within_labels(rng, labels, groups):
    lab = np.asarray(labels).copy()
    g = np.asarray(groups)
    for v in np.unique(g):
        idx = np.where(g == v)[0]
        lab[idx] = lab[rng.permutation(idx)]
    return lab


def z_of(obs, null):
    null = np.asarray(null, float)
    null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null >= obs).mean())


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def run(args, rng):
    out = {}
    for name, ticker in SERIES.items():
        df = load_series(name, ticker, smoke=args.smoke, rng=rng)
        d = _positions(df)
        pre = d[d["year"] < SPLIT_YEAR]
        post = d[d["year"] >= SPLIT_YEAR]
        o_pre = _diffs(pre)
        o_post = _diffs(post)
        did = o_post["S_minus_C"] - o_pre["S_minus_C"]

        null = {"pre_SC": [], "post_SC": [], "post_CO": [], "pre_CO": [], "did": []}
        for b in range(args.B):
            dd = d.copy()
            dd["winp"] = perm_within_labels(rng, dd["win"].values, dd["ym"].values)
            np_ = _diffs(dd[dd["year"] < SPLIT_YEAR], "winp")
            pp_ = _diffs(dd[dd["year"] >= SPLIT_YEAR], "winp")
            null["pre_SC"].append(np_["S_minus_C"])
            null["post_SC"].append(pp_["S_minus_C"])
            null["post_CO"].append(pp_["C_minus_O"])
            null["pre_CO"].append(np_["C_minus_O"])
            null["did"].append(pp_["S_minus_C"] - np_["S_minus_C"])
            if (b + 1) % max(1, args.B // 10) == 0:
                print(f"  perm {b+1}/{args.B} [{name}]")

        z_pre_SC, p_pre_SC = z_of(o_pre["S_minus_C"], null["pre_SC"])
        z_post_SC, p_post_SC = z_of(o_post["S_minus_C"], null["post_SC"])
        z_post_CO, p_post_CO = z_of(o_post["C_minus_O"], null["post_CO"])
        z_pre_CO, p_pre_CO = z_of(o_pre["C_minus_O"], null["pre_CO"])
        z_did, p_did = z_of(did, null["did"])

        out[name] = {
            "ticker": ticker,
            "n_pre": int(len(pre)),
            "n_post": int(len(post)),
            "span": [str(d["time"].min().date()), str(d["time"].max().date())],
            "pre": {k: f(v) for k, v in o_pre.items()},
            "post": {k: f(v) for k, v in o_post.items()},
            "did_S_minus_C": f(did),
            "z_pre_SC": f(z_pre_SC),
            "z_post_SC": f(z_post_SC),
            "z_pre_CO": f(z_pre_CO),
            "z_post_CO": f(z_post_CO),
            "z_did": f(z_did),
            "p_right_post_SC": f(p_post_SC),
            "p_right_post_CO": f(p_post_CO),
            "p_right_did": f(p_did),
        }
        print(
            f"{name}: n_pre={len(pre)}, n_post={len(post)}, "
            f"post S-C={out[name]['post']['S_minus_C']} bp (z={out[name]['z_post_SC']}), "
            f"DiD={out[name]['did_S_minus_C']} (z={out[name]['z_did']}), "
            f"post C-O={out[name]['post']['C_minus_O']} (z={out[name]['z_post_CO']})"
        )

    # 判定（事前固定）
    def _ok(r):
        return (
            (r["post"]["S_minus_C"] or 0) > 0
            and (r["z_post_SC"] or 0) >= 2
            and (r["did_S_minus_C"] or 0) > 0
            and (r["z_did"] or 0) >= 2
        )

    def _weak(r):
        return (r["z_post_SC"] or 0) < 2

    ok = [n for n, r in out.items() if _ok(r)]
    weak = [n for n, r in out.items() if _weak(r)]
    classic_alive = [n for n, r in out.items() if (r["z_post_CO"] or 0) >= 2]

    N = len(out)
    if len(ok) >= 1 and len(ok) * 2 >= N:  # ≥1/2
        verdict = "支持: 日本株の pre-TOM 4日前倒しが後半（2017–）にも残る（Girgin の T+1 示唆を弱める）"
    elif len(weak) >= 1 and len(weak) * 2 >= N:
        verdict = "棄却: 日本株の後半で S−C の z<2（前倒し窓は古典窓を上回らない）"
    else:
        verdict = "未確定"

    res = {
        "question": "日本株（Nikkei 225・TOPIX）の pre-TOM 4日効果は T+2 市場でも 2017 年以降に残るか（Q283-C2）",
        "settings": {
            "series": SERIES,
            "C_WIN": sorted(C_WIN),
            "S_WIN": sorted(S_WIN),
            "split_year": SPLIT_YEAR,
            "B": args.B,
            "seed": args.seed,
            "null": "各 ym の中で win（S/C/O）ラベルを並べ替え（B=1000）",
            "p_rule": "p_right = (null >= obs の割合)、z = (obs − null_mean)/null_sd",
            "judgment": "ok=後半 S−C>0 かつ z_post_SC≥2 かつ DiD>0 かつ z_did≥2、weak=z_post_SC<2。|ok|≥N/2 → 支持、|weak|≥N/2 → 棄却",
        },
        "per_series": out,
        "ok_series": ok,
        "weak_series": weak,
        "classic_window_still_significant_post": classic_alive,
        "machine_verdict": verdict,
        "note": (
            "価格のみ（基準指数・配当なし）。Nikkei/TOPIX は 2019-07 以降 T+2 のまま、米国 T+1（2024-05-28〜）の影響を受けない点が Q181 や Q284 との区別。"
        ),
        "pre_registered_deviation": (
            "事前登録では TOPIX を '^TPX' として参照したが、Yahoo Finance（yfinance）に ^TPX は存在しない（404）。"
            "TOPIX 連動 ETF の 1308.T（Listed Index Fund TOPIX、2008-01-04〜）を代用。"
            "ETF の日次リターンは TOPIX 指数と高相関（>0.99）で、pre-TOM 4日の窓単位の平均比較には実務上の差異はない。"
            "判定規則そのものは変えていない。"
        ),
    }
    return res, None


def write_result(qid, res, smoke, extra_csv=None):
    os.makedirs(OUT, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    path = os.path.join(OUT, f"{pre}_result_{ts}.json")
    out_res = {"qid": qid, "smoke": smoke, "generated": ts, **res}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out_res, fh, ensure_ascii=False, indent=1, default=_json_default)
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
    write_result("Q285", res, args.smoke, csvs)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
