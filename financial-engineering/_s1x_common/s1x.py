# -*- coding: utf-8 -*-
"""S10〜S13（データ源を 1 つ足す新しい S・2026-10-22 /lab-plan ターミナル版 N=10・Q394〜Q403）の共通部。
fe_core は書き換えない。Runner 型に次を足す薄い層:
  1. 封印: `_load` の後で time < SEAL（2024-07-01）に切る（S08 の SealedRunner と同じ）。読んだ df は `loaded[sym]` に残す
     （クロスアセット・横断の strategy が他銘柄を参照するため。Runner.run は全銘柄を読んでから strategy を呼ぶので二重読みなし）。
  2. 規程モード: Runner の `_rule_mode` は前後半の境が SPLIT_YEAR=2017 固定・main_param だけ。ここでは **spec.split_year** を使い、
     **全設定**について同じ鍵名（t_all/t_pre/t_post/mean_bp/max_dd/worst_day/stops/gate）で出す。`rule_mode` は main、`rule_mode_params` は設定ごと。
  3. 判定（judge_gate・3 分岐・事前固定・S09 と同じ形）: 支持＝規程モード（RULES_FINTOKEI・封印前・境 spec.split_year）の前後半とも年単位 t≥2 かつ
     max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2。棄却＝等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。
  4. データ源の補助: 実測スプレッド（_データ/raw/D1/spread_<sym>.csv）の日次系列と z、FOMC の暦（知識から記載・実行者が原典と照合・--fomc-csv で差し替え）、
     月替わり（各銘柄の足から数える）。
  5. データガード（S07 と同じ型）: 必要な銘柄が揃わなければ本番を実行せず status=データ待ち を書いて exit 2。
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
from fe_core import Runner, fmt, nw_t, sharpe_ann  # noqa: E402
from fe_core import size_weights, simulate_portfolio, yearly_t, RULES_FINTOKEI, RULES_NONE  # noqa: E402
from fe_core import _paths as P  # noqa: E402

SEAL = pd.Timestamp("2024-07-01")
IDX13 = list(P.IDX13)
BOND3 = list(P.BOND3)
WIDE48 = list(P.WIDE48)
USD7 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]   # 対ドル 7 ペア（FX22 のうち USD を含むもの）
USD_IS_QUOTE = {"EURUSD": True, "GBPUSD": True, "AUDUSD": True, "NZDUSD": True, "USDJPY": False, "USDCHF": False, "USDCAD": False}

# ---------------------------------------------------------------- FOMC の暦（定例会合の発表日。2 日会合は 2 日目）
# 知識から記載（Claude・2026-10-22）。**実行者が federalreserve.gov の "FOMC Meeting calendars" と照合すること。**
# 2020-03-03・03-15 の緊急利下げは定例でないため入れていない（2020-03-18 の定例は中止）。2025〜2026 は封印後で判定に使わない。
# 差し替え: スクリプトに `--fomc-csv <path>`（date 列・YYYY-MM-DD）を渡すとこの表の代わりに読む。
FOMC_DATES = [
    "2010-01-27", "2010-03-16", "2010-04-28", "2010-06-23", "2010-08-10", "2010-09-21", "2010-11-03", "2010-12-14",
    "2011-01-26", "2011-03-15", "2011-04-27", "2011-06-22", "2011-08-09", "2011-09-21", "2011-11-02", "2011-12-13",
    "2012-01-25", "2012-03-13", "2012-04-25", "2012-06-20", "2012-08-01", "2012-09-13", "2012-10-24", "2012-12-12",
    "2013-01-30", "2013-03-20", "2013-05-01", "2013-06-19", "2013-07-31", "2013-09-18", "2013-10-30", "2013-12-18",
    "2014-01-29", "2014-03-19", "2014-04-30", "2014-06-18", "2014-07-30", "2014-09-17", "2014-10-29", "2014-12-17",
    "2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17", "2015-07-29", "2015-09-17", "2015-10-28", "2015-12-16",
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
    "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
]
_FOMC_OVERRIDE = {"dates": None, "source": "knowledge(2026-10-22)"}


def fomc_dates():
    """FOMC 発表日（DatetimeIndex・昇順）。--fomc-csv が sys.argv にあればそれを読む（date 列）。smoke の合成データ（2015〜）にもそのまま当てる。"""
    if _FOMC_OVERRIDE["dates"] is not None:
        return _FOMC_OVERRIDE["dates"]
    av = sys.argv[1:]
    if "--fomc-csv" in av:
        path = av[av.index("--fomc-csv") + 1]
        d = pd.read_csv(path); col = "date" if "date" in d.columns else d.columns[0]
        _FOMC_OVERRIDE["dates"] = pd.DatetimeIndex(sorted(pd.to_datetime(d[col]).dt.floor("D").unique()))
        _FOMC_OVERRIDE["source"] = path
    else:
        _FOMC_OVERRIDE["dates"] = pd.DatetimeIndex(pd.to_datetime(FOMC_DATES))
    return _FOMC_OVERRIDE["dates"]


def fomc_source():
    return _FOMC_OVERRIDE["source"]


def bar_dates(df):
    """足の日付（暦日・UTC 0 時区切りの D1_fromH1 なら time の日付そのもの）。"""
    return pd.to_datetime(df["time"]).dt.floor("D").values.astype("datetime64[D]")


def fomc_day_index(df):
    """各 FOMC 発表日に対応する足の添字（その日の足。無ければ直後の足＝休場日対策。範囲外は捨てる）。"""
    d = bar_dates(df); fd = fomc_dates().values.astype("datetime64[D]")
    idx = np.searchsorted(d, fd, side="left")
    keep = idx < len(d)
    idx, fd = idx[keep], fd[keep]
    near = (d[idx] - fd).astype("timedelta64[D]").astype(int) <= 3   # データ開始前の日付が先頭の足に化けないよう 3 日以内だけ
    return np.unique(idx[near])


def hold_bars_pos(df, bar_idx, offsets):
    """「足 j+off（off∈offsets）のリターンを取る」pos。pos[t] は t→t+1 のリターンに効くので、足 j+off を取るには pos[j+off−1]=1。長さ len(df)。"""
    n = len(df); pos = np.zeros(n)
    for j in bar_idx:
        for off in offsets:
            k = j + off - 1
            if 0 <= k < n:
                pos[k] = 1.0
    return pos


def fomc_cycle_day(df):
    """FOMC サイクル日（Cieslak・Morse・Vissing-Jorgensen 2019 の数え方）: 各足について、直前の発表日の足からの営業日（足）数。
    発表日の前日の足は −1（次の会合の週 0 に属す）。発表日より前に会合が無い先頭は NaN。"""
    n = len(df); c = np.full(n, np.nan); fi = fomc_day_index(df)
    if len(fi) == 0:
        return c
    for j in range(n):
        k = np.searchsorted(fi, j, side="right") - 1
        if k >= 0:
            c[j] = j - fi[k]
    for j in fi:
        if j - 1 >= 0:
            c[j - 1] = -1
    return c


def even_week_mask(cycle_day):
    """偶数週: 週 0＝−1〜3、週 2＝9〜13、週 4＝19〜23、週 6＝29〜33（営業日）。"""
    c = cycle_day; m = np.zeros(len(c), bool)
    for lo, hi in ((-1, 3), (9, 13), (19, 23), (29, 33)):
        m |= (c >= lo) & (c <= hi)
    return m


def tom_offsets_pos(df, last=1, first=3):
    """月替わり: 月の最後の last 営業日と翌月の最初の first 営業日のリターンを取る pos。営業日は各銘柄の足で数える。"""
    d = pd.to_datetime(df["time"]); ym = (d.dt.year * 12 + d.dt.month).values
    n = len(df); take = np.zeros(n, bool)
    # 月の最初の足の添字
    starts = np.r_[0, np.flatnonzero(np.diff(ym) != 0) + 1]
    for s in starts:
        for off in range(first):
            if s + off < n and ym[min(s + off, n - 1)] == ym[s]:
                take[s + off] = True
        for off in range(1, last + 1):
            if s - off >= 0:
                take[s - off] = True
    take[: starts[1] if len(starts) > 1 else 0] = False  # 先頭の不完全な月は取らない
    pos = np.zeros(n); pos[:-1] = take[1:].astype(float)   # 足 j を取る → pos[j−1]
    return pos


# ---------------------------------------------------------------- スプレッド
_SPREAD = {}


def spread_rel_daily(sym, times, smoke=False, rng=None):
    """実測スプレッド（往復・価格比）の日次系列を times に合わせる（ffill）。無い銘柄は NaN。smoke は対数正規の合成（判定に使わない）。返り値 (np.ndarray, source)。"""
    idx = pd.to_datetime(pd.Series(times)).dt.floor("D").values
    if smoke:
        r = rng if rng is not None else np.random.default_rng(0)
        base = 1e-4 * np.exp(0.4 * r.standard_normal(len(idx)))
        base[r.random(len(idx)) < 0.02] *= 4.0
        return base, "smoke"
    if sym not in _SPREAD:
        path = os.path.join(P.DATA_DIR2, f"spread_{sym}.csv")
        if not os.path.exists(path):
            _SPREAD[sym] = None
        else:
            sp = pd.read_csv(path); sp["time"] = pd.to_datetime(sp["time"]).dt.floor("D")
            rel = (sp["spread"] / sp["bid_close"]).replace([np.inf, -np.inf], np.nan)
            s = pd.Series(rel.values, index=sp["time"].values).sort_index()
            _SPREAD[sym] = s[~s.index.duplicated()]
    s = _SPREAD[sym]
    if s is None:
        return np.full(len(idx), np.nan), "none"
    return s.reindex(idx).ffill().values, "spread_csv_daily"


def rolling_z(x, window=250, min_periods=120):
    """t までの window 本（t を含む）の平均・標準偏差で z 化。先頭は NaN。"""
    s = pd.Series(np.asarray(x, float))
    m = s.rolling(window, min_periods=min_periods).mean(); sd = s.rolling(window, min_periods=min_periods).std(ddof=1)
    return ((s - m) / sd).values


# ---------------------------------------------------------------- Runner
class SealedRunner(Runner):
    """Runner に封印（time < SEAL）・loaded・spec.split_year に従う全設定の規程モードを足す。流れ・統計・帰無・Holm は Runner のまま。"""

    def __init__(self, spec, strategy, judge=None, null=None, summarize_extra=None, here=None):
        super().__init__(spec, strategy, judge=judge or judge_gate, null=null, summarize_extra=summarize_extra, here=here)
        self.loaded = {}; self.smoke = False; self.rng = None

    def _load(self, sym, smoke, rng):
        self.smoke = smoke; self.rng = rng
        df = super()._load(sym, smoke, rng)
        df = df[df["time"] < SEAL].reset_index(drop=True)
        self.loaded[sym] = df
        return df

    def _rule_mode_one(self, dfs, p):
        spec = self.spec
        pos, close, cost = {}, {}, {}
        for sym, df in dfs.items():
            idx = pd.to_datetime(df["time"]); c = df["close"].values
            a = np.asarray(self.strategy(df, p, sym), float)
            if spec.warmup: a[: spec.warmup + 1] = 0.0
            a = np.sign(np.nan_to_num(a))
            pos[sym] = pd.Series(a, index=idx); close[sym] = pd.Series(c, index=idx)
            cost[sym] = pd.Series(self._cost(sym, c) / 1e4, index=idx)
        POS = pd.DataFrame(pos).sort_index().fillna(0.0); C = pd.DataFrame(close).sort_index().ffill()
        R = C.pct_change(fill_method=None); COST = pd.DataFrame(cost).sort_index().ffill().fillna(0.0)
        out = {}
        for name, rules in (("none", RULES_NONE), ("fintokei", RULES_FINTOKEI)):
            W = size_weights(POS, R, rules); sim = simulate_portfolio(W, R, COST, rules); port = sim["port"]
            pre = port[port.index.year < spec.split_year]; post = port[port.index.year >= spec.split_year]
            t_all, yt = yearly_t(port); t_pre, _ = yearly_t(pre); t_post, _ = yearly_t(post)
            out[name] = {"t_all": fmt(t_all), "t_pre": fmt(t_pre), "t_post": fmt(t_post),
                         "n_years_pre": int(pre.index.year.nunique()), "n_years_post": int(post.index.year.nunique()),
                         "nw_t_pre": fmt(nw_t(pre.to_numpy(), lag=5)) if len(pre) > 10 else None,
                         "nw_t_post": fmt(nw_t(post.to_numpy(), lag=5)) if len(post) > 10 else None,
                         "mean_bp": fmt(port.mean() * 1e4), "mean_bp_pre": fmt(pre.mean() * 1e4) if len(pre) else None,
                         "mean_bp_post": fmt(post.mean() * 1e4) if len(post) else None,
                         "sigma_pct": fmt(port.std() * 100), "sharpe": fmt(sharpe_ann(port.to_numpy())),
                         "max_dd": fmt(sim["max_dd"]), "worst_day": fmt(sim["worst_day"]), "stops": int(sim["stops"]),
                         "gross_median": fmt(float(W.abs().sum(axis=1).median())), "n_days": int(len(port)),
                         "years": yt.to_dict(orient="records"), "rules": dict(rules)}
        f = out["fintokei"]; ok = lambda v: v is not None and v == v  # noqa: E731
        out["gate"] = {"t_pre_ge2": bool(ok(f["t_pre"]) and f["t_pre"] >= 2), "t_post_ge2": bool(ok(f["t_post"]) and f["t_post"] >= 2),
                       "max_dd_within_6pct": bool(ok(f["max_dd"]) and f["max_dd"] >= -0.06)}
        out["gate"]["pass"] = all(out["gate"].values())
        out["split_year"] = spec.split_year; out["seal"] = str(SEAL.date())
        return out

    def _rule_mode(self, dfs):
        spec = self.spec
        per = [self._rule_mode_one(dfs, p) for p in spec.params]
        main = dict(per[spec.main_param]); main["params"] = [{"param": i, "p": p, "fintokei": {k: per[i]["fintokei"][k] for k in ("t_all", "t_pre", "t_post", "mean_bp", "max_dd", "sharpe", "stops")},
                                                             "none": {k: per[i]["none"][k] for k in ("t_all", "t_pre", "t_post", "mean_bp", "max_dd", "sharpe")},
                                                             "gate": per[i]["gate"]} for i, p in enumerate(spec.params)]
        return main


def judge_gate(res, spec):
    """3 分岐（Q394〜Q403 共通・事前固定）。支持: 規程モード（RULES_FINTOKEI・封印前・境 spec.split_year）の前後半とも年単位 t≥2 かつ max_dd≥−6%、
    かつ等金額（Runner main）の全期間 z≥2。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副設定・銘柄別は記述。"""
    m = res.get("main", {}); rm = res.get("rule_mode", {}); f = rm.get("fintokei", {}); gate = rm.get("gate", {})
    z = (m.get("all") or {}).get("z")
    if z is None or f.get("t_all") is None:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    if z < 1 or f["t_all"] < 0:
        return "棄却: 等金額の全期間 z<1 または 規程モードの t_all<0"
    if gate.get("pass") and z >= 2:
        return "支持: 規程モードで前後半とも t≥2・max_dd≥−6%、かつ等金額の全期間 z≥2"
    return "未確定"


def data_guard(spec, here, min_syms, extra_required=()):
    """必要な銘柄数が揃わなければ本番を実行しない（JSON に status=データ待ち を書いて exit 2）。extra_required は syms の外で必要な銘柄。"""
    from fe_core import syms_available, write_result
    ok, missing = syms_available(spec.syms, kind=spec.kind)
    ok2, missing2 = syms_available(list(extra_required), kind=spec.kind) if extra_required else ([], [])
    if len(ok) < min_syms or missing2:
        res = {"status": "データ待ち", "n_ok": len(ok), "n_required": min_syms, "missing": missing, "missing_extra": missing2,
               "note": "データガード: 必要な D1 が足りないため本番を実行しない。release で待ちに戻す。"}
        write_result(spec.qid, res, smoke=False, here=here)
        print(f"データ待ち: ok={len(ok)}/{len(spec.syms)} missing_extra={missing2}")
        sys.exit(2)


def run_main(spec, strategy, here, min_syms, extra_required=(), null=None, judge=None, summarize_extra=None, runner_holder=None):
    """スクリプトの入口。--readme／--idea-row はガードを飛ばす。runner_holder（dict）に obj を入れて strategy が loaded を参照できるようにする。"""
    av = sys.argv[1:]
    if "--smoke" not in av and "--readme" not in av and "--idea-row" not in av:
        data_guard(spec, here, min_syms, extra_required)
    r = SealedRunner(spec, strategy, judge=judge, null=null, summarize_extra=summarize_extra, here=here)
    if runner_holder is not None:
        runner_holder["obj"] = r
    r.execute(extra_args=lambda ap: ap.add_argument("--fomc-csv", default=None, help="FOMC 発表日の CSV（date 列）。省略で s1x.FOMC_DATES（知識から記載）"))
