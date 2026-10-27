# 土日決済の不具合（K.daily が平日以外の決済を落とす）を直した日次集計で、保存済みの取引記録から t・最大下落を出し直す。学習はしない。
import json, numpy as np, pandas as pd
T = lambda s: pd.Timestamp(s)
JOBS = [  # (Q, 取引ファイル, 開始, 終了, 説明)
    ("Q519", "results/trades_q519_W-exp_m1.csv", "2014-10-01", "2023-10-01", "WF9年 本体"),
    ("Q521", "results/trades_q519_W-exp-mtf_m1.csv", "2014-10-01", "2023-10-01", "WF9年 ＋H4/D1"),
    ("Q526", "results/trades_q519_W-exp-xs.csv", "2014-10-01", "2023-10-01", "WF9年 ＋全銘柄の値動き"),
    ("Q520", "results/trades_q520_d1_48.csv", "2014-10-01", "2023-10-01", "日足48銘柄 WF9年"),
    ("Q522", "results/trades_val_q522_m1.csv", "2023-10-01", "2025-10-01", "仮判断2年"),
    ("Q524-15", "results/trades_q524_15.csv", "2014-10-01", "2025-10-01", "WF11年 15銘柄"),
    ("Q524-円4", "results/trades_q524_new4.csv", "2014-10-01", "2025-10-01", "銘柄外 円クロス4"),
    ("Q525", "results/trades_q525_new16.csv", "2014-10-01", "2025-10-01", "銘柄外 16銘柄"),
    ("Q527", "results/trades_final_q527.csv", "2025-10-01", "2026-10-01", "最終1年 19銘柄"),
    ("Q530-A", "results/trades_q530_A_現行.csv", "2014-10-01", "2023-10-01", "上限あり（現行）"),
    ("Q530-B", "results/trades_q530_B_週上限なし.csv", "2014-10-01", "2023-10-01", "週上限なし"),
    ("Q530-C", "results/trades_q530_C_上限なし.csv", "2014-10-01", "2023-10-01", "上限なし"),
]

def tstat(x):
    x = np.asarray(x, float); return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))

def maxdd(x):
    eq = np.cumsum(x); return float((eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min())

def series(tr, col, s0, s1, fix):
    d = pd.to_datetime(tr["exit"], utc=True).dt.tz_convert(None).dt.normalize()
    if fix:
        wd = d.dt.weekday; d = d + pd.to_timedelta(np.where(wd == 5, 2, np.where(wd == 6, 1, 0)), unit="D")
        days = pd.bdate_range(T(s0), T(s1) - pd.Timedelta(days=1))
    else:
        days = pd.bdate_range(T(s0), T(s1) - pd.Timedelta(days=1))
    return tr.assign(day=d).groupby("day")[col].sum().reindex(days, fill_value=0.0)

out = {}
for q, f, s0, s1, lab in JOBS:
    tr = pd.read_csv(f); col = "R_m1" if "R_m1" in tr else "R"
    tr = tr[tr[col].notna()]
    wd = pd.to_datetime(tr["exit"], utc=True).dt.tz_convert(None).dt.weekday
    o, n = series(tr, col, s0, s1, False), series(tr, col, s0, s1, True)
    out[q] = dict(説明=lab, 損益の列=col, 件数=int(len(tr)), 土日決済=int((wd >= 5).sum()), 土日決済のR合計=round(float(tr.loc[wd >= 5, col].sum()), 1),
                  平均R=round(float(tr[col].mean()), 4), 合計R=round(float(tr[col].sum()), 1),
                  t_旧=round(tstat(o), 2), t_新=round(tstat(n), 2), 最大下落R_旧=round(maxdd(o.to_numpy()), 1), 最大下落R_新=round(maxdd(n.to_numpy()), 1))
    print(q, json.dumps(out[q], ensure_ascii=False), flush=True)
json.dump(out, open("results/recompute_daily_fix.json", "w"), ensure_ascii=False, indent=1)
