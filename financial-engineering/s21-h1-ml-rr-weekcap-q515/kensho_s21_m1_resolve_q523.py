# -*- coding: utf-8 -*-
"""Q523（記述・判定やり直しではない）: H1 の足の中で SL と TP の両方に触れた取引を、HistData 1 分足で順番判定して R を補正する。
対象: Q519 本体（WF 9 年）・Q521（WF 9 年）・Q522（仮判断 2 年）の取引表。
方法: 曖昧な足 j について、Dukascopy の足の始値からの距離（SL・TP）を、1 分足のその 1 時間の始値からの値動きと比べる（価格水準のずれに強い）。
     先に届いた方で決済。同じ 1 分で両方 → SL（保守的のまま）。1 分足が無い・本数不足（<30 本）→ SL のまま（判定不能として数える）。
使い方: python3 kensho_s21_m1_resolve_q523.py --h1 DIR --m1 DIR(<sym>_M1.parquet) --res DIR"""
import argparse, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W

SETS = {"Q519本体(WF)": "trades_q519_W-exp.csv", "Q521(WF)": "trades_q519_W-exp-mtf.csv", "Q522(仮判断)": "trades_val_q522.csv"}


def first_hit_m1(m1h, dr, d_sl, d_tp):
    """m1h: その 1 時間の 1 分足（bid）。d_sl/d_tp: 始値からの距離（価格差・符号つき）。返り値 'TP'/'SL'/None"""
    if m1h is None or len(m1h) < 30:
        return None
    o = m1h["open"].iloc[0]
    lo = (m1h["low"] - o).to_numpy(); hi = (m1h["high"] - o).to_numpy()
    if dr == 1:
        sl_hit = lo <= d_sl; tp_hit = hi >= d_tp
    else:
        sl_hit = hi >= d_sl; tp_hit = lo <= d_tp
    i_sl = np.argmax(sl_hit) if sl_hit.any() else 10 ** 9
    i_tp = np.argmax(tp_hit) if tp_hit.any() else 10 ** 9
    if i_sl == 10 ** 9 and i_tp == 10 ** 9:
        return None
    return "TP" if i_tp < i_sl else "SL"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h1", required=True); ap.add_argument("--m1", required=True); ap.add_argument("--res", required=True)
    a = ap.parse_args()
    trs = {lb: pd.read_csv(os.path.join(a.res, fn), parse_dates=["entry", "exit"]) for lb, fn in SETS.items()}
    for tr in trs.values():
        tr["R_m1"] = tr["R"].astype(float); tr["amb"] = ""
    for s in K.SYMS:                                   # 銘柄ごとに 1 分足を読む（メモリ節約）
        d = K.load(a.h1, s); _, _, D = K.labels(d, s)
        bo, bh, bl = d["open"].to_numpy(), d["high"].to_numpy(), d["low"].to_numpy()
        ao, ah, al = d["ask_open"].to_numpy(), d["ask_high"].to_numpy(), d["ask_low"].to_numpy()
        tpos = {t: j for j, t in enumerate(d["time"])}
        p = os.path.join(a.m1, f"{s}_M1.parquet")
        m = pd.read_parquet(p) if os.path.exists(p) else None
        mt = m["time"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy() if m is not None else None
        for lb, tr in trs.items():
            for k in np.where(tr["sym"].to_numpy() == s)[0]:
                row = tr.iloc[k]; dr, rr = K.ACTIONS[int(row["a"])]; i = int(row["i"]); e = i + 1
                j = tpos.get(row["exit"])
                if j is None:
                    continue
                P = ao[e] if dr == 1 else bo[e]; Dv = D[i]; SL = P - dr * Dv; TP = P + dr * rr * Dv
                if dr == 1:
                    both = (bl[j] <= SL) and (bh[j] >= TP) and not (bo[j] <= SL); o_ref = bo[j]
                else:
                    both = (ah[j] >= SL) and (al[j] <= TP) and not (ao[j] >= SL); o_ref = ao[j]
                if not both:
                    continue
                h0 = d["time"].iloc[j].tz_convert("UTC").tz_localize(None).to_datetime64(); h1 = h0 + np.timedelta64(1, "h")
                m1h = None
                if mt is not None:
                    lo_i, hi_i = np.searchsorted(mt, h0), np.searchsorted(mt, h1)
                    m1h = m.iloc[lo_i:hi_i]
                res = first_hit_m1(m1h, dr, SL - o_ref, TP - o_ref)
                tr.iat[k, tr.columns.get_loc("amb")] = res or "判定不能"
                if res == "TP":
                    tr.iat[k, tr.columns.get_loc("R_m1")] = rr + (row["R"] + 1.0)   # 保有コスト分を引き継ぐ
        del m
        print(f"  {s} 済", flush=True)
    out = {}
    for lb, tr in trs.items():
        tr.to_csv(os.path.join(a.res, SETS[lb].replace(".csv", "_m1.csv")), index=False)
        def pooled(col):
            if "fold" in tr.columns:
                p = pd.concat([K.daily(g.assign(R=g[col]), W.TS(Y), W.TS(Y + 1), g["r"].iloc[0]) for Y, g in tr.groupby("fold")])
            else:
                s0, s1 = pd.Timestamp("2023-10-01", tz="UTC"), pd.Timestamp("2025-10-01", tz="UTC")
                p = K.daily(tr.assign(R=tr[col]), s0, s1, tr["r"].iloc[0])
            return dict(mean_R=round(float(tr[col].mean()), 4), win=round(float((tr[col] > 0).mean()), 4), t=round(K.tstat(p), 2),
                        max_dd_pct=round(float(K.maxdd(p.to_numpy()) * 100), 2), total_pct=round(float(p.sum() * 100), 2))
        st = dict(n=len(tr), ambiguous=int((tr["amb"] != "").sum()), to_tp=int((tr["amb"] == "TP").sum()),
                  kept_sl=int((tr["amb"] == "SL").sum()), undecidable=int((tr["amb"] == "判定不能").sum()))
        out[lb] = dict(stat=st, before=pooled("R"), after=pooled("R_m1"))
        print(lb, json.dumps(out[lb], ensure_ascii=False), flush=True)
    json.dump(out, open(os.path.join(a.res, "result_q523.json"), "w"), ensure_ascii=False, indent=1)
    print("done")


if __name__ == "__main__":
    main()
