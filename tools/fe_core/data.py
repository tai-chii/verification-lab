# -*- coding: utf-8 -*-
"""データ読み込み。雛形で一致していた実装（load_* は数値を変えていない）に、欠損の点検（check_gaps・health）を足した。
失敗パターン集 2026-09-30（H1 で 352 か月欠け）・Q108（M15 で再発）の再発防止: 読んだ後に必ず点検できるようにする。"""
import os

import numpy as np
import pandas as pd

from ._paths import DATA_DIR, SEED

# ----------------------------------------------------------------------------- 読み込み（雛形どおり）
def _read(path):
    """CSV を読み、time を datetime にして並べ替え・重複除去する（生の読み込み）。
    使う場面: load_* の中。直接使うのは data_*.csv 以外の表を読むときだけ
    入力: path: CSV のパス（time 列が必要）
    返り値: DataFrame（time 昇順・重複なし）
    禁止: 失敗を空の DataFrame で握りつぶさない（例外はそのまま上げる）
    段階: 読み込み
    """
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def load_d1(sym, smoke=False, rng=None):
    """UTC 日足（data_<sym>_D1_fromH1.csv）。値動きのない足（high==low）は除く。
    使う場面: 日足の検証の読み込み。--smoke のときは合成データ
    入力: sym: 銘柄、smoke: 合成データにするか、rng: smoke 用の Generator
    返り値: DataFrame（time, open, high, low, close, ret, year）。ret は比（bp ではない）
    禁止: ret の単位を変えた列を同じ名前で作らない（旧 q284・q286 で bp 版があり事故の種）
    段階: 読み込み
    """
    if smoke:
        df = _smoke_ohlc(sym, rng, n=2600, freq="D", start="2015-01-01")
    else:
        df = _read(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    return df


def load_csv(name, smoke=False, rng=None, freq="h", n=20000, start="2015-01-01"):
    """任意の data_<name>.csv（H1/H4/M15/yahoo/ask など）を読む。
    使う場面: load_d1・load_h1 に無い足種や別ソース
    入力: name: data_ の後ろの名前、smoke/rng/freq/n/start: 合成データの設定
    返り値: DataFrame（生の列。ret・year は付かない）
    禁止: 同じ銘柄を別ソースで混ぜて 1 本の系列にしない
    段階: 読み込み
    """
    if smoke:
        return _smoke_ohlc(name, rng, n=n, freq=freq, start=start)
    return _read(os.path.join(DATA_DIR, f"data_{name}.csv"))


def load_h1(sym, smoke=False, rng=None, n=60000, start="2015-01-01"):
    """UTC 1 時間足（data_<sym>_H1_dukascopy.csv）。値動きのない足は除く。
    使う場面: 時間帯・イベント研究・H1 からの日足作成（h1_to_d1）
    入力: sym、smoke、rng、n/start: 合成データの長さと開始
    返り値: DataFrame（time, open, high, low, close, volume, ret, year, hour, dow）
    禁止: 読んだ後に check_gaps／health で欠損を点検せずに判定しない
    段階: 読み込み
    """
    df = load_csv(f"{sym}_H1_dukascopy", smoke, rng, freq="h", n=n, start=start)
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    return df


def h1_to_d1(h1, cutoff_hour=0):
    """H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。
    使う場面: 日の区切り（NY 17 時など）を変えた日足が要るとき
    入力: h1: load_h1 の返り値、cutoff_hour: 区切りの時刻（UTC）
    返り値: DataFrame（time, open, high, low, close, volume, nbars, ret, year）。本数 6 未満の日は除く
    禁止: cutoff を結果を見てから変えない（Q140 系の「区切り依存」を再現する）
    段階: 読み込み
    """
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
    """合成データ（GBM）。経路の確認用で、判定には使わない。
    使う場面: --smoke。load_* が内部で呼ぶ
    入力: sym（未使用）、rng、n: 本数、freq: pandas の頻度、start: 開始日
    返り値: DataFrame（time, open, high, low, close, volume）
    禁止: smoke の結果を結果 JSON の判定に使わない（smoke_ 接頭辞で分ける）
    段階: 読み込み
    """
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
    """data_<sym>_<kind>.csv があるか。
    使う場面: 銘柄ループの前。無い銘柄は missing に記録する
    入力: sym、kind: "D1_fromH1" か "H1_dukascopy" など
    返り値: bool
    禁止: 無い銘柄を黙って飛ばさない（JSON の missing に書く）
    段階: 読み込み
    """
    return os.path.exists(os.path.join(DATA_DIR, f"data_{sym}_{kind}.csv"))


def syms_available(syms, kind="D1_fromH1", smoke=False):
    """銘柄リストを「ある／ない」に分ける。
    使う場面: run の最初。ok だけを回し、missing を JSON に入れる
    入力: syms、kind、smoke（True なら全部ある扱い）
    返り値: (ok, missing)
    禁止: missing を空だと仮定しない
    段階: 読み込み
    """
    if smoke:
        return list(syms), []
    ok = [s for s in syms if exists_sym(s, kind)]
    return ok, [s for s in syms if s not in ok]


# ----------------------------------------------------------------------------- 欠損の点検（新規・2026-10-13）
_EXPECTED_PER_WEEK = {"H1": 24 * 5, "M15": 24 * 4 * 5, "H4": 6 * 5, "D1": 5}


def check_gaps(df, bar="H1", min_ratio=0.5):
    """月ごとの本数を数え、期待本数の min_ratio 未満の月と行の無い月を「欠け」として返す。
    使う場面: 読み込みの直後。欠けが 1 月でもあれば結果 JSON に残し、欠けた期間を除いた結果も並べる
    入力: df: time 列を持つ DataFrame、bar: "H1"/"M15"/"H4"/"D1"、min_ratio: 欠けと見なす比
    返り値: {"months", "missing_months", "missing": ["2019-03", ...], "worst_ratio"}
    禁止: 欠けを「データなし」と同じに扱わない（2026-09-30 の事故）
    段階: 読み込み
    """
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
    """銘柄ごとに 成功／データなし／失敗 を区別し、欠けのある銘柄の check_gaps をまとめる。
    使う場面: run の最初に 1 回。返り値をそのまま結果 JSON の "data_health" に入れる
    入力: syms、kind、bar（省略で kind から推定）、min_ratio
    返り値: {"ok", "no_data", "failed": {sym: 例外}, "gaps": {sym: check_gaps}, "n_gap_syms"}
    禁止: failed が 1 件でもあるのに結果を「確定」にしない
    段階: 読み込み
    """
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
