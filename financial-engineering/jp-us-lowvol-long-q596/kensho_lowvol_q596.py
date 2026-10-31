# -*- coding: utf-8 -*-
"""Q596 日本株・米国株の低ボラ買い（過去だけの β で市場ヘッジ）。事前登録: 事前登録_q596.md（変更禁止）。
【判定】フォワード候補: PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または全期間平均 ≤ 0。それ以外: 未確定。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_lowvol_q596.py [--B 200]"""
import argparse, datetime, importlib.util, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); sys.path.insert(0, os.path.join(FE, "..", "tools"))
import composite_gate as G
_s = importlib.util.spec_from_file_location("base578", os.path.join(FE, "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py")); B = importlib.util.module_from_spec(_s); _s.loader.exec_module(B)
FRAC, LOOK, WIN, MINP, HEDGE = 0.10, 252, 504, 252, 0.01 / 252


def legs(R, months, sigs, cost, shift=0):
    n = len(months); rows = []; prev = set()
    for j in range(n):
        t, e, x, el = months[j]; v = sigs[(j - shift) % n].reindex(el).dropna()
        if len(v) < B.MIN_NAMES: continue
        q = max(1, int(len(v) * FRAC)); L = list(v.sort_values().index[:q]); days = R.loc[(R.index > e) & (R.index <= x)]
        if not len(days): continue
        lg = days[L].mean(axis=1).copy(); mk = days[[c for c in v.index if c in days.columns]].mean(axis=1); turn = len(set(L) ^ prev) / (2 * q)
        lg.iloc[0] -= 2 * cost * turn; rows.append(pd.DataFrame({"long": lg, "mkt": mk, "turn": turn})); prev = set(L)
    return pd.concat(rows)


def hedge(d):
    b = (d["long"].rolling(WIN, min_periods=MINP).cov(d["mkt"]) / d["mkt"].rolling(WIN, min_periods=MINP).var()).shift(1).fillna(1.0)
    return d["long"] - b * d["mkt"], b


def stats(x):
    a, b = x[x.index < B.SPLIT], x[x.index >= B.SPLIT]; p = x[x > 0].sum(); n = -x[x < 0].sum(); r = x[x.index >= "2019-01-01"]; eq = x.cumsum()
    return dict(n_days=int(len(x)), first=str(x.index.min().date()), last=str(x.index.max().date()), mean_bp=1e4 * float(x.mean()), t_nw=float(B.nw_t(x)), sharpe=float(x.mean() / x.std() * np.sqrt(252)), pf=float(p / n), h1_bp=1e4 * float(a.mean()), h2_bp=1e4 * float(b.mean()), h1_ty=float(B.annual_t(a)), h2_ty=float(B.annual_t(b)), maxdd_pct=100 * float((eq - eq.cummax()).min()), since2019_bp=1e4 * float(r.mean()), since2019_t=float(B.nw_t(r)),
                hedge_cost_bp=1e4 * float((x - HEDGE).mean()), hedge_cost_t=float(B.nw_t(x - HEDGE)), by_year_pct={str(y): round(100 * float(v), 1) for y, v in x.groupby(x.index.year).sum().items()})


def verdict(s, z, c):
    if s["pf"] >= 1.05 and s["t_nw"] >= 1.5 and s["h1_bp"] > 0 and s["h2_bp"] > 0 and z >= 1.5 and c["関門"]["通過"]: return "フォワード候補"
    if z < 1 or s["mean_bp"] <= 0: return "棄却"
    return "未確定"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=200); ap.add_argument("--seed", type=int, default=20261101); a = ap.parse_args()
    rng = np.random.default_rng(a.seed); res = dict(qid="Q596", B=a.B, per={}); keep = {}
    for mkt in ("jp", "us"):
        cfg = B.CFG[mkt]; C, V = B.load_px(mkt, False, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5); months = B.build_months(C, V, cfg, LOOK); vol = R.rolling(60, min_periods=45).std()
        sigs = [vol.loc[t] for t, _, _, _ in months]; d = legs(R, months, sigs, cfg["cost"]); h, beta = hedge(d); st = stats(h); n = len(months); vals = []
        for i in range(a.B):
            dn = legs(R, months, sigs, cfg["cost"], shift=int(rng.integers(13, n - 13))); vals.append(float(hedge(dn)[0].mean()))
            if (i + 1) % 50 == 0: print(mkt, "帰無", i + 1, "/", a.B, flush=True)
        vals = np.array(vals); z = float((h.mean() - vals.mean()) / vals.std()); c = G.gate(h, f"{mkt} 低ボラ"); d0 = legs(R, months, sigs, 0.0); h0 = hedge(d0)[0]
        res["per"][mkt] = dict(stats=st, null=dict(null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(vals.std()), z=z, p=float((vals >= h.mean()).mean())), composite=c, verdict=verdict(st, z, c), コスト前_bp=1e4 * float(h0.mean()), 買いのみ=stats(d["long"]), β平均=float(beta[beta != 1].mean()), β最後=float(beta.iloc[-1]), 入れ替え=float(d.groupby(d.index.to_period("M"))["turn"].first().mean()), 月数=n)
        keep[mkt] = h; r = res["per"][mkt]
        print(mkt, r["verdict"], {q: round(st[q], 3) for q in ("mean_bp", "t_nw", "sharpe", "pf", "h1_bp", "h2_bp", "h1_ty", "h2_ty", "maxdd_pct", "since2019_bp", "since2019_t", "hedge_cost_t")}, "z", round(z, 2), "帰無", round(r["null"]["null_mean_bp"], 2), "±", round(r["null"]["null_sd_bp"], 2), "前", round(r["コスト前_bp"], 2), "β", round(r["β平均"], 2), "入替", round(r["入れ替え"], 2), flush=True)
        print("  composite", c["期間"], c["単体Sharpe"], c["相関"], c["合成Sharpe"], c["関門"], flush=True); print("  年別", st["by_year_pct"], flush=True)
    q = pd.read_csv(os.path.join(FE, "jp-us-ml-xsec-q582", "results", "daily_jp_q582.csv"), index_col=0, parse_dates=True)["ls"]; res["S30との相関_日本"] = float(keep["jp"].reindex(q.index).corr(q)); print("S30 との相関", round(res["S30との相関_日本"], 3), flush=True)
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); json.dump(res, open(os.path.join(HERE, "results", "result_q596.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float); pd.DataFrame(keep).to_csv(os.path.join(HERE, "results", "daily_q596.csv"))


if __name__ == "__main__":
    main()
