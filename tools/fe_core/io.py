# -*- coding: utf-8 -*-
"""引数と結果の書き出し。write_result の出力先は呼び出し元スクリプトの results/（雛形の OUT と同じ）。"""
import argparse
import datetime as _dt
import json
import os

import numpy as np
import pandas as pd

from ._paths import SEED, script_dir


def parse_args(default_B=300, extra=None, default_seed=SEED, argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=default_B, help="帰無の回数")
    ap.add_argument("--smoke", action="store_true", help="合成データで経路の確認（判定に使わない）")
    ap.add_argument("--seed", type=int, default=default_seed)
    if extra:
        extra(ap)
    return ap.parse_args(argv)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp, _dt.datetime, _dt.date)):
        return str(o)
    return str(o)


def write_result(qid, res, smoke, extra_csv=None, out_dir=None):
    """results/<qid>_result_<ts>.json を書く。out_dir を省けば <スクリプトのフォルダ>/results。"""
    here = script_dir()
    out = out_dir or os.path.join(here, "results")
    os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    path = os.path.join(out, f"{pre}_result_{ts}.json")
    res = {"qid": qid, "smoke": smoke, "generated": ts, **res}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=_json_default)
    print("wrote", os.path.relpath(path, here))
    if extra_csv is not None:
        for name, df in extra_csv.items():
            cp = os.path.join(out, f"{pre}_{name}_{ts}.csv"); df.to_csv(cp, index=False); print("wrote", os.path.relpath(cp, here))
    return path
