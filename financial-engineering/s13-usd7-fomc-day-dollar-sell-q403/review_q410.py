#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q410（Q403 の Opus 見直し）: FOMC 発表日のドル売りを発表 1 回単位に直して、集中度・期間依存を記述する。判定規則は変えない（記述だけ）。
等金額 7 ペアの当日 gross リターン（前日終値→当日終値、ドル売り向き）を発表ごとに平均。封印 time<2024-07-01。"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools")); sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core.data import load_d1  # noqa
import s1x as X  # noqa

rows = []
for s in X.USD7:
    df = load_d1(s); df = df[pd.to_datetime(df["time"]) < X.SEAL].reset_index(drop=True)
    df = df[pd.to_datetime(df["time"]) >= "2010-01-01"].reset_index(drop=True)
    r = np.log(df["close"]).diff().values * (1 if X.USD_IS_QUOTE[s] else -1)
    for j in X.fomc_day_index(df):
        if j >= 1:
            rows.append((pd.Timestamp(df["time"].iloc[j]).date(), s, r[j] * 1e4))
ev = pd.DataFrame(rows, columns=["date", "sym", "bp"]).groupby("date")["bp"].mean()
ev.index = pd.to_datetime(ev.index)
def stat(x):
    x = np.asarray(x); return {"n": int(len(x)), "mean_bp": round(float(x.mean()), 2), "t": round(float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))), 2),
                               "hit": round(float((x > 0).mean()), 3), "median_bp": round(float(np.median(x)), 2)}
pre, post = ev[ev.index.year < 2017], ev[ev.index.year >= 2017]
out = {"all": stat(ev), "pre": stat(pre), "post": stat(post),
       "post_excl_2022_2024": stat(post[post.index.year < 2022]), "post_2022_2024": stat(post[post.index.year >= 2022]),
       "pre_excl_2014": stat(pre[pre.index.year != 2014]),
       "post_drop_top5": stat(post.sort_values().iloc[:-5]), "all_drop_top5": stat(ev.sort_values().iloc[:-5]),
       "top5_post": {str(k.date()): round(v, 1) for k, v in post.sort_values().iloc[-5:].items()},
       "bottom5_all": {str(k.date()): round(v, 1) for k, v in ev.sort_values().iloc[:5].items()},
       "by_year": {int(y): stat(g) for y, g in ev.groupby(ev.index.year)}}
ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
p = os.path.join(HERE, "results", f"Q410_review_events_{ts}.json")
json.dump(out, open(p, "w"), ensure_ascii=False, indent=1); print(p)
print(json.dumps({k: v for k, v in out.items() if k != "by_year"}, ensure_ascii=False, indent=1))
