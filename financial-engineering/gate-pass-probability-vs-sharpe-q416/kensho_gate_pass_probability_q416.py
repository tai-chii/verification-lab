#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q416 基盤: 関門（σ0.5%/日・14 年の最大下落 −6% 以内＋前後半 t≥2）は年率シャープ S がいくら以上の戦略を何割通すか（S07 規程モード損益の 20 日ブロック・ブートストラップで S を 0〜3 に合わせて測る）。

【出典】[[検証/_基盤/戦略台帳]] 段階と関門（OOS 合格: 規程モードで前後半 t≥2・最大下落 −6% 以内）／要対応 2026-10-22 13:55「関門の DD 条件が今の探索の律速」（σ0.5%/日で 14 年の −6% にはシャープ約 1.5 以上要る、の見積り）／Man Group 'You're fired'（10 年・シャープ 0.5 で 2σ の下落に 43% で到達、IID 模擬）／Bailey・López de Prado 2014（最大下落の分布とシャープの関係）
【仮説】関門の「最大下落 −6% 以内」は σ 目標 0.5%/日（年率 約 8%）の下では年率シャープが 1.5 を超えないと半分も通らず、現在の探索（単一族・シャープ 0〜0.5）では方法の良し悪しに関係なく通らない。これが本当なら、関門は戦略の選別ではなく「探索の停止」として働いている。数値を出して taichi の C（関門の置き方）の判断材料にする。
【データ】48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）。TSMOM60（S07 本体）の合図 → RULES_FINTOKEI の size_weights → simulate_portfolio（コストは Runner._cost と同じ: COST_RT／スプレッド中央値／暗号 30 bp）→ 日次損益 port（2010-04〜2024-06・約 14 年）。
【定義】e＝port − mean(port)（偏差。ボラのクラスタ・歪度・銘柄間相関の実データの形を保つ）。年率シャープ S の経路＝m_S + ブロック再標本（20 日・長さ len(port)）の e、m_S＝S·sd(e)/√252。各経路で 最大下落（複利）・前半（<2017）／後半（≥2017）の年単位 t（yearly_t と同じ定義）を計算。比較として IID 正規（同じ sd）の経路も出す。
【測るもの】S∈{0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0} ごとに P(max_dd ≥ −6%)、P(t_pre≥2 かつ t_post≥2)、P(両方＝関門通過)。P(通過)=0.5 と 0.9 になる S を線形補間で。実データの S07 本体の実現値（シャープ・max_dd・t）も併記。
【帰無】並べ替え検定ではなく模擬（ブートストラップ B 経路）。B=2000（--B）。seed 固定。
【判定（事前固定・変更禁止）】支持（関門は現実的）: ブロック版で P(通過 | S=1.0) ≥ 0.5。棄却（関門が律速）: ブロック版で P(通過 | S=1.5) < 0.5。ほか → 未確定。IID 版は記述（ブロック版との差＝ボラのクラスタの影響）。
【捨てた案の数】2（年ブロック＝経路の数が少なく分散が大きい／σ 目標を変えた版の掃引＝C は「決めるのは人」なので S だけを動かす）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）。
【実装】fe_core（load_d1・tsmom_pos・size_weights・simulate_portfolio・yearly_t・Runner._cost・write_result）。--smoke --B 20 で経路確認（銘柄 3）。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import (Spec, Runner, load_d1, tsmom_pos, syms_available, health, size_weights, simulate_portfolio, yearly_t,  # noqa: E402
                     RULES_FINTOKEI, SPLIT_YEAR, sharpe_ann, parse_args, write_result, fmt)
import s1x as X  # noqa: E402

QID = "Q416"
SEAL = X.SEAL
S_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
BLOCK = 20
L = 60


def _port(syms, smoke, rng):
    """S07 本体（TSMOM60・RULES_FINTOKEI）の日次損益。コストは Runner._cost と同じ規則。"""
    spec = Spec(qid=QID, question="", hypothesis="", reject_if="", syms=syms, kind="D1_fromH1", start="2010-01-01")
    r = Runner(spec, lambda df, p, s: tsmom_pos(df["close"].values, L))
    pos, close, cost = {}, {}, {}
    for s in syms:
        df = load_d1(s, smoke, rng); df = df[(df["time"] >= "2010-01-01") & (df["time"] < SEAL)].reset_index(drop=True)
        idx = pd.to_datetime(df["time"]); c = df["close"].values
        a = tsmom_pos(c, L).astype(float); a[: L + 1] = 0.0
        pos[s] = pd.Series(a, index=idx); close[s] = pd.Series(c, index=idx); cost[s] = pd.Series(r._cost(s, c) / 1e4, index=idx)
    POS = pd.DataFrame(pos).sort_index().fillna(0.0); C = pd.DataFrame(close).sort_index().ffill()
    R = C.pct_change(fill_method=None); COST = pd.DataFrame(cost).sort_index().ffill().fillna(0.0)
    W = size_weights(POS, R, RULES_FINTOKEI); sim = simulate_portfolio(W, R, COST, RULES_FINTOKEI)
    port = sim["port"]; port = port[port.index >= pd.Timestamp("2010-04-01")]
    return port, sim


def _block_paths(rng, e, B, block):
    n = len(e); nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :n]
    return e[idx]


def _eval_paths(M, years):
    """M: (B, n) 日次損益。max_dd（複利）、前後半の年単位 t。"""
    eq = np.cumprod(1.0 + M, axis=1); dd = (eq / np.maximum.accumulate(eq, axis=1) - 1.0).min(axis=1)
    uy, start = np.unique(years, return_index=True)
    order = np.argsort(start); uy, start = uy[order], start[order]
    sums = np.add.reduceat(M, start, axis=1); cnt = np.diff(np.r_[start, len(years)])
    ymean = sums / cnt * 1e4
    keep = cnt >= 20; ymean = ymean[:, keep]; uy = uy[keep]
    def t_of(mask):
        x = ymean[:, mask]
        if x.shape[1] < 2: return np.full(M.shape[0], np.nan)
        sd = x.std(axis=1, ddof=1); return np.where(sd > 0, x.mean(axis=1) / sd * np.sqrt(x.shape[1]), np.nan)
    return dd, t_of(uy < SPLIT_YEAR), t_of(uy >= SPLIT_YEAR)


def run(args, rng):
    syms, missing = syms_available(X.WIDE48, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="D1_fromH1")
    if args.smoke:
        syms = syms[:3]
    port, sim = _port(syms, args.smoke, rng)
    years = port.index.year.values; e = (port - port.mean()).to_numpy(); sd = float(e.std(ddof=1)); n = len(e)
    t_all, _ = yearly_t(port)
    observed = {"sharpe": fmt(sharpe_ann(port.to_numpy())), "mean_bp": fmt(port.mean() * 1e4), "sigma_pct": fmt(sd * 100), "max_dd": fmt(sim["max_dd"]),
                "t_all": fmt(t_all), "t_pre": fmt(yearly_t(port[port.index.year < SPLIT_YEAR])[0]), "t_post": fmt(yearly_t(port[port.index.year >= SPLIT_YEAR])[0]),
                "n_days": int(n), "first": str(port.index[0].date()), "last": str(port.index[-1].date()), "stops": int(sim["stops"])}
    B = max(int(args.B), 10)
    Eb = _block_paths(rng, e, B, BLOCK); Ei = rng.standard_normal((B, n)) * sd
    table = {"block": {}, "iid": {}}
    for name, E in (("block", Eb), ("iid", Ei)):
        for S in S_GRID:
            m = S * sd / np.sqrt(252.0); M = E + m
            dd, tp, tq = _eval_paths(M, years)
            ok_dd = dd >= -0.06; ok_t = (tp >= 2) & (tq >= 2); ok = ok_dd & ok_t
            table[name][str(S)] = {"p_dd_ok": fmt(ok_dd.mean()), "p_t_ok": fmt(np.nanmean(ok_t)), "p_pass": fmt(ok.mean()),
                                   "dd_median": fmt(np.median(dd)), "dd_q10": fmt(np.quantile(dd, 0.10)), "t_pre_median": fmt(np.nanmedian(tp))}
    def s_at(name, target):
        xs = np.array(S_GRID); ps = np.array([table[name][str(S)]["p_pass"] or 0.0 for S in S_GRID])
        if ps.max() < target: return None
        i = int(np.argmax(ps >= target));
        if i == 0: return fmt(xs[0])
        x0, x1, p0, p1 = xs[i - 1], xs[i], ps[i - 1], ps[i]
        return fmt(x0 + (target - p0) / (p1 - p0) * (x1 - x0)) if p1 > p0 else fmt(x1)
    required = {name: {"S_for_p50": s_at(name, 0.5), "S_for_p90": s_at(name, 0.9)} for name in table}
    p10 = table["block"]["1.0"]["p_pass"] or 0.0; p15 = table["block"]["1.5"]["p_pass"] or 0.0
    if p10 >= 0.5:
        verdict = "支持（関門は現実的）: ブロック版で P(通過 | S=1.0) ≥ 0.5"
    elif p15 < 0.5:
        verdict = "棄却（関門が律速）: ブロック版で P(通過 | S=1.5) < 0.5"
    else:
        verdict = "未確定"
    if dh and (dh["failed"] or dh["gaps"]):
        verdict += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return {"question": __doc__.splitlines()[0].split(": ", 1)[-1], "syms": syms, "missing": missing, "data_health": dh, "seal": str(SEAL.date()),
            "observed_s07_fintokei": observed, "table": table, "required_sharpe": required, "B_paths": B, "block": BLOCK, "rules": dict(RULES_FINTOKEI),
            "machine_verdict": verdict, "note": "S は年率シャープ（m_S=S·sd/√252 を偏差に足す）。P は B 経路の割合。IID 版はボラのクラスタを消した比較"}


if __name__ == "__main__":
    args = parse_args(default_B=2000)
    rng = np.random.default_rng(args.seed)
    res = run(args, rng)
    print("machine_verdict:", res["machine_verdict"]); print(res["required_sharpe"])
    write_result(QID, res, args.smoke, here=HERE)
