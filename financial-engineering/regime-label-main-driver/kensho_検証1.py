#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kensho_検証1.py — 局面判定ラベルは既知の転換点を拾えるか（事前登録_検証1.md §2・§3 のまま・2026-11-13 固定）。

主: 過去の 8 つの転換点（期待する主役つき）。当たり＝出来事の日から 40 営業日のうち L＝期待する主役が 10 日以上。
    偶然との比較＝要因ごとに、全部の日を起点にして同じ条件を満たす割合 q(k)。当たりの数 H 以上になる確率 p を厳密に計算。
判定: 支持＝H ≥ 5 かつ p ≤ 0.05／棄却＝p > 0.20／ほかは未確定。
副（判定に使わない）: 2026-06-22 の (A) 前 40 日のうち L＝SEMI が 20 日以上 (B) 後 60 日以内に SEMI から別の要因へ切り替わり。
    2026-11-05 は前向きの予約（2027-02-01 以降に判定）。
記述: 要因ごとの日数の割合・年あたりの切り替わり・局面の長さ・変種（生の R² 最大、窓 40・120、連続 3・10。良く見えても採らない）。

使い方:  <venv_forward の python> kensho_検証1.py   （--smoke で経路だけ。results/_smoke/・判定に使わない）
"""
import argparse, datetime as dt, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_label as ML

EVENTS = [  # 事前登録 §2 の表（ラベルを計算する前に固定）
    (1, "2013-05-22", "緩和縮小の発言", "RATE"), (2, "2014-11-27", "OPEC の減産見送り", "OIL"), (3, "2016-01-04", "年初の急落（株と原油）", "OIL"),
    (4, "2020-02-24", "コロナの急落の始まり", "EQ"), (5, "2021-02-25", "米長期金利の急騰", "RATE"), (6, "2022-01-05", "FRB の引き締め転換", "RATE"),
    (7, "2023-05-25", "エヌビディア決算の翌日", "SEMI"), (8, "2024-07-31", "日銀の利上げ", "JPY")]
HIT_WIN, HIT_MIN = 40, 10
VARIANTS = {"主（窓60・連続5・普段との比較）": {}, "生の R² の最大": {"mode": "raw"}, "窓 40": {"W": 40, "MINV": 30}, "窓 120": {"W": 120, "MINV": 90},
            "連続 3": {"N": 3}, "連続 10": {"N": 10}}
COLORS = {"EQ": "#4c78a8", "SEMI": "#e45756", "RATE": "#f2a541", "USD": "#59a14f", "JPY": "#9c6ade", "OIL": "#6b6b6b"}
NAMES = {"EQ": "株", "SEMI": "半導体", "RATE": "米金利", "USD": "ドル", "JPY": "円", "OIL": "原油"}


def idx_on_or_after(cal, d):
    i = int(np.searchsorted(cal.values, np.datetime64(pd.Timestamp(d))))
    return i if i < len(cal) else None


def poisson_binom_tail(qs, H):
    """当たる確率が qs の独立な試行で、当たりが H 以上になる確率。"""
    dist = np.zeros(len(qs) + 1); dist[0] = 1.0
    for q in qs:
        dist[1:] = dist[1:] * (1 - q) + dist[:-1] * q; dist[0] *= (1 - q)
    return float(dist[H:].sum())


def judge(cal, L, sw):
    L = np.array([x if x is not None and x == x else "" for x in L], dtype=object); T = len(L)
    first = int(np.argmax(L != "")) if (L != "").any() else T
    res = {"ラベルの最初の日": str(cal[first].date()) if first < T else None, "ラベルの最後の日": str(cal[-1].date())}
    # 偶然の割合 q(k): 起点 s（ラベルあり・s+39 がデータの中）で、その後 40 日のうち L＝k が 10 日以上
    q = {}
    for k in ML.FACTORS:
        is_k = (L == k).astype(float); c = np.cumsum(np.insert(is_k, 0, 0.0))
        cnt = c[HIT_WIN:] - c[:-HIT_WIN]                      # cnt[s] = s..s+39 の日数
        starts = np.arange(first, T - HIT_WIN + 1)
        q[k] = float((cnt[starts] >= HIT_MIN).mean()) if len(starts) else float("nan")
    rows, qs, H = [], [], 0
    for no, d, name, k in EVENTS:
        i = idx_on_or_after(cal, d)
        if i is None or i < first or i + HIT_WIN > T:
            rows.append({"番号": no, "日付": d, "出来事": name, "期待": k, "状態": "範囲外"}); continue
        seg = L[i:i + HIT_WIN]; n = int((seg == k).sum()); hit = n >= HIT_MIN; H += int(hit); qs.append(q[k])
        vals, cnts = np.unique(seg, return_counts=True)
        into = [str(cal[t].date()) for t in range(max(first + 1, i - 10), i + HIT_WIN) if sw[t] and L[t] == k]
        rows.append({"番号": no, "日付": d, "出来事": name, "期待": k, "期待の日数": n, "当たり": bool(hit), "偶然の割合": round(q[k], 3),
                     "40日の内訳": {v: int(c) for v, c in sorted(zip(vals, cnts), key=lambda z: -z[1])}, "出来事の日のL": L[i],
                     "期待への切り替わりの日（-10〜+40）": into})
    n_eval = len(qs); p = poisson_binom_tail(qs, H) if n_eval else float("nan")
    if n_eval < len(EVENTS): verdict = "判定不能（範囲外の出来事あり）"
    elif H >= 5 and p <= 0.05: verdict = "支持"
    elif p > 0.20: verdict = "棄却"
    else: verdict = "未確定"
    res.update({"偶然の割合_q": {k: round(v, 3) for k, v in q.items()}, "出来事": rows, "当たりの数_H": H, "評価した数": n_eval,
                "偶然の期待値": round(float(np.sum(qs)), 2), "p": p, "判定": verdict})
    # 記述
    lab = L[first:]; n = len(lab); years = n / 252.0; nsw = int(np.asarray(sw)[first:].sum())
    runs, cur, ln = [], lab[0] if n else None, 0
    for x in lab:
        if x == cur: ln += 1
        else: runs.append(ln); cur, ln = x, 1
    runs.append(ln)
    res["記述"] = {"要因ごとの日数の割合": {k: round(float((lab == k).mean()), 3) for k in ML.FACTORS}, "切り替わりの回数": nsw,
                 "年あたりの切り替わり": round(nsw / years, 1) if years else None, "局面の長さの中央値（営業日）": float(np.median(runs)) if runs else None,
                 "局面の長さの平均": round(float(np.mean(runs)), 1) if runs else None, "細かすぎる（年12回超）": bool(years and nsw / years > 12)}
    return res


def peak_reading(cal, L, sw, d, pre=40, pre_min=20, post=60):
    """SOX の高値の読み方（副）: (A) 前 40 日のうち L＝SEMI が 20 日以上 (B) 後 60 日以内に SEMI から別の要因への切り替わり。"""
    L = np.array([x if x is not None and x == x else "" for x in L], dtype=object); T = len(L); i = idx_on_or_after(cal, d)
    if i is None or i - pre < 0: return {"日付": d, "状態": "範囲外"}
    nA = int((L[i - pre:i] == "SEMI").sum()); A = nA >= pre_min
    end = min(T - 1, i + post); outs = [str(cal[t].date()) for t in range(i + 1, end + 1) if sw[t] and L[t - 1] == "SEMI" and L[t] != "SEMI"]
    B = len(outs) > 0; enough = (i + post) <= T - 1
    reading = ("拾えた" if A and B else "主役は当てたが、高値は切り替わりとして出ない" if A else "この時期の半導体相場を主役として捉えていない")
    if A and not B and not enough: reading += "（後の 60 日がまだ揃っていない）"
    vals, cnts = np.unique(L[i - pre:i], return_counts=True); vals2, cnts2 = np.unique(L[i + 1:end + 1], return_counts=True)
    return {"日付": d, "A_前40日のSEMIの日数": nA, "A": bool(A), "B_SEMIからの切り替わりの日": outs, "B": bool(B), "後のデータが60日ある": bool(enough),
            "読み": reading, "前40日の内訳": {v: int(c) for v, c in zip(vals, cnts)}, "後の内訳": {v: int(c) for v, c in zip(vals2, cnts2)}, "出来事の日のL": L[i]}


def base_rates(cal, L, sw):
    """副の比べ用: 全部の日を起点にした (A)(B) の割合と、任意の日から 40 日以内に切り替わりがある割合。"""
    L = np.array([x if x is not None and x == x else "" for x in L], dtype=object); T = len(L); first = int(np.argmax(L != ""))
    sw = np.asarray(sw); a = b = n = 0; any40 = m = 0
    out_sw = np.array([bool(sw[t] and L[t - 1] == "SEMI" and L[t] != "SEMI") for t in range(T)])
    for i in range(first + 40, T - 60):
        n += 1; A = (L[i - 40:i] == "SEMI").sum() >= 20; a += A; b += bool(A and out_sw[i + 1:i + 61].any())
    for i in range(first, T - 40):
        m += 1; any40 += bool(sw[i + 1:i + 41].any())
    return {"A を満たす日の割合": round(a / n, 3) if n else None, "A かつ B の割合": round(b / n, 3) if n else None,
            "任意の日から40日以内に切り替わりがある割合": round(any40 / m, 3) if m else None}


def svg_timeline(cal, L, path, events):
    """1 年 1 行の色帯（L）と出来事の印。"""
    L = np.array([x if x is not None and x == x else "" for x in L], dtype=object)
    years = sorted({d.year for d, x in zip(cal, L) if x}); W, rh, x0, y0 = 900, 22, 60, 50; H = y0 + rh * len(years) + 70
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="11">', f'<rect width="{W}" height="{H}" fill="white"/>',
         '<text x="60" y="20" font-size="14">局面判定ラベル L（確定した主役）— 1 年 1 行・▼ は検証 1 の出来事（番号）と 2026 年の 2 件（T1・T2）</text>']
    for j, k in enumerate(ML.FACTORS):
        o.append(f'<rect x="{x0 + j * 110}" y="28" width="12" height="12" fill="{COLORS[k]}"/><text x="{x0 + j * 110 + 16}" y="38">{k} {NAMES[k]}</text>')
    xs = lambda d: x0 + (d.dayofyear - 1) / 366.0 * (W - x0 - 20)
    for r, y in enumerate(years):
        yy = y0 + r * rh; o.append(f'<text x="10" y="{yy + 14}">{y}</text>')
        idx = [t for t, d in enumerate(cal) if d.year == y and L[t]]
        s = 0
        while s < len(idx):
            e = s
            while e + 1 < len(idx) and L[idx[e + 1]] == L[idx[s]] and idx[e + 1] == idx[e] + 1: e += 1
            xa, xb = xs(cal[idx[s]]), xs(cal[idx[e]]) + (W - x0 - 20) / 260.0
            o.append(f'<rect x="{xa:.1f}" y="{yy + 3}" width="{max(xb - xa, 1):.1f}" height="{rh - 7}" fill="{COLORS[L[idx[s]]]}"/>'); s = e + 1
    for tag, d in events:
        d = pd.Timestamp(d)
        if d.year in years:
            yy = y0 + years.index(d.year) * rh; x = xs(d)
            o.append(f'<path d="M{x - 4:.1f},{yy - 1} L{x + 4:.1f},{yy - 1} L{x:.1f},{yy + 6} Z" fill="black"/><text x="{x + 6:.1f}" y="{yy + 4}" font-size="9">{tag}</text>')
    o.append("</svg>"); open(path, "w", encoding="utf-8").write("\n".join(o))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
    cal, R, X, report = ML.load_all(a.smoke)
    od = os.path.join(HERE, "results", "_smoke") if a.smoke else os.path.join(HERE, "results"); os.makedirs(od, exist_ok=True)
    out = {"検証": "局面判定ラベル 検証1（既知の転換点）", "実行": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "smoke": bool(a.smoke), "事前登録": "事前登録_検証1.md（2026-11-13 18:57）",
           "params": ML.PARAMS, "data": report, "変種": {}}
    for name, kw in VARIANTS.items():
        p = dict(ML.PARAMS); p.update({k: v for k, v in kw.items() if k != "mode"})
        lab = ML.build(cal, R, X, mode=kw.get("mode", "pct"), **p); L = lab["L"].tolist(); sw = lab["切り替わり"].values
        r = judge(cal, L, sw)
        if not kw:
            out["主"] = r
            out["副_2026-06-22"] = peak_reading(cal, L, sw, "2026-06-22")
            out["記述_2024-07-10（過去の同じ形）"] = peak_reading(cal, L, sw, "2024-07-10")
            out["副の比べ用の割合"] = base_rates(cal, L, sw)
            i5 = idx_on_or_after(cal, "2026-11-05")
            out["副_2026-11-05"] = {"状態": "前向きの予約（2027-02-01 以降の最初の実行で判定。定義は変えない）",
                                   "今あるデータ": f"{cal[-1].date()} まで（11-05 の後 {len(cal) - 1 - i5 if i5 is not None else 0} 営業日）"}
            tail = lab[lab["L"].notna()].tail(140)
            out["直近の切り替わり"] = [{"日": str(d.date()), "L": l} for d, l, s in zip(tail.index, tail["L"], tail["切り替わり"]) if s]
            out["最後の日のL"] = {"日": str(lab.index[-1].date()), "L": L[-1], "暫定": int(lab["暫定"].iloc[-1])}
            svg_timeline(cal, L, os.path.join(od, "局面ラベル_年表.svg"), [(str(n), d) for n, d, _, _ in EVENTS] + [("T1", "2026-06-22"), ("T2", "2026-11-05")])
        else:
            out["変種"][name] = {"H": r["当たりの数_H"], "p": r["p"], "判定（採らない・比べるだけ）": r["判定"], "当たった番号": [x["番号"] for x in r["出来事"] if x.get("当たり")],
                               "割合": r["記述"]["要因ごとの日数の割合"], "年あたりの切り替わり": r["記述"]["年あたりの切り替わり"], "q": r["偶然の割合_q"]}
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S"); p = os.path.join(od, f"検証1_判定_{stamp}.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    m = out["主"]; print(f"書いた: {p}")
    print(f"主: H={m['当たりの数_H']}/{m['評価した数']}  偶然の期待値={m['偶然の期待値']}  p={m['p']:.4f}  判定={m['判定']}")
    for r in m["出来事"]: print("  ", r.get("番号"), r.get("日付"), r.get("期待"), r.get("期待の日数"), "当たり" if r.get("当たり") else r.get("状態", "外れ"), r.get("40日の内訳"))
    print("記述:", m["記述"]); print("06-22:", out["副_2026-06-22"])
    for k, v in out["変種"].items(): print("  変種", k, v["H"], round(v["p"], 4), v["当たった番号"], v["年あたりの切り替わり"])


if __name__ == "__main__":
    main()
