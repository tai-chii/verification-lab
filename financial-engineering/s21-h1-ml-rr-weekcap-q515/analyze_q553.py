# -*- coding: utf-8 -*-
"""Q553 の判定と原因の切り分け（事前登録_q553.md）。使い方: python3 analyze_q553.py DATA E1_TRADES FOLD2025_TRADES OUT"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kensho_s21_h1_ml_rr_q515 as K
DATA, E1, F25, OUT = sys.argv[1:5]
T = pd.concat([pd.read_csv(E1, parse_dates=["entry", "exit"]), pd.read_csv(F25, parse_dates=["entry", "exit"])], ignore_index=True)
rows = []
for s, g in T.groupby("sym"):                      # Q539 と同じ c（入りの足の始値と出の足の終値のスプレッド ÷ 損切り幅）
    d = K.load(DATA, s); bh, bl, bc = d["high"].to_numpy(), d["low"].to_numpy(), d["close"].to_numpy(); pc = np.r_[bc[0], bc[:-1]]
    D = K.K_ATR * pd.Series(np.maximum(bh - bl, np.maximum(np.abs(bh - pc), np.abs(bl - pc)))).rolling(24, min_periods=24).mean().to_numpy()
    pos = pd.Series(np.arange(len(d)), index=pd.DatetimeIndex(d["time"]))
    e = pos.reindex(pd.DatetimeIndex(g["entry"])).to_numpy(); x = pos.reindex(pd.DatetimeIndex(g["exit"])).to_numpy(); ok = np.isfinite(e) & np.isfinite(x)
    ei = np.where(ok, e, 0).astype(int); xi = np.where(ok, x, 0).astype(int)
    c = np.where(ok, ((d["ask_open"] - d["open"]).clip(lower=0).to_numpy()[ei] + d["spr"].to_numpy()[xi]) / D[np.maximum(ei - 1, 0)], np.nan)
    rows.append(g.assign(c=c, D=D[np.maximum(ei - 1, 0)], px=bc[np.maximum(ei - 1, 0)]))
T = pd.concat(rows); T["gross"] = T["R"] + T["c"]; T["side"] = np.where(T["a"] < 3, "買い", "売り")
GRP = {"FX主要": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD", "EURGBP"], "円": ["USDJPY", "EURJPY", "GBPJPY"], "指数": ["US500", "USTECH", "GER40", "JPN225"], "金": ["XAUUSD"]}
T["grp"] = T["sym"].map({s: g for g, ss in GRP.items() for s in ss})
yrs = sorted(T["fold"].unique()); yr = T.groupby("fold")
res = {"n_years": len(yrs), "by_year": {}}
for Y, g in yr:
    res["by_year"][int(Y)] = dict(n=int(len(g)), mean_R=round(float(g.R.mean()), 4), gross_R=round(float(g.gross.mean()), 4), cost_R=round(float(g.c.mean()), 4),
                                  win=round(float((g.R > 0).mean()), 3), share_buy=round(float((g.side == "買い").mean()), 3),
                                  rr_mean=round(float(np.array([K.ACTIONS[a][1] for a in g.a]).mean()), 2),
                                  calib_slope=round(float(np.polyfit(g.pred, g.R, 1)[0]), 3), D_over_px_bp=round(float((g.D / g.px).median() * 1e4), 1))
m = np.array([res["by_year"][int(Y)]["mean_R"] for Y in yrs]); xs = np.arange(len(m))
slope = float(np.polyfit(xs, m, 1)[0]); rng = np.random.default_rng(20261027)
perm = np.array([np.polyfit(xs, rng.permutation(m), 1)[0] for _ in range(20000)])
p = float((1 + (perm <= slope).sum()) / (len(perm) + 1))
res["trend"] = dict(slope_R_per_year=round(slope, 5), p_one_sided=round(p, 4), mean_first_half=round(float(m[:6].mean()), 4), mean_second_half=round(float(m[6:].mean()), 4))
res["verdict"] = "減衰している" if p < 0.05 else ("ばらつきの範囲" if p >= 0.20 else "中間")
# 粗利・コストの傾きも同じ検定で（記述）
for k in ("gross_R", "cost_R"):
    v = np.array([res["by_year"][int(Y)][k] for Y in yrs]); sl = float(np.polyfit(xs, v, 1)[0])
    pp = np.array([np.polyfit(xs, rng.permutation(v), 1)[0] for _ in range(20000)])
    res[f"trend_{k}"] = dict(slope=round(sl, 5), p_down=round(float((1 + (pp <= sl).sum()) / 20001), 4), p_up=round(float((1 + (pp >= sl).sum()) / 20001), 4))
early, late = T[T.fold <= 2019], T[T.fold >= 2020]
res["by_group"] = {gname: dict(early_R=round(float(early[early.grp == gname].R.mean()), 4), late_R=round(float(late[late.grp == gname].R.mean()), 4),
                               early_gross=round(float(early[early.grp == gname].gross.mean()), 4), late_gross=round(float(late[late.grp == gname].gross.mean()), 4),
                               early_cost=round(float(early[early.grp == gname].c.mean()), 4), late_cost=round(float(late[late.grp == gname].c.mean()), 4))
                   for gname in GRP}
res["by_side"] = {sd: dict(early_R=round(float(early[early.side == sd].R.mean()), 4), late_R=round(float(late[late.side == sd].R.mean()), 4)) for sd in ("買い", "売り")}
json.dump(res, open(os.path.join(OUT, "result_q553.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
