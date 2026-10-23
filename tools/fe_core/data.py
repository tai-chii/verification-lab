# -*- coding: utf-8 -*-
"""データ読み込み。雛形で一致していた実装（load_* の time/open/high/low/close/ret/year の数値は変えていない）に、
欠損の点検（check_gaps・health）と空白の印（dt_prev_h・gap 列）を足した。
失敗パターン集 2026-09-30（H1 で 352 か月欠け）・Q108（M15 で平日 17% の欠け）・Q191（週末の埋め足）・Q209（空白をまたぐ +1379bp）の再発防止。
レビュー（2026-10-13・Opus）の H2・H3・M3・M6 を反映。"""
import os
import warnings

import numpy as np
import pandas as pd

from ._paths import DATA_DIR, SEED, data_path

# 足種ごとの「これより長い空白は欠け」の目安 [時間]。週末（約 48h）は空白と数えない
_GAP_HOURS = {"H1": 96, "M15": 96, "H4": 96, "D1": 24 * 7}  # 週末＋祝日（年末年始は 73h）は空白と数えない
_EXPECTED_PER_WEEK = {"H1": 24 * 5, "M15": 24 * 4 * 5, "H4": 6 * 5, "D1": 5}


def _bar_of(kind):
    return kind.split("_")[0].upper()


def _mark_gaps(df, bar):
    """dt_prev_h（前の行との時間差 [h]）と gap（空白をまたいだ行＝ret が複数本分）を付ける。既存の列は変えない。"""
    t = pd.to_datetime(df["time"])
    dt = t.diff().dt.total_seconds().values / 3600.0
    df["dt_prev_h"] = dt
    df["gap"] = np.isfinite(dt) & (dt > _GAP_HOURS.get(bar, 72))
    return df


# ----------------------------------------------------------------------------- 読み込み（雛形どおり＋列の追加）
def _read(path):
    """CSV を読み、time を datetime にして並べ替え・重複除去する（生の読み込み）。
    使う場面: load_* の中。直接使うのは data_*.csv 以外の表を読むときだけ
    入力: path: CSV のパス（time 列が必要）
    返り値: DataFrame（time 昇順・重複なし・同時刻は最初の行を残す）。df.attrs["n_dup"] に除いた重複の数
    禁止: 失敗を空の DataFrame で握りつぶさない（例外はそのまま上げる）
    段階: 読み込み
    """
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    if getattr(df["time"].dt, "tz", None) is not None:
        df["time"] = df["time"].dt.tz_convert("UTC").dt.tz_localize(None)
    n0 = len(df)
    df = df.sort_values("time", kind="stable").drop_duplicates("time", keep="first").reset_index(drop=True)
    df.attrs["n_dup"] = int(n0 - len(df))
    if df.attrs["n_dup"]:
        warnings.warn(f"{os.path.basename(path)}: 同時刻の重複 {df.attrs['n_dup']} 行を除いた（最初の行を残す）")
    return df


def load_d1(sym, smoke=False, rng=None):
    """UTC 日足（data_<sym>_D1_fromH1.csv）。値動きのない足（high==low）は除く。
    使う場面: 日足の検証の読み込み。--smoke のときは合成データ
    入力: sym: 銘柄、smoke: 合成データにするか、rng: smoke 用の Generator
    返り値: DataFrame（time, open, high, low, close, volume, ret, year, dt_prev_h, gap）。ret は比（bp ではない）。gap=True の行の ret は空白をまたいだ複数日分
    禁止: ret の単位を変えた列を同じ名前で作らない（旧 q284・q286 で bp 版があり事故の種）。gap 行を除くか残すかを結果に書く
    段階: 読み込み
    """
    if smoke:
        df = _smoke_ohlc(sym, rng, n=2600, freq="D", start="2015-01-01")
    else:
        df = _read(data_path(sym, "D1_fromH1"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    return _mark_gaps(df, "D1")


def load_csv(name, smoke=False, rng=None, freq="h", n=20000, start="2015-01-01"):
    """任意の data_<name>.csv（H1/H4/M15/yahoo/ask など）を読む。
    使う場面: load_d1・load_h1 に無い足種や別ソース
    入力: name: data_ の後ろの名前、smoke/rng/freq/n/start: 合成データの設定
    返り値: DataFrame（生の列。ret・year・gap は付かない）
    禁止: 同じ銘柄を別ソースで混ぜて 1 本の系列にしない
    段階: 読み込み
    """
    if smoke:
        return _smoke_ohlc(name, rng, n=n, freq=freq, start=start)
    return _read(os.path.join(DATA_DIR, f"data_{name}.csv"))


def load_h1(sym, smoke=False, rng=None, n=60000, start="2015-01-01"):
    """UTC 1 時間足（data_<sym>_H1_dukascopy.csv）。値動きのない足は除く（週末の埋め足もこれで落ちる）。
    使う場面: 時間帯・イベント研究・H1 からの日足作成（h1_to_d1）
    入力: sym、smoke、rng、n/start: 合成データの長さと開始
    返り値: DataFrame（time, open, high, low, close, volume, ret, year, hour, dow, dt_prev_h, gap）。time は足の開始時刻
    禁止: 読んだ後に health／check_gaps で欠損を点検せずに判定しない。gap=True の行の ret を時刻ラベルの損益に数えない
    段階: 読み込み
    """
    df = load_csv(f"{sym}_H1_dukascopy", smoke, rng, freq="h", n=n, start=start)
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    return _mark_gaps(df, "H1")


def h1_to_d1(h1, cutoff_hour=0):
    """H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。
    使う場面: 日の区切り（NY 17 時など）を変えた日足が要るとき
    入力: h1: load_h1 の返り値、cutoff_hour: 区切りの時刻（UTC 固定。夏時間は追わない）
    返り値: DataFrame（time, close_time, open, high, low, close, volume, nbars, ret, year, dt_prev_h, gap）。本数 6 未満の日は除く
    禁止: cutoff を結果を見てから変えない。別の表（load_d1 など）と結合するときは time ではなく close_time で合わせる（time で合わせると最大 cutoff 時間分の先読みになる）
    段階: 読み込み
    """
    t = h1["time"] - pd.Timedelta(hours=cutoff_hour)
    key = t.dt.floor("D")
    g = h1.groupby(key)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum() if "volume" in h1 else g["close"].size(), "nbars": g["close"].size(),
                      "close_time": g["time"].last() + pd.Timedelta(hours=1)})
    d.index.name = "time"; d = d.reset_index()
    d = d[(d["high"] != d["low"]) & (d["nbars"] >= 6)].reset_index(drop=True)
    d["ret"] = d["close"].pct_change(); d["year"] = d["time"].dt.year
    return _mark_gaps(d, "D1")


def _smoke_ohlc(sym, rng, n, freq, start):
    """合成データ（GBM）。経路の確認用で、判定には使わない。
    使う場面: --smoke。load_* が内部で呼ぶ
    入力: sym（未使用）、rng、n: 本数、freq: pandas の頻度、start: 開始日
    返り値: DataFrame（time, open, high, low, close, volume）
    禁止: smoke の結果を結果 JSON の判定に使わない（smoke_ 接頭辞で分ける）。rng を渡さないと全銘柄が同じ系列になる
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
    return os.path.exists(data_path(sym, kind))


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


# ----------------------------------------------------------------------------- 欠損の点検（2026-10-13・レビュー H2 で作り直し）
def check_gaps(df, bar="H1", min_ratio=0.8, gap_hours=None):
    """欠損の点検。月ごとの本数の不足と、暦の上の長い空白の両方を見る。load_* の返り値（high==low を除いた後）に使う。
    使う場面: 読み込みの直後。欠けが 1 件でもあれば結果 JSON に残し、欠けた期間を除いた結果も並べる
    入力: df: time 列を持つ DataFrame（load_* の返り値）、bar: "H1"/"M15"/"H4"/"D1"、min_ratio: 本数がこの比を下回る月を欠けとする、gap_hours: これより長い空白を欠けとする [h]（省略で足種の既定: H1/M15/H4=96、D1=168）
    返り値: {"months", "missing_months", "missing": ["2019-03", ...], "worst_ratio", "n_gaps", "max_gap_h", "gaps": [{"from","to","hours"}...上位5], "first", "last"}
    禁止: 欠けを「データなし」と同じに扱わない（2026-09-30 の事故）。生データ（埋め足つき）で点検しない（Q191: 週末の埋め足で比が 1.0 に見える）
    段階: 読み込み
    """
    empty = {"months": 0, "missing_months": 0, "missing": [], "worst_ratio": float("nan"), "n_gaps": 0, "max_gap_h": float("nan"), "gaps": [], "first": None, "last": None}
    if df is None or len(df) == 0 or "time" not in df:
        return empty
    bar = bar.upper()
    t = pd.to_datetime(df["time"]).sort_values().reset_index(drop=True)
    # 1) 暦の上の空白（週末 48h は含めない既定）
    gh = gap_hours if gap_hours is not None else _GAP_HOURS.get(bar, 72)
    dt = t.diff().dt.total_seconds().values / 3600.0
    idx = np.where(np.isfinite(dt) & (dt > gh))[0]
    gaps = sorted(({"from": str(t.iloc[i - 1]), "to": str(t.iloc[i]), "hours": float(dt[i])} for i in idx), key=lambda g: -g["hours"])
    # 2) 月ごとの本数（範囲は生の min/max から。先頭・末尾の部分月は比の判定からだけ外す）
    per_week = _EXPECTED_PER_WEEK.get(bar)
    ym = t.dt.to_period("M")
    cnt = ym.value_counts().sort_index()
    full = pd.period_range(ym.min(), ym.max(), freq="M")
    absent = [str(p) for p in full if p not in cnt.index]
    low = []; worst = float("nan")
    if per_week is not None and len(cnt):
        expected = per_week * 4.3
        inner = cnt.iloc[1:-1] if len(cnt) > 2 else cnt
        ratio = inner / expected
        low = [str(p) for p, r in ratio.items() if r < min_ratio]
        worst = 0.0 if absent else (float(ratio.min()) if len(ratio) else float("nan"))
    missing = sorted(set(absent) | set(low))
    return {"months": int(len(full)), "missing_months": len(missing), "missing": missing, "worst_ratio": worst,
            "n_gaps": int(len(gaps)), "max_gap_h": float(gaps[0]["hours"]) if gaps else 0.0, "gaps": gaps[:5],
            "first": str(t.iloc[0]), "last": str(t.iloc[-1])}


def health(syms, kind="H1_dukascopy", bar=None, min_ratio=0.8, gap_hours=None):
    """銘柄ごとに 成功／データなし／失敗 を区別し、load_* と同じ前処理（high==low を除く）の後で check_gaps をまとめる。
    使う場面: run の最初に 1 回。返り値をそのまま結果 JSON の "data_health" に入れる。failed が 1 件でもあれば結論を「確定」にしない
    入力: syms、kind（"H1_dukascopy"・"D1_fromH1" など）、bar（省略で kind から推定）、min_ratio、gap_hours
    返り値: {"ok", "no_data", "failed": {sym: 例外}, "gaps": {sym: check_gaps の結果（欠けがある銘柄だけ）}, "n_gap_syms", "n_dup": {sym: 重複行数（あれば）}}
    禁止: failed が 1 件でもあるのに結果を「確定」にしない。gaps が空でないのに空白を無視して年単位の平均を取らない
    段階: 読み込み
    """
    bar = (bar or _bar_of(kind)).upper()
    out = {"ok": [], "no_data": [], "failed": {}, "gaps": {}, "n_dup": {}}
    for s in syms:
        p = data_path(s, kind)  # 2026-10-22: load_* と同じ解決順（DATA_DIR → DATA_DIR2）。wide48 の 34 銘柄が no_data に誤報されていた
        if not os.path.exists(p):
            out["no_data"].append(s); continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = _read(p)
            if "high" in df and "low" in df:
                df = df[df["high"] != df["low"]]
            g = check_gaps(df, bar=bar, min_ratio=min_ratio, gap_hours=gap_hours)
        except Exception as e:  # 読めない＝失敗。黙って空にしない
            out["failed"][s] = repr(e); continue
        out["ok"].append(s)
        if df.attrs.get("n_dup"):
            out["n_dup"][s] = df.attrs["n_dup"]
        if g["missing_months"] or g["n_gaps"]:
            out["gaps"][s] = g
    out["n_gap_syms"] = len(out["gaps"])
    return out
