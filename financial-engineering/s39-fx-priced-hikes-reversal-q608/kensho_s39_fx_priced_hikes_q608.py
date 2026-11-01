# -*- coding: utf-8 -*-
"""Q608 S39 利上げ織り込みの行き過ぎの反転。事前登録 事前登録_q608.md と同一・変更禁止。
【仮説】2 年金利 − 政策金利の通貨間差が極端なとき、織り込まれた通貨は先回りで買われており、数週間〜数か月で戻る。
【判定】A PF≥1.05 B 日次 NW t≥1.5 C 前後半とも平均>0 D 帰無 z≥1.5 E キャリー符号との日次相関≤0.5 かつ値動き部分の NW t≥1 F composite。
A〜F すべて→支持（フォワード候補）。A〜D のどれか不成立→棄却。A〜D は満たすが E か F 不成立→未確定。
【多重比較の本数】金利の族に 1 本追加して 11 本。判定は 1 本。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_s39_fx_priced_hikes_q608.py ／ 経路確認 --smoke --B 5"""
import argparse, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, "..", "_fx_rates_common"), os.path.join(HERE, "..", "_s09_common")]
import fxrates as F
import s09carry as S9
from composite_gate import gate
W, MINV, Z_IN, Z_OUT, Z_STOP, H = 504, 400, 2.0, 0.5, 4.0, 120


def z_of(g, W=W, minv=MINV):
    s = pd.Series(g); m, sd = s.rolling(W, min_periods=minv).mean(), s.rolling(W, min_periods=minv).std(ddof=1); return ((s - m) / sd).to_numpy(float)


def carry_daily(P, smoke):
    """E の対照: 政策金利差の符号で常時保有（19 本・本案と同じ実コスト）。"""
    out = {}
    for s, p in P.items():
        pos = np.sign(np.nan_to_num(S9.rate_diff(s, p["D"].values, smoke=False))); c, n = p["c"], p["n"]; held = np.r_[0.0, pos[:-1]]; g = held * np.r_[0.0, c[1:] / c[:-1] - 1]
        dl = np.r_[0.0, np.diff(p["sw"][1])]; ds = np.r_[0.0, np.diff(p["sw"][-1])]; sw = np.where(held > 0, dl, np.where(held < 0, ds, 0.0)); sp = np.abs(np.diff(np.r_[0.0, pos])) * p["rel"] / 2
        out[s] = pd.Series(g + sw - sp, index=p["D"])
    return pd.concat(out, axis=1).fillna(0.0).sum(1) / len(P)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=F.B_DEFAULT); a = ap.parse_args()
    rng = np.random.default_rng(F.SEED); filled = F.fill_costs(); T = F.C.rate_table(); Y = F.yields_panel(a.smoke, rng); P = {}; Z = {}; Z252 = {}; Ok = {}; lo = {}; desc = {}
    for s in F.SYMS:
        p = F.load_pair(s, Y, T, a.smoke, rng); g = (p["yb"] - p["pb"]) - (p["yq"] - p["pq"]); P[s] = p; Z[s] = z_of(g); Z252[s] = z_of(g, 252, 200); Ok[s] = np.ones(p["n"], bool); lo[s] = int(np.argmax(np.isfinite(Z[s]))); desc[s] = float(np.nanstd(g)); print(s, p["n"], "z 有効", int(np.isfinite(Z[s]).sum()), flush=True)
    t, D, R, mo = F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H); res = dict(qid="Q608", strategy="S39", config=dict(seal=str(F.SEAL.date()), W=W, minv=MINV, z=[Z_IN, Z_OUT, Z_STOP], H=H, B=a.B, data_span=[str(min(p["D"][0] for p in P.values()).date()), str(max(p["D"][-1] for p in P.values()).date())], smoke=a.smoke), コスト補完=filled, 本体=F.summary(t, D, mo), g_sd=desc)
    z, nm, ns = F.null_z(P, R, lo, a.B, float(t["R"].mean())); res["帰無"] = dict(z=z, 平均_bp=nm, sd_bp=ns); cd = carry_daily(P, a.smoke); idx = D["net"].index; rho = float(D["net"].corr(cd.reindex(idx).fillna(0.0))); s = res["本体"]
    same = [float(np.sign(S9.rate_diff(r, pd.DatetimeIndex([e]).values, smoke=False)[0])) == dr for r, e, dr in zip(t["sym"], t["ed"], t["dr"])]; res["キャリー"] = dict(日次相関=rho, 対照Sharpe=float(cd.mean() / cd.std(ddof=1) * np.sqrt(252)), 同じ向きの割合=float(np.mean(same)))
    cg = gate(D["net"], "S39"); res["composite"] = cg; ck = dict(A=s["PF"] >= 1.05, B=s["NW_t"] >= 1.5, C=s["前半_bp"] > 0 and s["後半_bp"] > 0, D=z >= 1.5, E=rho <= 0.5 and s["値動きNW_t"] >= 1, F=bool(cg["関門"]["通過"])); res["判定の内訳"] = {k: bool(v) for k, v in ck.items()}; res["machine_verdict"] = F.verdict(ck)
    res["記述"] = dict(順張り=F.summary(*F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H, dirn=1)[:2], part=False), 窓252=F.summary(*F.book(P, Z252, Ok, Z_IN, Z_OUT, Z_STOP, H)[:2], part=False), 再入場なし=F.summary(*F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H, no_reenter=True)[:2], part=False), スプレッド2倍=F.summary(*F.book(P, Z, Ok, Z_IN, Z_OUT, Z_STOP, H, m=2.0)[:2], part=False))
    D["net"].to_csv(os.path.join(HERE, "results", ("smoke_" if a.smoke else "") + "daily_q608.csv")); F.dump(HERE, "q608", res, t, a.smoke); print({k: v for k, v in s.items() if k not in ("型別", "出口", "年別_bp", "ペア別_bp")}); print(res["帰無"], res["キャリー"], res["判定の内訳"], res["machine_verdict"])


if __name__ == "__main__":
    main()
