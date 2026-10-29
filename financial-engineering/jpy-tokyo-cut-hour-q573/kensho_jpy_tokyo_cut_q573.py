#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q573: 東京カット（15:00 JST＝6:00 UTC）の前後 1 時間で、ドル円と円クロスの値動きの向き（5 時台の向きが 6 時台に続く／反転する）は、24 時刻の多重比較の後にも残るか
================================================================================

【出典】
- 計画（事前登録）: 東京時間 10 案の 4（Fable 2026-10-30 深夜）。README_session_20261030.md: S21 の WF で 6 時台（UTC）のエントリーが 24 時刻中で最良（R 0.160・t 3.2）＝事後の観察。
- 先行: 時刻効果は Q153（M15 の 1 次自己相関は時刻で符号が変わらない・Holm 後 0）、Q242（暗号の時刻効果 0）。東京カットの実証は手元に無い。
- 読み: 6 時台が良いのは「ロンドン開場の直前の静かな時間」か「東京カット後の実需の流れ」か。本案は時刻の 1 次自己相関（5 時台の足の符号 → 6 時台の足）を全 24 時刻で測り、6 時台を事前の焦点とする。

【仮説（測る前に固定）】
H1: USDJPY・EURJPY・GBPJPY（H1・Dukascopy）で、5 時台の足の符号で 6 時台の足を持つ（順張り）純損益（コスト後）は、3 本プール・年単位 t ≥ 2・前後半（<2017／≥2017）とも正。
    かつ 24 時刻×3 通貨の順張り純損益を 1 族で Holm 補正したとき、6 時台が残る。
H0: 6 時台は Holm 後に残らない（Q153 と同じ）。
【データ】`学問/金融工学/作業/FX/システムトレード/data_{USDJPY,EURJPY,GBPJPY}_H1_dukascopy.csv`。**2024-07-01 以降は封印**。コスト: 往復 0.02 円（段階 1・COST_RT と同じ）。
【定義】足 h の bp = (close_h/open_h − 1)×1e4。順張り: pos_h = sign(bp_{h−1})、損益_h = pos_h × bp_h − |pos_h| × 片道コスト×2（毎回出入り）。日ごとに h=6 の損益 → 年単位 t（3 通貨プール＝通貨平均を年で）。
帰無: 日内の 24 本の順序を日ごとに並べ替え（B=1000）→ h=6 の順張り損益の z。Holm: 24 時刻×3 通貨＝72 本の順張り損益の t から p（両側）→ Holm。
【測るもの】6 時台の純損益 bp/日・年単位 t（全・前・後）・z、Holm 後に残る時刻の一覧（記述）、逆張り（符号を反転）の 6 時台（記述）、合成の追加関門（記述）。
【判定（事前固定・変更禁止）】6 時台: 年単位 t ≥ 2 かつ 前後半とも > 0 かつ z ≥ 2 かつ Holm 後に残る → 支持。全期間 t < 1 または Holm 後に残らない → 棄却。ほか未確定。
多重比較: 判定は 6 時台の 1 本＋Holm（72 本）。
【捨てた案の数】約 3: 15 分足で 14:45〜15:15 JST を切る（M15 は USDJPY のみ）、カット当日のオプション建玉（データ無し）、円クロス 4 本への拡張（支持なら次）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】設計・コードは Fable。実行と解釈は Opus。実行者は JSON の main・holm_survivors・machine_verdict を返す。
【実装】python3 kensho_jpy_tokyo_cut_q573.py（1 分）／--smoke
"""
import argparse, datetime as _dt, json, math, os, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
QID = "Q573"; SEAL = pd.Timestamp("2024-07-01"); SPLIT = 2017; SYMS = ["USDJPY", "EURJPY", "GBPJPY"]; COST_RT = 0.02; FOCUS = 6; SEED = 20261030


def _p(*parts):
    a = os.path.join(WS, *parts); return a if os.path.exists(a) else os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p); adj = np.empty(m); run = 0.0
    for i, k in enumerate(o):
        run = max(run, (m - i) * p[k]); adj[k] = min(1.0, run)
    return adj


def p_two(t, n):
    from math import erf, sqrt
    return 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2)))) if np.isfinite(t) else 1.0


def load(sym, smoke, rng):
    if smoke:
        t = pd.date_range("2010-01-01", "2024-06-30", freq="h"); n = len(t); c = 110 * np.exp(np.cumsum(rng.normal(0, 0.0008, n)))
        return pd.DataFrame({"time": t, "open": np.r_[c[0], c[:-1]], "close": c})
    d = pd.read_csv(_p("検証", "学問", "金融工学", "作業", "FX", "システムトレード", f"data_{sym}_H1_dukascopy.csv")); d["time"] = pd.to_datetime(d["time"])
    return d[d["time"] < SEAL].reset_index(drop=True)


def mats(d):
    d = d.copy(); d["day"] = d["time"].dt.normalize(); d["h"] = d["time"].dt.hour; d["bp"] = (d["close"] / d["open"] - 1) * 1e4
    M = d.pivot_table(index="day", columns="h", values="bp").reindex(columns=range(24)); M = M[M.index.dayofweek < 5]
    px = d.pivot_table(index="day", columns="h", values="open").reindex(columns=range(24)).loc[M.index]
    return M, px


def follow(M, px, h, cost):
    """h−1 の符号で h を持つ順張りの純損益 [bp]（毎回出入り）。"""
    prev = M[h - 1] if h > 0 else M[23].shift(1)
    pos = np.sign(prev); c = cost / px[h] * 1e4
    return (pos * M[h] - pos.abs() * c).dropna()


def year_t(s):
    y = s.groupby(s.index.year).mean(); return float(y.mean() / (y.std(ddof=1) / math.sqrt(len(y)))) if len(y) > 2 else float("nan")


def run(args):
    rng = np.random.default_rng(args.seed); per = {}; focus = []; grid = []; nulls = []
    for s in SYMS:
        M, px = mats(load(s, smoke=args.smoke, rng=rng)); per[s] = (M, px)
        for h in range(24):
            x = follow(M, px, h, COST_RT); grid.append({"sym": s, "h": h, "bp": float(x.mean()), "t": tstat(x), "n": int(len(x))})
        fx = follow(M, px, FOCUS, COST_RT); focus.append(fx.rename(s))
        # 帰無: 日内並べ替え
        V = M.values; prevcol, col = FOCUS - 1, FOCUS; nl = []
        for _ in range(args.B):
            P = np.take_along_axis(V, np.argsort(rng.random(V.shape), axis=1), axis=1)
            nl.append(float(np.nanmean(np.sign(P[:, prevcol]) * P[:, col])))
        nulls.append(np.asarray(nl))
    F = pd.concat(focus, axis=1); pool = F.mean(axis=1).dropna()
    gross = float(np.nanmean([np.nanmean(np.sign(per[s][0][FOCUS - 1]) * per[s][0][FOCUS]) for s in SYMS]))
    null = np.mean(np.vstack(nulls), axis=0); z = float((gross - null.mean()) / null.std(ddof=1)) if null.std(ddof=1) > 0 else float("nan")
    G = pd.DataFrame(grid); G["p"] = [p_two(t, n) for t, n in zip(G["t"], G["n"])]; G["p_holm"] = holm(G["p"].values)
    surv = G[G["p_holm"] < 0.05][["sym", "h", "bp", "t", "p_holm"]].round(3).to_dict("records")
    focus_holm = bool(((G["h"] == FOCUS) & (G["p_holm"] < 0.05) & (G["t"] > 0)).any())
    pre, post = pool[pool.index.year < SPLIT], pool[pool.index.year >= SPLIT]
    contra = -pool  # 逆張り（コストは同じなので符号だけ反転・記述）
    main = {"focus_hour_utc": FOCUS, "bp_per_day_pool": f(pool.mean(), 3), "year_t": f(year_t(pool), 2), "bp_pre": f(pre.mean(), 3), "bp_post": f(post.mean(), 3),
            "year_t_pre": f(year_t(pre), 2), "year_t_post": f(year_t(post), 2), "z": f(z, 2), "gross_bp": f(gross, 3), "null_mean": f(null.mean(), 3),
            "holm_focus_survives": focus_holm, "contrarian_bp": f(contra.mean(), 3), "n_days": int(len(pool))}
    g = lambda k: main[k] if main.get(k) is not None else float("nan")
    if g("year_t") >= 2 and g("bp_pre") > 0 and g("bp_post") > 0 and g("z") >= 2 and focus_holm:
        verdict = "支持: 東京カット後の 6 時台は 5 時台の向きに続く"
    elif g("year_t") < 1 or not focus_holm:
        verdict = "棄却"
    else:
        verdict = "未確定"
    res = {"question": "東京カット前後（5→6 時 UTC）の円ペアの順張りは Holm 後にも残るか", "settings": {"syms": SYMS, "cost_rt": COST_RT, "seal": str(SEAL.date()), "split": SPLIT, "B": args.B},
           "main": main, "holm_survivors": surv, "grid_hour_pool_bp": {int(h): f(G[G["h"] == h]["bp"].mean(), 3) for h in range(24)}, "machine_verdict": verdict,
           "multiple_comparisons": "判定は 6 時台 1 本＋72 本の Holm。ほかは記述。"}
    return res, pool


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=1000); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(); res, pool = run(a)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True); ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{QID}" if a.smoke else QID
    if not a.smoke:
        try:
            import sys; sys.path.insert(0, os.path.join(HERE, "..", "..", "tools")); from composite_gate import gate
            res["composite_gate"] = gate(pool / 1e4, "東京カット 6 時台順張り（円 3 本）")
        except Exception as e:
            res["composite_gate"] = f"失敗: {e}"
    p = os.path.join(out, f"{pre}_result_{ts}.json"); json.dump({"qid": QID, "smoke": a.smoke, "generated": ts, **res}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("wrote", os.path.relpath(p, HERE)); print("main:", res["main"]); print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
