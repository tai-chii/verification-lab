#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成への追加関門（2026-10-29・運用の決まり）: 候補の日次損益 CSV を生き残りの合成に 1/(n+1) 等リスクで足し、相関と合成 Sharpe の増分を出す。
使い方: python3 composite_gate.py <候補の日次CSV> [--col 列名] [--name 表示名]
  候補 CSV: 1 列目が日付。--col を省くと 2 列目。損益の単位は何でもよい（σ で割る）。
基準（記述・最終判定は /lab の事前登録で）: 各生き残りとの日次相関 ≤ 0.15、候補単体の Sharpe ≥ 0.5、合成 Sharpe が前後半とも下がらない。
生き残りの系列: financial-engineering/survivors-correlation-composite/results/survivors_daily_eqrisk.csv（run_survivors.py が作る）"""
import argparse, os, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
SURV = os.path.join(HERE, "..", "financial-engineering", "survivors-correlation-composite", "results", "survivors_daily_eqrisk.csv")
SURV_COLS = ["S17b 買い持ち", "S21 H1 ML", "S23 暗号の上昇時"]
SPLIT = "2021-01-01"


def sh(x):
    x = x.dropna(); return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if len(x) > 20 and x.std(ddof=1) > 0 else float("nan")


def gate(cand: pd.Series, name="候補"):
    S = pd.read_csv(SURV, index_col=0, parse_dates=True)[SURV_COLS]
    c = cand.copy(); c.index = pd.DatetimeIndex(c.index).tz_localize(None).normalize(); c = c.groupby(c.index).sum()
    idx = S.index.intersection(pd.date_range(c.index.min(), c.index.max()))
    S = S.loc[idx]; c = c.reindex(idx).fillna(0.0); c = c / c.std(ddof=1)
    base = S.mean(1); add = pd.concat([S, c], axis=1).mean(1)
    pre = lambda x: x[x.index < SPLIT]; post = lambda x: x[x.index >= SPLIT]
    corr = {k: round(float(c.corr(S[k])), 3) for k in S}
    r = {"name": name, "期間": [str(idx.min().date()), str(idx.max().date())], "n_days": int(len(idx)),
         "単体Sharpe": {"全": round(sh(c), 2), "前": round(sh(pre(c)), 2), "後": round(sh(post(c)), 2)}, "相関": corr,
         "合成Sharpe": {"全": [round(sh(base), 2), round(sh(add), 2)], "前": [round(sh(pre(base)), 2), round(sh(pre(add)), 2)], "後": [round(sh(post(base)), 2), round(sh(post(add)), 2)]}}
    ok_corr = all(v <= 0.15 for v in corr.values()); ok_sh = sh(c) >= 0.5
    ok_add = sh(pre(add)) >= sh(pre(base)) and sh(post(add)) >= sh(post(base))
    r["関門"] = {"相関≤0.15": ok_corr, "単体Sharpe≥0.5": ok_sh, "合成が前後半とも下がらない": ok_add, "通過": bool(ok_corr and ok_sh and ok_add)}
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--col", default=None); ap.add_argument("--name", default=None)
    a = ap.parse_args(); df = pd.read_csv(a.csv, index_col=0, parse_dates=True)
    col = a.col or df.columns[0]; print(json.dumps(gate(df[col], a.name or col), ensure_ascii=False, indent=1))
