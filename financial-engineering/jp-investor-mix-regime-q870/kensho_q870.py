# -*- coding: utf-8 -*-
"""Q870 個人投資家の売買シェアで、日本株の横断戦略を 1 か月反転と 12-1 モメンタムの間で切り替える。
仕様は 事前登録.md（2026-11-27 固定）。土台は Q563（kensho_xs_momentum_q563.py）の関数をそのまま使う。
実行: 作業層/venv_equities/bin/python kensho_q870.py   （--smoke は合成データで経路だけ）
"""
import argparse, importlib.util, json, os, datetime
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.environ.get("WS") or os.path.expanduser("~/ワークスペース")
spec = importlib.util.spec_from_file_location("q563", os.path.join(HERE, "..", "jp-us-xs-momentum-q563", "kensho_xs_momentum_q563.py"))
q = importlib.util.module_from_spec(spec); spec.loader.exec_module(q)

INV = os.path.join(WS, "作業層", "大容量", "jpx_investor_type", "weekly_val_2016_202406.csv")
SEAL = pd.Timestamp("2024-07-01"); SPLIT = pd.Timestamp("2020-10-01")
COST, LOOKBACK, SKIP, REV = 0.0010, 252, 21, 21
NW_LAG, B, SEED, MIN_SHIFT = 21, 1000, 870, 6

def run_ls_tagged(R, sig_at, months, cost):
    """q.run_ls と同じ計算で、判断日 t の列を足す（月ごとに戦略を選ぶため）。"""
    rows = []; prevL = prevS = set()
    for (t, e, x, el) in months:
        v = sig_at(t, el).dropna()
        if len(v) < q.MIN_NAMES: continue
        o = np.argsort(v.values); k = max(1, int(len(v) * q.FRAC))
        L, S = list(v.index[o[-k:]]), list(v.index[o[:k]])
        days = R.loc[(R.index >= e) & (R.index <= x)]
        if not len(days): continue
        ls = (days[L].mean(axis=1) - days[S].mean(axis=1)).copy()
        mk = days[[c for c in v.index if c in days.columns]].mean(axis=1)
        turn = (len(set(L) ^ prevL) / k + len(set(S) ^ prevS) / k) / 2
        ls.iloc[0] -= 2 * cost * turn
        rows.append(pd.DataFrame({"t": t, "ls": ls, "mkt": mk, "turn": turn}))
        prevL, prevS = set(L), set(S)
    return pd.concat(rows)

def share_z(inv, cols):
    s = inv[[c + "_s" for c in cols] + [c + "_b" for c in cols]].sum(axis=1) / (inv["tot_s"] + inv["tot_b"])
    m = s.rolling(4).mean()
    z = (m - m.rolling(52).mean()) / m.rolling(52).std()
    return pd.Series(z.values, index=pd.to_datetime(inv["week_end"]))

def regime_at(z, t):
    ok = z[(z.index + pd.Timedelta(days=7)) <= t].dropna()
    return np.nan if not len(ok) else float(ok.iloc[-1])

def build_D(Rd, Md, state, add_cost=True):
    """state: dict 判断日 t -> +1（反転）/ -1（モメンタム）。日次の D=S−E と S, E を返す。"""
    out = []; prev = None
    for t in sorted(state):
        r, m = Rd[Rd.t == t], Md[Md.t == t]
        if not len(r) or not len(m) or len(r) != len(m): continue
        pick = r if state[t] > 0 else m
        S = pick["ls"].values.copy()
        if add_cost and prev is not None and state[t] != prev:
            S[0] -= 2 * COST * max(0.0, 1 - float(pick["turn"].iloc[0]))
        E = 0.5 * r["ls"].values + 0.5 * m["ls"].values
        out.append(pd.DataFrame({"t": t, "S": S, "E": E, "D": S - E, "R": r["ls"].values, "M": m["ls"].values}, index=r.index))
        prev = state[t]
    return pd.concat(out)

def summ(x):
    x = x.dropna(); h1, h2 = x[x.index < SPLIT], x[x.index >= SPLIT]
    return dict(mean_bp=1e4 * x.mean(), t_nw=q.nw_t(x, NW_LAG), n=int(len(x)), h1_bp=1e4 * h1.mean(), h2_bp=1e4 * h2.mean())

def smoke_inv(rng):
    w = pd.date_range("2014-01-10", periods=560, freq="W-FRI")
    d = {c: np.exp(rng.normal(20, 0.1, len(w))) for c in ["for_s", "for_b", "ind_s", "ind_b", "tb_s", "tb_b"]}
    d["tot_s"] = d["for_s"] + d["ind_s"] + d["tb_s"]; d["tot_b"] = d["for_b"] + d["ind_b"] + d["tb_b"]
    return pd.DataFrame(d).assign(week_end=w.strftime("%Y-%m-%d"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=B)
    a = ap.parse_args(); rng = np.random.default_rng(SEED)
    C, V = q.load_px("jp", a.smoke, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    inv = smoke_inv(rng) if a.smoke else pd.read_csv(INV)
    months = q.build_months(C, V, q.CFG["jp"], LOOKBACK); pos = {t: i for i, t in enumerate(C.index)}
    def sig_mom(t, el): i = pos[t]; return (C.iloc[i - SKIP] / C.iloc[i - LOOKBACK] - 1).reindex(el)
    def sig_rev(t, el): i = pos[t]; return (-(C.iloc[i] / C.iloc[i - REV] - 1)).reindex(el)
    Md = run_ls_tagged(R, sig_mom, months, COST); Rd = run_ls_tagged(R, sig_rev, months, COST)

    zs = {k: share_z(inv, cols) for k, cols in dict(ind=["ind"], for_=["for"], tb=["tb"]).items()}
    ts = sorted(set(Md.t) & set(Rd.t)); ts = [t for t in ts if t < SEAL]
    zi = {t: regime_at(zs["ind"], t) for t in ts}; ts = [t for t in ts if not np.isnan(zi[t])]
    st = {t: (1 if zi[t] > 0 else -1) for t in ts}
    D = build_D(Rd, Md, st); D = D[D.index < SEAL]
    mon = D.groupby("t")["D"].sum(); pf = mon[mon > 0].sum() / -mon[mon < 0].sum() if (mon < 0).any() else np.inf
    st_arr = np.array([st[t] for t in ts]); n = len(ts); null = []
    for _ in range(a.B):
        k = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT)); sh = np.roll(st_arr, k)
        null.append(build_D(Rd, Md, dict(zip(ts, sh)))["D"].mean())
    null = np.array(null); z = (D["D"].mean() - null.mean()) / null.std()
    res = dict(qid="Q870", n_months=n, frac_high_ind=float((st_arr > 0).mean()), n_switch=int((np.diff(st_arr) != 0).sum()),
               first_month=str(ts[0].date()), last_month=str(ts[-1].date()),
               D=summ(D["D"]), S=summ(D["S"]), E=summ(D["E"]), R=summ(D["R"]), M=summ(D["M"]), PF_monthly=float(pf),
               null=dict(B=a.B, mean_bp=1e4 * null.mean(), sd_bp=1e4 * null.std(), z=float(z)))
    # 記述（合否に使わない）
    mr = D.groupby("t")[["R", "M"]].sum(); mr["state"] = [st[t] for t in mr.index]
    res["desc_2x2_monthly_bp"] = (1e4 * mr.groupby("state")[["R", "M"]].mean()).round(1).to_dict()
    for k in ["for_", "tb"]:
        zk = {t: regime_at(zs[k], t) for t in ts}; s2 = {t: (-1 if zk[t] > 0 else 1) for t in ts if not np.isnan(zk[t])}
        res[f"desc_{k}"] = summ(build_D(Rd, Md, s2)["D"])
    mk = Md.groupby("t")["mkt"].sum().reindex(ts).shift(1); zz = pd.Series(zi).reindex(ts); ok = mk.notna()
    b = np.polyfit(mk[ok], zz[ok], 1); resid = zz[ok] - np.polyval(b, mk[ok])
    res["desc_resid_mkt"] = summ(build_D(Rd, Md, {t: (1 if resid[t] > 0 else -1) for t in resid.index})["D"])
    res["desc_nocost_D"] = summ(build_D(Rd, Md, st, add_cost=False)["D"])
    d = res["D"]
    if d["t_nw"] >= 1.5 and d["h1_bp"] > 0 and d["h2_bp"] > 0 and z >= 1.5 and res["S"]["mean_bp"] > 0: v = "支持"
    elif d["t_nw"] < 1.0 or d["mean_bp"] <= 0: v = "棄却"
    else: v = "未確定"
    res["verdict"] = v; res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); res["smoke"] = a.smoke
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True); tag = "smoke_" if a.smoke else ""
    json.dump(res, open(os.path.join(out, f"{tag}result_q870.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    D.to_csv(os.path.join(out, f"{tag}daily_q870.csv"))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))

if __name__ == "__main__": main()
