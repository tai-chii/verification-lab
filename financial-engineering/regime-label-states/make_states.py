#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_states.py — 局面判定ラベル（状態の印・世界共通の 1 表）を作る。定義は 事前登録_状態ラベル.md §1 のまま（2026-11-13 19:57 固定）。

元データ: S21 の 19 銘柄の Dukascopy の日足だけ（読み込みは ../regime-label-main-driver/make_label.py の load_close。封印を開ける理由も同じ）。
  荒さ   高／低: 銘柄ごとに 20 日の標準偏差 ÷ その銘柄の直近 750 日の中央値。19 銘柄の対数の平均 > 0 なら「高」
  株の向き 上／下: US500 の終値 > 200 日移動平均なら「上」
  方向感 強／弱: 銘柄ごとに 60 日の |リターンの合計| ÷ リターンの絶対値の合計。19 銘柄の平均 > その平均の直近 750 日の中央値なら「強」
どの軸も、生の状態が N=5 営業日続けて反対になったら、その 5 日目に切り替える。すべてその日までのデータだけ。
結合するときは、日 d の取引に d の前の営業日の状態を当てる。

使い方:  <venv_forward の python> make_states.py   （--smoke は合成データで経路だけ。results/_smoke/）
"""
import argparse, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "regime-label-main-driver"))
import make_label as ML

AXES = {"荒さ": ("高", "低"), "株の向き": ("上", "下"), "方向感": ("強", "弱")}   # 先に書いた方が「見込みで成績が良い側」
P = {"VOL_W": 20, "VOL_MIN": 15, "ER_W": 60, "ER_MIN": 45, "BASE_W": 750, "BASE_MIN": 500, "MA_W": 200, "MA_MIN": 150, "MINT": 15}
N_DEFAULT = {"荒さ": 5, "株の向き": 5, "方向感": 5}


def load(smoke=False):
    """返り値: (cal, R[19 銘柄の対数リターン], us500 の終値（暦に合わせた Series）)"""
    cal, R, X, report = ML.load_all(smoke)
    R = R[ML.TARGETS]
    if smoke:
        us = pd.Series(100 * np.exp(np.nancumsum(R["US500"].values)), index=cal)
    else:
        us = ML.load_close("US500", {}).reindex(cal)
    return cal, R, us, report


def raw_states(cal, R, us):
    out = pd.DataFrame(index=cal)
    # 荒さ
    s20 = R.rolling(P["VOL_W"], min_periods=P["VOL_MIN"]).std()
    base = s20.rolling(P["BASE_W"], min_periods=P["BASE_MIN"]).median()
    lr = np.log(s20 / base); V = lr.mean(axis=1, skipna=True); V[lr.notna().sum(axis=1) < P["MINT"]] = np.nan
    out["荒さ_値"] = V; out["荒さ_生"] = np.where(V.isna(), None, np.where(V > 0, "高", "低"))
    # 株の向き
    ma = us.rolling(P["MA_W"], min_periods=P["MA_MIN"]).mean(); ratio = us / ma
    out["株の向き_値"] = ratio; out["株の向き_生"] = np.where(ratio.isna(), None, np.where(ratio > 1, "上", "下"))
    # 方向感（Kaufman の効率比）
    num = R.rolling(P["ER_W"], min_periods=P["ER_MIN"]).sum().abs(); den = R.abs().rolling(P["ER_W"], min_periods=P["ER_MIN"]).sum()
    er = num / den; E = er.mean(axis=1, skipna=True); E[er.notna().sum(axis=1) < P["MINT"]] = np.nan
    med = E.rolling(P["BASE_W"], min_periods=P["BASE_MIN"]).median()
    out["方向感_値"] = E; out["方向感_基準"] = med
    out["方向感_生"] = np.where(E.isna() | med.isna(), None, np.where(E > med, "強", "弱"))
    return out


def build(cal, R, us, N=None):
    N = dict(N_DEFAULT, **(N or {})); out = raw_states(cal, R, us)
    for ax in AXES:
        L, sw = ML.confirm(out[f"{ax}_生"].tolist(), N[ax])
        out[ax] = L; out[f"{ax}_切り替わり"] = sw
    ok = out[list(AXES)].notna().all(axis=1)
    out["組み合わせ"] = np.where(ok, out["荒さ"].astype(str) + "・" + out["株の向き"].astype(str) + "・" + out["方向感"].astype(str), None)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
    cal, R, us, report = load(a.smoke); lab = build(cal, R, us)
    od = os.path.join(HERE, "results", "_smoke") if a.smoke else os.path.join(HERE, "results"); os.makedirs(od, exist_ok=True)
    keep = lab[lab["組み合わせ"].notna()].copy(); keep.index.name = "date"
    cols = list(AXES) + ["組み合わせ"] + [f"{ax}_切り替わり" for ax in AXES] + ["荒さ_値", "株の向き_値", "方向感_値", "方向感_基準"]
    p = os.path.join(od, "状態ラベル.csv"); keep[cols].round(4).to_csv(p, encoding="utf-8")
    json.dump({"定義": "事前登録_状態ラベル.md §1", "params": P, "N": N_DEFAULT, "期間": [str(keep.index[0].date()), str(keep.index[-1].date()), int(len(keep))], "data": report},
              open(os.path.join(od, "状態ラベル_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"書いた: {p}  {keep.index[0].date()}〜{keep.index[-1].date()}  {len(keep)} 日")


if __name__ == "__main__":
    main()
