# -*- coding: utf-8 -*-
"""S08（暗号資産の族だけで順張り）の共通部（2026-10-22・/lab-plan ターミナル版 N=4・Q385/Q386）。
fe_core は書き換えない。Runner 型に次の 3 つを足す薄い層:
  1. 封印: Runner の `_load` の後で time < SEAL（2024-07-01）に切る（SealedRunner。流れは変えない。Runner に end が無いため）。
  2. 暗号版の規程モード: Runner の rule_mode は前後半の境を SPLIT_YEAR=2017 に固定しているので、暗号（2017〜）では t_pre が出ない。
     同じ鍵名（t_all/t_pre/t_post/mean_bp/max_dd/worst_day/stops/gate）で split 2021 の規程モードを extra に書く。
     規則: RULES_FINTOKEI のまま、レバ上限だけ min(2, 5)（Fintokei の暗号レバ 1:5 は 2 より緩いので実質 2）。日次停止は週末の足にも当たる（D1 に土日を含む）。
  3. コスト 2 本: 往復 30 bp（CRYPTO_COST_RT_REL・Runner の main）と、実測スプレッド（_データ/raw/D1/spread_<sym>.csv の日次系列を往復とみなす。無い銘柄は 30 bp）。
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
from fe_core import Runner, CRYPTO_COST_RT_REL, pnl_bp, by_year_stats, cluster_t, sharpe_ann, max_drawdown, fmt, nw_t  # noqa: E402
from fe_core import size_weights, simulate_portfolio, yearly_t, RULES_FINTOKEI, RULES_NONE  # noqa: E402
from fe_core import _paths as P  # noqa: E402

SEAL = pd.Timestamp("2024-07-01")
CRYPTO_SPLIT = 2021
CRYPTO2 = ["BTCUSD", "ETHUSD"]
RULES_CRYPTO = dict(RULES_FINTOKEI, max_leverage=min(RULES_FINTOKEI["max_leverage"], 5.0))  # 暗号レバ 1:5 の上限は 2 より緩い → 2 のまま


class SealedRunner(Runner):
    """Runner に封印（time < SEAL）を足すだけ。流れ・統計・帰無は Runner のまま。"""

    def _load(self, sym, smoke, rng):
        df = super()._load(sym, smoke, rng)
        return df[df["time"] < SEAL].reset_index(drop=True)


def measured_spread_rel(sym, times):
    """実測スプレッド（往復・価格比）の日次系列。spread_<sym>.csv が無ければ 30 bp の定数。返り値 (Series(index=times), source)."""
    path = os.path.join(P.DATA_DIR2, f"spread_{sym}.csv")
    idx = pd.to_datetime(pd.Series(times)).dt.floor("D")
    if not os.path.exists(path):
        return pd.Series(CRYPTO_COST_RT_REL, index=idx.values), "const30bp"
    sp = pd.read_csv(path); sp["time"] = pd.to_datetime(sp["time"])
    rel = (sp["spread"] / sp["bid_close"]).replace([np.inf, -np.inf], np.nan)
    s = pd.Series(rel.values, index=sp["time"].values).sort_index()
    s = s[~s.index.duplicated()]
    out = s.reindex(idx.values).ffill().bfill().fillna(CRYPTO_COST_RT_REL)
    return pd.Series(out.values, index=idx.values), "spread_csv_daily"


def rule_mode_block(pos_df, close_df, cost_oneway_df, split_year=CRYPTO_SPLIT, rules=RULES_CRYPTO):
    """規程モード（暗号版）: 合図の符号 → size_weights → simulate_portfolio → yearly_t。Runner の rule_mode と同じ鍵名＋nw_t。"""
    POS = np.sign(pos_df.fillna(0.0)); R = close_df.pct_change(fill_method=None)
    out = {}
    for name, rl in (("none", RULES_NONE), ("fintokei", rules)):
        W = size_weights(POS, R, rl); sim = simulate_portfolio(W, R, cost_oneway_df, rl); port = sim["port"]
        pre = port[port.index.year < split_year]; post = port[port.index.year >= split_year]
        t_all, yt = yearly_t(port); t_pre, _ = yearly_t(pre); t_post, _ = yearly_t(post)
        out[name] = {"t_all": fmt(t_all), "t_pre": fmt(t_pre), "t_post": fmt(t_post),
                     "n_years_pre": int(pre.index.year.nunique()), "n_years_post": int(post.index.year.nunique()),
                     "nw_t_pre": fmt(nw_t(pre.to_numpy(), lag=5)) if len(pre) > 10 else None, "nw_t_post": fmt(nw_t(post.to_numpy(), lag=5)) if len(post) > 10 else None,
                     "mean_bp": fmt(port.mean() * 1e4), "mean_bp_pre": fmt(pre.mean() * 1e4) if len(pre) else None, "mean_bp_post": fmt(post.mean() * 1e4) if len(post) else None,
                     "sigma_pct": fmt(port.std() * 100), "sharpe": fmt(sharpe_ann(port.to_numpy())),
                     "max_dd": fmt(sim["max_dd"]), "worst_day": fmt(sim["worst_day"]), "stops": int(sim["stops"]),
                     "gross_median": fmt(float(W.abs().sum(axis=1).median())), "n_days": int(len(port)),
                     "years": yt.to_dict(orient="records"), "rules": dict(rl)}
    f = out["fintokei"]; ok = lambda v: v is not None and v == v  # noqa: E731
    out["gate"] = {"t_pre_ge2": bool(ok(f["t_pre"]) and f["t_pre"] >= 2), "t_post_ge2": bool(ok(f["t_post"]) and f["t_post"] >= 2),
                   "max_dd_within_6pct": bool(ok(f["max_dd"]) and f["max_dd"] >= -0.06)}
    out["gate"]["pass"] = all(out["gate"].values())
    out["split_year"] = split_year; out["seal"] = str(SEAL.date())
    return out


def _period_stats(cells, split_year):
    out = {}
    for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, split_year), "post": (split_year, 9999)}.items():
        d = cells[(cells["year"] >= y0) & (cells["year"] < y1)]
        if d.empty:
            continue
        b = by_year_stats(d, "pnl_net", y0=y0, y1=y1); g = by_year_stats(d, "pnl_gross", y0=y0, y1=y1)
        pool = d.groupby("time")["pnl_net"].mean()
        out[pn] = {"n_years": b["n_years"], "years_dropped": b["years_dropped"], "n_syms": int(d["sym"].nunique()),
                   "bp_gross": fmt(g["mean"]), "bp_net": fmt(b["mean"]), "t_year": fmt(b["t"]), "t_cluster": fmt(cluster_t(d, "pnl_net", by="time")["t"]),
                   "sharpe_net": fmt(sharpe_ann(pool.values)), "max_dd_net_bp": fmt(max_drawdown(pool.values))}
    return out


def make_extra(spec, cache, strategy, subgroups=None):
    """summarize_extra 用。cache: strategy が貯めた {sym: df}。
    書くもの: rule_mode_crypto（30 bp）・rule_mode_crypto_spread（実測スプレッド）・net_spread（実測スプレッドの銘柄×設定の年単位統計）・subgroups（記述）。"""
    def _extra(cells, sp):
        syms = list(cache.keys())
        p = sp.params[sp.main_param]
        pos, close, c30, csp, src = {}, {}, {}, {}, {}
        for s in syms:
            df = cache[s]; idx = pd.to_datetime(df["time"]); c = df["close"].values
            a = np.asarray(strategy(df, p, s), float)
            if sp.warmup:
                a[: sp.warmup + 1] = 0.0
            pos[s] = pd.Series(a, index=idx); close[s] = pd.Series(c, index=idx)
            rel30 = sp.cost_rel.get(s, CRYPTO_COST_RT_REL); c30[s] = pd.Series(rel30 / 2.0, index=idx)
            ms, src[s] = measured_spread_rel(s, df["time"].values); csp[s] = pd.Series(ms.values / 2.0, index=idx)
        POS = pd.DataFrame(pos).sort_index().fillna(0.0); C = pd.DataFrame(close).sort_index().ffill()
        C30 = pd.DataFrame(c30).sort_index().ffill().fillna(0.0); CSP = pd.DataFrame(csp).sort_index().ffill().fillna(0.0)
        out = {"rule_mode_crypto": rule_mode_block(POS, C, C30), "rule_mode_crypto_spread": rule_mode_block(POS, C, CSP),
               "spread_source": src, "spread_median_rt_bp": {s: fmt(float(np.nanmedian(csp[s].values)) * 2e4) for s in syms}}
        # 実測スプレッドでの等金額の損益（Runner の cells と同じ形で銘柄×設定）
        frames = []
        for s in syms:
            df = cache[s]; c = df["close"].values; cb = csp[s].values * 1e4
            for i, pp in enumerate(sp.params):
                a = np.asarray(strategy(df, pp, s), float); n = pnl_bp(a, c, cb); g = pnl_bp(a, c, np.zeros(len(c)))
                if sp.warmup:
                    n[: sp.warmup + 1] = np.nan; g[: sp.warmup + 1] = np.nan
                frames.append(pd.DataFrame({"time": df["time"].values, "year": df["year"].values, "sym": s, "param": i, "pnl_net": n, "pnl_gross": g}))
        cs = pd.concat(frames, ignore_index=True)
        out["net_spread"] = {f"p{i}": _period_stats(cs[cs["param"] == i], sp.split_year) for i, _ in enumerate(sp.params)}
        if subgroups:
            out["subgroups"] = {}
            for gname, members in subgroups.items():
                ms = [s for s in syms if s in members]
                if not ms:
                    continue
                cg = cells[cells["sym"].isin(ms)]
                out["subgroups"][gname] = {"syms": ms, **{f"p{i}": _period_stats(cg[cg["param"] == i], sp.split_year) for i, _ in enumerate(sp.params)}}
                if len(ms) >= 1:
                    out["subgroups"][gname]["rule_mode_crypto"] = {k: v for k, v in rule_mode_block(POS[ms], C[ms], C30[ms]).items() if k in ("fintokei", "gate")}
        out["per_sym_main"] = {s: _period_stats(cells[(cells["sym"] == s) & (cells["param"] == sp.main_param)], sp.split_year) for s in syms}
        return out
    return _extra


def judge_s08(res, spec):
    """S08 の 3 分岐（Q385/Q386 共通・事前固定）。
    支持: 規程モード（暗号版・30 bp・split 2021・封印前）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main・30 bp）の全期間 z≥2。
    棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。実測スプレッド版は併記（判定には使わない）。"""
    m = res.get("main", {}); ex = res.get("extra", {}); rm = ex.get("rule_mode_crypto", {}); f = rm.get("fintokei", {}); gate = rm.get("gate", {})
    z = (m.get("all") or {}).get("z")
    if z is None or f.get("t_all") is None:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    if z < 1 or f["t_all"] < 0:
        return "棄却: 等金額の全期間 z<1 または 規程モードの t_all<0"
    if gate.get("pass") and z >= 2:
        return "支持: 規程モード（暗号版）で前後半とも t≥2・max_dd≥−6%、かつ等金額の全期間 z≥2"
    return "未確定"
