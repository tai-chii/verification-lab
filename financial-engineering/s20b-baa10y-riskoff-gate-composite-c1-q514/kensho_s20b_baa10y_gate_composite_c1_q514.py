#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q514 S20 再登録: S18 Q469 と同じ 4 族・同じ重み（1/4 固定・再正規化しない）で、キャリーと指数 β の 2 族だけを「BAA10Y（Moody's Baa−10 年債） が直近 20 営業日で拡大しているとき（risk-off）は 0」にした合成は、
封印前の規程 C1 の年単位 t が前後半とも 2 以上になり max_dd −6% 以内を保つか。

事前登録 事前登録_q514.md と同一・変更禁止（以下は転記）。Q513（HY OAS が 786 行で実行不能）の入力だけ BAA10Y に差し替えた再登録。

【仮説】
S18 と同じ 4 族・同じ重み（1/4 固定・再正規化しない）で、**キャリーと指数 β の 2 族だけ**を「BAA10Y（Moody's Baa−10 年債） が直近 20 営業日で拡大しているとき（risk-off）は 0」にすると、封印前の規程 C1 の年単位 t が前後半とも 2 以上になり、max_dd −6% 以内を保つ。順張り 2 族（暗号 TSMOM60・FX22 TSMOM60）は触らない（順張りはリスクオフで儲ける側なので）。
- 捨てる予想（支持されない方）: 変化ゲートも S19 と同じく「戻りを捨てる」側に働き、t_pre は 0.97 から上がらない。

【判定（事前固定・変更禁止・3 分岐）】
- 支持: 規程 C1 合成が封印前の前後半とも年単位 t ≥ 2、かつ max_dd ≥ −6%、かつ 等金額の循環シフト帰無に対して z ≥ 2（ゲートのタイミングに意味がある）。
- 棄却: 規程 C1 合成の t_pre が S18 再現値（0.97）以下、**または** ゲート 0 の日のキャリー＋β の平均リターンが正（＝S19 と同じ「戻りを捨てている」）。
- 未確定: それ以外（t_pre は上がったが 2 に届かない等）。未確定なら S20 は閉じ、変化の窓・閾値の掃引は**しない**（事後の掃引）。残る独立標本は封印後の前向きのみ。

【多重比較の本数】
- 合成族の試行: S16（1）＋ S18（1）＋ S20（1）＝ 3。族内の試行は S07 5・S08 2・S09 4・S17 1・S19 1 を引き継ぐ（結果 JSON の n_trials に合成 3・引き継ぎ 13 を分けて書く）。n_tests=1。

【定義】oas_t = BAA10Y（Moody's Baa−10 年債）（FRED BAA10Y・日次 1986〜）の t−2 営業日の値（暦日で前方埋めしない。無い日はゲート 1）。g_t = 0 if (oas_t − oas_{t−20}) > 0 else 1（閾値 0・窓 20 固定・掃引しない）。
　carry_t×g_t、beta_t×g_t、crypto_t・tsmom_t はゲートなし。各族は C1 で size_weights → simulate_portfolio → 1/4 で束ねる。合図 t → 損益 t+1（Q469 の実装のまま）。
【データ】Q469 と同一＋ _データ/raw/credit/BAA10Y.csv（列 date,close・%。取得は _データ/fetch/fetch_fred_credit.py。コーディングの段では実行しない）。封印 2024-07-01 以降は読まない。無ければ status=データ待ち・終了コード 2。2008-01-01 より後に始まっていたら status=データ源不足（first を添える）・終了コード 2。
【帰無】ゲート系列の循環シフト（B=500・min_shift=21）をキャリー・β に掛け直す。z・perm_p・null_summary を JSON に。
【副次（記述のみ）】ゲート 0 の日の比率、ゲート 0 の日のキャリー・β の平均リターン、族間相関、族ごとの t。--gate off（g≡1）は S18 再現。baseline_q469_match に Q469 結果との差を書く（t で ±0.05 超は実装の誤り）。
【実装】Q469 のコピー＋ゲート。fe_core は書き換えない。実行: --smoke --B 5（経路確認）／ python3 kensho_s20_credit_gate_composite_c1_q513.py（本番 B=500）。
"""
import datetime as _dt
import json
import os
import sys
import time as _time
import warnings

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s09_common"))
from fe_core import (load_d1, load_h1, h1_to_d1, syms_available, health, tsmom_pos, pnl_bp, cost_bp_oneway,  # noqa: E402
                     CRYPTO_COST_RT_REL, size_weights, simulate_portfolio, yearly_t, RULES_FINTOKEI, RULES_FINTOKEI_C1, RULES_NONE,
                     tstat, nw_t, sharpe_ann, max_drawdown, fmt, null_summary, holm, circ_shift, parse_args, write_result, Spec, Runner)
from fe_core import _paths as P  # noqa: E402
import s09carry as S9  # noqa: E402

QID = "Q514"
GATED = ("carry", "beta")           # ゲートを掛ける族（順張り 2 族は触らない）
GATE_LAG = 2                        # OAS は t−2 営業日の値（事前固定）
GATE_WINDOW = 20
GATE_THRESHOLD = 0.0
GATE_MIN_SHIFT = GATE_WINDOW + 1
OAS_PATH = ("検証", "_データ", "raw", "credit", "BAA10Y.csv")
BASELINE_T_PRE = 0.97               # S18 Q469 の再現値（事前登録の文）
SEAL = S9.SEAL                      # 2024-07-01（封印。読まない）
START = pd.Timestamp("2010-01-01")  # FX22 を同じ期間で揃える（Q389 と同じ）
SPLIT_YEAR = 2017
FX22 = list(S9.FX22)
CRYPTO2 = list(P.CRYPTO2)
L_TSMOM = 60
WARMUP = 120
MIN_SHIFT = 120
FAMILIES = ("carry", "crypto", "tsmom", "beta")
FAMILY_WEIGHT = {f: 1.0 / len(FAMILIES) for f in FAMILIES}     # 事前固定・1/4・再正規化しない
FAMILY_TRIALS_INHERITED = {"S07": 5, "S08": 2, "S09": 4, "S17": 1, "S19": 1}   # 引き継ぎ 13（Q514 事前登録。合成 3 は S16・S18・S20。Q513 は未実行で数えない）
COMPOSITE_TRIALS = 3
RULES_GATE = RULES_FINTOKEI_C1          # ★C1（2026-10-23）: σ 目標 0.25%/日
RETARGET_SIGMA = RULES_GATE["port_sigma_target"]  # 副次の再目標化（0.25%/日）
IDX10 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "AUS200", "SUI20"]   # Q468 と同じ（穴のある NLD25/EUSTX50/HKG33 は除外）
START_BETA = pd.Timestamp("2012-02-01")   # Q468 と同じ（US500/USTECH の 2011-12 の穴の後）
HOLD_BETA = 0.04                           # β 族の保有コスト年率（Q468 と同じ）
RETARGET_MAX_SCALE = 3.0

SPEC = {
    "qid": QID,
    "question": "S18 と同じ 4 族・同じ重みで、キャリーと指数 β の 2 族だけを BAA10Y（Moody's Baa−10 年債） の 20 営業日拡大（risk-off）の間 0 にした合成は、規程 C1 で封印前の前後半とも年単位 t≥2 かつ max_dd≥−6% か（合成 1 本のみ・掃引しない）",
    "hypothesis": "S18 と同じ 4 族・同じ重み（1/4 固定・再正規化しない）で、キャリーと指数 β の 2 族だけを「BAA10Y（Moody's Baa−10 年債） が直近 20 営業日で拡大しているとき（risk-off）は 0」にすると、封印前の規程 C1 の年単位 t が前後半とも 2 以上になり、max_dd −6% 以内を保つ。順張り 2 族（暗号 TSMOM60・FX22 TSMOM60）は触らない（順張りはリスクオフで儲ける側なので）。捨てる予想: 変化ゲートも S19 と同じく「戻りを捨てる」側に働き、t_pre は 0.97 から上がらない",
    "reject_if": "支持: 規程 C1 合成が封印前の前後半とも年単位 t ≥ 2、かつ max_dd ≥ −6%、かつ 等金額の循環シフト帰無に対して z ≥ 2（ゲートのタイミングに意味がある）。棄却: 規程 C1 合成の t_pre が S18 再現値（0.97）以下、または ゲート 0 の日のキャリー＋β の平均リターンが正（＝S19 と同じ「戻りを捨てている」）。未確定: それ以外（t_pre は上がったが 2 に届かない等）。未確定なら S20 は閉じ、変化の窓・閾値の掃引はしない（事後の掃引）。残る独立標本は封印後の前向きのみ",
    "families": {"carry": {"syms": FX22, "signal": "sign(policy_rate_diff, lag 1 暦日) × g", "swap": f"金利差 − 年 {S9.MARKUP_ANNUAL:.2%} マークアップ", "ref": "Q389 main"},
                 "crypto": {"syms": CRYPTO2, "signal": f"tsmom L={L_TSMOM}（ゲートなし）", "kind": "H1→D1 cutoff 0（土日込み）", "cost": "往復 30 bp", "ref": "Q385 main"},
                 "tsmom": {"syms": FX22, "signal": f"tsmom L={L_TSMOM}（ゲートなし）", "swap": "なし（Q367 の定義）", "ref": "Q367 FX 族"},
                 "beta": {"syms": IDX10, "signal": "常時 +1 × g", "start": str(START_BETA.date()), "hold_cost_annual": HOLD_BETA, "ref": "Q468 params 1（指数のみ）"}},
    "gate": {"source": "FRED BAA10Y", "lag_days": GATE_LAG, "window": GATE_WINDOW, "threshold": GATE_THRESHOLD}, "replaces": "Q513",
    "baseline": "Q469", "null_kind": f"ゲート系列の循環シフト min_shift={GATE_MIN_SHIFT}（キャリー・β に掛け直す）",
    "weights": FAMILY_WEIGHT, "renormalize_when_missing": False, "seal": str(SEAL.date()), "start": str(START.date()), "split_year": SPLIT_YEAR,
    "warmup": WARMUP, "rule_set": "fintokei_c1", "rules_fintokei": dict(RULES_GATE), "rules_none": dict(RULES_NONE), "B": 500, "n_tests": 1,
    "family_trials_inherited": FAMILY_TRIALS_INHERITED, "trials_this": 1,
    "discarded": "5（夜間プレミアム／キャリー精密化／COT／VIX 水準ゲートの合成適用／MOVE）",
    "knowledge_cutoff": "設計者（Fable）の知識は 2026-06。FRED の系列 ID・更新遅れは 2026-10-25 時点の知識。実行者は fetch 後に manifest.json の first/last と遅れを原典と照合する",
    "delegation": "Fable 設計・Sonnet コード（lab_code）・lab 実行",
    "designer": "Fable", "coder": "Sonnet", "batch": "週次設計 2026-10-25（Fable・最小ループの 1 回目）",
}

_COSTER = Runner(Spec(qid=QID, question="", hypothesis="", reject_if=""), None)   # Runner._cost の既定（COST_RT → スプレッド中央値 → 暗号 30 bp）だけ借りる


# ---------------------------------------------------------------- 読み込み
def load_fx(sym, smoke, rng):
    df = load_d1(sym, smoke, rng)
    df = df[(df["time"] >= START) & (df["time"] < SEAL)].reset_index(drop=True)
    df["carry_diff"] = S9.rate_diff(sym, df["time"].values, smoke=smoke, rng=rng)
    return df


def load_crypto(sym, smoke, rng):
    df = h1_to_d1(load_h1(sym, smoke, rng), 0)
    return df[df["time"] < SEAL].reset_index(drop=True)


def load_idx(sym, smoke, rng):
    df = load_d1(sym, smoke, rng)
    return df[(df["time"] >= START_BETA) & (df["time"] < SEAL)].reset_index(drop=True)


def fx_cost_bp(sym, close):
    return _COSTER._cost(sym, close)


def crypto_cost_bp(sym, close):
    return cost_bp_oneway(sym, close, rel=CRYPTO_COST_RT_REL)


# ---------------------------------------------------------------- ゲート（BAA10Y（Moody's Baa−10 年債））
class Gate:
    """OAS 営業日系列から作った g（0 = 休む / 1 = 通常）。営業日の index 上。D1 の日付に写すとき、OAS の無い日は 1。"""

    def __init__(self, dates, g):
        self.dates = pd.DatetimeIndex(dates); self.g = np.asarray(g, float)

    def on_dates(self, times, arr=None):
        g = self.g if arr is None else np.asarray(arr, float)
        ser = pd.Series(g, index=self.dates)
        return ser.reindex(pd.DatetimeIndex(pd.to_datetime(times)).floor("D")).fillna(1.0).to_numpy()


def make_gate(oas, off=False):
    """oas: Series（営業日 index・%）。t−2 営業日の値（位置ずらし）の 20 営業日差分 > 0 なら 0。封印以降は読まない。"""
    oas = oas[oas.index < SEAL].dropna()
    lag = oas.shift(GATE_LAG)
    d = lag - lag.shift(GATE_WINDOW)
    g = np.where(d.to_numpy() > GATE_THRESHOLD, 0.0, 1.0)      # NaN は比較が False → 1（休まない）
    if off:
        g = np.ones(len(g))
    keep = oas.index >= START
    return Gate(oas.index[keep], g[keep])


def load_oas(smoke, rng):
    if smoke:
        idx = pd.bdate_range("2009-06-01", "2024-06-28")
        return pd.Series(4.0 + np.cumsum(rng.normal(0, 0.1, len(idx))), index=idx)
    df = pd.read_csv(P._p(*OAS_PATH))
    df["date"] = pd.to_datetime(df["date"]); df = df.dropna().sort_values("date").drop_duplicates("date")
    return pd.Series(df["close"].astype(float).to_numpy(), index=pd.DatetimeIndex(df["date"]))


def oas_missing():
    return [] if os.path.exists(P._p(*OAS_PATH)) else ["BAA10Y"]


# ---------------------------------------------------------------- 合図（shift しない）
def sig_carry(df):
    pos = np.sign(np.nan_to_num(df["carry_diff"].values.astype(float)))
    pos[: WARMUP + 1] = 0.0
    return pos


def sig_tsmom(df):
    pos = np.asarray(tsmom_pos(df["close"].values, L_TSMOM), float)
    pos[: WARMUP + 1] = 0.0
    return pos


def sig_beta(df):
    pos = np.ones(len(df)); pos[: WARMUP + 1] = 0.0
    return pos


# ---------------------------------------------------------------- 族の表
class Family:
    """1 族 = 銘柄ごとの (df, pos, cost_bp) と、日付の和集合に写すための位置。"""

    def __init__(self, name, dfs, sig_fn, cost_fn, with_swap, hold_cost=0.0, gate=None):
        self.name, self.dfs, self.with_swap, self.hold_cost, self.gate = name, dfs, with_swap, float(hold_cost), gate
        self.syms = list(dfs.keys())
        self.base_pos = {s: sig_fn(df) for s, df in dfs.items()}
        self.pos = {s: (self.base_pos[s] * gate.on_dates(df["time"]) if gate is not None else self.base_pos[s]) for s, df in dfs.items()}
        self.cost = {s: cost_fn(s, df["close"].values) for s, df in dfs.items()}
        idx = pd.DatetimeIndex(sorted(set().union(*[set(pd.to_datetime(df["time"]).dt.floor("D")) for df in dfs.values()])))
        self.index = idx
        self.loc = {s: idx.get_indexer(pd.to_datetime(df["time"]).dt.floor("D")) for s, df in dfs.items()}

    def _sym_pnl(self, s, pos):
        df = self.dfs[s]; c = df["close"].values
        n = pnl_bp(pos, c, self.cost[s]); g = pnl_bp(pos, c, np.zeros(len(c)))
        if self.with_swap:
            carry, mk = S9.swap_bp(pos, df["carry_diff"].values, df["dt_prev_h"].values, S9.MARKUP_ANNUAL)
            n = n + carry - mk; g = g + carry
        if self.hold_cost:   # β 族: |建玉|×年率/252 を毎日引く（Q468 と同じ）
            n = n - np.abs(np.r_[0.0, pos[:-1]]) * self.hold_cost / 252.0 * 1e4
        n[: WARMUP + 1] = np.nan; g[: WARMUP + 1] = np.nan
        return n, g

    def daily_bp(self, g_arr=None):
        """等金額: 銘柄ごとの pnl_bp（コスト後・スワップ込み）を日ごとに銘柄平均。g_arr（ゲート系列を循環シフトしたもの）を渡すとそれで掛け直す（ゲート族のみ）。返り値 (net Series, gross Series)。"""
        N = np.full((len(self.index), len(self.syms)), np.nan); G = N.copy()
        for j, s in enumerate(self.syms):
            pos = self.pos[s] if g_arr is None else self.base_pos[s] * self.gate.on_dates(self.dfs[s]["time"], g_arr)
            n, g = self._sym_pnl(s, pos); N[self.loc[s], j] = n; G[self.loc[s], j] = g
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)   # 全銘柄が NaN の日（warmup・データ前）は NaN のまま（寄与 0 は composite 側で扱う）
            return pd.Series(np.nanmean(N, axis=1), index=self.index), pd.Series(np.nanmean(G, axis=1), index=self.index)

    def rule_mode(self, rules):
        """規程モード（族ごと）: sign(pos) → size_weights → simulate_portfolio。キャリー族は R_adj = R + carry − sign(W_prev)·markup（_s09_common と同じ）。"""
        pos, close, cost, diff = {}, {}, {}, {}
        for s, df in self.dfs.items():
            idx = pd.DatetimeIndex(pd.to_datetime(df["time"]).dt.floor("D"))
            pos[s] = pd.Series(np.sign(np.nan_to_num(self.pos[s])), index=idx); close[s] = pd.Series(df["close"].values, index=idx)
            cost[s] = pd.Series(self.cost[s] / 1e4, index=idx)
            if self.with_swap:
                diff[s] = pd.Series(df["carry_diff"].values, index=idx)
        POS = pd.DataFrame(pos).reindex(self.index).fillna(0.0); C = pd.DataFrame(close).reindex(self.index).ffill()
        R = C.pct_change(fill_method=None); COST = pd.DataFrame(cost).reindex(self.index).ffill().fillna(0.0)
        W = size_weights(POS, R, rules)
        RR = R
        if self.with_swap:
            DIFF = pd.DataFrame(diff).reindex(self.index).ffill()
            days = pd.Series(self.index, index=self.index).diff().dt.total_seconds().fillna(0.0) / 86400.0
            CARRY = DIFF.shift(1).fillna(0.0).div(100.0).mul(days / S9.DAYS_PER_YEAR, axis=0)
            MK = np.sign(W.shift(1).fillna(0.0)).mul(S9.MARKUP_ANNUAL * days / S9.DAYS_PER_YEAR, axis=0)
            RR = R + CARRY - MK
        sim = simulate_portfolio(W, RR, COST, rules, hold_cost=({s_: self.hold_cost for s_ in W.columns} if self.hold_cost else None))
        return sim, W


# ---------------------------------------------------------------- 統計の道具
def year_means(s, min_rows=20):
    """日次系列 s（index=日付）の年ごとの平均（行数 min_rows 未満の年は落とす）。返り値 DataFrame[year, mean, n]。"""
    d = pd.DataFrame({"x": s.dropna()}); d["year"] = d.index.year
    y = d.groupby("year")["x"].agg(["mean", "count"]).rename(columns={"count": "n"})
    return y[y["n"] >= min_rows].reset_index()


def period_slices(s):
    return {"all": s, "pre": s[s.index.year < SPLIT_YEAR], "post": s[s.index.year >= SPLIT_YEAR]}


def year_stats(s):
    out = {}
    for pn, x in period_slices(s).items():
        ym = year_means(x)
        out[pn] = {"n_years": int(len(ym)), "bp": fmt(ym["mean"].mean()) if len(ym) else None, "t_year": fmt(tstat(ym["mean"].to_numpy())),
                   "nw_t": fmt(nw_t(x.dropna().to_numpy(), lag=5)) if x.notna().sum() > 10 else None, "n_days": int(x.notna().sum()),
                   "_raw": float(ym["mean"].mean()) if len(ym) else np.nan}
    return out


def port_stats(port, stops=None, W_gross_median=None, rules=None):
    """simulate_portfolio の port（資金比）から規程モードの鍵名（Runner と同じ）。"""
    pre, post = port[port.index.year < SPLIT_YEAR], port[port.index.year >= SPLIT_YEAR]
    t_all, yt = yearly_t(port); t_pre, _ = yearly_t(pre); t_post, _ = yearly_t(post)
    eq = (1 + port.fillna(0.0)).cumprod(); dd = eq / eq.cummax() - 1
    out = {"t_all": fmt(t_all), "t_pre": fmt(t_pre), "t_post": fmt(t_post),
           "n_years_pre": int(pre.index.year.nunique()), "n_years_post": int(post.index.year.nunique()),
           "nw_t_pre": fmt(nw_t(pre.to_numpy(), lag=5)) if len(pre) > 10 else None, "nw_t_post": fmt(nw_t(post.to_numpy(), lag=5)) if len(post) > 10 else None,
           "mean_bp": fmt(port.mean() * 1e4), "mean_bp_pre": fmt(pre.mean() * 1e4) if len(pre) else None, "mean_bp_post": fmt(post.mean() * 1e4) if len(post) else None,
           "sigma_pct": fmt(port.std() * 100), "sharpe": fmt(sharpe_ann(port.to_numpy())), "sharpe_pre": fmt(sharpe_ann(pre.to_numpy())) if len(pre) > 2 else None,
           "sharpe_post": fmt(sharpe_ann(post.to_numpy())) if len(post) > 2 else None,
           "max_dd": fmt(float(dd.min())) if len(dd) else None, "max_dd_pre": fmt(float((dd[dd.index.year < SPLIT_YEAR]).min())) if len(pre) else None,
           "worst_day": fmt(float(port.min())) if len(port) else None, "n_days": int(len(port)), "years": yt.to_dict(orient="records")}
    if stops is not None:
        out["stops"] = int(stops)
    if W_gross_median is not None:
        out["gross_median"] = fmt(W_gross_median)
    if rules is not None:
        out["rules"] = dict(rules)
    return out


def gate_of(f):
    ok = lambda v: v is not None and v == v  # noqa: E731
    g = {"t_pre_ge2": bool(ok(f["t_pre"]) and f["t_pre"] >= 2), "t_post_ge2": bool(ok(f["t_post"]) and f["t_post"] >= 2),
         "max_dd_within_6pct": bool(ok(f["max_dd"]) and f["max_dd"] >= -0.06)}
    g["pass"] = all(g.values())
    return g


def composite(series_by_family, index):
    """1/len(FAMILIES) ずつ束ねる。族のデータが無い日は寄与 0（再正規化しない）。全族が無い日は NaN。"""
    tot = pd.Series(0.0, index=index); any_ = pd.Series(False, index=index)
    for f, s in series_by_family.items():
        x = s.reindex(index); has = x.notna()
        tot = tot + x.fillna(0.0) * FAMILY_WEIGHT[f]; any_ = any_ | has
    return tot.where(any_)


def retarget(port, target=RETARGET_SIGMA, window=60, max_scale=RETARGET_MAX_SCALE):
    """副次: 合成損益を t−1 までの σ60 で target に再目標化（scale ≤ max_scale）。等リスク合成で縮んだ σ を規程の目標に戻したときの t・DD を見る（判定に使わない）。"""
    sig = port.rolling(window, min_periods=window // 2).std().shift(1)
    scale = (target / sig).replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(upper=max_scale)
    return port * scale, scale


def judge(res):
    f = res["rule_mode"]["fintokei"]; gate = res["rule_mode"]["gate"]
    z = (res["main"].get("all") or {}).get("z")
    g0 = res["extra"]["gate0"]["carry_beta_mean_bp"]
    if f.get("t_pre") is None or g0 is None:
        return "未確定: 計算できない（規程 C1 の t_pre かゲート 0 の日のリターンが不足）"
    if f["t_pre"] <= BASELINE_T_PRE or g0 > 0:
        return "棄却: 規程 C1 合成の t_pre が S18 再現値（0.97）以下、またはゲート 0 の日のキャリー＋β の平均リターンが正（戻りを捨てている）"
    if gate.get("pass") and z is not None and z >= 2:
        return "支持: 規程 C1 合成が封印前の前後半とも t≥2・max_dd≥−6%、かつ等金額のゲート循環シフト帰無に対して z≥2"
    return "未確定: 棄却にも支持にも当たらない（掃引はしない）"


# ---------------------------------------------------------------- 本体
def data_guard(smoke):
    if smoke:
        return {"ok_fx": FX22, "missing_fx": [], "ok_crypto": CRYPTO2, "missing_crypto": [], "rates_missing": [], "ok_idx": IDX10, "missing_idx": [], "oas_missing": []}
    ok_fx, miss_fx = syms_available(FX22, kind="D1_fromH1")
    ok_c, miss_c = syms_available(CRYPTO2, kind="H1_dukascopy")
    _, rmiss = S9.rates_available()
    ok_i, miss_i = syms_available(IDX10, kind="D1_fromH1")
    omiss = oas_missing()
    short_first = None
    if not omiss:   # 開始が遅い系列は「データ源不足」（Q513 の再発防止）。封印前の 2024-05 までも要る
        o = load_oas(False, None)
        if o.index.min() > pd.Timestamp("2008-01-01"):
            short_first = str(o.index.min().date())
        elif o.index[o.index < SEAL].max() < pd.Timestamp("2024-05-01"):
            omiss = ["BAA10Y"]
    if short_first:
        write_result(QID, {"status": "データ源不足", "first": short_first, "missing": ["BAA10Y"],
                           "note": "BAA10Y が 2008-01-01 より後に始まる。manifest.json の first/last を原典と照合する。"}, smoke=False, here=HERE)
        print(f"データ源不足: BAA10Y first={short_first}")
        sys.exit(2)
    g = {"ok_fx": ok_fx, "missing_fx": miss_fx, "ok_crypto": ok_c, "missing_crypto": miss_c, "rates_missing": rmiss, "ok_idx": ok_i, "missing_idx": miss_i, "oas_missing": omiss}
    if len(ok_fx) < 20 or miss_c or rmiss or len(ok_i) < 8 or omiss:
        res = {"status": "データ待ち", "n_ok_fx": len(ok_fx), "missing": miss_fx + miss_c + omiss, "rates_missing": rmiss, "missing_idx": miss_i,
               "note": "S20 データガード: FX22 の D1（20 本以上）・BTC/ETH の H1・政策金利 8 通貨・指数 10（8 本以上）・BAA10Y（_データ/raw/credit/BAA10Y.csv。fetch_fred_credit.py で取得）のどれかが足りないため本番を実行しない。"}
        write_result(QID, res, smoke=False, here=HERE)
        print(f"データ待ち: fx {len(ok_fx)}/22 crypto_missing={miss_c} rates_missing={rmiss} oas_missing={omiss}")
        sys.exit(2)
    return g


def baseline_q469_match(composite_t, fam_t):
    """Q469 の最新の本番結果（s18 フォルダ）と --gate off 相当（ゲート無しの再計算）を比べる。t で ±0.05 超は実装の誤り。"""
    import glob
    d = os.path.join(HERE, "..", "s18-four-family-equal-risk-composite-c1-q469", "results")
    files = sorted(f for f in glob.glob(os.path.join(d, "Q469_result_*.json")))
    if not files:
        return {"status": "Q469 の結果ファイルなし", "match": None}
    q = json.load(open(files[-1], encoding="utf-8")); fq = q.get("rule_mode", {}).get("fintokei", {}); out = {"file": os.path.basename(files[-1]), "diffs": {}}
    for k in ("t_all", "t_pre", "t_post"):
        a, b = composite_t.get(k), fq.get(k)
        out["diffs"][k] = fmt(a - b) if a is not None and b is not None else None
    fa = q.get("extra", {}).get("family_alone", {}).get("fintokei", {})
    for f in ("crypto", "tsmom"):   # ゲートを掛けない族は Q469 と一致するはず
        a, b = fam_t.get(f, {}), fa.get(f, {})
        for k in ("t_all", "t_pre", "t_post"):
            out["diffs"][f"{f}.{k}"] = fmt(a[k] - b[k]) if a.get(k) is not None and b.get(k) is not None else None
    vals = [v for v in out["diffs"].values() if v is not None]
    out["match"] = bool(vals) and all(abs(v) <= 0.05 for v in vals)
    out["note"] = "t で ±0.05 を超えたら実装の誤り（ゲート以外を変えている）。実行者は release で止める"
    return out


def run(args, rng):
    t0 = _time.time()
    guard = data_guard(args.smoke)
    fx_syms = guard["ok_fx"] if not args.smoke else FX22[:6]
    cr_syms = guard["ok_crypto"]
    ix_syms = guard["ok_idx"] if not args.smoke else IDX10[:4]
    dh = None if args.smoke else {"fx22_D1": health(fx_syms, kind="D1_fromH1"), "crypto_H1": health(cr_syms, kind="H1_dukascopy", bar="H1"), "idx10_D1": health(ix_syms, kind="D1_fromH1")}
    fx = {s: load_fx(s, args.smoke, rng) for s in fx_syms}
    cr = {s: load_crypto(s, args.smoke, rng) for s in cr_syms}
    ix = {s: load_idx(s, args.smoke, rng) for s in ix_syms}
    oas = load_oas(args.smoke, rng)
    gate = make_gate(oas, off=(args.gate == "off"))
    fam = {"carry": Family("carry", fx, sig_carry, fx_cost_bp, True, gate=gate),
           "crypto": Family("crypto", cr, sig_tsmom, crypto_cost_bp, False),
           "tsmom": Family("tsmom", fx, sig_tsmom, fx_cost_bp, False),
           "beta": Family("beta", ix, sig_beta, fx_cost_bp, False, hold_cost=HOLD_BETA, gate=gate)}
    fam_off = {"carry": Family("carry", fx, sig_carry, fx_cost_bp, True), "beta": Family("beta", ix, sig_beta, fx_cost_bp, False, hold_cost=HOLD_BETA)}   # ゲート無し（S18 再現・副次）
    index = pd.DatetimeIndex(sorted(set().union(*[set(f.index) for f in fam.values()])))

    # ---- 等金額（帰無の対象）
    eq_net, eq_gross = {}, {}
    for f, F in fam.items():
        eq_net[f], eq_gross[f] = F.daily_bp()
    comp_net = composite(eq_net, index); comp_gross = composite(eq_gross, index)
    obs = year_stats(comp_net); obs_g = year_stats(comp_gross)
    null = {pn: [] for pn in ("all", "pre", "post")}
    for b in range(args.B):
        g_arr = circ_shift(rng, gate.g, min_shift=GATE_MIN_SHIFT)       # ゲートのタイミングだけ壊す（キャリー・β 共通の 1 本）
        nb = {f: (F.daily_bp(g_arr)[0] if f in GATED else eq_net[f]) for f, F in fam.items()}
        ys = year_stats(composite(nb, index))
        for pn in null:
            null[pn].append(ys[pn]["_raw"])
    main = {}
    for pn in ("all", "pre", "post"):
        ns = null_summary(obs[pn]["_raw"], null[pn]) if null[pn] else {"z": None, "pct": None, "p_perm": None, "degenerate": None, "B": 0}
        main[pn] = {k: v for k, v in obs[pn].items() if not k.startswith("_")}
        main[pn].update({"bp_gross": obs_g[pn]["bp"], "t_year_gross": obs_g[pn]["t_year"], "z": fmt(ns["z"]), "pct": fmt(ns["pct"]), "p_perm": fmt(ns["p_perm"]),
                         "null_degenerate": ns["degenerate"], "null_q025": fmt(ns.get("q025")), "null_q500": fmt(ns.get("q500")), "null_q975": fmt(ns.get("q975")),
                         "sharpe_net": fmt(sharpe_ann(period_slices(comp_net)[pn].dropna().to_numpy())),
                         "max_dd_net_bp": fmt(max_drawdown(period_slices(comp_net)[pn].dropna().to_numpy()))})
    main["family_eq"] = {f: {pn: {k: v for k, v in d.items() if not k.startswith("_")} for pn, d in year_stats(s).items()} for f, s in eq_net.items()}

    # ---- 規程モード（族ごと → 1/4 合成）
    rule_mode = {}
    fam_port = {"none": {}, "fintokei": {}}; fam_detail = {"none": {}, "fintokei": {}}; stops_sum = {"none": 0, "fintokei": 0}
    for name, rules in (("none", RULES_NONE), ("fintokei", RULES_GATE)):
        for f, F in fam.items():
            sim, W = F.rule_mode(rules)
            fam_port[name][f] = sim["port"]; stops_sum[name] += int(sim["stops"])
            fam_detail[name][f] = port_stats(sim["port"], stops=sim["stops"], W_gross_median=float(W.abs().sum(axis=1).median()))
        port = composite(fam_port[name], index).fillna(0.0)
        st = port_stats(port, stops=stops_sum[name], rules=rules)
        st["composite_days_below_daily_stop"] = int((port < RULES_GATE["daily_stop"]).sum())
        st["stops_note"] = "stops は族ごとの日次停止の合計（族ごとに規程を当てる設計）。composite_days_below_daily_stop は合成が −2.5% を割った日数（記述）"
        rule_mode[name] = st
    rule_mode["gate"] = gate_of(rule_mode["fintokei"]); rule_mode["rule_set"] = "fintokei_c1"
    rule_mode["split_year"] = SPLIT_YEAR; rule_mode["seal"] = str(SEAL.date()); rule_mode["weights"] = FAMILY_WEIGHT

    # ---- ベースライン（ゲート無し＝S18 再現）。ゲート族だけ差し替えて同じ C1 で束ねる
    base_port = dict(fam_port["fintokei"])
    for f, F in fam_off.items():
        sim, _ = F.rule_mode(RULES_GATE); base_port[f] = sim["port"]
    base_st = port_stats(composite(base_port, index).fillna(0.0), rules=RULES_GATE)
    rule_mode["baseline_gate_off"] = {**base_st, "gate": gate_of(base_st)}
    rule_mode["baseline_q469_match"] = baseline_q469_match(base_st, {f: fam_detail["fintokei"][f] for f in ("crypto", "tsmom")})

    # ---- 副次（記述）: ゲート 0 の日の比率・その日のキャリー・β のリターン
    g_cal = pd.Series(gate.on_dates(index), index=index)
    mask = g_cal.shift(1) == 0            # pos[t]（g_t）は t+1 の損益に効く
    eq_off = {f: F.daily_bp()[0].reindex(index) for f, F in fam_off.items()}
    g0 = {f: {"mean_bp": fmt(float(np.nanmean(eq_off[f][mask]))) if eq_off[f][mask].notna().any() else None,
              "mean_bp_gate1": fmt(float(np.nanmean(eq_off[f][~mask]))) if eq_off[f][~mask].notna().any() else None,
              "n_days_gate0": int(eq_off[f][mask].notna().sum())} for f in GATED}
    vals = [g0[f]["mean_bp"] for f in GATED if g0[f]["mean_bp"] is not None]
    gate0 = {"fraction_oas_days": fmt(float((gate.g == 0).mean())), "fraction_composite_days": fmt(float(mask.mean())),
             "fraction_in_30_55": bool(0.30 <= float((gate.g == 0).mean()) <= 0.55), "by_family_ungated_eq": g0,
             "carry_beta_mean_bp": fmt(float(sum(vals))) if vals else None,
             "note": "ゲート 0 の日（翌日の損益）にゲート無しのキャリー・β が稼いだ平均 bp（等金額・コスト後）。正なら戻りを捨てている。30〜50% を外れたら差分の向き・遅れを疑う"}
    fp = fam_port["fintokei"]
    P_ = pd.DataFrame({f: s.reindex(index) for f, s in fp.items()})
    both = P_.notna()
    corr_d = P_.corr(min_periods=250)
    M_ = P_.resample("ME").sum(min_count=1); corr_m = M_.corr(min_periods=24)
    contrib = {f: {"mean_bp_weighted": fmt(P_[f].fillna(0.0).mean() * FAMILY_WEIGHT[f] * 1e4), "n_days": int(both[f].sum()),
                   "first": str(P_[f].dropna().index.min().date()) if both[f].any() else None, "last": str(P_[f].dropna().index.max().date()) if both[f].any() else None}
               for f in FAMILIES}
    comp_f = composite(fp, index).fillna(0.0)
    extra = {"gate0": gate0, "family_alone": {"fintokei": fam_detail["fintokei"], "none": fam_detail["none"]},
             "family_corr_daily": corr_d.round(4).to_dict(), "family_corr_monthly": corr_m.round(4).to_dict(), "contribution_fintokei": contrib,
             "n_syms": {"carry": len(fx), "crypto": len(cr), "tsmom": len(fx), "beta": len(ix)}, "guard": guard,
             "oas_span": {"first": str(gate.dates.min().date()), "last": str(gate.dates.max().date()), "n": int(len(gate.dates))}}
    n_inh = sum(FAMILY_TRIALS_INHERITED.values())
    res = {"question": SPEC["question"], "spec": SPEC, "gate_mode": args.gate, "missing": guard["missing_fx"] + guard["missing_crypto"] + guard["missing_idx"] + guard["oas_missing"],
           "data_health": dh, "main": main, "rule_mode": rule_mode, "extra": extra,
           "baseline_q469_match": rule_mode["baseline_q469_match"],
           "null_summary": {k: main["all"][k] for k in ("z", "pct", "p_perm", "null_q025", "null_q500", "null_q975", "null_degenerate")},
           "perm_p": main["all"]["p_perm"], "z": main["all"]["z"],
           "max_dd": rule_mode["fintokei"]["max_dd"], "worst_day": rule_mode["fintokei"]["worst_day"], "stops": rule_mode["fintokei"]["stops"],
           "rule_mode_name": "fintokei_c1", "gate_result": rule_mode["gate"],
           "n_trials": {"composite": COMPOSITE_TRIALS, "inherited": n_inh, "inherited_detail": FAMILY_TRIALS_INHERITED, "this": 1},
           "multiple_comparisons": f"判定は合成 1 本（n_tests=1・Holm 不要）。合成の試行 {COMPOSITE_TRIALS}（S16・S18・S20）、族内の引き継ぎ {n_inh}",
           "elapsed_s": round(_time.time() - t0, 1)}
    res["rule_mode"]["rule_mode"] = "fintokei_c1"
    res["machine_verdict"] = judge(res)
    if args.gate == "off":
        res["machine_verdict"] += "（--gate off: S18 再現用。判定に使わない）"
    if dh and any((v["failed"] or v["gaps"]) for v in dh.values()):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    rows = []
    for f in FAMILIES:
        a = year_means(eq_net[f]).set_index("year")["mean"]; b = year_means(fp[f] * 1e4).set_index("year")["mean"]
        for y in sorted(set(a.index) | set(b.index)):
            rows.append({"family": f, "year": int(y), "eq_bp": a.get(y, np.nan), "fintokei_bp": b.get(y, np.nan)})
    a = year_means(comp_net).set_index("year")["mean"]; b = year_means(comp_f * 1e4).set_index("year")["mean"]
    for y in sorted(set(a.index) | set(b.index)):
        rows.append({"family": "composite", "year": int(y), "eq_bp": a.get(y, np.nan), "fintokei_bp": b.get(y, np.nan)})
    daily = pd.DataFrame({"time": index, "gate": g_cal.values, "eq_composite_bp": comp_net.values, "fintokei_composite": comp_f.values, **{f"fintokei_{f}": fp[f].reindex(index).values for f in FAMILIES}})
    return res, {"year_family": pd.DataFrame(rows), "daily_composite": daily}


def main():
    args = parse_args(default_B=SPEC["B"], extra=lambda ap: ap.add_argument("--gate", choices=["on", "off"], default="on", help="off: g≡1（S18 再現）"))
    rng = np.random.default_rng(args.seed)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{QID}" if args.smoke else QID
    with open(os.path.join(out, f"{pre}_spec_{ts}.json"), "w", encoding="utf-8") as fh:   # 事前登録を先に書く
        json.dump({"registered": ts, "B": args.B, "seed": args.seed, **SPEC}, fh, ensure_ascii=False, indent=1, default=str)
    res, csvs = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    path = write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res["machine_verdict"]); print("wrote", path)


if __name__ == "__main__":
    main()
