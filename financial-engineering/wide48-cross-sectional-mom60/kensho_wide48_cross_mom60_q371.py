#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S07 横断: 48 銘柄 wide48 D1 の横断モメンタム（L=60・上位1/3買い・下位1/3売り）。
各日、過去 L 日の log リターンで銘柄を順位付けし、上位 1/3 を +1、下位 1/3 を −1、残りを 0。
時系列版（Q367-Q370）と対になる銘柄ランキング型（Asness2013 Value and Momentum Everywhere 系）。
データが揃うまでは本番を実行しない: ok<40 なら「データ待ち」を書いて exit 2。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, GROUPS, syms_available, write_result, load_d1, exists_sym  # noqa: E402

WIDE48 = GROUPS["wide48"]


SPEC = Spec(
    qid="Q371",
    question="48 銘柄 wide48 の D1 横断モメンタム L=60（上位1/3買い・下位1/3売り）は封印前の前後半とも年単位 t≥2 か",
    hypothesis=(
        "各日 t に過去 L=60 日の log リターン ret_L[t,sym] で銘柄をランク付けし、"
        "上位 1/3 を +1、下位 1/3 を −1、残り 0。pos[t,sym] の等重き束の年単位 bp が "
        "pre（〜2016 末）・post（2017〜2024-06）とも t≥2"
    ),
    reject_if=(
        "pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか → 未確定"
    ),
    syms=list(WIDE48), kind="D1_fromH1",
    params=[{"L": 60, "long_frac": 1 / 3, "short_frac": 1 / 3, "min_syms": 10}],
    main_param=0, n_tests=2, warmup=120,
    B=500, null_kind="circ_shift", null_min_shift=120, split_year=2017, start="2008-01-01",
    discarded="0（S07 の横断版・5本中5本目。長短配分は 1/3 固定、L は 60 固定で掃引しない）",
    delegation="なし（Opus 設計 → Opus 実行）",
    source=(
        "[[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード系統 "
        "[[Asness・Moskowitz・Pedersen 2013 Value and Momentum Everywhere JF]]"
    ),
    data=(
        "48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。"
        "既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/、"
        "それ以外は 検証/_データ/raw/D1/。ok<40 ならデータ待ちで exit 2"
    ),
    measure="全48銘柄プール（等重き）の年単位 bp・t・束ねた t・Sharpe・最大下落・露出",
    null_desc=(
        "横断ランク pos（±1/0・連続日は保持）を各銘柄独立に循環シフト（min_shift=120・B=500）"
        "→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm"
    ),
    prior_art=(
        "WebSearch 2026-10-21「cross-sectional momentum top bottom quintile multi-asset Asness Moskowitz Pedersen"
        " value everywhere」。Asness・Moskowitz・Pedersen 2013（JF）が8資産クラスの横断で value/momentum を確認。"
        "既存の自検 [[15銘柄の日足で横断モメンタムと時系列モメンタムの差は前後半ともt2未満で...]]（Q約230）"
        "は 15 銘柄で差なしの未確定。48 銘柄×2008〜2024-06×独立追試は見つからない"
    ),
    batch="/lab-plan ターミナル版 2026-10-21・N=5 の 5 本目（S07 横断）",
    designer="Opus", coder="Opus",
)


_SMOKE = False
_PANEL_CACHE = {}


def _build_cs_panel(L, long_frac, short_frac, min_syms, rng):
    """48 銘柄の横断ランク pos パネル（行=時刻・列=銘柄）を作ってキャッシュ。
    各時刻 t で欠損のない銘柄数 n が min_syms 以上なら、ret_L の上位 ceil(n*long_frac) → +1、下位 ceil(n*short_frac) → -1。
    """
    key = (L, long_frac, short_frac, min_syms, _SMOKE)
    if key in _PANEL_CACHE:
        return _PANEL_CACHE[key]
    pxs = {}
    for s in WIDE48:
        if not _SMOKE and not exists_sym(s, "D1_fromH1"):
            continue
        try:
            d = load_d1(s, smoke=_SMOKE, rng=rng)
            pxs[s] = d.set_index("time")["close"]
        except Exception:
            continue
    if not pxs:
        _PANEL_CACHE[key] = pd.DataFrame()
        return _PANEL_CACHE[key]
    px = pd.DataFrame(pxs).sort_index()
    ret_L = np.log(px / px.shift(L))
    kL = max(1, int(np.ceil(len(ret_L.columns) * long_frac)))
    kS = max(1, int(np.ceil(len(ret_L.columns) * short_frac)))

    def _row(r):
        valid = r.dropna()
        out = pd.Series(0.0, index=r.index)
        n = len(valid)
        if n < min_syms:
            return out
        kl = max(1, int(np.ceil(n * long_frac)))
        ks = max(1, int(np.ceil(n * short_frac)))
        ranks = valid.rank(method="first")
        out.loc[valid.index[ranks > n - kl]] = 1.0
        out.loc[valid.index[ranks <= ks]] = -1.0
        return out

    pos = ret_L.apply(_row, axis=1)
    _PANEL_CACHE[key] = pos
    return pos


def strategy(df, p, sym):
    rng = np.random.default_rng(20261010)
    panel = _build_cs_panel(p["L"], p["long_frac"], p["short_frac"], p["min_syms"], rng)
    if panel.empty or sym not in panel.columns:
        return np.zeros(len(df))
    s = panel[sym].reindex(df["time"].values).fillna(0.0).values
    return s


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
    _SMOKE = "--smoke" in sys.argv
    if not _SMOKE and "--readme" not in sys.argv and "--idea-row" not in sys.argv:
        _data_guard()
    Runner(SPEC, strategy, here=HERE).execute()
