#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q280: EIA 原油在庫発表の実発表日に揃えた WTI・UKOIL の継続性再検証（2 銘柄プール）
================================================================================

【位置づけ】
- Q269（毎週水曜近似）の次段階。発表日を米祝日の木曜ずれまで反映し、WTI・UKOIL を1本にプールして検定する。
- Q269 の判定（事前閾値）は本検定でも変えない: プール全期間 |z|<2 → 支持（続かない）、|z|≥2 → 棄却（向きを書く）。それ以外は Q269 と並べて解釈。

【仮説（Q269 と同じ・測る前に固定）】
H: EIA 原油在庫発表（NY 10:30 ET）直後 1 時間（10 時台）の WTI・UKOIL の向きは、続く 11〜13 時台（3 時間）に反転も継続もしない: E[sign(r_0)·r_{1..3}]=0。

【データ】
WTI・UKOIL H1_dukascopy（2011-09〜2026-06）。発表日表は `eia_release_dates.csv`（`date,rule,reason`・NY 日付）。
- 既定: 毎週水曜 10:30 ET。
- 木曜ずれ: その週の Mon/Tue/Wed に米連邦祝日があるとき Thursday 10:30 ET（USFederalHolidayCalendar の observed 祝日で判定・Columbus Day を含む）。
- 来週分の Monday 5pm シフト等の例外（Christmas 直前）は本検定では反映しない: 近似ゆえに machine_verdict の脚注で明示する。
- 「知識から記載・実行者が EIA の原典（Release Schedule）と照合」。

【定義（Q269 と同じ・1通りに固定）】
NY 時刻 America/New_York。r_0 = 10 時台、r_1..3 = 11〜13 時台の和。y = sign(r_0)·r_1..3 [bp]。
対照: 他の曜日・時刻は Q269 側（本検定では event のみを扱う）。

【測るもの】
2 銘柄プールの y の平均と年単位 t（year × sym セル → 年平均 → 全期間平均）、符号付け替え帰無による z。
前後半（2012–2016／2017–）と銘柄別の数値は記述。

【帰無】
y = sign(r_0)·r_{1..3} の sign(r_0) をイベント日ごとに ±1 無作為に付け替え B=2000。
年ごとの平均→全期間平均を評価統計量とする（by_year_stats と同じ重み）。

【判定（事前固定・変更禁止）】
- プール（WTI+UKOIL）全期間 |z|<2 かつ 2 銘柄とも全期間 |z|<2 → 支持（続かない）。
- プール全期間 |z|≥2 かつ 2 銘柄とも前後半で同符号で |z|≥2 → 棄却（向きを書く）。
- それ以外 → 未確定（Q269 と並べて解釈）。
多重比較: 主判定はプールの全期間（1 本）。銘柄別・前後半は記述。

【捨てた案の数】
約2: 銘柄ごとの Fisher 結合（プールの方が標本効率が高い）、Thursday シフトの詳細手入力（信頼できる原典一覧が無い）。

【知識の締め切り】
Claude の知識の締め切りはおよそ 2026-06。データは 2026-06 まで。EIA の実暦の精密版はここでは追わない（近似の精度を machine_verdict に注記）。

【委託の確かめ方】
設計: Opus /lab（2026-10-13・Q269 の次段階）。実行と解釈は本セッション。
machine_verdict は上の判定規則の機械当て。確定／ノイズ／未確定の解釈は実行者が書く。

【実装】自己完結・決定的（乱数は帰無の並べ替えのみ seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_eia_pool_q280.py           （B=2000・30 秒目安）
      python3 kensho_eia_pool_q280.py --smoke   （合成データで経路の確認。判定には使わない）
"""
import argparse
import datetime as _dt
import json
import math
import os
import sys
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def _p(*parts):
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
OUT = os.path.join(HERE, "results")
EIA_CSV = os.path.join(HERE, "eia_release_dates.csv")
SYMS2 = ["WTI", "UKOIL"]
TZ = "America/New_York"
H0, H_FOLLOW = 10, [11, 12, 13]
SPLIT_YEAR = 2017
SEED = 20261013
QID = "Q280"
DEFAULT_B = 2000
START = "2012-01-01"


def _read(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def _smoke_ohlc(sym, rng, n=130000):
    rng = rng or np.random.default_rng(SEED)
    t = pd.date_range("2012-01-01", periods=n, freq="h")
    r = rng.normal(0.0, 0.0025, n)
    c = 50.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.001, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.001, n)))
    v = np.abs(rng.lognormal(5, 0.4, n))
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v})


def load_h1(sym, smoke, rng):
    if smoke:
        df = _smoke_ohlc(sym, rng)
    else:
        df = _read(os.path.join(DATA_DIR, f"data_{sym}_H1_dukascopy.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    return df


def exists_sym(sym):
    return os.path.exists(os.path.join(DATA_DIR, f"data_{sym}_H1_dukascopy.csv"))


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp, _dt.datetime, _dt.date)):
        return str(o)
    return str(o)


def daily_cells(sym, smoke, rng):
    """NY 日付ごとに r0・r123 [bp] を作る。"""
    df = load_h1(sym, smoke, rng)
    df = df[df["time"] >= pd.Timestamp(START)].reset_index(drop=True)
    t = pd.DatetimeIndex(df["time"]).tz_localize("UTC").tz_convert(TZ)
    d = pd.DataFrame({"ret_bp": df["ret"].values * 1e4, "nydate": t.tz_localize(None).normalize(), "nyhour": t.hour})
    d = d.dropna(subset=["ret_bp"])
    r0 = d[d["nyhour"] == H0].groupby("nydate")["ret_bp"].sum()
    fol = d[d["nyhour"].isin(H_FOLLOW)].groupby("nydate")["ret_bp"].agg(["sum", "size"])
    fol = fol[fol["size"] == len(H_FOLLOW)]["sum"]
    cells = pd.DataFrame({"r0": r0}).join(fol.rename("r123"), how="inner").reset_index()
    cells = cells[cells["r0"] != 0].reset_index(drop=True)
    cells["year"] = cells["nydate"].dt.year
    cells["dow"] = cells["nydate"].dt.dayofweek
    cells["y"] = np.sign(cells["r0"]) * cells["r123"]
    cells["sym"] = sym
    return cells


def eval_mean(y, year, sym):
    """year × sym セルで平均 → 年平均（銘柄で平均したあと）→ 全期間平均。"""
    df = pd.DataFrame({"y": y, "year": year, "sym": sym})
    df = df.dropna()
    if len(df) == 0:
        return float("nan"), 0, 0
    cell = df.groupby(["year", "sym"])["y"].mean()
    yr = cell.groupby(level=0).mean()
    return float(yr.mean()), int(len(yr)), int(len(df))


def eval_t_byyear(y, year, sym):
    df = pd.DataFrame({"y": y, "year": year, "sym": sym}).dropna()
    if len(df) == 0:
        return float("nan")
    cell = df.groupby(["year", "sym"])["y"].mean()
    yr = cell.groupby(level=0).mean()
    return tstat(yr.values)


def null_z(r0, r123, year, sym, B, rng):
    """sign(r0) を無作為に ±1 付け替えて、年×銘柄→年平均→全期間平均の統計量を B 回。"""
    n = len(r123)
    years = np.asarray(year)
    syms = np.asarray(sym)
    yu = np.unique(years)
    su = np.unique(syms)
    yr_idx = {v: i for i, v in enumerate(yu)}
    sy_idx = {v: i for i, v in enumerate(su)}
    yi = np.array([yr_idx[v] for v in years])
    si = np.array([sy_idx[v] for v in syms])
    nY, nS = len(yu), len(su)
    cell_count = np.zeros((nY, nS))
    for i in range(n):
        cell_count[yi[i], si[i]] += 1
    cell_count[cell_count == 0] = np.nan
    r123 = np.asarray(r123, float)
    S = rng.choice([-1.0, 1.0], size=(B, n))
    null = np.empty(B)
    for b in range(B):
        v = S[b] * r123
        cs = np.zeros((nY, nS))
        for i in range(n):
            cs[yi[i], si[i]] += v[i]
        cell_mean = cs / cell_count
        yr_mean = np.nanmean(cell_mean, axis=1)
        null[b] = np.nanmean(yr_mean)
    return null


def z_of(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null < obs).mean())


def run(args, rng):
    syms = [s for s in SYMS2 if (args.smoke or exists_sym(s))]
    missing = [s for s in SYMS2 if s not in syms]
    cells_all = []
    for s in syms:
        cells_all.append(daily_cells(s, args.smoke, rng))
    cells = pd.concat(cells_all, ignore_index=True)
    # 発表日
    if args.smoke:
        # smoke: 水曜のみ使う
        mask = (cells["dow"] == 2).values
        rule = "smoke_wednesday"
        n_rel_dates = int(cells.loc[mask, "nydate"].nunique())
    else:
        tab = pd.read_csv(EIA_CSV)
        rel = pd.to_datetime(tab["date"]).dt.normalize()
        rel_set = set(rel.tolist())
        mask = cells["nydate"].isin(rel_set).values
        rule = "eia_release_dates.csv (Wed default, Thu if Mon/Tue/Wed federal holiday)"
        n_rel_dates = len(rel_set)

    ev = cells[mask].reset_index(drop=True)
    # 統計
    summary = {"n_release_dates_in_csv": n_rel_dates, "n_event_rows_matched": int(len(ev)),
               "missing": missing, "event_rule": rule, "syms_used": syms}
    stats_all = {}
    for pn, (y0, y1) in (("all", (0, 9999)), ("pre", (0, SPLIT_YEAR)), ("post", (SPLIT_YEAR, 9999))):
        e = ev[(ev["year"] >= y0) & (ev["year"] < y1)].reset_index(drop=True)
        if len(e) < 5:
            stats_all[pn] = {"n_event": int(len(e)), "mean_bp": None, "t": None, "z": None, "pct": None}
            continue
        mean, n_years, n_rows = eval_mean(e["y"], e["year"], e["sym"])
        tst = eval_t_byyear(e["y"], e["year"], e["sym"])
        null = null_z(e["r0"], e["r123"], e["year"], e["sym"], args.B, rng)
        z, pct = z_of(mean, null)
        stats_all[pn] = {"n_event": int(len(e)), "n_years": int(n_years), "mean_bp": f(mean), "t": f(tst),
                          "z": f(z), "pct": f(pct)}
    # 銘柄別も記述
    per_sym = {}
    for s in syms:
        es = ev[ev["sym"] == s].reset_index(drop=True)
        per_sym[s] = {}
        for pn, (y0, y1) in (("all", (0, 9999)), ("pre", (0, SPLIT_YEAR)), ("post", (SPLIT_YEAR, 9999))):
            e = es[(es["year"] >= y0) & (es["year"] < y1)].reset_index(drop=True)
            if len(e) < 5:
                per_sym[s][pn] = {"n_event": int(len(e)), "mean_bp": None, "t": None, "z": None}
                continue
            mean, n_years, _ = eval_mean(e["y"], e["year"], e["sym"])
            tst = eval_t_byyear(e["y"], e["year"], e["sym"])
            null = null_z(e["r0"], e["r123"], e["year"], e["sym"], args.B, rng)
            z, pct = z_of(mean, null)
            per_sym[s][pn] = {"n_event": int(len(e)), "n_years": int(n_years), "mean_bp": f(mean), "t": f(tst),
                              "z": f(z), "pct": f(pct)}
    # 判定
    pool_all_z = stats_all["all"]["z"]
    def _ok_pool_all():
        return pool_all_z is not None and abs(pool_all_z) < 2
    def _ok_each_all():
        for s in syms:
            z = per_sym[s]["all"]["z"]
            if z is None or abs(z) >= 2:
                return False
        return True
    def _reject_each_halves():
        if pool_all_z is None or abs(pool_all_z) < 2:
            return False, None
        signs = []
        for s in syms:
            zp = per_sym[s]["pre"]["z"]; zq = per_sym[s]["post"]["z"]
            if zp is None or zq is None: return False, None
            if zp >= 2 and zq >= 2: signs.append(+1)
            elif zp <= -2 and zq <= -2: signs.append(-1)
            else: return False, None
        if all(sg == signs[0] for sg in signs):
            return True, "継続" if signs[0] > 0 else "反転"
        return False, None

    if len(syms) < 2:
        verdict = f"未確定: 銘柄が揃わない（missing={missing}）"
    elif pool_all_z is None:
        verdict = "未確定: 計算できない（z が nan）"
    elif _ok_pool_all() and _ok_each_all():
        verdict = f"支持: プール全期間 |z|={abs(pool_all_z):.2f}<2 かつ 2 銘柄とも |z|<2（発表直後の向きは続かない）"
    else:
        ok, dirn = _reject_each_halves()
        if ok:
            verdict = f"棄却: プール全期間 |z|={abs(pool_all_z):.2f}≥2 かつ 2 銘柄とも前後半で同符号 |z|≥2（{dirn}）"
        else:
            verdict = (f"未確定: プール |z|={abs(pool_all_z):.2f}（事前閾値 2）・前後半や銘柄別が揃わない。"
                       " Q269 と並べて解釈。EIA 原典との照合は近似（Mon/Tue/Wed 祝日の木曜ずれのみ）。")

    res = {"question": "EIA 原油在庫発表の実発表日に揃えた WTI・UKOIL の継続性再検証（2 銘柄プール）",
           "settings": {"syms": syms, "start": START, "tz": TZ, "hour0_ny": H0, "follow_hours_ny": H_FOLLOW,
                        "split_year": SPLIT_YEAR, "event_rule": rule, "eia_csv": EIA_CSV if not args.smoke else None,
                        "B": args.B, "seed": args.seed,
                        "null": "sign(r0) を日で無作為に付け替え → 年×銘柄→年平均→全期間平均"},
           "pool": stats_all, "per_sym": per_sym, "summary": summary,
           "machine_verdict": verdict,
           "multiple_comparisons": "主判定はプールの全期間（1 本）。銘柄別・前後半は記述。",
           "notes": "祝日の木曜ずれは USFederalHolidayCalendar（Mon/Tue/Wed に祝日 → Thu）で近似。EIA 原典のうち Monday 5pm シフト等の例外は反映しない。"}
    extra = {"event_days": ev[["sym", "nydate", "year", "r0", "r123", "y"]]}
    return res, extra


def write_result(qid, res, smoke, extra_csv=None):
    os.makedirs(OUT, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    path = os.path.join(OUT, f"{pre}_result_{ts}.json")
    res_full = {"qid": qid, "smoke": smoke, "generated": ts, **res}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res_full, f, ensure_ascii=False, indent=1, default=_json_default)
    print("wrote", os.path.relpath(path, HERE))
    if extra_csv is not None:
        for name, df in extra_csv.items():
            cp = os.path.join(OUT, f"{pre}_{name}_{ts}.csv")
            df.to_csv(cp, index=False)
            print("wrote", os.path.relpath(cp, HERE))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=DEFAULT_B)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
