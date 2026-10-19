#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q322: 銘柄ごとの年内並べ替えを束ねて「支持・確定」とした Q183・Q212・Q205 を、日付共通の並べ替えで再判定する（Q321 の次段階）
================================================================================

【前段】Q321（common-perm-size-q321）: 現実型の腕なし帰無で、銘柄 × 年の並べ替えを束ねた検定は 12.4% 誤って合格し、
年の中で日付を 1 つの並べ替えで動かして全銘柄を一緒に動かす版（fe_core.perm_dates_within）は 5.0% に戻った。
帰無が狭くなる向きの誤りなので、危ないのは z を判定に使って「支持・確定」とした行だけ。

【仮説（測る前に固定）】
H: 3 件とも z は小さくなる（帰無の sd が広がる）。Q205（z 6〜8）・Q183（z 10〜14）は z≥2 を保ち判定は変わらない見込み。
   Q212 の H1a 後半（z=+4.87・年 t=+0.81）は最も落ちやすい。見込みは判定に使わない。

【変えるのは帰無だけ（判定規則・統計・B・データは元の行のまま）】
- 元のスクリプトを importlib で読み込み、読み込み・統計の関数をそのまま使う（元のファイルは変えない）。
- Q183: V（直前 24 本の実現ボラ）を「全通貨の 1 時間の時刻の和集合」の格子に置き、年月の中で時刻を 1 つの並べ替えで動かす。
        格子で欠ける (時刻, 通貨) は通貨ごとに前の値で埋め、残りは後ろの値で埋めてから引く（ボラは持続するため）。
        元: V を通貨 × 年月の中で並べ替え。判定: 前後半とも ρ>0・ρ の z≥2・(b) 差>0・(b) t≥2 → 支持、どちらかで ρ の z<2 → 棄却、ほか未確定。
- Q212: 曜日ラベル（週末=1）は日付だけで決まるので、全通貨の日付の和集合の表を年の中で 1 つの並べ替えで動かし、全通貨に同じラベルを付ける。
        元: 日のラベルを通貨 × 年の中で並べ替え。判定: H1a 前後半とも同符号かつ |z|≥2、H1b 前後半とも差<0 かつ z≤−2。
- Q205: 規模 w を 15 銘柄の日付の和集合の格子に置き、年の中で日付を 1 つの並べ替えで動かす。欠ける日は銘柄ごとに前の値・後ろの値で埋める。
        元: w を銘柄ごとに年の中で並べ替え。判定: all15 前後半とも シャープ差の年単位 t≥2 かつ z≥2 → 支持、どちらかで t<2 → 棄却、ほか未確定。
- 年単位 t・NW t（並べ替えに依らない値）は元と同じ値が出ることを確かめる（実装の照合）。

【判定（事前固定）】各行の元の規則に、日付共通の z を入れて機械判定する。元の判定から変わった行だけ「判定の変更」とし、
  元の README・知見・キューの記載を直す。変わらない行は「再判定で維持」と記す。

【捨てた案の数】2: 銘柄 × 年と日付共通の両方を同じ乱数で回して sd 比を測る（記述としては Q321 で済み）、B を 999 に増やす（元と比べにくくなる）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】設計・コード・実行・解釈とも Opus 本体。
【実行】python3 kensho_common_perm_rejudge_q322.py --spec → --run Q205|Q212|Q183 --part i/n → --combine（Mac で実データ）
"""
import argparse, glob, importlib.util, json, math, os, sys, datetime as _dt
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FE, "..", "tools"))
from fe_core import perm_dates_within, z_of, null_summary  # noqa: E402

ORIG = {"Q183": ("crypto-h1-reversal-vol", "kensho_crypto_h1_reversal_vol_q183.py", "Q183_result_20261010_030124.json"),
        "Q212": ("crypto-weekend-effect", "kensho_crypto_weekend_q212.py", "Q212_result_20261010_172317.json"),
        "Q205": ("vol-targeting-tsmom", "kensho_vol_targeting_q205.py", "Q205_result_20261010_160540.json")}
B_TOTAL = 300
SEED = 20261019
PARTS = os.path.join(HERE, "results", "parts")
SPEC = {"qid": "Q322", "B": B_TOTAL, "seed": SEED, "orig": ORIG,
        "rule": "各行の元の判定規則に日付共通の z を入れる。統計・データ・B=300 は元のまま。欠けた格子は銘柄ごとに ffill→bfill（Q183・Q205）。Q212 は日付だけのラベルなので埋めない",
        "multiple_comparisons": "判定は元の行と同じ本数（Q183: 4、Q212: 4、Q205: 4）。再判定の 3 件は別々の問いとして扱う"}


def load_mod(q):
    d, f, _ = ORIG[q]
    sp = importlib.util.spec_from_file_location(f"orig_{q}", os.path.join(FE, d, f))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def grid_fill(frames, col):
    """frames: {sym: DataFrame(time, col)} → (times, W[T,S] を ffill→bfill, 各 sym の行位置)"""
    times = np.unique(np.concatenate([fr["time"].values for fr in frames.values()]))
    syms = list(frames)
    W = pd.DataFrame(np.nan, index=pd.DatetimeIndex(times), columns=syms)
    pos = {}
    for s, fr in frames.items():
        W.loc[pd.DatetimeIndex(fr["time"].values), s] = fr[col].values
        pos[s] = np.searchsorted(times, fr["time"].values)
    return times, W.ffill().bfill().values, syms, pos


# ----------------------------------------------------------------------------- Q205
def prep_Q205(m):
    syms, missing = m.syms_available(m.SYMS)
    store, frames, wf = {}, [], {}
    for s in syms:
        df = m.load_d1(s); c = df["close"].values; cb = m.cost_bp_oneway(s, c)
        sig = m.tsmom_pos(c, m.L_MOM)
        sd = pd.Series(df["ret"].values).rolling(m.VOL_N).std().values * math.sqrt(252)
        w = np.minimum(m.TARGET / np.where(sd > 0, sd, np.nan), m.CAP); w = np.nan_to_num(w)
        frames.append(pd.DataFrame({"year": df["year"].values, "sym": s, "fix": m.pnl_bp(sig, c, m.cost_bp_oneway(s, c)), "vt": m.pnl_bp(sig * w, c, cb)}))
        store[s] = (df["year"].values, sig, w, c, cb); wf[s] = pd.DataFrame({"time": df["time"].values, "w": w})
    obs = m.summarize(m.cell_stats(pd.concat(frames, ignore_index=True), ["fix", "vt"]))
    times, W, gs, pos = grid_fill(wf, "w")
    return {"obs": obs, "store": store, "times": times, "W": W, "gs": gs, "pos": pos, "missing": missing}


def null_Q205(m, P, rng, B):
    yrs = pd.DatetimeIndex(P["times"]).year.values
    out = {k: [] for k in P["obs"]}
    for b in range(B):
        Wp = perm_dates_within(rng, P["W"], yrs)
        fr = []
        for j, s in enumerate(P["gs"]):
            yr, sig, w, c, cb = P["store"][s]
            wp = Wp[P["pos"][s], j]
            fr.append(pd.DataFrame({"year": yr, "sym": s, "fix": m.pnl_bp(sig, c, cb), "vt": m.pnl_bp(sig * wp, c, cb)}))
        st = m.summarize(m.cell_stats(pd.concat(fr, ignore_index=True), ["fix", "vt"]))
        for k in out:
            if k in st:
                out[k].append(st[k]["sharpe_diff"])
    return {k: {"sharpe_diff": v} for k, v in out.items()}


def judge_Q205(obs, null):
    S = {}
    for k, v in obs.items():
        S[k] = {"sharpe_diff": v["sharpe_diff"], "sharpe_diff_t": v["sharpe_diff_t"], "z": z_of(v["sharpe_diff"], null[k]["sharpe_diff"])[0],
                "null": null_summary(v["sharpe_diff"], null[k]["sharpe_diff"])}
    pre, post = S.get("all15_pre", {}), S.get("all15_post", {})
    g = lambda p, k: (p.get(k) if p.get(k) == p.get(k) and p.get(k) is not None else 0)
    if all(g(p, "sharpe_diff_t") >= 2 and g(p, "z") >= 2 for p in (pre, post)):
        v = "支持: ボラ・ターゲティングは順張りのシャープを上げる"
    elif g(pre, "sharpe_diff_t") < 2 or g(post, "sharpe_diff_t") < 2:
        v = "棄却: 前後半のどちらかで t<2"
    else:
        v = "未確定"
    return S, v


# ----------------------------------------------------------------------------- Q212
def prep_Q212(m):
    syms, missing = m.syms_available(m.CRYPTO, kind="H1_dukascopy")
    frames = []
    for s in syms:
        h1 = m.load_h1(s); c = h1["close"].values
        gross = m.pnl_bp(m.tsmom_pos(c, m.L_MOM), c, np.zeros(len(c)))
        frames.append(pd.DataFrame({"sym": s, "year": h1["year"].values, "date": h1["time"].dt.floor("D").values, "wk": (h1["dow"].values >= 5).astype(int),
                                    "ret_bp": h1["ret"].values * 1e4, "gross": gross}).dropna())
    cells = pd.concat(frames, ignore_index=True)
    obs = m.summarize(m.cell_stats(cells))
    dates = cells.drop_duplicates("date")[["date", "wk"]].sort_values("date").reset_index(drop=True)
    return {"obs": obs, "cells": cells, "dates": dates, "missing": missing}


def null_Q212(m, P, rng, B):
    d = P["dates"]; yrs = pd.DatetimeIndex(d["date"].values).year.values
    out = {k: {"ret": [], "mom": []} for k in P["obs"]}
    for b in range(B):
        dd = pd.DataFrame({"date": d["date"].values, "wk_p": perm_dates_within(rng, d["wk"].values, yrs)})
        st = m.summarize(m.cell_stats(P["cells"].merge(dd, on="date", how="left"), "wk_p"))
        for k in out:
            if k in st:
                out[k]["ret"].append(st[k]["ret_diff_bp"]); out[k]["mom"].append(st[k]["mom_diff_bp"])
    return out


def judge_Q212(obs, null):
    S = {}
    for k, v in obs.items():
        S[k] = {**v, "ret_diff_z": z_of(v["ret_diff_bp"], null[k]["ret"])[0], "mom_diff_z": z_of(v["mom_diff_bp"], null[k]["mom"])[0],
                "null_ret": null_summary(v["ret_diff_bp"], null[k]["ret"]), "null_mom": null_summary(v["mom_diff_bp"], null[k]["mom"])}
    pre, post = S.get("pre", {}), S.get("post", {})
    g = lambda p, k: (p.get(k) or 0)
    a_ok = abs(g(pre, "ret_diff_z")) >= 2 and abs(g(post, "ret_diff_z")) >= 2 and np.sign(g(pre, "ret_diff_bp")) == np.sign(g(post, "ret_diff_bp"))
    b_ok = g(pre, "mom_diff_z") <= -2 and g(post, "mom_diff_z") <= -2 and g(pre, "mom_diff_bp") < 0 and g(post, "mom_diff_bp") < 0
    return S, ("H1a 支持: 週末のリターンに差あり" if a_ok else "H1a 棄却") + "／" + ("H1b 支持: 週末の順張りは弱い" if b_ok else "H1b 棄却")


# ----------------------------------------------------------------------------- Q183
def prep_Q183(m):
    syms, missing = m.syms_available(m.CRYPTO, kind="H1_dukascopy")
    frames = []
    for s in syms:
        df = m.load_csv(f"{s}_H1_dukascopy")
        df = df[df["high"] != df["low"]].reset_index(drop=True)
        c = df["close"].values; r = np.r_[np.nan, c[1:] / c[:-1] - 1]
        V = np.log(pd.Series(r).rolling(m.VOL_WIN).std().values)
        R = np.r_[-np.sign(np.nan_to_num(r[:-1])) * r[1:] * 1e4, np.nan]
        frames.append(pd.DataFrame({"sym": s, "time": df["time"].values, "ym": df["time"].dt.year.values * 100 + df["time"].dt.month.values,
                                    "year": df["time"].dt.year.values, "V": V, "R": R}).dropna())
    cells = pd.concat(frames, ignore_index=True)
    times, W, gs, _ = grid_fill({s: g[["time", "V"]] for s, g in cells.groupby("sym", sort=False)}, "V")
    ti = np.searchsorted(times, cells["time"].values); si = np.array([gs.index(s) for s in cells["sym"].values])
    tt = pd.DatetimeIndex(times); ym_grid = tt.year.values * 100 + tt.month.values
    groups_idx = {k: v.index.values for k, v in cells.groupby(["ym", "sym"])}
    Rv = cells["R"].values

    def stats(Vv):  # 元の run() の内側の stats をそのまま写した（元は関数の中にあり import できない）
        cs = {}
        for (ym, s), idx in groups_idx.items():
            v = Vv[idx]; R_ = Rv[idx]
            if len(idx) < 100:
                continue
            q = np.nanquantile(v, 0.8); top = v >= q
            cs[(ym, s)] = (m.spearman(v, R_), R_[top].mean(), R_[~top].mean())
        out = {}
        for pn, (y0, y1) in (("all", (0, 9999)), ("pre", (0, m.SPLIT_Y)), ("post", (m.SPLIT_Y, 9999))):
            by = {}
            for (ym, s), st in cs.items():
                if y0 <= ym // 100 < y1:
                    by.setdefault(ym, []).append(st)
            if len(by) < 6:
                continue
            arr = np.array([np.nanmean(np.array(v, float), axis=0) for v in by.values()])
            out[pn] = {"n_months": int(len(arr)), "rho_mean": float(np.nanmean(arr[:, 0])), "rho_t": m.nw_t(arr[:, 0], 3), "top_gross": float(np.nanmean(arr[:, 1])),
                       "top_minus_rest": float(np.nanmean(arr[:, 1] - arr[:, 2])), "top_minus_rest_t": m.nw_t(arr[:, 1] - arr[:, 2], 3)}
        return out
    obs = stats(cells["V"].values)
    return {"obs": obs, "stats": stats, "W": W, "ti": ti, "si": si, "ym_grid": ym_grid, "missing": missing, "n_grid": len(times), "n_cells": len(cells)}


def null_Q183(m, P, rng, B):
    out = {k: {"rho": [], "diff": []} for k in P["obs"]}
    for b in range(B):
        _, pi = perm_dates_within(rng, np.arange(len(P["ym_grid"])), P["ym_grid"], return_index=True)
        st = P["stats"](P["W"][pi[P["ti"]], P["si"]])
        for k in out:
            if k in st:
                out[k]["rho"].append(st[k]["rho_mean"]); out[k]["diff"].append(st[k]["top_minus_rest"])
    return out


def judge_Q183(obs, null):
    S = {}
    for k, v in obs.items():
        S[k] = {**v, "rho_z": z_of(v["rho_mean"], null[k]["rho"])[0], "diff_z": z_of(v["top_minus_rest"], null[k]["diff"])[0],
                "null_rho": null_summary(v["rho_mean"], null[k]["rho"]), "null_diff": null_summary(v["top_minus_rest"], null[k]["diff"])}
    pre, post = S.get("pre", {}), S.get("post", {})
    ok = lambda p: (p.get("rho_mean") or 0) > 0 and (p.get("rho_z") or 0) >= 2 and (p.get("top_minus_rest") or 0) > 0 and (p.get("top_minus_rest_t") or 0) >= 2
    if ok(pre) and ok(post):
        v = "支持: ボラは逆張りの見返りを予測する"
    elif (pre.get("rho_z") or 0) < 2 or (post.get("rho_z") or 0) < 2:
        v = "棄却: 前後半のどちらかで z<2"
    else:
        v = "未確定"
    return S, v


FUN = {"Q205": (prep_Q205, null_Q205, judge_Q205), "Q212": (prep_Q212, null_Q212, judge_Q212), "Q183": (prep_Q183, null_Q183, judge_Q183)}


def _json(o):
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def run_part(q, part, nparts):
    m = load_mod(q); prep, nullf, _ = FUN[q]
    P = prep(m)
    Bp = B_TOTAL // nparts + (1 if part < B_TOTAL % nparts else 0)
    rng = np.random.default_rng([SEED, int(q[1:]), part])
    null = nullf(m, P, rng, Bp)
    with open(os.path.join(PARTS, f"{q}_part{part}of{nparts}.json"), "w") as fh:
        json.dump({"q": q, "part": part, "nparts": nparts, "B": Bp, "obs": P["obs"], "null": null, "missing": P["missing"],
                   **({"n_grid": P["n_grid"], "n_cells": P["n_cells"]} if q == "Q183" else {})}, fh, default=_json)
    print(q, part, nparts, "B", Bp, "done")


def combine():
    res = {"qid": "Q322", "generated": _dt.datetime.now().isoformat(timespec="seconds"), "spec": SPEC, "rows": {}}
    for q in ORIG:
        fs = sorted(glob.glob(os.path.join(PARTS, f"{q}_part*.json")))
        if not fs:
            continue
        ds = [json.load(open(f)) for f in fs]
        nparts = ds[0]["nparts"]
        assert len(ds) == nparts and all(d["nparts"] == nparts for d in ds), f"{q}: parts 不足"
        obs = ds[0]["obs"]
        null = {}
        for d in ds:
            for k, v in d["null"].items():
                for kk, vv in v.items():
                    null.setdefault(k, {}).setdefault(kk, []).extend(vv)
        S, verdict = FUN[q][2](obs, null)
        orig = json.load(open(os.path.join(FE, ORIG[q][0], "results", ORIG[q][2])))
        res["rows"][q] = {"B": sum(d["B"] for d in ds), "verdict_common_date": verdict, "verdict_orig": orig.get("machine_verdict"),
                          "summary": S, "orig_summary": orig.get("summary"), "missing": ds[0]["missing"],
                          **({"n_grid": ds[0]["n_grid"], "n_cells": ds[0]["n_cells"]} if q == "Q183" else {})}
        print(q, "元:", orig.get("machine_verdict"), "→ 日付共通:", verdict)
    out = os.path.join(HERE, "results", f"Q322_result_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1, default=_json); print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", action="store_true"); ap.add_argument("--run"); ap.add_argument("--part", default="0/1"); ap.add_argument("--combine", action="store_true")
    a = ap.parse_args()
    if a.spec:
        p = os.path.join(HERE, "results", f"Q322_spec_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        json.dump({**SPEC, "doc": __doc__}, open(p, "w"), ensure_ascii=False, indent=1, default=_json); print("wrote", p)
    if a.run:
        i, n = map(int, a.part.split("/")); run_part(a.run, i, n)
    if a.combine:
        combine()
