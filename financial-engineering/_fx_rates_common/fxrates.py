# -*- coding: utf-8 -*-
"""S38・S39 の共通部（2026-11-01・Opus）。事前登録 事前登録_q607.md・事前登録_q608.md の【データ】【コスト】【帰無】を実装する。
合図 t → t+1 の終値の後に確定 → t+2 の始値で約定。実スワップは Q592 の annual（暦の晩の倍率: 水曜 3・土日 0）。"""
import csv, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path[:0] = [os.path.join(FE, "s21-real-swap-q592"), os.path.join(FE, "..", "tools")]
import kensho_s21_real_swap_q592 as C
from fe_core import load_d1
from fe_core.data import SEAL_END
from fe_core.metrics import nw_t

SYMS = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "CADJPY", "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "GBPAUD", "GBPCAD", "GBPCHF", "AUDCAD"]
AREA = {"USD": "US", "EUR": "XM", "JPY": "JP", "GBP": "GB", "AUD": "AU", "CAD": "CA", "CHF": "CH"}
YIELDS = os.path.join(FE, "ml-core-eurusd-h1", "ext", "yields_2y_daily.csv"); SPECS = os.path.join(WS, "検証", "lab-ops", "trade", "winnote", "symbol_specs_20261101_0006.csv")
H1 = os.path.join(WS, "作業層", "大容量", "market_data", "H1"); SEAL = pd.Timestamp(SEAL_END); SPLIT = pd.Timestamp("2017-01-01"); POST21 = pd.Timestamp("2021-01-01")
B_DEFAULT, MIN_SHIFT, SEED, WED = 200, 120, 20261101, 2
LEGS = {"EURAUD": ("EURUSD", "AUDUSD", -1), "EURCAD": ("EURUSD", "USDCAD", 1), "GBPAUD": ("GBPUSD", "AUDUSD", -1), "GBPCAD": ("GBPUSD", "USDCAD", 1), "GBPCHF": ("GBPUSD", "USDCHF", 1)}


def fill_costs():
    """Q591 の実測に無いクロス 5 本のマークアップを MT5 の仕様 CSV から同じ換算で足す。スプレッドは実測のある FX の中央値（事前登録）。"""
    sys.path.insert(0, os.path.join(FE, "fx-traprepeat-q591"))
    specs = {r["name"].rstrip("#.").upper()[:6]: r for r in csv.DictReader(open(SPECS, encoding="utf-8"))}; T = C.rate_table(); now = np.array([np.datetime64("2026-10-31", "D").astype(np.int64)]); mid = lambda n: (float(specs[n]["bid"]) + float(specs[n]["ask"])) / 2
    med = float(np.median([C.XMREL[s] for s in SYMS if s in C.XMREL])); out = {}
    for s, (a, b, e) in LEGS.items():
        r = specs[s]; px = mid(a) * mid(b) ** e; d = float(C.rate(T, s[:3], now)[0] - C.rate(T, s[3:6], now)[0])
        if r["swap_mode_name"] != "POINTS": raise SystemExit(f"{s}: 換算できない型 {r['swap_mode_name']}")
        al, ash = float(r["swap_long"]) * float(r["point"]) / px * 365, float(r["swap_short"]) * float(r["point"]) / px * 365
        C.REAL[s] = dict(m_long=d - al, m_short=-d - ash); C.XMREL[s] = med; out[s] = dict(px=px, m_long=d - al, m_short=-d - ash)
    return dict(xmrel_median=med, 補った=out)


def yields_panel(smoke=False, rng=None):
    if smoke:
        idx = pd.date_range("2013-01-01", "2024-06-28"); return pd.DataFrame({a: 2 + np.cumsum(rng.normal(0, .03, len(idx))) for a in AREA.values()}, index=idx)
    y = pd.read_csv(YIELDS, index_col=0, parse_dates=True); y = y[y.index < SEAL]   # 封印済み: SEAL で切る
    return y.reindex(pd.bdate_range(y.index.min(), y.index.max())).ffill(limit=5)


def duka_rel(s):
    """Dukascopy の日次の相対スプレッド（H1 の ask があるペアだけ）。"""
    p = os.path.join(H1, f"{s}.parquet")
    if not os.path.exists(p): return None
    d = pd.read_parquet(p, columns=["time", "close", "ask_close"]); t = pd.to_datetime(d["time"], utc=True).dt.tz_localize(None); d = d[t < SEAL]; t = t[t < SEAL]   # 封印済み: SEAL で切る
    return ((d["ask_close"] - d["close"]) / d["close"]).clip(lower=0).groupby(t.dt.normalize().values).median()


def load_pair(s, Y, T, smoke=False, rng=None):
    d = load_d1(s, smoke=smoke, rng=rng); D = pd.DatetimeIndex(d["time"]).tz_localize(None).normalize(); o, c = d["open"].to_numpy(float), d["close"].to_numpy(float)
    keep = D >= pd.Timestamp("2010-01-01"); D, o, c = D[keep], o[keep], c[keep]; n = len(D); days = D.to_numpy("datetime64[D]").astype(np.int64)
    rel = np.full(n, C.XMREL[s]); dk = None if smoke else duka_rel(s)
    if dk is not None: rel = np.maximum(rel, np.nan_to_num(dk.reindex(D, method="ffill").to_numpy(float)))
    axis = pd.date_range(D.min(), D.max()); wd = axis.weekday.to_numpy(); w = np.where(wd >= 5, 0.0, np.where(wd == WED, 3.0, 1.0)); ax = axis.to_numpy("datetime64[D]").astype(np.int64)
    sw = {}
    for dr in (1, -1):                       # 暦の晩ごとにその日の政策金利差で積む。cum[i] は最初の足から足 i までの受け取り
        a = C.annual(s, np.full(len(ax), dr), ax, T) / 365 * w; cum = np.r_[0.0, np.cumsum(a)]; sw[dr] = cum[(days - ax[0]).astype(int)]
    yb, yq = (Y[AREA[x]].reindex(D).to_numpy(float) for x in (s[:3], s[3:6]))
    pb, pq = (C.rate(T, x, days) * 100 for x in (s[:3], s[3:6]))
    return dict(s=s, D=D, o=o, c=c, rel=rel, sw=sw, yb=yb, yq=yq, pb=pb, pq=pq, n=n)


def simulate(z, ok, z_in, z_out, z_stop, H, dirn=-1, no_reenter=False):
    """合図 t → t+2 始値で建てる。毎日の z で出口を判定し、判定 k の約定は k+2 始値。向き dirn=-1 は反転。手じまいの足から次の合図を探す（Q605 と同じ）。"""
    n = len(z); rows = []; t = 0; blocked = 0
    while t < n - 3:
        zt = z[t]
        if np.isfinite(zt) and abs(zt) <= z_out: blocked = 0
        if not np.isfinite(zt) or abs(zt) < z_in or not ok[t] or (no_reenter and blocked == np.sign(zt)): t += 1; continue
        dr = int(dirn * np.sign(zt)); e = t + 2; k = t + 1; x = e + H; why = "時間"
        while True:
            if k + 2 >= e + H: break
            if k >= n: x = n - 1; why = "終端"; break
            if np.isfinite(z[k]):
                if abs(z[k]) <= z_out: x = k + 2; why = "戻り"; break
                if abs(z[k]) >= z_stop: x = k + 2; why = "損切り"; break
            k += 1
        x = min(x, n - 1); rows.append((t, e, x, dr, why)); blocked = int(np.sign(zt)); t = x
    return rows


def evaluate(rows, p, m=1.0):
    """1 件ごとの損益と、日次の評価（値動き／スプレッド後／ネット）。m はスプレッド倍率。"""
    o, c, n = p["o"], p["c"], p["n"]; g, sp, sw = np.zeros(n), np.zeros(n), np.zeros(n); tr = []
    for t, e, x, dr, why in rows:
        g[e] += dr * (c[e] / o[e] - 1); g[e + 1:x] += dr * (c[e + 1:x] / c[e:x - 1] - 1); g[x] += dr * (o[x] / c[x - 1] - 1)
        cost = m * (p["rel"][e] + p["rel"][x]) / 2; sp[e] += m * p["rel"][e] / 2; sp[x] += m * p["rel"][x] / 2
        nights = np.diff(p["sw"][dr][e:x + 1]); sw[e + 1:x + 1] += nights; s_ = float(nights.sum()); gr = dr * (o[x] / o[e] - 1)
        tr.append(dict(sym=p["s"], ed=p["D"][e], xd=p["D"][x], dr=dr, h=x - e, why=why, gross=gr, swap=s_, spread=cost, R=gr + s_ - cost))
    idx = p["D"]
    return tr, pd.DataFrame({"gross": g, "price_net": g - sp, "net": g - sp + sw}, index=idx)


def book(P, Z, Ok, z_in, z_out, z_stop, H, dirn=-1, m=1.0, no_reenter=False):
    trs, day = [], {}; R = {}
    for s, p in P.items():
        r = simulate(Z[s], Ok[s], z_in, z_out, z_stop, H, dirn, no_reenter); R[s] = r; tr, dl = evaluate(r, p, m); trs += tr; day[s] = dl
    t = pd.DataFrame(trs); cols = ("gross", "price_net", "net")
    D = {k: pd.concat({s: d[k] for s, d in day.items()}, axis=1).fillna(0.0).sum(1) / len(P) for k in cols}
    op = {s: pd.Series(1, index=np.concatenate([P[s]["D"][a[1]:a[2]] for a in R[s]])).groupby(level=0).max() for s in P if R[s]}
    return t, D, R, int(pd.concat(op, axis=1).fillna(0).sum(1).max())


def pf(r):
    return float(r[r > 0].sum() / -r[r < 0].sum()) if (r < 0).any() else float("inf")


def yearly_t(s):
    y = s.groupby(s.index.year).sum(); return float(y.mean() / y.std(ddof=1) * np.sqrt(len(y))) if len(y) > 2 else float("nan")


def summary(t, D, maxopen=None, part=True):
    a, b = t[t["ed"] < SPLIT], t[t["ed"] >= SPLIT]; nd = D["net"]; yrs = (t["xd"].max() - t["ed"].min()).days / 365.25
    res = dict(件数=int(len(t)), 年件数=float(len(t) / yrs), 月件数=float(len(t) / yrs / 12), 平均保有=float(t["h"].mean()), コスト前_bp=float(t["gross"].mean() * 1e4), スワップ_bp=float(t["swap"].mean() * 1e4), スプレッド_bp=float(t["spread"].mean() * 1e4), mean_bp=float(t["R"].mean() * 1e4),
               PF=pf(t["R"]), NW_t=float(nw_t(nd.to_numpy())), NW_t_lag20=float(nw_t(nd.to_numpy(), lag=20)), 値動きNW_t=float(nw_t(D["price_net"].to_numpy())), 前半_bp=float(a["R"].mean() * 1e4), 後半_bp=float(b["R"].mean() * 1e4), 後半2021_bp=float(t[t["ed"] >= POST21]["R"].mean() * 1e4),
               前半コスト前_bp=float(a["gross"].mean() * 1e4), 後半コスト前_bp=float(b["gross"].mean() * 1e4), 年単位t_前=yearly_t(nd[nd.index < SPLIT]), 年単位t_後=yearly_t(nd[nd.index >= SPLIT]), Sharpe=float(nd.mean() / nd.std(ddof=1) * np.sqrt(252)), 同時保有最大=maxopen)
    if part:
        cat = np.where(t["sym"].str.contains("JPY"), "円絡み", np.where(t["sym"].str.contains("USD"), "ドル絡み", "クロス")); res["型別"] = {k: dict(n=int(len(g)), mean_bp=float(g["R"].mean() * 1e4), コスト前_bp=float(g["gross"].mean() * 1e4)) for k, g in t.groupby(cat)}
        res["出口"] = {k: dict(n=int(len(g)), mean_bp=float(g["R"].mean() * 1e4)) for k, g in t.groupby("why")}; res["年別_bp"] = {int(k): float(v * 1e4) for k, v in t.groupby(t["ed"].dt.year)["R"].mean().items()}
        res["ペア別_bp"] = {k: [int(len(g)), float(g["R"].mean() * 1e4)] for k, g in t.groupby("sym")}
    return res


def null_z(P, R, lo, B, obs):
    """ペアごとに建てた日を循環シフト（保有本数と向きはそのまま）。統計量はコスト後の 1 件平均。"""
    rng = np.random.default_rng(SEED); Y = {s: (np.array([r[1] for r in v]), np.array([r[2] - r[1] for r in v]), np.array([r[3] for r in v])) for s, v in R.items() if v}; null = np.empty(B)
    for b in range(B):
        tot, cnt = 0.0, 0
        for s, (e, h, dr) in Y.items():
            p = P[s]; L = p["n"] - lo[s] - h.max() - 1; sh = rng.integers(MIN_SHIFT, max(L - MIN_SHIFT, MIN_SHIFT + 1)); e2 = lo[s] + (e - lo[s] + sh) % L; x2 = e2 + h
            sw = np.where(dr > 0, p["sw"][1][x2] - p["sw"][1][e2], p["sw"][-1][x2] - p["sw"][-1][e2]); tot += (dr * (p["o"][x2] / p["o"][e2] - 1) + sw - (p["rel"][e2] + p["rel"][x2]) / 2).sum(); cnt += len(e)
        null[b] = tot / cnt
    return float((obs - null.mean()) / null.std(ddof=1)), float(null.mean() * 1e4), float(null.std(ddof=1) * 1e4)


def verdict(ck):
    if not all(ck[k] for k in "ABCD"): return "棄却"
    return "支持（フォワード候補）" if ck["E"] and ck["F"] else "未確定"


def dump(here, q, res, t, smoke):
    pre = "smoke_" if smoke else ""; t.to_csv(os.path.join(here, "results", f"{pre}trades_{q}.csv"), index=False)
    json.dump(res, open(os.path.join(here, "results", f"{pre}result_{q}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
