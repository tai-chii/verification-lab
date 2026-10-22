#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q449（アイデア候補 Q444-C1）: wide48 D1 の高ボラ局面の方向的中率の上乗せは、局面ごとの基準率と
MRS 平滑化ラベルの先読みで説明されるか（Jain 2026 の 56〜59% を分解）。イベント型（分類の的中率）なので土台を直接使う。

== 事前登録（2026-10-22 21:20・Opus・測る前に固定。アイデア候補 Q444-C1 の行をそのまま写す） ==
問い: Jain 2026 は MRS の高ボラ局面で方向的中率 56〜59%（低ボラ 50〜53%）。手元の 48 銘柄 D1 で、同じ単純な分類器の
      高ボラ局面の的中率の上乗せは (i) 局面内の基準率 max(p,1−p) と (ii) 局面ラベルの先読み（全期間の平滑化確率）で説明されるか。
データ: wide48 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）、2008-01-01〜2024-06-30（2024-07-01 以降は封印なので読まない）。
分類器（1 つに固定）: ロジスティック回帰（sklearn・C=1・L2・学習期間の平均と標準偏差で標準化）。入力は Jain の型の 6 個
      SMA10 乖離・EMA10 乖離・RSI14・MACD(12,26,9) ヒストグラム/終値・BB(20,2) %b・W%R14（どれも t までの値）。
      ラベル＝翌日 r_{t+1}>0（r=0 の日と翌日が gap の日は除く）。銘柄ごとに拡張窓で年 1 回再学習（学習 ≥500 行の年から予測）。予測＝確率>0.5。
局面（予測の起点の日 t に付ける。3 通り）:
  S＝銘柄ごとに評価期間全体で推定した 2 局面 MRS（statsmodels MarkovRegression、定数＋分散の切替、入力は 100×r）の平滑化確率（高分散の局面）>0.5
  F＝同じモデルを年 Y の前日までの行で推定し、その母数でフィルタした確率（t までの情報）>0.5。年 1 回再推定
  V＝過去 σ20（r_{t−19..t} の標準偏差）が銘柄内の拡張窓 70% 分位以上（上位 30%）。分位の履歴は 250 本以上
  3 定義とも値がある行（共通標本）だけで比べる。
測るもの: 定義×局面ごとに 的中率・局面内の上昇日比率 p・基準率 max(p,1−p)・超過＝的中率−基準率。
      基準率は (定義, 局面, 銘柄) ごとに評価期間全体の p から作る（Jain は 1 銘柄・局面全体の基準率。銘柄×年に切ると小標本で
      max(p,1−p) が上に偏るので避けた）。年の値＝銘柄をまたいだ行数加重の平均。年単位 t（全期間・前半 <2017・後半 2017〜）。
      分解: 高−低の的中率差 = 超過の差 + 基準率の差、比 = 基準率の差 / 的中率差。
帰無: 局面ラベルを銘柄内で循環シフト（共通標本の並びで、シフト量 ∈ [60, n−60]）B=500。高ボラ超過（全期間・行数加重）と
      高−低の的中率差の帰無分布 → z・perm_p。n_tests=2（判定に使う V・F の高ボラ超過）で Holm。
判定（事前固定・3 分岐）:
  支持（Jain の主張が手元で残る）＝V と F の両方で高ボラの超過が全期間の年単位 t≥2 かつ前半・後半の平均とも正
  棄却（基準率・先読みで説明）＝V と F の両方で高ボラの超過の全期間の年単位 t<1
  ほか → 未確定。分類器・入力・30% の閾値を結果を見て変えない。
予想（事前）: S では高ボラの的中率差が出るが F・V では消え、超過は 3 定義とも 0 と区別できない（Q147・Q307 から棄却寄り）。
事前登録の補足（測る前）: 基準率 max(p̂,1−p̂) は p̂ の標本誤差で上に偏る（局面の行が少ないほど大きい）。これで超過が負に寄って
      「t<1＝棄却」が機械的に出る恐れがあるので、帰無の平均を引いた超過（null-centered）も記述として出す。判定は上の規則のまま。
      生の判定と null-centered の向きが割れたら README の解釈に書く。
捨てた案: 1（Q444-C2 局面で有意な指標が入れ替わるか＝多重比較の型で棄却）。分類器・閾値・入力の掃引はしない。
LLM の知識の締め切り: 2026-06（Opus 5.5）。データは封印前 <2024-07-01 だけ。結果は知識に含まれ得ないが、Jain 2026 の数値は読んだ。
委託の確かめ方: なし（Opus が設計・実装・実行）。MRS の当てはめ失敗は data_health.failed に書く。
"""
import os
import sys
import warnings
import multiprocessing as mp

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (GROUPS, SEED, load_d1, syms_available, parse_args, write_result,  # noqa: E402
                     tstat, holm)

QID = "Q449"
WIDE48 = GROUPS["wide48"]
START, SEAL = "2008-01-01", "2024-07-01"
SPLIT = 2017
MIN_TRAIN = 500
V_Q, V_MIN_HIST = 0.70, 250
MIN_SHIFT = 60
DEFS = ["S", "F", "V"]
JUDGE_DEFS = ["V", "F"]
N_TESTS = 2


# ----------------------------------------------------------------------------- 入力（t までの値だけ）
def features(df):
    c, h, l = df["close"], df["high"], df["low"]
    sma10 = c.rolling(10).mean()
    ema10 = c.ewm(span=10, adjust=False).mean()
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    hist = (macd - macd.ewm(span=9, adjust=False).mean()) / c
    m20, s20 = c.rolling(20).mean(), c.rolling(20).std(ddof=0)
    pb = (c - (m20 - 2 * s20)) / (4 * s20).replace(0, np.nan)
    hh, ll = h.rolling(14).max(), l.rolling(14).min()
    wr = (hh - c) / (hh - ll).replace(0, np.nan)
    return pd.DataFrame({"sma_dev": c / sma10 - 1, "ema_dev": c / ema10 - 1, "rsi": rsi,
                         "macd_h": hist, "bb_pb": pb, "wr": wr})


def _mrs(y):
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    return MarkovRegression(y, k_regimes=2, trend="c", switching_variance=True)


def _hi_state(mod, params):
    names = list(mod.param_names)
    s0, s1 = params[names.index("sigma2[0]")], params[names.index("sigma2[1]")]
    return 1 if s1 > s0 else 0


def per_symbol(args):
    sym, smoke, seed = args
    warnings.filterwarnings("ignore")
    from sklearn.linear_model import LogisticRegression
    rng = np.random.default_rng(seed)
    out = {"sym": sym, "failed": [], "n_raw": 0}
    df = load_d1(sym, smoke=smoke, rng=rng)
    df = df[(df["time"] >= START) & (df["time"] < SEAL)].reset_index(drop=True)
    out["n_raw"] = int(len(df))
    X = features(df)
    r = df["ret"].values
    r_next = np.r_[r[1:], np.nan]
    gap_next = np.r_[df["gap"].values[1:], True]
    y = (r_next > 0).astype(float)
    ok_lab = np.isfinite(r_next) & (r_next != 0) & (~gap_next)
    ok_x = X.notna().all(axis=1).values
    year = df["year"].values
    years = sorted(set(year))

    # 予測（拡張窓・年 1 回）
    pred = np.full(len(df), np.nan)
    for Y in years:
        tr = ok_lab & ok_x & (year < Y)
        te = ok_x & (year == Y)
        if tr.sum() < MIN_TRAIN or te.sum() == 0:
            continue
        mu, sd = X[tr].mean(), X[tr].std(ddof=0).replace(0, 1)
        m = LogisticRegression(C=1.0, max_iter=1000)
        m.fit(((X[tr] - mu) / sd).values, y[tr])
        pred[te] = (m.predict_proba(((X[te] - mu) / sd).values)[:, 1] > 0.5).astype(float)

    # MRS 入力（先頭の NaN を落とす）
    ok_r = np.isfinite(r)
    idx_r = np.where(ok_r)[0]
    yr = 100 * r[ok_r]
    lab = {k: np.full(len(df), np.nan) for k in DEFS}

    # S: 全期間の平滑化確率
    try:
        mod = _mrs(yr)
        res = mod.fit(disp=False)
        hs = _hi_state(mod, res.params)
        sp = np.asarray(res.smoothed_marginal_probabilities)
        sp = sp[:, hs] if sp.ndim == 2 else sp
        lab["S"][idx_r] = (sp > 0.5).astype(float)
    except Exception as e:  # noqa: BLE001
        out["failed"].append(f"S:{type(e).__name__}")

    # F: 年 Y の前日までで推定 → その母数でフィルタ（t までの情報）
    try:
        mod_full = _mrs(yr)
        yr_year = year[idx_r]
        for Y in years:
            ntr = int((yr_year < Y).sum())
            if ntr < MIN_TRAIN or not (yr_year == Y).any():
                continue
            try:
                mtr = _mrs(yr[:ntr])
                rtr = mtr.fit(disp=False)
                hs = _hi_state(mtr, rtr.params)
                fr = mod_full.filter(rtr.params)
                fp = np.asarray(fr.filtered_marginal_probabilities)
                fp = fp[:, hs] if fp.ndim == 2 else fp
                sel = yr_year == Y
                lab["F"][idx_r[sel]] = (fp[sel] > 0.5).astype(float)
            except Exception as e:  # noqa: BLE001
                out["failed"].append(f"F{Y}:{type(e).__name__}")
    except Exception as e:  # noqa: BLE001
        out["failed"].append(f"F:{type(e).__name__}")

    # V: 過去 σ20 の銘柄内拡張窓分位
    s20 = pd.Series(r).rolling(20).std(ddof=1)
    q = s20.expanding(min_periods=V_MIN_HIST).quantile(V_Q)
    v = np.where(q.notna() & s20.notna(), (s20 >= q).astype(float), np.nan)
    lab["V"] = v

    keep = ok_lab & np.isfinite(pred) & np.isfinite(lab["S"]) & np.isfinite(lab["F"]) & np.isfinite(lab["V"])
    if not np.isfinite(lab["S"]).any() or not np.isfinite(lab["F"]).any():
        keep[:] = False
    out["rows"] = pd.DataFrame({
        "sym": sym, "time": df["time"].values[keep], "year": year[keep],
        "hit": (pred[keep] == y[keep]).astype(int), "up": y[keep].astype(int), "pred": pred[keep].astype(int),
        **{f"reg_{k}": lab[k][keep].astype(int) for k in DEFS},
    })
    return out


# ----------------------------------------------------------------------------- 集計
def cell_stats(d, reg_col):
    """(局面, 銘柄) の基準率を評価期間全体で作り、銘柄×年の超過を出す。"""
    g = d.groupby([reg_col, "sym"]).agg(p=("up", "mean"))
    g["base"] = np.maximum(g["p"], 1 - g["p"])
    d = d.join(g["base"], on=[reg_col, "sym"])
    d = d.assign(exc=d["hit"] - d["base"])
    return d


def summarize(d, k):
    col = f"reg_{k}"
    dd = cell_stats(d, col)
    out = {}
    for rg, name in ((1, "high"), (0, "low")):
        x = dd[dd[col] == rg]
        yv = x.groupby("year").agg(hit=("hit", "mean"), base=("base", "mean"), exc=("exc", "mean"),
                                   p=("up", "mean"), n=("hit", "size"))
        yv = yv[yv["n"] >= 20]
        o = {"n": int(len(x)), "share": float(len(x) / len(dd)),
             "hit": float(x["hit"].mean()), "p_up": float(x["up"].mean()), "base": float(x["base"].mean()),
             "exc": float(x["exc"].mean()), "n_years": int(len(yv)),
             "years_dropped": sorted(set(dd["year"].unique()) - set(yv.index))}
        for per, m in (("all", yv.index >= 0), ("pre", yv.index < SPLIT), ("post", yv.index >= SPLIT)):
            o[f"exc_{per}_yr_mean"] = float(yv.loc[m, "exc"].mean()) if m.any() else float("nan")
            o[f"exc_{per}_t"] = tstat(yv.loc[m, "exc"].values)
            o[f"hit_{per}_yr_mean"] = float(yv.loc[m, "hit"].mean()) if m.any() else float("nan")
        out[name] = o
        out[f"{name}_by_year"] = yv.reset_index().to_dict(orient="list")
    hd = out["high"]["hit"] - out["low"]["hit"]
    bd = out["high"]["base"] - out["low"]["base"]
    out["decomp"] = {"hit_diff": hd, "base_diff": bd, "exc_diff": hd - bd,
                     "base_share": (bd / hd) if abs(hd) > 1e-12 else float("nan")}
    return out


def null_stats(arrs, k, rng, B):
    """局面ラベルを銘柄内で循環シフト。統計量: 高ボラ超過（全期間・行数加重）、高−低の的中率差。
    arrs: 銘柄ごとの (hit, up, {定義: ラベル})（時刻順）。"""
    def stat(regs):
        nH = sH_hit = sH_base = nL = sL_hit = 0.0
        for (hit, up, _), rg in zip(arrs, regs):
            for v in (1, 0):
                m = rg == v
                n = m.sum()
                if n == 0:
                    continue
                p = up[m].mean(); base = max(p, 1 - p); hs = hit[m].sum()
                if v == 1:
                    nH += n; sH_hit += hs; sH_base += base * n
                else:
                    nL += n; sL_hit += hs
        return (sH_hit - sH_base) / nH, sH_hit / nH - sL_hit / nL
    obs = stat([a[2][k] for a in arrs])
    sims = np.empty((B, 2))
    for b in range(B):
        regs = []
        for a in arrs:
            rg = a[2][k]; n = len(rg)
            s = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT)) if n > 2 * MIN_SHIFT else 0
            regs.append(np.roll(rg, s))
        sims[b] = stat(regs)
    return obs, sims


def main():
    args = parse_args(default_B=500)
    rng = np.random.default_rng(args.seed)
    ok, missing = syms_available(WIDE48, smoke=args.smoke)
    syms = ok[:4] if args.smoke else ok
    seeds = [int(x) for x in rng.integers(0, 2**31 - 1, len(syms))]
    jobs = [(s, args.smoke, sd) for s, sd in zip(syms, seeds)]
    with mp.get_context("spawn").Pool(min(8, os.cpu_count() or 2)) as pool:
        outs = pool.map(per_symbol, jobs)
    failed = {o["sym"]: o["failed"] for o in outs if o["failed"]}
    frames = [o["rows"] for o in outs if len(o["rows"])]
    no_rows = [o["sym"] for o in outs if len(o["rows"]) == 0]
    d = pd.concat(frames, ignore_index=True)
    print(f"rows={len(d)} syms={d.sym.nunique()} no_rows={no_rows} failed={failed}")

    res = {"question": "wide48 D1 の高ボラ局面の方向的中率の上乗せは基準率と MRS 平滑化ラベルの先読みで説明されるか",
           "period": [START, SEAL], "n_tests": N_TESTS, "B": args.B, "seed": args.seed,
           "data_health": {"n_ok": len(ok), "missing": missing, "no_rows": no_rows, "failed": failed,
                           "n_rows": int(len(d)), "n_syms_used": int(d.sym.nunique()),
                           "rows_per_sym": d.groupby("sym").size().to_dict()},
           "overall_hit": float(d["hit"].mean()), "overall_p_up": float(d["up"].mean()),
           "label_agreement": {f"{a}{b}": float((d[f"reg_{a}"] == d[f"reg_{b}"]).mean())
                               for a, b in (("S", "F"), ("S", "V"), ("F", "V"))},
           "defs": {}}
    arrs = []
    for s, g in d.groupby("sym"):
        g = g.sort_values("time")
        arrs.append((g["hit"].values, g["up"].values, {k: g[f"reg_{k}"].values for k in DEFS}))
    nullrng = np.random.default_rng(args.seed + 1)
    pvals = {}
    for k in DEFS:
        sm = summarize(d, k)
        obs, sims = null_stats(arrs, k, nullrng, args.B)
        mu, sd = sims.mean(axis=0), sims.std(axis=0, ddof=1)
        q = np.percentile(sims, [2.5, 97.5], axis=0)
        z = (np.array(obs) - mu) / sd
        perm_p_exc = float((1 + (sims[:, 0] >= obs[0]).sum()) / (args.B + 1))
        perm_p_diff = float((1 + (sims[:, 1] >= obs[1]).sum()) / (args.B + 1))
        sm["null"] = {"obs_high_exc": obs[0], "obs_hit_diff": obs[1],
                      "null_mean": mu.tolist(), "null_sd": sd.tolist(), "null_q025_975": q.tolist(),
                      "z_high_exc": float(z[0]), "z_hit_diff": float(z[1]),
                      "perm_p_high_exc": perm_p_exc, "perm_p_hit_diff": perm_p_diff,
                      "high_exc_null_centered": float(obs[0] - mu[0])}
        pvals[k] = perm_p_exc
        res["defs"][k] = sm
    adj = holm([pvals[k] for k in JUDGE_DEFS])
    res["multiple_comparisons"] = {"n_tests": N_TESTS, "tests": JUDGE_DEFS,
                                   "perm_p": [pvals[k] for k in JUDGE_DEFS], "holm": adj.tolist()}
    res["null_degenerate"] = {k: bool(res["defs"][k]["null"]["null_sd"][0] < 1e-9) for k in DEFS}
    res["years_dropped"] = {k: res["defs"][k]["high"]["years_dropped"] for k in DEFS}

    hi = {k: res["defs"][k]["high"] for k in JUDGE_DEFS}
    sup = all(h["exc_all_t"] >= 2 and h["exc_pre_yr_mean"] > 0 and h["exc_post_yr_mean"] > 0 for h in hi.values())
    rej = all(h["exc_all_t"] < 1 for h in hi.values())
    res["verdict"] = "支持" if sup else ("棄却" if rej else "未確定")
    if failed:
        res["verdict_note"] = "data_health.failed あり（MRS の当てはめ失敗）。失敗銘柄を除いた共通標本で判定"
    print("verdict:", res["verdict"])
    for k in DEFS:
        h, l, n = res["defs"][k]["high"], res["defs"][k]["low"], res["defs"][k]["null"]
        print(f"{k}: hitH={h['hit']:.4f} hitL={l['hit']:.4f} baseH={h['base']:.4f} baseL={l['base']:.4f} "
              f"excH_t={h['exc_all_t']:.2f} pre={h['exc_pre_yr_mean']:.4f} post={h['exc_post_yr_mean']:.4f} "
              f"z_exc={n['z_high_exc']:.2f} z_diff={n['z_hit_diff']:.2f} nc={n['high_exc_null_centered']:.4f}")
    write_result(QID, res, smoke=args.smoke, here=HERE)


if __name__ == "__main__":
    main()
