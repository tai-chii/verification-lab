# -*- coding: utf-8 -*-
"""S14（tick 出来高）・S15（利上げ局面の事前定義）の共通部（2026-10-22 /lab-plan ターミナル版 N=10・2 回目・Q411〜Q415）。
fe_core は書き換えない。`_s1x_common/s1x.py` の SealedRunner（封印・全設定の規程モード）と judge_gate を使い、次を足す薄い層:
  1. 出来高: `volume_ratio`（V の 20 日平均／250 日平均）、`volume_z`（log V の 250 日 z）、`vw_tsmom_pos`（出来高加重 TSMOM）。
     **出来高は 15 銘柄の H1（Dukascopy の tick 出来高）だけにある**ので kind="H1→D1"（h1_to_d1 が日次に合計する）。
     `_データ/raw/D1` の 48 銘柄 D1 には volume 列が無い（fetch の書き出しで落ちている）。値動きのない足を除いた後の H1 では出来高 0 は無い（EURUSD 全年 0%・US500 2012〜17 に 2〜18%）。
  2. 利上げ局面（政策金利 `_データ/raw/rates/policy_<CCY>.csv`・s09carry.load_policy を再利用）: `hike_within`（直近 W 暦日に上げが 1 回以上あったか）、
     `n_hiking`（8 中銀のうち上げた数）。時刻 t の合図には t−1 暦日までの情報だけ（rates/README の実施日ずれ対策）。
  3. `run_main`: kind="H1→D1" でもデータガードが動く（s1x.data_guard は kind をそのまま exists_sym に渡すので H1→D1 では必ず missing になる）。
土台に移したい候補: volume_ratio・volume_z・vw_tsmom_pos・hike_within・n_hiking（出来高族を signals.py に足すときは CATALOG に載せる）。
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(_HERE, "..", "_s1x_common"))
sys.path.insert(0, os.path.join(_HERE, "..", "_s09_common"))
from fe_core import syms_available, write_result  # noqa: E402
import s1x as X  # noqa: E402
import s09carry as S9  # noqa: E402

SEAL = X.SEAL
CCY8 = list(S9.CCY8)


# ---------------------------------------------------------------- 出来高
def volume_ratio(v, short=20, long=250):
    """出来高の短期平均／長期平均（参加の増減）。0 は欠測として NaN。先頭 long/2 本は NaN。"""
    s = pd.Series(np.asarray(v, float)).replace(0, np.nan)
    return (s.rolling(short, min_periods=short).mean() / s.rolling(long, min_periods=long // 2).mean()).values


def volume_z(v, window=250, min_periods=120):
    """log 出来高の t までの window 本（t を含む）での z。0 は欠測。"""
    s = np.log(pd.Series(np.asarray(v, float)).replace(0, np.nan))
    m = s.rolling(window, min_periods=min_periods).mean(); sd = s.rolling(window, min_periods=min_periods).std(ddof=1)
    return ((s - m) / sd).values


def vw_tsmom_pos(close, v, L=60, norm=250):
    """出来高加重 TSMOM: 直近 L 本の Σ ret_i × (v_i / v̄_norm) の符号。出来高の多い日の値動きを重く見る。先頭 L 本は 0。shift しない。"""
    ret = pd.Series(np.asarray(close, float)).pct_change()
    vol = pd.Series(np.asarray(v, float)).replace(0, np.nan)
    w = (vol / vol.rolling(norm, min_periods=norm // 2).mean()).fillna(1.0)   # 出来高が無い区間は等重み（素の TSMOM と同じ）
    s = (ret * w).rolling(L, min_periods=L).sum()
    return np.sign(np.nan_to_num(s.values))


# ---------------------------------------------------------------- 利上げ局面
def hike_within(ccy, times, window_days=365, lag_days=1, smoke=False, rng=None):
    """各 time について、t−lag_days 暦日までの window_days 暦日に政策金利の上げが 1 回以上あったか（bool 配列）。"""
    s = S9.load_policy(ccy, smoke, rng)
    up = (s.diff() > 0).astype(float)
    cnt = up.rolling(window_days, min_periods=1).sum()
    t = (pd.to_datetime(pd.Series(times)).dt.floor("D") - pd.Timedelta(days=lag_days)).values
    return cnt.reindex(t, method="ffill").fillna(0.0).values > 0


def n_hiking(times, window_days=180, lag_days=1, ccys=None, smoke=False, rng=None):
    """8 中銀（既定 CCY8）のうち、直近 window_days 暦日に利上げした数（int 配列）。"""
    ccys = ccys or CCY8
    out = np.zeros(len(times), int)
    for c in ccys:
        out += hike_within(c, times, window_days, lag_days, smoke, rng).astype(int)
    return out


# ---------------------------------------------------------------- 入口
def run_main(spec, strategy, here, min_syms, judge=None, null=None, summarize_extra=None, runner_holder=None):
    """--readme／--idea-row はガードを飛ばす。kind="H1→D1" は H1_dukascopy の存在で判定する。"""
    av = sys.argv[1:]
    kind = spec.kind.replace("H1→D1", "H1_dukascopy")
    if "--smoke" not in av and "--readme" not in av and "--idea-row" not in av:
        ok, missing = syms_available(spec.syms, kind=kind)
        if len(ok) < min_syms:
            res = {"status": "データ待ち", "n_ok": len(ok), "n_required": min_syms, "missing": missing,
                   "note": "データガード: 必要な銘柄が足りないため本番を実行しない。release で待ちに戻す。"}
            write_result(spec.qid, res, smoke=False, here=here)
            print(f"データ待ち: ok={len(ok)}/{len(spec.syms)}")
            sys.exit(2)
    r = X.SealedRunner(spec, strategy, judge=judge, null=null, summarize_extra=summarize_extra, here=here)
    if runner_holder is not None:
        runner_holder["obj"] = r
    r.execute()
