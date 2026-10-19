#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q320: 手元の標準の判定（年単位 t≥2・日クラスタ t・Holm・年内並べ替え z）は、15 銘柄の順張り損益の
実際の自己相関（ϕ1）と歪度に合わせた合成探索でも名目 5% を守るか（Canli 2026 の Null Zoo を手元へ・Q319-C1）
================================================================================
事前登録の正本は下の SPEC。測る前に固定（2026-10-19・Opus）。

使い方:
  python3 kensho_null_zoo_size_q320.py --calib            （Mac。実データ 15 銘柄 × TSMOM L=5..300 の 60 本の純損益から
                                                           ϕ1・歪度・尖度・残差・ポジションの反転率を results/calib_Q320.npz と
                                                           results/Q320_calib_<日時>.json に書く。fe_core の by_year_stats・cluster_t と
                                                           このスクリプトの一括計算が一致するかの自己点検も行う）
  python3 kensho_null_zoo_size_q320.py --sim --reps 2000 [--part 0/2]   （calib から合成を回す。fe_core は不要）
  python3 kensho_null_zoo_size_q320.py --combine          （parts を束ねて判定し results/Q320_result_<日時>.json）
  --smoke（合成の calib で経路だけ確かめる。判定に使わない）
"""
import argparse
import datetime as _dt
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

SPEC = {
    "qid": "Q320",
    "question": "手元の標準の判定（年単位 t≥2・日クラスタ t・Holm・年内並べ替え z）は、15 銘柄の順張り損益の実際の ϕ1・歪度に合わせた腕なしの合成探索で、名目 5% を守るか",
    "hypothesis": "どれかの判定の 5% 棄却率（サイズ）が名目を明らかに超える（Canli 2026: ϕ=0.2 で自己相関を無視する検定は約 2 割、負の歪度で補正つき t は 7.6% を誤って合格させる）",
    "data": "15 銘柄 D1_fromH1（2008〜2026-06）。TSMOM L=5,10,…,300（60 本）の日次純損益（fe_core.tsmom_pos・pnl_bp・cost_bp_oneway。t>300 から）",
    "synthetic": ("銘柄 s × ルール k ごとに実損益の ϕ1（ラグ 1 の自己相関）を推定し |ϕ1|<0.05 なら 0 に固定。残差 e=(x−m)−ϕ(x_{-1}−m)（m を引くので腕なし）。"
                  "合成は x_t=ϕ x_{t−1}+e*_t。e* は実残差の『日付ごとの 15 銘柄 × 60 本の行』を復元抽出（銘柄間・ルール間の相関と歪度・尖度をそのまま持ち込む。"
                  "その日に無い銘柄の値は、その銘柄の別の日から 1 回だけ埋めて固定）。各銘柄の実際の日付の並び（欠け・BTC の開始）で切る"),
    "judges": {
        "J1_year_t": "ルールごとに年単位 t（年の中で銘柄平均→年の平均。行が 20 未満の年は除く＝fe_core.by_year_stats）で |t|≥2（両側）",
        "J2_cluster_t": "ルールごとに日クラスタ t（日ごとの銘柄平均に Newey-West lag 5＝fe_core.cluster_t）で |t|≥1.96（両側）",
        "J3_holm60": "60 本の J2 の両側正規 p に Holm（α=0.05）。どれか 1 本でも合格する割合（探索全体の誤合格率 FWER）",
        "J4_perm_within_year": ("主ルール L=60 だけ。ポジションを銘柄 × 年の中で並べ替え（fe_core.perm_within と同じ）、年単位平均の帰無を B=199 回。"
                                "perm_p 両側（fe_core.perm_p side='two'）< 0.05。ポジションは実際の L=60 の反転率に合わせた ±1 のマルコフ連鎖、r=s_{-1}·x とおいて損益が x になるようにする"),
    },
    "reject_if": ("支持（手元の判定にサイズの歪みがある）＝J1〜J4 のどれかの棄却率 ≥ 7.5%。棄却（歪みなし）＝4 つすべて ≤ 6.0%（2,000 回の二項の 95% 上限）。ほか未確定。"
                  "J1・J2 はルール 60 本 × 2,000 回の平均、J3 は 2,000 回、J4 は 2,000 回"),
    "reps": 2000, "B_perm": 199, "main_L": 60, "Ls": list(range(5, 301, 5)), "phi_floor": 0.05, "warmup": 300,
    "power": "主ルール L=60 に腕を足す（銘柄ごとに μ_s = c·sd_s。c は束ねた日次平均のシャープが年率 1 になる値）。J1〜J4 と Holm で L=60 が合格する割合（記述）",
    "control": "対照（記述）: 同じ抽出で ϕ=0・日ごとに共通の符号をランダムに掛ける（相関と尖度は残し歪度を 0 に）。J1〜J3 のみ",
    "descriptive": "60 本のうち最良の 1 本が J1・J2 を通る割合（補正なしの探索）、片側（t≥2）の率、ルール別の率の範囲、実データの ϕ1・歪度・尖度",
    "nominal_note": "J1 は年数 ≈18 の t 分布では iid でも |t|≥2 が約 6% になる（閾値の決め方由来）。J4 は B=199・p<0.05 で交換可能なら 4.5%。対照と並べて読む",
    "multiple_comparisons": "判定は 4 つの率（記述の閾値判定。率どうしの多重補正はしない）",
    "prior_art": ("WebSearch 2026-10-19 は Q319 の接続で実施済み（アイデア候補 Q319-C1 の行に『先行研究チェック済み』）。"
                  "Canli 2026 Null Zoo（自己相関・歪度でのサイズ）、Lo 2002（シャープの自己相関補正）。手元の判定・手元の損益の ϕ1/歪度でのサイズは未確認（条件の穴）"),
    "discarded": "約3: ブロック・ブートストラップで実損益を直接リサンプル（ϕ1 と歪度を分けて調べられない）、GARCH の誤差（事前登録は ϕ1・歪度に合わせる）、J4 を 60 本すべてで（計算量が 60 倍）",
    "knowledge_cutoff": "Claude の知識の締め切りはおよそ 2026-06。データは 2008〜2026-06 で締め切り前。合成なので相場観は入らない",
    "delegation": "設計・コード・実行・解釈とも Opus 本体（2026-10-19）。委託なし。一括計算は --calib の自己点検で fe_core と照合",
    "designer": "Opus", "coder": "Opus",
}
SEED = 20261019


# ----------------------------------------------------------------------------- 実データ → 校正
def calib(smoke=False):
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
    import pandas as pd
    from fe_core import SYMS, fmt, health  # noqa: F401
    from fe_core.data import load_d1, syms_available
    from fe_core.costs import cost_bp_oneway, pnl_bp
    from fe_core.signals import tsmom_pos
    from fe_core.metrics import by_year_stats, cluster_t
    rng = np.random.default_rng(SEED)
    syms, missing = syms_available(SYMS, kind="D1_fromH1", smoke=smoke)
    dh = None if smoke else health(syms, kind="H1_dukascopy")
    Ls, W, kmain = SPEC["Ls"], SPEC["warmup"], SPEC["Ls"].index(SPEC["main_L"])
    per = {}
    for s in syms:
        df = load_d1(s, smoke, rng)
        c = df["close"].values; cb = cost_bp_oneway(s, c)
        X = np.full((len(c), len(Ls)), np.nan)
        for k, L in enumerate(Ls):
            pos = tsmom_pos(c, L); X[:, k] = pnl_bp(pos, c, cb)
            if k == kmain:
                pm = pos[W:]
                flip = float(np.mean(pm[1:] != pm[:-1]))
        X[: W + 1] = np.nan
        per[s] = (df["time"].values.astype("datetime64[D]"), df["year"].values, X, flip)
    dates = np.unique(np.concatenate([per[s][0][W + 1:] for s in syms]))
    T, S, K = len(dates), len(syms), len(Ls)
    Xp = np.full((T, S, K), np.nan, np.float64)
    for j, s in enumerate(syms):
        t, _, X, _ = per[s]
        ix = np.searchsorted(dates, t[W + 1:]); Xp[ix, j, :] = X[W + 1:]
    years = dates.astype("datetime64[Y]").astype(int) + 1970
    mask = np.isfinite(Xp[:, :, 0])
    # ϕ1・残差
    phi = np.zeros((S, K)); stats = []
    E = np.full((T, S, K), np.nan)
    for j in range(S):
        v = mask[:, j]
        for k in range(K):
            x = Xp[v, j, k]; m = x.mean(); xc = x - m
            r1 = float((xc[1:] * xc[:-1]).sum() / (xc ** 2).sum())
            ph = r1 if abs(r1) >= SPEC["phi_floor"] else 0.0
            phi[j, k] = ph
            e = xc.copy(); e[1:] = xc[1:] - ph * xc[:-1]
            E[v, j, k] = e
            sd = xc.std(); sk = float((xc ** 3).mean() / sd ** 3); ku = float((xc ** 4).mean() / sd ** 4)
            stats.append({"sym": syms[j], "L": Ls[k], "phi1": r1, "skew": sk, "kurt": ku, "sd_bp": float(sd), "mean_bp": float(m), "n": int(len(x))})
    flips = np.array([per[s][3] for s in syms])
    # 自己点検: 一括計算 vs fe_core
    yt, ct = year_t(Xp, mask, years), cluster_tv(Xp, mask)
    chk = []
    for k in (0, kmain, K - 1):
        rows = []
        for j, s in enumerate(syms):
            v = mask[:, j]
            rows.append(pd.DataFrame({"time": dates[v], "year": years[v], "sym": s, "x": Xp[v, j, k]}))
        d = pd.concat(rows)
        a, b = by_year_stats(d, "x")["t"], cluster_t(d, "x", by="time")["t"]
        chk.append({"L": Ls[k], "year_t_fe": a, "year_t_vec": float(yt[k]), "cl_t_fe": b, "cl_t_vec": float(ct[k])})
    ok = all(abs(c_["year_t_fe"] - c_["year_t_vec"]) < 1e-6 and abs(c_["cl_t_fe"] - c_["cl_t_vec"]) < 1e-6 for c_ in chk)
    os.makedirs(RES, exist_ok=True)
    tag = "smoke_" if smoke else ""
    np.savez_compressed(os.path.join(RES, f"{tag}calib_Q320.npz"), E=E.astype(np.float32), phi=phi, mask=mask, years=years,
                        sd=np.array([[st["sd_bp"] for st in stats[j * K:(j + 1) * K]] for j in range(S)]), flips=flips,
                        syms=np.array(syms), Ls=np.array(Ls), Xp=Xp.astype(np.float32))
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    st = np.array([[d_["phi1"], d_["skew"], d_["kurt"]] for d_ in stats])
    out = {"qid": "Q320", "kind": "calib", "registered_spec": SPEC, "syms": syms, "missing": missing, "data_health": dh,
           "T_union": T, "n_days_by_sym": {s: int(mask[:, j].sum()) for j, s in enumerate(syms)},
           "selfcheck_ok": bool(ok), "selfcheck": chk,
           "real_year_t": {int(L): float(yt[k]) for k, L in enumerate(Ls)}, "real_cluster_t": {int(L): float(ct[k]) for k, L in enumerate(Ls)},
           "phi1_q": dict(zip(["min", "q25", "med", "q75", "max"], np.percentile(st[:, 0], [0, 25, 50, 75, 100]).tolist())),
           "skew_q": dict(zip(["min", "q25", "med", "q75", "max"], np.percentile(st[:, 1], [0, 25, 50, 75, 100]).tolist())),
           "kurt_q": dict(zip(["min", "q25", "med", "q75", "max"], np.percentile(st[:, 2], [0, 25, 50, 75, 100]).tolist())),
           "share_phi_zeroed": float(np.mean(np.abs(st[:, 0]) < SPEC["phi_floor"])),
           "flip_rate_L60": dict(zip(syms, flips.tolist())), "per_sym_rule": stats}
    with open(os.path.join(RES, f"{tag}Q320_calib_{ts}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print("calib T=%d S=%d K=%d selfcheck_ok=%s phi1 med=%.3f skew med=%.2f" % (T, S, K, ok, out["phi1_q"]["med"], out["skew_q"]["med"]))


# ----------------------------------------------------------------------------- 一括の統計（fe_core と同じ定義）
def year_t(X, mask, years, min_rows=20):
    """X: (T,S,K)。by_year_stats と同じ: 年の行数（全銘柄）<20 の年を除き、年×銘柄の平均→年の平均→t。"""
    uy = np.unique(years)
    M = (years[None, :] == uy[:, None]).astype(np.float64)               # (Y,T)
    X0 = np.where(mask[:, :, None], X, 0.0)
    cnt = M @ mask.astype(np.float64)                                    # (Y,S)
    sums = np.einsum("yt,tsk->ysk", M, X0)
    with np.errstate(invalid="ignore", divide="ignore"):
        ys = sums / cnt[:, :, None]
    ys[cnt == 0] = np.nan
    keep = cnt.sum(1) >= min_rows
    ym = np.nanmean(ys[keep], axis=1)                                     # (Y',K)
    n = ym.shape[0]
    return ym.mean(0) / (ym.std(0, ddof=1) / math.sqrt(n))


def cluster_tv(X, mask, lag=5):
    X0 = np.where(mask[:, :, None], X, 0.0)
    c = mask.sum(1).astype(np.float64)
    v = c > 0
    dm = X0[v].sum(1) / c[v][:, None]                                     # (T',K)
    n = dm.shape[0]; e = dm - dm.mean(0)
    s = (e ** 2).sum(0)
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] * e[:-k]).sum(0)
    return dm.mean(0) / (np.sqrt(s) / n)


def norm_p2(t):
    return np.array([math.erfc(abs(x) / math.sqrt(2)) for x in np.atleast_1d(t)])


def holm_any(p, alpha=0.05):
    ps = np.sort(p); m = len(p)
    return bool(ps[0] <= alpha / m)


def holm_reject_k(p, k, alpha=0.05):
    order = np.argsort(p, kind="stable"); m = len(p)
    for i, j in enumerate(order):
        if p[j] > alpha / (m - i):
            return False
        if j == k:
            return True
    return False


# ----------------------------------------------------------------------------- 合成
def sim(reps, part, nparts, smoke=False):
    tag = "smoke_" if smoke else ""
    z = np.load(os.path.join(RES, f"{tag}calib_Q320.npz"), allow_pickle=False)
    E, phi, mask, years, sd, flips = z["E"].astype(np.float64), z["phi"], z["mask"], z["years"], z["sd"], z["flips"]
    Ls = list(z["Ls"]); kmain = Ls.index(SPEC["main_L"])
    T, S, K = E.shape
    rng0 = np.random.default_rng(SEED)
    # 抽出の母集団: 8 銘柄以上がそろう日。欠けた銘柄は自分の別の日から 1 回だけ埋めて固定
    pool = np.where(mask.sum(1) >= 8)[0]
    P = E[pool].copy()
    for j in range(S):
        own = np.where(mask[:, j])[0]
        miss = ~np.isfinite(P[:, j, 0])
        P[miss, j, :] = E[rng0.choice(own, miss.sum()), j, :]
    # 腕の大きさ: 束ねた日次平均のシャープが年率 1
    Xr = z["Xp"].astype(np.float64)[:, :, kmain]
    X0 = np.where(mask, Xr - np.nanmean(Xr, 0), 0.0); c = mask.sum(1)
    sd_pool = (X0[c > 0].sum(1) / c[c > 0]).std()
    sdm = sd[:, kmain]
    # 銘柄ごとの平均 sd（その日にいる銘柄で）
    avg_sd = float((mask * sdm[None, :]).sum(1)[c > 0].mean() / c[c > 0].mean())
    cc = (sd_pool / math.sqrt(252)) / avg_sd
    mu = cc * sdm                                                           # (S,)
    # 年内並べ替えの準備（主ルール）: 有効セルを (銘柄, 年) の順に並べる
    cells = np.argwhere(mask)                                               # (N,2) t,s
    gid = cells[:, 1] * 10000 + years[cells[:, 0]]
    o = np.lexsort((cells[:, 0], gid)); cells, gid = cells[o], gid[o]
    ug, start, gcount = np.unique(gid, return_index=True, return_counts=True)
    g_sym = ug // 10000; g_year = ug % 10000
    uy = np.unique(years)
    yrows = np.array([mask[years == y].sum() for y in uy])
    keep_years = uy[yrows >= 20]
    B = 199 if not smoke else 19
    seeds = np.random.SeedSequence(SEED + 1).spawn(nparts)[part]
    rng = np.random.default_rng(seeds)

    rec = {k: [] for k in ["J1", "J2", "J3", "J4", "J4z", "J1_up", "best_J1", "best_J2",
                           "C1", "C2", "C3", "P1", "P2", "P3", "P4"]}
    J1_by_k = np.zeros(K); J2_by_k = np.zeros(K)
    my_reps = [r for r in range(reps) if r % nparts == part]
    for r in my_reps:
        idx = rng.integers(0, len(pool), T)
        e = P[idx]                                                           # (T,S,K)
        sign = rng.choice([-1.0, 1.0], T)
        x = np.empty_like(e); x[0] = e[0]
        for t in range(1, T):
            x[t] = phi * x[t - 1] + e[t]
        xc = e * sign[:, None, None]                                          # 対照
        res = {}
        for name, X in (("m", x), ("c", xc)):
            yt = year_t(X, mask, years); ct = cluster_tv(X, mask)
            p = norm_p2(ct)
            res[name] = (yt, ct, p)
        yt, ct, p = res["m"]
        rec["J1"].append(float(np.mean(np.abs(yt) >= 2))); rec["J2"].append(float(np.mean(np.abs(ct) >= 1.96)))
        rec["J1_up"].append(float(np.mean(yt >= 2)))
        J1_by_k += np.abs(yt) >= 2; J2_by_k += np.abs(ct) >= 1.96
        rec["J3"].append(float(holm_any(p)))
        rec["best_J1"].append(float(np.max(np.abs(yt)) >= 2)); rec["best_J2"].append(float(np.max(np.abs(ct)) >= 1.96))
        yc, cc_, pc = res["c"]
        rec["C1"].append(float(np.mean(np.abs(yc) >= 2))); rec["C2"].append(float(np.mean(np.abs(cc_) >= 1.96))); rec["C3"].append(float(holm_any(pc)))
        # 腕（主ルールだけ）
        xa = x.copy(); xa[:, :, kmain] += mu[None, :]
        ya, ca = year_t(xa[:, :, kmain:kmain + 1], mask, years)[0], cluster_tv(xa[:, :, kmain:kmain + 1], mask)[0]
        pa = p.copy(); pa[kmain] = norm_p2(ca)[0]
        rec["P1"].append(float(ya >= 2)); rec["P2"].append(float(ca >= 1.96)); rec["P3"].append(float(holm_reject_k(pa, kmain)))
        # J4: ポジション ±1 のマルコフ連鎖（反転率は実際の L=60）
        sp = np.empty((T, S)); sp[0] = rng.choice([-1.0, 1.0], S)
        fl = rng.random((T, S)) < flips[None, :]
        for t in range(1, T):
            sp[t] = np.where(fl[t], -sp[t - 1], sp[t - 1])
        slag = sp[cells[:, 0], cells[:, 1]]
        xm = x[cells[:, 0], cells[:, 1], kmain]; xa_m = xa[cells[:, 0], cells[:, 1], kmain]
        ret = slag * xm; ret_a = slag * xa_m
        u = gid[None, :] + rng.random((B, len(gid)))
        order = np.argsort(u, axis=1)
        perm = slag[order]
        for nm, rr in (("J4", ret), ("P4", ret_a)):
            obs_g = np.add.reduceat(slag * rr, start) / gcount
            null_g = np.add.reduceat(perm * rr[None, :], start, axis=1) / gcount
            obs = yearmean_from_groups_scalar(obs_g, g_year, keep_years)
            nul = yearmean_from_groups_scalar(null_g, g_year, keep_years)
            cen = nul.mean(); k_ = int((np.abs(nul - cen) >= abs(obs - cen)).sum()); pp = (1 + k_) / (B + 1)
            if nm == "J4":
                rec["J4"].append(float(pp < 0.05)); zz = (obs - cen) / nul.std(ddof=1); rec["J4z"].append(float(abs(zz) >= 1.96))
            else:
                rec["P4"].append(float(pp < 0.05 and obs > cen))
        if (len(rec["J1"]) % 50) == 0:
            print(f"part {part}: {len(rec['J1'])}/{len(my_reps)}", flush=True)
    os.makedirs(os.path.join(RES, "parts"), exist_ok=True)
    out = {"part": part, "nparts": nparts, "n": len(my_reps), "B_perm": B, "rec": rec,
           "J1_by_k": J1_by_k.tolist(), "J2_by_k": J2_by_k.tolist(), "arm_c": cc, "Ls": [int(L) for L in Ls]}
    with open(os.path.join(RES, "parts", f"{tag}Q320_part{part}of{nparts}.json"), "w") as fh:
        json.dump(out, fh)
    print("wrote part", part)


def yearmean_from_groups_scalar(gm, g_year, keep_years):
    """gm: (..., G) の年×銘柄の平均 → 年ごとに銘柄平均 → 年の平均（by_year_stats の mean と同じ）。"""
    ys = [gm[..., g_year == y].mean(-1) for y in keep_years]
    return np.stack(ys, -1).mean(-1)


# ----------------------------------------------------------------------------- 束ねて判定
def combine(smoke=False):
    tag = "smoke_" if smoke else ""
    parts = sorted(glob.glob(os.path.join(RES, "parts", f"{tag}Q320_part*of*.json")))
    if not smoke:
        parts = [p for p in parts if "smoke_" not in os.path.basename(p)]
    D = [json.load(open(p)) for p in parts]
    rec = {k: sum((d["rec"][k] for d in D), []) for k in D[0]["rec"]}
    n = len(rec["J1"])
    rate = {k: float(np.mean(v)) for k, v in rec.items()}
    Jk1 = np.sum([d["J1_by_k"] for d in D], 0) / n; Jk2 = np.sum([d["J2_by_k"] for d in D], 0) / n
    ub = 0.05 + 1.96 * math.sqrt(0.05 * 0.95 / n)
    four = {"J1_year_t": rate["J1"], "J2_cluster_t": rate["J2"], "J3_holm60": rate["J3"], "J4_perm_within_year": rate["J4"]}
    if max(four.values()) >= 0.075:
        v = "支持: " + "・".join(f"{k}={x:.1%}" for k, x in four.items() if x >= 0.075) + " が 7.5% 以上"
    elif max(four.values()) <= 0.060:
        v = "棄却: 4 つすべて 6.0% 以下"
    else:
        v = "未確定: 最大 " + max(four, key=four.get) + f"={max(four.values()):.1%}（6.0〜7.5%）"
    calibs = sorted(glob.glob(os.path.join(RES, f"{tag}Q320_calib_*.json")))
    cal = json.load(open(calibs[-1])) if calibs else {}
    out = {"qid": "Q320", "question": SPEC["question"], "spec": SPEC, "n_reps": n, "binom_upper95": ub,
           "machine_verdict": v, "size": four,
           "size_detail": {"J1_one_sided_t_ge_2": rate["J1_up"], "J4_abs_z_ge_1.96": rate["J4z"],
                           "best_of_60_J1": rate["best_J1"], "best_of_60_J2": rate["best_J2"],
                           "J1_range_over_L": [float(Jk1.min()), float(Jk1.max())], "J2_range_over_L": [float(Jk2.min()), float(Jk2.max())],
                           "J1_by_L": dict(zip(D[0]["Ls"], Jk1.tolist())), "J2_by_L": dict(zip(D[0]["Ls"], Jk2.tolist()))},
           "control_phi0_sym": {"J1": rate["C1"], "J2": rate["C2"], "J3": rate["C3"]},
           "power_L60_sharpe1": {"J1_t_ge_2": rate["P1"], "J2_t_ge_1.96": rate["P2"], "J3_holm": rate["P3"], "J4_perm": rate["P4"], "arm_c": D[0]["arm_c"]},
           "calib_ref": os.path.basename(calibs[-1]) if calibs else None,
           "calib_summary": {k: cal.get(k) for k in ["phi1_q", "skew_q", "kurt_q", "share_phi_zeroed", "n_days_by_sym", "selfcheck_ok", "flip_rate_L60", "data_health", "missing"]},
           "parts": [os.path.basename(p) for p in parts]}
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RES, f"{tag}Q320_result_{ts}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("machine_verdict:", v); print(json.dumps({"size": four, "control": out["control_phi0_sym"], "power": out["power_L60_sharpe1"], "detail": {k: out["size_detail"][k] for k in ["J1_one_sided_t_ge_2", "J4_abs_z_ge_1.96", "best_of_60_J1", "best_of_60_J2", "J1_range_over_L", "J2_range_over_L"]}}, ensure_ascii=False, indent=1))
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", action="store_true"); ap.add_argument("--sim", action="store_true"); ap.add_argument("--combine", action="store_true")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--reps", type=int, default=SPEC["reps"])
    ap.add_argument("--part", default="0/1")
    a = ap.parse_args()
    os.makedirs(RES, exist_ok=True)
    if a.calib:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(RES, f"{'smoke_' if a.smoke else ''}Q320_spec_{ts}.json"), "w", encoding="utf-8") as fh:
            json.dump({"registered": ts, "seed": SEED, **SPEC}, fh, ensure_ascii=False, indent=1)
        calib(a.smoke)
    if a.sim:
        p, n = map(int, a.part.split("/")); sim(a.reps, p, n, a.smoke)
    if a.combine:
        combine(a.smoke)


if __name__ == "__main__":
    main()
