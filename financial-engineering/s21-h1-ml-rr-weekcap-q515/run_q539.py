# -*- coding: utf-8 -*-
"""Q539: S21 のコストの厳しさ（事前登録_q539.md）。学習し直さず、売買ごとのスプレッド分の R を出して何倍にもする。"""
import glob, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, "."); import kensho_s21_h1_ml_rr_q515 as K

DATA = sys.argv[1]; TR = sys.argv[2]; OUT = sys.argv[3]; os.makedirs(OUT, exist_ok=True)
tr = pd.read_csv(TR, parse_dates=["entry", "exit"])
rows = []
for s, g in tr.groupby("sym"):
    p = glob.glob(os.path.join(DATA, "**", f"{s}.parquet"), recursive=True)
    p = [x for x in p if "market_data/H1" in x or "market_data" in x and "forward" not in x][0]
    d = K.load(os.path.dirname(p), s)
    bh, bl, bc = d["high"].to_numpy(), d["low"].to_numpy(), d["close"].to_numpy()
    trr = np.maximum(bh - bl, np.maximum(np.abs(bh - np.r_[bc[0], bc[:-1]]), np.abs(bl - np.r_[bc[0], bc[:-1]])))
    D = K.K_ATR * pd.Series(trr).rolling(24, min_periods=24).mean().to_numpy()
    t = pd.DatetimeIndex(d["time"]); pos = pd.Series(np.arange(len(d)), index=t)
    e = pos.reindex(pd.DatetimeIndex(g["entry"])).to_numpy(); x = pos.reindex(pd.DatetimeIndex(g["exit"])).to_numpy()
    ok = np.isfinite(e) & np.isfinite(x); e = e.astype(float); x = x.astype(float)
    sp_open = (d["ask_open"] - d["open"]).clip(lower=0).to_numpy(); sp_close = d["spr"].to_numpy()
    ei = np.where(ok, e, 0).astype(int); xi = np.where(ok, x, 0).astype(int)
    Dv = D[np.maximum(ei - 1, 0)]
    c = np.where(ok, (sp_open[ei] + sp_close[xi]) / Dv, np.nan); sx = np.where(ok, sp_close[xi] / Dv, np.nan)
    gg = g.assign(c=c, sx=sx, i_match=(g["i"].to_numpy() == ei - 1) & ok)
    rows.append(gg)
T = pd.concat(rows).sort_values("exit").reset_index(drop=True)
grp = {"FX主要": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD", "EURGBP"], "円": ["USDJPY", "EURJPY", "GBPJPY"],
       "指数": ["US500", "USTECH", "GER40", "JPN225"], "金": ["XAUUSD"]}
bd = pd.bdate_range(T["exit"].min().normalize().tz_localize(None), T["exit"].max().normalize().tz_localize(None))


def summ(R):
    s = pd.Series(R, index=T["exit"].dt.tz_localize(None).dt.normalize())
    day = s.groupby(level=0).sum().reindex(bd, fill_value=0.0)
    cum = day.cumsum(); dd = float((cum - cum.cummax()).min())
    yr = s.groupby(s.index.year).sum()
    return {"mean_R": float(np.mean(R)), "daily_t": float(day.mean() / day.std(ddof=1) * np.sqrt(len(day))), "total_R": float(np.sum(R)),
            "max_dd_R": dd, "pos_years": int((yr > 0).sum()), "n_years": int(len(yr))}


R0 = T["R"].to_numpy(); c = T["c"].to_numpy(); sx = T["sx"].to_numpy(); slip = np.where(R0 <= -0.95, sx, 0.0)
res = {"n": int(len(T)), "n_unmatched": int(T["c"].isna().sum()), "i_match_rate": float(T["i_match"].mean()),
       "mean_cost_R": float(np.nanmean(c)), "median_cost_R": float(np.nanmedian(c)), "share_stop_exits": float((R0 <= -0.95).mean()), "scen": {}}
c = np.nan_to_num(c); slip = np.nan_to_num(slip)
for k in (1, 1.5, 2, 3):
    for sl in (False, True):
        R = R0 - (k - 1) * c - (slip if sl else 0)
        res["scen"][f"k{k}{'_slip' if sl else ''}"] = summ(R)
res["breakeven_k"] = float(1 + R0.mean() / c.mean())
res["by_group"] = {}
for gname, ss in grp.items():
    m = T["sym"].isin(ss).to_numpy()
    res["by_group"][gname] = {"n": int(m.sum()), "mean_R": float(R0[m].mean()), "mean_cost_R": float(c[m].mean()), "breakeven_k": float(1 + R0[m].mean() / c[m].mean())}
res["by_sym_breakeven_k"] = {s: float(1 + R0[T["sym"].to_numpy() == s].mean() / c[T["sym"].to_numpy() == s].mean()) for s in sorted(T["sym"].unique())}
sc = res["scen"]
res["verdict"] = {"2倍に耐える": sc["k2"]["mean_R"] > 0 and sc["k2"]["daily_t"] >= 2, "3倍に耐える": sc["k3"]["mean_R"] > 0 and sc["k3"]["daily_t"] >= 2,
                  "滑りにも耐える": sc["k1_slip"]["mean_R"] > 0 and sc["k1_slip"]["daily_t"] >= 2}
json.dump(res, open(os.path.join(OUT, "result_q539.json"), "w"), ensure_ascii=False, indent=1)
T.to_csv(os.path.join(OUT, "trades_cost_q539.csv"), index=False)
print(json.dumps({k: v for k, v in res.items() if k != "by_sym_breakeven_k"}, ensure_ascii=False, indent=1)); print(json.dumps(res["by_sym_breakeven_k"], ensure_ascii=False))
