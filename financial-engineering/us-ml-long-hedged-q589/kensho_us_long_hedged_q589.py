# -*- coding: utf-8 -*-
"""Q589 米国株 横断 ML の「上位 10% 買い − 適格平均」を フォワードに入れる関門（2026-10-31）で判定する。事前登録: 事前登録_q589.md（変更禁止）。
【判定】フォワード入り: コスト後 PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または 全期間平均 ≤ 0。それ以外: 未確定。
【多重比較】株式無料層の横断 8 件目。新しい学習はしない（Q582 の保存済み予測と Q582/Q583 の日次 CSV を使う）。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_us_long_hedged_q589.py [--B 200]"""
import argparse, datetime, importlib.util, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); TOOLS = os.path.join(FE, "..", "tools")
sys.path.insert(0, TOOLS)
import composite_gate as G
_sp = importlib.util.spec_from_file_location("q582", os.path.join(FE, "jp-us-ml-xsec-q582", "kensho_ml_xsec_q582.py"))
M = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(M); B = M.B
SPLIT = "2017-01-01"; HEDGE = 0.01 / 252


def series(mkt):
    a = pd.read_csv(os.path.join(FE, "jp-us-ml-xsec-q582", "results", f"daily_{mkt}_q582.csv"), index_col=0, parse_dates=True)
    b = pd.read_csv(os.path.join(FE, "jp-ml-xsec-holdout-q583", "results", f"daily_{mkt}_q583.csv"), index_col=0, parse_dates=True)
    assert not a.index.intersection(b.index).size, "Q582 と Q583 の日付が重なる"
    return pd.concat([a, b]).sort_index()


def desc(x):
    x = x.dropna(); p = x[x > 0].sum(); n = -x[x < 0].sum(); h1, h2 = x[x.index < SPLIT], x[x.index >= SPLIT]; r19 = x[x.index >= "2019-01-01"]
    return dict(n_days=int(len(x)), first=str(x.index.min().date()), last=str(x.index.max().date()), mean_bp=1e4 * float(x.mean()), t_nw=float(B.nw_t(x)),
                sharpe=float(x.mean() / x.std() * np.sqrt(252)), pf=float(p / n), h1_bp=1e4 * float(h1.mean()), h2_bp=1e4 * float(h2.mean()),
                h1_ty=float(B.annual_t(h1)), h2_ty=float(B.annual_t(h2)), hedge_cost_mean_bp=1e4 * float((x - HEDGE).mean()), hedge_cost_t=float(B.nw_t(x - HEDGE)),
                since2019_bp=1e4 * float(r19.mean()), since2019_t=float(B.nw_t(r19)),
                cum_bp_by_year={str(y): round(1e4 * float(v), 1) for y, v in x.groupby(x.index.year).sum().items()})


def null_long(mkt, Bn, seed):
    cfg = M.CFG[mkt]; rng = np.random.default_rng(seed)
    C, V = M.load(mkt, False, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    P = M.panel(C, V, M.build_months(C, V, cfg)); del V
    pr = pd.read_csv(os.path.join(FE, "jp-us-ml-xsec-q582", "results", f"preds_{mkt}_q582.csv.gz"), parse_dates=["t"])
    pred = P[["t", "sym"]].merge(pr, on=["t", "sym"], how="left")["p"]; pred.index = P.index
    obs = M.run_ls(R, P, pred, cfg["cost"])["long_mkt"].mean()
    n = P.loc[pred.notna(), "t"].nunique(); vals = []
    for i in range(Bn):
        vals.append(M.run_ls(R, P, pred, cfg["cost"], shift=int(rng.integers(13, n - 13)))["long_mkt"].mean())
        if (i + 1) % 50 == 0: M.log(mkt, "帰無", i + 1, "/", Bn)
    vals = np.array(vals); sd = vals.std()
    return dict(B=Bn, obs_bp=1e4 * float(obs), null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(sd), z=float((obs - vals.mean()) / sd), p=float((vals >= obs).mean()), data_end=str(C.index.max().date()))


def verdict(s, z, c):
    g = c["関門"]; ok = s["pf"] >= 1.05 and s["t_nw"] >= 1.5 and s["h1_bp"] > 0 and s["h2_bp"] > 0 and z >= 1.5 and g["通過"]
    if ok: return "フォワード入り"
    if z < 1 or s["mean_bp"] <= 0: return "棄却"
    return "未確定"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=200); ap.add_argument("--seed", type=int, default=20261031); a = ap.parse_args()
    res = dict(qid="Q589", rule=__doc__.split("【判定】")[1].split("\n")[0], B=a.B, per_market={})
    for mkt in ["us", "jp"]:
        d = series(mkt); s = desc(d["long_mkt"]); M.log(mkt, "循環シフト帰無 B", a.B)
        nl = null_long(mkt, a.B, a.seed); c = G.gate(d["long_mkt"], f"{mkt} 買いのみ−適格平均")
        res["per_market"][mkt] = dict(stats=s, null=nl, composite=c, verdict=verdict(s, nl["z"], c) if mkt == "us" else "（記述・判定なし）")
        d["long_mkt"].to_csv(os.path.join(HERE, "results", f"daily_long_{mkt}_q589.csv"))
        json.dump(res, open(os.path.join(HERE, "results", "result_q589.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    res["machine_verdict"] = res["per_market"]["us"]["verdict"]; res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    json.dump(res, open(os.path.join(HERE, "results", "result_q589.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    for m, r in res["per_market"].items():
        print(m, json.dumps({k: v for k, v in r["stats"].items() if k != "cum_bp_by_year"}, ensure_ascii=False, default=float)); print("  年別", r["stats"]["cum_bp_by_year"]); print("  帰無", r["null"])
        print("  composite", json.dumps({k: r["composite"][k] for k in ("期間", "単体Sharpe", "相関", "合成Sharpe", "関門")}, ensure_ascii=False)); print("  判定", r["verdict"])


if __name__ == "__main__":
    main()
