# -*- coding: utf-8 -*-
"""Q565: S21 パイプライン（Q534 E1＝run_q547 と同じ流れ）を、方向の情報が無い合成 H1 に通す帰無検定（事前登録_q565.md）。
使い方: python3 run_q565.py DATA_DIR OUT_DIR DATASEED [DATASEED ...]"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z
import kensho_s21_reopen_q534 as E

MODEL_SEED = 20261025


def synth(d, sign_of):
    """足ごとの符号反転（事前登録の定義）。d は K.load 後。sign_of: 時刻 → ±1。"""
    d = d.copy().reset_index(drop=True)
    o, h, l, c = (np.log(d[x].to_numpy(float)) for x in ["open", "high", "low", "close"])
    g = o - np.r_[o[0], c[:-1]]; g[0] = 0.0
    rh, rl, rc = h - o, l - o, c - o
    s = sign_of.reindex(d["time"]).to_numpy()
    neg = s < 0
    g2 = np.where(neg, -g, g); rc2 = np.where(neg, -rc, rc)
    rh2 = np.where(neg, -rl, rh); rl2 = np.where(neg, -rh, rl)
    c2 = o[0] + np.cumsum(g2 + rc2); o2 = c2 - rc2
    ratio = np.exp(c2 - c)  # 価格水準の比でスプレッドを伸縮
    spo = (d["ask_open"] - d["open"]).to_numpy(); spc = (d["ask_close"] - d["close"]).to_numpy()
    sph = (d["ask_high"] - d["high"]).to_numpy(); spl = (d["ask_low"] - d["low"]).to_numpy()
    O, H, L, C = np.exp(o2), np.exp(o2 + rh2), np.exp(o2 + rl2), np.exp(c2)
    aO = O + spo * ratio; aC = C + spc * ratio
    aH = H + np.where(neg, spl, sph) * ratio; aL = L + np.where(neg, sph, spl) * ratio
    aH = np.maximum(aH, np.maximum(aO, aC)); aL = np.minimum(aL, np.minimum(aO, aC))
    d["open"], d["high"], d["low"], d["close"] = O, H, L, C
    d["ask_open"], d["ask_high"], d["ask_low"], d["ask_close"] = aO, aH, aL, aC
    d["spr"] = (d["ask_close"] - d["close"]).clip(lower=0)
    return d


def check(real, syn):
    def atr(d):
        tr = np.maximum(d["high"] - d["low"], np.maximum((d["high"] - d["close"].shift()).abs(), (d["low"] - d["close"].shift()).abs()))
        return float((tr.rolling(24).mean() / d["close"]).median())
    r = np.sign(np.diff(np.log(syn["close"].to_numpy())))
    return dict(atr_ratio=atr(syn) / atr(real), sign_agree_lag1=float((r[1:] == r[:-1]).mean()),
                real_sign_agree_lag1=float((np.sign(np.diff(np.log(real["close"].to_numpy())))[1:] == np.sign(np.diff(np.log(real["close"].to_numpy())))[:-1]).mean()))


DATA, OUT = sys.argv[1], sys.argv[2]; SEEDS = [int(x) for x in sys.argv[3:]]; os.makedirs(OUT, exist_ok=True); t00 = time.time()
raw = {s: K.load(DATA, s) for s in J.SYMS15}
alltimes = pd.Index(sorted(set().union(*[set(d["time"]) for d in raw.values()])))
for sd in SEEDS:
    rng = np.random.default_rng(sd)
    sign_of = pd.Series(rng.choice([-1.0, 1.0], size=len(alltimes)), index=alltimes)
    dataw, chk = {}, {}
    for s in J.SYMS15:
        d2 = synth(raw[s], sign_of); chk[s] = check(raw[s], d2)
        o = J.make(d2, s); Rw, Xw = Z.labels_wk(o["d"], s)
        dataw[s] = dict(o, R=Rw, X=Xw, _sr=E.since_reopen(o["d"]))
    print(f"seed={sd} 合成・準備 済 {time.time()-t00:.0f}s", flush=True)
    K.SEED = MODEL_SEED; TR, DY = [], []
    for Y in E.YEARS:
        s0, s1 = W.TS(Y), W.TS(Y + 1)
        m, _ = Q.train_window(dataw, s0, None)
        P = K.predict(m, dataw, s0 - Q.WARM, s1); PP = J.apply_thr(dataw, P, J.thr_series(dataw, P), s0)
        tr = K.run_policy(dataw, E.block(PP, dataw, 1), 0.0).assign(fold=Y)
        TR.append(tr); DY.append(K.daily(tr, s0, s1, 1.0))
        print(f"seed={sd} {Y}: n={len(tr)} R={tr['R'].mean():.4f} sum={tr['R'].sum():.0f} | {time.time()-t00:.0f}s", flush=True)
    tr = pd.concat(TR); p = pd.concat(DY).groupby(level=0).sum()
    st = Z.stats(tr, p, len(E.YEARS)); st["data_seed"] = sd
    st["passed"] = bool(st["t"] >= 2 and st["pos_years"] >= 7)
    st["check"] = dict(atr_ratio_median=float(np.median([v["atr_ratio"] for v in chk.values()])),
                       sign_agree_lag1_mean=float(np.mean([v["sign_agree_lag1"] for v in chk.values()])),
                       real_sign_agree_lag1_mean=float(np.mean([v["real_sign_agree_lag1"] for v in chk.values()])), by_sym=chk)
    tr.to_csv(os.path.join(OUT, f"trades_q565_seed{sd}.csv.gz"), index=False, compression="gzip")
    json.dump(st, open(os.path.join(OUT, f"stats_q565_seed{sd}.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("RESULT", json.dumps({k: st[k] for k in ("data_seed", "n", "mean_R", "t", "total_R", "max_dd_R", "pos_years", "passed")}), flush=True)
print("done", round(time.time() - t00), flush=True)
