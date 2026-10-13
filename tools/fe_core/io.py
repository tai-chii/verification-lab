# -*- coding: utf-8 -*-
"""引数と結果の書き出し。write_result の出力先は呼び出し元スクリプトの results/（雛形の OUT と同じ）。
レビュー（2026-10-13・Opus）M7 を反映: np.bool_ を bool に、NaN は None に、同秒の上書きを防ぐ、here を明示できる。"""
import argparse
import datetime as _dt
import json
import math
import os

import numpy as np
import pandas as pd

from ._paths import SEED, script_dir


def parse_args(default_B=500, extra=None, default_seed=SEED, argv=None):
    """共通の引数（--B 帰無の回数、--smoke、--seed）。
    使う場面: main の最初。検証固有の引数は extra(ap) で足す
    入力: default_B（既定 500＝改善判定.md の既定）、extra: ArgumentParser を受けて add_argument する関数、default_seed、argv（テスト用）
    返り値: argparse.Namespace
    禁止: 事前登録した B・seed を結果を見てから変えない
    段階: 共通
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=default_B, help="帰無の回数")
    ap.add_argument("--smoke", action="store_true", help="合成データで経路の確認（判定に使わない）")
    ap.add_argument("--seed", type=int, default=default_seed)
    if extra:
        extra(ap)
    return ap.parse_args(argv)


def _json_default(o):
    """numpy・Timestamp を JSON にできる形へ。
    使う場面: write_result の内部。json.dump(default=_json_default)
    入力: o: 任意のオブジェクト
    返り値: bool / int / float / list / str（NaN は None）
    禁止: —
    段階: 保存
    """
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp, _dt.datetime, _dt.date)):
        return str(o)
    return str(o)


def sanitize(o):
    """結果 dict を JSON に安全な形へ再帰的に直す（NaN/inf → None、np.bool_ → bool、np.float64 → float、tuple → list）。
    使う場面: write_result の内部。json.dumps(allow_nan=False) を通す前
    入力: o: dict / list / スカラー
    返り値: 同じ構造
    禁止: —
    段階: 保存
    """
    if isinstance(o, dict):
        return {str(k): sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, np.ndarray):
        return [sanitize(v) for v in o.tolist()]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, (pd.Timestamp, _dt.datetime, _dt.date)):
        return str(o)
    return o


def write_result(qid, res, smoke, extra_csv=None, out_dir=None, here=None):
    """results/<qid>_result_<ts>.json（smoke は smoke_ 接頭辞）と任意の CSV を書く。既存のファイルは上書きしない。
    使う場面: run の返り値を main で保存する。1 回の実行で 1 回
    入力: qid、res: dict、smoke: bool、extra_csv: {名前: DataFrame}、out_dir: 省略で <here>/results、here: 呼び出し元の __file__ のフォルダ（省略で sys.argv[0] のフォルダ。Runner や Jupyter からは必ず渡す）
    返り値: 書いた JSON のパス
    禁止: 結果を上書きしない（同じ秒なら _1, _2 を付ける）。巨大な配列を JSON に入れない（CSV へ）。res に qid/smoke/generated を入れない（ここで付ける）
    段階: 保存
    """
    here = here or script_dir()
    out = out_dir or os.path.join(here, "results")
    os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    stem = f"{pre}_result_{ts}"; path = os.path.join(out, stem + ".json"); k = 0
    while os.path.exists(path):
        k += 1; stem = f"{pre}_result_{ts}_{k}"; path = os.path.join(out, stem + ".json")
    body = {k2: v for k2, v in res.items() if k2 not in ("qid", "smoke", "generated")}
    res = sanitize({"qid": qid, "smoke": bool(smoke), "generated": ts, **body})
    with open(path, "x", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=_json_default, allow_nan=False)
    print("wrote", _rel(path, here))
    if extra_csv is not None:
        suffix = ts if k == 0 else f"{ts}_{k}"
        for name, df in extra_csv.items():
            cp = os.path.join(out, f"{pre}_{name}_{suffix}.csv"); df.to_csv(cp, index=False); print("wrote", _rel(cp, here))
    return path


def _rel(p, here):
    try:
        return os.path.relpath(p, here)
    except ValueError:  # Windows で別ドライブ
        return p
