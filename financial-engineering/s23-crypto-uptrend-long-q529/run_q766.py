# -*- coding: utf-8 -*-
"""Q766 / S23: 執行の遅れ（取引可能な 1 時間足 k 本）への依存。事前登録_q766.md と同一・変更禁止。
【判定】頑健: k<=24 の 7 セルすべてでシャープ>買って持つ かつ 最大下落が浅い。弱い: k<=6 のどれかでシャープ<=買って持つ。中間: それ以外。
多重比較の本数には足さない（頑健性の記述）。S23 の規則・停止線は変えない。
使い方: python3 run_q766.py --h1 DIR"""
import argparse, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "s22-crypto-ml-fintokei-q528"))
import crypto_core as C
import run_q529 as R

DELAYS = [0, 1, 2, 3, 6, 12, 24, 48, 72]
FINAL = (pd.Timestamp("2025-10-01"), pd.Timestamp("2026-10-01"))


def daily_series_delayed(h1dir, coin, k):
    """R.daily_series と同じ。執行の値だけ、次の取引可能 1 時間足からさらに k 本後ろの始値にする。"""
    h1 = C.load_h1(h1dir, coin); b = C.bars(h1, "D1")
    o = h1["open"].to_numpy(); j = b["j_last"].to_numpy() + 1 + k
    b["exec_px"] = np.where(j < len(h1), o[np.minimum(j, len(h1) - 1)], np.nan)
    b["day"] = b["g"]
    return b


def series_for_delay(h1dir, k):
    bs = {c: daily_series_delayed(h1dir, c, k) for c in ["BTC", "ETH"]}
    for c in bs:
        bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
    pos = {c: R.tsmom(bs[c], 60) for c in bs}
    main = R.combine([R.backtest(bs[c], pos[c], R.HALF[c]) for c in bs])
    bh = R.combine([R.backtest(bs[c], np.ones(len(bs[c])), R.HALF[c]) for c in bs])
    return main, bh


def final_stats(p):
    x = p[(p.index >= FINAL[0]) & (p.index < FINAL[1])]
    if len(x) < 20:
        return None
    eq = (1 + x).cumprod()
    return dict(sharpe=round(float(x.mean() / x.std() * np.sqrt(252)), 2) if x.std() > 0 else 0.0,
                max_dd=round(float((eq / eq.cummax() - 1).min()), 3), total=round(float(eq.iloc[-1] - 1), 3))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h1", required=True); a = ap.parse_args()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    rows = []
    for k in DELAYS:
        m, b = series_for_delay(a.h1, k)
        sm, sb = R.stats(m, "S23"), R.stats(b, "BH")
        rows.append(dict(delay_h=k, sharpe=round(sm["sharpe"], 3), max_dd=round(sm["max_dd"], 3), cagr=round(sm["cagr"], 3), t=round(sm["t"], 2),
                         bh_sharpe=round(sb["sharpe"], 3), bh_max_dd=round(sb["max_dd"], 3),
                         final_S23=final_stats(m), final_BH=final_stats(b)))
        print(k, rows[-1], flush=True)
    df = pd.DataFrame(rows)
    r0 = df[df.delay_h == 0].iloc[0]
    assert abs(r0.sharpe - 0.88) < 0.01 and abs(r0.max_dd - (-0.614)) < 0.002, "Q529 を再現できない"
    ok = (df.sharpe > df.bh_sharpe) & (df.max_dd > df.bh_max_dd)
    robust = bool(ok[df.delay_h <= 24].all())
    weak = bool((df.sharpe <= df.bh_sharpe)[df.delay_h <= 6].any())
    verdict = "頑健" if robust else ("弱い" if weak else "中間")
    r24 = df[df.delay_h == 24].iloc[0]
    res = dict(qid="Q766", verdict=verdict, cells=len(DELAYS), n_ok_le24=int(ok[df.delay_h <= 24].sum()),
               sharpe_0=float(r0.sharpe), sharpe_24=float(r24.sharpe),
               drop_24_pct=round(float(1 - r24.sharpe / r0.sharpe) * 100, 1), rows=rows)
    json.dump(res, open(os.path.join(HERE, "results", "result_q766.json"), "w"), ensure_ascii=False, indent=1, default=str)
    df.drop(columns=["final_S23", "final_BH"]).assign(
        final_S23_sharpe=[r["final_S23"]["sharpe"] if r["final_S23"] else None for r in rows],
        final_BH_sharpe=[r["final_BH"]["sharpe"] if r["final_BH"] else None for r in rows],
        final_S23_total=[r["final_S23"]["total"] if r["final_S23"] else None for r in rows]).to_csv(
        os.path.join(HERE, "results", "surface_q766.csv"), index=False)
    print("判定:", verdict, f"k<=24 で条件を満たすセル {res['n_ok_le24']}/7・k=24 のシャープは k=0 から {res['drop_24_pct']}% 落ち")


if __name__ == "__main__":
    main()
