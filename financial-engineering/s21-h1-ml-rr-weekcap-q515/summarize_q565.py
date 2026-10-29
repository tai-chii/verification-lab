# -*- coding: utf-8 -*-
"""Q565 の集計（事前登録_q565.md の判定をそのまま当てる）。使い方: python3 summarize_q565.py OUT_DIR"""
import glob, json, os, sys
import numpy as np
S = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(sys.argv[1], "stats_q565_seed*.json")))]
S.sort(key=lambda d: d["data_seed"])
t = np.array([d["t"] for d in S]); npass = sum(d["passed"] for d in S); n = len(S)
rate = npass / n; med = float(np.median(t))
verdict = "健全" if (rate <= 0.10 and med < 1) else ("要修正" if rate > 0.10 else "未確定")
bad_years = [d["data_seed"] for d in S if any(v == 0 for v in d["years_R"].values()) or len(d["years_R"]) != 11]
out = dict(n_seeds=n, n_pass=npass, pass_rate=rate, t_median=med, t_min=float(t.min()), t_max=float(t.max()),
           n_t_ge_2=int((t >= 2).sum()), mean_R_median=float(np.median([d["mean_R"] for d in S])),
           mean_trades=float(np.mean([d["n"] for d in S])), pos_years=[d["pos_years"] for d in S],
           atr_ratio=[round(d["check"]["atr_ratio_median"], 4) for d in S],
           sign_agree=[round(d["check"]["sign_agree_lag1_mean"], 4) for d in S], seeds_with_empty_year=bad_years, verdict=verdict,
           per_seed=[{k: d[k] for k in ("data_seed", "n", "mean_R", "t", "total_R", "max_dd_R", "pos_years", "passed")} for d in S])
json.dump(out, open(os.path.join(sys.argv[1], "result_q565.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "per_seed"}, ensure_ascii=False))
