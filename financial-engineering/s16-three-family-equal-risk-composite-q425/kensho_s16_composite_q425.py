#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q425 S16: 弱い正の 3 族（キャリー符号 FX22〔Q389〕・BTC/ETH TSMOM60〔Q385〕・FX22 TSMOM60〔Q367 の FX 族〕）を事前固定の
等リスク 1/3 合成にした 1 本は、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か。合成 1 本のみ・掃引しない。

【出典】[[検証/_基盤/戦略台帳]] S16（taichi 方針 B・2026-10-22 15:50）／要対応 2026-10-22 13:55・15:50・15:55／Q389（キャリー符号・等金額 z 2.94・規程 t_all 0.72・max_dd −22%）
　／Q385（BTC+ETH TSMOM60・規程〔暗号版 split 2021〕t_pre 2.33・t_post 2.13・max_dd −13.4%）／Q367（S07 本体・FX 族は粗利小さく正）
　／Q416（関門の通過確率: σ0.5%/日の単一系列では年率シャープ ≈2.7 で P(通過)=0.5）／Clare・Seaton・Smith・Thomas 2015（キャリー＋トレンドの合成で DD が浅い・1981〜2012）
　／Koijen・Moskowitz・Pedersen・Vrugt 2018 'Carry'／Moskowitz・Ooi・Pedersen 2012 TSMOM。
【仮説】単一の族は規程モードの max_dd −6% に届かない（S02・S04b・S07・S08・S09 の最良で −13〜−39%）。相関の低い 3 族（キャリー・暗号順張り・FX 順張り）の
　規程モード損益を 1/3 ずつ束ねると、各族の σ 目標 0.5%/日 に対して合成の σ は √((1+2ρ̄)/3) 倍に縮み（ρ̄ は平均相関）、t は族の平均が正なら上がり、
　最大下落は −6% 以内に収まる。族と重みは結果を見る前に固定（1/3・再正規化なし）。
【データ】FX22（8 通貨の 22 ペア）の D1_fromH1（2010-01-01〜・封印 time<2024-07-01。FX8 は 学問/…/システムトレード、14 クロスは _データ/raw/D1）。
　BTCUSD（H1 2017-05〜）・ETHUSD（H1 2017-12〜）の H1_dukascopy を h1_to_d1（UTC 0 時区切り・土日込み）で日足に（Q385 と同じ）。
　政策金利: _データ/raw/rates/policy_<CCY>.csv（BIS・8 通貨・時刻 t の金利差は t−1 暦日に実施中の値＝Q389 と同じ）。
　コスト: FX8 は COST_RT（往復 2 pips）、14 クロスは spread_<sym>.csv の中央値（Runner._cost の既定＝Q384/Q389 と同じ）、BTC/ETH は往復 30 bp（Q385 main）。
　キャリー族のスワップ: 金利差 − 年 0.75% マークアップ（Q389 と同じ・_s09_common.swap_bp）。TSMOM 族（FX22）はスワップ無し（Q367 の定義のまま）。
【定義】族 A（carry）: pos=sign(i_base − i_quote)（band 0）。族 B（crypto）: pos=sign(close[t]−close[t−60])（BTC・ETH）。族 C（tsmom）: 同じ TSMOM60 を FX22 に。
　いずれも warmup 120 本は pos=0。規程モード: 各族ごとに size_weights(RULES_FINTOKEI)（σ 目標 0.5%/日・1 銘柄 1.5%・レバ 2・日次 −2.5% 停止）→ simulate_portfolio → 族の日次損益 port_f。
　合成 port = (1/3)·Σ_f port_f（族のデータが無い日・期間は寄与 0。重みは再正規化しない。土日は暗号族だけが動く）。
　等金額（帰無用）: 各族の銘柄ごとの pnl_bp（コスト後・キャリーはスワップ込み）を日ごとに銘柄平均し、同じ 1/3 で束ねた日次 bp。
【測るもの】規程モード合成の年単位 t（全期間／前半 <2017／後半 ≥2017）・mean_bp・σ・Sharpe・max_dd・worst_day・停止（族ごとの合計と合成が −2.5% を割った日数）・gate。
　等金額合成の年単位 bp・年単位 t・束ねた nw_t・Sharpe・max_dd・帰無 z・perm_p。
　副次（記述・判定に使わない）: 各族単独の規程モード（t_all/t_pre/t_post/max_dd/Sharpe）、族間の日次・月次損益相関、各族の寄与（mean_bp の分解）、
　合成を σ60（t−1 までの情報）で 0.5%/日 に再目標化した版の t・max_dd（C〔DD 条件の見直し〕の材料。レバ上限 3 倍）、族の有効年数、引き継いだ族内試行数 11 での Bonferroni p。
【帰無】族ごとに固有の帰無を同時に引く（B=500）: 族 A は銘柄ごとの符号反転（Q389 と同じ・循環シフトでは帰無が観測と一致しうる）、族 B・C は合図の循環シフト（min_shift=120）。
　→ 等金額合成の年単位平均 bp（全期間・前半・後半）の帰無分布 → z・perm_p。Holm は前後半の 2 本（m=2・記述）。判定に使う検定は全期間 z の 1 本（n_tests=1）。
【判定（事前固定・変更禁止）】支持: 規程モード合成（封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額合成の全期間 z≥2。
　棄却: 等金額合成の全期間 z<1、または規程モード合成の t_all<0。ほか → 未確定。副次は判定に使わない。
　不通過なら S16 は閉じ、要対応に「C（DD 条件の見直し）」を ★ で taichi に提案する（台帳 S16 (4)）。通れば初の採用候補（フォワードへ）。封印（2024-07〜）は開けない。
【捨てた案の数】4（族の重みを σ やシャープで最適化＝事後の掃引／4 族目（指数の買い持ち β）を足す＝台帳の 3 族固定に反する／1 冊の建玉表に合算して規程モードを 1 回かける＝
　族の等リスクが崩れる（FX 44 スロット対 暗号 2）ので副次にも入れない／キャリー族と TSMOM 族で FX22 の合図が逆のとき相殺を数えない＝族ごとの損益を束ねる設計なら自然に相殺される）。
【多重比較】この案の試行は 1。族内の試行は S07 5＋S08 2＋S09 4＝11 を引き継ぎ、本件で 12。結果 JSON に family_trials_inherited を書く。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない。検証期間は封印前（〜2024-06）のみ。
【委託の確かめ方】なし（Fable 設計・コード → Sonnet 実行）。
【実装】土台（fe_core）を直接使う型。金利差・スワップ・符号反転帰無は _s09_common/s09carry.py を再利用。コストは Runner._cost（Q384 と同じ既定）。
　実行: --smoke --B 5（経路確認）／ python3 kensho_s16_composite_q425.py（本番 B=500）。データガード: FX22 が 20 本未満・BTC/ETH の H1・政策金利 8 通貨のどれかが無ければ
　status=データ待ち を書いて exit 2。
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
                     CRYPTO_COST_RT_REL, size_weights, simulate_portfolio, yearly_t, RULES_FINTOKEI, RULES_NONE,
                     tstat, nw_t, sharpe_ann, max_drawdown, fmt, null_summary, holm, circ_shift, parse_args, write_result, Spec, Runner)
from fe_core import _paths as P  # noqa: E402
import s09carry as S9  # noqa: E402

QID = "Q425"
SEAL = S9.SEAL                      # 2024-07-01（封印。読まない）
START = pd.Timestamp("2010-01-01")  # FX22 を同じ期間で揃える（Q389 と同じ）
SPLIT_YEAR = 2017
FX22 = list(S9.FX22)
CRYPTO2 = list(P.CRYPTO2)
L_TSMOM = 60
WARMUP = 120
MIN_SHIFT = 120
FAMILIES = ("carry", "crypto", "tsmom")
FAMILY_WEIGHT = {f: 1.0 / 3.0 for f in FAMILIES}     # 事前固定・再正規化しない
FAMILY_TRIALS_INHERITED = {"S07": 5, "S08": 2, "S09": 4}
RETARGET_SIGMA = RULES_FINTOKEI["port_sigma_target"]  # 副次の再目標化（0.5%/日）
RETARGET_MAX_SCALE = 3.0

SPEC = {
    "qid": QID,
    "question": "弱い正の 3 族（キャリー符号 FX22・BTC/ETH TSMOM60・FX22 TSMOM60）を事前固定の等リスク 1/3 合成にした 1 本は、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か（合成 1 本のみ・掃引しない）",
    "hypothesis": "相関の低い 3 族の規程モード損益（各 σ 目標 0.5%/日）を 1/3 ずつ束ねると合成の σ が縮み、t は上がり、最大下落は −6% 以内に収まる。族と重みは結果を見る前に固定",
    "reject_if": "支持: 規程モード合成（封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額合成の全期間 z≥2（族ごとの帰無: キャリーは符号反転・順張りは循環シフト）。棄却: 等金額合成の全期間 z<1、または規程モード合成の t_all<0。ほか → 未確定。副次（族単独・相関・再目標化）は判定に使わない。不通過なら S16 を閉じ C（DD 条件の見直し）を ★ で提案",
    "families": {"carry": {"syms": FX22, "signal": "sign(policy_rate_diff, lag 1 暦日)", "swap": f"金利差 − 年 {S9.MARKUP_ANNUAL:.2%} マークアップ", "null": "signflip per sym", "ref": "Q389 main"},
                 "crypto": {"syms": CRYPTO2, "signal": f"tsmom L={L_TSMOM}", "kind": "H1→D1 cutoff 0（土日込み）", "cost": "往復 30 bp", "null": f"circ_shift min_shift={MIN_SHIFT}", "ref": "Q385 main"},
                 "tsmom": {"syms": FX22, "signal": f"tsmom L={L_TSMOM}", "swap": "なし（Q367 の定義）", "null": f"circ_shift min_shift={MIN_SHIFT}", "ref": "Q367 FX 族"}},
    "weights": FAMILY_WEIGHT, "renormalize_when_missing": False, "seal": str(SEAL.date()), "start": str(START.date()), "split_year": SPLIT_YEAR,
    "warmup": WARMUP, "rules_fintokei": dict(RULES_FINTOKEI), "rules_none": dict(RULES_NONE), "B": 500, "n_tests": 1,
    "family_trials_inherited": FAMILY_TRIALS_INHERITED, "trials_this": 1,
    "discarded": "4（重みの最適化／4 族目 β／1 冊合算／相殺の数え方）",
    "knowledge_cutoff": "Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない",
    "delegation": "なし（Fable 設計・コード → Sonnet 実行）",
    "designer": "Fable", "coder": "Fable", "batch": "/lab-plan ターミナル版 2026-10-22 夜・3 回目（N=10 のうち S16 本体の 1 件のみ）",
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


def fx_cost_bp(sym, close):
    return _COSTER._cost(sym, close)


def crypto_cost_bp(sym, close):
    return cost_bp_oneway(sym, close, rel=CRYPTO_COST_RT_REL)


# ---------------------------------------------------------------- 合図（shift しない）
def sig_carry(df):
    pos = np.sign(np.nan_to_num(df["carry_diff"].values.astype(float)))
    pos[: WARMUP + 1] = 0.0
    return pos


def sig_tsmom(df):
    pos = np.asarray(tsmom_pos(df["close"].values, L_TSMOM), float)
    pos[: WARMUP + 1] = 0.0
    return pos


# ---------------------------------------------------------------- 族の表
class Family:
    """1 族 = 銘柄ごとの (df, pos, cost_bp) と、日付の和集合に写すための位置。"""

    def __init__(self, name, dfs, sig_fn, cost_fn, with_swap, null_fn):
        self.name, self.dfs, self.with_swap, self.null_fn = name, dfs, with_swap, null_fn
        self.syms = list(dfs.keys())
        self.pos = {s: sig_fn(df) for s, df in dfs.items()}
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
        n[: WARMUP + 1] = np.nan; g[: WARMUP + 1] = np.nan
        return n, g

    def daily_bp(self, rng=None):
        """等金額: 銘柄ごとの pnl_bp（コスト後・スワップ込み）を日ごとに銘柄平均。rng を渡すと族固有の帰無で合図を壊してから。返り値 (net Series, gross Series)。"""
        N = np.full((len(self.index), len(self.syms)), np.nan); G = N.copy()
        for j, s in enumerate(self.syms):
            pos = self.pos[s] if rng is None else self.null_fn(rng, self.pos[s])
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
        sim = simulate_portfolio(W, RR, COST, rules)
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
    """1/3 ずつ束ねる。族のデータが無い日は寄与 0（再正規化しない）。全族が無い日は NaN。"""
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
    m = res["main"]; f = res["rule_mode"]["fintokei"]; gate = res["rule_mode"]["gate"]
    z = (m.get("all") or {}).get("z")
    if z is None or f.get("t_all") is None:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    if z < 1 or f["t_all"] < 0:
        return "棄却: 等金額合成の全期間 z<1 または 規程モード合成の t_all<0"
    if gate.get("pass") and z >= 2:
        return "支持: 規程モード合成で前後半とも t≥2・max_dd≥−6%、かつ等金額合成の全期間 z≥2"
    return "未確定"


# ---------------------------------------------------------------- 本体
def data_guard(smoke):
    if smoke:
        return {"ok_fx": FX22, "missing_fx": [], "ok_crypto": CRYPTO2, "missing_crypto": [], "rates_missing": []}
    ok_fx, miss_fx = syms_available(FX22, kind="D1_fromH1")
    ok_c, miss_c = syms_available(CRYPTO2, kind="H1_dukascopy")
    _, rmiss = S9.rates_available()
    g = {"ok_fx": ok_fx, "missing_fx": miss_fx, "ok_crypto": ok_c, "missing_crypto": miss_c, "rates_missing": rmiss}
    if len(ok_fx) < 20 or miss_c or rmiss:
        res = {"status": "データ待ち", "n_ok_fx": len(ok_fx), "missing": miss_fx + miss_c, "rates_missing": rmiss,
               "note": "S16 データガード: FX22 の D1（20 本以上）・BTC/ETH の H1・政策金利 8 通貨のどれかが足りないため本番を実行しない。release で待ちに戻す。"}
        write_result(QID, res, smoke=False, here=HERE)
        print(f"データ待ち: fx {len(ok_fx)}/22 crypto_missing={miss_c} rates_missing={rmiss}")
        sys.exit(2)
    return g


def run(args, rng):
    t0 = _time.time()
    guard = data_guard(args.smoke)
    fx_syms = guard["ok_fx"] if not args.smoke else FX22[:6]
    cr_syms = guard["ok_crypto"]
    dh = None if args.smoke else {"fx22_D1": health(fx_syms, kind="D1_fromH1"), "crypto_H1": health(cr_syms, kind="H1_dukascopy", bar="H1")}
    fx = {s: load_fx(s, args.smoke, rng) for s in fx_syms}
    cr = {s: load_crypto(s, args.smoke, rng) for s in cr_syms}
    fam = {"carry": Family("carry", fx, sig_carry, fx_cost_bp, True, lambda r, p: S9.null_signflip(r, p, None, None, None)),
           "crypto": Family("crypto", cr, sig_tsmom, crypto_cost_bp, False, lambda r, p: circ_shift(r, p, min_shift=MIN_SHIFT)),
           "tsmom": Family("tsmom", fx, sig_tsmom, fx_cost_bp, False, lambda r, p: circ_shift(r, p, min_shift=MIN_SHIFT))}
    index = pd.DatetimeIndex(sorted(set().union(*[set(f.index) for f in fam.values()])))

    # ---- 等金額（帰無の対象）
    eq_net, eq_gross = {}, {}
    for f, F in fam.items():
        eq_net[f], eq_gross[f] = F.daily_bp()
    comp_net = composite(eq_net, index); comp_gross = composite(eq_gross, index)
    obs = year_stats(comp_net); obs_g = year_stats(comp_gross)
    null = {pn: [] for pn in ("all", "pre", "post")}
    for b in range(args.B):
        nb = {f: F.daily_bp(rng)[0] for f, F in fam.items()}
        ys = year_stats(composite(nb, index))
        for pn in null:
            null[pn].append(ys[pn]["_raw"])
    main = {}; pvals = {}
    for pn in ("all", "pre", "post"):
        ns = null_summary(obs[pn]["_raw"], null[pn]) if null[pn] else {"z": None, "pct": None, "p_perm": None, "degenerate": None, "B": 0}
        main[pn] = {k: v for k, v in obs[pn].items() if not k.startswith("_")}
        main[pn].update({"bp_gross": obs_g[pn]["bp"], "t_year_gross": obs_g[pn]["t_year"], "z": fmt(ns["z"]), "pct": fmt(ns["pct"]), "p_perm": fmt(ns["p_perm"]),
                         "null_degenerate": ns["degenerate"], "null_q025": fmt(ns.get("q025")), "null_q500": fmt(ns.get("q500")), "null_q975": fmt(ns.get("q975")),
                         "sharpe_net": fmt(sharpe_ann(period_slices(comp_net)[pn].dropna().to_numpy())),
                         "max_dd_net_bp": fmt(max_drawdown(period_slices(comp_net)[pn].dropna().to_numpy()))})
        if pn in ("pre", "post"):
            pvals[pn] = ns["p_perm"] if ns["p_perm"] is not None else np.nan
    if pvals:
        adj = holm(list(pvals.values()))
        for (pn, _), a in zip(pvals.items(), adj):
            main[pn]["p_holm"] = fmt(a)
    n_inh = sum(FAMILY_TRIALS_INHERITED.values()) + 1
    main["all"]["p_bonf_family12"] = fmt(min(1.0, main["all"]["p_perm"] * n_inh)) if main["all"]["p_perm"] is not None else None
    main["family_eq"] = {f: {pn: {k: v for k, v in d.items() if not k.startswith("_")} for pn, d in year_stats(s).items()} for f, s in eq_net.items()}

    # ---- 規程モード（族ごと → 1/3 合成）
    rule_mode = {}
    fam_port = {"none": {}, "fintokei": {}}; fam_detail = {"none": {}, "fintokei": {}}; stops_sum = {"none": 0, "fintokei": 0}
    for name, rules in (("none", RULES_NONE), ("fintokei", RULES_FINTOKEI)):
        for f, F in fam.items():
            sim, W = F.rule_mode(rules)
            fam_port[name][f] = sim["port"]; stops_sum[name] += int(sim["stops"])
            fam_detail[name][f] = port_stats(sim["port"], stops=sim["stops"], W_gross_median=float(W.abs().sum(axis=1).median()))
        port = composite(fam_port[name], index).fillna(0.0)
        st = port_stats(port, stops=stops_sum[name], rules=rules)
        st["composite_days_below_daily_stop"] = int((port < RULES_FINTOKEI["daily_stop"]).sum())
        st["stops_note"] = "stops は族ごとの日次停止の合計（族ごとに規程を当てる設計）。composite_days_below_daily_stop は合成が −2.5% を割った日数（記述）"
        rule_mode[name] = st
    rule_mode["gate"] = gate_of(rule_mode["fintokei"])
    rule_mode["split_year"] = SPLIT_YEAR; rule_mode["seal"] = str(SEAL.date()); rule_mode["weights"] = FAMILY_WEIGHT

    # ---- 副次（記述）
    fp = fam_port["fintokei"]
    P_ = pd.DataFrame({f: s.reindex(index) for f, s in fp.items()})
    both = P_.notna()
    corr_d = P_.corr(min_periods=250)
    M_ = P_.resample("ME").sum(min_count=1); corr_m = M_.corr(min_periods=24)
    contrib = {f: {"mean_bp_weighted": fmt(P_[f].fillna(0.0).mean() * FAMILY_WEIGHT[f] * 1e4), "n_days": int(both[f].sum()),
                   "first": str(P_[f].dropna().index.min().date()) if both[f].any() else None, "last": str(P_[f].dropna().index.max().date()) if both[f].any() else None}
               for f in FAMILIES}
    comp_f = composite(fp, index).fillna(0.0)
    rt_port, rt_scale = retarget(comp_f)
    rho_bar = float(np.nanmean([corr_d.loc[a, b] for i, a in enumerate(FAMILIES) for b in FAMILIES[i + 1:]]))
    extra = {"family_alone": {"fintokei": fam_detail["fintokei"], "none": fam_detail["none"]},
             "family_corr_daily": corr_d.round(4).to_dict(), "family_corr_monthly": corr_m.round(4).to_dict(), "rho_bar_daily": fmt(rho_bar),
             "sigma_shrink_theory": fmt(np.sqrt((1 + 2 * rho_bar) / 3)) if rho_bar == rho_bar else None,
             "contribution_fintokei": contrib,
             "retarget_sigma": {"note": f"合成を t−1 までの σ60 で {RETARGET_SIGMA:.3%}/日 に再目標化（scale ≤ {RETARGET_MAX_SCALE}）。判定に使わない。C（DD 条件）の材料",
                                "scale_median": fmt(float(rt_scale.replace(0, np.nan).median())), **port_stats(rt_port)},
             "retarget_gate_descriptive": gate_of(port_stats(rt_port)),
             "eq_composite_sigma_pct": fmt(comp_net.std() / 1e4 * 100),
             "n_syms": {"carry": len(fx), "crypto": len(cr), "tsmom": len(fx)}, "guard": guard}
    res = {"question": SPEC["question"], "spec": SPEC, "missing": guard["missing_fx"] + guard["missing_crypto"], "data_health": dh,
           "main": main, "rule_mode": rule_mode, "extra": extra,
           "multiple_comparisons": f"判定は合成 1 本（全期間 z と規程 gate）。族内の試行は S07 5＋S08 2＋S09 4＝11 を引き継ぎ本件で {n_inh}（p_bonf_family12 は記述）。前後半の Holm（m=2）は記述",
           "elapsed_s": round(_time.time() - t0, 1)}
    res["machine_verdict"] = judge(res)
    if dh and any((v["failed"] or v["gaps"]) for v in dh.values()):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    # CSV: 年×族（等金額 bp と規程モード bp）・合成
    rows = []
    for f in FAMILIES:
        a = year_means(eq_net[f]).set_index("year")["mean"]; b = year_means(fp[f] * 1e4).set_index("year")["mean"]
        for y in sorted(set(a.index) | set(b.index)):
            rows.append({"family": f, "year": int(y), "eq_bp": a.get(y, np.nan), "fintokei_bp": b.get(y, np.nan)})
    a = year_means(comp_net).set_index("year")["mean"]; b = year_means(comp_f * 1e4).set_index("year")["mean"]
    for y in sorted(set(a.index) | set(b.index)):
        rows.append({"family": "composite", "year": int(y), "eq_bp": a.get(y, np.nan), "fintokei_bp": b.get(y, np.nan)})
    daily = pd.DataFrame({"time": index, "eq_composite_bp": comp_net.values, "fintokei_composite": comp_f.values, **{f"fintokei_{f}": fp[f].reindex(index).values for f in FAMILIES}})
    return res, {"year_family": pd.DataFrame(rows), "daily_composite": daily}


def main():
    args = parse_args(default_B=SPEC["B"])
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
