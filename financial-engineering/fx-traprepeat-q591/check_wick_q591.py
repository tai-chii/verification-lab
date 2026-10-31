# -*- coding: utf-8 -*-
"""Q591 の確かめ（記述）: クロスの合成は足の実体だけで約定を判定する。本物の高安がある FX 8 本で F1 の規則を「本物の高安」「実体だけ」の 2 通りに回し、
実データの平均と帰無 z がどれだけ動くかを見る。F1 の判定（5 本が実体だけ）が、ヒゲを入れると変わりうるかの材料。判定には使わない。"""
import importlib.util, json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sp = importlib.util.spec_from_file_location("q591", os.path.join(HERE, "kensho_traprepeat_q591.py")); Q = importlib.util.module_from_spec(sp); sp.loader.exec_module(Q)
SY = ["EURGBP", "EURUSD", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "EURJPY", "AUDJPY"]; B = 200; ct = Q.cost_table(); R = Q.rate_series()


def body(x):
    y = dict(x); y["h"] = np.maximum(x["o"], x["c"]); y["l"] = np.minimum(x["o"], x["c"]); return y


def net(x, s):
    p = Q.prep(x); swl, sws = Q.swaps(s, p["days"], R); d, _, _ = Q.to_df(Q.run("F1", x, p, swl, sws, ct["rel"][s]), p["days"]); return d["g"] - d["c"] + d["s"]


res = {}; rng = np.random.default_rng(20261031); D = {s: Q.add_sig(Q.load_sym(s)) for s in SY}
for name, f in (("本物の高安", lambda x: x), ("実体だけ", body)):
    obs = pd.concat([net(f(D[s]), s) for s in SY], axis=1, sort=True).mean(axis=1); obs = obs[obs.index >= Q.EVAL]; vals = []
    for i in range(B):
        m = pd.concat([net(f(Q.synth(D[s], rng, D[s]["sig"])), s) for s in SY], axis=1, sort=True).mean(axis=1); vals.append(float(m[m.index >= Q.EVAL].mean()))
    vals = np.array(vals); res[name] = dict(obs_bp=1e4 * float(obs.mean()), t_nw=Q.nw(obs), null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(vals.std()), z=float((obs.mean() - vals.mean()) / vals.std()))
    print(name, {k: round(v, 3) for k, v in res[name].items()}, flush=True)
json.dump(res, open(os.path.join(HERE, "results", "check_wick_q591.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
