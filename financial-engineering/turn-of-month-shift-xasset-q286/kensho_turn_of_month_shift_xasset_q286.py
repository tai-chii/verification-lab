#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q286: 商品・BTC・FX の pre-TOM 4日効果は残るか（15銘柄パネルの非米国株13本・Q283-C3）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-13「商品・BTC・FX の pre-TOM 4日効果は残るか（15銘柄パネルの非米国株13 本）」(Q283-C3)。
- 接続ログ 2026-10-13・条件の穴（Q283-C3・クロス資産）:
  Girgin 2026 の pre-TOM 4日前倒しを、15銘柄パネルから Q181 で棄却済みの US500・USTECH を除いた13本（FX8+XAUUSD/XAGUSD/WTI/UKOIL/BTCUSD）に移植。
  株の月末配当再投資ではないフロー（商品の月末ロールオーバー・BTC の月末決済集中・FX の月末リバランス）で前倒し山が残るか見れば、Girgin の pre-TOM が株固有か全市場共通のカレンダー効果かを分離できる。
  先行研究チェック済（2026-10-13、関連: Carchano・Pardo 2011 Nikkei/S&P/DAX 先物の古典 TOM・diva-portal.org 15 市場株式 TOM・暗号 TOM サーベイ。
  金/銀/原油/BTC/FX の pre-TOM 4日前倒し窓 S−C はカバーされない）。
- 関連の自検証: Q181（SPX/US500/USTECH、S/C/O・DiD → 棄却）、Q284（FX8 で offset −6..+3 の帰無上位 5% が前後半で一致せず → 棄却）、
  Q285（Nikkei/TOPIX で S−C 後半 z<2・DiD z<2 → 棄却）。本件は Q181 の方法（S/C/O 窓・DiD）を13本に当て Holm 補正で判定する。

【仮説（測る前に固定）】
H1（Girgin 2026 のブログ主張の全市場共通性）:
  13本のうち、後半（2017–）で mean(S)−mean(C) > 0 が Holm 補正（α=0.05/13）後に有意、かつ前半（≤2016）で mean(S)−mean(C) の符号が同じ（>0）の銘柄が ≥3本
  → pre-TOM 4日前倒しは全市場共通（Girgin の T+1 示唆は株固有ではない）。
H0: 上の条件を満たす銘柄が ≤1本 → 棄却（Girgin の主張は株固有の現象で、商品・BTC・FX には及ばない）。
2本: 未確定。

【データ】15銘柄パネルから US500・USTECH を除いた13本の D1_fromH1、2008–2026-06。
Dukascopy 由来（手元の `検証/学問/金融工学/作業/FX/システムトレード/data_<SYM>_D1_fromH1.csv`）。価格のみ・コスト0 の粗利段階1。
- FX8: EURUSD・GBPUSD・AUDUSD・USDJPY・USDCHF・USDCAD・EURJPY（2026-03 まで）・GBPJPY
- 商品4: XAUUSD（2008-05〜）・XAGUSD（2008-01〜）・WTI（2011-09〜）・UKOIL（2010-12〜）
- 暗号1: BTCUSD（2017-05〜）

【定義（Q181・Q285 と揃える）】
- 月末からの営業日位置 k: 月の最初 3 営業日 = +1,+2,+3、月の最終営業日 = −1、その前 = −2,−3,...。
- 古典窓 C = {−1,+1,+2,+3}。前倒し窓 S = {−4,−3,−2}。その他 O = それ以外。
- 日次リターン [bp]（終値→終値）。各銘柄・各期間の mean(S), mean(C), mean(O)。差 S−C, C−O。差の差 DiD = (S−C)_post − (S−C)_pre。
- 期間: 前半 year < 2017、後半 year ≥ 2017。
- 帰無: 各月（ym）の中で窓ラベル win（S/C/O）を並べ替え（B=1000）。各並べ替えで前後半の S−C・C−O を再計算し、観測との z・片側 p_right = (null ≥ obs の割合) を出す。

【判定（事前固定・変更禁止）】
- 各銘柄 i について post 期間の p_right(S−C) を集めて Holm 補正（α=0.05・多重数 m=13）を当てる。
  Holm: p_(1) ≤ p_(2) ≤ ... ≤ p_(13) に対し、i 番目に小さい p_(i) を α/(m−i+1) と比べる。p_(i) < α/(m−i+1) なら棄却（有意）し続け、超えたらそこで止める。
- 「後半 Holm 有意（S−C>0 かつ Holm 補正通過）」かつ「前半も S−C>0 の銘柄」を数える。これを「前後半で同符号の Holm 有意本数」=K とする。
  BTCUSD は前半（year<2017）に営業日が1件も無いので、仕様上「前半で S−C>0」の判定自体が不能。
  判定を変えずに扱うため、BTCUSD は K の母集団から除く（取り扱いの事前固定・結果欄に明記）。
- 支持: K ≥ 3
- 棄却: K ≤ 1
- 未確定: K = 2
補助情報として、Holm 補正前の p_right<0.05 本数、古典窓 (C−O)_post が後半で有意な銘柄も記録（判定を変えない）。

【捨てた案の数】約4:
(i) 月末の位置を暦日で取る案 → 営業日（Q181・Q285 と揃える）、
(ii) 多重補正を Bonferroni → Holm（Holm のほうが同じ厳密性で検定力が高い）、
(iii) 配当調整 → FX・商品・BTC は配当なしなので無関係・米国株は本検証では除外、
(iv) BTC を除いて12本にする案 → 13本のまま、BTC は K から除外する扱いを事前固定（原仕様の文言「13本」を守る）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06（EURJPY は 2026-03）。締め切り後の独立標本は無い。
Girgin 2026 のブログは 2026-09 時点のスライド窓だが、SPY ETF の標本と本検証のクロス資産13本は独立標本に当たる。

【委託の確かめ方】設計・コード・実行・解釈は Opus 本体。委託なし。

【実装】自己完結。実行: python3 kensho_turn_of_month_shift_xasset_q286.py（B=1000、約 1〜2 分）。
--B 100 で短縮・--smoke で経路確認（判定不可）。
"""

import argparse
import datetime as _dt
import json
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

SYMBOLS = [
    "EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY",
    "XAUUSD", "XAGUSD", "WTI", "UKOIL", "BTCUSD",
]
C_WIN = {-1, 1, 2, 3}
S_WIN = {-4, -3, -2}
SPLIT_YEAR = 2017
SEED = 20261013
ALPHA = 0.05
M_TESTS = len(SYMBOLS)  # 13


def _read(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def load_d1(sym):
    df = _read(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    return df


def _smoke_ohlc(sym, rng, n=4800, start="2008-01-01"):
    t = pd.bdate_range(start, periods=n)
    r = rng.normal(0.0, 0.006, n)
    c = 1.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.001, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.001, n)))
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


def holm_adjusted(p_values, alpha=0.05):
    """Holm step-down. 入力: dict {sym: p}. 出力: dict {sym: {"rank":, "threshold":, "reject":}}."""
    items = [(sym, p) for sym, p in p_values.items() if p is not None and np.isfinite(p)]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    result = {}
    reject_so_far = True
    for i, (sym, p) in enumerate(items, start=1):
        threshold = alpha / (m - i + 1)
        if reject_so_far and p < threshold:
            reject = True
        else:
            reject = False
            reject_so_far = False
        result[sym] = {"rank": i, "p": float(p), "threshold": float(threshold), "reject": reject}
    for sym, p in p_values.items():
        if sym not in result:
            result[sym] = {"rank": None, "p": None, "threshold": None, "reject": False}
    return result


def run(args, rng):
    per_sym = {}
    missing = []
    for sym in SYMBOLS:
        path = os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv")
        if args.smoke:
            df = _smoke_ohlc(sym, rng)
        elif not os.path.exists(path):
            missing.append(sym)
            continue
        else:
            df = load_d1(sym)
        d = _positions(df)
        pre = d[d["year"] < SPLIT_YEAR]
        post = d[d["year"] >= SPLIT_YEAR]
        o_pre = _diffs(pre)
        o_post = _diffs(post)
        did = o_post["S_minus_C"] - o_pre["S_minus_C"]

        null_pre_SC, null_post_SC, null_post_CO, null_did = [], [], [], []
        for b in range(args.B):
            dd = d.copy()
            dd["winp"] = perm_within_labels(rng, dd["win"].values, dd["ym"].values)
            np_ = _diffs(dd[dd["year"] < SPLIT_YEAR], "winp")
            pp_ = _diffs(dd[dd["year"] >= SPLIT_YEAR], "winp")
            null_pre_SC.append(np_["S_minus_C"])
            null_post_SC.append(pp_["S_minus_C"])
            null_post_CO.append(pp_["C_minus_O"])
            null_did.append(pp_["S_minus_C"] - np_["S_minus_C"])

        z_pre_SC, p_pre_SC = z_of(o_pre["S_minus_C"], null_pre_SC)
        z_post_SC, p_post_SC = z_of(o_post["S_minus_C"], null_post_SC)
        z_post_CO, p_post_CO = z_of(o_post["C_minus_O"], null_post_CO)
        z_did, p_did = z_of(did, null_did)

        per_sym[sym] = {
            "n_pre": int(len(pre)),
            "n_post": int(len(post)),
            "span": [str(d["time"].min().date()), str(d["time"].max().date())],
            "pre": {k: f(v) for k, v in o_pre.items()},
            "post": {k: f(v) for k, v in o_post.items()},
            "did_S_minus_C": f(did),
            "z_pre_SC": f(z_pre_SC),
            "z_post_SC": f(z_post_SC),
            "z_post_CO": f(z_post_CO),
            "z_did": f(z_did),
            "p_right_post_SC": f(p_post_SC),
            "p_right_pre_SC": f(p_pre_SC),
            "p_right_post_CO": f(p_post_CO),
            "p_right_did": f(p_did),
        }
        pre_SC = per_sym[sym]["pre"]["S_minus_C"]
        print(
            f"{sym}: n_pre={len(pre)}, n_post={len(post)}, "
            f"post S-C={per_sym[sym]['post']['S_minus_C']} bp (z={per_sym[sym]['z_post_SC']}), "
            f"pre S-C={pre_SC}, "
            f"DiD={per_sym[sym]['did_S_minus_C']} (z={per_sym[sym]['z_did']})"
        )

    # Holm 補正（post S−C の p_right に対して m=13）
    p_post_SC = {sym: per_sym[sym]["p_right_post_SC"] for sym in per_sym}
    holm = holm_adjusted(p_post_SC, alpha=ALPHA)

    # 判定: 「後半 Holm 有意」かつ「前半も S−C>0」の銘柄数 K。BTCUSD は前半不能なので K から除外。
    K_syms = []
    excluded_from_K = []
    for sym in per_sym:
        rej = holm[sym]["reject"]
        pre_SC = per_sym[sym]["pre"]["S_minus_C"]
        post_SC = per_sym[sym]["post"]["S_minus_C"]
        n_pre = per_sym[sym]["n_pre"]
        if n_pre == 0:
            excluded_from_K.append(sym)
            continue
        if rej and (post_SC is not None and post_SC > 0) and (pre_SC is not None and pre_SC > 0):
            K_syms.append(sym)
    K = len(K_syms)

    if K >= 3:
        verdict = f"支持: K={K}（≥3）→ pre-TOM 4日前倒しは全市場共通（商品・BTC・FX にも及ぶ）"
    elif K <= 1:
        verdict = f"棄却: K={K}（≤1）→ Girgin の pre-TOM は株固有の現象で、商品・BTC・FX には及ばない"
    else:
        verdict = f"未確定: K={K}（=2）"

    # 補助: 補正前 p_right<0.05 本数、古典窓有意銘柄
    pre_holm_sig = [sym for sym in per_sym if (per_sym[sym]["p_right_post_SC"] is not None and per_sym[sym]["p_right_post_SC"] < 0.05)]
    classic_sig = [sym for sym in per_sym if (per_sym[sym]["z_post_CO"] is not None and per_sym[sym]["z_post_CO"] >= 2)]
    pre_holm_sig_with_sign = [
        sym for sym in pre_holm_sig
        if per_sym[sym]["n_pre"] > 0
        and per_sym[sym]["pre"]["S_minus_C"] is not None and per_sym[sym]["pre"]["S_minus_C"] > 0
    ]

    res = {
        "question": "商品・BTC・FX の pre-TOM 4日効果は残るか（15銘柄パネルの非米国株13本・Q283-C3）",
        "settings": {
            "symbols": SYMBOLS,
            "n_tests_m": M_TESTS,
            "C_WIN": sorted(C_WIN),
            "S_WIN": sorted(S_WIN),
            "split_year": SPLIT_YEAR,
            "B": args.B,
            "seed": args.seed,
            "alpha": ALPHA,
            "null": "各 ym の中で win（S/C/O）ラベルを並べ替え（B=1000）",
            "p_rule": "p_right = (null >= obs の割合)、z = (obs − null_mean)/null_sd",
            "multiple_correction": "Holm step-down（m=13、α=0.05）",
            "judgment": "K = post Holm 有意 かつ pre S−C>0 の銘柄数（BTCUSD は前半不能なので除外）。K≥3 支持、K≤1 棄却、K=2 未確定",
        },
        "missing": missing,
        "excluded_from_K": excluded_from_K,
        "per_symbol": per_sym,
        "holm": holm,
        "K_symbols": K_syms,
        "K": K,
        "pre_holm_significant": pre_holm_sig,
        "pre_holm_significant_with_pre_positive": pre_holm_sig_with_sign,
        "classic_window_still_significant_post": classic_sig,
        "machine_verdict": verdict,
        "pre_registered_deviation": (
            "BTCUSD は 2017-05 開始で前半（year<2017）に営業日が1件も無く、「前半 S−C>0」の判定が仕様上不能。"
            "判定規則を変えずに扱うため、BTCUSD を K の母集団から除外することを事前固定し、結果にその旨を明記。"
            "WTI（2011-09〜）・UKOIL（2010-12〜）は前半が5〜6年分あり、通常どおり判定に含める。"
        ),
        "data_range_note": (
            "EURJPY は 2026-03-31 まで、他は 2026-06-30 まで。BTCUSD は 2017-05-07〜。per_symbol の span/n_pre/n_post を参照。"
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
    write_result("Q286", res, args.smoke, csvs)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
