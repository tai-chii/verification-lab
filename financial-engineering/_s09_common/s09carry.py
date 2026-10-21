# -*- coding: utf-8 -*-
"""S09（キャリー＝政策金利差を OHLCV の次に足す最初のデータ源）の共通部（2026-10-22・/lab-plan ターミナル版 N=4・Q389〜Q392）。
fe_core は書き換えない。Runner 型に次を足す薄い層:
  1. 金利差: `_データ/raw/rates/policy_<CCY>.csv`（BIS WS_CBPOL・実施日ベース・8 通貨）から、ペア（base/quote）の金利差 [%/年] を日足の時刻に合わせる。
     時刻 t に使う値は **t − 1 暦日に実施中の政策金利**（rates/README: 発表日と実施日のずれ対策で翌営業日以降に使う）。`_load` の後で df["carry_diff"] に付ける。
  2. スワップ損益: 建玉 held[t]=pos[t−1] が t−1→t の暦日数（dt_prev_h/24。週末またぎは 3 日）ぶん金利差を受け取る（売りは払う）。
     マークアップ（業者の取り分・年 0.75%＝台帳の 0.5〜1% の中点）は建玉の向きによらず常に払う。gross（コスト 0）には金利差だけ、net には金利差 − マークアップ − スプレッドを入れる。
     cells に swap・markup・pnl_price_net（スワップ抜きの net）を残し、規程モードは R_adj = R + carry − sign(W_prev)·markup で simulate_portfolio に渡す（日次停止・最大下落にスワップが正しく入る）。
  3. 封印: `_load` の後で time < SEAL（2024-07-01）に切る（S08 の SealedRunner と同じ）。
  4. 帰無: キャリー符号は年単位で動かないので循環シフトでは帰無が観測と一致しうる（符号が一度も変わらないペアは不変）。S09 のキャリー系（Q389・Q392）は
     **銘柄ごとの符号反転**（null_signflip: 各ペアの pos に独立に ±1 を掛ける）を使う。「金利差の向きは総収益（値動き＋スワップ）の向きを知らない」が帰無。
     TSMOM を含む案（Q390・Q391）は従来どおり循環シフト。
  5. 判定（judge_s09・3 分岐・事前固定）: 支持＝規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2。
     棄却＝等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。スワップ抜きの同じ数字（no_swap）を必ず並べる（データ源を足して関門の数字が上がるか）。
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
from fe_core import Runner, pnl_bp, by_year_stats, cluster_t, sharpe_ann, max_drawdown, fmt, nw_t  # noqa: E402
from fe_core import size_weights, simulate_portfolio, yearly_t, RULES_FINTOKEI, RULES_NONE  # noqa: E402
from fe_core import _paths as P  # noqa: E402

SEAL = pd.Timestamp("2024-07-01")
FX22 = list(P.FX22)
CCY8 = ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "NZD"]
RATES_DIR = P._p("検証", "_データ", "raw", "rates")
MARKUP_ANNUAL = 0.0075      # 年 0.75%（台帳 S09: 過去のスワップ近似＝金利差 − 年 0.5〜1% のマークアップ。中点で固定・掃引しない）
RATE_LAG_DAYS = 1           # 実施日の翌日から合図に使う（rates/README）
DAYS_PER_YEAR = 365.0
START = "2010-01-01"        # FX22 のうち 14 ペアは 2010-01 から。22 ペアを同じ期間で揃える
_POLICY = {}


def pair_ccys(sym):
    """"EURUSD" → ("EUR", "USD")。FX22 はすべて 8 通貨の組。"""
    return sym[:3], sym[3:6]


def rates_available(ccys=CCY8):
    """policy_<CCY>.csv がある通貨／ない通貨。"""
    ok = [c for c in ccys if os.path.exists(os.path.join(RATES_DIR, f"policy_{c}.csv"))]
    return ok, [c for c in ccys if c not in ok]


def load_policy(ccy, smoke=False, rng=None):
    """政策金利 [%] の暦日系列（ffill）。smoke のときは段階状の合成系列（判定には使わない）。"""
    key = (ccy, smoke)
    if key in _POLICY:
        return _POLICY[key]
    if smoke:
        r = rng if rng is not None else np.random.default_rng(abs(hash(ccy)) % (2**32))
        idx = pd.date_range("2008-01-01", "2026-12-31", freq="D")
        steps = np.cumsum(r.choice([-0.25, 0.0, 0.0, 0.0, 0.25], size=len(idx) // 90 + 1))  # 90 日ごとに段階的に動く
        vals = np.repeat(np.clip(2.0 + steps, -0.75, 8.0), 90)[: len(idx)]
        s = pd.Series(vals, index=idx)
    else:
        path = os.path.join(RATES_DIR, f"policy_{ccy}.csv")
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"]); df = df.sort_values("date").drop_duplicates("date", keep="last")
        s = pd.Series(df["policy_rate_pct"].astype(float).values, index=df["date"].values)
        s = s.asfreq("D").ffill()
    _POLICY[key] = s
    return s


def rate_diff(sym, times, lag_days=RATE_LAG_DAYS, smoke=False, rng=None):
    """ペアの金利差 [%/年]（base − quote）を日足の時刻 times に合わせる。時刻 t の値は t − lag_days 暦日に実施中の政策金利。先頭の無い期間は NaN。"""
    b, q = pair_ccys(sym)
    t = (pd.to_datetime(pd.Series(times)).dt.floor("D") - pd.Timedelta(days=lag_days)).values
    pb = load_policy(b, smoke, rng).reindex(t, method="ffill").values
    pq = load_policy(q, smoke, rng).reindex(t, method="ffill").values
    return pb - pq


def swap_bp(pos, diff_pct, dt_prev_h, markup=MARKUP_ANNUAL):
    """スワップ [bp] の 2 列 (carry, markup_cost)。行 t に入るのは held[t]=pos[t−1] が t−1→t の暦日数ぶん受け取る金利差（t−1 時点の diff）。
    carry[t] = held[t]·diff[t−1]/100·days/365·1e4（売りは負）、markup[t] = |held[t]|·markup·days/365·1e4（常に払う）。先頭は 0。days は dt_prev_h/24（NaN は 0）。"""
    pos = np.nan_to_num(np.asarray(pos, float)); d = np.asarray(diff_pct, float)
    held = np.r_[0.0, pos[:-1]]; dprev = np.r_[np.nan, d[:-1]]
    days = np.asarray(dt_prev_h, float) / 24.0; days = np.where(np.isfinite(days), days, 0.0)
    carry = held * np.nan_to_num(dprev) / 100.0 * days / DAYS_PER_YEAR * 1e4
    mk = np.abs(held) * markup * days / DAYS_PER_YEAR * 1e4
    return carry, mk


def total_return_close(close, diff_pct, dt_prev_h):
    """スワップ込みの総収益指数（買い持ちの立場）: close[t]·Π(1 + diff[s−1]/100·days_s/365)。Q391 の副設定（総収益の TSMOM）用。t までの情報だけ。"""
    c = np.asarray(close, float); d = np.asarray(diff_pct, float)
    days = np.asarray(dt_prev_h, float) / 24.0; days = np.where(np.isfinite(days), days, 0.0)
    acc = np.r_[0.0, np.nan_to_num(d[:-1])] / 100.0 * days / DAYS_PER_YEAR
    return c * np.cumprod(1.0 + acc)


def null_signflip(rng, pos, df, p, sym):
    """帰無: 銘柄ごとに独立な符号反転（pos × ±1）。キャリー符号のように年単位で動かない合図用（循環シフトでは帰無が観測と一致しうる）。"""
    return np.asarray(pos, float) * float(rng.choice([-1.0, 1.0]))


class CarryRunner(Runner):
    """Runner に 封印・金利差（df["carry_diff"]）・スワップ損益（cells と規程モード）を足す。流れ・統計・Holm は Runner のまま。
    markup: 年率（既定 0.75%）。loaded: _load した df（横断版の strategy がパネルを組むために参照する。Runner.run は全銘柄を読んでから strategy を呼ぶ）。"""

    def __init__(self, spec, strategy, judge=None, null=None, summarize_extra=None, here=None, markup=MARKUP_ANNUAL):
        super().__init__(spec, strategy, judge=judge or judge_s09, null=null, summarize_extra=summarize_extra, here=here)
        self.markup = float(markup); self.loaded = {}

    def _load(self, sym, smoke, rng):
        df = super()._load(sym, smoke, rng)
        df = df[df["time"] < SEAL].reset_index(drop=True)
        df["carry_diff"] = rate_diff(sym, df["time"].values, smoke=smoke, rng=rng)
        self.loaded[sym] = df
        return df

    def _cells(self, dfs, rng, null=False):
        frames = []
        for sym, df in dfs.items():
            c = df["close"].values; cb = self._cost(sym, c); zero = np.zeros(len(c))
            for i, p in enumerate(self.spec.params):
                pos = np.asarray(self.strategy(df, p, sym), float)
                if len(pos) != len(c):
                    raise ValueError(f"strategy の返り値の長さが違う: {sym} {len(pos)} != {len(c)}")
                if null:
                    pos = self._null_pos(rng, pos, df, p, sym)
                g0, n0 = pnl_bp(pos, c, zero), pnl_bp(pos, c, cb)
                carry, mk = swap_bp(pos, df["carry_diff"].values, df["dt_prev_h"].values, self.markup)
                g = g0 + carry; n = n0 + carry - mk
                if self.spec.warmup:
                    for a in (g, n, g0, n0, carry, mk):
                        a[: self.spec.warmup + 1] = np.nan
                frames.append(pd.DataFrame({"time": df["time"].values, "year": df["year"].values, "sym": sym, "param": i,
                                            "gap": df["gap"].values if "gap" in df else False,
                                            "pnl_gross": g, "pnl_net": n, "exp": np.abs(np.r_[0.0, pos[:-1]]),
                                            "pnl_price_gross": g0, "pnl_price_net": n0, "swap": carry, "markup": mk}))
        return pd.concat(frames, ignore_index=True)

    def _rule_mode(self, dfs):
        """Runner の rule_mode と同じ鍵名（t_all/t_pre/t_post/mean_bp/max_dd/worst_day/stops/gate）に、スワップ込み（既定）とスワップ抜き（*_no_swap）を並べる。"""
        spec = self.spec; p = spec.params[spec.main_param]
        pos, close, cost, diff = {}, {}, {}, {}
        for sym, df in dfs.items():
            idx = pd.to_datetime(df["time"]); c = df["close"].values
            a = np.asarray(self.strategy(df, p, sym), float)
            if spec.warmup: a[: spec.warmup + 1] = 0.0
            a = np.sign(np.nan_to_num(a))
            pos[sym] = pd.Series(a, index=idx); close[sym] = pd.Series(c, index=idx)
            cost[sym] = pd.Series(self._cost(sym, c) / 1e4, index=idx); diff[sym] = pd.Series(df["carry_diff"].values, index=idx)
        POS = pd.DataFrame(pos).sort_index().fillna(0.0); C = pd.DataFrame(close).sort_index().ffill()
        R = C.pct_change(fill_method=None); COST = pd.DataFrame(cost).sort_index().ffill().fillna(0.0)
        DIFF = pd.DataFrame(diff).sort_index().ffill()
        days = pd.Series(POS.index, index=POS.index).diff().dt.total_seconds().fillna(0.0) / 86400.0
        CARRY = DIFF.shift(1).fillna(0.0).div(100.0).mul(days / DAYS_PER_YEAR, axis=0)
        out = {}
        for name, rules in (("none", RULES_NONE), ("fintokei", RULES_FINTOKEI)):
            W = size_weights(POS, R, rules); Wp = W.shift(1).fillna(0.0)
            MK = np.sign(Wp).mul(self.markup * days / DAYS_PER_YEAR, axis=0)
            for suffix, RR in (("", R + CARRY - MK), ("_no_swap", R)):
                sim = simulate_portfolio(W, RR, COST, rules); port = sim["port"]
                pre = port[port.index.year < spec.split_year]; post = port[port.index.year >= spec.split_year]
                t_all, yt = yearly_t(port); t_pre, _ = yearly_t(pre); t_post, _ = yearly_t(post)
                out[name + suffix] = {"t_all": fmt(t_all), "t_pre": fmt(t_pre), "t_post": fmt(t_post),
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
        out["swap"] = {"markup_annual": self.markup, "rate_lag_days": RATE_LAG_DAYS, "seal": str(SEAL.date()), "split_year": spec.split_year,
                       "mean_abs_diff_pct": fmt(float(np.nanmean(np.abs(DIFF.to_numpy())))),
                       "delta_t_pre_swap": fmt(f["t_pre"] - out["fintokei_no_swap"]["t_pre"]) if ok(f["t_pre"]) and ok(out["fintokei_no_swap"]["t_pre"]) else None,
                       "delta_t_post_swap": fmt(f["t_post"] - out["fintokei_no_swap"]["t_post"]) if ok(f["t_post"]) and ok(out["fintokei_no_swap"]["t_post"]) else None}
        return out


def _period_stats(cells, split_year, col="pnl_net"):
    out = {}
    for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, split_year), "post": (split_year, 9999)}.items():
        d = cells[(cells["year"] >= y0) & (cells["year"] < y1)]
        if d.empty:
            continue
        b = by_year_stats(d, col, y0=y0, y1=y1)
        pool = d.groupby("time")[col].mean()
        out[pn] = {"n_years": b["n_years"], "years_dropped": b["years_dropped"], "n_syms": int(d["sym"].nunique()),
                   "bp": fmt(b["mean"]), "t_year": fmt(b["t"]), "t_cluster": fmt(cluster_t(d, col, by="time")["t"]),
                   "sharpe": fmt(sharpe_ann(pool.values)), "max_dd_bp": fmt(max_drawdown(pool.values))}
    return out


def make_extra(spec):
    """summarize_extra: スワップの分解（値動き／スワップ／マークアップ）・スワップ抜きの等金額統計・銘柄別（main）・金利差の記述。"""
    def _extra(cells, sp):
        m = cells[cells["param"] == sp.main_param]
        out = {"decomposition_main": {}}
        for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, sp.split_year), "post": (sp.split_year, 9999)}.items():
            d = m[(m["year"] >= y0) & (m["year"] < y1)]
            if d.empty:
                continue
            out["decomposition_main"][pn] = {k: fmt(float(np.nanmean(d[k].to_numpy()))) for k in ("pnl_price_gross", "pnl_price_net", "swap", "markup", "pnl_gross", "pnl_net")}
        out["no_swap_main"] = {"price_net": _period_stats(m, sp.split_year, "pnl_price_net"), "price_gross": _period_stats(m, sp.split_year, "pnl_price_gross")}
        out["per_param_no_swap"] = {f"p{i}": _period_stats(cells[cells["param"] == i], sp.split_year, "pnl_price_net") for i, _ in enumerate(sp.params)}
        out["per_sym_main"] = {s: {"net": _period_stats(m[m["sym"] == s], sp.split_year), "swap_bp": fmt(float(np.nanmean(m.loc[m["sym"] == s, "swap"].to_numpy())))}
                               for s in sorted(m["sym"].unique())}
        yr = m.groupby("year")[["swap", "markup", "pnl_price_net", "pnl_net", "exp"]].mean()
        out["by_year_main"] = {int(y): {k: fmt(v) for k, v in row.items()} for y, row in yr.iterrows()}
        return out
    return _extra


def judge_s09(res, spec):
    """S09 の 3 分岐（Q389〜Q392 共通・事前固定）。
    支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main・スワップ込み）の全期間 z≥2。
    棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。スワップ抜き（no_swap）・副設定・銘柄別は記述（判定に使わない）。"""
    m = res.get("main", {}); rm = res.get("rule_mode", {}); f = rm.get("fintokei", {}); gate = rm.get("gate", {})
    z = (m.get("all") or {}).get("z")
    if z is None or f.get("t_all") is None:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    if z < 1 or f["t_all"] < 0:
        return "棄却: 等金額の全期間 z<1 または 規程モードの t_all<0"
    if gate.get("pass") and z >= 2:
        return "支持: 規程モードで前後半とも t≥2・max_dd≥−6%、かつ等金額の全期間 z≥2"
    return "未確定"


def data_guard(spec, here, min_syms=20):
    """FX22 の D1 と 8 通貨の政策金利が揃っていなければ本番を実行しない（JSON に status=データ待ち を書いて exit 2）。"""
    from fe_core import syms_available, write_result
    ok, missing = syms_available(spec.syms, kind=spec.kind)
    rok, rmissing = rates_available()
    if len(ok) < min_syms or rmissing:
        res = {"status": "データ待ち", "n_ok": len(ok), "n_required": min_syms, "missing": missing, "rates_missing": rmissing,
               "note": "S09 データガード: FX22 の D1 か policy_<CCY>.csv が足りないため本番を実行しない。release で待ちに戻す。"}
        write_result(spec.qid, res, smoke=False, here=here)
        print(f"データ待ち: ok={len(ok)}/{len(spec.syms)} rates_missing={rmissing}")
        sys.exit(2)


def main(spec, strategy, here, null=None):
    """スクリプトの入口。--readme／--idea-row はガードを飛ばす。"""
    av = sys.argv[1:]
    if "--smoke" not in av and "--readme" not in av and "--idea-row" not in av:
        data_guard(spec, here)
    CarryRunner(spec, strategy, judge=judge_s09, null=null, summarize_extra=make_extra(spec), here=here).execute()
