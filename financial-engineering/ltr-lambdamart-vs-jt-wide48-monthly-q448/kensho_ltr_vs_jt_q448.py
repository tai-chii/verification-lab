#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q448: ランキング学習（LambdaMART）の並べ替えは、単純な過去リターン並べ（JT）に対してコスト後も上乗せが残るか。
wide48 D1 → 月末に集約・上下 10 銘柄の等ウェイト L−S・月次リバランス。イベント型（土台の関数を直接使う）。

== 事前登録（測る前に固定・2026-10-22 Opus。アイデア候補 Q447-C1 の行をそのまま写す） ==
問い: 同じ入力・同じ上下 k=10 で、LambdaMART の月次 L−S は JT（12 か月リターン順）より総 bp/月が大きく、
      その差は片道 5bp 控除後も残るか。回転率（LTR/JT）と損益分岐コストはどうか。
仮説: LTR は順位精度の上乗せで総 bp を上げるが、入れ替えが多く、片道 5bp 控除後に差が縮む（Poh+2020 のコストの穴）。
データ: wide48（FX22・IDX13・CMD8・BOND3・CRYPTO2）D1。月末の終値（月の最後の足が月末 7 日以内のもの）。
        月末は 2026-06 まで（EURUSD など DATA_DIR の正本が 2026-06-30 で終わるため、全銘柄で同じ終点にする）。
        1 か月の銘柄数が 30 未満の月は取引しない（両戦略とも同じ月だけ）。
入力（Poh と同じ型・7 本）: h=1,3,6,12 か月リターン ÷（日次 log リターンの 63 日標準偏差×√(21h)）、
        MACD 3 本（(S,L)=(8,24),(16,48),(32,96) の EWM 差 ÷ 63 日価格標準偏差、さらに ÷ その 252 日標準偏差）。
並べ方: JT＝12 か月の生リターン順。LTR＝LightGBM lambdarank（ラベル＝翌月リターンの月内十分位 0..9、群＝月）。
        拡張窓で年 1 回再学習（Y 年の検証には、翌月リターンが Y−1 年末までに確定した月だけで学習）。
        最初の検証年は学習月が 36 以上になる年。ハイパラは下の LGB_PARAMS の 1 組で固定。
損益: 上位 10 を +0.1、下位 10 を −0.1（総建玉 2）。L−S 総 bp/月 ＝ 上位平均 − 下位平均（翌月の単純リターン）。
      回転 ＝ Σ|w_t − w_{t−1}|（ドリフトは無視・最初の月は w_{t−1}=0）。コスト ＝ 回転 × 片道 c。損益分岐 c* ＝ 総 bp 平均 ÷ 回転平均。
統計: 月次差 d＝LTR−JT（総・控除後）を年ごとに平均 → 年単位 t（全期間・前半＜2017・後半≥2017）。
帰無（記述）: LTR のスコアを月内で並べ替え B=500 → LTR 総 bp/月の帰無分布 → z（LTR に順位の腕があるか）。
判定（事前固定・3 分岐）:
  支持＝総 bp 差の全期間 t≥2 かつ前後半とも正、かつ片道 5bp 控除後の差も全期間 t≥2。
  棄却＝総 bp 差の全期間 t<1（コスト前で既に差なし）または控除後の差の全期間平均が負。
  ほか → 未確定。
多重比較: 判定に使う検定は 2 本（総差・控除後差）で、支持は両方の AND（交わり―合併検定のため補正不要）。n_tests=2 と記録。
捨てた案の数: 0（k=10・ハイパラ・入力・c=5bp は 1 組で固定。k・c の掃引は記述のみ: c=2,10bp の損益分岐は c* で読める）。
LLM の知識の締め切り: 2026-06（Opus 5.5）。データの終点も 2026-06 で、標本外の期間は無い。
委託の確かめ方: 委託なし（Opus 設計・Opus 実行）。月次の L−S を手計算で 1 か月照合する（--check）。
先行研究: 接続ログ 2026-10-22 Q447-C1。Poh+ arXiv:2105.10019 §5.6 は "All returns are computed in the absence of
  transaction costs"（2026-10-22 WebFetch で原文確認・通貨 31 種のみで暗号資産は無い）。二次要約の「暗号資産でコスト後も上回る」は誤り。
注意: wide48 は株ではなく多資産（Poh+2020 は米株）。48 銘柄は学習データが薄い。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (GROUPS, load_d1, exists_sym, health, write_result, tstat,  # noqa: E402
                     null_summary, parse_args, spearman)

QID = "Q448"
WIDE48 = GROUPS["wide48"]
K = 10
COST_BP = 5.0
MIN_SYMS = 30
MIN_TRAIN_MONTHS = 36
END = pd.Timestamp("2026-06-30")
SPLIT_YEAR = 2017
FEATS = ["r1n", "r3n", "r6n", "r12n", "macd8", "macd16", "macd32"]
LGB_PARAMS = dict(objective="lambdarank", n_estimators=300, learning_rate=0.05, num_leaves=15,
                  min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                  random_state=20261022, deterministic=True, force_row_wise=True, n_jobs=1, verbose=-1)


def build_panel(smoke=False, rng=None):
    """月末ごとの特徴・JT 指標・翌月リターンの縦長表と、読めた銘柄一覧。"""
    rows, used = [], []
    for s in WIDE48:
        if not smoke and not exists_sym(s, "D1_fromH1"):
            continue
        d = load_d1(s, smoke=smoke, rng=rng)
        d = d[d["time"] <= END].set_index("time")
        c = d["close"].astype(float)
        lr = np.log(c).diff()
        sig = lr.rolling(63, min_periods=50).std()
        macd = {}
        for S, L in ((8, 24), (16, 48), (32, 96)):
            q = (c.ewm(halflife=np.log(0.5) / np.log(1 - 1 / S)).mean()
                 - c.ewm(halflife=np.log(0.5) / np.log(1 - 1 / L)).mean()) / c.rolling(63, min_periods=50).std()
            macd[S] = q / q.rolling(252, min_periods=200).std()
        day = pd.DataFrame({"close": c, "sig": sig, "t": d.index, **{f"macd{S}": v for S, v in macd.items()}})
        m = day.resample("ME").last()
        m = m[(m.index - pd.to_datetime(m["t"])).dt.days <= 7]  # 月末 7 日以内に足がある月だけ
        m = m.reindex(pd.date_range(m.index.min(), m.index.max(), freq="ME"))
        for h in (1, 3, 6, 12):
            m[f"r{h}"] = m["close"] / m["close"].shift(h) - 1
            m[f"r{h}n"] = m[f"r{h}"] / (m["sig"] * np.sqrt(21 * h))
        m["fwd"] = m["close"].shift(-1) / m["close"] - 1
        m["sym"] = s
        rows.append(m)
        used.append(s)
    P = pd.concat(rows).rename_axis("month").reset_index()
    P = P.dropna(subset=FEATS + ["r12", "fwd"])
    n = P.groupby("month")["sym"].transform("size")
    P = P[n >= MIN_SYMS].sort_values(["month", "sym"]).reset_index(drop=True)
    P["label"] = P.groupby("month")["fwd"].transform(
        lambda x: np.minimum(9, np.floor(x.rank(method="first").sub(1) / len(x) * 10))).astype(int)
    return P, used


def ltr_scores(P):
    """年 1 回の拡張窓学習で検証月の LTR スコアを付ける。"""
    import lightgbm as lgb
    months = np.sort(P["month"].unique())
    years = sorted(pd.DatetimeIndex(months).year.unique())
    P = P.copy()
    P["score"] = np.nan
    P["fold_year"] = np.nan
    for Y in years:
        cutoff = pd.Timestamp(f"{Y - 1}-12-31")
        tr = P[(P["month"] + pd.offsets.MonthEnd(1)) <= cutoff]  # 翌月リターンが Y−1 年末までに確定
        te_mask = P["month"].dt.year == Y
        if tr["month"].nunique() < MIN_TRAIN_MONTHS or not te_mask.any():
            continue
        g = tr.groupby("month", sort=True).size().values
        mdl = lgb.LGBMRanker(**LGB_PARAMS)
        mdl.fit(tr[FEATS].values, tr["label"].values, group=g)
        P.loc[te_mask, "score"] = mdl.predict(P.loc[te_mask, FEATS].values)
        P.loc[te_mask, "fold_year"] = Y
    return P[P["score"].notna()].reset_index(drop=True)


def ls_month(T, col, k=K):
    """月ごとの L−S 総 bp と重み（sym→w）。"""
    out = {}
    for m, g in T.groupby("month", sort=True):
        g = g.sort_values([col, "sym"])
        lo, hi = g.iloc[:k], g.iloc[-k:]
        w = {s: 1.0 / k for s in hi["sym"]}
        w.update({s: -1.0 / k for s in lo["sym"]})
        out[m] = ((hi["fwd"].mean() - lo["fwd"].mean()) * 1e4, w)
    return out


def series(T, col):
    res = ls_month(T, col)
    prev, recs = {}, []
    for m, (bp, w) in res.items():
        keys = set(w) | set(prev)
        to = sum(abs(w.get(s, 0.0) - prev.get(s, 0.0)) for s in keys)
        recs.append({"month": m, "gross": bp, "turnover": to, "net": bp - to * COST_BP})
        prev = w
    return pd.DataFrame(recs).set_index("month")


def yearly_t(x):
    y = x.groupby(x.index.year).mean()
    pre, post = y[y.index < SPLIT_YEAR], y[y.index >= SPLIT_YEAR]
    return {"all": {"mean": float(y.mean()), "t": tstat(y.values), "n_years": int(len(y))},
            "pre": {"mean": float(pre.mean()) if len(pre) else None, "t": tstat(pre.values), "n_years": int(len(pre))},
            "post": {"mean": float(post.mean()) if len(post) else None, "t": tstat(post.values), "n_years": int(len(post))}}


def judge(g, n):
    ga, gp, gq, na = g["all"], g["pre"], g["post"], n["all"]
    if (np.isfinite(ga["t"]) and ga["t"] >= 2 and (gp["mean"] or 0) > 0 and (gq["mean"] or 0) > 0
            and np.isfinite(na["t"]) and na["t"] >= 2):
        return "支持"
    if (not np.isfinite(ga["t"])) or ga["t"] < 1 or na["mean"] < 0:
        return "棄却"
    return "未確定"


def run(args, rng):
    P, used = build_panel(args.smoke, rng)
    T = ltr_scores(P)
    jt, lt = series(T, "r12"), series(T, "score")
    d_g, d_n = lt["gross"] - jt["gross"], lt["net"] - jt["net"]
    g, n = yearly_t(d_g), yearly_t(d_n)
    # 帰無: LTR スコアを月内で並べ替え
    null = []
    grp = T.groupby("month").indices
    for _ in range(args.B):
        sc = T["score"].values.copy()
        for idx in grp.values():
            sc[idx] = sc[rng.permutation(idx)]
        Tb = T.assign(score_b=sc)
        null.append(np.mean([v[0] for v in ls_month(Tb, "score_b").values()]))
    ic = {c: float(np.nanmean([spearman(gg[c].values, gg["fwd"].values) for _, gg in T.groupby("month")]))
          for c in ("r12", "score")}
    ys = T.assign(year=T["month"].dt.year).groupby(["year", "sym"]).size().rename("n_months").reset_index()
    mo = pd.concat({"jt": jt, "ltr": lt}, axis=1)
    mo.columns = [f"{a}_{b}" for a, b in mo.columns]
    stat = {}
    for name, s in (("jt", jt), ("ltr", lt)):
        stat[name] = {"gross_bp_m": float(s["gross"].mean()), "net_bp_m": float(s["net"].mean()),
                      "turnover_m": float(s["turnover"].mean()),
                      "breakeven_bp_oneway": float(s["gross"].mean() / s["turnover"].mean()),
                      "gross_yearly": yearly_t(s["gross"]), "net_yearly": yearly_t(s["net"]),
                      "sharpe_ann_gross": float(s["gross"].mean() / s["gross"].std(ddof=1) * np.sqrt(12))}
    res = {
        "status": "完了",
        "question": "LambdaMART の月次 L−S（上下10）は JT に対しコスト後も上乗せが残るか（wide48）",
        "settings": {"K": K, "cost_bp_oneway": COST_BP, "min_syms": MIN_SYMS, "min_train_months": MIN_TRAIN_MONTHS,
                     "end": str(END.date()), "split_year": SPLIT_YEAR, "feats": FEATS, "lgb": LGB_PARAMS, "B": args.B,
                     "seed": args.seed},
        "data_health": health(WIDE48, kind="D1_fromH1"),
        "n_syms_used": len(used), "n_syms_in_test": int(T["sym"].nunique()),
        "test_months": [str(T["month"].min().date()), str(T["month"].max().date())], "n_test_months": int(len(jt)),
        "syms_per_month": {"min": int(T.groupby("month").size().min()), "max": int(T.groupby("month").size().max())},
        "years_dropped": [],
        "stat": stat,
        "turnover_ratio_ltr_over_jt": float(lt["turnover"].mean() / jt["turnover"].mean()),
        "diff_gross_yearly": g, "diff_net_yearly": n,
        "ic_spearman_mean": ic,
        "null_ltr_gross": null_summary(float(lt["gross"].mean()), null),
        "multiple_comparisons": "判定は総差・控除後差の 2 本の AND（交わり―合併・補正不要）",
        "n_tests": 2,
        "machine_verdict": judge(g, n),
    }
    res["null_degenerate"] = res["null_ltr_gross"]["degenerate"]
    return res, {"monthly": mo.reset_index(), "year_sym": ys}


def check(T_month=None):
    """1 か月の L−S を手計算で照合する。"""
    rng = np.random.default_rng(1)
    P, _ = build_panel(False, rng)
    m = P["month"].iloc[len(P) // 2]
    g = P[P["month"] == m].sort_values("r12")
    hand = (g["fwd"].iloc[-K:].mean() - g["fwd"].iloc[:K].mean()) * 1e4
    auto = ls_month(P[P["month"] == m], "r12")[m][0]
    print("check", m.date(), round(hand, 6), round(auto, 6), "一致" if abs(hand - auto) < 1e-9 else "不一致")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check(); sys.exit(0)
    args = parse_args(default_B=500)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    p = write_result(QID, res, smoke=args.smoke, extra_csv=csvs, here=HERE)
    print(p)
    print({k: res[k] for k in ("machine_verdict", "turnover_ratio_ltr_over_jt", "n_test_months", "test_months")})
    print("diff_gross", res["diff_gross_yearly"]); print("diff_net", res["diff_net_yearly"])
    for k in ("jt", "ltr"):
        s = res["stat"][k]; print(k, {a: s[a] for a in ("gross_bp_m", "net_bp_m", "turnover_m", "breakeven_bp_oneway", "sharpe_ann_gross")})
    print("ic", res["ic_spearman_mean"], "null", res["null_ltr_gross"])
