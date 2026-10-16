#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q307: 同じ特徴量の分類器で、ラベルを同日にすると上げ下げの精度は跳ね、翌日では基準率に落ちるか（HSAT の精度 0.69 はリークで再現できるか・Q306-C1）
================================================================================
事前登録の正本は下の SPEC（fe_core の Spec を事前登録の入れ物として使う「土台を直接使う型」）。測る前に固定（2026-10-17・Opus）。
実行: python3 kensho_same_day_label_leak_q307.py（B=500）／ --smoke --B 5 ／ --readme ／ --idea-row
"""
import datetime as _dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (Spec, SYMS, parse_args, write_result, syms_available, health, load_h1, h1_to_d1,  # noqa: E402
                     rsi, z_of, perm_p, fmt)
from fe_core.readme import render_readme, render_idea_row  # noqa: E402

WIN = 5
FEATS = ["close", "volume", "close_diff", "rsi14", "sma20", "macd", "mom10"]
SPLIT = (0.6, 0.8)   # 学習 0〜60%・選択 60〜80%・テスト 80〜100%（時系列順・銘柄ごと）
RIDGE = 1e-2

SPEC = Spec(
    qid="Q307",
    question="同じ特徴量の分類器で、ラベルを同日にすると上げ下げの精度は跳ね、翌日では基準率に落ちるか（HSAT の精度 0.69 はリークで再現できるか・Q306-C1）",
    hypothesis="HSAT と同じ 7 特徴量（終値・出来高・終値差・RSI14・SMA20・MACD・モメンタム10）の直近 5 日の窓（35 次元）を入力にしたロジスティック回帰で、"
               "ラベルを同日（r_t>0。窓の最後の日の値動き）にするとテストの精度は 15 銘柄平均で基準率 max(p_up,1−p_up) を 10 ポイント以上上回り、"
               "翌日（r_t+1>0）にすると基準率と区別できない",
    reject_if="支持（論文の精度はリークで再現できる）: 同日ラベルの精度が 15 銘柄平均で基準率 +0.10 以上 かつ 翌日ラベルの『精度−基準率』の 15 銘柄平均が、テストのラベルを年内で並べ替えた帰無に対し z<2。"
              "棄却: 同日ラベルでも基準率 +0.03 未満。ほか → 未確定。判定に使うのは正規化『全期間 min-max』（論文の書き方に近い方）。学習期間のみの正規化は記述",
    syms=list(SYMS), kind="H1→D1", params=[{"label": "same_day"}, {"label": "next_day"}], n_tests=1, B=500,
    null_kind="none",
    discarded="約3: 木モデル（Mac に sklearn が無く入れられないため・ロジスティック回帰に変更。測る前の決定）、Transformer の再実装（論文のコード非公開・再現の幅が大きい）、窓幅 3/7/10 の掃引（論文の主結果の窓幅 5 に固定）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2008〜2026-06 で締め切り前。規則は固定で相場観は使わない",
    delegation="設計・コード・実行・解釈は Opus 本体（2026-10-17）。委託なし。数値は JSON から直接読む",
    source="[[Mustafa2026-1_技術指標を足したTransformerは25銘柄の上げ下げ分類で平均F1が0.70と比較モデルの0.34から0.49を上回った]]、"
           "[[Mustafa2026-3_比較モデルの高いF1の多くは下げを一度も当てない偏りで論文の成功は正解が誤りより多いことと定義されている]]、知見 Q147（単純規則は基準率を超えない）、接続ログ Q306-C1",
    data="15 銘柄 H1_dukascopy → h1_to_d1（UTC 0 時区切り。出来高＝ティック数の和）。銘柄ごとに時系列順で 60/20/20",
    measure="テストの精度・F1（上げを正例）・基準率・TN=0 の有無を、ラベル 2 通り × 正規化 2 通りで。選択期間の精度も記述",
    null_desc="翌日ラベル: 銘柄ごとにテストのラベルを暦年内で並べ替え（予測は固定）B 回 → 『精度−基準率』の 15 銘柄平均の帰無 → z",
    prior_art="WebSearch 2026-10-17・standard・\"stock price direction prediction look-ahead bias same-day label leakage technical indicators deep learning inflated accuracy\"。"
              "Information leakage in financial machine learning research（Algorithmic Finance 2019）、arXiv 2608.26106（SPY の当日方向予測）。HSAT の特徴量でリークの大きさを測った例は未確認（追試＋診断）",
    batch="単発（接続 Q306 の通過案）", designer="Opus", coder="Claude（Opus）",
    settings={"win": WIN, "feats": FEATS, "split": SPLIT, "ridge": RIDGE, "model": "L2 ロジスティック回帰（Newton 法）"},
)


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def features(d):
    c = d["close"].values.astype(float)
    f = pd.DataFrame({"close": c, "volume": d["volume"].values.astype(float),
                      "close_diff": np.r_[np.nan, np.diff(c)], "rsi14": rsi(c, 14),
                      "sma20": pd.Series(c).rolling(20).mean().values,
                      "macd": ema(c, 12) - ema(c, 26), "mom10": c - pd.Series(c).shift(10).values})
    return f


def windowed(f):
    cols = []
    for k in range(WIN - 1, -1, -1):  # t−4 … t
        cols.append(f.shift(k).add_suffix(f"_l{k}"))
    return pd.concat(cols, axis=1)


def minmax(X, ref):
    lo, hi = np.nanmin(ref, axis=0), np.nanmax(ref, axis=0)
    span = np.where(hi - lo > 0, hi - lo, 1.0)
    return (X - lo) / span


def fit_logit(X, y, lam=RIDGE, it=50):
    Xb = np.c_[np.ones(len(X)), X]; w = np.zeros(Xb.shape[1])
    R = lam * np.eye(Xb.shape[1]); R[0, 0] = 0
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(Xb @ w, -30, 30)))
        g = Xb.T @ (p - y) + R @ w
        H = (Xb * (p * (1 - p))[:, None]).T @ Xb + R + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(H, g); w -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def predict(w, X):
    return (np.c_[np.ones(len(X)), X] @ w > 0).astype(int)


def scores(y, yhat):
    tp = int(((yhat == 1) & (y == 1)).sum()); tn = int(((yhat == 0) & (y == 0)).sum())
    fp = int(((yhat == 1) & (y == 0)).sum()); fn = int(((yhat == 0) & (y == 1)).sum())
    acc = (tp + tn) / max(len(y), 1); pu = y.mean() if len(y) else np.nan
    prec = tp / (tp + fp) if tp + fp else 0.0; rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"acc": acc, "base": max(pu, 1 - pu), "f1": f1, "tp": tp, "tn": tn, "fp": fp, "fn": fn, "n": len(y)}


def run_sym(d):
    f = features(d); W = windowed(f)
    c = d["close"].values.astype(float)
    r = np.r_[np.nan, c[1:] / c[:-1] - 1]
    labels = {"same_day": r, "next_day": np.r_[r[1:], np.nan]}
    years = pd.to_datetime(d["time"]).dt.year.values
    out = {}
    for lab, rr in labels.items():
        ok = W.notna().all(axis=1).values & np.isfinite(rr) & (rr != 0)
        X = W.values[ok]; y = (rr[ok] > 0).astype(int); yr = years[ok]; n = len(y)
        i1, i2 = int(n * SPLIT[0]), int(n * SPLIT[1])
        for norm in ("global", "train_only"):
            ref = X if norm == "global" else X[:i1]
            Xn = minmax(X, ref)
            w = fit_logit(Xn[:i1], y[:i1])
            yh = predict(w, Xn)
            out[(lab, norm)] = {"sel": scores(y[i1:i2], yh[i1:i2]), "test": scores(y[i2:], yh[i2:]),
                                "_y_test": y[i2:], "_yh_test": yh[i2:], "_yr_test": yr[i2:]}
    return out


def run(args, rng):
    syms, missing = syms_available(SPEC.syms, kind="H1_dukascopy", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="H1_dukascopy")
    per = {}
    for s in syms:
        d = h1_to_d1(load_h1(s, args.smoke, rng), 0).reset_index(drop=True)
        if "gap" in d:
            d = d[~d["gap"].astype(bool)].reset_index(drop=True)
        per[s] = run_sym(d)
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "cells": {}, "per_sym": {}}
    for key in [("same_day", "global"), ("same_day", "train_only"), ("next_day", "global"), ("next_day", "train_only")]:
        tests = [per[s][key]["test"] for s in syms]; sels = [per[s][key]["sel"] for s in syms]
        edge = np.array([t["acc"] - t["base"] for t in tests])
        res["cells"]["|".join(key)] = {"acc_mean": fmt(np.mean([t["acc"] for t in tests])), "base_mean": fmt(np.mean([t["base"] for t in tests])),
                                       "edge_mean": fmt(edge.mean()), "f1_mean": fmt(np.mean([t["f1"] for t in tests])),
                                       "n_syms_tn0": int(sum(t["tn"] == 0 for t in tests)), "n_syms_tp0": int(sum(t["tp"] == 0 for t in tests)),
                                       "sel_acc_mean": fmt(np.mean([t["acc"] for t in sels])), "n_syms_edge_pos": int((edge > 0).sum())}
        for s in syms:
            res["per_sym"].setdefault(s, {})["|".join(key)] = {k: (fmt(v) if isinstance(v, float) else v) for k, v in per[s][key]["test"].items()}
    # 帰無（翌日ラベル・全期間 min-max）: テストのラベルを暦年内で並べ替え
    key = ("next_day", "global")
    obs = float(np.mean([per[s][key]["test"]["acc"] - per[s][key]["test"]["base"] for s in syms]))
    null = []
    for _ in range(args.B):
        e = []
        for s in syms:
            y, yh, yr = per[s][key]["_y_test"], per[s][key]["_yh_test"], per[s][key]["_yr_test"]
            yp = y.copy()
            for g in np.unique(yr):
                m = np.where(yr == g)[0]; yp[m] = rng.permutation(y[m])
            sc = scores(yp, yh); e.append(sc["acc"] - sc["base"])
        null.append(float(np.mean(e)))
    z, pct = z_of(obs, np.array(null)) if null else (None, None)
    res["null_next_day_global"] = {"obs_edge": fmt(obs), "z": fmt(z), "pct": fmt(pct), "p_perm": fmt(perm_p(obs, np.array(null))) if null else None,
                                   "null_q025": fmt(float(np.quantile(null, .025))) if null else None,
                                   "null_q975": fmt(float(np.quantile(null, .975))) if null else None, "B": len(null)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    res["multiple_comparisons"] = "判定は 同日（全期間 min-max）の精度と 翌日（全期間 min-max）の z の 2 つの交差。学習期間のみの正規化・F1・選択期間は記述"
    return res


def judge(res):
    sd = res["cells"]["same_day|global"]; z = res["null_next_day_global"]["z"]
    if sd["edge_mean"] is None or z is None:
        return "未確定: 計算できない"
    if sd["edge_mean"] >= 0.10 and z < 2:
        return f"支持: 同日ラベルの精度が基準率 +{sd['edge_mean']:.3f}、翌日ラベルは帰無に z={z:.2f}<2（論文の精度はリークで再現できる）"
    if sd["edge_mean"] < 0.03:
        return "棄却: 同日ラベルでも基準率 +0.03 未満"
    return "未確定"


def main():
    av = sys.argv[1:]; script = os.path.basename(__file__)
    if "--readme" in av:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型"))
        print("wrote README.md"); return
    if "--idea-row" in av:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE)).replace("fe_core Runner 型", "fe_core 土台を直接使う型")); return
    args = parse_args(default_B=SPEC.B)
    rng = np.random.default_rng(args.seed)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{SPEC.qid}" if args.smoke else SPEC.qid
    with open(os.path.join(out, f"{pre}_spec_{ts}.json"), "w", encoding="utf-8") as fh:
        json.dump({"qid": SPEC.qid, "registered": ts, "B": args.B, "seed": args.seed, **SPEC.as_dict()}, fh, ensure_ascii=False, indent=1)
    res = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    write_result(SPEC.qid, res, args.smoke, here=HERE)
    print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
