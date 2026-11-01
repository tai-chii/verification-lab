# -*- coding: utf-8 -*-
"""Q607 S38 FX の 2 年金利差で説明できない 20 日の値動きの平均回帰。事前登録 事前登録_q607.md と同一・変更禁止。
【仮説】為替は金利差の変化に反応するが、それを超えて動いた分は一時的な偏りで、数週間で戻る。
【判定】A PF≥1.05 B 日次 NW t≥1.5 C 前後半とも平均>0 D 帰無 z≥1.5 E β=0 版との日次差の平均>0 かつ NW t≥1 F composite。
A〜F すべて→支持（フォワード候補）。A〜D のどれか不成立→棄却。A〜D は満たすが E か F 不成立→未確定。
【多重比較の本数】金利の族に 1 本追加して 10 本。判定は 1 本。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_s38_fx_rate_gap_q607.py ／ 経路確認 --smoke --B 5"""
import argparse, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_fx_rates_common"))
import fxrates as F
from composite_gate import gate
W, N, Z_IN, Z_OUT, Z_STOP, H, MINV = 252, 20, 2.0, 0.5, 4.0, 20, 200


def z_resid(c, d, W=W, beta0=False):
    """変化の残差の 20 日累積を標準化する。beta0 は素の反転（E の対照）。返り値 z, β。"""
    r = np.r_[np.nan, np.diff(np.log(c))]; x = np.r_[np.nan, np.diff(d)]; n = len(c); z, be = np.full(n, np.nan), np.full(n, np.nan)
    for t in range(W, n):
        rw, xw = r[t - W + 1:t + 1], x[t - W + 1:t + 1]; v = np.isfinite(rw) & (np.isfinite(xw) | beta0)
        if v.sum() < MINV * W / 252: continue
        b = 0.0 if beta0 else float((rw[v] * xw[v]).sum() / (xw[v] ** 2).sum()) if (xw[v] ** 2).sum() > 0 else np.nan
        if not np.isfinite(b): continue
        e = rw - b * (0.0 if beta0 else xw); be[t] = b; s = np.nanstd(e, ddof=1); last = e[-N:]
        if s > 0 and np.isfinite(last).all(): z[t] = last.sum() / (s * np.sqrt(N))
    return z, be


def z_level(c, d, W=252):
    """水準回帰の残差の z（記述）。"""
    y = np.log(c); n = len(c); z, be = np.full(n, np.nan), np.full(n, np.nan)
    for t in range(W - 1, n):
        a, b = d[t - W + 1:t + 1], y[t - W + 1:t + 1]; v = np.isfinite(a) & np.isfinite(b)
        if v.sum() < MINV or not np.isfinite(d[t]): continue
        s, i = np.polyfit(a[v], b[v], 1); e = b[v] - s * a[v] - i; sd = e.std(ddof=2); be[t] = s
        if sd > 0: z[t] = (y[t] - s * d[t] - i) / sd
    return z, be


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=F.B_DEFAULT); a = ap.parse_args()
    rng = np.random.default_rng(F.SEED); filled = F.fill_costs(); T = F.C.rate_table(); Y = F.yields_panel(a.smoke, rng); P = {}; Z = {}; Ok = {}; Z0 = {}; Z126 = {}; Ok126 = {}; ZL = {}; OkL = {}; lo = {}; All = {}; beta = {}
    for s in F.SYMS:
        p = F.load_pair(s, Y, T, a.smoke, rng); d = p["yb"] - p["yq"]; P[s] = p
        z, b = z_resid(p["c"], d); Z[s] = z; Ok[s] = np.nan_to_num(b) > 0; lo[s] = int(np.argmax(np.isfinite(z))); All[s] = np.ones(p["n"], bool); beta[s] = b
        Z0[s], _ = z_resid(p["c"], d, beta0=True); Z126[s], b2 = z_resid(p["c"], d, W=126); Ok126[s] = np.nan_to_num(b2) > 0; ZL[s], b3 = z_level(p["c"], d); OkL[s] = np.nan_to_num(b3) > 0
        print(s, p["n"], "z 有効", int(np.isfinite(z).sum()), flush=True)
    t, D, R, mo = F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H); res = dict(qid="Q607", strategy="S38", config=dict(seal=str(F.SEAL.date()), W=W, N=N, z=[Z_IN, Z_OUT, Z_STOP], H=H, B=a.B, data_span=[str(min(p["D"][0] for p in P.values()).date()), str(max(p["D"][-1] for p in P.values()).date())], smoke=a.smoke), コスト補完=filled, 本体=F.summary(t, D, mo))
    obs = float(t["R"].mean()); z, nm, ns = F.null_z(P, R, lo, a.B, obs); res["帰無"] = dict(z=z, 平均_bp=nm, sd_bp=ns)
    t0, D0, _, m0 = F.book(P, Z0, All, Z_IN, Z_OUT, Z_STOP, H); res["β0版"] = F.summary(t0, D0, m0, part=False); df = (D["net"] - D0["net"].reindex(D["net"].index).fillna(0.0)); res["β0との差"] = dict(平均_bp日=float(df.mean() * 1e4), NW_t=float(F.nw_t(df.to_numpy())))
    cg = gate(D["net"], "S38"); res["composite"] = cg; s = res["本体"]
    ck = dict(A=s["PF"] >= 1.05, B=s["NW_t"] >= 1.5, C=s["前半_bp"] > 0 and s["後半_bp"] > 0, D=z >= 1.5, E=df.mean() > 0 and res["β0との差"]["NW_t"] >= 1, F=bool(cg["関門"]["通過"])); res["判定の内訳"] = {k: bool(v) for k, v in ck.items()}; res["machine_verdict"] = F.verdict(ck)
    res["記述"] = dict(窓126=F.summary(*F.book(P, Z126, Ok126, Z_IN, Z_OUT, Z_STOP, H)[:2], part=False), 水準回帰=F.summary(*F.book(P, ZL, OkL, Z_IN, Z_OUT, Z_STOP, H)[:2], part=False), 再入場なし=F.summary(*F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H, no_reenter=True)[:2], part=False), スプレッド2倍=F.summary(*F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H, m=2.0)[:2], part=False), β中央値={k: float(np.nanmedian(v)) for k, v in beta.items()})
    D["net"].to_csv(os.path.join(HERE, "results", ("smoke_" if a.smoke else "") + "daily_q607.csv")); F.dump(HERE, "q607", res, t, a.smoke); print({k: v for k, v in s.items() if k not in ("型別", "出口", "年別_bp", "ペア別_bp")}); print(res["帰無"], res["β0との差"], res["判定の内訳"], res["machine_verdict"])


if __name__ == "__main__":
    main()
