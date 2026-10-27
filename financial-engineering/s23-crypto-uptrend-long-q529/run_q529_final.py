# -*- coding: utf-8 -*-
"""Q529 最終 1 年（2025-10〜2026-09）を 1 回だけ開ける。規則は run_q529 の主のまま。"""
import json, sys
import numpy as np, pandas as pd
import run_q529 as R, crypto_core as C
R.S0, R.SEAL = R.T("2025-10-01"), R.T("2026-10-01")
h1, out = sys.argv[1], sys.argv[2]
bs = {c: R.daily_series(h1, c) for c in ["BTC", "ETH"]}
for c in bs:
    bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
m = lambda c: (bs[c].index >= R.S0.tz_convert(None)) & (bs[c].index < R.SEAL.tz_convert(None))
res = {}
bh = R.combine([R.backtest(bs[c], np.ones(len(bs[c])), R.HALF[c]) for c in bs]); res["buy_hold"] = R.stats(bh, "買って持つ")
pos = {c: R.tsmom(bs[c], 60) for c in bs}
mp = R.combine([R.backtest(bs[c], pos[c], R.HALF[c]) for c in bs]); res["main"] = R.stats(mp, "TSMOM60")
res["main"]["in_market"] = {c: float(pos[c][m(c)].mean()) for c in bs}
res["main"]["n_switch"] = {c: int(np.abs(np.diff(pos[c][m(c)])).sum()) for c in bs}
res["main"]["by_coin"] = {c: R.stats(R.backtest(bs[c], pos[c], R.HALF[c]), c) for c in bs}
res["bh_by_coin"] = {c: R.stats(R.backtest(bs[c], np.ones(len(bs[c])), R.HALF[c]), c) for c in bs}
null = R.circ_null(bs, pos); res["main"]["null_z"] = float((res["main"]["sharpe"] - null.mean()) / null.std(ddof=1)); res["main"]["null_mean"] = float(null.mean())
sel = lambda p: p[(p.index >= R.S0.tz_convert(None)) & (p.index < R.SEAL.tz_convert(None))]
mon = pd.DataFrame({"main": sel(mp), "bh": sel(bh)}); mon.index = pd.DatetimeIndex(mon.index)
res["monthly"] = mon.groupby(mon.index.to_period("M")).apply(lambda x: (1 + x).prod() - 1).round(4).astype(float).rename(index=str).to_dict("index")
crit = dict(sharpe_gt_bh=res["main"]["sharpe"] > res["buy_hold"]["sharpe"], dd_shallower=res["main"]["max_dd"] > res["buy_hold"]["max_dd"])
res["criteria"] = crit; res["verdict"] = "合格" if all(crit.values()) else "不合格"
json.dump(res, open(f"{out}/result_q529_final.json", "w"), ensure_ascii=False, indent=1, default=str)
mon.to_csv(f"{out}/daily_q529_final.csv")
for k in ["buy_hold", "main"]:
    r = res[k]; print(f"{r['label']:<10} シャープ {r['sharpe']:.2f} 最大下落 {r['max_dd']*100:.1f}% 通算 {r['total']*100:.1f}% t {r['t']:.2f}")
print(json.dumps({k: res["main"][k] for k in ["in_market", "n_switch", "null_z", "null_mean"]}, ensure_ascii=False))
for c in bs: print(c, "TSMOM", {k: round(res['main']['by_coin'][c][k], 3) for k in ['sharpe', 'max_dd', 'total']}, "BH", {k: round(res['bh_by_coin'][c][k], 3) for k in ['sharpe', 'max_dd', 'total']})
for k, v in res["monthly"].items(): print(k, f"{v['main']*100:+.1f}%  BH {v['bh']*100:+.1f}%")
print(crit, res["verdict"])
