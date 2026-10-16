#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q297 の補助（記述・判定には使わない・2026-10-16 実行時に追加）。
本体は UTC 14 時台 → 20 時台に固定しており、夏時間（3〜11 月）は 20 時台＝NY 16〜17 時（引け後）・14 時台＝NY 10〜11 時になる。
ここでは NY 現地時刻（America/New_York）で 初動＝9 時台の足（9:30 の寄りを含む）・終盤＝15 時台の足 にそろえた r を前後半で並べる。
2011-10〜2012-05 の本数不足の月（data_health の gaps）を除いた版も出す。帰無は本体と同じ ret_close の並べ替え B=1000。"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import load_h1, z_of, perm_p, SPLIT_YEAR, fmt
rng = np.random.default_rng(20261010)
out = {}
for sym in ["US500", "USTECH"]:
    df = load_h1(sym); df = df[df["time"] >= "2011-09-01"].copy()
    ny = df["time"].dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    df["nyh"] = ny.dt.hour.values; df["date"] = ny.dt.date.values
    o = df[df["nyh"] == 9][["date", "open", "close", "time"]]; c = df[df["nyh"] == 15][["date", "open", "close"]]
    m = o.merge(c, on="date", suffixes=("_o", "_c"))
    m["ro"] = np.log(m.close_o / m.open_o); m["rc"] = np.log(m.close_c / m.open_c); m["year"] = pd.to_datetime(m["time"]).dt.year
    m["ym"] = pd.to_datetime(m["time"]).dt.strftime("%Y-%m")
    for tag, mm in {"all_rows": m, "drop_2011-10_2012-05": m[~m.ym.between("2011-10", "2012-05")]}.items():
        pre = mm.year < SPLIT_YEAR; post = ~pre
        r = lambda a, b: float(np.corrcoef(a, b)[0, 1])
        rp, rq = r(mm.ro[pre], mm.rc[pre]), r(mm.ro[post], mm.rc[post]); d = rp - rq
        ro, rc = mm.ro.values, mm.rc.values; pr = pre.values
        null = []
        for _ in range(1000):
            x = rng.permutation(rc); null.append(r(ro[pr], x[pr]) - r(ro[~pr], x[~pr]))
        z, _ = z_of(d, null)
        out[f"{sym}_{tag}"] = {"n_pre": int(pre.sum()), "n_post": int(post.sum()), "r_all": fmt(r(mm.ro, mm.rc)), "r_pre": fmt(rp), "r_post": fmt(rq),
                               "delta": fmt(d), "z": fmt(z), "p_right": fmt(perm_p(d, null, side="greater"))}
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
p = os.path.join(HERE, "results", "Q297_sup_ny_local_hours.json"); json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v)
