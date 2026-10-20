#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S07 本体: 48 銘柄 wide48 D1 TSMOM60（σ60 ボラ正規化・等リスク束）。
事前登録の正本は SPEC（docstring に重複して書かない）。
データが揃うまでは本番を実行しない: ok<40 なら「データ待ち」を書いて exit 2。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, syms_available, write_result, by_year_stats, fmt, GROUPS  # noqa: E402

WIDE48 = GROUPS["wide48"]


SPEC = Spec(
    qid="Q367",
    question="48 銘柄 wide48 の D1 TSMOM60（σ60 ボラ正規化・等リスク束）は封印前（〜2024-06）の前後半とも年単位 t≥2 か",
    hypothesis=(
        "pos[t] = sign(close[t]−close[t−60]) × target_vol/σ60[t]（target_vol=0.10 年率、"
        "σ60 は直近 60 本の日次 log リターンの標準偏差を年率化）。等重みで全銘柄を束ね、"
        "pre（〜2016 末）・post（2017〜2024-06）とも年単位 t≥2"
    ),
    reject_if=(
        "pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。"
        "ほか（符号条件・t 条件のどちらかで未達） → 未確定"
    ),
    syms=list(WIDE48), kind="D1_fromH1",
    params=[{"L": 60, "target_vol": 0.10, "sigma_win": 60}],
    main_param=0, n_tests=2, warmup=120,
    B=500, null_kind="circ_shift", null_min_shift=120, split_year=2017, start="2008-01-01",
    discarded="0（S07 の最初の実装。本体仕様はそのままで試行は本体＋L∈{60,120,250}＋横断の5本に固定）",
    delegation="なし（Opus 設計 → Sonnet 実行）",
    source=(
        "[[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード "
        "[[Moskowitz2012-1_時系列モメンタムは12か月の予測力を持ち58先物のすべてで正]]（原典 Moskowitz・Ooi・Pedersen 2012）"
    ),
    data=(
        "48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。"
        "既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/data_*_D1_fromH1.csv、"
        "それ以外は 検証/_データ/raw/D1/data_*_D1_fromH1.csv。"
        "ok<40 ならデータ待ちで実行しない（status=データ待ち で exit 2）"
    ),
    measure=(
        "全48銘柄プール（等重み）の年単位平均 bp（コスト0と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。"
        "族別（fx22/idx13/cmd8/bond3）の寄与は extra に記述（判定には使わない）"
    ),
    null_desc=(
        "合図（±target_vol/σ60 の連続量）を各銘柄独立に循環シフト（min_shift=120・B=500）→ "
        "全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm"
    ),
    prior_art=(
        "WebSearch 2026-10-21「Moskowitz Ooi Pedersen time series momentum 58 futures volatility scaling 2012」"
        "で原典 Moskowitz・Ooi・Pedersen (2012, JFE) と後継（Baltas・Kosowski 2020、Garleanu・Pedersen 2024 "
        "arXiv 2507.15876 CTA replication）を確認。"
        "48 銘柄×σ60 ボラ正規化×等リスク束の封印前 2008〜2024-06 期間での独立追試は見つからない（原典は 1965〜2009）"
    ),
    batch="/lab-plan ターミナル版 2026-10-21・N=5 の 1 本目（S07 本体）",
    designer="Opus", coder="Opus",
)


def strategy(df, p, sym):
    """合図: sign(close[t]−close[t−L]) × target_vol/σ60[t]。shift しない（pnl_bp がずらす）。"""
    c = df["close"].values
    L = p["L"]
    tgt = p["target_vol"]
    w = p["sigma_win"]
    n = len(c)
    sgn = np.zeros(n)
    sgn[L:] = np.sign(c[L:] - c[:-L])
    r = np.zeros(n)
    r[1:] = np.log(c[1:] / c[:-1])
    s = pd.Series(r).rolling(w, min_periods=w).std(ddof=1).values * np.sqrt(252.0)
    scale = np.zeros(n)
    ok = (s > 1e-6) & np.isfinite(s)
    scale[ok] = tgt / s[ok]
    scale = np.clip(scale, 0.0, 5.0)
    return sgn * scale


def _summarize_families(cells, spec):
    """族別（fx22/idx13/cmd8/bond3）の記述統計を extra に残す（判定には使わない）。"""
    out = {}
    sy = spec.split_year
    periods = {"all": (0, 9999), "pre": (0, sy), "post": (sy, 9999)}
    for fam in ("fx22", "idx13", "cmd8", "bond3"):
        members = GROUPS[fam]
        for pi, _ in enumerate(spec.params):
            ci = cells[(cells["param"] == pi) & (cells["sym"].isin(members))]
            if ci.empty:
                continue
            for pn, (y0, y1) in periods.items():
                b = by_year_stats(ci, "pnl_net", y0=y0, y1=y1)
                out[f"p{pi}_{fam}_{pn}"] = {
                    "n_years": b["n_years"],
                    "n_syms": int(ci["sym"].nunique()),
                    "bp_net": fmt(b["mean"]),
                    "t_year": fmt(b["t"]),
                }
    return out


def _data_guard():
    """ok<40 ならデータ待ちで exit 2（ledger の S07 データガード 2026-10-21）。"""
    ok, missing = syms_available(WIDE48, kind="D1_fromH1")
    if len(ok) < 40:
        res = {
            "status": "データ待ち",
            "qid": SPEC.qid,
            "n_ok": len(ok),
            "n_required": 40,
            "n_total": len(WIDE48),
            "ok": ok,
            "missing": missing,
            "note": "S07 データガード: ok<40 のため本番を実行しない。release で待ちに戻す。",
        }
        write_result(SPEC.qid, res, smoke=False, here=HERE)
        print(f"データ待ち: ok={len(ok)}/{len(WIDE48)} missing={len(missing)}")
        sys.exit(2)


if __name__ == "__main__":
    if "--smoke" not in sys.argv and "--readme" not in sys.argv and "--idea-row" not in sys.argv:
        _data_guard()
    Runner(SPEC, strategy, summarize_extra=_summarize_families, here=HERE).execute()
