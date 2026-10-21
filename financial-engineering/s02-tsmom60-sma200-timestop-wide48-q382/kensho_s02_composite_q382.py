#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q382 S02: 48 銘柄 D1 の TSMOM60 × SMA200 同符号ゲート × 時間ストップ 20 日の合成（部品は既存値で固定・掃引なし）。
事前登録の正本は SPEC。Runner 型（ボラ・ターゲティングは Runner の規程モード rule_mode が size_weights で自動で当てる）。
実行: --smoke --B 5（経路確認）／ 本番（B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, Runner, tsmom_pos, sma_pos, syms_available, write_result, by_year_stats, fmt, GROUPS  # noqa: E402
from s04ml import WIDE48_COST_REL  # noqa: E402

WIDE48 = GROUPS["wide48"]

SPEC = Spec(
    qid="Q382",
    question="48 銘柄 D1 の TSMOM60 × SMA200 同符号ゲート × 時間ストップ 20 日の合成（部品は既存値で固定・掃引なし）は規程モードの封印前の前後半で t≥2 かつ最大下落 −6% 以内か",
    hypothesis=(
        "pos[t] = sign(close[t]−close[t−60]) を、sign(close[t]−SMA200[t]) と同符号のときだけ採用（違えば 0）。"
        "同じ向きを 20 日持ったら 0 にし、TSMOM60 の符号が反転するまで再建玉しない（Q251 の時間ストップ）。"
        "ボラ・ターゲティング（Q205）は規程モードの size_weights（σ60 等リスク・σ目標 0.5%）が当てる。"
        "合成の規程モード損益が封印前の前後半とも年単位 t≥2 で、最大下落が −6% 以内"
    ),
    reject_if=(
        "支持: 規程モードの gate.pass（t_pre≥2 かつ t_post≥2 かつ max_dd≥−6%）かつ 生（等金額）の pre・post bp_net>0 かつ Holm 後 p<0.05。"
        "棄却: 全期間 z<1、または規程モードの max_dd<−20%（S07 本体 Q367 の −95% と同じ型＝部品で救えない）。ほか → 未確定"
    ),
    syms=list(WIDE48), kind="D1_fromH1",
    params=[{"L": 60, "sma": 200, "hold": 20}],
    main_param=0, n_tests=2, warmup=250,
    B=500, null_kind="circ_shift", null_min_shift=120, split_year=2017, start="2008-01-01",
    cost_rel=dict(WIDE48_COST_REL),  # COST_RT に無い 34 銘柄の往復コスト（比）。既定だと往復 30bp（暗号並み）に落ちる
    discarded="2（MA200 を株価指数だけに当てる案＝Q151 の確定範囲だが族で分けると掃引になる、時間ストップ N=10/40＝Q251 の副次）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source=(
        "[[検証/_基盤/戦略台帳]] S02／知見 [[日足順張りの建玉を直前60日の実現ボラの逆数で規模調整すると年ごとのシャープが約0.09上がる]]（Q205 確定）／"
        "知見 [[株価指数の200日線と12か月モメンタムの保有現金規則だけが同じ露出の無作為なタイミングより最大下落が浅く、商品と為替では下落の軽さは露出の低さで説明できる]]（Q151 確定）／"
        "Q251（時間ストップは下落を浅くするが純損益は上げない・支持）"
    ),
    data="48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は FX/システムトレード、それ以外は 検証/_データ/raw/D1。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="生（等金額）の年単位 bp（コスト 0 と段階1）・t・Sharpe・最大下落・露出と、規程モード（rule_mode.fintokei: t_pre/t_post・max_dd・worst_day・stops）。族別（fx22/idx13/cmd8/bond3）は extra に記述",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 全 48 銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm",
    prior_art=(
        "WebSearch 2026-10-22「time series momentum 200-day moving average agreement filter time stop composite multi-asset drawdown」: "
        "Quantpedia（商品の絶対トレンドフィルタ）、Alpha Architect（TSMOM の下落）、Antonacci の dual momentum。TSMOM60×SMA200 同符号×時間ストップの 3 部品を 48 銘柄 D1 で合成し固定最大損失の下で測った研究は見つからない"
    ),
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 9 本目（S02 合成）", designer="Fable", coder="Fable",
)


def strategy(df, p, sym):
    """合図: TSMOM(L) と SMA(sma) 位置が同符号のときだけ ±1。同じ向きを hold 日持ったら 0、TSMOM 符号が反転するまで再建玉しない。shift しない。"""
    c = df["close"].values
    ts = tsmom_pos(c, p["L"]); ma = sma_pos(c, p["sma"])
    base = np.where((ts != 0) & (ts == ma), ts, 0.0)
    n = len(c); pos = np.zeros(n); cur = 0.0; age = 0; locked = 0.0  # locked: 時間ストップ後に再建玉を禁じている向き
    for t in range(n):
        s = base[t]
        if locked != 0.0 and ts[t] != locked:
            locked = 0.0                       # TSMOM の符号が反転 → 禁止を解く
        if s == locked and s != 0.0:
            s = 0.0                            # 禁止中の向きは建てない
        if s != 0.0 and s == cur:
            age += 1
            if age >= p["hold"]:
                locked = cur; cur = 0.0; age = 0; s = 0.0
        elif s != 0.0:
            cur = s; age = 1
        else:
            cur = 0.0; age = 0
        pos[t] = cur
    return pos


def _summarize_families(cells, spec):
    out = {}
    sy = spec.split_year
    for fam in ("fx22", "idx13", "cmd8", "bond3"):
        ci = cells[(cells["param"] == 0) & (cells["sym"].isin(GROUPS[fam]))]
        if ci.empty:
            continue
        for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, sy), "post": (sy, 9999)}.items():
            b = by_year_stats(ci, "pnl_net", y0=y0, y1=y1)
            out[f"{fam}_{pn}"] = {"n_years": b["n_years"], "n_syms": int(ci["sym"].nunique()), "bp_net": fmt(b["mean"]), "t_year": fmt(b["t"])}
    out["exposure_all"] = fmt(cells.loc[cells["param"] == 0, "exp"].mean())
    return out


def judge(res, spec):
    m = res["main"]; rm = res.get("rule_mode", {}); g = rm.get("gate", {}); f = rm.get("fintokei", {})
    pre, post, allp = m.get("pre", {}), m.get("post", {}), m.get("all", {})
    if any(v is None for v in [pre.get("bp_net"), post.get("bp_net"), pre.get("p_holm"), post.get("p_holm"), allp.get("z")]) or not f:
        return "未確定: 計算できない（期間・銘柄の不足か帰無の退化）"
    if allp["z"] < 1 or (f.get("max_dd") is not None and f["max_dd"] < -0.20):
        return "棄却: 全期間 z<1 または規程モードの max_dd<−20%"
    if g.get("pass") and pre["bp_net"] > 0 and post["bp_net"] > 0 and pre["p_holm"] < 0.05 and post["p_holm"] < 0.05:
        return "支持: 規程モード gate.pass かつ生の前後半 bp_net>0・Holm 後 p<0.05"
    return "未確定"


def _data_guard():
    ok, missing = syms_available(WIDE48, kind="D1_fromH1")
    if len(ok) < 40:
        write_result(SPEC.qid, {"status": "データ待ち", "qid": SPEC.qid, "n_ok": len(ok), "n_required": 40, "n_total": len(WIDE48), "ok": ok, "missing": missing,
                                "note": "S07 データガード: ok<40 のため本番を実行しない。release で待ちに戻す。"}, smoke=False, here=HERE)
        print(f"データ待ち: ok={len(ok)}/{len(WIDE48)} missing={len(missing)}"); sys.exit(2)


if __name__ == "__main__":
    if "--smoke" not in sys.argv and "--readme" not in sys.argv and "--idea-row" not in sys.argv:
        _data_guard()
    Runner(SPEC, strategy, judge=judge, summarize_extra=_summarize_families, here=HERE).execute()
