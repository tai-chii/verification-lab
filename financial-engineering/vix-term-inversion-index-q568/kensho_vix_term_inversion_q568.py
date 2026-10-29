#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q568: VIX の期間構造の逆転（VIX/VIX3M ≥ 1）の後 20 営業日は、株価指数 10 本の平均リターンがそれ以外の日より高いか
================================================================================

【出典】
- 計画（事前登録）: 無料の新しい源 2 案 第1弾（Opus 2026-10-29）。アイデア候補.md の該当行。taichi「まずは無料分で進めて」（合成に足す独立したエッジ探し）。
- Fassas & Hourvouliades (2019) JRFM 12(3):113「VIX Futures as a Market Timing Indicator」: VIX 先物の期間構造の形は S&P 500 の逆張りのタイミング指標になる。
- 連鎖: Q473（S19）で VIX の水準ゲート（高 VIX の日に指数を休む）は棄却。閉じた日（高 VIX）の指数の平均は +8.6 bp/日で、開いた日 +2.7 bp/日より高かった。
  → 水準ではなく「期間構造の逆転（短期の恐怖が中期を上回る）」の後に、逆に持つと稼げるか。
- 運用の決まり 2026-10-29: 新しい bot は合成への追加関門（tools/composite_gate.py）も見る。

【仮説（測る前に固定）】
H1: 逆転日（VIX/VIX3M ≥ 1.0）から 20 営業日の窓に入っている日の、指数 10 本等金額のリターンは、窓の外の日より高い。
H0: 差は 0 と区別できない（または負）。

【データ】
- CBOE 公式 CDN の VIX・VIX3M 日足終値（`_データ/raw/vol/cboe_VIX.csv`・`cboe_VIX3M.csv`、fetch_cboe_vix_term.py）。VIX3M は 2009-09-18 から。
- 指数 10 本（US500・USTECH・US30・GER40・JPN225・UK100・FRA40・ESP35・AUS200・SUI20）の D1（fe_core.load_d1・UTC 0 時区切り）。S17b と同じ。
- 期間: 2009-10-01〜2024-06-30（**2024-07-01 以降は封印**）。前半 <2017・後半 ≥2017。

【定義（1 通りに固定）】
- 合図: ratio[d] = VIX 終値 / VIX3M 終値（米国の営業日 d）。指数の D1 の日 t には **t−1 暦日以前で最新の ratio** を使う（米国 16:15 ET 確定・UTC 0 時の足より前に既知だが安全側）。
- 逆転日: ratio ≥ 1.0（閾値は動かさない）。窓: 逆転日の翌日から 20 指数営業日（共通の暦＝10 本のどれかが動いた日）。窓の中なら in=1。
- 損益: 各指数の D1 の close-to-close リターンの等金額平均 − 保有コスト年 4%/252（S17b と同じ・建てているときだけ）。
- (a) 条件つき平均の差: 日ごとの指数平均リターン r[t] を in=1 と in=0 に分け、年ごとに (in=1 の平均 − in=0 の平均) → 年単位 t（in=1 の日が 5 日以上ある年だけ）。
- (b) 戦略 B: in=1 の日だけ指数 10 本を等金額で買い、ほかは持たない。比較: 常に持つ（S17b の指数部分）。Sharpe・最大下落・保有日の割合。
- 帰無: 逆転日の列（0/1）を循環シフト（min_shift 250 日）して窓を作り直し、(a) の全期間の差を B=1000 回 → z。

【測るもの】(a) の差 [bp/日]・年単位 t（全・前・後）・z。(b) の Sharpe（全・前・後）と常に持つとの比較、合成の追加関門（composite_gate.py）の結果。
記述: 逆転日の数・窓の日の割合・年ごとの内訳、閾値 0.95・1.05 と窓 10・40 日の感度（判定に使わない）。

【判定（事前固定・変更禁止）】
(a) の差が 前半・後半とも > 0 かつ 年単位 t ≥ 2（全期間）かつ z ≥ 2 → **支持: 逆転の後は指数を持つと稼げる**。
(a) の全期間の差 ≤ 0、または z < 1 → **棄却**。それ以外 → 未確定。
多重比較: 判定は (a) の 1 本（閾値 1.0・窓 20 日の 1 点）。感度・(b)・追加関門は記述。

【捨てた案の数】約 5: VX 先物の 1・2 限月の傾き（ファイルが多い・VIX3M で代用）、閾値の格子（感度で記述のみ）、逆転中だけ持つ（窓なし・底を待たずに入る）、
逆転で売る（S19 の棄却と同じ向き）、VIX9D/VIX（短すぎて日々の揺れが大きい）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。

【委託の確かめ方】設計・コードは Opus（2026-10-29）。実行と解釈は後で Opus。実行者は JSON の main（差・t・z）と machine_verdict、gate を返す。

【実装】実行: python3 kensho_vix_term_inversion_q568.py（B=1000・1 分以内）／--smoke（合成データ・判定に使わない）
"""
import argparse, datetime as _dt, json, math, os, sys, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
QID = "Q568"
IDX10 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "AUS200", "SUI20"]
START, SEAL_END, SPLIT = pd.Timestamp("2009-10-01"), pd.Timestamp("2024-07-01"), 2017
THR, WIN, HOLD_COST = 1.0, 20, 0.04
MIN_SHIFT, SEED = 250, 20261029
SENS = [(0.95, 20), (1.05, 20), (1.0, 10), (1.0, 40)]


def _p(*parts):
    a = os.path.join(WS, *parts)
    return a if os.path.exists(a) else os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def sharpe(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if len(x) > 20 and x.std(ddof=1) > 0 else float("nan")


def maxdd(x):
    c = np.cumsum(np.nan_to_num(x)); return float((c - np.maximum.accumulate(c)).min())


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


# ----------------------------------------------------------------------------- データ
def load(smoke, rng):
    if smoke:
        t = pd.bdate_range("2009-10-01", "2024-06-28")
        n = len(t); r = rng.normal(0.0003, 0.011, n)
        vix = 18 * np.exp(np.cumsum(rng.normal(0, 0.06, n)) * 0.2); vix3m = vix * np.exp(rng.normal(0.08, 0.06, n))
        ratio = pd.Series(vix / vix3m, index=t)
        return pd.Series(r, index=t), ratio, {"idx_days": n}
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
    from fe_core import load_d1
    R = {}
    for s in IDX10:
        d = load_d1(s); d = d[(d["time"] >= START) & (d["time"] < SEAL_END)]
        R[s] = pd.Series(d["ret"].to_numpy(), index=pd.DatetimeIndex(d["time"]).tz_localize(None).normalize())
    P = pd.DataFrame(R).sort_index()
    r = P.mean(axis=1, skipna=True).dropna()
    vol = _p("検証", "_データ", "raw", "vol")
    v = pd.read_csv(os.path.join(vol, "cboe_VIX.csv"), parse_dates=["date"]).set_index("date")["close"]
    v3 = pd.read_csv(os.path.join(vol, "cboe_VIX3M.csv"), parse_dates=["date"]).set_index("date")["close"]
    ratio = (v / v3).dropna(); ratio = ratio[ratio.index < SEAL_END]
    return r, ratio, {"idx_days": int(len(r)), "n_syms_last": int(P.iloc[-1].notna().sum())}


def align_ratio(r_index, ratio):
    """指数の日 t に、t−1 暦日以前で最新の ratio を当てる。"""
    s = ratio.copy(); s.index = s.index + pd.Timedelta(days=1)
    return s.reindex(r_index.union(s.index)).ffill().reindex(r_index)


def window_flag(ev, win):
    """ev: 0/1（日 t の合図が逆転）。逆転日の翌日から win 日を in=1。"""
    e = np.asarray(ev, float); n = len(e); out = np.zeros(n)
    idx = np.flatnonzero(e > 0)
    for i in idx:
        out[i + 1: min(n, i + 1 + win)] = 1.0
    return out


def cond_diff(r, inn, years):
    d = pd.DataFrame({"r": r, "in": inn, "y": years})
    rows = []
    for y, g in d.groupby("y"):
        a, b = g[g["in"] == 1]["r"], g[g["in"] == 0]["r"]
        if len(a) >= 5 and len(b) >= 5:
            rows.append((y, a.mean() - b.mean()))
    yy = pd.DataFrame(rows, columns=["y", "diff"])
    allm = d[d["in"] == 1]["r"].mean() - d[d["in"] == 0]["r"].mean()
    return float(allm), yy


def run(args):
    rng = np.random.default_rng(args.seed)
    r, ratio, meta = load(args.smoke, rng)
    rat = align_ratio(r.index, ratio)
    valid = rat.notna().values
    r = r[valid]; rat = rat[valid]
    years = r.index.year.values
    ev = (rat.values >= THR).astype(float)
    inn = window_flag(ev, WIN)
    rv = r.values
    full, yy = cond_diff(rv, inn, years)
    pre, post = years < SPLIT, years >= SPLIT
    fp, _ = cond_diff(rv[pre], inn[pre], years[pre]); fq, _ = cond_diff(rv[post], inn[post], years[post])
    t_all = tstat(yy["diff"].values)
    # 帰無
    null = []
    n = len(ev)
    for _ in range(args.B):
        k = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT)); e2 = np.roll(ev, k)
        m, _ = cond_diff(rv, window_flag(e2, WIN), years); null.append(m)
    null = np.asarray(null)
    z = float((full - null.mean()) / null.std(ddof=1)) if null.std(ddof=1) > 0 else float("nan")
    # 戦略 B と常に持つ
    cost = HOLD_COST / 252
    stratB = inn * (rv - cost); always = rv - cost
    def stats(x, m):
        return {"sharpe": f(sharpe(x[m]), 3), "mean_bp": f(np.nanmean(x[m]) * 1e4, 3), "maxdd_add": f(maxdd(x[m]), 4)}
    allm = np.ones(n, bool)
    strat = {"B_window_only": {p: stats(stratB, m) for p, m in (("all", allm), ("pre", pre), ("post", post))},
             "always_long": {p: stats(always, m) for p, m in (("all", allm), ("pre", pre), ("post", post))},
             "B_exposure": f(inn.mean(), 3)}
    sens = {}
    for thr, win in SENS:
        e = (rat.values >= thr).astype(float); w = window_flag(e, win); m, yv = cond_diff(rv, w, years)
        sens[f"thr{thr}_win{win}"] = {"diff_bp": f(m * 1e4, 3), "year_t": f(tstat(yv["diff"].values), 3), "in_share": f(w.mean(), 3), "n_events": int(e.sum())}
    main = {"diff_bp_all": f(full * 1e4, 3), "diff_bp_pre": f(fp * 1e4, 3), "diff_bp_post": f(fq * 1e4, 3), "year_t_all": f(t_all, 3),
            "z": f(z, 3), "null_mean_bp": f(null.mean() * 1e4, 3), "null_p2_5_bp": f(np.percentile(null, 2.5) * 1e4, 3), "null_p97_5_bp": f(np.percentile(null, 97.5) * 1e4, 3),
            "n_events": int(ev.sum()), "in_share": f(inn.mean(), 3), "n_days": int(n), "years_used": int(len(yy))}
    g = lambda k: main.get(k) if main.get(k) is not None else float("nan")
    if g("diff_bp_pre") > 0 and g("diff_bp_post") > 0 and g("year_t_all") >= 2 and g("z") >= 2:
        verdict = "支持: 逆転の後は指数を持つと稼げる"
    elif g("diff_bp_all") <= 0 or g("z") < 1:
        verdict = "棄却"
    else:
        verdict = "未確定"
    by_year = {int(y): f(d * 1e4, 2) for y, d in zip(yy["y"], yy["diff"])}
    daily = pd.DataFrame({"date": r.index, "r_idx": rv, "ratio": rat.values, "event": ev, "in": inn, "stratB": stratB})
    res = {"question": "VIX/VIX3M≥1 の逆転後 20 営業日は指数 10 本の平均リターンが高いか", "settings": {"thr": THR, "win": WIN, "B": args.B, "start": str(START.date()), "seal_end": str(SEAL_END.date()),
           "split_year": SPLIT, "hold_cost": HOLD_COST, "min_shift": MIN_SHIFT}, "data": meta, "main": main, "by_year_diff_bp": by_year, "strategy": strat,
           "sensitivity": sens, "machine_verdict": verdict,
           "multiple_comparisons": "判定は (a) の 1 本。感度 4 点・戦略 B・合成の追加関門は記述。"}
    return res, daily


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=1000); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    res, daily = run(args)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{QID}" if args.smoke else QID
    p = os.path.join(out, f"{pre}_result_{ts}.json"); json.dump({"qid": QID, "smoke": args.smoke, "generated": ts, **res}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dp = os.path.join(out, f"{pre}_daily_{ts}.csv"); daily.to_csv(dp, index=False)
    print("wrote", os.path.relpath(p, HERE)); print("main:", res["main"]); print("machine_verdict:", res["machine_verdict"])
    if not args.smoke:
        try:
            sys.path.insert(0, os.path.join(HERE, "..", "..", "tools")); from composite_gate import gate
            s = daily.set_index("date")["stratB"]; gr = gate(s, "Q568 逆転後 20 日の指数 β")
            print("composite_gate:", json.dumps(gr["関門"], ensure_ascii=False))
            res2 = json.load(open(p, encoding="utf-8")); res2["composite_gate"] = gr; json.dump(res2, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception as e:
            print("composite_gate 失敗:", e)


if __name__ == "__main__":
    main()
