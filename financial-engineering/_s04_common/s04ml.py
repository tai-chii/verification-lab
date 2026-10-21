# -*- coding: utf-8 -*-
"""S04（ML 層）の検証スクリプト共通部（2026-10-22・/lab-plan ターミナル版 N=10）。
fe_core/ml.py・risk.py を組み合わせた「読み込み → 特徴量 → 封印 → ウォークフォワード → 予測→規模 → 規程モード損益 → 統計」の流れ。
fe_core は書き換えない。ここは S04 の各スクリプト（Q374〜Q383）だけが使う薄い層で、判定（judge）は各スクリプトが持つ。

決まり:
- 封印: panel を作った直後に time < SEAL（2024-07-01）で切る。封印期間の行は標準化にも使わない（ridge_fit_predict は学習窓の中で標準化する）。
- 評価は walk_forward の評価窓（年次・学習窓固定長・embargo ≥ k）だけ。学習しか無い年は建玉 0（評価期間に入れない）。
- 予測 → 規模の変換は 3 通り（sign／clip／kelly）。天井は RULES_FINTOKEI の定数のまま。
- ベースライン: 同じ評価期間・同じコスト・同じ規程モードの S07 等リスク TSMOM60 と「持たない（0）」。
"""
import os
import sys
import time as _time

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
from fe_core import (  # noqa: E402
    GROUPS, SPLIT_YEAR, COST_RT, CRYPTO_COST_RT_REL, load_d1, syms_available, health, cost_bp_oneway, tsmom_pos,
    make_features, make_target, meta_label, panel, walk_forward, ridge_fit_predict, gbm_fit_predict, pbo_cscv, TrialLog,
    size_weights, simulate_portfolio, yearly_t, RULES_FINTOKEI, RULES_NONE, spearman, nw_t, tstat, sharpe_ann, fmt,
    perm_within, null_summary, write_result,
)

SEAL = pd.Timestamp("2024-07-01")
WIDE48 = list(GROUPS["wide48"])
FAMILY_PREFIX = {"mom": ("mom_", "momz_"), "vol": ("vol_",), "range": ("range_",), "dow": ("dow_",)}


# ----------------------------------------------------------------------------- 読み込み
def data_guard(qid, here, syms=WIDE48, n_required=40):
    """S07 データガード（2026-10-21）: ok<n_required なら status=データ待ち を書いて exit 2。"""
    ok, missing = syms_available(syms, kind="D1_fromH1")
    if len(ok) < n_required:
        res = {"status": "データ待ち", "qid": qid, "n_ok": len(ok), "n_required": n_required, "n_total": len(syms),
               "ok": ok, "missing": missing, "note": "S07 データガード: ok<40 のため本番を実行しない。release で待ちに戻す。"}
        write_result(qid, res, smoke=False, here=here)
        print(f"データ待ち: ok={len(ok)}/{len(syms)} missing={len(missing)}")
        sys.exit(2)


def load_all(syms, smoke, rng, start="2008-01-01", smoke_n_syms=3):
    """銘柄ごとの日足。--smoke なら合成データ・銘柄 smoke_n_syms 本に落とす。返り値 (dfs, missing, data_health)。"""
    if smoke:
        syms = list(syms)[:smoke_n_syms]
    ok, missing = syms_available(syms, kind="D1_fromH1", smoke=smoke)
    dh = None if smoke else health(ok, kind="D1_fromH1")
    dfs = {}
    for s in ok:
        df = load_d1(s, smoke, rng)
        df = df[df["time"] >= pd.Timestamp(start)].reset_index(drop=True)
        if len(df) > 300:
            dfs[s] = df
    return dfs, missing, dh


# wide48 のうち COST_RT（段階1・価格単位）に無い 34 銘柄の往復コスト（価格に対する比）。2026-10-22 /lab-plan で判明:
# fe_core の既定はこれらを CRYPTO_COST_RT_REL（往復 30bp）に落とすので、為替クロスや株価指数に暗号資産並みのコストが掛かっていた
# （Q367〜Q371 の S07 はこの既定で走っている。粗利 +0.52bp → 純 −0.70bp の差の多くがこれ）。
# 値は「知識から記載（Dukascopy の典型スプレッド×2 の概数・保守側）・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合」。
WIDE48_COST_REL = {
    **{s: 3e-4 for s in ("NZDUSD", "EURGBP", "EURAUD", "EURCAD", "EURCHF", "GBPAUD", "GBPCAD", "GBPCHF", "AUDNZD", "AUDCAD")},   # 為替クロス 往復 3bp
    **{s: 3e-4 for s in ("AUDJPY", "CADJPY", "CHFJPY", "NZDJPY")},                                                              # 円クロス 往復 3bp
    **{s: 4e-4 for s in ("US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "EUSTX50", "AUS200", "HKG33", "SUI20", "NLD25")},  # 株価指数 往復 4bp（US500 の 1pt≒3.3bp と同水準）
    "BRENT": 10e-4, "COPPER": 15e-4, "NATGAS": 20e-4, "XPDUSD": 30e-4, "XPTUSD": 20e-4,                                          # 商品
    "BUND": 2e-4, "USTBOND": 3e-4, "UKGILT": 4e-4,                                                                                # 債券
    "ETHUSD": CRYPTO_COST_RT_REL,                                                                                                 # 暗号 往復 30bp
}


def cost_oneway_frac(sym, close):
    """片道コスト（比）。COST_RT（段階1・価格単位）→ WIDE48_COST_REL（比）→ CRYPTO_COST_RT_REL の順に探す。"""
    rel = None if sym in COST_RT else WIDE48_COST_REL.get(sym, CRYPTO_COST_RT_REL)
    return cost_bp_oneway(sym, close, rel=rel) / 1e4


def wide_tables(dfs):
    """date×sym の終値・日次リターン・片道コスト（比）。"""
    C = pd.DataFrame({s: pd.Series(df["close"].values, index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()
    R = C.pct_change(fill_method=None)
    COST = pd.DataFrame({s: pd.Series(cost_oneway_frac(s, df["close"].values), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index().ffill().fillna(0.0)
    return C, R, COST


# ----------------------------------------------------------------------------- 特徴量・目的変数
def select_cols(X, fset):
    """族の集合（"all" か "mom+vol" のような '+' 区切り）で列を選ぶ。"""
    if fset == "all":
        return list(X.columns)
    cols = []
    for fam in fset.split("+"):
        pre = FAMILY_PREFIX[fam]
        cols += [c for c in X.columns if c.startswith(pre)]
    return cols


def build_panel(dfs, target_fn, feat_kw=None, seal=SEAL):
    """銘柄ごとに (X, y) を作って縦に積み、封印で切る。target_fn(df) -> Series（index=time）。
    返り値 (X_all, y_all, meta[time, sym])。封印（time >= seal）の行はここで落とす。"""
    frames = {}
    for s, df in dfs.items():
        X = make_features(df, **(feat_kw or {}))
        y = target_fn(df)
        frames[s] = (X, y)
    X_all, y_all, meta = panel(frames)
    keep = (meta["time"] < seal).to_numpy()
    X_all = X_all.iloc[keep]; y_all = y_all.iloc[keep]; meta = meta.iloc[keep].reset_index(drop=True)
    return X_all, y_all, meta


# ----------------------------------------------------------------------------- モデル
def fit_predict(model, Xtr, ytr, Xte, classify=False):
    """model: ("ridge", alpha) | ("gbm", dict)。分類は gbm だけ（ridge は線形確率）。"""
    kind, arg = model
    if kind == "ridge":
        return ridge_fit_predict(Xtr, ytr, Xte, alpha=float(arg))
    if kind == "gbm":
        return gbm_fit_predict(Xtr, ytr, Xte, classify=classify, **(arg or {}))
    raise ValueError(f"model が不明: {kind}")


def wf_predict(X, y, meta, model, cols, train_years=4, embargo_days=10, expanding=False, classify=False, per_sym=False, label_perm_rng=None):
    """年次ウォークフォワードで評価窓の予測を集める。返り値 DataFrame(date×sym) の予測（評価窓以外は NaN）。
    label_perm_rng を渡すと学習窓のラベルを年内で並べ替える（ラベル並べ替え帰無）。per_sym=True なら銘柄別に学習。"""
    t = pd.to_datetime(meta["time"]).to_numpy()
    folds = walk_forward(t, train_years=train_years, test_years=1, embargo_days=embargo_days, end=SEAL)
    Xv = X[cols].to_numpy(float); yv = y.to_numpy(float); yrs = pd.DatetimeIndex(t).year.to_numpy()
    syms = meta["sym"].to_numpy()
    out = np.full(len(yv), np.nan)
    for tr, te, ty in folds:
        if expanding:
            tr = (t < (pd.Timestamp(f"{ty}-01-01") - pd.Timedelta(days=embargo_days)).to_datetime64()) & (t >= t.min())
        groups = [(tr & (syms == s), te & (syms == s)) for s in np.unique(syms[te])] if per_sym else [(tr, te)]
        for mtr, mte in groups:
            if mtr.sum() < (200 if per_sym else 500) or mte.sum() == 0:
                continue
            ytr = yv[mtr]
            if label_perm_rng is not None:
                ytr = perm_within(label_perm_rng, ytr, yrs[mtr])
            out[mte] = fit_predict(model, Xv[mtr], ytr, Xv[mte], classify)
    pred = pd.DataFrame({"time": meta["time"].to_numpy(), "sym": syms, "p": out}).pivot(index="time", columns="sym", values="p").sort_index()
    return pred


# ----------------------------------------------------------------------------- 予測 → 規模
def _rolling_score_sigma(pred, W=250):
    """予測スコアの直近 W 本の標準偏差（t までの情報。min 60）。"""
    return pred.rolling(W, min_periods=60).std().replace(0, np.nan)


def convert_direction(pred, rule, W=250):
    """方向予測（スコア＝予測リターン）→ 規模 [−1, 1]。
    sign: 符号のみ ±1。clip: score/σ_score を ±1 に切る。kelly: p̂=Φ(score/σ_score) として (p̂−0.5)×4×0.25 を ±1 に切る。"""
    import math
    z = pred / _rolling_score_sigma(pred, W)
    if rule == "sign":
        return np.sign(pred).fillna(0.0)
    if rule == "clip":
        return z.clip(-1, 1).fillna(0.0)
    if rule == "kelly":
        cdf = np.vectorize(lambda v: 0.5 * (1 + math.erf(v / math.sqrt(2))) if np.isfinite(v) else np.nan)
        p = pd.DataFrame(cdf(z.to_numpy(float)), index=z.index, columns=z.columns)
        return ((p - 0.5) * 4 * 0.25).clip(-1, 1).where(z.notna(), 0.0).fillna(0.0)
    raise ValueError(rule)


def convert_meta(pred_p, signal, rule, W=250):
    """メタラベル（p=乗って勝つ確率の予測）→ 乗る規模 [0, 1] × 合図（±1）。
    sign: p>0.5 で 1、以下 0。clip: (p−0.5)/σ_score を [0, 1] に切る。kelly: (p−0.5)×4×0.25 を [0, 1] に切る。
    負（合図の逆張り）はメタラベリングでは取らないので下限 0。"""
    s = pred_p - 0.5
    if rule == "sign":
        size = (s > 0).astype(float)
    elif rule == "clip":
        size = (s / _rolling_score_sigma(s, W)).clip(0, 1)
    elif rule == "kelly":
        size = (s * 4 * 0.25).clip(0, 1)
    else:
        raise ValueError(rule)
    size = size.where(pred_p.notna(), 0.0).fillna(0.0)
    return size * signal.reindex_like(size).fillna(0.0)


# ----------------------------------------------------------------------------- 規程モードの損益
def eval_portfolio(pos, R, COST, eval_start=None, sigma=None):
    """pos(date×sym・連続値可) → RULES_NONE と RULES_FINTOKEI の損益。eval_start 以前は建玉 0。
    返り値 {"none": {...}, "fintokei": {...}, "gate": {...}, "port_fintokei": Series, "port_none": Series}。"""
    pos = pos.reindex(index=R.index, columns=R.columns).fillna(0.0)
    if eval_start is not None:
        pos.loc[pos.index < pd.Timestamp(eval_start)] = 0.0
    out = {}
    for name, rules in (("none", RULES_NONE), ("fintokei", RULES_FINTOKEI)):
        W = size_weights(pos, R, rules, sigma=sigma if name == "fintokei" else None)
        sim = simulate_portfolio(W, R, COST, rules)
        port = sim["port"]
        if eval_start is not None:
            port = port[port.index >= pd.Timestamp(eval_start)]
        port = port[port.index < SEAL]
        t_all, yt = yearly_t(port); t_pre, _ = yearly_t(port[port.index.year < SPLIT_YEAR]); t_post, _ = yearly_t(port[port.index.year >= SPLIT_YEAR])
        pre = port[port.index.year < SPLIT_YEAR]; post = port[port.index.year >= SPLIT_YEAR]
        eq = (1 + port).cumprod(); dd = eq / eq.cummax() - 1
        out[name] = {"t_all": fmt(t_all), "t_pre": fmt(t_pre), "t_post": fmt(t_post),
                     "mean_bp": fmt(port.mean() * 1e4), "mean_bp_pre": fmt(pre.mean() * 1e4) if len(pre) else None, "mean_bp_post": fmt(post.mean() * 1e4) if len(post) else None,
                     "n_years_pre": int(pre.index.year.nunique()) if len(pre) else 0, "n_years_post": int(post.index.year.nunique()) if len(post) else 0,
                     "sigma_pct": fmt(port.std() * 100), "sharpe": fmt(sharpe_ann(port.to_numpy())),
                     "max_dd": fmt(float(dd.min()) if len(dd) else np.nan), "worst_day": fmt(float(port.min()) if len(port) else np.nan),
                     "stops": int(sim["stops"]), "gross_median": fmt(float(W.abs().sum(axis=1).median())), "n_days": int(len(port)),
                     "years": yt.to_dict(orient="records"), "rules": dict(rules)}
        out["port_" + name] = port
    f = out["fintokei"]
    ok = lambda v: v is not None and v == v
    out["gate"] = {"t_pre_ge2": bool(ok(f["t_pre"]) and f["t_pre"] >= 2), "t_post_ge2": bool(ok(f["t_post"]) and f["t_post"] >= 2),
                   "max_dd_within_6pct": bool(ok(f["max_dd"]) and f["max_dd"] >= -0.06)}
    out["gate"]["pass"] = all(out["gate"].values())
    return out


def strip_ports(d):
    """JSON に入れる前に Series を落とす。"""
    return {k: v for k, v in d.items() if not k.startswith("port_")}


def baseline_tsmom(dfs, R, COST, eval_start, L=60):
    """S07 本体（等リスク TSMOM L）と「持たない」の同じ評価期間の損益。"""
    pos = pd.DataFrame({s: pd.Series(tsmom_pos(df["close"].values, L), index=pd.to_datetime(df["time"])) for s, df in dfs.items()}).sort_index()
    s07 = eval_portfolio(pos, R, COST, eval_start)
    zero = eval_portfolio(pos * 0.0, R, COST, eval_start)
    return pos, s07, zero


# ----------------------------------------------------------------------------- 統計
def ic_by_year(pred, target_wide):
    """年ごとの IC（日ごとの横断スピアマンの平均ではなく、年内の全 (日, 銘柄) の順位相関）と、日次 IC の nw_t。"""
    p = pred.stack(); y = target_wide.stack()
    df = pd.concat([p.rename("p"), y.rename("y")], axis=1).dropna()
    if df.empty:
        return {"ic_all": None, "ic_years": {}, "t_year": None, "ic_daily_mean": None, "ic_daily_nw_t": None}
    yrs = df.index.get_level_values(0).year
    ic_y = {int(k): fmt(spearman(g["p"].to_numpy(), g["y"].to_numpy())) for k, g in df.groupby(yrs)}
    vals = np.array([v for v in ic_y.values() if v is not None], float)
    daily = df.groupby(level=0).apply(lambda g: spearman(g["p"].to_numpy(), g["y"].to_numpy()) if len(g) >= 5 else np.nan).dropna()
    return {"ic_all": fmt(spearman(df["p"].to_numpy(), df["y"].to_numpy())), "ic_years": ic_y, "t_year": fmt(tstat(vals)) if len(vals) > 1 else None,
            "ic_daily_mean": fmt(daily.mean()) if len(daily) else None, "ic_daily_nw_t": fmt(nw_t(daily.to_numpy(), lag=5)) if len(daily) > 10 else None}


def auc(p, y):
    """ROC-AUC（順位で計算。同点は 0.5）。"""
    p = np.asarray(p, float); y = np.asarray(y, float); ok = np.isfinite(p) & np.isfinite(y); p, y = p[ok], y[ok]
    n1 = (y == 1).sum(); n0 = (y == 0).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(p).rank().to_numpy()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def target_wide(dfs, target_fn):
    return pd.DataFrame({s: target_fn(df) for s, df in dfs.items()}).sort_index()


def eval_start_of(meta, train_years):
    """評価が始まる年の 1 月 1 日（walk_forward の最初の評価年）。"""
    t = pd.to_datetime(meta["time"]); y0 = t.min().year + train_years
    return pd.Timestamp(f"{y0}-01-01")


def elapsed_since(t0):
    return round(_time.time() - t0, 1)


# ----------------------------------------------------------------------------- 方向予測の格子（S04c 系・Q378〜Q381・Q383 が共用）
def trial_name(g):
    m = g["model"]; mname = f"{m[0]}:{m[1]}" if m[0] == "ridge" else f"{m[0]}:d{m[1].get('max_depth', 3)}i{m[1].get('max_iter', 200)}"
    return "|".join([g.get("fset", "all"), mname, g.get("rule", "clip"), f"k{g.get('k', 5)}", f"tr{g.get('train_years', 4)}{'x' if g.get('expanding') else ''}",
                     "persym" if g.get("per_sym") else "pool", "clf" if g.get("classify") else "reg"])


def direction_experiment(dfs, R, COST, grid, main_idx, args, rng, max_trials=50, null_B=None):
    """格子の各点で「翌 k 日リターン（または符号）の予測 → 規模 → 規程モード損益」を回し、main のラベル並べ替え帰無・PBO・ベースラインをまとめて返す。
    grid: dict の list（fset, model, rule, k, train_years, expanding, per_sym, classify, embargo）。main_idx: 判定に使う添字。
    返り値: 結果 dict（JSON 可・Series なし）。"""
    log = TrialLog(max_trials=max_trials); trials = {}; ports = []; cache = {}; panels = {}
    def get_panel(k, classify):
        key = (k, classify)
        if key not in panels:
            tf = (lambda df, k=k: (make_target(df, k, "sign") > 0).astype(float).where(make_target(df, k, "ret").notna())) if classify else (lambda df, k=k: make_target(df, k, "ret"))
            panels[key] = build_panel(dfs, tf) + (target_wide(dfs, lambda df, k=k: make_target(df, k, "ret")),)
        return panels[key]
    eval_start = None
    for i, g in enumerate(grid):
        k = g.get("k", 5); ty = g.get("train_years", 4); emb = g.get("embargo", max(10, k)); clf = bool(g.get("classify"))
        X, y, meta, Yret = get_panel(k, clf)
        es = eval_start_of(meta, ty); eval_start = es if eval_start is None else min(eval_start, es)
        ckey = (g.get("fset", "all"), str(g["model"]), k, ty, bool(g.get("expanding")), bool(g.get("per_sym")), clf)
        if ckey not in cache:
            cache[ckey] = wf_predict(X, y, meta, g["model"], select_cols(X, g.get("fset", "all")), ty, emb, expanding=bool(g.get("expanding")), classify=clf, per_sym=bool(g.get("per_sym")))
        pred = cache[ckey]
        score = (pred - 0.5) if clf else pred           # 分類は p−0.5 をスコアに
        pos = convert_direction(score, g.get("rule", "clip"))
        ev = eval_portfolio(pos, R, COST, es)
        name = trial_name(g)
        log.add({k2: (str(v) if k2 == "model" else v) for k2, v in g.items()}, ev["fintokei"]["mean_bp"] or 0.0)
        ic = ic_by_year(pred, Yret)
        trials[name] = {"eval_start": str(es.date()), "ic": ic, "fintokei": {kk: v for kk, v in ev["fintokei"].items() if kk not in ("years", "rules")},
                        "none_mean_bp": ev["none"]["mean_bp"], "none_t_all": ev["none"]["t_all"], "gate": ev["gate"]}
        if clf:
            st = pd.concat([pred.stack().rename("p"), (Yret > 0).astype(float).where(Yret.notna()).stack().rename("y")], axis=1).dropna()
            trials[name]["auc"] = fmt(auc(st["p"], st["y"])) if len(st) else None
        ports.append(ev["port_fintokei"].rename(name))
        if i == main_idx:
            main = {"name": name, "eval": ev, "X": X, "y": y, "meta": meta, "g": g, "es": es}
    g = main["g"]; k = g.get("k", 5); ty = g.get("train_years", 4); emb = g.get("embargo", max(10, k)); clf = bool(g.get("classify"))
    _, s07, zero = baseline_tsmom(dfs, R, COST, main["es"], L=60)
    null = []
    for b in range(args.B if null_B is None else null_B):
        pn = wf_predict(main["X"], main["y"], main["meta"], g["model"], select_cols(main["X"], g.get("fset", "all")), ty, emb, expanding=bool(g.get("expanding")), classify=clf, per_sym=bool(g.get("per_sym")), label_perm_rng=rng)
        evn = eval_portfolio(convert_direction((pn - 0.5) if clf else pn, g.get("rule", "clip")), R, COST, main["es"])
        null.append(evn["fintokei"]["mean_bp"] if evn["fintokei"]["mean_bp"] is not None else np.nan)
    obs = main["eval"]["fintokei"]["mean_bp"]
    ns = null_summary(obs if obs is not None else np.nan, np.array(null, float)) if len(null) >= 2 else {"B": len(null)}
    Mx = pd.concat(ports, axis=1).fillna(0.0).to_numpy()
    pbo = pbo_cscv(Mx, S=8) if Mx.shape[1] >= 2 and Mx.shape[0] >= 16 else {"pbo": None, "N": int(Mx.shape[1])}
    return {"eval_start": str(main["es"].date()), "seal": str(SEAL.date()), "main_name": main["name"], "main": strip_ports(main["eval"]), "main_ic": trials[main["name"]]["ic"],
            "baseline_s07": strip_ports(s07), "baseline_zero": strip_ports(zero), "null": ns, "pbo": pbo, **log.to_json(), "trials_detail": trials}


def judge_vs_s07(res):
    """S04c 系の既定の 3 分岐（Q374 と同じ文）。"""
    f = res["main"]["fintokei"]; b = res["baseline_s07"]["fintokei"]; z = res["null"].get("z"); p = res["null"].get("p_perm"); pbo = res["pbo"].get("pbo")
    need = [f["mean_bp_pre"], f["mean_bp_post"], b["mean_bp_pre"], b["mean_bp_post"], f["t_pre"], f["t_post"], f["max_dd"]]
    if any(v is None for v in need):
        return "未確定: 計算できない（評価期間の不足か帰無の退化）"
    if not (f["mean_bp_pre"] > max(b["mean_bp_pre"], 0) and f["mean_bp_post"] > max(b["mean_bp_post"], 0)):
        return "棄却: main が前後半のどちらかで S07 本体（またはゼロ）をコスト後に上回らない"
    if z is not None and z < 1:
        return "棄却: ラベル並べ替え帰無の z<1"
    if f["t_pre"] >= 2 and f["t_post"] >= 2 and f["max_dd"] >= -0.06 and (p is not None and p < 0.05) and (pbo is not None and pbo < 0.5):
        return "支持: 前後半とも S07 本体を上回り t≥2・max_dd≥−6%・perm_p<0.05・PBO<0.5"
    return "未確定"


def ml_main(SPEC, HERE, run, script_kind="土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）"):
    """S04 スクリプト共通の main（--readme／--idea-row／データガード／smoke の B 制限／保存）。"""
    from fe_core import parse_args, render_readme, render_idea_row, sanitize
    script = os.path.basename(sys.argv[0])
    if "--readme" in sys.argv:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind=script_kind)); print("wrote README.md"); return
    if "--idea-row" in sys.argv:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE))); return
    args = parse_args(default_B=SPEC.B)
    if not args.smoke:
        data_guard(SPEC.qid, HERE)
    else:
        args.B = min(args.B, 2)
    rng = np.random.default_rng(args.seed)
    res = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    print("machine_verdict:", res["machine_verdict"])
    print(write_result(SPEC.qid, sanitize(res), args.smoke, here=HERE))
