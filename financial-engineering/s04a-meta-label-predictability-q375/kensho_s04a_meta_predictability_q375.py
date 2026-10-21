#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q375 S04a 前提: TSMOM60 のメタラベルは、そもそも t までの特徴量で当てられるか（族の切除 × 地平線 k）。
事前登録の正本は SPEC。土台を直接使う型（fe_core.ml、共通部 _s04_common/s04ml.py）。損益ではなく予測の質（AUC・IC）が主問い。
【出典】[[検証/_基盤/戦略台帳]] S04a／López de Prado 2018 AFML ch.3／知見 [[過去リターンとMA乖離と実現ボラだけを入力にした木モデルの12時間先予測はEURUSDの1時間足で順位情報も損益も取り出せずコスト以前に信号がない]]
【仮説】メタラベル y=1{TSMOM60 に乗った t→t+k の損益>0} はリッジ（α=1）で、評価窓（2012〜2024-06）の AUC がラベル並べ替え帰無より高い。族の切除で寄与する族が分かる。
【データ】wide48 D1_fromH1（2008-01〜）。封印: time<2024-07-01。年次ウォークフォワード（学習 4 年固定長・embargo=max(10,k)）。
【定義】格子 = 特徴量 {mom, vol, range, dow, all} × k {5, 10, 20} = 15 試行（ridge α=1 のみ）。main（事前固定）= (all, k=5)。
【測るもの】試行ごとの AUC（評価窓全体）、年ごとの AUC の平均と t、IC（順位相関）と日次 IC の nw_t（lag=k）。main のラベル並べ替え帰無 B=50 の AUC 分布。
  参考として main の p̂ を clip 変換で乗せた規程モード損益（判定には使わない）。
【帰無】ラベル並べ替え（学習窓のラベルを年内で並べ替えて学習し直す）→ main の AUC の帰無分布 → z・perm_p。
【判定（事前固定・変更禁止）】支持: main の AUC が perm_p<0.05 かつ 年ごとの AUC>0.5 の年が 2/3 以上 かつ 前後半（2012〜16／2017〜24-06）とも年平均 AUC>0.5。
  棄却: main の帰無 z<1、または前後半のどちらかで年平均 AUC≤0.5。ほか → 未確定。
【捨てた案の数】2（GBM を含める案＝Q374 で数える、横断族 xsec を足す案＝make_features に無いので fe_core に足してから）
【知識の締め切り】Claude 2026-06。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）
【実装】python3 kensho_s04a_meta_predictability_q375.py（--B 50 既定・リッジだけなので数分）。--smoke で合成 3 銘柄・B 2。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, parse_args, write_result, meta_label, tsmom_pos, TrialLog, null_summary, fmt, tstat, render_readme, render_idea_row, sanitize  # noqa: E402
import s04ml as M  # noqa: E402

TRAIN_YEARS = 4
FEATURE_SETS = ["mom", "vol", "range", "dow", "all"]
KS = [5, 10, 20]
MODEL = ("ridge", 1.0)
MAIN = ("all", 5)

SPEC = Spec(
    qid="Q375",
    question="48 銘柄 D1 の TSMOM60 メタラベル（k∈{5,10,20}）は族の切除（mom／vol／range／dow／全部）のリッジで AUC・IC がラベル並べ替え帰無より高いか（メタラベルはそもそも当てられるか）",
    hypothesis="main=(all, k=5) のリッジの評価窓 AUC がラベル並べ替え帰無より高く、前後半とも年平均 AUC>0.5。族の切除で寄与する族（mom／vol／range／dow）が分かる",
    reject_if="支持: main の AUC の perm_p<0.05 かつ 年ごとの AUC>0.5 の年が 2/3 以上 かつ 前後半とも年平均 AUC>0.5。棄却: main の帰無 z<1、または前後半のどちらかで年平均 AUC≤0.5。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{"fset": f, "k": k} for f in FEATURE_SETS for k in KS],
    main_param=FEATURE_SETS.index(MAIN[0]) * 3 + KS.index(MAIN[1]), n_tests=1, warmup=250, B=50, null_kind="none", start="2008-01-01",
    discarded="2（GBM を含める・xsec 族を足す）", delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] S04a／López de Prado 2018 AFML ch.3／知見 [[過去リターンとMA乖離と実現ボラだけを入力にした木モデルの12時間先予測はEURUSDの1時間足で順位情報も損益も取り出せずコスト以前に信号がない]]",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="15 試行の AUC（評価窓全体・年ごと）、IC と日次 IC の nw_t、main のラベル並べ替え帰無の AUC 分布（z・perm_p）。参考: main の clip 変換の規程モード損益",
    null_desc="ラベル並べ替え（学習窓のメタラベルを年内で並べ替えて学習し直す）B=50 → main の AUC の帰無分布",
    prior_art="WebSearch 2026-10-22「meta-labeling predictability feature importance trend following secondary model AUC」: Hudson & Thames の特徴量重要度の解説、Insper の追試（二次モデルの性能は弱い）。AUC の値と族の切除を順張り合図で系統的に報告した研究は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 2 本目（S04a 前提）", designer="Fable", coder="Fable",
)


def _auc_by_year(pred, Y):
    st = pd.concat([pred.stack().rename("p"), Y.stack().rename("y")], axis=1).dropna()
    if st.empty:
        return {"auc_all": None, "years": {}, "n": 0}
    yrs = st.index.get_level_values(0).year
    by = {int(k): fmt(M.auc(g["p"], g["y"])) for k, g in st.groupby(yrs)}
    return {"auc_all": fmt(M.auc(st["p"], st["y"])), "years": by, "n": int(len(st))}


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    sig = pd.DataFrame({s: pd.Series(tsmom_pos(df["close"].values, 60), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()
    log = TrialLog(max_trials=50); trials = {}; main_pred = None; main_Y = None; panels = {}
    for k in KS:
        tf = lambda df, k=k: meta_label(df, tsmom_pos(df["close"].values, 60), k)
        X, y, meta = M.build_panel(dfs, tf); panels[k] = (X, y, meta)
        Y = M.target_wide(dfs, tf)
        for fset in FEATURE_SETS:
            pred = M.wf_predict(X, y, meta, MODEL, M.select_cols(X, fset), TRAIN_YEARS, max(10, k))
            a = _auc_by_year(pred, Y); ic = M.ic_by_year(pred, Y)
            name = f"{fset}|k{k}"
            log.add({"fset": fset, "k": k}, a["auc_all"] if a["auc_all"] is not None else 0.5)
            trials[name] = {"auc": a, "ic": ic}
            if (fset, k) == MAIN:
                main_pred, main_Y = pred, Y
    eval_start = M.eval_start_of(panels[MAIN[1]][2], TRAIN_YEARS)
    X, y, meta = panels[MAIN[1]]
    null = []
    for b in range(args.B):
        pn = M.wf_predict(X, y, meta, MODEL, M.select_cols(X, MAIN[0]), TRAIN_YEARS, max(10, MAIN[1]), label_perm_rng=rng)
        null.append(_auc_by_year(pn, main_Y)["auc_all"])
    main_name = f"{MAIN[0]}|k{MAIN[1]}"
    obs = trials[main_name]["auc"]["auc_all"]
    ns = null_summary(obs if obs is not None else np.nan, np.array([v if v is not None else np.nan for v in null], float)) if len(null) >= 2 else {"B": len(null)}
    yrs = trials[main_name]["auc"]["years"]
    pre = [v for yy, v in yrs.items() if yy < M.SPLIT_YEAR and v is not None]; post = [v for yy, v in yrs.items() if yy >= M.SPLIT_YEAR and v is not None]
    ref = M.strip_ports(M.eval_portfolio(M.convert_meta(main_pred, sig, "clip"), R, COST, eval_start))
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs), "eval_start": str(eval_start.date()),
           "main_name": main_name, "main": {"auc_all": obs, "auc_pre_mean": fmt(np.mean(pre)) if pre else None, "auc_post_mean": fmt(np.mean(post)) if post else None,
                                            "frac_years_auc_gt_05": fmt(np.mean([v > 0.5 for v in pre + post])) if (pre + post) else None, "n_years": len(pre + post),
                                            "auc_year_t_vs_05": fmt(tstat(np.array(pre + post) - 0.5)) if len(pre + post) > 1 else None},
           "null": ns, "ref_pnl_clip": ref, **log.to_json(), "trials_detail": trials,
           "multiple_comparisons": "判定は main 1 本（AUC）。15 試行は記述", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(res):
    m = res["main"]; z = res["null"].get("z"); p = res["null"].get("p_perm")
    if m["auc_pre_mean"] is None or m["auc_post_mean"] is None or m["frac_years_auc_gt_05"] is None:
        return "未確定: 計算できない（評価期間の不足）"
    if (z is not None and z < 1) or m["auc_pre_mean"] <= 0.5 or m["auc_post_mean"] <= 0.5:
        return "棄却: 帰無 z<1 か、前後半のどちらかで年平均 AUC≤0.5"
    if p is not None and p < 0.05 and m["frac_years_auc_gt_05"] >= 2 / 3:
        return "支持: perm_p<0.05 かつ AUC>0.5 の年が 2/3 以上 かつ 前後半とも年平均 AUC>0.5"
    return "未確定"


if __name__ == "__main__":
    script = os.path.basename(__file__)
    if "--readme" in sys.argv:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型（fe_core.ml・_s04_common/s04ml.py）")); print("wrote README.md"); sys.exit(0)
    if "--idea-row" in sys.argv:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE))); sys.exit(0)
    args = parse_args(default_B=SPEC.B)
    if not args.smoke:
        M.data_guard(SPEC.qid, HERE)
    else:
        args.B = min(args.B, 2)
    rng = np.random.default_rng(args.seed)
    res = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    print("machine_verdict:", res["machine_verdict"])
    print(write_result(SPEC.qid, sanitize(res), args.smoke, here=HERE))
