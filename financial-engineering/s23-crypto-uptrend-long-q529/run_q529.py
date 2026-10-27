# -*- coding: utf-8 -*-
"""Q529 / S23: 暗号資産の上昇トレンドだけ買って持つ（TSMOM60・ロングのみ）。事前登録_q529.md。
使い方: python3 run_q529.py --h1 DIR --out DIR [--q528 DIR(ML つき副のための Q528 データを作る)]"""
import argparse, json, os
import numpy as np, pandas as pd
import crypto_core as C

T = lambda s: pd.Timestamp(s, tz="UTC")
S0, SEAL = T("2018-01-01"), T("2025-10-01")
HALF = {"BTC": 0.0002, "ETH": 0.00075}


def daily_series(h1dir, coin):
    """営業日の日足（21:00 UTC 区切り）と、次の取引可能 1 時間足の始値（執行値）。"""
    h1 = C.load_h1(h1dir, coin); b = C.bars(h1, "D1")
    o = h1["open"].to_numpy(); j = b["j_last"].to_numpy() + 1
    b["exec_px"] = np.where(j < len(h1), o[np.minimum(j, len(h1) - 1)], np.nan)
    b["day"] = b["g"]
    return b


def backtest(b, pos, half):
    """pos[t]: t の終値で決めた保有（0/1）。執行は次の始値。損益は 1 倍の名目で日次の比率。
    日 t+1 の損益 = 保有 × (exec_{t+1}→exec_{t+2} の比率)。コストは保有の変化のたびに片道。"""
    px = b["exec_px"].to_numpy(float)
    ret = np.zeros(len(b)); ret[:-1] = px[1:] / px[:-1] - 1          # exec_t → exec_{t+1}
    p = np.asarray(pos, float)                                      # t の終値で決め、exec_t（次の始値）で入る → exec_t→exec_{t+1} に効く
    pnl = p * ret - np.abs(np.diff(np.r_[0, p])) * half
    return pd.Series(pnl, index=b["day"].to_numpy())


def tsmom(b, L):
    c = b["close"].to_numpy(float); s = np.zeros(len(c)); s[L:] = (c[L:] > c[:-L]).astype(float); return s


def with_stop(b, base, k=3.0):
    c, h = b["close"].to_numpy(float), b["high"].to_numpy(float); atr = b["atr"].to_numpy(float)
    pos = np.zeros(len(c)); inpos = False; peak = 0; blocked = False
    for t in range(len(c)):
        if base[t] == 0:
            inpos = False; blocked = False; pos[t] = 0; continue
        if blocked:
            pos[t] = 0; continue
        if not inpos:
            inpos = True; peak = c[t]
        peak = max(peak, h[t])
        if np.isfinite(atr[t]) and c[t] < peak - k * atr[t]:
            inpos = False; blocked = True; pos[t] = 0          # 次に上昇トレンドが切れて再判定されるまで休む
        else:
            pos[t] = 1
    return pos


def stats(p, label):
    p = p[(p.index >= S0.tz_convert(None)) & (p.index < SEAL.tz_convert(None))] if p.index.tz is None else p[(p.index >= S0) & (p.index < SEAL)]
    eq = (1 + p).cumprod(); dd = float((eq / eq.cummax() - 1).min())
    sh = float(p.mean() / p.std() * np.sqrt(252)) if p.std() > 0 else 0.0
    yr = p.groupby(pd.DatetimeIndex(p.index).year).apply(lambda x: float((1 + x).prod() - 1)).round(4).to_dict()
    return dict(label=label, sharpe=sh, max_dd=dd, total=float(eq.iloc[-1] - 1), cagr=float(eq.iloc[-1] ** (252 / len(p)) - 1),
                t=C.tstat(p), year=yr)


def circ_null(bs, positions, B=200, seed=C.SEED):
    rng = np.random.default_rng(seed); out = []
    for _ in range(B):
        parts = []
        for c in ["BTC", "ETH"]:
            pos = positions[c]; n = len(pos); s = rng.integers(30, n - 30)
            parts.append(backtest(bs[c], np.roll(pos, s), HALF[c]))
        p = combine(parts); out.append(stats(p, "")["sharpe"])
    return np.array(out)


def combine(parts):
    df = pd.concat(parts, axis=1).fillna(0.0)
    return df.mean(axis=1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h1", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    bs = {c: daily_series(a.h1, c) for c in ["BTC", "ETH"]}
    for c in bs:
        bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
    res = {}
    # 買って持ち続ける
    bh = combine([backtest(bs[c], np.ones(len(bs[c])), HALF[c]) for c in bs]); res["buy_hold"] = stats(bh, "買って持つ")
    # 主
    pos = {c: tsmom(bs[c], 60) for c in bs}
    main_p = combine([backtest(bs[c], pos[c], HALF[c]) for c in bs]); res["main"] = stats(main_p, "TSMOM60")
    res["main"]["in_market"] = {c: float(pos[c][(bs[c].index >= S0.tz_convert(None)) & (bs[c].index < SEAL.tz_convert(None))].mean()) for c in bs}
    res["main"]["n_switch"] = {c: int(np.abs(np.diff(pos[c][(bs[c].index >= S0.tz_convert(None)) & (bs[c].index < SEAL.tz_convert(None))])).sum()) for c in bs}
    res["main"]["by_coin"] = {c: stats(backtest(bs[c], pos[c], HALF[c]), c) for c in bs}
    null = circ_null(bs, pos); z = float((res["main"]["sharpe"] - null.mean()) / null.std(ddof=1))
    res["main"]["null_sharpe_mean"] = float(null.mean()); res["main"]["null_z"] = z
    crit = dict(sharpe_gt_bh=res["main"]["sharpe"] > res["buy_hold"]["sharpe"], dd_shallower=res["main"]["max_dd"] > res["buy_hold"]["max_dd"],
                t_ge_2=res["main"]["t"] >= 2, null_z_ge_2=z >= 2)
    res["criteria"] = crit
    res["verdict"] = "支持" if all(crit.values()) else ("棄却" if not (crit["sharpe_gt_bh"] and crit["dd_shallower"]) else "未確定")
    # 副
    res["stop3atr"] = stats(combine([backtest(bs[c], with_stop(bs[c], pos[c]), HALF[c]) for c in bs]), "TSMOM60＋3ATR 損切り")
    for L in [20, 120]:
        res[f"tsmom{L}"] = stats(combine([backtest(bs[c], tsmom(bs[c], L), HALF[c]) for c in bs]), f"TSMOM{L}")
    json.dump(res, open(os.path.join(a.out, "result_q529.json"), "w"), ensure_ascii=False, indent=1, default=str)
    pd.DataFrame({"main": main_p, "buy_hold": bh}).to_csv(os.path.join(a.out, "daily_q529.csv"))
    for k in ["buy_hold", "main", "stop3atr", "tsmom20", "tsmom120"]:
        r = res[k]; print(f"{r['label']:<22} シャープ {r['sharpe']:.2f}  最大下落 {r['max_dd']*100:6.1f}%  年率 {r['cagr']*100:6.1f}%  t {r['t']:.2f}  年別 {r['year']}")
    print("主:", json.dumps({k: res['main'][k] for k in ['in_market', 'n_switch', 'null_sharpe_mean', 'null_z']}, ensure_ascii=False))
    print("判定:", res["criteria"], res["verdict"])


if __name__ == "__main__":
    main()
