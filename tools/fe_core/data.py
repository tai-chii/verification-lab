# -*- coding: utf-8 -*-
"""データ読み込み。雛形で一致していた実装（load_* は数値を変えていない）に、欠損の点検（check_gaps・health）を足した。
失敗パターン集 2026-09-30（H1 で 352 か月欠け）・Q108（M15 で再発）の再発防止: 読んだ後に必ず点検できるようにする。"""
import os

import numpy as np
import pandas as pd

from ._paths import DATA_DIR, SEED

# ----------------------------------------------------------------------------- 読み込み（雛形どおり）
def _read(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def load_d1(sym, smoke=False, rng=None):
    """UTC 日足（D1_fromH1）。値動きのない足（high==low）は除く。列: time, open, high, low, close, ret, year"""
    if smoke:
        df = _smoke_ohlc(sym, rng, n=2600, freq="D", start="2015-01-01")
    else:
        df = _read(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    return df


def load_csv(name, smoke=False, rng=None, freq="h", n=20000, start="2015-01-01"):
    """任意の data_<name>.csv（H1/H4/M15/yahoo/ask）。"""
    if smoke:
        return _smoke_ohlc(name, rng, n=n, freq=freq, start=start)
    return _read(os.path.join(DATA_DIR, f"data_{name}.csv"))


def load_h1(sym, smoke=False, rng=None, n=60000, start="2015-01-01"):
    """UTC 1時間足（H1_dukascopy）。値動きのない足は除く。列: time, open, high, low, close, volume, ret, year, hour, dow"""
    df = load_csv(f"{sym}_H1_dukascopy", smoke, rng, freq="h", n=n, start=start)
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    return df


def h1_to_d1(h1, cutoff_hour=0):
    """H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。"""
    t = h1["time"] - pd.Timedelta(hours=cutoff_hour)
    key = t.dt.floor("D")
    g = h1.groupby(key)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum() if "volume" in h1 else g["close"].size(), "nbars": g["close"].size()})
    d.index.name = "time"; d = d.reset_index()
    d = d[(d["high"] != d["low"]) & (d["nbars"] >= 6)].reset_index(drop=True)
    d["ret"] = d["close"].pct_change(); d["year"] = d["time"].dt.year
    return d


def _smoke_ohlc(sym, rng, n, freq, start):
    """合成データ（GBM）。判定には使わない。"""
    rng = rng or np.random.default_rng(SEED)
    t = pd.date_range(start, periods=n, freq=freq)
    r = rng.normal(0.0001, 0.006, n)
    c = 100.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n)))
    v = np.abs(rng.lognormal(8, 0.5, n))
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v})


def exists_sym(sym, kind="D1_fromH1"):
    return os.path.exists(os.path.join(DATA_DIR, f"data_{sym}_{kind}.csv"))


def syms_available(syms, kind="D1_fromH1", smoke=False):
    if smoke:
        return list(syms), []
    ok = [s for s in syms if exists_sym(s, kind)]
    return ok, [s for s in syms if s not in ok]


# ----------------------------------------------------------------------------- 欠損の点検（新規・2026-10-13）
_EXPECTED_PER_WEEK = {"H1": 24 * 5, "M15": 24 * 4 * 5, "H4": 6 * 5, "D1": 5}


def check_gaps(df, bar="H1", min_ratio=0.5):
    """月ごとの本数を数え、期待本数の min_ratio 未満の月を「欠け」として返す。
    返り値: {"months": 総月数, "missing_months": 欠けた月の数, "missing": ["2019-03", ...], "worst_ratio": 最も少ない月の比}
    期待本数は週あたりの本数 × 4.3。先頭月・末尾月は部分月なので除く。"""
    if df is None or len(df) == 0 or "time" not in df:
        return {"months": 0, "missing_months": 0, "missing": [], "worst_ratio": float("nan")}
    per_week = _EXPECTED_PER_WEEK.get(bar.upper(), None)
    t = pd.to_datetime(df["time"])
    ym = t.dt.to_period("M")
    cnt = ym.value_counts().sort_index()
    if len(cnt) > 2:
        cnt = cnt.iloc[1:-1]
    if per_week is None or len(cnt) == 0:
        return {"months": int(len(cnt)), "missing_months": 0, "missing": [], "worst_ratio": float("nan")}
    expected = per_week * 4.3
    ratio = cnt / expected
    # 連続した月の抜け（行が1本もない月）も数える
    full = pd.period_range(cnt.index.min(), cnt.index.max(), freq="M")
    absent = [str(p) for p in full if p not in cnt.index]
    low = [str(p) for p, r in ratio.items() if r < min_ratio]
    missing = sorted(set(absent) | set(low))
    return {"months": int(len(full)), "missing_months": len(missing), "missing": missing,
            "worst_ratio": float(ratio.min()) if len(ratio) else float("nan")}


def health(syms, kind="H1_dukascopy", bar=None, min_ratio=0.5):
    """銘柄ごとに 成功／データなし／失敗 を区別して返す。結果 JSON の "data_health" にそのまま入れる想定。
    kind から bar を推定（H1_dukascopy→H1、D1_fromH1→D1、M15_...→M15）。"""
    if bar is None:
        bar = kind.split("_")[0]
    out = {"ok": [], "no_data": [], "failed": {}, "gaps": {}}
    for s in syms:
        p = os.path.join(DATA_DIR, f"data_{s}_{kind}.csv")
        if not os.path.exists(p):
            out["no_data"].append(s); continue
        try:
            g = check_gaps(_read(p), bar=bar, min_ratio=min_ratio)
        except Exception as e:  # 読めない＝失敗。黙って空にしない
            out["failed"][s] = repr(e); continue
        out["ok"].append(s)
        if g["missing_months"]:
            out["gaps"][s] = g
    out["n_gap_syms"] = len(out["gaps"])
    return out
