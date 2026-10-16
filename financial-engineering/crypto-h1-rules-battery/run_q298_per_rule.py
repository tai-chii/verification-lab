#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q298 の実行補助（2026-10-16 追加・判定規則は変えない）。
Runner は main_param の 1 ルールにしか帰無を作らず、既定の判定（main の前後半 2 本）を使う。SPEC の判定は 3 ルール × 前後半 = 6 本の Holm なので、
main_param を 0/1/2 に替えて 3 回走らせ、各回の pre/post の perm_p（片側 greater）を集めて Holm（m=6）を本体の外で掛ける。
使い方: python3 run_q298_per_rule.py <0|1|2> [--B 500]   → 3 回の後 python3 run_q298_per_rule.py combine
"""
import dataclasses, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kensho_crypto_h1_rules_battery_q298 as M  # noqa: E402
from fe_core import Runner, holm  # noqa: E402

if sys.argv[1] == "combine":
    rows = []
    for i in range(3):
        fs = sorted(glob.glob(os.path.join(HERE, "results", f"Q298_r{i}_result_*.json")))
        r = json.load(open(fs[-1])); m = r["main"]
        for pn in ("pre", "post"):
            rows.append((i, pn, m[pn]["bp_net"], m[pn]["p_perm"], m["all"]["z"], os.path.basename(fs[-1])))
    adj = holm([x[3] for x in rows])
    out = []
    for (i, pn, bp, p, zall, f), a in zip(rows, adj):
        out.append({"rule": M.SPEC.params[i]["mode"], "period": pn, "bp_net": bp, "p_perm": p, "p_holm_m6": a, "z_all": zall, "file": f})
    sup = all(o["bp_net"] > 0 and o["p_holm_m6"] < 0.05 for o in out)
    rej = all(o["z_all"] < 1 for o in out)
    verdict = "支持" if sup else ("棄却: 3 ルールとも全期間 z<1" if rej else "未確定")
    json.dump({"rows": out, "verdict_spec_rule": verdict}, open(os.path.join(HERE, "results", "Q298_combined_holm_m6.json"), "w"), ensure_ascii=False, indent=1)
    for o in out: print(o)
    print("verdict(SPEC の 6 本 Holm):", verdict); sys.exit()
i = int(sys.argv[1])
spec = dataclasses.replace(M.SPEC, qid=f"Q298_r{i}", main_param=i)
Runner(spec, M.strategy, here=HERE).execute(argv=sys.argv[2:])
