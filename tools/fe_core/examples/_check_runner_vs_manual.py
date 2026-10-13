# Runner と、土台の関数を直接呼んだ手書きの流れが同じ数値になるか（銘柄×年の bp・年単位 t・Sharpe）。B=0 で帰無は省く。
import os, sys, json, glob, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import fe_core as F
from kensho_example_tsmom_runner import SPEC, strategy

t0 = time.time()
path, res = F.Runner(SPEC, strategy, here=HERE).execute(argv=["--B", "0"])
ys = pd.read_csv(sorted(glob.glob(os.path.join(HERE, "results", "EXAMPLE_year_sym_*.csv")))[-1])
# 手書き
rows = []
for s in F.SYMS:
    if not F.exists_sym(s): continue
    df = F.load_d1(s); c = df["close"].values; cb = F.cost_bp_oneway(s, c)
    for i, p in enumerate(SPEC.params):
        pos = F.tsmom_pos(c, p["L"]); n = F.pnl_bp(pos, c, cb); g = F.pnl_bp(pos, c, np.zeros(len(c)))
        n[:SPEC.warmup + 1] = np.nan; g[:SPEC.warmup + 1] = np.nan
        d = pd.DataFrame({"year": df["year"].values, "sym": s, "param": i, "pnl_net": n, "pnl_gross": g, "time": df["time"].values})
        rows.append(d)
cells = pd.concat(rows)
man = cells.groupby(["param", "sym", "year"])[["pnl_gross", "pnl_net"]].mean().reset_index()
mg = ys.merge(man, on=["param", "sym", "year"], suffixes=("_r", "_m"))
print("銘柄×年 行数", len(ys), len(man), "| bp_net 最大差", float((mg.pnl_net_r - mg.pnl_net_m).abs().max()), "| bp_gross 最大差", float((mg.pnl_gross_r - mg.pnl_gross_m).abs().max()))
c0 = cells[cells.param == 0]
for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, 2017), "post": (2017, 9999)}.items():
    st = F.by_year_stats(c0, "pnl_net", y0=y0, y1=y1)
    pool = c0[(c0.year >= y0) & (c0.year < y1)].groupby("time")["pnl_net"].mean()
    r = res["main"][pn]
    print(pn, "手書き bp", round(st["mean"], 4), "Runner", r["bp_net"], "| t", round(st["t"], 4), r["t_year"], "| sharpe", round(F.sharpe_ann(pool.values), 4), r["sharpe_net"])
print("verdict:", res["machine_verdict"], "| elapsed", res["elapsed_s"], "s | total", round(time.time() - t0, 1), "s")
