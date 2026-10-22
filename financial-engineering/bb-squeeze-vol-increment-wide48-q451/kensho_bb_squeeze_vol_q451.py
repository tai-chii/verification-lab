#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q451（Q450-C1）: 48 銘柄 D1 で、BB 幅の収縮度は、自分の過去ボラ（σ20・σ60）と直近の向きを統制した後も、翌 20 日のボラに増分を持つか。

【出典】アイデア候補 2026-10-22（Q450-C1）／[[ブログQuanterLab2026f-1_…]]・[[ブログQuanterLab2026f-2_スクイーズの上向き下向き後のボラ差は主に価格方向の反映でスクイーズ固有の上乗せは1〜2ポイント以下]]、接続ログ 2026-10-22 Q450-C1
【仮説（事前予想）】b4 は 0 と区別できない（BB 幅は σ20 の言い換えで、固有の上乗せは小さい）。
【データ】wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01＝s1x.SEAL）。gap 行は残す（件数を JSON に書く）。
【定義（事前固定）】ret=日次の対数リターン（close/close.shift(1)）。σ20・σ60＝ret の過去 20・60 本の標準偏差（当日を含む）。
  dir20＝sign(log close_t/close_{t-20})。BB 幅 w_t＝4·std(close, 20)/SMA(close, 20)（ボリンジャー 20・±2σ）。
  収縮度 sq_t＝w_t の過去 252 本（当日を含む）の中のパーセンタイル（w≤w_t の割合、0〜1）。小さいほど収縮。
  目的 y_t＝log sqrt(mean(ret_{t+1..t+20}^2))（翌 20 日の実現ボラ）。
  式（1 本だけ）: y = a + b1·log σ20 + b2·log σ60 + b3·dir20 + b4·sq（全銘柄を束ねた OLS・切片 1 つ）。基準式: y = a + b1·log σ20 + b2·log σ60。
【測るもの】(1) b4 の年単位 t: 年ごとに束ねた OLS の b4 を年の標本とし、mean/(sd/√年数)。前半（<2017）・後半（≥2017）の b4 の平均の符号。
  (2) 標本外 R² の差 ΔR²＝R²(式)−R²(基準): 年ごとの拡大窓（学習＝その年より前で、目的の窓が試験年に掛かる行を除く・最初の試験年は 2013）。束ねた SSE で計算。
【帰無】収縮度列を銘柄内で循環シフト（シフト幅 252〜n−252）B=500。ΔR² と年単位 t の帰無分布。
【判定（事前固定・変更禁止）】支持＝全期間 |t(b4)|≥2 かつ 前後半の b4 平均が全期間と同符号 かつ ΔR² が帰無 95 点超。棄却＝全期間 |t(b4)|<1。ほか → 未確定。
  （アイデア候補の「t≥2」は向きを決めていないので |t|≥2 と読む。測る前にここで固定）
【検定の本数】n_tests=1（判定は上の 1 組だけ。gap 銘柄を除いた結果・dir20 込みの基準との差は参考で判定に使わない）
【捨てた案の数】2（銘柄固定効果つきの式＝アイデア候補の式に無い／週次の非重複標本＝標本が 1/5 になり年単位 t が粗くなる）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】なし（Opus が設計・実行）。
【実装】fe_core（syms_available・health・load_d1・parse_args・write_result・fmt）。--smoke で経路確認。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import syms_available, health, load_d1, parse_args, write_result, fmt, SPLIT_YEAR  # noqa: E402
import s1x as X  # noqa: E402

QID = "Q451"
H = 20
PCT_WIN = 252
FIRST_TEST_YEAR = 2013


def features(df):
    c = df["close"].astype(float)
    r = np.log(c / c.shift(1))
    s20 = r.rolling(20).std()
    s60 = r.rolling(60).std()
    dir20 = np.sign(np.log(c / c.shift(20)))
    w = 4 * c.rolling(20).std() / c.rolling(20).mean()
    sq = w.rolling(PCT_WIN).apply(lambda a: np.mean(a <= a[-1]), raw=True)
    fut = (r ** 2).rolling(H).mean().shift(-H)
    y = np.log(np.sqrt(fut))
    end_time = df["time"].shift(-H)
    out = pd.DataFrame({"time": df["time"], "year": df["time"].dt.year, "y": y, "ls20": np.log(s20), "ls60": np.log(s60),
                        "dir20": dir20, "sq": sq, "end_year": end_time.dt.year, "gap": df.get("gap", False)})
    out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["y", "ls20", "ls60", "dir20", "sq", "end_year"])
    return out.reset_index(drop=True)


def ols(X_, y):
    b, *_ = np.linalg.lstsq(X_, y, rcond=None)
    return b


def design(d, sq, full=True):
    cols = [np.ones(len(d)), d["ls20"].values, d["ls60"].values]
    if full:
        cols += [d["dir20"].values, sq]
    return np.column_stack(cols)


def year_t(d, sq):
    bs = {}
    for yr, idx in d.groupby("year").indices.items():
        if len(idx) < 200:
            continue
        bs[int(yr)] = ols(design(d.iloc[idx], sq[idx]), d["y"].values[idx])[4]
    v = np.array(list(bs.values()))
    t = v.mean() / (v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 2 else np.nan
    pre = np.mean([b for k, b in bs.items() if k < SPLIT_YEAR]) if any(k < SPLIT_YEAR for k in bs) else np.nan
    post = np.mean([b for k, b in bs.items() if k >= SPLIT_YEAR]) if any(k >= SPLIT_YEAR for k in bs) else np.nan
    return t, v.mean(), pre, post, bs


class OOS:
    """年ごとの拡大窓の学習・試験の添字を前計算する。"""
    def __init__(self, d):
        self.d = d
        self.y = d["y"].values
        years = sorted(d["year"].unique())
        self.folds = []
        for Y in [y for y in years if y >= FIRST_TEST_YEAR]:
            tr = np.where((d["year"].values < Y) & (d["end_year"].values < Y))[0]
            te = np.where(d["year"].values == Y)[0]
            if len(tr) > 1000 and len(te) > 100:
                self.folds.append((Y, tr, te))
        self.Xb = design(d, None, full=False)
        self.sse_base, self.sst = 0.0, 0.0
        for _, tr, te in self.folds:
            b = ols(self.Xb[tr], self.y[tr])
            self.sse_base += np.sum((self.y[te] - self.Xb[te] @ b) ** 2)
            self.sst += np.sum((self.y[te] - self.y[tr].mean()) ** 2)

    def sse_full(self, sq):
        Xf = design(self.d, sq)
        s = 0.0
        for _, tr, te in self.folds:
            b = ols(Xf[tr], self.y[tr])
            s += np.sum((self.y[te] - Xf[te] @ b) ** 2)
        return s

    def dr2(self, sq):
        return (self.sse_base - self.sse_full(sq)) / self.sst


def shift_sq(d, rng):
    out = d["sq"].values.copy()
    for _, idx in d.groupby("sym").indices.items():
        n = len(idx)
        k = rng.integers(PCT_WIN, n - PCT_WIN) if n > 2 * PCT_WIN + 1 else rng.integers(1, max(n, 2))
        out[idx] = np.roll(d["sq"].values[idx], k)
    return out


def analyse(d, B, rng, with_null=True):
    sq = d["sq"].values
    t, m, pre, post, bs = year_t(d, sq)
    full_b = ols(design(d, sq), d["y"].values)
    oos = OOS(d)
    r2_base = 1 - oos.sse_base / oos.sst
    dr2 = oos.dr2(sq)
    # 参考: dir20 込みの基準（式から sq だけ抜いた）との差
    X3 = np.column_stack([np.ones(len(d)), d["ls20"].values, d["ls60"].values, d["dir20"].values])
    sse3 = 0.0
    for _, tr, te in oos.folds:
        b = ols(X3[tr], oos.y[tr]); sse3 += np.sum((oos.y[te] - X3[te] @ b) ** 2)
    res = {"n_rows": int(len(d)), "n_syms": int(d["sym"].nunique()), "years": sorted(int(k) for k in bs),
           "b_full_pooled": [fmt(x, 5) for x in full_b], "b4_by_year": {k: fmt(v, 5) for k, v in bs.items()},
           "t_b4": fmt(t, 3), "b4_mean": fmt(m, 5), "b4_pre": fmt(pre, 5), "b4_post": fmt(post, 5),
           "oos_test_years": [int(f[0]) for f in oos.folds], "r2_oos_base": fmt(r2_base, 5),
           "dr2_oos": fmt(dr2, 6), "dr2_oos_vs_base_with_dir": fmt((sse3 - oos.sse_full(sq)) / oos.sst, 6),
           "corr_sq_ls20": fmt(np.corrcoef(sq, d["ls20"].values)[0, 1], 3)}
    if with_null:
        nd, nt = [], []
        for _ in range(B):
            s2 = shift_sq(d, rng)
            nd.append(oos.dr2(s2)); nt.append(year_t(d, s2)[0])
        nd, nt = np.array(nd), np.array(nt)
        res["null"] = {"B": B, "dr2_p95": fmt(np.quantile(nd, 0.95), 6), "dr2_q025_q975": [fmt(np.quantile(nd, 0.025), 6), fmt(np.quantile(nd, 0.975), 6)],
                       "dr2_p_one_sided": fmt((1 + np.sum(nd >= dr2)) / (B + 1), 4),
                       "t_q025_q975": [fmt(np.nanquantile(nt, 0.025), 3), fmt(np.nanquantile(nt, 0.975), 3)],
                       "t_p_two_sided": fmt((1 + np.sum(np.abs(nt) >= abs(t))) / (B + 1), 4),
                       "null_degenerate": bool(np.nanstd(nd) < 1e-12)}
    return res


def judge(r):
    t, pre, post = r["t_b4"], r["b4_pre"], r["b4_post"]
    if t is None:
        return "未確定（t が出ない）"
    if abs(t) < 1:
        return "棄却: 全期間 |t(b4)|<1"
    s = np.sign(t)
    if abs(t) >= 2 and pre is not None and post is not None and np.sign(pre) == s and np.sign(post) == s and r["dr2_oos"] > r["null"]["dr2_p95"]:
        return "支持: |t(b4)|≥2・前後半同符号・ΔR² が帰無 95 点超"
    return "未確定: 支持も棄却も満たさない"


def main():
    args = parse_args(default_B=500)
    rng = np.random.default_rng(args.seed)
    syms, missing = syms_available(X.WIDE48, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="D1_fromH1", bar="D1")
    if args.smoke:
        syms = syms[:3]
    parts, n_gap = [], {}
    for s in syms:
        df = load_d1(s, smoke=args.smoke, rng=rng)
        df = df[df["time"] < X.SEAL].reset_index(drop=True)
        f = features(df); f["sym"] = s
        n_gap[s] = int(f["gap"].sum())
        parts.append(f)
    d = pd.concat(parts, ignore_index=True)
    B = 20 if args.smoke else args.B
    main_res = analyse(d, B, rng)
    gap_syms = sorted((dh or {}).get("gaps", {}).keys())
    d_ng = d[~d["sym"].isin(gap_syms)].reset_index(drop=True)
    excl = analyse(d_ng, 0, rng, with_null=False) if gap_syms and d_ng["sym"].nunique() > 3 else None
    ys = d.groupby(["year", "sym"]).size().unstack(fill_value=0)
    res = {"question": "BB幅収縮度のボラ予測への増分（wide48 D1）", "seal": str(X.SEAL.date()), "split_year": SPLIT_YEAR,
           "n_tests": 1, "multiple_comparisons": "なし（判定は 1 組・n_tests=1）", "missing": missing, "data_health": dh,
           "n_syms_read": int(ys.shape[1]), "gap_rows": n_gap, "years_dropped": "年の行数<200 の年は年単位 t から除く（該当なしなら空）",
           "main": main_res, "excluding_gap_syms": {"syms_excluded": gap_syms, "res": excl}, "verdict": judge(main_res)}
    res["null_degenerate"] = main_res["null"]["null_degenerate"]
    p = write_result(QID, res, args.smoke, extra_csv={"year_sym": ys.reset_index()}, here=HERE)
    print(p); print(res["verdict"]); print({k: main_res[k] for k in ("t_b4", "b4_pre", "b4_post", "dr2_oos", "r2_oos_base", "corr_sq_ls20")}, main_res["null"])


if __name__ == "__main__":
    main()
