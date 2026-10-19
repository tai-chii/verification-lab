#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q320 事後の診断（記述・判定には使わない。本体の実行後 2026-10-19 に追加）。
J4（年内並べ替え）の 16% の原因を分ける: 主ルール L=60 だけで 3 通りの合成を回す。
  A 本体と同じ（日付を 15 銘柄で共通に抽出・ϕ は推定値）
  B 銘柄ごとに別の日付を抽出（銘柄間の相関を消す）・ϕ は推定値
  C 日付は共通・ϕ=0・日ごとの共通符号（歪度 0、相関は残す）
使い方: python3 q320_j4_diag.py --reps 300
"""
import argparse, json, os, datetime as _dt
import numpy as np
import kensho_null_zoo_size_q320 as M

ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=300); a = ap.parse_args()
z = np.load(os.path.join(M.RES, "calib_Q320.npz"))
E, phi, mask, years, flips = z["E"].astype(float), z["phi"], z["mask"], z["years"], z["flips"]
k0 = list(z["Ls"]).index(60); E = E[:, :, k0]; phi = phi[:, k0]
T, S = E.shape
rng0 = np.random.default_rng(M.SEED)
pool = np.where(mask.sum(1) >= 8)[0]; P = E[pool].copy()
for j in range(S):
    own = np.where(mask[:, j])[0]; miss = ~np.isfinite(P[:, j])
    P[miss, j] = E[rng0.choice(own, miss.sum()), j]
cells = np.argwhere(mask); gid = cells[:, 1] * 10000 + years[cells[:, 0]]
o = np.lexsort((cells[:, 0], gid)); cells, gid = cells[o], gid[o]
ug, start, gcount = np.unique(gid, return_index=True, return_counts=True); g_year = ug % 10000
uy = np.unique(years); keep = uy[np.array([mask[years == y].sum() for y in uy]) >= 20]
B = 199; rng = np.random.default_rng(M.SEED + 7)
rej = {"A": [], "B": [], "C": []}
for r in range(a.reps):
    sp = np.empty((T, S)); sp[0] = rng.choice([-1.0, 1.0], S); fl = rng.random((T, S)) < flips[None, :]
    for t in range(1, T):
        sp[t] = np.where(fl[t], -sp[t - 1], sp[t - 1])
    slag = sp[cells[:, 0], cells[:, 1]]
    order = np.argsort(gid[None, :] + rng.random((B, len(gid))), axis=1); perm = slag[order]
    idx = rng.integers(0, len(pool), T)
    eA = P[idx]
    eB = np.stack([P[rng.integers(0, len(pool), T), j] for j in range(S)], 1)
    eC = P[idx] * rng.choice([-1.0, 1.0], T)[:, None]
    for nm, e, ph in (("A", eA, phi), ("B", eB, phi), ("C", eC, np.zeros(S))):
        x = np.empty_like(e); x[0] = e[0]
        for t in range(1, T):
            x[t] = ph * x[t - 1] + e[t]
        rr = slag * x[cells[:, 0], cells[:, 1]]
        obs = M.yearmean_from_groups_scalar(np.add.reduceat(slag * rr, start) / gcount, g_year, keep)
        nul = M.yearmean_from_groups_scalar(np.add.reduceat(perm * rr[None, :], start, axis=1) / gcount, g_year, keep)
        cen = nul.mean(); k_ = int((np.abs(nul - cen) >= abs(obs - cen)).sum())
        rej[nm].append((1 + k_) / (B + 1) < 0.05)
out = {"note": "事後の診断（記述）", "reps": a.reps, "B": B, "J4_rate": {k: float(np.mean(v)) for k, v in rej.items()},
       "variants": {"A": "本体と同じ", "B": "銘柄ごとに別の日付（相関なし）", "C": "相関あり・ϕ=0・歪度0"}}
ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
json.dump(out, open(os.path.join(M.RES, f"Q320_j4diag_{ts}.json"), "w"), ensure_ascii=False, indent=1)
print(out)
