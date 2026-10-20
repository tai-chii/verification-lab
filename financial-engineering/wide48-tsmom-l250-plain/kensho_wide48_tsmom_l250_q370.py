#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S07 L=250: 48 銘柄 wide48 D1 のプレーン TSMOM（L=250・約12ヶ月）。
Moskowitz2012 の最強ホライズン（12ヶ月）に最も近い。
データが揃うまでは本番を実行しない: ok<40 なら「データ待ち」を書いて exit 2。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, tsmom_pos, GROUPS, syms_available, write_result  # noqa: E402

WIDE48 = GROUPS["wide48"]


SPEC = Spec(
    qid="Q370",
    question="48 銘柄 wide48 の D1 プレーン TSMOM L=250（約12ヶ月・ボラ正規化なし）は封印前の前後半とも年単位 t≥2 か",
    hypothesis=(
        "pos[t] = sign(close[t]−close[t−250])。全48銘柄を等重みで束ね、"
        "pre（〜2016 末）・post（2017〜2024-06）とも年単位 t≥2"
    ),
    reject_if=(
        "pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか → 未確定"
    ),
    syms=list(WIDE48), kind="D1_fromH1",
    params=[{"L": 250}],
    main_param=0, n_tests=2, warmup=300,
    B=500, null_kind="circ_shift", null_min_shift=300, split_year=2017, start="2008-01-01",
    discarded="0（S07 の L 掃引3本の3本目。試行は本体＋L∈{60,120,250}＋横断の5本に固定）",
    delegation="なし（Opus 設計 → Sonnet 実行）",
    source=(
        "[[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード "
        "[[Moskowitz2012-1_時系列モメンタムは12か月の予測力を持ち58先物のすべてで正]]"
    ),
    data=(
        "48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。"
        "既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/、"
        "それ以外は 検証/_データ/raw/D1/。ok<40 ならデータ待ちで exit 2"
    ),
    measure="全48銘柄プール（等重み）の年単位 bp・t・束ねた t・Sharpe・最大下落・露出",
    null_desc="合図（±1/0）を循環シフト（min_shift=300・B=500）→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm",
    prior_art=(
        "WebSearch 2026-10-21「time-series momentum 12-month lookback long horizon trend following 250-day」。"
        "Moskowitz2012 原典が 12 ヶ月で全58銘柄で正の予測力を報告（最強ホライズン）。"
        "post-crisis（2009〜）の後続研究（AQR Insights、Hurst2017）でも 12 ヶ月は頑健。"
        "48 銘柄×2008〜2024-06×封印前の独立追試は見つからない"
    ),
    batch="/lab-plan ターミナル版 2026-10-21・N=5 の 4 本目（S07 L=250）",
    designer="Opus", coder="Opus",
)


def strategy(df, p, sym):
    return tsmom_pos(df["close"].values, p["L"])


def _data_guard():
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
    Runner(SPEC, strategy, here=HERE).execute()
