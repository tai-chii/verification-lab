#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q418 基盤: 48 銘柄 D1_fromH1 の銘柄×年の足の本数の一覧と、本数 126 未満の年を年単位 t から除くと TSMOM60 等金額の前後半 t がどれだけ動くか（by_year_stats の min_rows 既定の見直し）。

【出典】[[検証/_基盤/知識/検証方法論/失敗パターン集]] 2026-10-22 15:13 の訂正（US500/USTECH 2011 の −80〜−165 bp は穴ではなく「4 本だけの年」を年単位で数えたため）／要対応 2026-10-22 14:54（year_sym に銘柄・年ごとの足の本数を出してほしい）／fe_core.by_year_stats（min_rows=20・レビュー H3）
【仮説】by_year_stats の min_rows=20 は「全銘柄を束ねた年の行数」に掛かるので、1 銘柄の短い年（データ開始年・穴の年）は落ちずに「年の中の銘柄平均」に等重みで入る。本数の少ない (銘柄, 年) は 1 標本としての分散が大きく、年単位 t を上下に動かす。本数 126 未満（半年未満）のセルを除くと、S07 本体（TSMOM60・等金額）の前後半 t が 0.3 以上動く本があるなら、Runner の year_sym に本数を出し、min_rows をセル単位で掛ける土台の変更が要る。
【データ】48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）。市場の判定はせず、データの監査。
【定義】セル＝(銘柄, 年)。n_bars＝その年の足の本数、gap_bars＝gap=True の本数。TSMOM60 の等金額 pnl_net（Runner._cells と同じ計算: pnl_bp・コストは Runner._cost）。
【測るもの】(1) セルの一覧（n_bars・gap_bars・mean_bp）を CSV に。n_bars<126 のセルの数と割合、該当の銘柄・年。(2) 全期間／前半（<2017）／後半の年単位 t（by_year_stats・min_rows=20）を、(a) 全セル、(b) n_bars<126 のセルを除く、(c) n_bars<200 を除く、で比べる（Δt）。(3) 本数の少ないセルの mean_bp の絶対値と、全セルの分布との比（過大な重みの可視化）。
【帰無】なし（監査。t の差は記述）。
【判定（事前固定・変更禁止）】支持（既定を変える）: n_bars<126 のセルが全セルの 3% 以上 かつ 前半または後半の |Δt|（(b)−(a)）≥0.3。棄却: n_bars<126 のセルが 1% 未満 かつ |Δt|<0.1。ほか → 未確定。
【捨てた案の数】1（S07〜S13 の全スクリプトを再計算＝S07 は棄却済みで「再計算しない」と台帳にある。TSMOM60 の 1 本だけで影響の大きさを測る）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）。
【実装】fe_core（Spec・Runner._load/_cells/_cost・by_year_stats・write_result）＋ _s1x_common の SealedRunner（封印）。--smoke で経路確認（銘柄 3）。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec, tsmom_pos, syms_available, health, by_year_stats, SPLIT_YEAR, parse_args, write_result, fmt  # noqa: E402
import s1x as X  # noqa: E402

QID = "Q418"
THRESHOLDS = (126, 200)


def run(args, rng):
    syms, missing = syms_available(X.WIDE48, kind="D1_fromH1", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="D1_fromH1")
    if args.smoke:
        syms = syms[:3]
    spec = Spec(qid=QID, question="", hypothesis="", reject_if="", syms=syms, kind="D1_fromH1", start="2010-01-01", params=[{"L": 60}], warmup=60)
    r = X.SealedRunner(spec, lambda df, p, s: tsmom_pos(df["close"].values, p["L"]))
    dfs = {s: r._load(s, args.smoke, rng) for s in syms}
    cells = r._cells(dfs, rng)
    agg = cells.groupby(["sym", "year"]).agg(n_bars=("pnl_net", "size"), n_pnl=("pnl_net", "count"), gap_bars=("gap", "sum"), mean_bp=("pnl_net", "mean")).reset_index()
    agg["abs_mean_bp"] = agg["mean_bp"].abs()
    n_cells = len(agg)
    short = {str(th): agg[agg["n_bars"] < th] for th in THRESHOLDS}
    def t_table(c):
        return {pn: {k: fmt(v) if k in ("mean", "t") else v for k, v in by_year_stats(c, "pnl_net", y0=y0, y1=y1).items()}
                for pn, (y0, y1) in (("all", (0, 9999)), ("pre", (0, SPLIT_YEAR)), ("post", (SPLIT_YEAR, 9999)))}
    t_all_cells = t_table(cells)
    t_excl = {}
    for th in THRESHOLDS:
        bad = set(map(tuple, short[str(th)][["sym", "year"]].values.tolist()))
        keep = ~cells.set_index(["sym", "year"]).index.isin(list(bad))
        t_excl[str(th)] = t_table(cells[keep])
    delta = {str(th): {pn: fmt((t_excl[str(th)][pn]["t"] or np.nan) - (t_all_cells[pn]["t"] or np.nan)) for pn in ("all", "pre", "post")} for th in THRESHOLDS}
    frac126 = len(short["126"]) / n_cells if n_cells else 0.0
    d_pre, d_post = delta["126"]["pre"], delta["126"]["post"]
    big = max(abs(d_pre or 0.0), abs(d_post or 0.0))
    if frac126 >= 0.03 and big >= 0.3:
        verdict = "支持（既定を変える）: 本数<126 のセルが 3% 以上で前半または後半の |Δt|≥0.3"
    elif frac126 < 0.01 and big < 0.1:
        verdict = "棄却: 本数<126 のセルは 1% 未満で |Δt|<0.1"
    else:
        verdict = "未確定"
    if dh and (dh["failed"] or dh["gaps"]):
        verdict += "（data_health に gaps あり: 監査なので記述）"
    med_abs = float(agg["abs_mean_bp"].median()) if n_cells else np.nan
    return {"question": __doc__.splitlines()[0].split(": ", 1)[-1], "syms": syms, "missing": missing, "data_health": dh, "seal": str(X.SEAL.date()),
            "n_cells": int(n_cells), "n_short": {th: int(len(d)) for th, d in short.items()}, "frac_short": {th: fmt(len(d) / n_cells) for th, d in short.items()},
            "short_cells_126": short["126"][["sym", "year", "n_bars", "gap_bars", "mean_bp"]].round(2).to_dict(orient="records"),
            "t_all_cells": t_all_cells, "t_excluding": t_excl, "delta_t": delta,
            "abs_mean_bp_ratio_short_vs_all": fmt(float(short["126"]["abs_mean_bp"].median()) / med_abs) if len(short["126"]) and med_abs > 0 else None,
            "gap_bars_total": int(agg["gap_bars"].sum()), "machine_verdict": verdict}, {"cells_sym_year": agg}


if __name__ == "__main__":
    args = parse_args(default_B=0)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    print("machine_verdict:", res["machine_verdict"], res["n_short"], res["delta_t"])
    write_result(QID, res, args.smoke, csvs, here=HERE)
