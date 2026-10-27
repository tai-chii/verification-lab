# -*- coding: utf-8 -*-
"""Q556 / S23: 日足の区切り時刻（0〜23 時 UTC）への依存。事前登録_q556.md と同一・変更禁止。
【判定】台地: シャープが同じ区切りの買って持つより高いセル ≥19/24 かつ 最大下落が浅いセル ≥19/24。尖り: シャープ ≤12/24。中間: それ以外。
多重比較の本数には足さない（頑健性の記述）。S23 の規則・停止線は変えない。
使い方: python3 run_q556.py --h1 DIR"""
import argparse, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "s22-crypto-ml-fintokei-q528"))
import crypto_core as C
import run_q529 as R

FINAL = (pd.Timestamp("2025-10-01"), pd.Timestamp("2026-10-01"))


def series_for_cut(h1dir, h):
    C.SHIFT = pd.Timedelta(hours=(24 - h) % 24)
    bs = {c: R.daily_series(h1dir, c) for c in ["BTC", "ETH"]}
    for c in bs:
        bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
    pos = {c: R.tsmom(bs[c], 60) for c in bs}
    main = R.combine([R.backtest(bs[c], pos[c], R.HALF[c]) for c in bs])
    bh = R.combine([R.backtest(bs[c], np.ones(len(bs[c])), R.HALF[c]) for c in bs])
    dev = lambda b: (b.index >= R.S0.tz_convert(None)) & (b.index < R.SEAL.tz_convert(None))
    extra = dict(in_market=round(float(np.mean([pos[c][dev(bs[c])].mean() for c in bs])), 3),
                 n_switch=int(sum(np.abs(np.diff(pos[c][dev(bs[c])])).sum() for c in bs)))
    return main, bh, extra


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
    for h in range(24):
        m, b, ex = series_for_cut(a.h1, h)
        sm, sb = R.stats(m, "S23"), R.stats(b, "BH")
        rows.append(dict(cut_utc=h, sharpe=round(sm["sharpe"], 3), max_dd=round(sm["max_dd"], 3), cagr=round(sm["cagr"], 3), t=round(sm["t"], 2),
                         bh_sharpe=round(sb["sharpe"], 3), bh_max_dd=round(sb["max_dd"], 3), **ex,
                         final_S23=final_stats(m), final_BH=final_stats(b)))
        print(h, rows[-1], flush=True)
    df = pd.DataFrame(rows)
    r21 = df[df.cut_utc == 21].iloc[0]
    assert abs(r21.sharpe - 0.88) < 0.01 and abs(r21.max_dd - (-0.614)) < 0.002, "Q529 を再現できない"
    n_sh = int((df.sharpe > df.bh_sharpe).sum()); n_dd = int((df.max_dd > df.bh_max_dd).sum())
    verdict = "台地" if (n_sh >= 19 and n_dd >= 19) else ("尖り" if n_sh <= 12 else "中間")
    rank21 = int((df.sharpe > r21.sharpe).sum()) + 1
    res = dict(qid="Q556", verdict=verdict, cells=24, n_sharpe_gt_bh=n_sh, n_dd_shallower=n_dd,
               sharpe_21utc=float(r21.sharpe), rank_21utc=rank21, sharpe_median=float(df.sharpe.median()),
               sharpe_min=float(df.sharpe.min()), sharpe_max=float(df.sharpe.max()),
               bh_sharpe_median=float(df.bh_sharpe.median()), max_dd_median=float(df.max_dd.median()),
               note_21_top3=("今の区切りは当たりの側" if rank21 <= 3 else ""), rows=rows)
    json.dump(res, open(os.path.join(HERE, "results", "result_q556.json"), "w"), ensure_ascii=False, indent=1, default=str)
    df.drop(columns=["final_S23", "final_BH"]).assign(
        final_S23_sharpe=[r["final_S23"]["sharpe"] if r["final_S23"] else None for r in rows],
        final_BH_sharpe=[r["final_BH"]["sharpe"] if r["final_BH"] else None for r in rows]).to_csv(os.path.join(HERE, "results", "surface_q556.csv"), index=False)
    print("判定:", verdict, f"シャープ>BH {n_sh}/24・DD 浅い {n_dd}/24・21 時は {rank21} 位")


if __name__ == "__main__":
    main()
