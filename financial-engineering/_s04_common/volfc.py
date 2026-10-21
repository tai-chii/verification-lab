# -*- coding: utf-8 -*-
"""S04b 補正版（Q387/Q388）のボラ予測の共通部（2026-10-22・/lab-plan ターミナル版 N=4）。
Q376 の欠陥: log(RV5) を学習して exp で戻しただけなので中央値の予測になり、実現/予測の平均が 2.29（上に偏る）。σ̂ が小さすぎて規程モードの建玉が過大。
ここでは「水準で学習する」か「学習窓の残差でスミアリング補正する」かで平均を狙い、較正（実現/予測の平均）を測ってから QLIKE とサイジングに進む。
fe_core・s04ml.py は書き換えない。walk_forward・ridge_fit_predict・qlike は fe_core のもの。

予測器（5 本・格子はこれで固定。TrialLog で数える）:
  naive60         σ60²（R.rolling(60).std()²）。基準。
  ewma94          RiskMetrics の EWMA 分散（λ=0.94・adjust なし）。
  har_level_persym  Corsi 2009 の HAR-RV（RV_1・RV_5・RV_22 の水準）を銘柄別に、学習窓 4 年固定長・embargo 10 でリッジ（α=1・標準化は学習窓内）。← main
  har_level_pool  同じ HAR を 48 銘柄プールで。水準の違いを σ60² で正規化（y/σ60²・x/σ60²）してから学習し、予測に σ60² を掛け戻す。
  loghar_smear    Q376 型の log-HAR（log RV_1/5/22 → log RV5・プール・リッジ α=1）に Duan 1983 のスミアリング係数 mean(exp(残差_学習窓)) を掛ける。
予測分散の下限: 0.1×σ60²（負・ゼロの予測を避ける。事前固定）。
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
from fe_core import walk_forward, ridge_fit_predict, qlike, nw_t, tstat, fmt  # noqa: E402

SEAL = pd.Timestamp("2024-07-01")
K = 5
TRAIN_YEARS = 4
EMBARGO = 10
PREDICTORS = ["naive60", "ewma94", "har_level_persym", "har_level_pool", "loghar_smear"]
MAIN = "har_level_persym"
FLOOR_MULT = 0.1
CALIB_RANGE = (0.8, 1.25)
RV_EPS = 1e-10


def rv_target_level(df, k=K):
    """翌 k 日の実現分散（r² の平均・水準）。index=time。末尾 k 本は NaN。gap 行の ret（複数日分）はそのまま（Q376 と同じ。結果に明記）。"""
    r2 = (df["ret"].astype(float) ** 2).to_numpy()
    n = len(r2); fwd = np.full(n, np.nan)
    cs = np.r_[0.0, np.nancumsum(r2)]
    for i in range(n - k):
        fwd[i] = (cs[i + 1 + k] - cs[i + 1]) / k
    return pd.Series(fwd, index=pd.to_datetime(df["time"]))


def har_features(df):
    """HAR-RV の説明変数（t までの情報）: rv1=r²[t]、rv5=直近 5 日平均、rv22=直近 22 日平均、sig60sq=σ60²。index=time。"""
    r2 = (df["ret"].astype(float) ** 2)
    X = pd.DataFrame({"rv1": r2, "rv5": r2.rolling(5).mean(), "rv22": r2.rolling(22).mean(),
                      "sig60sq": df["ret"].astype(float).rolling(60, min_periods=30).std() ** 2})
    X.index = pd.to_datetime(df["time"]); X.index.name = "time"
    return X


def _wf_rows(times):
    return walk_forward(times, train_years=TRAIN_YEARS, test_years=1, embargo_days=EMBARGO, end=SEAL)


def _fit_wf(Xv, yv, times, min_train=200, smear=False):
    """年次ウォークフォワードでリッジ（α=1）。smear=True なら各 fold の学習残差から Duan のスミアリング係数を返す（exp 空間）。"""
    out = np.full(len(yv), np.nan); sm = np.full(len(yv), np.nan)
    for tr, te, _ in _wf_rows(times):
        if tr.sum() < min_train or te.sum() == 0:
            continue
        out[te] = ridge_fit_predict(Xv[tr], yv[tr], Xv[te], alpha=1.0)
        if smear:
            fit_tr = ridge_fit_predict(Xv[tr], yv[tr], Xv[tr], alpha=1.0)
            sm[te] = float(np.mean(np.exp(yv[tr] - fit_tr)))
    return out, sm


def predict_all(dfs, R, which=PREDICTORS):
    """予測器ごとの日次分散の予測 DataFrame(date×sym)。評価窓（ウォークフォワードの test）以外は NaN（naive/ewma は全期間）。
    返り値 (preds: {name: DataFrame}, info: {name: {...}})。"""
    sig60sq = R.rolling(60, min_periods=30).std() ** 2
    feats = {s: har_features(df) for s, df in dfs.items()}
    ys = {s: rv_target_level(df) for s, df in dfs.items()}
    preds, info = {}, {}
    for name in which:
        if name == "naive60":
            preds[name] = sig60sq.copy(); info[name] = {"kind": "naive"}; continue
        if name == "ewma94":
            preds[name] = (R ** 2).ewm(alpha=1 - 0.94, adjust=False).mean().where(R.notna()); info[name] = {"kind": "ewma", "lambda": 0.94}; continue
        cols = ["rv1", "rv5", "rv22"]; out = {}
        if name == "har_level_persym":
            n_folds = 0
            for s in dfs:
                X = feats[s][cols]; y = ys[s]; ok = X.notna().all(axis=1) & y.notna()
                Xv = X[ok].to_numpy(float); yv = y[ok].to_numpy(float); t = X.index[ok]
                p, _ = _fit_wf(Xv, yv, t); n_folds += len(_wf_rows(t))
                out[s] = pd.Series(p, index=t)
            preds[name] = pd.DataFrame(out).sort_index(); info[name] = {"kind": "har_level_persym", "n_folds_total": n_folds}
        elif name in ("har_level_pool", "loghar_smear"):
            Xs, ys_, ms = [], [], []
            for s in dfs:
                X = feats[s]; y = ys[s]
                if name == "har_level_pool":
                    sc = X["sig60sq"].replace(0, np.nan)
                    Xn = X[cols].div(sc, axis=0); yn = y / sc
                else:
                    Xn = np.log(X[cols].clip(lower=RV_EPS)); yn = np.log(y.clip(lower=RV_EPS))
                ok = Xn.notna().all(axis=1) & yn.notna() & np.isfinite(yn)
                Xs.append(Xn[ok]); ys_.append(yn[ok]); ms.append(pd.DataFrame({"time": Xn.index[ok], "sym": s}))
            Xp = pd.concat(Xs); yp = pd.concat(ys_); meta = pd.concat(ms, ignore_index=True)
            keep = (meta["time"] < SEAL).to_numpy(); Xp, yp, meta = Xp.iloc[keep], yp.iloc[keep], meta.iloc[keep].reset_index(drop=True)
            p, sm = _fit_wf(Xp.to_numpy(float), yp.to_numpy(float), meta["time"].to_numpy(), min_train=500, smear=(name == "loghar_smear"))
            pf = pd.DataFrame({"time": meta["time"], "sym": meta["sym"], "p": p}).pivot(index="time", columns="sym", values="p").sort_index()
            if name == "har_level_pool":
                preds[name] = pf.reindex(index=R.index, columns=R.columns) * sig60sq
                info[name] = {"kind": "har_level_pool", "normalizer": "sig60sq"}
            else:
                smf = pd.DataFrame({"time": meta["time"], "sym": meta["sym"], "p": sm}).pivot(index="time", columns="sym", values="p").sort_index()
                preds[name] = np.exp(pf.reindex(index=R.index, columns=R.columns)) * smf.reindex(index=R.index, columns=R.columns)
                info[name] = {"kind": "loghar_smear", "smear_median": fmt(float(np.nanmedian(sm))) if np.isfinite(sm).any() else None}
        else:
            raise ValueError(name)
        # 下限（事前固定）: 0.1×σ60²
        pr = preds[name].reindex(index=R.index, columns=R.columns)
        preds[name] = pr.where(pr.isna(), np.maximum(pr, FLOOR_MULT * sig60sq))
    return preds, info, sig60sq


def evaluate(pred, RV, sig60sq, mask):
    """QLIKE（銘柄ごと→平均）、σ60 との損失差（日次・銘柄平均 → nw_t lag=K、年単位 t）、較正（実現/予測の平均・中央値）。mask: 評価期間の bool（index）。"""
    p = pred.loc[mask]; ev = RV.loc[mask]; b = sig60sq.loc[mask]
    ql = {s: qlike(p[s].to_numpy(), ev[s].to_numpy()) for s in p.columns}
    ql_vals = np.array([v for v in ql.values() if v == v], float)
    l_this = (ev / p - np.log(ev / p) - 1); l_base = (ev / b - np.log(ev / b) - 1)
    diff = (l_base - l_this).where(p.notna() & ev.notna() & b.notna()).mean(axis=1).dropna()
    yr = diff.groupby(diff.index.year).mean()
    ratio = (ev / p).where(p.notna() & ev.notna())
    per_sym_mean = ratio.mean(axis=0)
    return {"qlike_mean": fmt(float(ql_vals.mean())) if len(ql_vals) else None, "qlike_n_syms": int(len(ql_vals)),
            "loss_diff_vs_sig60_mean": fmt(diff.mean()) if len(diff) else None,
            "loss_diff_nw_t": fmt(nw_t(diff.to_numpy(), lag=K)) if len(diff) > 10 else None,
            "loss_diff_year_t": fmt(tstat(yr.to_numpy())) if len(yr) > 1 else None, "loss_diff_years": {int(k): fmt(v) for k, v in yr.items()},
            "calib_mean_ratio": fmt(float(per_sym_mean.mean())) if per_sym_mean.notna().any() else None,
            "calib_median_ratio": fmt(float(np.nanmedian(ratio.to_numpy()))) if ratio.notna().any().any() else None,
            "calib_ok": bool(per_sym_mean.notna().any() and CALIB_RANGE[0] <= float(per_sym_mean.mean()) <= CALIB_RANGE[1]),
            "n_rows": int(ratio.notna().sum().sum())}


def eval_mask(index, eval_start):
    return (index >= pd.Timestamp(eval_start)) & (index < SEAL)


def rv_wide(dfs):
    return pd.DataFrame({s: rv_target_level(df) for s, df in dfs.items()}).sort_index()
