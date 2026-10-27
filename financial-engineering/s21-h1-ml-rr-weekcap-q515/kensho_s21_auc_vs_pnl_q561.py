# -*- coding: utf-8 -*-
"""Q561: RF の四半期 AUC（Q560・コスト抜き）は S21 WF（Q555 の腕 WX）の同じ四半期の損益と対応するか（事前登録_q561.md）。
事前登録 事前登録_q561.md と同一・変更禁止。学習はしない。既存の結果ファイルを突き合わせるだけ。

【出典】Q559・Q560（四半期の難しさの散らばりは本物・銘柄差は雑音・ラグ 1 自己相関 0.1）／ Q555（S21 WF の 108 か月・腕 WX＝拡大窓・毎月学習し直し、Y＝年 1 回）。
【仮説】同じ特徴量で測った「局面の難しさ」（RF の学習外 AUC）が低い四半期は、S21 の 1 件あたり R も低い。
【データ】`results/cells_q560.csv`・`results/result_q560.json`（per_q_auc）・`results/trades_q555.csv.gz`（腕 WX・入った足の四半期で集計）。
  重なる期間 2016Q4〜2025Q3 の 36 四半期。
【定義】四半期 AUC = Q560 の per_q_auc（15 銘柄プール）。四半期 R = WX の売買を入った足の四半期で集め、1 件あたり平均 R（主）と合計 R（記述）。
  セル = 銘柄 × 四半期（WX の売買 ≥10 件のセルだけ）。
【測るもの】
  主: ρ_q = 四半期 AUC と四半期の 1 件あたり R の Spearman（36 点）。
  副 1: ρ_cell = セル AUC（Q560）とセルの 1 件あたり R の Spearman。
  副 2（先読み）: ρ_lag = 前の四半期の AUC と 今の四半期の 1 件あたり R の Spearman（35 点）。
  記述: 腕 Y でも同じ 3 つ・合計 R 版・四半期 AUC の上位 1/3 と下位 1/3 の四半期の平均 R の差。
【帰無】四半期（またはセル）の並べ替え B=5000。片側 p =(1+#{帰無 ρ ≥ 観測})/(B+1)。頑健性: 四半期の循環シフト（35 通り全部）での順位。
【判定（事前固定・変更禁止・多重比較 3 本〔ρ_q・ρ_cell・ρ_lag〕に Holm）】
- 支持（地図は S21 の損益と対応する）: ρ_q ≥ 0.3 かつ Holm 後 p < 0.05。
- 棄却（対応しない）: ρ_q ≤ 0。
- 未確定: それ以外。ρ_lag が Holm 後 p<0.05 なら「先読みにも使える」と記述に足す（判定には使わない）。
【捨てた案】Q559（コスト込み）の AUC を使う（コストの予測が混ざる）・月次で対応を見る（Q560 の地図は四半期）・S21 の日次 t と対応させる — の 3 つ。
【知識の締め切り】Claude はおよそ 2026-06。期間はすべて締め切り前。
【委託の確かめ方】`result_q561.json` の `judgement` は機械判定。`quarters_q561.csv` を散布図（横 AUC・縦 1 件あたり R）にして見る。
【実装】結果ファイルの突き合わせだけ。`--smoke` は合成の 2 ファイルで通す。

使い方: python3 kensho_s21_auc_vs_pnl_q561.py RESULTS_DIR [--B 5000] [--smoke]
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
from scipy import stats as sps

QID = "Q561"
SEED = 20261028
Q0, Q1 = "2016-Q4", "2025-Q3"
MIN_CELL_TRADES = 10
TESTS = ["rho_q", "rho_cell", "rho_lag"]


def qlabel(ts):
    ts = pd.Timestamp(ts)
    return f"{ts.year}-Q{(ts.month - 1) // 3 + 1}"


def qrange(q0, q1):
    y0, k0 = int(q0[:4]), int(q0[-1]); y1, k1 = int(q1[:4]), int(q1[-1]); out = []
    y, k = y0, k0
    while (y, k) <= (y1, k1):
        out.append(f"{y}-Q{k}"); k += 1
        if k == 5:
            y += 1; k = 1
    return out


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); m = np.isfinite(a) & np.isfinite(b)
    return float(sps.spearmanr(a[m], b[m]).statistic) if m.sum() >= 3 else np.nan


def perm_p(a, b, B, rng):
    obs = spearman(a, b); a = np.asarray(a, float); b = np.asarray(b, float)
    null = np.array([spearman(a, rng.permutation(b)) for _ in range(B)])
    null = null[np.isfinite(null)]
    return obs, float((1 + (null >= obs).sum()) / (len(null) + 1)), float(null.mean()), float(null.std(ddof=1))


def circ_rank(a, b):
    """四半期の循環シフト（0 を除く全部）に対する観測の順位（記述）。"""
    a = np.asarray(a, float); b = np.asarray(b, float); n = len(a)
    vals = np.array([spearman(a, np.roll(b, k)) for k in range(1, n)])
    return float((vals >= spearman(a, b)).mean()), float(np.nanmean(vals))


def holm(p):
    p = np.asarray(p, float); m = len(p); order = np.argsort(p); adj = np.empty(m); run = 0.0
    for k, i in enumerate(order):
        run = max(run, (m - k) * p[i]); adj[i] = min(1.0, run)
    return adj


def judge(rho_q, p_holm_q):
    if rho_q >= 0.3 and p_holm_q < 0.05:
        return "支持（地図は S21 の損益と対応する）"
    if rho_q <= 0:
        return "棄却（対応しない）"
    return "未確定"


def load_inputs(rdir, smoke, rng):
    if smoke:
        qs = qrange(Q0, Q1); syms = ["EURUSD", "US500", "XAUUSD"]
        per_q = {q: 0.52 + rng.normal(0, 0.015) for q in qs}
        cells = pd.DataFrame([(s, q, per_q[q] + rng.normal(0, 0.03)) for s in syms for q in qs], columns=["sym", "q", "auc"])
        rows = []
        for arm in ["WX", "Y"]:
            for q in qs:
                for s in syms:
                    n = 40; t = pd.Timestamp(f"{q[:4]}-{3*int(q[-1])-2:02d}-15", tz="UTC")
                    rows += [(s, t, arm, (per_q[q] - 0.52) * 5 + rng.normal(0, 1)) for _ in range(n)]
        trades = pd.DataFrame(rows, columns=["sym", "entry", "arm", "R"])
        return per_q, cells, trades
    r = json.load(open(os.path.join(rdir, "result_q560.json")))
    cells = pd.read_csv(os.path.join(rdir, "cells_q560.csv"))
    trades = pd.read_csv(os.path.join(rdir, "trades_q555.csv.gz"))
    trades["entry"] = pd.to_datetime(trades["entry"], utc=True)
    return r["per_q_auc"], cells, trades


def analyze(per_q, cells, trades, arm, qs, B, rng):
    t = trades[trades["arm"] == arm].copy(); t["q"] = t["entry"].map(qlabel); t = t[t["q"].isin(qs)]
    qa = pd.Series(per_q).reindex(qs).astype(float)
    qr = t.groupby("q")["R"].agg(["mean", "sum", "count"]).reindex(qs)
    df = pd.DataFrame(dict(q=qs, auc=qa.to_numpy(), mean_R=qr["mean"].to_numpy(), sum_R=qr["sum"].to_numpy(), n=qr["count"].to_numpy()))
    rho_q, p_q, nm_q, ns_q = perm_p(df["auc"], df["mean_R"], B, rng)
    rho_sum = spearman(df["auc"], df["sum_R"])
    rank_circ, mean_circ = circ_rank(df["auc"].to_numpy(), df["mean_R"].to_numpy())
    # セル
    cr = t.groupby(["sym", "q"])["R"].agg(["mean", "count"]).reset_index()
    cm = cells.merge(cr, on=["sym", "q"], how="inner"); cm = cm[cm["count"] >= MIN_CELL_TRADES]
    rho_cell, p_cell, nm_c, ns_c = perm_p(cm["auc"], cm["mean"], B, rng)
    # 先読み
    rho_lag, p_lag, nm_l, ns_l = perm_p(df["auc"].to_numpy()[:-1], df["mean_R"].to_numpy()[1:], B, rng)
    # 上位/下位 1/3
    k = len(df) // 3; srt = df.sort_values("auc")
    terc = dict(low_third_mean_R=float(srt["mean_R"].head(k).mean()), high_third_mean_R=float(srt["mean_R"].tail(k).mean()))
    return dict(arm=arm, n_quarters=int(df["auc"].notna().sum()), n_cells=int(len(cm)),
                rho_q=dict(obs=rho_q, p_raw=p_q, null_mean=nm_q, null_sd=ns_q, circ_shift_rank=rank_circ, circ_shift_mean=mean_circ),
                rho_cell=dict(obs=rho_cell, p_raw=p_cell, null_mean=nm_c, null_sd=ns_c),
                rho_lag=dict(obs=rho_lag, p_raw=p_lag, null_mean=nm_l, null_sd=ns_l),
                rho_q_sumR=rho_sum, terciles=terc), df, cm


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("results"); ap.add_argument("--B", type=int, default=5000); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(); rng = np.random.default_rng(SEED); tag = "smoke_" if a.smoke else ""
    os.makedirs(a.results, exist_ok=True)
    per_q, cells, trades = load_inputs(a.results, a.smoke, rng)
    qs = qrange(Q0, Q1)
    res = dict(qid=QID, run_at=time.strftime("%Y-%m-%d %H:%M"), smoke=a.smoke, B=a.B, quarters=f"{Q0}〜{Q1}（{len(qs)}）", min_cell_trades=MIN_CELL_TRADES)
    main_res, df, cm = analyze(per_q, cells, trades, "WX", qs, a.B, rng)
    p_raw = [main_res[k]["p_raw"] for k in TESTS]; p_h = holm(p_raw)
    for k, ph in zip(TESTS, p_h):
        main_res[k]["p_holm"] = float(ph)
    res["WX"] = main_res
    res["Y"] = analyze(per_q, cells, trades, "Y", qs, a.B, rng)[0]
    res["judgement"] = judge(main_res["rho_q"]["obs"], main_res["rho_q"]["p_holm"]); res["machine_verdict"] = res["judgement"]
    res["lag_note"] = "先読みにも使える（ρ_lag Holm 後 p<0.05）" if main_res["rho_lag"]["p_holm"] < 0.05 else "先読みは確認できない"
    df.to_csv(os.path.join(a.results, f"{tag}quarters_q561.csv"), index=False); cm.to_csv(os.path.join(a.results, f"{tag}cells_q561.csv"), index=False)
    with open(os.path.join(a.results, f"{tag}result_q561.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(dict(judgement=res["judgement"], lag=res["lag_note"], WX={k: main_res[k] for k in TESTS}, terciles=main_res["terciles"],
                          Y_rho_q=res["Y"]["rho_q"]["obs"]), ensure_ascii=False, indent=1)); print("done")


if __name__ == "__main__":
    main()
