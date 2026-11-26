#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p0_check.py — 事前登録の合格条件を「実力ゼロの戦略でも通る確率 P0」で測る（2026-11-27・taichi「足して」）。

なぜ: これまでの試行は実効で約 175〜375 本あり、開発期間の最良の t は偶然でも 2.7〜3.0 に届く
（`_基盤/知識/検証方法論/試行の実効数_20261127.md`）。偶然を落とすのは「1 回だけ開ける期間」の合格条件だが、
記録中の 8 本のうち 6 本はその条件の P0 が 14〜50% か、条件が無かった。結果を見る前に P0 を出し、5% 以下を目安にする。

計算:
  --series を渡すと、その日次（か週次・月次）の損益を平均 0 にずらし、循環ブロック・ブートストラップで判定期間と同じ長さの系列を
  --n 本作り、条件を全部当てて通った割合を P0 とする。真の年率シャープ 0.5・1.0 の場合（平均を足す）も同じやり方で出す（検出力）。
  --series が無いと正規近似（t・平均の条件と「前後半とも正」だけ。PF は系列が要る）。
  帰無 z（並べ替え・循環シフト）の条件はここでは作れない。損益の条件と独立とみなして掛けるなら --z-pass に帰無での通過率を渡す。

使い方:
  python3 p0_check.py --T 520 --t 2.0                                           # 正規近似: 日次 t ≥ 2 を 520 日
  python3 p0_check.py --T 730 --series dev_daily.csv --col net --pf 1.05 --nw-t 1.5 --halves --mean-min 0
  python3 p0_check.py --T 24 --per-year 12 --t 2.0 --series ic_monthly.csv --col ic --block 3
終了コード: 0＝P0 ≤ --max（既定 0.05）・1＝P0 が目安を超える・2＝使い方の誤り
"""
import argparse, json, math, sys
import numpy as np


def norm_sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2))


def nw_t(x, lag):
    n = len(x); m = x.mean(); e = x - m
    g0 = (e @ e) / n; s = g0
    for k in range(1, lag + 1):
        gk = (e[k:] @ e[:-k]) / n
        s += 2 * (1 - k / (lag + 1)) * gk
    return m / math.sqrt(s / n) if s > 0 else 0.0


def passes(x, a):
    """条件を全部当てる。返り値: (全部通ったか, 条件ごとの結果の辞書)"""
    r = {}
    m = x.mean(); sd = x.std(ddof=1)
    if a.mean_min is not None: r["平均"] = m > a.mean_min if a.mean_min == 0 else m >= a.mean_min
    if a.t is not None: r["t"] = (m / sd * math.sqrt(len(x)) if sd > 0 else 0) >= a.t
    if a.nw_t is not None: r["NW t"] = nw_t(x, a.lag) >= a.nw_t
    if a.pf is not None:
        neg = -x[x < 0].sum(); r["PF"] = (x[x > 0].sum() / neg if neg > 0 else np.inf) >= a.pf
    if a.halves:
        h = len(x) // 2; r["前後半"] = x[:h].mean() > 0 and x[h:].mean() > 0
    if a.years:
        k = int(a.per_year); chunks = [x[i:i + k] for i in range(0, len(x) - k + 1, k)]
        r["年ごと"] = all(c.mean() > 0 for c in chunks) if chunks else False
    return all(r.values()), r


def boot(base, a, shift, rng):
    n, T, b = len(base), a.T, a.block
    ok = 0; per = {}
    for _ in range(a.n):
        starts = rng.integers(0, n, size=math.ceil(T / b))
        idx = np.concatenate([(s + np.arange(b)) % n for s in starts])[:T]
        good, r = passes(base[idx] + shift, a)
        ok += good
        for k, v in r.items(): per[k] = per.get(k, 0) + v
    return ok / a.n, {k: round(v / a.n, 4) for k, v in per.items()}


def main():
    ap = argparse.ArgumentParser(description="事前登録の合格条件の P0（実力ゼロで通る確率）")
    ap.add_argument("--T", type=int, required=True, help="判定期間の観測数（日次なら営業日数）")
    ap.add_argument("--per-year", type=float, default=252, help="1 年の観測数（日次 252・週次 52・月次 12）")
    ap.add_argument("--t", type=float, help="t ≥ この値（自己相関の補正なし）")
    ap.add_argument("--nw-t", type=float, help="Newey-West の t ≥ この値（系列が要る）")
    ap.add_argument("--lag", type=int, default=5)
    ap.add_argument("--mean-min", type=float, help="平均がこの値を超える（0 なら > 0、それ以外は ≥）")
    ap.add_argument("--pf", type=float, help="PF ≥ この値（系列が要る）")
    ap.add_argument("--halves", action="store_true", help="前後半とも平均 > 0")
    ap.add_argument("--years", action="store_true", help="1 年ずつの平均がすべて > 0（系列が要る）")
    ap.add_argument("--z-pass", type=float, help="帰無 z の条件が帰無で通る割合（独立とみなして掛ける。例: z ≥ 1.5 なら 0.067）")
    ap.add_argument("--series", help="開発期間の損益の CSV（列は --col）。平均を 0 にずらして使う")
    ap.add_argument("--col", help="損益の列の名前")
    ap.add_argument("--block", type=int, default=20, help="ブロックの長さ（日次 20・週次 4・月次 3）")
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261127)
    ap.add_argument("--max", type=float, default=0.05, help="P0 の目安（これ以下なら終了コード 0）")
    a = ap.parse_args()
    if not any(v is not None for v in (a.t, a.nw_t, a.mean_min, a.pf)) and not (a.halves or a.years):
        ap.error("条件を 1 つ以上指定する")
    out = {"T": a.T, "1年の観測数": a.per_year, "乱数の種": a.seed}
    if a.series:
        import pandas as pd
        df = pd.read_csv(a.series)
        x = pd.to_numeric(df[a.col], errors="coerce").dropna().to_numpy(float)
        if len(x) < max(50, a.block * 5): ap.error(f"系列が短すぎる（{len(x)}）")
        base = x - x.mean(); sd = base.std(ddof=1)
        rng = np.random.default_rng(a.seed)
        res = {}
        for name, sr in (("P0", 0.0), ("SR0.5", 0.5), ("SR1.0", 1.0)):
            p, per = boot(base, a, sr / math.sqrt(a.per_year) * sd, rng)
            res[name] = dict(通過=round(p, 4), 条件ごと=per)
        out.update(方法="平均 0 にずらした循環ブロック・ブートストラップ", ブロック=a.block, 回数=a.n, 系列=a.series, 列=a.col, 系列の長さ=len(x), 結果=res)
        p0 = res["P0"]["通過"]
    else:
        if a.nw_t is not None or a.pf is not None or a.years:
            ap.error("NW t・PF・年ごとの条件には --series が要る")
        res = {}
        for name, sr in (("P0", 0.0), ("SR0.5", 0.5), ("SR1.0", 1.0)):
            mu_t = sr * math.sqrt(a.T / a.per_year)                   # 平均の t の期待値
            p = 1.0
            if a.t is not None: p *= norm_sf(a.t - mu_t)
            if a.mean_min is not None and a.t is None: p *= norm_sf(0 - mu_t)   # 平均 > 0 を t > 0 と読む（mean_min が 0 でないときは近似できないので系列を使う）
            if a.halves: p *= norm_sf(-mu_t / math.sqrt(2)) ** 2 if a.t is None else 1.0  # t の条件と重なるときは掛けない（概算）
            res[name] = dict(通過=round(p, 4))
        out.update(方法="正規近似（条件は独立とみなす概算）", 結果=res)
        p0 = res["P0"]["通過"]
        if a.mean_min not in (None, 0): out["注"] = "mean_min が 0 以外は正規近似で扱えない（--series を渡す）"
    if a.z_pass is not None:
        for k in out["結果"]: out["結果"][k]["通過_z込み"] = round(out["結果"][k]["通過"] * (a.z_pass if k == "P0" else 1.0), 4)
        out["注_z"] = "帰無 z は損益の条件と独立とみなして P0 にだけ掛けた（検出力の行には掛けていない＝上限）"
        p0 = out["結果"]["P0"]["通過_z込み"]
    out["P0"] = p0; out["目安"] = a.max; out["判定"] = "よい（P0 が目安以下）" if p0 <= a.max else "弱い（P0 が目安を超える。条件を強めるか期間を延ばす）"
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if p0 <= a.max else 1)


if __name__ == "__main__":
    main()
