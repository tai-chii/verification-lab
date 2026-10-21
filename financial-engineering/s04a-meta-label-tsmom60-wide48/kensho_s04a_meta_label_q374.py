#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q374 S04a 本体: 48 銘柄 D1 の TSMOM60 合図にメタラベリング（乗るか・規模を ML が決める）を重ねる。
事前登録の正本は SPEC。土台を直接使う型（fe_core.ml + fe_core.risk、共通部 _s04_common/s04ml.py）。
【出典】[[検証/_基盤/戦略台帳]] S04a（2026-10-21）／López de Prado 2018 AFML ch.3 メタラベリング／主張カード [[Bailey2017-1_期間内の最良が期間外で中央値より下になる割合でバックテストの過剰適合の確率を測れる]]
【仮説】合図は TSMOM60 の符号。メタラベル y=1{合図に乗った t→t+5 の損益>0}（fe_core.meta_label, k=5）を特徴量（mom/vol/range/dow・t まで）で予測し、
  p̂ を「乗る規模 [0,1]」に変換して合図に掛ける。規程モード（RULES_FINTOKEI）の損益が、同じ評価期間の S07 本体（等リスク TSMOM60）とゼロをコスト後に上回る。
【データ】wide48 D1_fromH1（2008-01〜）。封印: time<2024-07-01 で panel を切る。評価は年次ウォークフォワード（学習 4 年固定長・embargo 10 日≥k）の評価窓＝2012〜2024-06。
【定義】格子 = 特徴量 {mom, mom+vol, all} × モデル {ridge α=1, ridge α=100, gbm(depth3,iter200)} × 変換 {sign, clip, kelly} = 27 試行（TrialLog max 50）。
  main（事前固定）= (all, ridge α=1, clip)。変換の天井は RULES_FINTOKEI の定数のまま。
【測るもの】main の規程モード: 前半（2012〜2016）・後半（2017〜2024-06）の年単位 t、mean_bp、max_dd、worst_day、stops、Sharpe。S07・ゼロのベースラインを同じ鍵で。IC（p̂ とメタラベル）・AUC を併記。等金額（RULES_NONE）も併記。
【帰無】ラベル並べ替え（学習窓のメタラベルを年内で並べ替えて学習し直す）B 回 → main の規程モード mean_bp（評価期間全体）の帰無分布 → z・perm_p。
【判定（事前固定・変更禁止）】支持: main の規程モードが前後半とも mean_bp が S07 本体を上回り（かつ >0）、t_pre≥2 かつ t_post≥2、max_dd≥−6%、perm_p<0.05、PBO<0.5。
  棄却: main が前後半のどちらかで S07 本体を上回らない、または帰無 z<1。ほか → 未確定。
【捨てた案の数】3（GBM を main にする案、k=20 の案、負の規模＝逆張りを許す案。いずれも「リッジを先に・天井は定数・方向は合図」の原則に反する）
【知識の締め切り】Claude 2026-06。規則は固定で相場観は使わない。評価期間は締め切りより前。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行。実行者は trials の n=27・pbo・null の B を JSON で確かめる）
【実装】python3 kensho_s04a_meta_label_q374.py（--B 20 既定・GBM 9 試行 × 13 年で十数分）。--smoke で合成 3 銘柄・B 2。--readme で README。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))
from fe_core import Spec, parse_args, write_result, meta_label, tsmom_pos, pbo_cscv, TrialLog, null_summary, fmt, render_readme, render_idea_row, sanitize  # noqa: E402
import s04ml as M  # noqa: E402

K = 5
TRAIN_YEARS = 4
EMBARGO = 10
FEATURE_SETS = ["mom", "mom+vol", "all"]
MODELS = [("ridge", 1.0), ("ridge", 100.0), ("gbm", {"max_depth": 3, "max_iter": 200})]
RULES = ["sign", "clip", "kelly"]
MAIN = ("all", ("ridge", 1.0), "clip")

SPEC = Spec(
    qid="Q374",
    question="48 銘柄 D1 の TSMOM60 合図にメタラベリング（k=5・族 mom/vol/range/dow・リッジ→GBM・予測→規模 3 通り・格子 27）を重ねると、規程モードの封印前の前後半で S07 本体とゼロをコスト後に上回り年単位 t≥2 か",
    hypothesis="メタラベル y=1{TSMOM60 に乗った t→t+5 の損益>0} を特徴量（t まで）で予測し p̂→乗る規模 [0,1]×合図。main=(all, ridge α=1, clip) の規程モード損益が評価期間（2012〜2024-06）の前後半とも S07 等リスク TSMOM60 とゼロをコスト後に上回る",
    reject_if="支持: main の規程モードが前後半とも mean_bp で S07 本体を上回り（かつ >0）、t_pre≥2 かつ t_post≥2、max_dd≥−6%、ラベル並べ替え perm_p<0.05、PBO<0.5。棄却: main が前後半のどちらかで S07 本体を上回らない、または帰無 z<1。ほか → 未確定",
    syms=list(M.WIDE48), kind="D1_fromH1", params=[{"fset": f, "model": m, "rule": r} for f in FEATURE_SETS for m in MODELS for r in RULES],
    main_param=FEATURE_SETS.index(MAIN[0]) * 9 + MODELS.index(MAIN[1]) * 3 + RULES.index(MAIN[2]), n_tests=2, warmup=250, B=20, null_kind="none", start="2008-01-01",
    discarded="3（GBM を main にする・k=20・負の規模を許す）", delegation="なし（Fable 設計 → Sonnet 実行。trials n=27・pbo・B を JSON で確認）",
    source="[[検証/_基盤/戦略台帳]] S04a／López de Prado 2018 AFML ch.3／[[Bailey2017-1_期間内の最良が期間外で中央値より下になる割合でバックテストの過剰適合の確率を測れる]]",
    data="wide48 D1_fromH1（2008-01〜、封印 2024-07-01 で切る）。既存 15 銘柄は FX/システムトレード、それ以外は 検証/_データ/raw/D1。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない",
    measure="main の規程モード（RULES_FINTOKEI）: 前半 2012〜2016・後半 2017〜2024-06 の年単位 t・mean_bp・max_dd・worst_day・stops・Sharpe。同じ鍵で S07 本体（等リスク TSMOM60）とゼロ。IC・AUC・等金額版・27 試行の TrialLog・PBO（CSCV S=8）",
    null_desc="ラベル並べ替え（学習窓のメタラベルを年内で並べ替えて学習し直す）B=20 → main の規程モード mean_bp の帰無分布 → z・perm_p",
    prior_art="WebSearch 2026-10-22「meta-labeling time series momentum trend following gradient boosting futures bet sizing」: 近いのは Nousiainen 2022（Donchian × RF・サイズを確率で）、Insper の meta-labeling 追試（改善は弱い）、Lim・Zohren・Roberts 2019 DMN（深層でサイズ学習）。48 銘柄 D1・TSMOM60・規程モード（固定最大損失）の下での独立追試は見つからない",
    batch="/lab-plan ターミナル版 2026-10-22・N=10 の 1 本目（S04a 本体）", designer="Fable", coder="Fable",
)


def run(args, rng):
    t0 = M._time.time()
    dfs, missing, dh = M.load_all(SPEC.syms, args.smoke, rng, start=SPEC.start)
    C, R, COST = M.wide_tables(dfs)
    sig = pd.DataFrame({s: pd.Series(tsmom_pos(df["close"].values, 60), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()
    X, y, meta = M.build_panel(dfs, lambda df: meta_label(df, tsmom_pos(df["close"].values, 60), K))
    eval_start = M.eval_start_of(meta, TRAIN_YEARS)
    Ywide = M.target_wide(dfs, lambda df: meta_label(df, tsmom_pos(df["close"].values, 60), K))
    _, s07, zero = M.baseline_tsmom(dfs, R, COST, eval_start, L=60)

    log = TrialLog(max_trials=50); trials = {}; ports = []; preds = {}
    for fset in FEATURE_SETS:
        for model in MODELS:
            key = (fset, str(model))
            if key not in preds:
                preds[key] = M.wf_predict(X, y, meta, model, M.select_cols(X, fset), TRAIN_YEARS, EMBARGO, classify=(model[0] == "gbm"))
            p = preds[key]
            for rule in RULES:
                pos = M.convert_meta(p, sig, rule)
                ev = M.eval_portfolio(pos, R, COST, eval_start)
                name = f"{fset}|{model[0]}:{model[1] if model[0]=='ridge' else 'd3i200'}|{rule}"
                log.add({"fset": fset, "model": str(model), "rule": rule}, ev["fintokei"]["mean_bp"] or 0.0)
                trials[name] = {"fintokei": {k: v for k, v in ev["fintokei"].items() if k not in ("years", "rules")}, "none_mean_bp": ev["none"]["mean_bp"], "none_t_all": ev["none"]["t_all"], "gate": ev["gate"]}
                ports.append(ev["port_fintokei"].rename(name))
    main_name = f"{MAIN[0]}|ridge:{MAIN[1][1]}|{MAIN[2]}"
    p_main = preds[(MAIN[0], str(MAIN[1]))]
    pos_main = M.convert_meta(p_main, sig, MAIN[2])
    main = M.eval_portfolio(pos_main, R, COST, eval_start)
    ic = M.ic_by_year(p_main, Ywide)
    st = pd.concat([p_main.stack().rename("p"), Ywide.stack().rename("y")], axis=1).dropna()
    auc_all = M.auc(st["p"], st["y"]) if len(st) else float("nan")
    # 帰無: ラベル並べ替え（main のモデルだけ学習し直す）
    null = []
    for b in range(args.B):
        pn = M.wf_predict(X, y, meta, MAIN[1], M.select_cols(X, MAIN[0]), TRAIN_YEARS, EMBARGO, label_perm_rng=rng)
        evn = M.eval_portfolio(M.convert_meta(pn, sig, MAIN[2]), R, COST, eval_start)
        null.append(evn["fintokei"]["mean_bp"] if evn["fintokei"]["mean_bp"] is not None else np.nan)
    ns = null_summary(main["fintokei"]["mean_bp"] if main["fintokei"]["mean_bp"] is not None else np.nan, np.array(null, float)) if len(null) >= 2 else {"B": len(null)}
    Mx = pd.concat(ports, axis=1).fillna(0.0).to_numpy()
    pbo = pbo_cscv(Mx, S=8) if Mx.shape[1] >= 2 and Mx.shape[0] >= 16 else {"pbo": None}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "n_syms": len(dfs),
           "eval_start": str(eval_start.date()), "seal": str(M.SEAL.date()), "k": K, "train_years": TRAIN_YEARS, "embargo_days": EMBARGO,
           "main_name": main_name, "main": M.strip_ports(main), "baseline_s07": M.strip_ports(s07), "baseline_zero": M.strip_ports(zero),
           "ic_main": ic, "auc_main": fmt(auc_all), "null": ns, "pbo": pbo, **log.to_json(), "trials_detail": trials,
           "multiple_comparisons": f"判定は main 1 本（規程モード・前後半）。格子 {len(log.rows)} 試行は TrialLog と PBO で数える", "elapsed_s": M.elapsed_since(t0)}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    return res


def judge(res):
    f = res["main"]["fintokei"]; b = res["baseline_s07"]["fintokei"]; z = res["null"].get("z"); p = res["null"].get("p_perm"); pbo = res["pbo"].get("pbo")
    need = [f["mean_bp_pre"], f["mean_bp_post"], b["mean_bp_pre"], b["mean_bp_post"], f["t_pre"], f["t_post"], f["max_dd"]]
    if any(v is None for v in need):
        return "未確定: 計算できない（評価期間の不足か帰無の退化）"
    beats = f["mean_bp_pre"] > max(b["mean_bp_pre"], 0) and f["mean_bp_post"] > max(b["mean_bp_post"], 0)
    if not beats:
        return "棄却: main が前後半のどちらかで S07 本体（またはゼロ）をコスト後に上回らない"
    if z is not None and z < 1:
        return "棄却: ラベル並べ替え帰無の z<1"
    if f["t_pre"] >= 2 and f["t_post"] >= 2 and f["max_dd"] >= -0.06 and (p is not None and p < 0.05) and (pbo is not None and pbo < 0.5):
        return "支持: 前後半とも S07 本体を上回り t≥2・max_dd≥−6%・perm_p<0.05・PBO<0.5"
    return "未確定"


if __name__ == "__main__":
    script = os.path.basename(__file__)
    if "--readme" in sys.argv:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）")); print("wrote README.md"); sys.exit(0)
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
