# -*- coding: utf-8 -*-
"""Q594 日本株の決算後ドリフト（E1 決算の反応・E2 予想の上方修正）。事前登録: 事前登録_q594.md（変更禁止）。
【判定】フォワード候補: PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または全期間平均 ≤ 0。それ以外: 未確定。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_jp_pead_q594.py --check（件数だけ）／ 本番は引数なしで 1 回だけ。"""
import argparse, datetime, glob, gzip, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import composite_gate as G
J = os.path.join(WS, "作業層", "大容量", "jquants"); SPLIT = pd.Timestamp("2025-07-01"); HOLD, COST = 20, 0.0010; TOPN, MINPX = 1000, 100.0


def load_px():
    d = pd.read_parquet(os.path.join(J, "equities_daily.parquet"), columns=["Date", "Code", "C", "AdjC", "Va"])  # 封印済み: 無料層の範囲が封印期間と重なる。Q544・Q545 と同じ扱いでこの 1 回だけ判定（事前登録_q594.md）
    A = d.pivot(index="Date", columns="Code", values="AdjC").sort_index(); C = d.pivot(index="Date", columns="Code", values="C").reindex(A.index); V = d.pivot(index="Date", columns="Code", values="Va").reindex(A.index)
    R = A.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    adv = V.rolling(20, min_periods=15).mean().shift(1); rk = adv.rank(axis=1, ascending=False)
    E = (rk <= TOPN) & (C.shift(1) >= MINPX)
    mkt = R.where(E).mean(axis=1)
    return R, E, mkt


def load_events():
    rows = []
    for f in sorted(glob.glob(os.path.join(J, "fins", "*.json.gz"))):
        rows += json.load(gzip.open(f, "rt", encoding="utf-8"))
    d = pd.DataFrame(rows)[["DiscDate", "DiscTime", "Code", "DocType", "CurFYEn", "FNP"]]
    d["FNP"] = pd.to_numeric(d["FNP"], errors="coerce"); d["date"] = pd.to_datetime(d["DiscDate"])
    d = d.sort_values(["Code", "date", "DiscTime"]).reset_index(drop=True)
    return d


def react_index(d, days):
    """反応の日の位置。終わりの前の開示は当日、後は翌営業日。休日は次の営業日"""
    cut = np.where(d["date"] >= pd.Timestamp("2024-11-05"), "15:30:00", "15:00:00"); after = d["DiscTime"].to_numpy(str) >= cut
    i = days.searchsorted(d["date"].to_numpy()); same = (i < len(days)) & (days[np.minimum(i, len(days) - 1)] == d["date"].to_numpy())
    return np.where(same & after, i + 1, i)


def e1_e2(d, R, E, mkt):
    days = R.index; col = {c: k for k, c in enumerate(R.columns)}; r = react_index(d, days); RA, EA = R.to_numpy(), E.to_numpy(); out = []
    for k, x in enumerate(d.itertuples(index=False)):
        c = col.get(x.Code); i = r[k]
        if c is None or i >= len(days) or not EA[i, c] or not np.isfinite(RA[i, c]): continue
        out.append((k, i, c, x.Code, RA[i, c] - mkt.iloc[i], "FinancialStatements" in x.DocType))
    ev = pd.DataFrame(out, columns=["k", "i", "c", "code", "adj", "fin"])
    d2 = d.copy(); pv = d2[d2["FNP"].notna()].groupby(["Code", "CurFYEn"])["FNP"].shift(1); d2["prev"] = pv
    d2["rev"] = np.where(d2["prev"] > 0, (d2["FNP"] - d2["prev"]) / d2["prev"], np.nan); ev["rev"] = d2["rev"].to_numpy()[ev["k"].to_numpy()]
    fin = ev[ev["fin"]].drop_duplicates(["c", "i"]).sort_values("i").reset_index(drop=True); ii = fin["i"].to_numpy(); ad = fin["adj"].to_numpy(); q80 = np.full(len(fin), np.nan); q20 = np.full(len(fin), np.nan)
    for j in range(len(fin)):
        a = np.searchsorted(ii, ii[j] - 60); b = np.searchsorted(ii, ii[j])
        if b - a >= 100: q80[j], q20[j] = np.quantile(ad[a:b], [0.8, 0.2])
    fin["q80"], fin["q20"] = q80, q20
    return ev, fin


class Book:
    def __init__(self, R, E, mkt, hold):
        self.A = np.nan_to_num(R.to_numpy()); self.m = np.nan_to_num(mkt.to_numpy()); self.n = len(R); self.h = hold; self.ix = R.index

    def series(self, ei, ec):
        n, h = self.n, self.h; s = np.zeros(n); cnt = np.zeros(n); ent = np.zeros(n); ex = np.zeros(n)
        for e, c in zip(ei, ec):
            a, b = e + 1, min(e + 1 + h, n)
            if a >= n: continue
            s[a:b] += self.A[a:b, c]; cnt[a:b] += 1; ent[a] += 1
            if b <= n and b - 1 >= a: ex[b - 1] += 1
        ok = cnt >= 10; gross = np.where(ok, s / np.maximum(cnt, 1), 0.0); cost = np.where(ok, (ent + ex) * COST / np.maximum(cnt, 1), 0.0)
        return pd.DataFrame({"gross": gross, "cost": cost, "cnt": cnt, "ok": ok}, index=self.ix)


def nw(x, lag=21):
    x = np.asarray(x, float); n = len(x); e = x - x.mean(); s = e @ e
    for k in range(1, lag + 1): s += 2 * (1 - k / (lag + 1)) * (e[:-k] @ e[k:])
    return float(x.mean() / np.sqrt(s / n / n))


def stats(x):
    a, b = x[x.index < SPLIT], x[x.index >= SPLIT]; p = x[x > 0].sum(); n = -x[x < 0].sum(); eq = x.cumsum()
    return dict(n_days=int(len(x)), mean_bp=1e4 * float(x.mean()), t_nw=nw(x), sharpe=float(x.mean() / x.std() * np.sqrt(252)), pf=float(p / n), h1_bp=1e4 * float(a.mean()), h2_bp=1e4 * float(b.mean()), maxdd_pct=100 * float((eq - eq.cummax()).min()), by_half_year={str(k): round(1e4 * float(v), 1) for k, v in x.groupby(x.index.to_period("Q")).sum().items()})


def verdict(s, z, c):
    if s["pf"] >= 1.05 and s["t_nw"] >= 1.5 and s["h1_bp"] > 0 and s["h2_bp"] > 0 and z >= 1.5 and c["関門"]["通過"]: return "フォワード候補"
    if z < 1 or s["mean_bp"] <= 0: return "棄却"
    return "未確定"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); ap.add_argument("--B", type=int, default=500); a = ap.parse_args()
    R, E, mkt = load_px(); d = load_events(); ev, fin = e1_e2(d, R, E, mkt)
    L1 = fin[fin["adj"] >= fin["q80"]]; S1 = fin[fin["adj"] <= fin["q20"]]; L2 = ev[ev["rev"] >= 0.10].drop_duplicates(["c", "i"]); S2 = ev[ev["rev"] <= -0.10].drop_duplicates(["c", "i"])
    print("開示", len(d), "適格の事象", len(ev), "決算", len(fin), "E1 買い", len(L1), "売り", len(S1), "E2 買い", len(L2), "売り", len(S2), "日", R.index.min().date(), R.index.max().date(), "開示の範囲", d["date"].min().date(), d["date"].max().date(), flush=True)
    if a.check: return
    if os.path.exists(os.path.join(HERE, "results", "result_q594.json")): raise SystemExit("結果が既にある。この判定は 1 回だけ")
    B20 = Book(R, E, mkt, HOLD); B5 = Book(R, E, mkt, 5); rng = np.random.default_rng(20261101); res = dict(qid="Q594", 件数=dict(開示=len(d), 決算=len(fin), E1買い=len(L1), E1売り=len(S1), E2買い=len(L2), E2売り=len(S2)), sig={}); keep = {}
    mon = fin.assign(m=R.index.to_period("M")[fin["i"].to_numpy()]); pool = {m: g for m, g in mon.groupby("m")}
    for name, Lg, Sg in (("E1", L1, S1), ("E2", L2, S2)):
        A = B20.series(Lg["i"].to_numpy(), Lg["c"].to_numpy()); mk = pd.Series(np.where(A["ok"], B20.m, 0.0), index=A.index); use = A["ok"].cumsum() > 0; net = (A["gross"] - A["cost"] - mk)[use]; st = stats(net)
        lm = pd.Series(R.index.to_period("M")[Lg["i"].to_numpy()]).value_counts(); vals = []
        for b in range(a.B):
            ii, cc = [], []
            for m, cnt in lm.items():
                g = pool.get(m)
                if g is None or not len(g): continue
                ix = rng.integers(0, len(g), cnt); ii.append(g["i"].to_numpy()[ix]); cc.append(g["c"].to_numpy()[ix])
            N = B20.series(np.concatenate(ii), np.concatenate(cc)); vals.append(float((N["gross"] - N["cost"] - pd.Series(np.where(N["ok"], B20.m, 0.0), index=N.index))[use].mean()))
            if (b + 1) % 100 == 0: print(name, "帰無", b + 1, "/", a.B, flush=True)
        vals = np.array(vals); z = float((net.mean() - vals.mean()) / vals.std()); c = G.gate(net, f"PEAD {name}")
        Sx = B20.series(Sg["i"].to_numpy(), Sg["c"].to_numpy()); ls = (A["gross"] - A["cost"] - np.where(Sx["ok"], Sx["gross"] + Sx["cost"], 0.0))[use]; h5 = B5.series(Lg["i"].to_numpy(), Lg["c"].to_numpy()); n5 = (h5["gross"] - h5["cost"] - np.where(h5["ok"], B5.m, 0.0))[use]
        r = dict(stats=st, null=dict(B=a.B, null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(vals.std()), z=z, p=float((vals >= net.mean()).mean())), composite=c, verdict=verdict(st, z, c), コスト前_bp=1e4 * float((A["gross"] - mk)[use].mean()), コスト_bp=1e4 * float(A["cost"][use].mean()), 同時保有=float(A["cnt"][use].mean()),
                 記述=dict(LS=stats(ls), 買いのみ=stats((A["gross"] - A["cost"])[use]), 市場=stats(mk[use]), 保有5日=stats(n5)))
        res["sig"][name] = r; keep[name] = net
        print(name, r["verdict"], {q: round(st[q], 3) for q in ("n_days", "mean_bp", "t_nw", "sharpe", "pf", "h1_bp", "h2_bp", "maxdd_pct")}, "z", round(z, 2), "帰無", round(r["null"]["null_mean_bp"], 2), "±", round(r["null"]["null_sd_bp"], 2), "前", round(r["コスト前_bp"], 2), "コスト", round(r["コスト_bp"], 2), "同時", round(r["同時保有"], 1), flush=True)
        print("  composite", c["期間"], c["単体Sharpe"], c["相関"], c["合成Sharpe"], c["関門"], flush=True)
        print("  記述", {k: (round(v["mean_bp"], 2), round(v["t_nw"], 2), round(v["sharpe"], 2)) for k, v in r["記述"].items()}, "四半期", st["by_half_year"], flush=True)
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); json.dump(res, open(os.path.join(HERE, "results", "result_q594.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float); pd.DataFrame(keep).to_csv(os.path.join(HERE, "results", "daily_q594.csv"))


if __name__ == "__main__":
    main()
