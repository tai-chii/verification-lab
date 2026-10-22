#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q461: 選び直す WFO で直前窓の全候補の純損益が負なら休むと、常に最良を選ぶより標本外の純損益・最大下落は良くなるか
================================================================================

【出典】
- 事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q460-C3 の行（Opus 2026-10-22・接続から）。
- 文献: ブログ Zenn 2026 hiro-2「毎月選び直す WFO は開発で固定条件を 118pips 上回りフォワードで 592pips 下回った」
  （hiro_algo の WFO は「全候補マイナスでも最もましな 1 つを選ぶ」）。
- 関連知見: Q177（選び直す頻度・事後選択はランダム選択より負）、Q210（直近 20 日損益の符号で規模切替は効かない）。
- コード: Q177（`../reselection-frequency/kensho_reselection_frequency_q177.py`）の `_walk` を f=21 に固定して再利用し、土台は fe_core。

【仮説（測る前に固定）】
H1: 直前窓（756 営業日）で全 L の窓内純損益が ≤0 のとき次の 21 日を休む（B）と、常に最良 L を持つ（A）より標本外の純損益が高い。
H0: B−A は 0 と区別できない（休む区間は A の損益の無作為な一部）。

【データ】15 銘柄 D1_fromH1（FX8＋TREND7）。封印: time < 2024-07-01 で切ってから全計算（2026-10-22 の規則）。
候補 L ∈ {5,10,…,300}（60・Q177 と同じ）。段階 1 コスト（片道 COST_RT/2、L の切替・休む／戻るの |Δpos| にもコスト）。

【定義（1通りに固定）】
- 選び直し時点 t = 756, 777, …（f=21）。窓 = [t−756, t)。各 L の窓内平均純損益の最大を与える L を選ぶ（A）。
- B: その最大値が ≤0（＝全 L の窓内純損益 ≤0）なら [t, t+21) のポジションを 0。そうでなければ A と同じ。
- 標本外 = 各銘柄の t ≥ 757（Q177 と同じく最初の 757 日の損益は NaN）。
- 集計: 銘柄×暦年の平均純損益 [bp/日]（標本外が 100 日以上の年だけ）→ 年ごとに銘柄平均 → 年を単位に B−A の平均と t。前後半（〜2016 / 2017〜）。
- 最大下落: 等金額（日ごとに銘柄平均）の累積純損益の最大下落 [bp]、A と B の差（記述）。
- 休んだ日の割合 = 全銘柄の標本外日のうち B が休んだ日の割合。
- 帰無: 銘柄ごと・暦年ごとに「休む日」の印を同じ年の中で循環シフト（k∈[1, n−1]）し、A のポジションに掛けて B' を作る。
  B'−A の年単位平均の分布（B=300）。観測の B−A 平均がその 95 点を超えるか。

【判定（事前固定・変更禁止）】all15・全期間で
- 休んだ日の割合 < 2% → 「対象なし」で未確定（他より先に当てる）。
- 支持: B−A の年単位 t ≥ 2 かつ 前半・後半の B−A 平均がともに正 かつ 観測 > 帰無の 95 点。
- 棄却: |t| < 1 または 前半と後半で B−A の符号が割れる。
- それ以外は未確定。窓（756）・閾値（0）・f（21）を結果を見て変えない。
判定に使う検定は 1 本（n_tests=1）。群別（FX8・TREND7）・最大下落は記述。

【捨てた案の数】約 3: 閾値を 0 でなく帰無の分位にする案、休む代わりに規模を半分にする案（Q210 で効かない）、f を 63 にもする案（Q177 で頻度は効かない）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。手順は機械的で、封印後（2024-07〜）は読まない。

【委託の確かめ方】設計・コード・実行・解釈は Opus（同一セッション）。休んだ日の割合・A の純損益が Q177 の f=21（全期間 0.42 bp/日）と同程度か（封印で期間は短い）を照合する。

実行: python3 kensho_wfo_rest_q461.py（B=300）／--smoke
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q461"
DEFAULT_B = 300
LS = list(range(5, 301, 5))
SEL_DAYS = 756
FREQ = 21
SEAL = pd.Timestamp("2024-07-01")
MIN_DAYS_YEAR = 100
GRP = {"all15": SYMS, "fx8": FX8, "trend7": TREND7}


def walk(M, POS):
    """A のポジションと休む印（B が 0 にする日）を返す。Q177 の _walk と同じ選び方（f=21）。"""
    T = M.shape[0]; posA = np.zeros(T); rest = np.zeros(T, bool); t = SEL_DAYS; n_sel = 0; n_rest = 0
    while t < T:
        w = M[t - SEL_DAYS:t].mean(axis=0); k = int(np.argmax(w))
        posA[t:t + FREQ] = POS[t:t + FREQ, k]
        if w[k] <= 0:
            rest[t:t + FREQ] = True; n_rest += 1
        n_sel += 1; t += FREQ
    return posA, rest, n_sel, n_rest


def oos_pnl(pos, c, cb):
    p = pnl_bp(pos, c, cb); p[:SEL_DAYS + 1] = np.nan
    return p


def year_means(pnl, yrs):
    d = pd.DataFrame({"year": yrs, "pnl": pnl}).dropna().groupby("year")["pnl"].agg(["mean", "count"])
    return d[d["count"] >= MIN_DAYS_YEAR]["mean"]


def agg_diff(cells, members, y0, y1):
    """cells: (sym, year, A, B) → 年ごとに銘柄平均 → B−A の年単位。"""
    sub = cells[cells["sym"].isin(members) & (cells["year"] >= y0) & (cells["year"] < y1)]
    if sub.empty:
        return None
    by = sub.groupby("year")[["A", "B"]].mean()
    d = by["B"] - by["A"]
    return {"n_years": int(len(by)), "A_mean": fmt(by["A"].mean()), "A_t": fmt(tstat(by["A"].values)), "B_mean": fmt(by["B"].mean()),
            "B_t": fmt(tstat(by["B"].values)), "diff_mean": fmt(d.mean()), "diff_t": fmt(tstat(d.values)), "_d": float(d.mean())}


def run(args, rng):
    hl = None if args.smoke else health(SYMS, kind="D1_fromH1", bar="D1")
    syms, missing = syms_available(SYMS, smoke=args.smoke)
    cells = []; daily = {}; rest_days = {}; oos_days = {}; sels = {}; store = {}
    for s in syms:
        df = load_d1(s, args.smoke, rng)
        df = df[df["time"] < SEAL].reset_index(drop=True)
        c = df["close"].values; cb = cost_bp_oneway(s, c); yrs = df["year"].values
        POS = np.column_stack([tsmom_pos(c, L) for L in LS]); M = np.column_stack([pnl_bp(POS[:, j], c, cb) for j in range(len(LS))])
        posA, rest, n_sel, n_rest = walk(M, POS)
        posB = posA * (~rest)
        pA = oos_pnl(posA, c, cb); pB = oos_pnl(posB, c, cb)
        yA = year_means(pA, yrs); yB = year_means(pB, yrs)
        for y in yA.index:
            cells.append((s, int(y), float(yA[y]), float(yB[y])))
        oos = np.isfinite(pA)
        rest_days[s] = int((rest & oos).sum()); oos_days[s] = int(oos.sum()); sels[s] = (n_sel, n_rest)
        daily[s] = pd.DataFrame({"time": df["time"].values, "A": pA, "B": pB}).set_index("time")
        store[s] = (posA, rest, c, cb, yrs, set(int(y) for y in yA.index))
        print(s, "休む回", n_rest, "/", n_sel, "休む日", rest_days[s], "/", oos_days[s])
    cells = pd.DataFrame(cells, columns=["sym", "year", "A", "B"])
    yrs_kept = sorted(cells["year"].unique().tolist())

    # 帰無: 年内で休む印を循環シフト
    null = {g: [] for g in GRP}
    for b in range(args.B):
        rows = []
        for s in syms:
            posA, rest, c, cb, yrs, keep = store[s]
            rs = rest.copy()
            oos_idx = np.arange(len(c)) > SEL_DAYS
            for y in np.unique(yrs):
                idx = np.where((yrs == y) & oos_idx)[0]
                if len(idx) >= 2:
                    rs[idx] = np.roll(rest[idx], int(rng.integers(1, len(idx))))
            pBn = oos_pnl(posA * (~rs), c, cb)
            yBn = year_means(pBn, yrs); yA = cells[cells["sym"] == s].set_index("year")["A"]
            for y in yA.index:
                rows.append((s, int(y), float(yA[y]), float(yBn.get(y, np.nan))))
        nc = pd.DataFrame(rows, columns=["sym", "year", "A", "B"])
        for g, mem in GRP.items():
            r = agg_diff(nc, mem, 0, 9999)
            null[g].append(r["_d"] if r else np.nan)

    out = {}
    for g, mem in GRP.items():
        for pn, (y0, y1) in (("all", (0, 9999)), ("pre", (0, SPLIT_YEAR)), ("post", (SPLIT_YEAR, 9999))):
            r = agg_diff(cells, mem, y0, y1)
            if r is None:
                continue
            d = r.pop("_d")
            if pn == "all":
                nl = np.asarray(null[g], float)
                r["null"] = null_summary(d, nl); r["null_q95"] = fmt(np.nanquantile(nl, 0.95))
            mem_ok = [m for m in mem if m in oos_days]
            r["rest_frac"] = fmt(sum(rest_days[m] for m in mem_ok) / max(1, sum(oos_days[m] for m in mem_ok)))
            if pn == "all":
                port = pd.concat([daily[m] for m in mem_ok], axis=0).groupby(level=0)[["A", "B"]].mean().dropna()
                r["mdd_A"] = fmt(max_drawdown(port["A"].values), 1); r["mdd_B"] = fmt(max_drawdown(port["B"].values), 1)
                r["mdd_B_minus_A"] = fmt(max_drawdown(port["B"].values) - max_drawdown(port["A"].values), 1)
                r["sharpe_A"] = fmt(sharpe_ann(port["A"].values)); r["sharpe_B"] = fmt(sharpe_ann(port["B"].values))
            out[f"{g}_{pn}"] = r

    # gaps のある銘柄を除いた記述
    gap_syms = sorted((hl or {}).get("gaps", {}).keys())
    ex = [m for m in SYMS if m not in gap_syms]
    r_ex = agg_diff(cells, ex, 0, 9999)
    if r_ex:
        r_ex.pop("_d"); out["all15_ex_gaps_all"] = {**r_ex, "excluded": gap_syms}

    a = out["all15_all"]; pre = out.get("all15_pre", {}); post = out.get("all15_post", {})
    t, dp, dq = a["diff_t"], pre.get("diff_mean"), post.get("diff_mean")
    obs = a["diff_mean"]; q95 = a["null_q95"]
    if a["rest_frac"] is not None and a["rest_frac"] < 0.02:
        verdict = "未確定（対象なし: 休んだ日 < 2%）"
    elif t is not None and t >= 2 and dp is not None and dq is not None and dp > 0 and dq > 0 and obs is not None and q95 is not None and obs > q95:
        verdict = "支持: 全候補負なら休むと純損益が上がる"
    elif (t is not None and abs(t) < 1) or (dp is not None and dq is not None and np.sign(dp) != np.sign(dq)):
        verdict = "棄却: 休んでも純損益は変わらない（または前後半で割れる）"
    else:
        verdict = "未確定"
    years_dropped = sorted(set(range(min(yrs_kept), max(yrs_kept) + 1)) - set(yrs_kept)) if yrs_kept else []
    res = {"question": "選び直す WFO で全候補が負なら休むと標本外の純損益・最大下落は良くなるか",
           "settings": {"LS": "5..300 step5 (60)", "SEL_DAYS": SEL_DAYS, "FREQ": FREQ, "seal": str(SEAL.date()), "B": args.B, "seed": args.seed,
                        "min_days_year": MIN_DAYS_YEAR, "split_year": SPLIT_YEAR},
           "data_health": hl, "missing": missing, "years_kept": yrs_kept, "years_dropped": years_dropped,
           "selections": {s: {"n_sel": v[0], "n_rest": v[1], "rest_days": rest_days[s], "oos_days": oos_days[s]} for s, v in sels.items()},
           "summary": out, "machine_verdict": verdict, "n_tests": 1,
           "multiple_comparisons": "判定は all15_all の B−A（t・前後半の符号・帰無 95 点）の 1 本。群別・最大下落・gaps 除外は記述。",
           "null_degenerate": bool(a["null"].get("degenerate"))}
    return res, {"cells": cells}


def main():
    args = parse_args(default_B=DEFAULT_B, default_seed=20261022)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
