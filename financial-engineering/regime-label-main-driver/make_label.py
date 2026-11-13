#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_label.py — 局面判定ラベル（世界共通の 1 本）を作る。定義は 事前登録_検証1.md §1 のまま（2026-11-13 固定）。

何の主役か: S21 の 19 銘柄（FX 14・指数 4・金 1）。要因 6 つ: EQ 株・SEMI 半導体・RATE 米金利・USD ドル・JPY 円・OIL 原油。
  1. R²(i,k,t): 直近 W=60 営業日の相関の 2 乗（有効 45 日未満は欠損）
  2. A(k,t): 対象の R² の単純平均（15 本未満は欠損）。FX・指数・金の別の平均も残す
  3. P(k,t): A がその要因自身の過去（〜t）の中で下から何 % か（過去 500 営業日未満は欠損）
  4. M(t): P が最大の要因（同点は A が大きい方）
  5. L(t): M が N=5 営業日続けて同じ別の要因になったら、その 5 日目に切り替える（これがラベル）
すべてその日までのデータだけで計算する。結合するときは L(d−1) を当てる。

使い方:  <venv_forward の python> make_label.py            # results/局面ラベル_検証1版.csv と _meta.json
         ... make_label.py --smoke                          # 合成データで経路だけ確かめる（results/_smoke/。判定に使わない）
封印: ラベルは 2024-07 以降の価格も読む（対象と要因の価格だけ。戦略の損益は読まない）。taichi 承認 2026-11-13（事前登録 §4-1）。
"""
import argparse, bisect, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
from fe_core import data as FD
from fe_core._paths import _p

FX14 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"]
IDX4 = ["US500", "USTECH", "GER40", "JPN225"]
GOLD = ["XAUUSD"]
TARGETS = FX14 + IDX4 + GOLD
GROUPS = {"FX": FX14, "IDX": IDX4, "GOLD": GOLD}
USD7 = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "NZDUSD": -1, "USDJPY": 1, "USDCHF": 1, "USDCAD": 1}   # ドル高方向
JPY6 = ["EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"]                                        # 円安方向
FACTORS = ["EQ", "SEMI", "RATE", "USD", "JPY", "OIL"]
PARAMS = {"W": 60, "MINV": 45, "N": 5, "HIST": 500, "MINT": 15}      # 事前登録の固定値
SKIP = {("US500", "EQ"), ("US500", "SEMI")}   # US500×EQ は自分自身。US500×SEMI は作り方から常に 0（情報が無い）ので平均に入れない

D1DIR = _p("検証", "_データ", "raw", "D1")
MACRO = _p("検証", "_データ", "raw", "macro")
H1DIRS = [_p("作業層", "大容量", "market_data", "H1"), _p("作業層", "大容量", "market_data_forward", "H1")]


# ----------------------------------------------------------------------------- 読み込み
def _open_csv(path):
    df = FD._read(path)
    df = FD._seal(df, end=None)   # 封印を開ける: 局面ラベルは対象と要因の価格だけを読む（戦略の損益は読まない）。taichi 承認 2026-11-13・事前登録 §4-1
    df = df[df["high"] != df["low"]]
    return pd.Series(df["close"].values, index=pd.DatetimeIndex(df["time"]).normalize(), dtype=float)


def _h1_to_d1(path):
    h = pd.read_parquet(path, columns=["time", "high", "low", "close"])   # 封印を開ける: 同上（日足の足りない月を時間足から補う）
    t = pd.to_datetime(h["time"])
    if t.dt.tz is not None: t = t.dt.tz_convert("UTC").dt.tz_localize(None)
    h = h.assign(d=t.dt.normalize().values, t=t.values).sort_values("t")
    g = h.groupby("d")
    d = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last()})
    d = d[(d["high"] != d["low"]) & (d.index.dayofweek != 6)]            # 値動きの無い日と日曜の短い足は落とす（fetch_dukascopy_d1.py と同じ）
    return d["close"].astype(float)


def load_close(sym, report):
    """日足の終値。正本は _データ/raw/D1。届いていない日だけ、macro/tail_*.csv → 時間足（検証用 → フォワード用）の順で足す。"""
    parts = [("D1", _open_csv(os.path.join(D1DIR, f"data_{sym}_D1_fromH1.csv")))]
    tp = os.path.join(MACRO, f"tail_{sym}_D1.csv")
    if os.path.exists(tp): parts.append(("tail", _open_csv(tp)))
    for i, hd in enumerate(H1DIRS):
        hp = os.path.join(hd, f"{sym}.parquet")
        if os.path.exists(hp): parts.append((f"H1_{i}", _h1_to_d1(hp)))
    out = parts[0][1]; rep = {"D1": [str(out.index[0].date()), str(out.index[-1].date()), int(len(out))]}
    for name, s in parts[1:]:
        both = out.index.intersection(s.index)
        if len(both):   # 重なる日で終値が一致するか（つなぎ目の点検）
            rel = (s.reindex(both) / out.reindex(both) - 1).abs()
            rep[f"{name}_重なり"] = {"日数": int(len(both)), "最大の差": float(rel.max()), "差1e-4超の日数": int((rel > 1e-4).sum())}
        add = s[~s.index.isin(out.index)]
        if len(add):
            rep[f"{name}_追加"] = [str(add.index[0].date()), str(add.index[-1].date()), int(len(add))]
            out = pd.concat([out, add]).sort_index()
    report[sym] = rep
    return out


def load_macro(name):
    df = pd.read_csv(os.path.join(MACRO, f"{name}.csv"))                # 封印を開ける: 同上（要因の系列）
    return pd.Series(df["close"].astype(float).values, index=pd.DatetimeIndex(pd.to_datetime(df["date"])).normalize())


def load_all(smoke=False):
    """返り値: (cal, R[対象の対数リターン], X[要因の元の系列], report)。リターンは暦（EURUSD の平日）の隣り合う 2 日に終値があるときだけ。"""
    report = {}
    if smoke:
        rng = np.random.default_rng(7); cal = pd.bdate_range("2010-01-04", "2017-12-29")
        n = len(cal); com = rng.normal(0, 0.006, n)
        R = pd.DataFrame({s: 0.5 * com + rng.normal(0, 0.006, n) for s in TARGETS + ["WTI"]}, index=cal)
        X = {"SOX": pd.Series(0.9 * R["US500"].values + rng.normal(0, 0.01, n), index=cal), "RATE": pd.Series(rng.normal(0, 0.05, n), index=cal)}
        return cal, R, X, {"smoke": True}
    closes = {s: load_close(s, report) for s in TARGETS + ["WTI"]}
    e = closes["EURUSD"]; cal = e.index[e.index.dayofweek < 5]
    R = pd.DataFrame({s: np.log(c.reindex(cal)).diff() for s, c in closes.items()}, index=cal)
    sox = load_macro("SOX"); ust = load_macro("UST10Y")
    X = {"SOX": np.log(sox.reindex(cal)).diff(), "RATE": ust.reindex(cal).diff()}
    for n_, s in (("SOX", sox), ("UST10Y", ust), ("WTI", closes["WTI"])):
        report.setdefault("_最後の日", {})[n_] = str(s.index[-1].date())
    report["_暦"] = [str(cal[0].date()), str(cal[-1].date()), int(len(cal))]
    return cal, R, X, report


# ----------------------------------------------------------------------------- 計算
def _rs(x, W):
    c = np.cumsum(np.insert(x, 0, 0.0)); out = np.full(len(x), np.nan)
    if len(x) >= W: out[W - 1:] = c[W:] - c[:-W]
    return out


def roll_corr(a, b, W, MINV):
    """t を終わりとする W 行の窓の相関係数。a・b のどちらかが欠損の行は使わない。有効が MINV 未満なら欠損。"""
    m = np.isfinite(a) & np.isfinite(b); A = np.where(m, a, 0.0); B = np.where(m, b, 0.0)
    n = _rs(m.astype(float), W); sa, sb = _rs(A, W), _rs(B, W); saa, sbb, sab = _rs(A * A, W), _rs(B * B, W), _rs(A * B, W)
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sab - sa * sb / n; va = saa - sa * sa / n; vb = sbb - sb * sb / n
        r = cov / np.sqrt(va * vb)
    r[~(n >= MINV) | ~(va > 1e-18) | ~(vb > 1e-18)] = np.nan
    return np.clip(r, -1, 1)


def basket(R, comps, excl=None, need=1):
    cols = [c for c in comps if c != excl]
    sign = np.array([comps[c] if isinstance(comps, dict) else 1.0 for c in cols])
    M = R[cols].values * sign; k = np.isfinite(M).sum(axis=1)
    with np.errstate(invalid="ignore"):
        out = np.nansum(M, axis=1) / np.where(k > 0, k, np.nan)
    out[k < need] = np.nan
    return out


def factor_for(R, X, k, target):
    """対象 target に当てる要因 k の系列（自分自身が部品のときは抜いて作る）。SEMI は SOX の元のリターン（残差は r2() の中で取る）。"""
    if k == "EQ": return R["US500"].values
    if k == "SEMI": return X["SOX"].values
    if k == "RATE": return X["RATE"].values
    if k == "OIL": return R["WTI"].values
    if k == "USD": return basket(R, USD7, excl=target, need=5)
    if k == "JPY": return basket(R, JPY6, excl=target, need=4)
    raise KeyError(k)


def r2(R, X, target, k, W, MINV):
    y = R[target].values; x = factor_for(R, X, k, target)
    if k != "SEMI":
        return roll_corr(y, x, W, MINV) ** 2
    # SEMI: 同じ窓の中で SOX を US500 に回帰した残りで説明できる割合 ＝ 半偏相関の 2 乗
    e = R["US500"].values; m = np.isfinite(y) & np.isfinite(x) & np.isfinite(e)
    y, x, e = (np.where(m, v, np.nan) for v in (y, x, e))
    rys, rye, rse = roll_corr(y, x, W, MINV), roll_corr(y, e, W, MINV), roll_corr(x, e, W, MINV)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = (rys - rye * rse) ** 2 / (1 - rse ** 2)
    out[~(1 - rse ** 2 > 1e-9)] = np.nan
    return out


def expanding_pct(a, HIST):
    out = np.full(len(a), np.nan); hist = []
    for t, v in enumerate(a):
        if not np.isfinite(v): continue
        bisect.insort(hist, v)
        if len(hist) >= HIST: out[t] = bisect.bisect_right(hist, v) / len(hist)
    return out


def confirm(M, N):
    """M（生の主役）→ L（確定した主役）と切り替わりの印。"""
    L = [None] * len(M); sw = np.zeros(len(M), dtype=int); cur = cand = None; run = 0
    for t, m in enumerate(M):
        if m is None: L[t] = cur; continue
        if cur is None: cur = m
        elif m == cur: cand, run = None, 0
        else:
            if m == cand: run += 1
            else: cand, run = m, 1
            if run >= N: cur, cand, run = m, None, 0; sw[t] = 1
        L[t] = cur
    return L, sw


def build(cal, R, X, W=60, MINV=45, N=5, HIST=500, MINT=15, mode="pct"):
    """ラベルの表を作る。mode="pct" が事前登録の定義、"raw" は 3（普段との比較）を抜いた比べ用の変種。"""
    T = len(cal); out = pd.DataFrame(index=cal)
    A = {};
    for k in FACTORS:
        r2s = {t: r2(R, X, t, k, W, MINV) for t in TARGETS if (t, k) not in SKIP}
        M_ = np.column_stack(list(r2s.values())); cnt = np.isfinite(M_).sum(axis=1)
        with np.errstate(invalid="ignore"):
            a = np.nansum(M_, axis=1) / np.where(cnt > 0, cnt, np.nan)
        a[cnt < MINT] = np.nan; A[k] = a; out[f"A_{k}"] = a
        for g, members in GROUPS.items():
            G = np.column_stack([r2s[t] for t in members if t in r2s]) if any(t in r2s for t in members) else np.full((T, 1), np.nan)
            c = np.isfinite(G).sum(axis=1)
            with np.errstate(invalid="ignore"):
                out[f"A_{k}_{g}"] = np.nansum(G, axis=1) / np.where(c > 0, c, np.nan)
    S = {k: (expanding_pct(A[k], HIST) if mode == "pct" else A[k].copy()) for k in FACTORS}
    for k in FACTORS: out[f"P_{k}"] = S[k]
    Sm = np.column_stack([S[k] for k in FACTORS]); Am = np.column_stack([A[k] for k in FACTORS])
    M = [None] * T
    for t in range(T):
        if not np.all(np.isfinite(Sm[t])): continue
        best = np.flatnonzero(Sm[t] == Sm[t].max())
        M[t] = FACTORS[best[np.argmax(Am[t][best])]]
    L, sw = confirm(M, N)
    out["M"] = M; out["L"] = L; out["切り替わり"] = sw
    # 向き（記述）: 要因の直近 20 営業日のリターンの合計の符号。SEMI は SOX の元のリターン
    dirs = {"EQ": R["US500"].values, "SEMI": X["SOX"].values, "RATE": X["RATE"].values, "USD": basket(R, USD7, need=5), "JPY": basket(R, JPY6, need=4), "OIL": R["WTI"].values}
    for k, v in dirs.items():
        s = pd.Series(v, index=cal).rolling(20, min_periods=10).sum()
        out[f"向き_{k}"] = np.sign(s).astype("Int64")
    # 暫定: 要因の元の系列が直近 3 営業日に 1 つも無い日（取得が届いていない）
    stale = np.zeros(T, dtype=int)
    for v in (R["US500"].values, X["SOX"].values, X["RATE"].values, R["WTI"].values, R["EURUSD"].values):
        last = pd.Series(np.where(np.isfinite(v), np.arange(T), np.nan)).ffill().values
        stale |= (np.arange(T) - np.nan_to_num(last, nan=-10**6) > 3).astype(int)
    out["暫定"] = stale
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
    cal, R, X, report = load_all(a.smoke)
    lab = build(cal, R, X, **PARAMS)
    od = os.path.join(HERE, "results", "_smoke") if a.smoke else os.path.join(HERE, "results"); os.makedirs(od, exist_ok=True)
    cols = ["L", "M", "切り替わり", "暫定"] + [f"P_{k}" for k in FACTORS] + [f"A_{k}" for k in FACTORS] + \
           [f"A_{k}_{g}" for k in FACTORS for g in GROUPS] + [f"向き_{k}" for k in FACTORS]
    keep = lab[lab["L"].notna()][cols].copy(); keep.index.name = "date"
    p = os.path.join(od, "局面ラベル_検証1版.csv"); keep.round(4).to_csv(p, encoding="utf-8")
    meta = {"定義": "事前登録_検証1.md §1", "params": PARAMS, "factors": FACTORS, "targets": TARGETS, "skip": sorted(map(list, SKIP)),
            "半導体の系列": "SOX（Nasdaq 公式 API）", "金利の系列": "米財務省の 10 年利回り（DGS10 と同じ数値の発行元。FRED は 2026-11-13 に応答なし）",
            "ラベルの期間": [str(keep.index[0].date()), str(keep.index[-1].date()), int(len(keep))], "data": report}
    json.dump(meta, open(os.path.join(od, "局面ラベル_検証1版_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"書いた: {p}  {keep.index[0].date()}〜{keep.index[-1].date()}  {len(keep)} 日")


if __name__ == "__main__":
    main()
