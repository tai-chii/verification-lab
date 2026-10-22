#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q415 S15: 48 銘柄 D1 の TSMOM60 を「8 中銀のうち直近 180 暦日に利上げした数 ≥4」の局面だけ持つと、常時より規程モードの前後半 t と最大下落が改善するか。
事前登録の正本は SPEC。Runner 型（封印・全設定の規程モードは _s1x_common/s1x.py、利上げ局面は _s14_common/s14.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s15_tsmom_global_hiking_q415.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s14_common"))
from fe_core import Spec, tsmom_pos, fmt  # noqa: E402
import s14 as S14  # noqa: E402
X = S14.X

SPEC = Spec(
    qid="Q415",
    question="48 銘柄 D1 の TSMOM60 を「8 中銀（USD EUR JPY GBP AUD CAD CHF NZD）のうち直近 180 暦日に利上げした数が 4 以上」の局面だけ持つと、常時持つ S07 本体より規程モードの前後半 t と最大下落が改善するか",
    hypothesis="Man Group 2024（BTOP50 と FF 金利・1987〜）: 順張りは利上げ局面の大半で正、2022 年は +15%。機構: 金融引き締めは金利・為替・債券に持続的な方向（政策の段階的な変更）を作り、順張りはそれを拾う。緩和・据え置きの局面では往来相場で順張りが負ける。S07（48 銘柄 TSMOM60）は全期間で粗利 ≈0・規程モード max_dd −95% だったが、損失が据え置き局面に集中しているなら、局面で絞れば t と下落が改善する。局面は政策金利（ポイントインタイム・t−1 暦日まで）だけで決め、閾値 4／8 と窓 180 日は事前に固定。局面外は 0（持たない）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）で局面限定（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ 局面限定の max_dd が常時（param 1）より浅く t_all も高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの局面限定の t_all が常時以下（局面が効かない）。ほか → 未確定。局面の日数（年別）・族別の寄与は記述。S15 の族内試行は Q414（2）・Q415（2）＝4",
    syms=list(X.WIDE48), kind="D1_fromH1", start="2010-01-01",
    params=[{"L": 60, "min_hiking": 4}, {"L": 60, "min_hiking": None}], main_param=0, n_tests=2, warmup=120, per_year=252,
    B=500, split_year=2017, null_kind="circ_shift", null_min_shift=120,
    discarded="3（閾値 2〜6 の掃引＝4（過半）に固定／各銘柄の自国中銀だけで局面を決める＝S12 の金利モメンタムと同じ族／利下げ局面も「持つ」側に入れる＝Man の結果は利上げ側）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S15（利上げ局面の事前定義）／Man Group 2024 'Views from the floor 2024-01-23'（BTOP50 と利上げ局面・運用会社の資料＝参考）／Neville ほか 2021 'The best strategies for inflationary times' JPM／S07 Q367（48 銘柄 TSMOM60 本体）／政策金利 `_データ/raw/rates/policy_<CCY>.csv`（BIS・8 通貨）",
    data="48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 8 通貨の政策金利（実施日ベース・t−1 暦日まで）。局面＝直近 180 暦日に上げた中銀の数 ≥4。コスト: Runner の既定（COST_RT／スプレッド中央値／暗号 30 bp）",
    measure="等金額: 48 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（局面で下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（局面限定・常時の両設定＝rule_mode.params）。extra: 局面の日数（年別）、利上げ中銀数の分布、族別（fx/idx/cmd/bond/crypto）の net bp（局面内）",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）。注意: 局面限定は合図ゼロの区間が長いので、失敗パターン集 2026-10-22 の「循環シフト帰無の中心のずれ」を事後の判断で点検する（Q417 がその頻度を測る）",
    prior_art="WebSearch 2026-10-22「trend following performance during global monetary tightening cycles central bank hiking regime trend strategies returns」: Man Group 2024（BTOP50・利上げ局面の大半で正・運用会社の資料で利害あり）、PIMCO・Wellington（債券・株の利上げ局面成績で順張りではない）。独立な学術研究と、非米中銀を含む「利上げ中銀数」の局面定義は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 5 本目（S15・TSMOM60×グローバル利上げ局面）", designer="Fable", coder="Fable",
    settings={"seal": str(S14.SEAL.date()), "regime_window_days": 180, "rate_lag_days": 1, "ccys": S14.CCY8, "s15_family_trials": "Q414（2）・Q415（2）＝4"},
)
RUNNER = {"obj": None}
_N = {}


def _nhike(df):
    r = RUNNER["obj"]; smoke = bool(r and r.smoke)
    t = df["time"].values; key = (smoke, len(t), str(t[0]), str(t[-1]))
    if key not in _N:
        _N[key] = S14.n_hiking(t, SPEC.settings["regime_window_days"], SPEC.settings["rate_lag_days"], S14.CCY8, smoke=smoke, rng=(r.rng if r else None))
    return _N[key]


def strategy(df, p, sym):
    """合図: TSMOM60。min_hiking が None でなければ、利上げ中銀数 < min_hiking の日は 0。shift しない。"""
    pos = tsmom_pos(df["close"].values, p["L"]).astype(float)
    if p["min_hiking"] is None:
        return pos
    return np.where(_nhike(df) >= p["min_hiking"], pos, 0.0)


def judge(res, spec):
    """3 分岐（事前固定）。支持: main が規程 gate 通過・max_dd と t_all が常時より良い・等金額 z≥2。棄却: z<1 または main の t_all ≤ 常時。ほか → 未確定。"""
    m = res.get("main", {}); rm = res.get("rule_mode", {}); f = rm.get("fintokei", {}); gate = rm.get("gate", {})
    z = (m.get("all") or {}).get("z"); params = rm.get("params") or []
    if z is None or f.get("t_all") is None or len(params) < 2:
        return "未確定: 計算できない（帰無の退化か規程モードの不足）"
    g0 = params[0]["fintokei"]; g1 = params[1]["fintokei"]
    if z < 1 or (g0["t_all"] is not None and g1["t_all"] is not None and g0["t_all"] <= g1["t_all"]):
        return "棄却: 等金額の全期間 z<1 または 局面限定の t_all が常時以下"
    if gate.get("pass") and z >= 2 and g0["max_dd"] > g1["max_dd"] and g0["t_all"] > g1["t_all"]:
        return "支持: 局面限定が規程モードで前後半 t≥2・max_dd≥−6%、常時より max_dd 浅く t_all 高く、等金額 z≥2"
    return "未確定"


def extra(cells, spec):
    out = {}
    r = RUNNER["obj"]
    if r is not None and r.loaded:
        df0 = max(r.loaded.values(), key=len); n = _nhike(df0); yrs = df0["year"].values
        out["regime_days_by_year"] = {int(y): int(((n >= 4)[yrs == y]).sum()) for y in np.unique(yrs)}
        out["n_hiking_hist"] = {int(k): int(v) for k, v in zip(*np.unique(n, return_counts=True))}
    fam = {"fx": X.P.FX22, "idx": X.IDX13, "cmd": X.P.CMD8, "bond": X.BOND3, "crypto": X.P.CRYPTO2}
    c0 = cells[cells["param"] == 0]
    out["family_net_bp_regime"] = {k: fmt(c0[c0["sym"].isin(v)]["pnl_net"].mean()) for k, v in fam.items()}
    out["family_exposure_regime"] = {k: fmt(c0[c0["sym"].isin(v)]["exp"].mean()) for k, v in fam.items()}
    return out


if __name__ == "__main__":
    S14.run_main(SPEC, strategy, HERE, min_syms=40, judge=judge, summarize_extra=extra, runner_holder=RUNNER)
