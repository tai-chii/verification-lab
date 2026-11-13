#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kensho_合成_結合.py — 状態ラベルの 2 本目の結合: 生き残り 3 本の合成に「稼げていない局面」があるか。事前登録_合成の穴.md のまま（2026-11-13 20:31 固定）。読むだけ。

元: survivors-correlation-composite/results/survivors_daily_eqrisk.csv（各本を日次σで 1 にそろえた系列・2017-08-17〜2025-10-01）と Q723 の results/状態ラベル.csv。
主: 合成（1/3 等リスク）× 3 軸。2 つの状態の日次の平均の差・Newey-West（ラグ 10）・Holm。日 d の損益には d の前の営業日の状態を当てる。
読み方: Holm 後 p ≤ 0.05 の軸がある → その軸の弱い側に穴がある。どれも届かない → この 3 軸では穴は見えない。重み・停止・売買には使わない。
"""
import datetime as dt, json, math, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.dirname(HERE)
AXES = {"荒さ": ("低", "高"), "株の向き": ("上", "下"), "方向感": ("強", "弱")}   # 先に書いた方が「見込みで良い側」（方向感は見込みなし）
LAG = 10; MAIN = "合成（1/3 等リスク）"; BOTS = ["S17b 買い持ち", "S21 H1 ML", "S23 暗号の上昇時"]


def lrv(u, lag=LAG):
    u = np.asarray(u, float); n = len(u); e = u - u.mean(); s = (e ** 2).sum()
    for k in range(1, min(lag, n - 1) + 1): s += 2 * (1 - k / (lag + 1)) * (e[k:] * e[:-k]).sum()
    return s / n


def diff_nw(x, d):
    """状態 d（1/0）の間の平均の差と Newey-West の t。影響関数 u = d(x−m1)/p1 − (1−d)(x−m0)/p0 の長期分散を使う。"""
    x = np.asarray(x, float); d = np.asarray(d, float); n = len(x); p1 = d.mean(); p0 = 1 - p1
    m1 = x[d == 1].mean(); m0 = x[d == 0].mean()
    u = d * (x - m1) / p1 - (1 - d) * (x - m0) / p0
    se = math.sqrt(lrv(u) / n); t = (m1 - m0) / se
    return m1, m0, t, math.erfc(abs(t) / math.sqrt(2))


def holm(ps):
    order = sorted(ps, key=ps.get); m = len(order); out = {}; prev = 0.0
    for r, k in enumerate(order):
        adj = min(1.0, max(prev, (m - r) * ps[k])); out[k] = adj; prev = adj
    return out


def sharpe(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def episodes(s):
    """状態ごとの「続いた期間の数」。"""
    v = s.values; out = {}
    for i, x in enumerate(v):
        if i == 0 or x != v[i - 1]: out[x] = out.get(x, 0) + 1
    return out


def main():
    D = pd.read_csv(os.path.join(FE, "survivors-correlation-composite", "results", "survivors_daily_eqrisk.csv"), index_col=0, parse_dates=True)   # 生き残りの日次（2026-10-29 作成の系列をそのまま）
    lab = pd.read_csv(os.path.join(HERE, "results", "状態ラベル.csv"), index_col=0, parse_dates=True)
    cal = lab.index.values; idx = np.searchsorted(cal, D.index.values, side="left") - 1
    assert (idx >= 0).all()
    for ax in list(AXES) + ["組み合わせ"]: D[ax] = lab[ax].values[idx]
    out = {"実行": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "事前登録": "事前登録_合成の穴.md（2026-11-13 20:31）", "期間": [str(D.index[0].date()), str(D.index[-1].date()), int(len(D))],
           "NW のラグ": LAG, "全体": {c: {"平均": round(float(D[c].mean()), 4), "年率シャープ": round(sharpe(D[c]), 2)} for c in [MAIN] + BOTS}, "主": {}}
    ps = {}
    for ax, (hi, lo) in AXES.items():
        m1, m0, t, p = diff_nw(D[MAIN].values, (D[ax] == hi).values.astype(float))
        out["主"][ax] = {hi: {"平均": round(m1, 4), "年率シャープ": round(sharpe(D.loc[D[ax] == hi, MAIN]), 2), "日数": int((D[ax] == hi).sum())},
                        lo: {"平均": round(m0, 4), "年率シャープ": round(sharpe(D.loc[D[ax] == lo, MAIN]), 2), "日数": int((D[ax] == lo).sum())},
                        f"差（{hi}−{lo}）": round(m1 - m0, 4), "t": round(t, 2), "p": p, "続いた期間の数": episodes(D[ax])}
        ps[ax] = p
    hp = holm(ps); holes = []
    for ax, (hi, lo) in AXES.items():
        d = out["主"][ax]; d["p_Holm"] = hp[ax]
        if hp[ax] <= 0.05:
            weak = lo if d[f"差（{hi}−{lo}）"] > 0 else hi; d["読み"] = f"穴がある（弱い側: {weak}）"; holes.append(f"{ax}＝{weak}")
        else: d["読み"] = "差は見えない"
    out["判定"] = ("合成は次の状態で稼げていない: " + "・".join(holes)) if holes else "この 3 軸では合成の穴は見えない"
    desc = {"各本×軸": {}, "合成の組み合わせ別（薄いので読みすぎない）": {}}
    for b in BOTS:
        desc["各本×軸"][b] = {}
        for ax, (hi, lo) in AXES.items():
            m1, m0, t, p = diff_nw(D[b].values, (D[ax] == hi).values.astype(float))
            desc["各本×軸"][b][ax] = {hi: {"平均": round(m1, 4), "年率シャープ": round(sharpe(D.loc[D[ax] == hi, b]), 2)}, lo: {"平均": round(m0, 4), "年率シャープ": round(sharpe(D.loc[D[ax] == lo, b]), 2)},
                                     f"差（{hi}−{lo}）": round(m1 - m0, 4), "t": round(t, 2)}
    for k, g in D.groupby("組み合わせ"):
        desc["合成の組み合わせ別（薄いので読みすぎない）"][k] = {"日数": int(len(g)), "平均": round(float(g[MAIN].mean()), 4), "年率シャープ": round(sharpe(g[MAIN]), 2)}
    out["記述"] = desc
    json.dump(out, open(os.path.join(HERE, "results", "合成_結合.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
