#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q572: 金（XAUUSD）はアジア時間（上海金の 1:30〜7:30 UTC ≒ H1 の 2〜7 時の足）に持つだけで、コスト後に年単位 t ≥ 2 の正のドリフトがあるか（ロンドン時間は負か）
================================================================================

【出典】
- 計画（事前登録）: 東京時間 10 案の 3（Fable 2026-10-30 深夜・taichi「寝ている間に検証するコード」）。
- 先行: 金の日中季節性（アジア時間に上がり、ロンドン PM fix 前後で下がる）は実務で広く言われ、学術では Caminschi & Heaney (2014) J. Futures Markets「Fixing a leaky fixing」が
  ロンドン fix 前後の金の価格パターンを報告。手元: Q289（XAUUSD のロンドン fix V字）は未確定。
- 運用の決まり 2026-10-29: 合成の追加関門を記述で見る。

【仮説（測る前に固定）】
H1: XAUUSD の H1 で、UTC 2:00〜7:00 の足（5 本・始値 2:00 → 終値 6:00 の足まで）を毎営業日買い持ちすると、コスト後（往復 0.6 ドル）で年単位 t ≥ 2・前後半（<2017／≥2017）とも正。
副: ロンドン時間（8:00〜16:00 UTC）の同じ買い持ちは負（記述）。
H0: 差が 0 と区別できない、または年単位 t < 1。

【データ】`学問/金融工学/作業/FX/システムトレード/data_XAUUSD_H1_dukascopy.csv`（BID・2008-05〜）。**2024-07-01 以降は封印**。
【定義】1 日の損益 = Σ_{h=2..6} (close_h/open_h − 1)（足ごとの close-to-open ではなく 2:00 の始値→7:00 の始値＝6 時の足の終値の 1 区間の比率）− 往復コスト 0.6/価格。
年単位 t: 年ごとの日次平均 → 年の平均÷標準誤差。帰無: 日ごとの「持つ日」の列を循環シフトしても意味が無い（毎日持つ）ので、**時間帯の循環シフト**＝24 時間の窓を無作為な開始時刻（0〜23）にずらした 5 時間の買い持ちを B=23（全部）＋ bp の並べ替え（日内の 24 本の順序を日ごとに並べ替え B=1000）→ 2〜7 時の bp の z。
【測るもの】bp/日・年単位 t（全・前・後）・z、ロンドン 8〜16 時の bp（記述）、24 時間の時刻別 bp の表（記述）、合成の追加関門（記述）。
【判定（事前固定・変更禁止）】全期間 年単位 t ≥ 2 かつ 前後半とも bp > 0 かつ z ≥ 2 → 支持。全期間 t < 1 または bp ≤ 0 → 棄却。ほか未確定。
多重比較: 判定は 2〜7 時の 1 本。時刻別・ロンドンは記述。
【捨てた案の数】約 3: 窓の開始・長さの格子（記述の表で代用）、売りも入れる（ロンドンで売る＝別 ID）、銀・プラチナへの横展開（支持なら次）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】設計・コードは Fable。実行と解釈は Opus。実行者は JSON の main と machine_verdict を返す。
【実装】python3 kensho_gold_asia_hours_q572.py（1 分）／--smoke
"""
import argparse, datetime as _dt, json, math, os, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
QID = "Q572"; SEAL = pd.Timestamp("2024-07-01"); SPLIT = 2017; COST_RT = 0.6; H0, H1 = 2, 7; SEED = 20261030


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


def load(smoke, rng):
    if smoke:
        t = pd.date_range("2010-01-01", "2024-06-30", freq="h"); n = len(t); c = 1500 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
        return pd.DataFrame({"time": t, "open": np.r_[c[0], c[:-1]], "close": c})
    d = pd.read_csv(_p("検証", "学問", "金融工学", "作業", "FX", "システムトレード", "data_XAUUSD_H1_dukascopy.csv")); d["time"] = pd.to_datetime(d["time"])
    return d[d["time"] < SEAL].reset_index(drop=True)


def hour_matrix(d):
    """日×24 の足ごとの bp（close/open − 1）。無い足は NaN。"""
    d = d.copy(); d["day"] = d["time"].dt.normalize(); d["h"] = d["time"].dt.hour; d["bp"] = (d["close"] / d["open"] - 1) * 1e4
    M = d.pivot_table(index="day", columns="h", values="bp"); M = M.reindex(columns=range(24))
    px = d.pivot_table(index="day", columns="h", values="open").reindex(columns=range(24))
    return M, px


def window_bp(M, px, h0, h1, cost):
    bp = M.iloc[:, h0:h1].sum(axis=1, min_count=1)
    c = cost / px.iloc[:, h0] * 1e4
    return (bp - c).dropna()


def year_t(s):
    y = s.groupby(s.index.year).mean(); return float(y.mean() / (y.std(ddof=1) / math.sqrt(len(y)))) if len(y) > 2 else float("nan")


def run(args):
    rng = np.random.default_rng(args.seed); d = load(args.smoke, rng); M, px = hour_matrix(d)
    M = M[M.index.dayofweek < 5]; px = px.loc[M.index]
    s = window_bp(M, px, H0, H1, COST_RT)
    pre, post = s[s.index.year < SPLIT], s[s.index.year >= SPLIT]
    lon = window_bp(M, px, 8, 16, COST_RT)
    # 帰無: 日内の 24 本を日ごとに並べ替え、2〜7 の 5 本の和（コスト前）の分布
    base = M.iloc[:, H0:H1].sum(axis=1, min_count=1).dropna(); null = []
    V = M.loc[base.index].values
    for _ in range(args.B):
        P = np.take_along_axis(V, np.argsort(rng.random(V.shape), axis=1), axis=1)
        null.append(float(np.nanmean(np.nansum(P[:, H0:H1], axis=1))))
    null = np.asarray(null); z = float((base.mean() - null.mean()) / null.std(ddof=1)) if null.std(ddof=1) > 0 else float("nan")
    hours = {int(h): {"bp_mean": f(M[h].mean(), 3), "t": f(tstat(M[h].dropna()), 2)} for h in range(24)}
    main = {"bp_per_day": f(s.mean(), 3), "year_t": f(year_t(s), 2), "bp_pre": f(pre.mean(), 3), "bp_post": f(post.mean(), 3), "year_t_pre": f(year_t(pre), 2), "year_t_post": f(year_t(post), 2),
            "z": f(z, 2), "null_mean_bp": f(null.mean(), 3), "n_days": int(len(s)), "london_8_16_bp": f(lon.mean(), 3), "london_year_t": f(year_t(lon), 2),
            "sharpe_ann": f(s.mean() / s.std(ddof=1) * math.sqrt(252), 2)}
    g = lambda k: main[k] if main.get(k) is not None else float("nan")
    if g("year_t") >= 2 and g("bp_pre") > 0 and g("bp_post") > 0 and g("z") >= 2:
        verdict = "支持: 金はアジア時間の買い持ちでコスト後に正のドリフト"
    elif g("year_t") < 1 or g("bp_per_day") <= 0:
        verdict = "棄却"
    else:
        verdict = "未確定"
    res = {"question": "XAUUSD は 2〜7 時 UTC の買い持ちでコスト後に年単位 t≥2 か", "settings": {"window_utc": [H0, H1], "cost_rt": COST_RT, "seal": str(SEAL.date()), "split": SPLIT, "B": args.B},
           "main": main, "by_hour": hours, "by_year_bp": {int(y): f(v, 2) for y, v in s.groupby(s.index.year).mean().items()}, "machine_verdict": verdict,
           "multiple_comparisons": "判定は 2〜7 時の 1 本。時刻別・ロンドンは記述。"}
    return res, s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=1000); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(); res, s = run(a)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True); ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{QID}" if a.smoke else QID
    if not a.smoke:
        try:
            import sys; sys.path.insert(0, os.path.join(HERE, "..", "..", "tools")); from composite_gate import gate
            res["composite_gate"] = gate(s / 1e4, "金アジア時間 2-7UTC 買い持ち")
        except Exception as e:
            res["composite_gate"] = f"失敗: {e}"
    p = os.path.join(out, f"{pre}_result_{ts}.json"); json.dump({"qid": QID, "smoke": a.smoke, "generated": ts, **res}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    s.rename("bp").to_csv(os.path.join(out, f"{pre}_daily_{ts}.csv"))
    print("wrote", os.path.relpath(p, HERE)); print("main:", res["main"]); print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
