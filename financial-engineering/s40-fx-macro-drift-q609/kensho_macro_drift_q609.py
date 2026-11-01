# -*- coding: utf-8 -*-
"""Q609 米国の指標発表の反応のドル方向に 5 営業日持つ（S40 候補）。事前登録: 事前登録_q609.md（変更禁止）。
【判定】フォワード候補: PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または全期間平均 ≤ 0。それ以外: 未確定。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_macro_drift_q609.py [--B 500]。試験: --smoke [--inject bp]（合成の経路・判定に使わない）"""
import argparse, datetime, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path[:0] = [os.path.join(FE, "s21-real-swap-q592"), os.path.join(FE, "..", "tools")]
import kensho_s21_real_swap_q592 as C
import composite_gate as G
from fe_core.data import SEAL_END
from fe_core.metrics import nw_t

PAIRS = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "NZDUSD": -1, "USDJPY": 1, "USDCHF": 1, "USDCAD": 1}
SYMS = list(PAIRS); S = np.array([PAIRS[s] for s in SYMS], float)
H1 = os.path.join(WS, "作業層", "大容量", "market_data", "H1"); SEAL = pd.Timestamp(SEAL_END); SPLIT = pd.Timestamp("2018-01-01"); POST21 = pd.Timestamp("2021-01-01")
CLOCK = {"NFP": "08:30", "CPI": "08:30", "FOMC": "14:00"}; HOLD, Z_IN, NEV, MINEV, LAG = 120, 1.0, 24, 12, 10; SEED = 20261101


def bar_of(dates, hhmm):
    """NY の日付と時刻 → 発表の時刻を含む H1 足の始まり（UTC・tz なし）"""
    t = pd.to_datetime([f"{pd.Timestamp(d).date()} {hhmm}" for d in dates]).tz_localize("America/New_York").tz_convert("UTC").floor("h").tz_localize(None)
    return t


def events():
    d = pd.read_csv(os.path.join(HERE, "events_us.csv"), parse_dates=["date"]); return d[d["date"] < SEAL].sort_values("date").reset_index(drop=True)


def load_real():
    cl, op, rel = {}, {}, {}
    for s in SYMS:
        d = pd.read_parquet(os.path.join(H1, f"{s}.parquet"), columns=["time", "open", "close", "ask_close"]); t = pd.to_datetime(d["time"], utc=True).dt.tz_localize(None); k = t < SEAL   # 封印済み: SEAL で切る
        d, t = d[k].copy(), t[k]; d.index = pd.DatetimeIndex(t); cl[s], op[s] = d["close"], d["open"]
        rel[s] = ((d["ask_close"] - d["close"]) / d["close"]).clip(lower=0).groupby(d.index.normalize()).median()
    Cl = pd.DataFrame(cl).sort_index().ffill(limit=5); Op = pd.DataFrame(op).reindex(Cl.index); Op = Op.where(Op.notna(), Cl.shift(1))
    return Cl.dropna(), Op.reindex(Cl.dropna().index), rel


def synth(rng, ev, inject):
    idx = pd.date_range("2010-01-01", "2024-06-28 23:00", freq="h"); idx = idx[idx.weekday < 5]; n = len(idx)
    R = rng.normal(0, 6e-4, n)[:, None] + rng.normal(0, 6e-4, (n, len(SYMS)))
    pos = pd.Series(np.arange(n), index=idx)
    for k, g in ev.groupby("type"):
        e = pos.reindex(bar_of(g["date"], CLOCK[k])).dropna().astype(int).to_numpy()
        for x in e:
            j = rng.normal(0, 30e-4); R[x] += j
            if inject and x + 2 + HOLD < n: R[x + 2: x + 2 + HOLD] += np.sign(j) * inject * 1e-4 / HOLD
    Cl = pd.DataFrame(np.exp(np.cumsum(R * S, axis=0)), index=idx, columns=SYMS); return Cl, Cl.shift(1).fillna(1.0), {s: pd.Series(dtype=float) for s in SYMS}


class Panel:
    def __init__(self, Cl, Op, rel):
        self.idx = Cl.index; self.lc, self.lo = np.log(Cl.to_numpy(float)), np.log(Op.to_numpy(float)); n = len(Cl)
        self.R = np.vstack([np.zeros(len(SYMS)), np.diff(self.lc, axis=0)]) * S; self.CR = np.cumsum(self.R, axis=0); self.pos = pd.Series(np.arange(n), index=self.idx)
        D = self.idx.normalize(); dc = Cl.groupby(D).last(); self.sig = np.log(dc).diff().rolling(60, min_periods=40).std().shift(1); self.T = C.rate_table()
        self.c = pd.DataFrame({s: rel[s].reindex(dc.index).ffill().fillna(0.0).clip(lower=C.XMREL[s]) for s in SYMS}, index=dc.index)

    def calc(self, e, hold=HOLD):
        """足 e の配列 → 反応 u・重み w・コスト・スワップの部品。e+1 の終値で入り e+1+hold の終値で出る"""
        keep = (e + 1 + hold) < len(self.idx); e = e[keep]; dates = self.idx[e].normalize(); sg = self.sig.reindex(dates).to_numpy(float); ok = np.isfinite(sg).all(axis=1); e, dates, sg = e[ok], dates[ok], sg[ok]
        r = (self.lc[e + 1] - self.lo[e]) * S; u = np.mean(r / sg, axis=1); w = (1 / sg) / (1 / sg).sum(axis=1, keepdims=True); cost = (w * self.c.reindex(dates).to_numpy(float)).sum(axis=1)
        return e, dates, u, w, cost

    def net(self, e, dates, d, w, cost, hold=HOLD):
        """向き d（+ ＝ドル買い）の 1 件の損益: コスト前・スワップ・コスト後（対数・bp にしない）"""
        b0, b1 = e + 1, e + 1 + hold; gross = d * ((self.CR[b1] - self.CR[b0]) * w).sum(axis=1)
        days = dates.to_numpy("datetime64[D]").astype(np.int64); et, xt = self.idx[b0].tz_localize("UTC"), self.idx[b1].tz_localize("UTC"); nt = C.nights(et, xt, 2); sw = np.zeros(len(e))
        for i, s in enumerate(SYMS): sw += w[:, i] * C.annual(s, d * S[i], days, self.T) / 365 * nt
        return gross, sw, gross - cost + sw

    def series(self, b0, b1, d, w, cost, sw):
        pnl = np.zeros(len(self.idx))
        for k in range(len(b0)):
            a, b = b0[k] + 1, b1[k] + 1; pnl[a:b] += d[k] * (self.R[a:b] @ w[k]) + sw[k] / (b - a); pnl[a] -= cost[k] / 2; pnl[b - 1] -= cost[k] / 2
        D = self.idx.normalize(); D = D + pd.to_timedelta((self.idx.weekday == 6).astype(int), unit="D"); s = pd.Series(pnl, index=D).groupby(level=0).sum()
        return s.reindex(pd.bdate_range(self.idx[b0.min()].normalize(), self.idx[b1.max()].normalize())).fillna(0.0)


def signals(P, ev):
    rows, W = [], {}
    for k, g in ev.groupby("type"):
        t = bar_of(g["date"], CLOCK[k]); e = P.pos.reindex(t).dropna().astype(int).to_numpy(); e, dates, u, w, cost = P.calc(e); den = np.full(len(u), np.nan)
        for i in range(MINEV, len(u)): p = u[max(0, i - NEV):i]; den[i] = np.sqrt(np.mean(p ** 2))
        rows.append(pd.DataFrame(dict(type=k, e=e, date=dates, u=u, z=u / den, cost=cost)).assign(i=range(len(e)))); W[k] = w
    x = pd.concat(rows, ignore_index=True); x["w_i"] = x["i"]; return x.dropna(subset=["z"]).sort_values("e").reset_index(drop=True), W


def take(P, x, W, z_in=Z_IN, hold=HOLD, sign=1):
    t = x[x["z"].abs() >= z_in].copy()
    if hold != HOLD: t = t[(t["e"] + 1 + hold) < len(P.idx)]
    w = np.vstack([W[k][i] for k, i in zip(t["type"], t["w_i"])]); d = sign * np.sign(t["z"].to_numpy()); e = t["e"].to_numpy(); dates = pd.DatetimeIndex(t["date"]); cost = t["cost"].to_numpy()
    g, sw, n = P.net(e, dates, d, w, cost, hold); t["d"], t["gross"], t["swap"], t["net"] = d, g, sw, n
    return t, w


def stats(t):
    n = t["net"].to_numpy(); p, m = n[n > 0].sum(), -n[n < 0].sum(); D = pd.DatetimeIndex(t["date"])
    return dict(n=len(n), mean_bp=1e4 * float(n.mean()), gross_bp=1e4 * float(t["gross"].mean()), pf=float(p / m) if m > 0 else float("nan"), win=float((n > 0).mean()), trade_t=float(n.mean() / n.std(ddof=1) * np.sqrt(len(n))), h1_bp=1e4 * float(n[D < SPLIT].mean()), h2_bp=1e4 * float(n[D >= SPLIT].mean()), post21_bp=1e4 * float(n[D >= POST21].mean()) if (D >= POST21).any() else float("nan"))


def null(P, ev, t, B, rng):
    """採用した各件を、同じ月の発表なしの平日の同じ NY 時刻に置き換える。反応の向きに建てる（閾値なし）。"""
    evd = set(pd.DatetimeIndex(ev["date"]).normalize()); days = pd.bdate_range(ev["date"].min(), ev["date"].max()); days = days[~days.isin(list(evd))]; pool = {}
    for hhmm in sorted(set(CLOCK.values())):
        e = P.pos.reindex(bar_of(days, hhmm)); e = e.dropna().astype(int).to_numpy(); e2, dates, u, w, cost = P.calc(e)
        # calc は e を絞るので、NY の日付は足の時刻から戻す
        nyd = P.idx[e2].tz_localize("UTC").tz_convert("America/New_York").normalize().tz_localize(None); _, _, n = P.net(e2, dates, np.sign(u), w, cost); s = pd.Series(n, index=nyd); pool[hhmm] = {m: g.to_numpy() for m, g in s.groupby(s.index.to_period("M"))}
    tot = np.zeros(B); k = 0; size = []
    for typ, dt_ in zip(t["type"], pd.DatetimeIndex(t["date"])):
        m = pd.Timestamp(dt_).to_period("M"); a = pool[CLOCK[typ]].get(m)
        if a is None or not len(a): continue
        tot += a[rng.integers(0, len(a), B)]; k += 1; size.append(len(a))
    v = tot / k; return dict(平均_bp=1e4 * float(v.mean()), sd_bp=1e4 * float(v.std(ddof=1)), 使った件数=k, 候補の中央値=int(np.median(size))), v


def verdict(st, nw, z, c):
    if st["pf"] >= 1.05 and nw >= 1.5 and st["h1_bp"] > 0 and st["h2_bp"] > 0 and z >= 1.5 and c["関門"]["通過"]: return "フォワード候補"
    if z < 1 or st["mean_bp"] <= 0: return "棄却"
    return "未確定"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=500); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--inject", type=float, default=0.0); a = ap.parse_args()
    rng = np.random.default_rng(SEED); ev = events()
    Cl, Op, rel = synth(rng, ev, a.inject) if a.smoke else load_real()
    P = Panel(Cl, Op, rel); x, W = signals(P, ev); t, w = take(P, x, W); st = stats(t)
    e = t["e"].to_numpy(); ds = P.series(e + 1, e + 1 + HOLD, t["d"].to_numpy(), w, t["cost"].to_numpy(), t["swap"].to_numpy()); nw = float(nw_t(ds.to_numpy(), lag=LAG)); sh = float(ds.mean() / ds.std(ddof=1) * np.sqrt(252))
    nl, v = null(P, ev, t, a.B, rng); z = float((t["net"].mean() - v.mean()) / v.std(ddof=1)); nl["z"] = z; nl["p"] = float((v >= t["net"].mean()).mean())
    print("件数", {k: int(n) for k, n in t["type"].value_counts().items()}, "全事象", len(x), "同時保有", round(float(((ds != 0).mean())), 3), flush=True)
    print({k: round(q, 3) for k, q in st.items()}, "NW t", round(nw, 3), "Sharpe", round(sh, 3), "帰無", round(nl["平均_bp"], 2), "±", round(nl["sd_bp"], 2), "z", round(z, 2), flush=True)
    if a.smoke: print("smoke: 判定に使わない。結果は保存しない"); return
    c = G.gate(ds, "S40 指標ドリフト"); vd = verdict(st, nw, z, c); print("判定", vd, c["期間"], c["単体Sharpe"], c["相関"], c["合成Sharpe"], c["関門"], flush=True)
    desc = {}
    for k in sorted(t["type"].unique()): desc[k] = stats(t[t["type"] == k])
    desc["反転の向き"] = stats(take(P, x, W, sign=-1)[0]); desc["閾値なし"] = stats(take(P, x, W, z_in=0.0)[0])
    for h in (24, 72): desc[f"保有{h}本"] = stats(take(P, x, W, hold=h)[0])
    ys = t.groupby(pd.DatetimeIndex(t["date"]).year)["net"]; desc["年別_bp合計"] = {str(y): round(1e4 * float(q.sum()), 1) for y, q in ys}
    desc["反応の大きさ"] = dict(事象の絶対u平均=float(x["u"].abs().mean()), 平均コスト_bp=1e4 * float(t["cost"].mean()), 平均スワップ_bp=1e4 * float(t["swap"].mean()))
    res = dict(qid="Q609", B=a.B, seed=SEED, stats=st, nw_t=nw, sharpe=sh, null=nl, composite=c, verdict=vd, 記述=desc, generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    json.dump(res, open(os.path.join(HERE, "results", "result_q609.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    ds.rename("net").to_csv(os.path.join(HERE, "results", "daily_q609.csv")); t.drop(columns=["w_i", "i"]).to_csv(os.path.join(HERE, "results", "trades_q609.csv"), index=False)
    print(json.dumps(desc, ensure_ascii=False, default=float)[:2500])


if __name__ == "__main__":
    main()
