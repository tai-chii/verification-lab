#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q428 基盤: 関門の候補 C1（σ 目標 0.25%／0.35%/日・最大下落 −6%）と C2（最大下落 ≥ −0.75×年率 σ）は年率シャープ S の戦略を何割通し、1 年以内の −6%／−10% 到達率はいくらか（Q416 の S07 ブロック・ブートストラップを規程の変種に当てる・★ C の判断材料）。

【出典】[[検証/_基盤/戦略台帳]] 段階と関門／要対応 2026-10-22 16:14「★ S16 も閉じた: C（関門の DD 条件の見直し）を提案」（C1＝σ 目標を下げた版を結果を見る前に固定、C2＝max_dd を年率 σ に比例した値に）／Q416（現行の関門は S≈2.7 で半数・S 1.0 で 0.2%・律速は DD）／Man Group 'You're fired'（IID 模擬・最大下落の到達率）／Mannheim 大の MDD 模擬（IID ブートストラップは MDD を過小評価、ブロック再標本が頑健）／運用規程 第 8 条（Fintokei: 最大損失 −10% は初期資金基準・累計停止 −6%）
【仮説】C1（σ 0.25%/日）は最大下落の分布を半分の深さに縮めるので、年率シャープ 1.5 の戦略の過半を通す（現行 4%）。一方 C2 を文字どおり「実現の年率 σ × 0.75」で置くと、σ 目標 0.5%（年率 約 8%）では −6% とほぼ同じで緩和にならず、実現 σ が目標を下回る戦略（Q425 の 0.23%/日）にはむしろ厳しくなる。これが本当なら ★ C の実質の選択肢は C1 の σ の値（0.25 か 0.35 か）で、C2 は定義を直さないと使えない。
【データ】48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）。TSMOM60（S07 本体）の合図 → 規程の変種ごとに size_weights → simulate_portfolio（コストは Runner._cost と同じ）→ 日次損益 port（2010-04〜2024-06・約 14 年）。Q416 と同じ源。
【定義】変種＝{current: σ 0.5%・gate −6%, C1_025: σ 0.25%・gate −6%, C1_035: σ 0.35%・gate −6%, C2: σ 0.5%・gate ≥ −0.75×（経路の実現 σ×√252）}。sym_cap 1.5%・レバ 2・日次停止 −2.5% は全変種で同じ（C1 は port_sigma_target だけ変える）。各変種で e＝port − mean(port)、年率シャープ S の経路＝m_S + 20 日ブロック再標本の e、m_S＝S·sd(e)/√252。各経路で 14 年の最大下落（複利）・前半（<2017）／後半（≥2017）の年単位 t・通過（dd ok かつ t_pre≥2 かつ t_post≥2）。1 年到達率＝暦年ごとに年初からの累積損益の最小値が −6%（累計停止）／−10%（Fintokei 失格）以下になった (経路, 年) の割合＝「1 口座・1 年あたりの失格率」。IID 正規（同じ sd）は比較。
【測るもの】変種 × S∈{0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0} ごとに P(dd ok)・P(t ok)・P(通過)・dd 中央値・1 年到達率（−6%／−10%）。P(通過)=0.5／0.9 になる S を線形補間。各変種の S07 本体の実現値（σ・max_dd・t）。
【帰無】並べ替え検定ではなく模擬（ブロック再標本 B 経路・seed 固定）。B=2000（--B）。
【判定（事前固定・変更禁止）】C1_025 のブロック版について: 支持（C1 で関門は S 1.5 を半数以上通す）: P(通過 | S=1.5) ≥ 0.5。棄却（C1 でも律速）: P(通過 | S=2.0) < 0.5。ほか → 未確定。C1_035・C2・到達率・IID 版は記述（★ C の表）。結果を見てから σ の値を増やさない（0.25 と 0.35 の 2 点で固定）。
【捨てた案の数】3（過去 16 戦略の結果 JSON を C1/C2 で当て直す＝事後の掃引なので不可／σ 目標の細かい掃引＝値は人が決める／S16 合成の損益を源にする＝暗号が前半に無く 14 年の形が偏る）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）。
【実装】fe_core（load_d1・tsmom_pos・size_weights・simulate_portfolio・yearly_t・Runner._cost・write_result）。Q416 の経路生成と評価をそのまま使い、規程の変種と 1 年到達率を足した。--smoke --B 20 で経路確認（銘柄 3）。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (Spec, Runner, load_d1, tsmom_pos, syms_available, health, size_weights, simulate_portfolio, yearly_t,  # noqa: E402
                     RULES_FINTOKEI, SPLIT_YEAR, sharpe_ann, parse_args, write_result, fmt)
from fe_core import _paths as P  # noqa: E402

QID = "Q428"
SEAL = pd.Timestamp("2024-07-01")
WIDE48 = list(P.WIDE48)
S_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
BLOCK = 20
L = 60
DD_GATE = -0.06
BREACH_LEVELS = {"stop6": -0.06, "fail10": -0.10}
# 規程の変種（事前固定。結果を見てから足さない）。gate: "abs" は −6% 固定、"rel" は −0.75×経路の実現年率 σ
VARIANTS = {
    "current": dict(rules=dict(RULES_FINTOKEI), gate="abs", note="現行: σ 0.5%/日・max_dd −6%"),
    "C1_025": dict(rules={**RULES_FINTOKEI, "port_sigma_target": 0.0025}, gate="abs", note="C1: σ 0.25%/日・max_dd −6%（判定に使う）"),
    "C1_035": dict(rules={**RULES_FINTOKEI, "port_sigma_target": 0.0035}, gate="abs", note="C1': σ 0.35%/日・max_dd −6%（記述）"),
    "C2": dict(rules=dict(RULES_FINTOKEI), gate="rel", rel_mult=0.75, note="C2: σ 0.5%/日・max_dd ≥ −0.75×実現年率 σ（記述）"),
}
JUDGE_VARIANT = "C1_025"


def _frames(syms, smoke, rng):
    """銘柄ごとの (pos, close, cost) を 1 回だけ読む（変種で共有）。"""
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
    return POS, R, COST


def _port(POS, R, COST, rules):
    """S07 本体（TSMOM60）を規程 rules で走らせた日次損益。"""
    W = size_weights(POS, R, rules); sim = simulate_portfolio(W, R, COST, rules)
    port = sim["port"]; port = port[port.index >= pd.Timestamp("2010-04-01")]
    return port, sim


def _block_paths(rng, e, B, block):
    n = len(e); nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :n]
    return e[idx]


def _eval_paths(M, years):
    """M: (B, n) 日次損益。14 年の max_dd（複利）、前後半の年単位 t、経路の実現年率 σ。"""
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
    ann_sigma = M.std(axis=1, ddof=1) * np.sqrt(252.0)
    return dd, t_of(uy < SPLIT_YEAR), t_of(uy >= SPLIT_YEAR), ann_sigma


def _yearly_breach(M, years, level):
    """暦年ごとに「年初からの累積損益（複利）の最小値 ≤ level」となった (経路, 年) の割合。足が 126 本未満の年は数えない。"""
    uy, start = np.unique(years, return_index=True)
    order = np.argsort(start); uy, start = uy[order], start[order]
    ends = np.r_[start[1:], len(years)]
    hits, cells = 0, 0
    for s, e in zip(start, ends):
        if e - s < 126:
            continue
        cum = np.cumprod(1.0 + M[:, s:e], axis=1) - 1.0
        hits += int((cum.min(axis=1) <= level).sum()); cells += M.shape[0]
    return (hits / cells) if cells else float("nan"), cells // max(M.shape[0], 1)


def run(args, rng):
    syms, missing = syms_available(WIDE48, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="D1_fromH1")
    if args.smoke:
        syms = syms[:3]
    POS, R, COST = _frames(syms, args.smoke, rng)
    B = max(int(args.B), 10)
    out = {}
    for vname, v in VARIANTS.items():
        port, sim = _port(POS, R, COST, v["rules"])
        years = port.index.year.values; e = (port - port.mean()).to_numpy(); sd = float(e.std(ddof=1)); n = len(e)
        t_all, _ = yearly_t(port)
        observed = {"sharpe": fmt(sharpe_ann(port.to_numpy())), "mean_bp": fmt(port.mean() * 1e4), "sigma_pct": fmt(sd * 100), "max_dd": fmt(sim["max_dd"]),
                    "t_all": fmt(t_all), "t_pre": fmt(yearly_t(port[port.index.year < SPLIT_YEAR])[0]), "t_post": fmt(yearly_t(port[port.index.year >= SPLIT_YEAR])[0]),
                    "n_days": int(n), "first": str(port.index[0].date()), "last": str(port.index[-1].date()), "stops": int(sim["stops"]),
                    "ann_sigma_pct": fmt(sd * np.sqrt(252.0) * 100)}
        Eb = _block_paths(rng, e, B, BLOCK); Ei = rng.standard_normal((B, n)) * sd
        table = {"block": {}, "iid": {}}
        for name, E in (("block", Eb), ("iid", Ei)):
            for S in S_GRID:
                m = S * sd / np.sqrt(252.0); M = E + m
                dd, tp, tq, asig = _eval_paths(M, years)
                gate_level = np.full(len(dd), DD_GATE) if v["gate"] == "abs" else -float(v["rel_mult"]) * asig
                ok_dd = dd >= gate_level; ok_t = (tp >= 2) & (tq >= 2); ok = ok_dd & ok_t
                row = {"p_dd_ok": fmt(ok_dd.mean()), "p_t_ok": fmt(np.nanmean(ok_t)), "p_pass": fmt(ok.mean()),
                       "dd_median": fmt(np.median(dd)), "dd_q10": fmt(np.quantile(dd, 0.10)), "t_pre_median": fmt(np.nanmedian(tp)),
                       "gate_level_median": fmt(np.median(gate_level)), "ann_sigma_median": fmt(np.median(asig))}
                for bname, lev in BREACH_LEVELS.items():
                    rate, ny = _yearly_breach(M, years, lev)
                    row[f"breach_year_{bname}"] = fmt(rate); row["n_years_counted"] = int(ny)
                table[name][str(S)] = row

        def s_at(name, target):
            xs = np.array(S_GRID); ps = np.array([table[name][str(S)]["p_pass"] or 0.0 for S in S_GRID])
            if ps.max() < target: return None
            i = int(np.argmax(ps >= target))
            if i == 0: return fmt(xs[0])
            x0, x1, p0, p1 = xs[i - 1], xs[i], ps[i - 1], ps[i]
            return fmt(x0 + (target - p0) / (p1 - p0) * (x1 - x0)) if p1 > p0 else fmt(x1)
        out[vname] = {"note": v["note"], "rules": {k: val for k, val in v["rules"].items()}, "gate": v["gate"] if v["gate"] == "abs" else f"rel x{v['rel_mult']}",
                      "observed_s07": observed, "table": table,
                      "required_sharpe": {name: {"S_for_p50": s_at(name, 0.5), "S_for_p90": s_at(name, 0.9)} for name in table}}
    jt = out[JUDGE_VARIANT]["table"]["block"]
    p15 = jt["1.5"]["p_pass"] or 0.0; p20 = jt["2.0"]["p_pass"] or 0.0
    if p15 >= 0.5:
        verdict = f"支持（C1 σ0.25% で関門は S 1.5 を半数以上通す）: ブロック版 P(通過 | S=1.5)={p15:.3f} ≥ 0.5"
    elif p20 < 0.5:
        verdict = f"棄却（C1 でも律速）: ブロック版 P(通過 | S=2.0)={p20:.3f} < 0.5"
    else:
        verdict = f"未確定: P(通過 | S=1.5)={p15:.3f}, P(通過 | S=2.0)={p20:.3f}"
    if dh and (dh["failed"] or dh["gaps"]):
        verdict += "（data_health に failed/gaps あり: 確定にする前に点検）"
    summary = {v: {"S_for_p50_block": out[v]["required_sharpe"]["block"]["S_for_p50"],
                   "p_pass_S15_block": out[v]["table"]["block"]["1.5"]["p_pass"],
                   "breach_year_fail10_S15_block": out[v]["table"]["block"]["1.5"]["breach_year_fail10"],
                   "observed_sigma_pct": out[v]["observed_s07"]["sigma_pct"], "observed_max_dd": out[v]["observed_s07"]["max_dd"]} for v in out}
    return {"question": __doc__.splitlines()[0].split(": ", 1)[-1], "syms": syms, "missing": missing, "data_health": dh, "seal": str(SEAL.date()),
            "variants": out, "summary_for_decision": summary, "judge_variant": JUDGE_VARIANT, "B_paths": B, "block": BLOCK, "dd_gate_abs": DD_GATE,
            "breach_levels": BREACH_LEVELS, "machine_verdict": verdict,
            "note": "S は年率シャープ（m_S=S·sd/√252 を偏差に足す）。P は B 経路の割合。breach_year_* は (経路, 暦年) のうち年初からの累積損益が水準以下になった割合＝1 口座 1 年あたりの到達率。C2 は経路ごとの実現年率 σ×0.75 を関門にした文字どおりの定義"}


if __name__ == "__main__":
    args = parse_args(default_B=2000)
    rng = np.random.default_rng(args.seed)
    res = run(args, rng)
    print("machine_verdict:", res["machine_verdict"]); print(res["summary_for_decision"])
    write_result(QID, res, args.smoke, here=HERE)
