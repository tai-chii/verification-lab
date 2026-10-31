# -*- coding: utf-8 -*-
"""Q592 S21 の学習外 28,888 件を XM の実スワップ・実スプレッドで計算し直す。事前登録: 事前登録_q592.md（変更禁止）。新しい学習はしない。
【判定】(B) 実スワップが PF ≥ 1.05 かつ 日次 t ≥ 1.5 かつ 前後半とも平均 > 0 → 実スワップに耐える。満たさない → ★。(C) 実スワップ＋XM 実スプレッドの平均 R ≤ 0 → XM のスタンダード口座では実弾にしない。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_s21_real_swap_q592.py"""
import datetime, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
S21 = os.path.join(FE, "s21-h1-ml-rr-weekcap-q515"); sys.path.insert(0, S21)
import kensho_s21_h1_ml_rr_q515 as K
H1 = os.path.join(WS, "作業層", "大容量", "market_data", "H1"); RATES = os.path.join(WS, "検証", "_データ", "raw", "rates")
REAL = json.load(open(os.path.join(FE, "fx-traprepeat-q591", "results", "swap_real_q591.json"), encoding="utf-8"))["実スワップの換算"]
XMREL = json.load(open(os.path.join(FE, "fx-traprepeat-q591", "results", "cost_table.json"), encoding="utf-8"))["rel"]
CFD_CCY = {"XAUUSD": "USD", "US500": "USD", "USTECH": "USD", "GER40": "EUR", "JPN225": "JPY"}; TRIPLE = {"XAUUSD": 2, "US500": 4, "USTECH": 4, "GER40": 4, "JPN225": 4}   # weekday（月=0）。FX・GOLD は水曜。CSV の swap_3days: 3=水・5=金
SPLIT = pd.Timestamp("2020-01-01", tz="UTC")


def rate_table():
    T = {}
    for c in ("USD", "JPY", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF"):
        d = pd.read_csv(os.path.join(RATES, f"policy_{c}.csv"), parse_dates=["date"]).dropna().sort_values("date")
        T[c] = (d["date"].to_numpy("datetime64[D]").astype(np.int64), d["policy_rate_pct"].to_numpy(float) / 100)
    return T


def rate(T, c, days):
    x, y = T[c]; return y[np.clip(np.searchsorted(x, days - 1, side="right") - 1, 0, len(y) - 1)]


def annual(s, dr, days, T):
    k = REAL[s]
    if s in CFD_CCY:
        d = rate(T, CFD_CCY[s], days) - k["rate_now"]; return np.where(dr > 0, k["long"] - d, k["short"] + d)
    diff = rate(T, s[:3], days) - rate(T, s[3:6], days); return np.where(dr > 0, diff - k["m_long"], -diff - k["m_short"])


def nights(et, xt, tri):
    """サーバーの日付をまたいだ晩の倍率の合計。土日の晩は無し。tri の曜日は 3 倍"""
    a = et.tz_convert("Europe/Athens").normalize().tz_localize(None); b = xt.tz_convert("Europe/Athens").normalize().tz_localize(None); out = np.zeros(len(a))
    for i, (u, v) in enumerate(zip(a, b)):
        n = 0.0; d = u
        while d < v:
            w = d.weekday(); n += 0.0 if w >= 5 else (3.0 if w == tri else 1.0); d += pd.Timedelta(days=1)
        out[i] = n
    return out


def ev(t, col):
    r = t[col]; g = t.groupby(t["xd"])[col].sum(); idx = pd.bdate_range(g.index.min(), g.index.max()); dl = g.reindex(idx).fillna(0.0)
    p = r[r > 0].sum(); n = -r[r < 0].sum(); a, b = r[t["et"] < SPLIT], r[t["et"] >= SPLIT]; eq = dl.cumsum()
    return dict(n=int(len(r)), mean_R=float(r.mean()), total_R=float(r.sum()), t_daily=float(dl.mean() / dl.std(ddof=1) * np.sqrt(len(dl))), pf=float(p / n), h1=float(a.mean()), h2=float(b.mean()), maxdd_R=float((eq - eq.cummax()).min()))


def main():
    T = rate_table(); tr = pd.read_csv(os.path.join(S21, "results", "trades_q534_E1.csv")); parts = []; chk = 0
    for s, g in tr.groupby("sym"):
        d = K.load(H1, s); bh, bl, bc = (d[c].to_numpy(float) for c in ("high", "low", "close"))
        trn = np.maximum(bh - bl, np.maximum(np.abs(bh - np.r_[bc[0], bc[:-1]]), np.abs(bl - np.r_[bc[0], bc[:-1]])))
        D = K.K_ATR * pd.Series(trn).rolling(24, min_periods=24).mean().to_numpy()
        g = g.copy(); e = g["i"].to_numpy() + 1; dr = np.array([K.ACTIONS[a][0] for a in g["a"]]); et = pd.to_datetime(g["entry"], utc=True); xt = pd.to_datetime(g["exit"], utc=True)
        tt = pd.to_datetime(d["time"].to_numpy()[e], utc=True); chk += int((pd.DatetimeIndex(tt) != pd.DatetimeIndex(et)).sum())
        P = np.where(dr > 0, d["ask_open"].to_numpy(float)[e], d["open"].to_numpy(float)[e]); Dv = D[g["i"].to_numpy()]
        hh = (xt - et).dt.total_seconds().to_numpy() / 3600; hold = K.HOLD_RATE[K.CLASS[s]] / 8760 * hh * P / Dv
        days = et.dt.tz_localize(None).to_numpy("datetime64[D]").astype(np.int64); ng = nights(pd.DatetimeIndex(et), pd.DatetimeIndex(xt), TRIPLE.get(s, 2))
        sw = annual(s, dr, days, T) / 365 * ng * P / Dv
        ex = (XMREL[s] * P - d["spr"].to_numpy(float)[e]) / Dv
        g["dr"], g["et"], g["hold"], g["swapR"], g["extra"], g["ng"], g["hh"] = dr, et, hold, sw, ex, ng, hh; g["xd"] = xt.dt.tz_localize(None).dt.normalize(); parts.append(g)
    t = pd.concat(parts, ignore_index=True); t["A"] = t["R"]; t["base"] = t["R"] + t["hold"]; t["B"] = t["base"] + t["swapR"]; t["C"] = t["B"] - t["extra"]; t["cls"] = t["sym"].map({**{s: "FX" for s in K.SYMS[:10]}, "XAUUSD": "金", "US500": "指数", "USTECH": "指数", "GER40": "指数", "JPN225": "指数"})
    res = dict(qid="Q592", 時刻の不一致=chk, n=int(len(t)), 平均保有時間=float(t["hh"].mean()), 晩の平均=float(t["ng"].mean()), モデルの保有コスト_R=float(t["hold"].mean()), 実スワップ_R=float(t["swapR"].mean()), 追加スプレッド_R=float(t["extra"].mean()))
    res["全体"] = {c: ev(t, c) for c in ("A", "base", "B", "C")}
    res["方向"] = {("買い" if k > 0 else "売り"): {c: ev(g, c) for c in ("A", "B", "C")} | dict(実スワップ_R=float(g["swapR"].mean())) for k, g in t.groupby("dr")}
    res["銘柄群"] = {k: {c: ev(g, c) for c in ("A", "B", "C")} | dict(実スワップ_R=float(g["swapR"].mean()), 追加スプレッド_R=float(g["extra"].mean())) for k, g in t.groupby("cls")}
    res["銘柄"] = {k: dict(n=int(len(g)), A=float(g["A"].mean()), B=float(g["B"].mean()), C=float(g["C"].mean()), swap=float(g["swapR"].mean()), extra=float(g["extra"].mean())) for k, g in t.groupby("sym")}
    b = res["全体"]["B"]; c = res["全体"]["C"]
    res["判定_B"] = "実スワップに耐える" if b["pf"] >= 1.05 and b["t_daily"] >= 1.5 and b["h1"] > 0 and b["h2"] > 0 else "★ 見直し"
    res["判定_C"] = "XM のスタンダード口座では実弾にしない" if c["mean_R"] <= 0 else "XM の総コストでも平均は正"
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    json.dump(res, open(os.path.join(HERE, "results", "result_q592.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items() if not isinstance(v, dict)})
    for c_, v in res["全体"].items(): print(c_, {k: round(x, 3) for k, x in v.items()})
    for grp in ("方向", "銘柄群"):
        for k, v in res[grp].items(): print(grp, k, "swap", round(v["実スワップ_R"], 4), {c_: (round(v[c_]["mean_R"], 4), round(v[c_]["t_daily"], 2), round(v[c_]["pf"], 3)) for c_ in ("A", "B", "C")})
    print(pd.DataFrame(res["銘柄"]).T.round(4).to_string())


if __name__ == "__main__":
    main()
