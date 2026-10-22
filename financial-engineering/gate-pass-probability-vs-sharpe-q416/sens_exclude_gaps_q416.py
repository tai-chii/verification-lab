#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q416 感度: data_health の gaps 14 銘柄を除いた 34 銘柄で本体を再実行（判定規則・本体は変更しない。結果は results/Q416_sens_nogaps_*.json）。"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kensho_gate_pass_probability_q416 as K
from fe_core import parse_args
GAPS = {'US500','USTECH','GER40','JPN225','UK100','FRA40','EUSTX50','HKG33','SUI20','NLD25','WTI','BRENT','BUND','USTBOND'}
K.X.WIDE48 = [s for s in K.X.WIDE48 if s not in GAPS]
args = parse_args(default_B=2000); rng = np.random.default_rng(args.seed)
res = K.run(args, rng)
print(res["machine_verdict"], res["required_sharpe"], res["observed_s07_fintokei"])
print({S: res["table"]["block"][S]["p_pass"] for S in res["table"]["block"]}, {S: res["table"]["block"][S]["p_dd_ok"] for S in res["table"]["block"]})
json.dump(res, open(os.path.join(HERE, "results", "Q416_sens_nogaps_%s.json" % res.get("generated", "x")), "w"), ensure_ascii=False, indent=1, default=str)
