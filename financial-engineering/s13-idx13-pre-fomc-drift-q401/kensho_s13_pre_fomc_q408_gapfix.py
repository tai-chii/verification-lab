#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q408（Q401 の Opus 見直し）: Q401 と同じ事前登録（仮説・判定規則・帰無・設定 2 本）で、データの穴を跨ぐ足の合図だけを 0 にして再計算する。

事前登録からの変更点（判定規則は変えない・実装の修正だけ）:
- 足 k+1 が前の足から 168h 超（fe_core の D1 の gap 既定と同じ）なら、その足を取る合図 pos[k] を 0 にする。
  理由: Q401 の前半 −1.57 bp は US500/USTECH 2011 の穴（2011-09-22〜2012-01-16）を跨ぐ足（−80/−58 bp＝約 4 か月分の値動き）が作っていた（Q401 README「事後の判断」）。
- それ以外（銘柄・期間・封印・コスト・帰無 B=500・Holm m=2・judge_gate）は Q401 のまま。修正前の結果は results/Q401_result_20261022_145054.json。
- qid を Q408 にして結果を Q401 と別名で残す。
実行: python3 kensho_s13_pre_fomc_q408_gapfix.py（--smoke で経路確認）
"""
import dataclasses
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
import s1x as X  # noqa: E402
from kensho_s13_pre_fomc_q401 import SPEC as SPEC401, strategy as strategy401, make_extra  # noqa: E402

GAP_H = 168.0

SPEC = dataclasses.replace(
    SPEC401, qid="Q408", coder="Opus（Q401 の Fable コードを包むだけ）",
    data=SPEC401.data + "。**Q408: 前の足から 168h 超の足（データの穴を跨ぐ足）は合図を 0**",
    settings={**SPEC401.settings, "gap_fix": "足 k+1 の dt_prev>168h なら pos[k]=0（Q408・判定規則は不変）", "base_result": "results/Q401_result_20261022_145054.json"},
)


def strategy(df, p, sym):
    pos = np.asarray(strategy401(df, p, sym), float).copy()
    t = pd.to_datetime(df["time"]).values
    dt_h = np.diff(t).astype("timedelta64[m]").astype(float) / 60.0   # dt_h[k] = time[k+1]-time[k]
    pos[:-1][dt_h > GAP_H] = 0.0
    if STUB_MIN_BARS:
        # 追加の修正（--stub-fix）: 銘柄×年の足が STUB_MIN_BARS 本未満の年（データ開始直後の切れ端）は合図を 0。
        # 等金額は銘柄×年の平均を年で束ねるので、4 本しかない年の 1 回の FOMC が 1 年分の重みを持つ（US500/USTECH 2011）。
        yr = pd.to_datetime(df["time"]).dt.year.values
        cnt = pd.Series(yr).map(pd.Series(yr).value_counts()).values
        stub = cnt < STUB_MIN_BARS
        pos[:-1][stub[1:]] = 0.0
    return pos


STUB_MIN_BARS = 60 if "--stub-fix" in sys.argv else 0
if STUB_MIN_BARS:
    sys.argv.remove("--stub-fix")
    SPEC = dataclasses.replace(SPEC, settings={**SPEC.settings, "stub_fix": f"銘柄×年の足 <{STUB_MIN_BARS} 本の年は合図 0（Q408 感度分析）"})


if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=10, summarize_extra=make_extra(SPEC))
