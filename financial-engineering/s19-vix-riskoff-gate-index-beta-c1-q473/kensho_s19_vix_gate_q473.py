#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S19: VIX リスクオフ・ゲート。株価指数 10 の買い持ち β（Q468 params 1）を、VIX（t−1 暦日の終値）が直近 250 観測の 80 分位以下の日だけ持つ。
★ A の 1 源（CBOE ボラ指数・FRED・2026-10-24 取得）の最初の 1 本。関門は規程 C1（σ0.25%/日）＋保有コスト年 4%。
事前登録の正本は SPEC。実行: --smoke --B 5／本番 python3 kensho_s19_vix_gate_q473.py（B=500）／--readme
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import Spec, Runner, fmt, by_year_stats  # noqa: E402
from fe_core import _paths as P  # noqa: E402

IDX10 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "AUS200", "SUI20"]
HOLD = 0.04
VOL_DIR = os.path.join(P.WS, "検証", "_データ", "raw", "vol")
_VIX_CACHE = {}


def load_vix(smoke=False, rng=None):
    """VIX 日次終値（date→close）。smoke は合成（対数 AR(1)・平均 18）。"""
    if "s" in _VIX_CACHE and not smoke:
        return _VIX_CACHE["s"]
    if smoke:
        n = 6000; x = np.zeros(n); x[0] = np.log(18.0)
        for i in range(1, n):
            x[i] = np.log(18.0) + 0.97 * (x[i - 1] - np.log(18.0)) + rng.normal(0, 0.06)
        s = pd.Series(np.exp(x), index=pd.date_range("2008-01-01", periods=n, freq="D"))
        return s
    df = pd.read_csv(os.path.join(VOL_DIR, "VIX.csv")); s = pd.Series(df["close"].values, index=pd.to_datetime(df["date"]))
    _VIX_CACHE["s"] = s
    return s


def vix_gate(times, p, smoke=False, rng=None):
    """times（UTC 日足の time）ごとに、t−1 暦日までに既知の VIX がその時点までの直近 win 観測の q 分位以下なら 1、超えれば 0。
    VIX の分位は VIX 系列自身の rolling（shift 1 で当日を含めない）。VIX が未知（開始前）の日は 0。"""
    v = load_vix(smoke, rng)
    thr = v.rolling(p["win"], min_periods=p["win"]).quantile(p["q"]).shift(1)   # t の閾値は t−1 までの win 観測
    on = (v <= thr).astype(float).where(thr.notna(), np.nan)
    # D1 の足 time（UTC 0:00 区切り。日付 d の足は d の 0:00〜24:00）に対し、暦日 d−1 までの VIX（asof）を使う
    t = pd.to_datetime(pd.Series(times)).dt.floor("D") - pd.Timedelta(days=1)
    g = on.reindex(on.index.union(t.values)).sort_index().ffill().reindex(t.values).to_numpy()
    return np.nan_to_num(g, nan=0.0)


SPEC = Spec(
    qid="Q473",
    question="S19 VIX リスクオフ・ゲート: 株価指数 10 の買い持ち β を VIX（t−1）が直近 250 観測の 80 分位以下の日だけ持つと、常時買い持ち（Q468 params 1）より規程 C1 で t_all・max_dd が良くなり、C1 関門（前後半 t≥2・max_dd −6%）を通るか",
    hypothesis=(
        "pos[t]=1{VIX[t−1] ≤ Q80(VIX[t−251..t−1])}（指数 10 に同じゲート）。高 VIX 局面は株式のボラが高く平均リターンが低い（Moreira・Muir 2017 のボラ管理）ので、"
        "リスクオフ局面を外すと規程 C1（σ60 で規模化・保有コスト 4%）の下で t が上がり max_dd が浅くなる。封印前 2012-02〜2024-06・境 2017"
    ),
    reject_if=(
        "判定は規程モード C1（保有コスト 4% 込み）の main_param=0（ゲートあり）。"
        "支持: gate.pass（t_pre≥2 かつ t_post≥2 かつ max_dd≥−6%）かつ ゲートありが params 1（ゲートなし・同じ実行）より t_all と max_dd の両方で良い。"
        "棄却: ゲートありの規程 t_all が ゲートなし以下、または 等金額 z<1。ほか → 未確定。params 2（分位 0.9）・3（窓 120）は記述で判定に使わない"
    ),
    syms=list(IDX10), kind="D1_fromH1",
    params=[{"win": 250, "q": 0.80, "gate": True}, {"win": 250, "q": 0.80, "gate": False}, {"win": 250, "q": 0.90, "gate": True}, {"win": 120, "q": 0.80, "gate": True}],
    main_param=0, n_tests=2, warmup=60,
    B=500, null_kind="circ_shift", null_min_shift=120, split_year=2017, start="2012-02-01", end="2024-07-01",
    settings={"rule_set": "fintokei_c1", "holding_cost_annual": {s: HOLD for s in IDX10},
              "family": "リスクプレミアム（買い持ち）×ボラ局面ゲート", "family_trials": 3, "data_source_added": "CBOE VIX（FRED VIXCLS・_データ/raw/vol/VIX.csv・1990〜）",
              "gate": "C1 σ0.25%/日・max_dd −6%・前後半 t≥2", "point_in_time": "VIX は t−1 暦日の終値（US 16:15 ET 確定）。閾値は t−1 までの rolling 分位"},
    discarded=(
        "3（族内の試行は params のゲート 3 本〔main・分位 0.9・窓 120〕に固定）。捨てた案: FX22 TSMOM60 と BTC/ETH TSMOM60 に同じゲート（β で効けば別 ID）、"
        "キャリー族への VIX ゲート（Brunnermeier ほか 2008 の線。スワップ実装が要るので別 ID）、VIX 水準で連続的に規模を変える（Moreira・Muir の 1/σ² は S04b 系で σ60 と差が無かった）"
    ),
    delegation="なし（Fable 設計・実行 → Opus 見直し）。実行者は VIX の asof（t−1）が未来を見ていないことを spec の point_in_time で確かめる",
    source=(
        "[[検証/_基盤/戦略台帳]] S19（★ A・2026-10-24）／Q468（S17 β: C1 単独 t 1.41・max_dd −9.3%・指数のみ Sharpe 0.38）／"
        "Moreira・Muir 2017「Volatility-Managed Portfolios」(JF)／Brunnermeier・Nagel・Pedersen 2008「Carry Trades and Currency Crashes」（VIX 上昇とキャリー崩れ）"
    ),
    data="指数 10 の D1（_データ/raw/D1・2012-02-01〜2024-06-30）＋ VIX 日次終値（_データ/raw/vol/VIX.csv・FRED VIXCLS）。保有コスト年 4%（Q468 と同じ）",
    measure="規程 C1 の t（all/pre/post）・mean_bp・max_dd・worst_day・stops（判定）、ゲートなし（params 1）との差。等金額の年単位 bp・t・z。extra: ゲートが閉じていた日の比率・年別、ゲート閉中の指数リターン平均（記述）",
    null_desc="ゲート（0/1）の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp の帰無分布 → z・perm_p。ゲートの「位置」に情報が無ければ観測は帰無の中央",
    prior_art=(
        "WebSearch 2026-10-24「VIX threshold timing equity index exposure risk-off filter backtest out-of-sample evidence volatility managed portfolios Moreira Muir」: "
        "Moreira・Muir 2017（前月の実現分散の逆数で規模を変えると株式などでシャープが上がる）、追試の学位論文・WP（ミューチュアルファンドでは効果が弱い）。"
        "VIX の rolling 分位の 0/1 ゲートを CFD 保有コスト・固定最大損失・σ0.25% の下で、2012〜2024-06 の前後半で見た追試は見当たらない。itiger 等のニュースは根拠にしない"
    ),
    batch="/lab-plan 2026-10-24（Fable・★ A の 1 源・N=1）",
    designer="Fable", coder="Fable",
)


def strategy(df, p, sym):
    n = len(df)
    if not p.get("gate", True):
        return np.ones(n)
    return vix_gate(df["time"].values, p, smoke=getattr(strategy, "smoke", False), rng=getattr(strategy, "rng", None))


def judge(res, spec):
    rm = res.get("rule_mode") or {}; f = rm.get("fintokei") or {}; g = rm.get("gate") or {}
    if "error" in rm or not f or rm.get("rule_set") != "fintokei_c1":
        return "未確定: 規程モード C1 が計算できない"
    base = (res.get("extra") or {}).get("ungated_rule_mode") or {}
    z = ((res.get("main") or {}).get("all") or {}).get("z")
    ok = lambda v: v is not None and v == v  # noqa: E731
    better = ok(base.get("t_all")) and f["t_all"] > base["t_all"] and f["max_dd"] > base["max_dd"]
    if g.get("pass") and better:
        return "支持: 規程 C1 で関門通過、かつゲートなしより t_all・max_dd とも良い"
    if (ok(base.get("t_all")) and f["t_all"] <= base["t_all"]) or (ok(z) and z < 1):
        return f"棄却: ゲートありの規程 t_all={fmt(f['t_all'])} ≤ なし {fmt(base.get('t_all'))}、または 等金額 z={fmt(z)}<1"
    return f"未確定: 規程 C1 t_pre={fmt(f.get('t_pre'))} t_post={fmt(f.get('t_post'))} max_dd={fmt(f.get('max_dd'))}（なし: t_all {fmt(base.get('t_all'))} max_dd {fmt(base.get('max_dd'))}）"


def summarize_extra(cells, spec):
    out = {}
    # ゲートの閉じていた日の比率（US500 の行で代表）
    c0 = cells[(cells["param"] == 0) & (cells["sym"] == IDX10[0])]
    out["gate_closed_ratio"] = fmt(1.0 - c0["exp"].mean()) if len(c0) else None
    out["gate_closed_by_year"] = {int(y): fmt(1.0 - v) for y, v in c0.groupby("year")["exp"].mean().items()} if len(c0) else {}
    # ゲート閉中と開中の指数リターン平均（等金額 gross・params 1 の行から）
    c1 = cells[cells["param"] == 1].merge(cells[cells["param"] == 0][["time", "sym", "exp"]].rename(columns={"exp": "gate"}), on=["time", "sym"], how="left")
    for nm, m in (("open", c1["gate"] > 0.5), ("closed", c1["gate"] <= 0.5)):
        d = c1[m]
        out[f"index_ret_bp_gate_{nm}"] = {"mean": fmt(d["pnl_gross"].mean()), "n": int(d["pnl_gross"].notna().sum()), "std": fmt(d["pnl_gross"].std())}
    # 各 params の等金額年単位
    for pi in range(len(spec.params)):
        d = cells[cells["param"] == pi]
        b = by_year_stats(d, "pnl_net"); out[f"p{pi}_eq_all"] = {"bp_net": fmt(b["mean"]), "t_year": fmt(b["t"])}
    return out


if __name__ == "__main__":
    args_smoke = "--smoke" in sys.argv
    strategy.smoke = args_smoke; strategy.rng = np.random.default_rng(0) if args_smoke else None
    R = Runner(SPEC, strategy, judge=judge, summarize_extra=summarize_extra, here=HERE)
    # ゲートなし（params 1）の規程 C1 を extra に足す: run をラップ
    _orig_run = R.run

    def run_with_base(args, rng):
        res, csvs = _orig_run(args, rng)
        try:
            mp = SPEC.main_param; SPEC.main_param = 1
            from fe_core import syms_available
            syms, _ = syms_available(SPEC.syms, kind="D1_fromH1", smoke=args.smoke)
            dfs = {s: R._load(s, args.smoke, rng) for s in syms}
            rm1 = R._rule_mode(dfs); SPEC.main_param = mp
            res.setdefault("extra", {})["ungated_rule_mode"] = {k: v for k, v in rm1["fintokei"].items() if k != "rules"}
            res["extra"]["ungated_gate"] = rm1["gate"]
        except Exception as e:  # noqa: BLE001
            SPEC.main_param = 0; res.setdefault("extra", {})["ungated_rule_mode"] = {"error": str(e)[:200]}
        suffix = "（data_health に failed/gaps あり: 確定にする前に点検）" if "確定にする前に点検" in res.get("machine_verdict", "") else ""
        res["machine_verdict"] = judge(res, SPEC) + suffix
        return res, csvs

    R.run = run_with_base
    R.execute()
