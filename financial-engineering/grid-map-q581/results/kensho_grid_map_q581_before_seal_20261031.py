#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q581: グリッドの設定地図 — 26 銘柄 H1 × 間隔 5 × 本数 3 × 型 3 の 1,170 セルで、
              ボラの塊を保った帰無より良く、前後半ともコスト後に正のセルはあるか（Q580 の次段階・夜間計算）
================================================================================

【出典】
- 計画（事前登録）: Q580 の次段階・taichi「寝ている間に計算」（Opus 2026-10-30・設計とコード）。アイデア候補.md の Q581 の行。
- 前段: Q580（棄却）。FX8・k=0.5・N=20 の半々グリッドは純損益 −59 bp/年、年内並べ替え帰無に z −2.6。
  残った問い: (1) 実データが帰無より悪いのは「戻りやすさの不足（符号の依存）」か「ボラの塊（範囲外への逸脱）」か、
  (2) 間隔・本数・型（買いのみ／売りのみ）・銘柄（金・原油・指数・暗号資産）を変えれば勝てるセルはあるか。
- 主張カード: [[Brock1992-2_買いと売りの差はランダムウォークやGARCHでは説明できない]]（GARCH 型の帰無＝ボラを保つ帰無で比べる型）、
  [[Alonso2026-3_候補J個から最大を選ぶと全部不偏でも推定値は上に偏る]]（1,170 セルの最大を選ぶ偏り → Holm で抑える）。
- 関連知見: Q579、Q580、「為替の超短期の平均回帰は 2015 年以降の 1 時間足では消えた」。
- 先行研究チェック（WebSearch 2026-10-30・英語）: Q580 と同じ検索（"grid trading strategy foreign exchange backtest profitability random walk mean reversion academic paper"）。
  格子の理論（Virtus Interpress）と BTC のグリッド（Stevens）はあるが、多資産 H1 で「ボラを保つ帰無」と前後半・多重比較補正で設定地図を作った実証は見つからない（条件の穴）。

【仮説（測る前に固定）】
H1: 1,170 セルのうち少なくとも 1 つで、純損益（含み損込み・コスト後）がボラを保つ帰無より大きく（Holm 補正後の片側 p < 0.05）、
    かつ純損益の年単位 t が前後半とも ≥ 2。
H0: どのセルも帰無と区別できない（格子は符号の依存から稼げない）。

【データ】H1_dukascopy 26 銘柄: FX8・TREND7（XAUUSD・XAGUSD・WTI・UKOIL・US500・USTECH・BTCUSD）・暗号資産 11（BTC 重複を除き 18+…で計 26）。
前後半: FX・TREND7 は <2017／≥2017、暗号資産（BTCUSD を除く 10 本）はデータが 2017〜なので <2022／≥2022（Q264 と同じ境目）。BTCUSD は TREND7 側の境目（2017）。

【定義（1 通りに固定）】
- 年ごとに独立の 1 回（Q580 と同じ）: 起点 a = 年初の H1 終値（対数）。Δ = k × ATR20(D1・前年末) / 前年末の終値。年末に全決済。1000 本未満の年と前年末 ATR の無い年は除く。
- 型: both（起点の下に買い N 本・上に売り N 本）、buy（下の買い N 本だけ）、sell（上の売り N 本だけ）。利確 1 間隔・リピート。
- 経路は H1 の終値だけ、水準をまたいだら水準の価格で約定（Q580 と同じ。負の偏りは帰無も同じ扱い）。
- コスト: 約定ごとに片道（FX・TREND7 は段階 1 の COST_RT、暗号資産は往復 30bp の仮置き）。年末の強制決済も。スワップなし。
- 単位: グリッドの名目（水準数）に対する bp/年。
- 設定: k ∈ {0.25, 0.5, 1, 2, 4} × N ∈ {10, 20, 40} × 型 3 = 45 設定 × 26 銘柄 = 1,170 セル。

【帰無（2 種）】銘柄×年ごとに
- perm（記述・Q580 と同じ）: H1 の対数リターンを年内で並べ替え（自己相関もボラの塊も壊す）。
- vol（判定）: σ_t = H1 リターンの EWMA（λ=0.97・前の足までの情報）、z_t = r_t/σ_t を年内で並べ替え、r*_t = σ_t z*_t、年の合計が実データと同じになるよう定数を足す。
  ボラの塊（いつ荒れるか）は実データのまま、符号の並び（戻りやすさ・続きやすさ）だけを壊す。
- 1 回のパスで各 50 本。持ち時間いっぱいパスを積み増す（上限 B=2000）。判定に必要な最小は B=200（届かなければ未確定）。
- z = (観測の年平均 − 帰無の年平均の平均) / 帰無の年平均の標準偏差。片側 p は正規近似（1,170 本の Holm には経験 p の分解能が足りないため）。

【測るもの】
判定: 各セルの z_vol と Holm 補正後 p（m=1,170）、純損益の年単位 t（前後半）。
記述（判定外）: z_perm、z_perm − z_vol（ボラの塊の寄与）、FX8 の設定別平均、上位 20 セル、Q580 の主設定（k=0.5・N=20・both）の銘柄別分解。

【判定（事前固定・変更禁止）】
- 支持: Holm 補正後 p_vol < 0.05 かつ純損益の年単位 t が前後半とも ≥ 2 のセルが 1 つ以上。
- 棄却: Holm 補正後 p_vol < 0.05 のセルが 0（B ≥ 200 のとき）。
- 未確定: それ以外（帰無より良いセルはあるがコスト後に前後半とも正ではない／B < 200）。

【多重比較】1,170 セルを 1 つの族として Holm（片側 α=0.05）。前後半の t は追加の AND 条件（補正を緩めない）。

【捨てた案の数】約 6: 範囲を何年も固定（年の独立性が崩れる）、M15 で足の中の約定（3 銘柄しかない）、GARCH の当てはめ（重い・EWMA で代用）、
スワップを外部金利から（データ無し）、時間足の格子（H4 は H1 の終値の部分集合で情報が増えない）、k・N をさらに細かく（族が大きくなるだけ）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。FX・TREND7 のデータの終端は 2026-06、暗号資産は 2026-09。

【委託の確かめ方】設計・コードは Opus（2026-10-30）。計算は Mac の夜間コマンド（run_night_20261030c.sh）、判定と記録は翌朝の /lab（担当 opus）。
/lab の実行者は計算をやり直さない: results/Q581_result_*.json が無ければ `python3 kensho_grid_map_q581.py --analyze` だけを走らせる。

【実装】自己完結（共通の土台を埋め込み）。格子は水準×時刻の 2 次元配列でヒステリシスをベクトル化。spawn の Pool で銘柄ごとに並列。
途中結果は results/partial/ に銘柄×パスごとに保存し、同じコマンドで続きから。
実行: python3 kensho_grid_map_q581.py --hours 7（計算＋最後に分析）／--analyze（分析だけ）／--smoke（合成データ・経路確認）
"""

# ============================================================================= 共通の土台（各スクリプトに同じものを埋め込む・自己完結）
import argparse
import datetime as _dt
import itertools
import json
import math
import os
import sys
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # ワークスペース


def _p(*parts):
    """macOS 共有の NFD 名に対応（NFC で無ければ NFD で探す）。"""
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
OUT = os.path.join(HERE, "results")
FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
FX6 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD"]  # ドル建て先進国（Q019・Q054 と同じ）
TREND7 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL", "US500", "USTECH", "BTCUSD"]
SYMS = FX8 + TREND7
CRYPTO = ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "ADAUSD", "BCHUSD", "XLMUSD", "EOSUSD", "LNKUSD", "DOTUSD", "SOLUSD"]
# 往復コスト（価格単位・段階1の保守値。Q136〜Q190 と同じ表）
COST_RT = {"EURUSD": .0002, "GBPUSD": .0002, "AUDUSD": .0002, "USDCHF": .0002, "USDCAD": .0002,
           "USDJPY": .02, "EURJPY": .02, "GBPJPY": .02, "XAUUSD": 0.6,
           "XAGUSD": 0.04, "WTI": 0.06, "UKOIL": 0.06, "US500": 1.0, "USTECH": 3.0, "BTCUSD": 40.0}
CRYPTO_COST_RT_REL = 30e-4  # 暗号資産: 往復 30bp の仮置き（Q152 と同じ）
SPLIT_YEAR = 2017
SEED = 20261010
GROUPS = {"all15": SYMS, "fx8": FX8, "trend7": TREND7}


# ----------------------------------------------------------------------------- データ
def _read(path):
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def load_d1(sym, smoke=False, rng=None):
    """UTC 日足（D1_fromH1）。値動きのない足（high==low）は除く。列: time, open, high, low, close, ret, year"""
    if smoke:
        df = _smoke_ohlc(sym, rng, n=2600, freq="D", start="2015-01-01")
    else:
        df = _read(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"))
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    return df


def load_csv(name, smoke=False, rng=None, freq="h", n=20000, start="2015-01-01"):
    """任意の data_<name>.csv（H1/H4/M15/yahoo/ask）。"""
    if smoke:
        return _smoke_ohlc(name, rng, n=n, freq=freq, start=start)
    return _read(os.path.join(DATA_DIR, f"data_{name}.csv"))


def load_h1(sym, smoke=False, rng=None, n=60000, start="2015-01-01"):
    """UTC 1時間足（H1_dukascopy）。値動きのない足は除く。列: time, open, high, low, close, volume, ret, year, hour, dow"""
    df = load_csv(f"{sym}_H1_dukascopy", smoke, rng, freq="h", n=n, start=start)
    df = df[df["high"] != df["low"]].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    df["year"] = df["time"].dt.year
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    return df


def h1_to_d1(h1, cutoff_hour=0):
    """H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。"""
    t = h1["time"] - pd.Timedelta(hours=cutoff_hour)
    key = t.dt.floor("D")
    g = h1.groupby(key)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum() if "volume" in h1 else g["close"].size(), "nbars": g["close"].size()})
    d.index.name = "time"; d = d.reset_index()
    d = d[(d["high"] != d["low"]) & (d["nbars"] >= 6)].reset_index(drop=True)
    d["ret"] = d["close"].pct_change(); d["year"] = d["time"].dt.year
    return d


def _smoke_ohlc(sym, rng, n, freq, start):
    """合成データ（GBM）。判定には使わない。"""
    rng = rng or np.random.default_rng(SEED)
    t = pd.date_range(start, periods=n, freq=freq)
    r = rng.normal(0.0001, 0.006, n)
    c = 100.0 * np.exp(np.cumsum(r))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n)))
    v = np.abs(rng.lognormal(8, 0.5, n))
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v})


def exists_sym(sym, kind="D1_fromH1"):
    return os.path.exists(os.path.join(DATA_DIR, f"data_{sym}_{kind}.csv"))


def cost_bp_oneway(sym, close, rel=None):
    """片道コスト [bp]（価格に対する比）。rel を渡せば相対コスト（往復）を使う。"""
    if rel is not None:
        return np.full(len(close), rel / 2 * 1e4)
    return COST_RT[sym] / 2 / np.asarray(close, float) * 1e4


# ----------------------------------------------------------------------------- 合図と損益
def tsmom_pos(close, L):
    c = np.asarray(close, float)
    s = np.zeros(len(c))
    s[L:] = np.sign(c[L:] - c[:-L])
    return s


def sma_pos(close, n):
    c = pd.Series(np.asarray(close, float))
    m = c.rolling(n).mean().values
    s = np.sign(c.values - m)
    s[np.isnan(m)] = 0.0
    return s


def atr(high, low, close, n=20):
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    return pd.Series(tr).rolling(n).mean().values


def rsi(close, n):
    c = pd.Series(np.asarray(close, float))
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).values


def pnl_bp(pos, close, cost_oneway_bp):
    """pos[t] は t の終値で決めて t+1 のリターンに効く。pnl[t+1] = pos[t]*ret[t+1]*1e4 − |pos[t]−pos[t−1]|*片道[bp]。先頭は 0。"""
    c = np.asarray(close, float); pos = np.asarray(pos, float)
    ret = np.zeros(len(c)); ret[1:] = c[1:] / c[:-1] - 1
    held = np.r_[0.0, pos[:-1]]
    prev = np.r_[0.0, held[:-1]]
    cost = np.abs(held - prev) * np.r_[0.0, cost_oneway_bp[:-1]]
    return held * ret * 1e4 - cost


# ----------------------------------------------------------------------------- 統計
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def nw_t(x, lag=5):
    """Newey-West（Bartlett）の t。"""
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan")
    e = x - x.mean()
    s = (e ** 2).sum()
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] * e[:-k]).sum()
    se = math.sqrt(max(s, 1e-300)) / n
    return float(x.mean() / se) if se > 0 else float("nan")


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
    if len(x) < 3:
        return float("nan")
    rx = np.array(pd.Series(x).rank().values, float); ry = np.array(pd.Series(y).rank().values, float)
    rx -= rx.mean(); ry -= ry.mean()
    d = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def max_drawdown(pnl):
    cum = np.cumsum(np.asarray(pnl, float)); peak = np.maximum.accumulate(cum)
    return float((cum - peak).min()) if len(cum) else float("nan")


def sharpe_ann(pnl, per_year=252):
    x = np.asarray(pnl, float); x = x[np.isfinite(x)]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(per_year)) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def qlike(s2_pred, r2):
    """QLIKE 損失（小さいほど良い）。r2: 実現分散、s2_pred: 予測分散。"""
    s2 = np.asarray(s2_pred, float); r2 = np.asarray(r2, float)
    m = np.isfinite(s2) & np.isfinite(r2) & (s2 > 0) & (r2 > 0)
    return float(np.mean(r2[m] / s2[m] - np.log(r2[m] / s2[m]) - 1)) if m.sum() > 2 else float("nan")


def z_of(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null < obs).mean())


def perm_within(rng, x, groups):
    """groups（例: 年）の中で x を並べ替える。"""
    x = np.asarray(x, float).copy(); g = np.asarray(groups)
    for v in np.unique(g):
        idx = np.where(g == v)[0]
        x[idx] = x[rng.permutation(idx)]
    return x


def block_perm(rng, x, block):
    """block 本ごとの塊を並べ替える（塊の中の順序は保つ）。"""
    x = np.asarray(x, float); n = len(x); nb = int(math.ceil(n / block))
    order = rng.permutation(nb)
    out = np.concatenate([x[b * block:(b + 1) * block] for b in order])
    return out[:n]


def circ_shift(rng, x, min_shift=1):
    """循環シフト（合図とリターンの対応を壊し、合図の自己相関は保つ）。"""
    x = np.asarray(x, float); n = len(x)
    k = int(rng.integers(min_shift, max(min_shift + 1, n - min_shift)))
    return np.roll(x, k)


def holm(pvals):
    p = np.asarray(pvals, float); m = len(p); order = np.argsort(p); adj = np.empty(m)
    run = 0.0
    for i, k in enumerate(order):
        run = max(run, (m - i) * p[k]); adj[k] = min(1.0, run)
    return adj


def by_year_stats(df, col, year_col="year", y0=0, y1=9999):
    """年を単位にした平均と t（銘柄は年の中で平均してから）。df: year, sym, col。"""
    d = df[(df[year_col] >= y0) & (df[year_col] < y1)]
    if d.empty:
        return {"n_years": 0, "mean": float("nan"), "t": float("nan")}
    if "sym" in d.columns:
        yr = d.groupby([year_col, "sym"])[col].mean().groupby(level=0).mean()
    else:
        yr = d.groupby(year_col)[col].mean()
    yr = yr.dropna()
    return {"n_years": int(len(yr)), "mean": float(yr.mean()) if len(yr) else float("nan"), "t": tstat(yr.values)}


# ----------------------------------------------------------------------------- 入出力
def parse_args(default_B=300, extra=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=default_B, help="帰無の回数")
    ap.add_argument("--smoke", action="store_true", help="合成データで経路の確認（判定に使わない）")
    ap.add_argument("--seed", type=int, default=SEED)
    if extra:
        extra(ap)
    return ap.parse_args()


def write_result(qid, res, smoke, extra_csv=None):
    os.makedirs(OUT, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = f"smoke_{qid}" if smoke else qid
    path = os.path.join(OUT, f"{pre}_result_{ts}.json")
    res = {"qid": qid, "smoke": smoke, "generated": ts, **res}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=_json_default)
    print("wrote", os.path.relpath(path, HERE))
    if extra_csv is not None:
        for name, df in extra_csv.items():
            cp = os.path.join(OUT, f"{pre}_{name}_{ts}.csv"); df.to_csv(cp, index=False); print("wrote", os.path.relpath(cp, HERE))
    return path


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


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def syms_available(syms, kind="D1_fromH1", smoke=False):
    if smoke:
        return list(syms), []
    ok = [s for s in syms if exists_sym(s, kind)]
    return ok, [s for s in syms if s not in ok]
# ============================================================================= 共通の土台ここまで


import multiprocessing as mp
import time
import zlib

QID = "Q581"
SEED = 20261031
KS = [0.25, 0.5, 1.0, 2.0, 4.0]
NS = [10, 20, 40]
TYPES = ["both", "buy", "sell"]
CONFIGS = [(k, n, ty) for k in KS for n in NS for ty in TYPES]
PASS_B = int(os.environ.get("Q581_PASS_B", "50"))  # 本番は 50（環境変数は試走用）
B_MAX = 2000
B_MIN_JUDGE = 200
LAM = 0.97
ATR_N = 20
CRYPTO_SPLIT = 2022
MAIN_CFG = (0.5, 20, "both")
ALL_SYMS = list(dict.fromkeys(FX8 + TREND7 + CRYPTO))
PART = os.environ.get("Q581_PART", os.path.join(OUT, "partial"))  # spawn の子にも渡るよう環境変数で
STOP_FILE = _p("検証", "自動実行", "止める")


def split_year(sym):
    return CRYPTO_SPLIT if (sym in CRYPTO and sym != "BTCUSD") else SPLIT_YEAR


def cost_of(sym, price):
    if sym in COST_RT:
        return float(COST_RT[sym] / 2 / price * 1e4)
    return CRYPTO_COST_RT_REL / 2 * 1e4


def grid_net(lp, a, delta, n, ty, cost_bp, detail=False):
    """水準×時刻でベクトル化した格子。返り値: 純損益（1 水準あたり bp）［detail なら (net, gross, trips, end_mtm, mdd)］。"""
    T = len(lp)
    j = np.arange(1, n + 1, dtype=float)
    Ls, sides = [], []
    if ty in ("both", "buy"):
        Ls.append(a - j * delta); sides.append(np.ones(n))
    if ty in ("both", "sell"):
        Ls.append(a + j * delta); sides.append(-np.ones(n))
    L = np.concatenate(Ls)[:, None]; sd = np.concatenate(sides)[:, None]
    tp = L + sd * delta
    P = lp[None, :]
    enter = np.where(sd > 0, P <= L, P >= L)
    leave = np.where(sd > 0, P >= tp, P <= tp)
    ev = np.where(enter, 1, np.where(leave, -1, 0)).astype(np.int8)
    idx = np.where(ev != 0, np.arange(T)[None, :], 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    st = np.take_along_axis(ev, idx, axis=1)
    on = (st == 1)
    on[:, 0] = on[:, 0] & (ev[:, 0] == 1)
    d = np.diff(np.concatenate([np.zeros((on.shape[0], 1), bool), on], axis=1).astype(np.int8), axis=1)
    n_open = (d == 1).sum(); n_close = (d == -1).sum()
    end_on = on[:, -1]
    end_mtm = float((sd[:, 0] * (lp[-1] - L[:, 0]) * end_on).sum() * 1e4)
    fills = n_open + n_close + int(end_on.sum())
    gross = n_close * delta * 1e4 + end_mtm
    nlev = L.shape[0]
    net = (gross - fills * cost_bp) / nlev
    if not detail:
        return net
    cum_close = np.cumsum(d == -1, axis=1) * delta * 1e4
    unreal = on * sd * (P - L) * 1e4
    cum_fill = np.cumsum(np.abs(d), axis=1) * cost_bp
    eq = (cum_close + unreal - cum_fill).sum(axis=0) / nlev
    mdd = float((eq - np.maximum.accumulate(np.r_[0.0, eq])[1:]).min())
    return net, gross / nlev, int(n_close), end_mtm / nlev, mdd


def episodes(sym, smoke, rng):
    h1 = load_h1(sym, smoke, rng, n=70000, start="2008-01-01")
    d1 = h1_to_d1(h1, 0)
    d1["atr"] = atr(d1["high"].values, d1["low"].values, d1["close"].values, ATR_N)
    lp_all = np.log(h1["close"].values.astype(float))
    r_all = np.r_[0.0, np.diff(lp_all)]
    v = np.empty_like(r_all); s2 = np.nanmean(r_all[1:500] ** 2) if len(r_all) > 500 else np.nanmean(r_all ** 2)
    for i in range(len(r_all)):  # EWMA（前の足までの情報）
        v[i] = s2
        s2 = LAM * s2 + (1 - LAM) * r_all[i] ** 2
    sig_all = np.sqrt(np.maximum(v, 1e-14))
    eps = []
    yrs = h1["year"].values
    for y in sorted(np.unique(yrs)):
        prev = d1[d1["time"] < pd.Timestamp(f"{y}-01-01")]
        m = yrs == y
        if prev.empty or not np.isfinite(prev["atr"].iloc[-1]) or m.sum() < 1000:
            continue
        lp = lp_all[m]
        sig = sig_all[m][1:]
        eps.append({"year": int(y), "lp": lp, "sig": sig, "dk": float(prev["atr"].iloc[-1] / prev["close"].iloc[-1]),
                    "cost": cost_of(sym, float(prev["close"].iloc[-1]))})
    return eps


_CACHE = {}


def _eps(sym, smoke):
    key = (sym, smoke)
    if key not in _CACHE:
        _CACHE[key] = episodes(sym, smoke, np.random.default_rng(SEED + zlib.crc32(sym.encode()) % 1000))
    return _CACHE[key]


def task_obs(args):
    sym, smoke = args
    eps = _eps(sym, smoke)
    C, Y = len(CONFIGS), len(eps)
    out = {k: np.full((C, Y), np.nan) for k in ("net", "gross", "trips", "end_mtm", "mdd")}
    for yi, e in enumerate(eps):
        for ci, (k, n, ty) in enumerate(CONFIGS):
            r = grid_net(e["lp"], e["lp"][0], k * e["dk"], n, ty, e["cost"], detail=True)
            for key, val in zip(("net", "gross", "trips", "end_mtm", "mdd"), r):
                out[key][ci, yi] = val
    np.savez_compressed(os.path.join(PART, f"{sym}_obs.npz"), years=np.array([e["year"] for e in eps]), **out)
    return sym


def task_null(args):
    sym, pidx, smoke = args
    eps = _eps(sym, smoke)
    rng = np.random.default_rng([SEED, pidx, zlib.crc32(sym.encode())])
    C, Y = len(CONFIGS), len(eps)
    perm = np.full((C, Y, PASS_B), np.nan, dtype=np.float32); vol = np.full((C, Y, PASS_B), np.nan, dtype=np.float32)
    for yi, e in enumerate(eps):
        lp = e["lp"]; r = np.diff(lp); a = lp[0]; sig = e["sig"]; zz = r / sig; tot = r.sum()
        for b in range(PASS_B):
            p1 = a + np.r_[0.0, np.cumsum(rng.permutation(r))]
            rv = sig * rng.permutation(zz); rv += (tot - rv.sum()) / len(rv)
            p2 = a + np.r_[0.0, np.cumsum(rv)]
            for ci, (k, n, ty) in enumerate(CONFIGS):
                dl = k * e["dk"]
                perm[ci, yi, b] = grid_net(p1, a, dl, n, ty, e["cost"])
                vol[ci, yi, b] = grid_net(p2, a, dl, n, ty, e["cost"])
    np.savez_compressed(os.path.join(PART, f"{sym}_p{pidx:03d}.npz"), perm=perm, vol=vol)
    return sym, pidx


def done_passes(sym):
    return sorted(int(f.split("_p")[-1][:3]) for f in os.listdir(PART) if f.startswith(sym + "_p") and f.endswith(".npz"))


def compute(args, syms):
    os.makedirs(PART, exist_ok=True)
    t0 = time.time(); budget = args.hours * 3600
    ctx = mp.get_context("spawn")
    with ctx.Pool(args.workers) as pool:
        todo = [(s, args.smoke) for s in syms if not os.path.exists(os.path.join(PART, f"{s}_obs.npz"))]
        if todo:
            for s in pool.imap_unordered(task_obs, todo):
                print(f"  obs {s}  {time.time() - t0:.0f}s", flush=True)
        last = None
        max_pass = B_MAX // PASS_B
        for p in range(max_pass):
            if os.path.exists(STOP_FILE):
                print("止めるファイルがあるので終了", flush=True); break
            todo = [(s, p, args.smoke) for s in syms if p not in done_passes(s)]
            if not todo:
                continue
            left = budget - (time.time() - t0)
            if last is not None and left < 1.15 * last * len(todo) / len(syms):
                print(f"持ち時間が足りない（残り {left/60:.0f} 分・前回 {last/60:.1f} 分/パス）ので終了", flush=True); break
            ts = time.time()
            for s, pi in pool.imap_unordered(task_null, todo):
                pass
            last = (time.time() - ts) * len(syms) / len(todo)
            print(f"  パス {p + 1}/{max_pass} 完了（B={PASS_B * (p + 1)}）{last/60:.1f} 分  経過 {(time.time() - t0)/3600:.2f} h", flush=True)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2)) if np.isfinite(z) else float("nan")


def analyze(args, syms):
    rows, B_by = [], {}
    for s in syms:
        fo = os.path.join(PART, f"{s}_obs.npz")
        if not os.path.exists(fo):
            continue
        ob = np.load(fo); years = ob["years"]
        ps = done_passes(s)
        if not ps:
            continue
        P = [np.load(os.path.join(PART, f"{s}_p{p:03d}.npz")) for p in ps]
        perm = np.concatenate([x["perm"] for x in P], axis=2); vol = np.concatenate([x["vol"] for x in P], axis=2)
        B_by[s] = perm.shape[2]
        sy = split_year(s)
        for ci, (k, n, ty) in enumerate(CONFIGS):
            net = ob["net"][ci]
            obs = float(np.nanmean(net))
            pm = np.nanmean(perm[ci], axis=0); vm = np.nanmean(vol[ci], axis=0)
            zp, _ = z_of(obs, pm); zv, _ = z_of(obs, vm)
            pre = net[years < sy]; post = net[years >= sy]
            rows.append({"sym": s, "k": k, "N": n, "type": ty, "n_years": int(len(net)), "net_mean": obs,
                         "net_t_pre": tstat(pre), "net_t_post": tstat(post), "n_pre": int(len(pre)), "n_post": int(len(post)),
                         "gross_mean": float(np.nanmean(ob["gross"][ci])), "trips_mean": float(np.nanmean(ob["trips"][ci])),
                         "end_mtm_mean": float(np.nanmean(ob["end_mtm"][ci])), "worst_mdd": float(np.nanmin(ob["mdd"][ci])),
                         "null_perm_mean": float(pm.mean()), "null_vol_mean": float(vm.mean()),
                         "z_perm": zp, "z_vol": zv, "p_vol": norm_sf(zv), "B": int(perm.shape[2])})
    cells = pd.DataFrame(rows)
    B_min = int(min(B_by.values())) if B_by else 0
    pv = cells["p_vol"].fillna(1.0).values
    cells["p_vol_holm"] = holm(pv)
    cells["holm_pass"] = cells["p_vol_holm"] < 0.05
    cells["halves_pass"] = (cells["net_t_pre"] >= 2) & (cells["net_t_post"] >= 2)
    n_holm = int(cells["holm_pass"].sum()); n_both = int((cells["holm_pass"] & cells["halves_pass"]).sum())
    if B_min < B_MIN_JUDGE:
        verdict = "未確定"
    elif n_both >= 1:
        verdict = "支持"
    elif n_holm == 0:
        verdict = "棄却"
    else:
        verdict = "未確定"
    fx = cells[cells["sym"].isin(FX8)]
    by_cfg = fx.groupby(["k", "N", "type"]).agg(net=("net_mean", "mean"), z_vol=("z_vol", "mean"), z_perm=("z_perm", "mean"),
                                                excess_vol=("null_vol_mean", "mean")).reset_index()
    by_cfg["excess_vol"] = by_cfg["net"] - by_cfg["excess_vol"]
    k0, n0, t0 = MAIN_CFG
    main = cells[(cells["k"] == k0) & (cells["N"] == n0) & (cells["type"] == t0)][["sym", "net_mean", "z_perm", "z_vol", "null_perm_mean", "null_vol_mean"]]
    top = cells.sort_values("z_vol", ascending=False).head(20)
    res = {
        "config": {"syms": syms, "missing": [s for s in ALL_SYMS if s not in syms], "configs": len(CONFIGS), "n_cells": int(len(cells)),
                   "pass_B": PASS_B, "B_min": B_min, "B_by_sym": B_by, "B_min_judge": B_MIN_JUDGE, "lambda": LAM, "split_year": SPLIT_YEAR,
                   "crypto_split": CRYPTO_SPLIT, "seed": SEED},
        "machine_verdict": verdict,
        "parts": {"n_holm_pass": n_holm, "n_holm_and_halves": n_both, "B_min": B_min, "m_holm": int(len(cells))},
        "top20_by_z_vol": top.to_dict("records"),
        "main_cfg_by_symbol": main.to_dict("records"),
        "fx8_by_config": by_cfg.to_dict("records"),
        "summary": {"share_z_vol_pos": float((cells["z_vol"] > 0).mean()), "share_net_pos": float((cells["net_mean"] > 0).mean()),
                    "mean_z_perm_minus_z_vol": float((cells["z_perm"] - cells["z_vol"]).mean())},
        "note": "machine_verdict は事前固定の規則で機械的に付けたもの。解釈は実行者が README の「結果」に書く。z の p は正規近似。",
    }
    write_result(QID, res, args.smoke, extra_csv={"cells": cells, "fx8_by_config": by_cfg})
    print("machine_verdict:", verdict, res["parts"])


def main():
    def extra(ap):
        ap.add_argument("--hours", type=float, default=float(os.environ.get("Q581_HOURS", "7")))
        ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
        ap.add_argument("--analyze", action="store_true", help="計算せず partial から分析だけ")
        ap.add_argument("--syms", default="", help="カンマ区切りで銘柄を絞る（試走用）")
    args = parse_args(default_B=0, extra=extra)
    global PART
    if args.smoke:
        PART = os.path.join(OUT, "smoke_partial")
    os.environ["Q581_PART"] = PART
    os.makedirs(PART, exist_ok=True)
    syms = [s for s in (args.syms.split(",") if args.syms else ALL_SYMS) if s]
    if not args.smoke:
        syms = [s for s in syms if exists_sym(s, "H1_dukascopy")]
    print(f"=== {QID} 銘柄 {len(syms)}・設定 {len(CONFIGS)}・workers {args.workers}・持ち時間 {args.hours}h", flush=True)
    if not args.analyze:
        compute(args, syms)
    analyze(args, syms)


if __name__ == "__main__":
    main()
