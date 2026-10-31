# -*- coding: utf-8 -*-
"""Q590 Q589 の買い側を過去だけの β で市場ヘッジして、フォワードに入れる関門で判定する。事前登録: 事前登録_q590.md（変更禁止）。再試行は 1 回だけ。
【判定】フォワード入り: PF ≥ 1.05 かつ NW t ≥ 1.5 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 1.5 かつ composite の 3 条件すべて。棄却: 帰無 z < 1 または全期間平均 ≤ 0。それ以外: 未確定。
実行（Mac）: 作業層/大容量/venv_forward/bin/python kensho_us_beta_hedged_q590.py [--B 200]"""
import argparse, datetime, importlib.util, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, "..")
_sp = importlib.util.spec_from_file_location("q589", os.path.join(FE, "us-ml-long-hedged-q589", "kensho_us_long_hedged_q589.py"))
Q = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(Q); M, B, G = Q.M, Q.B, Q.G
WIN, MINP = 504, 252


def hedge(lo, mk):
    b = (lo.rolling(WIN, min_periods=MINP).cov(mk) / mk.rolling(WIN, min_periods=MINP).var()).shift(1).fillna(0.0)
    return lo - b * mk, b


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=200); ap.add_argument("--seed", type=int, default=20261031); a = ap.parse_args()
    d = Q.series("us"); h, b = hedge(d["long_mkt"], d["mkt"]); s = Q.desc(h)
    s["beta_mean"], s["beta_last"] = float(b[b != 0].mean()), float(b.iloc[-1])
    cfg = M.CFG["us"]; rng = np.random.default_rng(a.seed)
    C, V = M.load("us", False, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    P = M.panel(C, V, M.build_months(C, V, cfg)); del V
    pr = pd.read_csv(os.path.join(FE, "jp-us-ml-xsec-q582", "results", "preds_us_q582.csv.gz"), parse_dates=["t"])
    pred = P[["t", "sym"]].merge(pr, on=["t", "sym"], how="left")["p"]; pred.index = P.index
    f = lambda k: (lambda x: hedge(x["long_mkt"], x["mkt"])[0].mean())(M.run_ls(R, P, pred, cfg["cost"], shift=k))
    obs = f(0); n = P.loc[pred.notna(), "t"].nunique(); vals = []
    for i in range(a.B):
        vals.append(f(int(rng.integers(13, n - 13))))
        if (i + 1) % 50 == 0: M.log("帰無", i + 1, "/", a.B)
    vals = np.array(vals); sd = vals.std(); nl = dict(B=a.B, obs_bp=1e4 * float(obs), null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(sd), z=float((obs - vals.mean()) / sd), p=float((vals >= obs).mean()))
    c = G.gate(h, "US 買いのみ β ヘッジ"); v = Q.verdict(s, nl["z"], c)
    res = dict(qid="Q590", machine_verdict=v, rule=__doc__.split("【判定】")[1].split("\n")[0], stats=s, null=nl, composite=c, config=dict(win=WIN, minp=MINP), generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    json.dump(res, open(os.path.join(HERE, "results", "result_q590.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    pd.concat([h.rename("hedged"), b.rename("beta")], axis=1).to_csv(os.path.join(HERE, "results", "daily_q590.csv"))
    print(json.dumps({k: v2 for k, v2 in s.items() if k != "cum_bp_by_year"}, ensure_ascii=False, default=float)); print("年別", s["cum_bp_by_year"]); print("帰無", nl)
    print("composite", json.dumps({k: c[k] for k in ("単体Sharpe", "相関", "合成Sharpe", "関門")}, ensure_ascii=False)); print("判定", v)


if __name__ == "__main__":
    main()
