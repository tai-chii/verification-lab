# -*- coding: utf-8 -*-
"""Q520: Q519 本体の設計を日足・48 銘柄で。事前登録_q520.md。
使い方: python3 kensho_s21e_d1_48_wf_q520.py --d1 DIR(data_*_D1_fromH1.csv, spread_*.csv) --h1 DIR(指数回帰用 parquet) --out DIR"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q

FX = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "NZDUSD", "EURGBP", "AUDJPY", "CADJPY",
      "CHFJPY", "NZDJPY", "EURAUD", "EURCAD", "EURCHF", "GBPAUD", "GBPCAD", "GBPCHF", "AUDNZD", "AUDCAD"]
IDX13 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "EUSTX50", "AUS200", "HKG33", "SUI20", "NLD25"]
CMD = ["XAUUSD", "XAGUSD", "WTI", "BRENT", "COPPER", "NATGAS", "XPDUSD", "XPTUSD"]
BOND = ["BUND", "USTBOND", "UKGILT"]
CRYPTO = ["BTCUSD", "ETHUSD"]
SYMS = FX + IDX13 + CMD + BOND + CRYPTO
H1_15 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP", "XAUUSD", "US500", "USTECH", "GER40", "JPN225"]
CLS = {**{s: 0 for s in FX}, **{s: 1 for s in CMD}, **{s: 2 for s in IDX13}, **{s: 3 for s in BOND}, **{s: 4 for s in CRYPTO}}
HOLD = {0: 0.01, 1: 0.04, 2: 0.04, 3: 0.04, 4: 0.10}
GROUP = lambda s: ("円絡みFX" if s in FX and "JPY" in s else "円以外FX" if s in FX else "指数" if s in IDX13 else "商品" if s in CMD else "債券" if s in BOND else "暗号")

# Q515 の部品を日足用に差し替え
_daily_orig = K.daily
def _daily_d1(tr, start, end, r):
    """暗号資産の週末決済は翌月曜に計上（営業日の暦から落とさない）。"""
    if len(tr):
        ex = tr["exit"].dt.tz_convert("UTC")
        dow = ex.dt.dayofweek
        tr = tr.assign(exit=ex + pd.to_timedelta(np.where(dow >= 5, 7 - dow, 0), unit="D"))
    return _daily_orig(tr, start, end, r)
K.daily = _daily_d1
K.SYMS = SYMS
K.CLASS = CLS
K.HOLD_RATE = HOLD


def load_d1(d1_dir, sym):
    d = pd.read_csv(os.path.join(d1_dir, f"data_{sym}_D1_fromH1.csv"), parse_dates=["time"])
    d["time"] = d["time"].dt.tz_localize("UTC")
    d = d[d["high"] != d["low"]].sort_values("time").reset_index(drop=True)
    sp = pd.read_csv(os.path.join(d1_dir, f"spread_{sym}.csv"), parse_dates=["time"])[["time", "spread"]]
    sp["time"] = sp["time"].dt.tz_localize("UTC")
    sp["spread"] = sp["spread"].where(sp["spread"] > 0)
    sp["spr"] = sp["spread"].rolling(20, min_periods=1).median()
    d = pd.merge_asof(d, sp[["time", "spr"]], on="time", direction="backward")
    d["spr"] = d["spr"].ffill().bfill()
    for c in ["open", "high", "low", "close"]:
        d[f"ask_{c}"] = d[c] + d["spr"]
    d["volume"] = np.nan
    return d


def build(d1_dir):
    out = {}
    for s in SYMS:
        d = load_d1(d1_dir, s); R, X, D = K.labels(d, s); F = K.features(d, D, s)
        out[s] = dict(time=d["time"].reset_index(drop=True), R=R, X=X, F=F)
    print(f"  {len(out)} 銘柄", flush=True)
    return out


WF_START, WF_END = None, None


def pnl_by_exit(tr, start, end):
    """各トレードの損益 R×r を決済日に計上（年をまたぐ決済も数える）。start〜end の営業日。週末決済は翌月曜。"""
    days = pd.bdate_range(start.tz_convert(None).normalize(), (end - pd.Timedelta(days=1)).tz_convert(None).normalize())
    if len(tr) == 0:
        return pd.Series(0.0, index=days)
    ex = tr["exit"].dt.tz_convert("UTC"); dow = ex.dt.dayofweek
    day = (ex + pd.to_timedelta(np.where(dow >= 5, 7 - dow, 0), unit="D")).dt.tz_convert(None).dt.normalize()
    return (tr["R"] * tr["r"]).groupby(day.values).sum().reindex(days, fill_value=0.0)


def group_stats(tr, fn=GROUP):
    o = {}
    for k, x in tr.groupby(tr["sym"].map(fn))["R"]:
        o[k] = dict(n=int(len(x)), mean_R=round(float(x.mean()), 4), t=round(float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))), 2) if len(x) > 2 else None)
    return o


def sharpe(p):
    return float(p.mean() / p.std() * np.sqrt(252)) if p.std() > 0 else 0.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--d1", required=True); ap.add_argument("--h1", required=True)
    ap.add_argument("--out", required=True); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    print("ラベル・特徴量", flush=True); data = build(a.d1)
    folds, daily, trades = [], [], []
    for Y in W.YEARS:
        t0 = time.time(); s0, s1, si = W.TS(Y), W.TS(Y + 1), W.TS(Y - 1)
        m_in, _ = Q.train_window(data, si, None, step=1)
        tri = Q.rel_policy_trades(data, m_in, si, s0); pi = K.daily(tri, si, s0, 1.0)
        r = min(K.R_CAP, K.SIGMA_TARGET / pi.std()) if pi.std() > 0 else K.R_CAP
        models, ntr = Q.train_window(data, s0, None, step=1)
        tr = Q.rel_policy_trades(data, models, s0, s1).assign(fold=Y, r=r)
        p = pnl_by_exit(tr, s0, W.TS(W.YEARS[-1] + 1))  # この年に入ったトレードを決済日で（翌年以降の決済も含む）
        pe = pnl_by_exit(tr, s0, s1)
        f = dict(year=f"{Y}-10〜{Y+1}-09", n_train=ntr, r=r, inner=dict(n=len(tri), t=K.tstat(pi)),
                 V=dict(n_trades=int(len(tr)), mean_R=float(tr["R"].mean()) if len(tr) else None, t_daily=K.tstat(pe),
                        mean_daily_pct=float(pe.mean() * 100), max_dd_pct=float(K.maxdd(pe.to_numpy()) * 100),
                        sum_entries_pct=float((tr["R"] * r).sum() * 100), exit_after_year=float((tr["exit"] >= s1).mean()) if len(tr) else 0.0),
                 groups=group_stats(tr), sec=round(time.time() - t0))
        folds.append(f); daily.append(p); trades.append(tr)
        print(f"[D1-48] {f['year']}: r={r:.5f} n={f['V']['n_trades']} R={f['V']['mean_R']:.4f} 入った分の損益={f['V']['sum_entries_pct']:+.2f}% "
              f"翌年以降に決済={f['V']['exit_after_year']:.0%} | 内側 n={len(tri)} t={K.tstat(pi):.2f} | {f['sec']}s", flush=True)
    TR = pd.concat(trades)
    # 年別の正負は「その年に決済された損益」（pnl_by_exit の年区切り）で数える
    P = pnl_by_exit(TR, W.TS(W.YEARS[0]), W.TS(W.YEARS[-1] + 1))
    for f, Y in zip(folds, W.YEARS):
        pe = P[(P.index >= W.TS(Y).tz_convert(None)) & (P.index < W.TS(Y + 1).tz_convert(None))]
        f["V"].update(t_daily=K.tstat(pe), mean_daily_pct=float(pe.mean() * 100), max_dd_pct=float(K.maxdd(pe.to_numpy()) * 100)); TR.to_csv(os.path.join(a.out, "trades_q520_d1_48.csv"), index=False)
    ir = W.index_ret_daily(a.h1, W.TS(W.YEARS[0]), W.TS(W.YEARS[-1] + 1))
    j = pd.concat([P.rename("p"), ir.rename("m")], axis=1).dropna()
    at, beta = W.nw_alpha_t(j["p"].to_numpy(), j["m"].to_numpy())
    pos = sum(1 for f in folds if f["V"]["mean_daily_pct"] > 0)
    crit = dict(t_ge_2=K.tstat(P) >= 2, pos_years_ge_6=pos >= 6, alpha_t_ge_2=at >= 2, dd_ok=K.maxdd(P.to_numpy()) * 100 >= -6.0)
    nsat = sum(crit.values())
    # 15 銘柄だけ（同じ r で）
    tr15 = TR[TR["sym"].isin(H1_15)]
    p15 = pnl_by_exit(tr15, W.TS(W.YEARS[0]), W.TS(W.YEARS[-1] + 1))
    # H1 の Q519 本体と比較
    h1 = pd.read_csv(os.path.join(a.out, "trades_q519_W-exp.csv"), parse_dates=["entry", "exit"])
    ph1 = pd.concat([K.daily(g, W.TS(Y), W.TS(Y + 1), g["r"].iloc[0]) for Y, g in h1.groupby("fold")])
    res = dict(qid="Q520", run_at=time.strftime("%Y-%m-%d %H:%M"), folds=folds,
               pooled=dict(t=K.tstat(P), sharpe=sharpe(P), mean_daily_pct=float(P.mean() * 100), max_dd_pct=float(K.maxdd(P.to_numpy()) * 100),
                           total_pct=float(P.sum() * 100), n=int(len(TR)), mean_R=float(TR["R"].mean()), pos_years=pos, alpha_t_nw=at, beta=beta,
                           groups=group_stats(TR), criteria=crit, verdict=("支持" if nsat == 4 else ("未確定" if nsat == 3 else "棄却"))),
               d1_15syms=dict(t=K.tstat(p15), sharpe=sharpe(p15), n=int(len(tr15)), mean_R=float(tr15["R"].mean()) if len(tr15) else None,
                              max_dd_pct=float(K.maxdd(p15.to_numpy()) * 100)),
               h1_q519=dict(t=K.tstat(ph1), sharpe=sharpe(ph1), max_dd_pct=float(K.maxdd(ph1.to_numpy()) * 100), total_pct=float(ph1.sum() * 100)))
    res["d1_beats_h1"] = bool(res["pooled"]["t"] > res["h1_q519"]["t"] and res["pooled"]["sharpe"] > res["h1_q519"]["sharpe"])
    json.dump(res, open(os.path.join(a.out, "result_q520.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: res[k] for k in ["pooled", "d1_15syms", "h1_q519", "d1_beats_h1"]}, ensure_ascii=False, indent=1), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
