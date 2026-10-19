#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q321: 複数銘柄を束ねた年内並べ替えを「銘柄 × 年ごとに別々」ではなく「年の中で日付を全銘柄共通に並べ替える」に
すると、腕なしの合成で 5% 棄却率（サイズ）が名目に戻るか（Q320 の次段階）
================================================================================
事前登録の正本は下の SPEC。測る前に固定（2026-10-19・Opus）。

Q320 の合成からの作り直しの理由（測る前に書く）:
  Q320 の J4 は「ポジション ±1 を銘柄ごとに独立のマルコフ連鎖で作り、損益 x（銘柄間で相関あり）を r=s·x で戻す」形。
  この世界ではポジションが銘柄間で無相関なのに損益だけが相関している。帰無の並べ替え統計 Σ s_perm·s·x の銘柄間の
  交差項は E[a_s a_s']=0（a_s=s_perm·s は銘柄間で独立）で消えるので、日付を共通に並べ替えても交差項は戻らない
  （共通並べ替えが効く余地が無い）。現実の帰無（ポジションも収益も銘柄間で相関し、両者は独立）では、損益の銘柄間の
  相関は「ポジションの相関 × 収益の相関」から生まれ、日付共通の並べ替えはポジションの横の並びを保つので交差項を残す。
  そこで本体（判定）は現実型の帰無 M で測り、Q320 型の世界 V は記述として並べる。

使い方:
  python3 kensho_common_perm_size_q321.py --calib     （Mac。実データ 15 銘柄の日次収益 r[bp] と TSMOM L=60 の保有ポジションを
                                                        results/calib_Q321.npz に書く。実データでの J4a・J4b の p も記述として出す）
  python3 kensho_common_perm_size_q321.py --sim --reps 2000 --part 0/4
  python3 kensho_common_perm_size_q321.py --combine
  --smoke（合成データで経路だけ確かめる。判定に使わない）
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
    "qid": "Q321",
    "question": "束ねた年内並べ替えを全銘柄共通の（日付の）並べ替えにすると、腕なしの合成でサイズが名目 5% に戻るか",
    "hypothesis": "銘柄 × 年ごとに別々の並べ替え（J4a, fe_core.perm_within に sym×year を渡す形）は銘柄間の相関を壊して帰無の分散を過小に見積もりサイズが膨らむ（Q320: 16.4%）。年の中で日付を全銘柄共通に並べ替える（J4b）と横の相関が残り名目に戻る",
    "data": "15 銘柄 D1_fromH1（2008〜2026-06）。日次収益 r[bp]=close の比×1e4（gap 行は残す＝Q320 と同じ）。ポジションは TSMOM L=60（fe_core.tsmom_pos）の保有（1 本ずらし）。各銘柄 t>300 から（Q320 と同じ）。コストは入れない（帰無のサイズだけを見る）",
    "null_M_main": ("現実型の帰無（判定に使う）: 収益は銘柄ごとに平均を引いた実収益の『日付ごとの 15 銘柄の行』を定常ブートストラップ（平均ブロック 20 日、"
                    "8 銘柄以上がそろう日から。欠けた銘柄はその銘柄の別の日から 1 回だけ埋めて固定）。ポジションは実際の L=60 の保有行列（和集合の暦で前埋め・先頭は後埋め）を"
                    "全銘柄共通に循環シフト（k〜一様[252, T−252]）。収益とポジションは独立＝腕なし。銘柄間の相関はポジション・収益の両方に実データのまま残る。損益=保有×収益を各銘柄の実際の日付で切る"),
    "null_V_desc": "Q320 型の世界（記述）: 収益の行は M と同じ抽出、ポジションは銘柄ごとに別の k で循環シフト（横の相関なし）、損益=抽出した行そのもの（r=s·e と戻す）。共通並べ替えでも直らない見込み",
    "judges": {
        "J4a_perm_sym_year": "ポジションを銘柄 × 年の中で並べ替え（fe_core.perm_within と同じ）。統計は年単位平均（年×銘柄の平均→年の中で銘柄平均→年の平均。行が 20 未満の年は除く）。B=199、両側 perm_p<0.05（fe_core.perm_p side='two'）",
        "J4b_perm_common_date": "年の中で日付を 1 つの並べ替え π で並べ替え、全銘柄のポジションの行を一緒に動かす（保有[π(t), :]）。統計・B・p は J4a と同じ",
        "J1_year_t": "参考（記述）: 損益の年単位 t で |t|≥2",
        "J2_cluster_t": "参考（記述）: 日クラスタ t（NW lag5）で |t|≥1.96",
    },
    "reject_if": ("M での J4b の棄却率で判定。回復（支持）＝J4b ≤ 6.0%（2,000 回の二項の 95% 上限）。未回復（棄却）＝J4b ≥ 7.5%。ほか未確定。"
                  "付記（事前に決めた読み方）: M で J4a ≤ 6.0% なら、Q320 の J4 16% は『ポジション無相関・損益相関』という合成の作り由来で、"
                  "現実型の帰無では銘柄別の並べ替えも膨らまない（このとき J4b の判定は『回復』でも差の意味は小さいと書く）"),
    "reps": 2000, "B_perm": 199, "L": 60, "warmup": 300, "mean_block": 20, "shift_min": 252,
    "descriptive": "V の J4a・J4b、M・V の J1・J2、M・V の J4a と J4b の帰無 sd の比、実データでの J4a・J4b の p（B=999・コストなし。判定に使わない）、ポジション・収益の銘柄間の平均相関",
    "multiple_comparisons": "判定は M の J4b の率 1 つ",
    "prior_art": "Q320 の続き（Q319 の接続で先行研究チェック済み）。共通の日付の並べ替えで横の相関を保つのは、Romano-Wolf 型の同時ブートストラップ・パネルの時点ごとの再標本化と同じ考え。手元の判定での測定は未",
    "discarded": "約2: 銘柄ごとに別の並べ替えのまま帰無 sd を相関で割り増す補正（手元の運用から離れる）、ブロック並べ替え（年内並べ替えの置き換えは別の問い）",
    "knowledge_cutoff": "Claude の知識の締め切りはおよそ 2026-06。データは 2008〜2026-06。合成なので相場観は入らない",
    "delegation": "設計・コード・実行・解釈とも Opus 本体（2026-10-19）。委託なし",
    "designer": "Opus", "coder": "Opus",
}
SEED = 20261021


# ----------------------------------------------------------------------------- 実データ → 校正
def calib(smoke=False):
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
    from fe_core import SYMS, health
    from fe_core.data import load_d1, syms_available
    from fe_core.signals import tsmom_pos
    rng = np.random.default_rng(SEED)
    syms, missing = syms_available(SYMS, kind="D1_fromH1", smoke=smoke)
    dh = None if smoke else health(syms, kind="H1_dukascopy")
    W, L = SPEC["warmup"], SPEC["L"]
    per = {}
    for s in syms:
        df = load_d1(s, smoke, rng)
        c = df["close"].values.astype(float)
        r = np.r_[np.nan, c[1:] / c[:-1] - 1] * 1e4
        pos = tsmom_pos(c, L); held = np.r_[0.0, pos[:-1]]
        t = df["time"].values.astype("datetime64[D]")
        per[s] = (t[W + 1:], r[W + 1:], held[W + 1:])
    dates = np.unique(np.concatenate([per[s][0] for s in syms]))
    T, S = len(dates), len(syms)
    R = np.full((T, S), np.nan); H = np.full((T, S), np.nan)
    for j, s in enumerate(syms):
        t, r, h = per[s]; ix = np.searchsorted(dates, t); R[ix, j] = r; H[ix, j] = h
    years = dates.astype("datetime64[Y]").astype(int) + 1970
    mask = np.isfinite(R) & np.isfinite(H)
    os.makedirs(RES, exist_ok=True)
    tag = "smoke_" if smoke else ""
    np.savez_compressed(os.path.join(RES, f"{tag}calib_Q321.npz"), R=R, H=H, mask=mask, years=years, syms=np.array(syms),
                        dates=dates.astype(str))
    # 記述: 実データでの J4a・J4b（コストなし・B=999）
    pre = prep(mask, years)
    Hff = ffill_bfill(H)
    rngr = np.random.default_rng(SEED + 99)
    real = {}
    cells = pre["cells"]
    rr = R[cells[:, 0], cells[:, 1]]; hh = H[cells[:, 0], cells[:, 1]]
    for nm, fn in (("J4a", null_sym_year), ("J4b", null_common_date)):
        obs, nul = stat_obs_null(pre, hh, rr, Hff, rngr, 999, fn)
        cen = nul.mean(); k_ = int((np.abs(nul - cen) >= abs(obs - cen)).sum())
        real[nm] = {"obs_bp_per_day": float(obs), "null_mean": float(cen), "null_sd": float(nul.std(ddof=1)),
                    "z": float((obs - cen) / nul.std(ddof=1)), "p_two": (1 + k_) / 1000}
    out = {"qid": "Q321", "kind": "calib", "registered_spec": SPEC, "syms": syms, "missing": missing, "data_health": dh,
           "T_union": T, "n_days_by_sym": {s: int(mask[:, j].sum()) for j, s in enumerate(syms)},
           "mean_pairwise_corr": {"position": mean_pair_corr(H), "return": mean_pair_corr(R), "pnl": mean_pair_corr(H * R)},
           "real_L60_nocost_descriptive": real}
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(RES, f"{tag}Q321_calib_{ts}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: out[k] for k in ["T_union", "mean_pairwise_corr", "real_L60_nocost_descriptive"]}, ensure_ascii=False, indent=1))


def mean_pair_corr(X):
    import pandas as pd
    c = pd.DataFrame(X).corr(min_periods=250).values
    iu = np.triu_indices_from(c, 1)
    return float(np.nanmean(c[iu]))


def ffill_bfill(H):
    import pandas as pd
    return pd.DataFrame(H).ffill().bfill().values


# ----------------------------------------------------------------------------- 並べ替えの準備と統計
def prep(mask, years, min_rows=20):
    cells = np.argwhere(mask)                                               # (N,2) t,s
    gid = cells[:, 1] * 10000 + years[cells[:, 0]]
    o = np.lexsort((cells[:, 0], gid)); cells, gid = cells[o], gid[o]
    ug, start, gcount = np.unique(gid, return_index=True, return_counts=True)
    uy = np.unique(years)
    yrows = np.array([mask[years == y].sum() for y in uy])
    keep = uy[yrows >= min_rows]
    g_year = ug % 10000
    gsel = [np.where(g_year == y)[0] for y in keep]
    return {"cells": cells, "gid": gid, "start": start, "gcount": gcount, "gsel": gsel, "years": years, "T": len(years)}


def yearmean(pre, v):
    """v: (..., N) のセル値 → 年×銘柄の平均 → 年の中で銘柄平均 → 年の平均（Q320 の yearmean_from_groups_scalar と同じ）"""
    gm = np.add.reduceat(v, pre["start"], axis=-1) / pre["gcount"]
    return np.stack([gm[..., g].mean(-1) for g in pre["gsel"]], -1).mean(-1)


def null_sym_year(pre, Hfull, hh, rng, B):
    """J4a: 銘柄 × 年の中で実セルのポジションを並べ替え（fe_core.perm_within と同じ）"""
    u = pre["gid"][None, :] + rng.random((B, len(pre["gid"])))
    return hh[np.argsort(u, axis=1)]


def null_common_date(pre, Hfull, hh, rng, B):
    """J4b: 年の中で日付を 1 つの並べ替え π で並べ替え、全銘柄の保有の行を一緒に動かす。
    years は昇順（dates が昇順）なので argsort(years + 一様乱数) の各位置 t は同じ年の別の日付を指す"""
    yrs = pre["years"].astype(np.float64)
    pi = np.argsort(yrs[None, :] + rng.random((B, len(yrs))), axis=1)    # (B,T)
    ct, cs = pre["cells"][:, 0], pre["cells"][:, 1]
    return Hfull[pi[:, ct], cs[None, :]]


def stat_obs_null(pre, hh, rr, Hfull, rng, B, fn):
    obs = yearmean(pre, hh * rr)
    hp = fn(pre, Hfull, hh, rng, B)
    nul = yearmean(pre, hp * rr[None, :])
    return float(obs), nul


def perm_p_two(obs, nul):
    cen = nul.mean(); k_ = int((np.abs(nul - cen) >= abs(obs - cen)).sum())
    return (1 + k_) / (len(nul) + 1)


# ----------------------------------------------------------------------------- 合成
def sim(reps, part, nparts, smoke=False):
    sys.path.insert(0, os.path.join(HERE, "..", "null-zoo-size-q320"))
    from kensho_null_zoo_size_q320 import year_t, cluster_tv
    tag = "smoke_" if smoke else ""
    z = np.load(os.path.join(RES, f"{tag}calib_Q321.npz"), allow_pickle=False)
    R, H, mask, years = z["R"], z["H"], z["mask"], z["years"]
    T, S = R.shape
    rng0 = np.random.default_rng(SEED)
    Rd = R - np.nanmean(np.where(mask, R, np.nan), 0)                        # 腕なし: 銘柄ごとの平均を引く
    pool = np.where(mask.sum(1) >= 8)[0]
    P = Rd[pool].copy()
    for j in range(S):
        own = np.where(mask[:, j])[0]; miss = ~np.isfinite(P[:, j])
        P[miss, j] = Rd[rng0.choice(own, miss.sum()), j]
    Hff = ffill_bfill(np.where(mask, H, np.nan))
    pre = prep(mask, years)
    ct, cs = pre["cells"][:, 0], pre["cells"][:, 1]
    B = SPEC["B_perm"] if not smoke else 19
    pcont = 1 - 1 / SPEC["mean_block"]; npool = len(pool); smin = SPEC["shift_min"]
    rng = np.random.default_rng(np.random.SeedSequence(SEED + 1).spawn(nparts)[part])
    keys = ["M_J4a", "M_J4b", "M_J1", "M_J2", "V_J4a", "V_J4b", "V_J1", "V_J2", "M_sdratio", "V_sdratio", "M_J4a_z", "M_J4b_z"]
    rec = {k: [] for k in keys}
    my = [r for r in range(reps) if r % nparts == part]
    for i, r in enumerate(my):
        # 収益の行: 定常ブートストラップ
        idx = np.empty(T, int); idx[0] = rng.integers(npool)
        cont = rng.random(T) < pcont; jump = rng.integers(0, npool, T)
        for t in range(1, T):
            idx[t] = (idx[t - 1] + 1) % npool if cont[t] else jump[t]
        e = P[idx]                                                           # (T,S)
        rr = e[ct, cs]
        # M: 全銘柄共通のシフト
        k = int(rng.integers(smin, T - smin)); HM = np.roll(Hff, k, axis=0)
        # V: 銘柄ごとに別のシフト。損益は抽出した行そのもの（r=s·e）
        HV = np.stack([np.roll(Hff[:, j], int(rng.integers(smin, T - smin))) for j in range(S)], 1)
        for w, Hs, pnl_cells, rcell in (("M", HM, None, None), ("V", HV, rr, None)):
            hh = Hs[ct, cs]
            r_use = rr if w == "M" else hh * rr                              # V: r=s·e → 損益 = s·r = e
            sds = {}
            for nm, fn in (("J4a", null_sym_year), ("J4b", null_common_date)):
                obs, nul = stat_obs_null(pre, hh, r_use, Hs, rng, B, fn)
                rec[f"{w}_{nm}"].append(float(perm_p_two(obs, nul) < 0.05)); sds[nm] = nul.std(ddof=1)
                if w == "M":
                    rec[f"M_{nm}_z"].append(float(abs((obs - nul.mean()) / sds[nm]) >= 1.96))
            rec[f"{w}_sdratio"].append(float(sds["J4b"] / sds["J4a"]))
            X = np.full((T, S, 1), 0.0); X[ct, cs, 0] = hh * r_use
            rec[f"{w}_J1"].append(float(abs(year_t(X, mask, years)[0]) >= 2))
            rec[f"{w}_J2"].append(float(abs(cluster_tv(X, mask)[0]) >= 1.96))
        if (i + 1) % 50 == 0:
            print(f"part {part}: {i + 1}/{len(my)}", flush=True)
    os.makedirs(os.path.join(RES, "parts"), exist_ok=True)
    with open(os.path.join(RES, "parts", f"{tag}Q321_part{part}of{nparts}.json"), "w") as fh:
        json.dump({"part": part, "nparts": nparts, "n": len(my), "B_perm": B, "rec": rec}, fh)
    print("wrote part", part)


# ----------------------------------------------------------------------------- 束ねて判定
def combine(smoke=False):
    tag = "smoke_" if smoke else ""
    parts = sorted(glob.glob(os.path.join(RES, "parts", f"{tag}Q321_part*of*.json")))
    if not smoke:
        parts = [p for p in parts if "smoke_" not in os.path.basename(p)]
    D = [json.load(open(p)) for p in parts]
    rec = {k: sum((d["rec"][k] for d in D), []) for k in D[0]["rec"]}
    n = len(rec["M_J4b"])
    rate = {k: float(np.mean(v)) for k, v in rec.items()}
    ub = 0.05 + 1.96 * math.sqrt(0.05 * 0.95 / n)
    x = rate["M_J4b"]
    if x <= 0.060:
        v = f"支持（回復）: M の J4b={x:.1%} ≤ 6.0%"
    elif x >= 0.075:
        v = f"棄却（未回復）: M の J4b={x:.1%} ≥ 7.5%"
    else:
        v = f"未確定: M の J4b={x:.1%}（6.0〜7.5%）"
    note = "M の J4a ≤ 6.0%（Q320 の 16% は合成の作り由来）" if rate["M_J4a"] <= 0.060 else f"M の J4a={rate['M_J4a']:.1%}（現実型でも銘柄別の並べ替えは膨らむ）"
    calibs = sorted(glob.glob(os.path.join(RES, f"{tag}Q321_calib_*.json")))
    cal = json.load(open(calibs[-1])) if calibs else {}
    out = {"qid": "Q321", "question": SPEC["question"], "spec": SPEC, "n_reps": n, "binom_upper95": ub,
           "machine_verdict": v, "registered_note": note,
           "M_realistic": {k[2:]: rate[k] for k in rate if k.startswith("M_")},
           "V_q320_like": {k[2:]: rate[k] for k in rate if k.startswith("V_")},
           "calib_ref": os.path.basename(calibs[-1]) if calibs else None,
           "calib_summary": {k: cal.get(k) for k in ["mean_pairwise_corr", "real_L60_nocost_descriptive", "n_days_by_sym", "missing", "data_health"]},
           "parts": [os.path.basename(p) for p in parts]}
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RES, f"{tag}Q321_result_{ts}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("machine_verdict:", v); print("note:", note)
    print(json.dumps({"M": out["M_realistic"], "V": out["V_q320_like"]}, ensure_ascii=False, indent=1))
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
        with open(os.path.join(RES, f"{'smoke_' if a.smoke else ''}Q321_spec_{ts}.json"), "w", encoding="utf-8") as fh:
            json.dump({"registered": ts, "seed": SEED, **SPEC}, fh, ensure_ascii=False, indent=1)
        calib(a.smoke)
    if a.sim:
        p, n = map(int, a.part.split("/")); sim(a.reps, p, n, a.smoke)
    if a.combine:
        combine(a.smoke)


if __name__ == "__main__":
    main()
