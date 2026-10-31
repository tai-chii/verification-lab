#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q579: MA 整列の局面では翌 24 本の分散比が 1 を超え、整列していない局面では 1 を下回るか
              （トレンド bot × トラリピ切替の前提・15 銘柄 H1）
================================================================================

【出典】
- 計画（事前登録）: taichi の指示で 1 案生成（Opus 2026-10-30・設計とコードまで、実行と解釈は未）。アイデア候補.md の Q579 の行。
- 発端: taichi の案「2〜3 本の MA がきれいにクロス（整列）している時はトレンドフォロー bot を多く動かし、それ以外はトラリピ（グリッド）を動かす」。
  この bot が勝つには (a) 整列中はトレンドが続き（分散比 > 1）、(b) 非整列中は平均回帰している（分散比 < 1）の両方が要る。本検証はその前提だけを測る（bot 本体は作らない）。
- 主張カード: [[Brock1992-1_ダウ平均の移動平均の買いシグナル中は年12パーセント売りシグナル中はマイナス7パーセント]]（MA の合図で条件づけた先のリターン）、
  [[Alahmadi・Basingab2026-3_設定の選び方が弱形効率性検定の結論に実質的に効く]]（分散比の設定依存）。
- 関連知見: Q148（分散比の q 依存は偽陽性並み）、Q149（分散比で有意な年は 4% で翌年の売買はコスト後に負）、
  「為替の超短期の平均回帰は 2015 年以降の 1 時間足では消えた」、Q294（符号つき自己相関はボラ局面で差がない）。
  → 無条件の分散比は 1 にほぼ等しいことが分かっている。本案は「MA 整列で条件づけると 1 から両側に割れるか」という条件の穴。
- 先行研究チェック（WebSearch 2026-10-30・英語）: 検索語 "variance ratio conditional on moving average alignment trend regime mean reversion FX intraday grid trading"
  ／"regime switching trend following mean reversion foreign exchange variance ratio intraday momentum daily reversal timescale study"。
  株価のモメンタム／平均回帰のレジーム切替モデル（"A regime-switching model of stock returns with momentum and mean reversion"）や為替の連続時間レジーム切替モデルはあるが、
  MA 整列でラベルを付けた局面別の分散比を 15 銘柄 H1 で循環シフト帰無と前後半で判定した実証は見つからない（条件の穴）。MQL5 の販売 EA の説明は根拠にしない。

【仮説（測る前に固定）】
H1a: 整列局面の VR(24) は非整列局面より大きい（D = VR_al − VR_un > 0）。
H1b: 非整列局面の VR(24) は 1 より小さい（U = VR_un − 1 < 0、平均回帰＝グリッドが勝てる地合い）。
H0: どちらも 0 と区別できない（MA 整列は先の値動きの性質を分けない）。

【データ】15 銘柄（FX8＋TREND7）の H1_dukascopy（FX 2008〜、油・指数 2011-09〜、BTC 2017〜、2026-06 まで）。前半 <2017／後半 ≥2017（年は起点 t の年）。

【定義（1 通りに固定）】
- r_t = log(close_t / close_{t−1})（値動きのない足は除いた後）。
- 整列ラベル lab_t（足 t の終値で確定・先読みなし）: 終値 > SMA20 > SMA50 > SMA200 → +1（上昇整列）、終値 < SMA20 < SMA50 < SMA200 → −1（下降整列）、それ以外 → 0（非整列）。SMA200 が出るまでは除外。
- 起点 t からの先の q 本: S_q(t) = Σ_{j=1..q} r_{t+j}、Q_q(t) = Σ_{j=1..q} r_{t+j}²。
- 局面 M の分散比: VR_M(q) = Σ_{t∈M} S_q(t)² / Σ_{t∈M} Q_q(t)（中心化しない 2 次モーメント比。局面内の向きの続き（ドリフト）も自己相関も 1 からのずれに入る。局面ごとのボラの違いは分母で揃う）。
  起点は重なる（毎時）。推論は年単位の t と循環シフトの帰無で行う。
- 対数ではなく水準で比べる: log VR は標本の少ない局面ほど負に偏る（Jensen。合成データの試走で整列局面の起点数が少ないぶん D が t≈−3 に偏るのを確認）。
  比の推定量 ΣS²/ΣQ は独立増分のもとで Var(ΣQ)=Cov(ΣS²,ΣQ) となり 1 次の偏りが消えるので、水準を使う。
  A = VR_al − 1、U = VR_un − 1、D = VR_al − VR_un。
  中心化しないので無条件のドリフトも VR に入るが、H1 の 24 本では年率 15% のドリフトでも VR を約 0.3% 押し上げるだけ（判定の大きさに比べ無視できる）。
- 主の q = 24（1 日）。銘柄×年のセルで、各局面の起点が 500 本未満なら NaN。
- 年の統計: 銘柄×年の D・U → 年ごとに銘柄平均 → 前後半それぞれ年単位の t（by_year_stats）。

【帰無】銘柄ごとに整列ラベル列を循環シフト（最小 480 本＝約 20 営業日。ラベルの持続と出現率は保ち、先のリターンとの対応だけ壊す）× B=300。
全期間の all15 の D（銘柄ごとの全期間 D の銘柄平均）を帰無分布と比べて z_D。U の z は記述（U の判定は「0 より小さいか」を年単位の t で見る）。

【測るもの】
判定: all15・q=24 の D と U の前後半の年単位 t（4 本）と全期間の z_D（1 本）。
記述（判定外）: q ∈ {6, 120}、fx8／trend7、2 本 MA 版（終値>SMA20>SMA50 またはその逆）、銘柄別の D・U・z、整列の時間比率と平均の続く本数・1000 本あたりの切替回数、
整列中の順張りの先 24 本の向きつきリターン（bp・コスト前）、整列が始まる直前 48 本の向きつきの動き（bp と、直前 48 本の実現ボラに対する倍率＝切替時にグリッドが逆向きに抱える大きさの目安）。

【判定（事前固定・変更禁止）】
- 支持: all15・q=24 で、前後半とも D の t ≥ 2 かつ U の t ≤ −2、かつ全期間の z_D ≥ 2。
- 棄却: 前後半とも D の t < 1、または前後半とも U の t > −1（どちらかの前提が両期間で崩れれば、切替 bot の前提は成り立たない。どちらが崩れたかは parts に出す）。
- 未確定: それ以外。

【多重比較】判定に使うのは上の 5 本だけ（AND 条件なので補正しない）。q・群・2 本 MA 版・銘柄別は記述に留め、判定を変えない。

【捨てた案の数】約 5: ATR で局面を分ける（値動きの大きさで向きの続きを測らない）、効率比・ADX での局面分け（別の案として残す）、
グリッド bot とトレンド bot の損益を直接バックテスト（パラメータが多く過学習しやすい・前提の確認が先）、MA の期間の格子（多重比較が増える）、D1 版（H1 の方がグリッドの時間軸に近い）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。データの終端も 2026-06。

【委託の確かめ方】設計・コードは Opus（2026-10-30）。実行と解釈は後で /lab（担当 opus）。実行者は JSON のパス・D と U の前後半の t・z_D・machine_verdict と parts を返す。

【実装】自己完結（共通の土台を埋め込み）。実行: python3 kensho_ma_alignment_vr_q579.py（B=300、15 銘柄 H1 で数分）／--B 30／--smoke（合成データ・経路確認のみ）
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


SEAL_END = "2024-07-01"  # 封印 time<2024-07-01（2026-10-31 事後の判断で追加）


def load_h1(sym, smoke=False, rng=None, n=60000, start="2015-01-01"):
    """UTC 1時間足（H1_dukascopy）。値動きのない足は除く。列: time, open, high, low, close, volume, ret, year, hour, dow"""
    df = load_csv(f"{sym}_H1_dukascopy", smoke, rng, freq="h", n=n, start=start)
    if not smoke:
        df = df[df["time"] < pd.Timestamp(SEAL_END)]
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


QID = "Q579"
SEED = 20261030
DEFAULT_B = 300
Q_MAIN = 24
Q_DESC = [6, 120]
MIN_START = 500
MIN_SHIFT = 480
PRE_ONSET = 48
MA3 = (20, 50, 200)


def labels(close, mas):
    c = pd.Series(np.asarray(close, float))
    s = [c.rolling(n).mean().values for n in mas]
    cv = c.values
    up = cv > s[0]
    dn = cv < s[0]
    for a, b in zip(s[:-1], s[1:]):
        up &= a > b
        dn &= a < b
    lab = np.where(up, 1.0, np.where(dn, -1.0, 0.0))
    lab[np.isnan(s[-1])] = np.nan
    return lab


def fwd_sums(r, q):
    """S_q(t)=Σ r_{t+1..t+q}、Q_q(t)=Σ r²_{t+1..t+q}。末尾 q 本は NaN。"""
    n = len(r)
    c1 = np.r_[0.0, np.cumsum(r)]
    c2 = np.r_[0.0, np.cumsum(r * r)]
    S = np.full(n, np.nan); Q = np.full(n, np.nan)
    idx = np.arange(n - q)
    S[idx] = c1[idx + q + 1] - c1[idx + 1]
    Q[idx] = c2[idx + q + 1] - c2[idx + 1]
    return S, Q


def log_vr(S2, Q, mask, min_n=MIN_START):
    """名前は互換のため。返すのは VR − 1（水準）。"""
    m = mask & np.isfinite(S2) & np.isfinite(Q)
    if m.sum() < min_n:
        return float("nan")
    den = Q[m].sum()
    return float(S2[m].sum() / den - 1.0) if den > 0 else float("nan")


def runs(lab):
    """整列（≠0）の連続本数の平均と 1000 本あたりの切替回数。"""
    v = lab[np.isfinite(lab)]
    if len(v) < 2:
        return float("nan"), float("nan")
    al = (v != 0).astype(int)
    sw = int((np.diff(v) != 0).sum())
    starts = np.flatnonzero(np.diff(np.r_[0, al]) == 1)
    ends = np.flatnonzero(np.diff(np.r_[al, 0]) == -1)
    dur = (ends - starts + 1) if len(starts) else np.array([np.nan])
    return float(np.nanmean(dur)), float(sw / len(v) * 1000)


def sym_cells(sym, df, q, lab):
    """銘柄×年の logVR_al・logVR_un と全期間値を返す。"""
    r = np.r_[0.0, np.diff(np.log(df["close"].values.astype(float)))]
    S, Q = fwd_sums(r, q)
    S2 = S * S
    yr = df["year"].values
    fin = np.isfinite(lab)
    al = fin & (lab != 0)
    un = fin & (lab == 0)
    rows = []
    for y in np.unique(yr):
        my = yr == y
        a = log_vr(S2, Q, al & my); u = log_vr(S2, Q, un & my)
        rows.append({"sym": sym, "year": int(y), "A": a, "U": u, "D": a - u if np.isfinite(a) and np.isfinite(u) else np.nan})
    full = {"A": log_vr(S2, Q, al), "U": log_vr(S2, Q, un)}
    full["D"] = full["A"] - full["U"]
    return rows, full, (r, S, Q, S2)


def null_D(rng, lab, S2, Q, B):
    """ラベルを循環シフトした全期間 D・U の帰無。"""
    fin = np.isfinite(lab)
    lv = lab[fin]
    S2f = S2[fin]; Qf = Q[fin]
    outD = np.full(B, np.nan); outU = np.full(B, np.nan)
    n = len(lv)
    if n < 2 * MIN_SHIFT + 10:
        return outD, outU
    for b in range(B):
        k = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT))
        l2 = np.roll(lv, k)
        a = log_vr(S2f, Qf, l2 != 0); u = log_vr(S2f, Qf, l2 == 0)
        outD[b] = a - u; outU[b] = u
    return outD, outU


def half_stats(cells, col, syms):
    d = cells[cells["sym"].isin(syms)]
    return {"full": by_year_stats(d, col), "pre": by_year_stats(d, col, y1=SPLIT_YEAR), "post": by_year_stats(d, col, y0=SPLIT_YEAR)}


def machine_verdict(D, U, zD):
    tdp, tdq = D["pre"]["t"], D["post"]["t"]
    tup, tuq = U["pre"]["t"], U["post"]["t"]
    parts = {
        "D_pre_t": f(tdp), "D_post_t": f(tdq), "U_pre_t": f(tup), "U_post_t": f(tuq), "z_D": f(zD),
        "H1a_aligned_more_trend_both_halves": bool(np.isfinite(tdp) and np.isfinite(tdq) and tdp >= 2 and tdq >= 2),
        "H1b_unaligned_mean_revert_both_halves": bool(np.isfinite(tup) and np.isfinite(tuq) and tup <= -2 and tuq <= -2),
        "D_fails_both_halves(t<1)": bool(np.isfinite(tdp) and np.isfinite(tdq) and tdp < 1 and tdq < 1),
        "U_fails_both_halves(t>-1)": bool(np.isfinite(tup) and np.isfinite(tuq) and tup > -1 and tuq > -1),
    }
    if parts["H1a_aligned_more_trend_both_halves"] and parts["H1b_unaligned_mean_revert_both_halves"] and np.isfinite(zD) and zD >= 2:
        v = "支持"
    elif parts["D_fails_both_halves(t<1)"] or parts["U_fails_both_halves(t>-1)"]:
        v = "棄却"
    else:
        v = "未確定"
    return v, parts


def run(args, rng):
    syms, missing = syms_available(SYMS, kind="H1_dukascopy", smoke=args.smoke)
    data = {}
    for s in syms:
        data[s] = load_h1(s, args.smoke, rng)

    # ---- 主: 3 本 MA・q=24（判定）
    cells, fulls, nullD, nullU, sym_rows, desc_extra = [], {}, {}, {}, [], []
    for s, df in data.items():
        lab = labels(df["close"].values, MA3)
        rows, full, (r, S, Q, S2) = sym_cells(s, df, Q_MAIN, lab)
        cells += rows; fulls[s] = full
        nD, nU = null_D(rng, lab, S2, Q, args.B)
        nullD[s] = nD; nullU[s] = nU
        zD_s, _ = z_of(full["D"], nD)
        zU_s, _ = z_of(full["U"], nU)
        fin = np.isfinite(lab)
        mdur, swk = runs(lab)
        # 整列中の順張りの先 24 本（bp・コスト前）
        al = fin & (lab != 0) & np.isfinite(S)
        trend_bp = lab[al] * S[al] * 1e4
        tr_year = pd.DataFrame({"sym": s, "year": df["year"].values[al], "trend_bp": trend_bp})
        desc_extra.append(tr_year)
        # 整列が始まる直前 48 本の向きつきの動き
        lv = np.where(fin, lab, np.nan)
        onset = np.flatnonzero((np.abs(np.nan_to_num(lv)) == 1) & (np.r_[np.nan, lv[:-1]] == 0))
        onset = onset[onset >= PRE_ONSET]
        lc = np.log(df["close"].values.astype(float))
        c2 = np.r_[0.0, np.cumsum(r * r)]
        mv = lab[onset] * (lc[onset] - lc[onset - PRE_ONSET])
        vol = np.sqrt(c2[onset + 1] - c2[onset + 1 - PRE_ONSET])
        ratio = np.where(vol > 0, mv / vol, np.nan)
        sym_rows.append({"sym": s, "A_full": f(full["A"]), "U_full": f(full["U"]), "D_full": f(full["D"]),
                         "z_D": f(zD_s), "z_U": f(zU_s), "share_aligned": f(float((lab[fin] != 0).mean())),
                         "mean_aligned_run_bars": f(mdur, 1), "switches_per_1000": f(swk, 2),
                         "trend_fwd24_bp_mean": f(float(np.nanmean(trend_bp)) if len(trend_bp) else float("nan")),
                         "n_onsets": int(len(onset)), "pre_onset48_bp_mean": f(float(np.nanmean(mv * 1e4)) if len(mv) else float("nan")),
                         "pre_onset48_vol_ratio_mean": f(float(np.nanmean(ratio)) if len(ratio) else float("nan"))})
    cells = pd.DataFrame(cells)

    D = half_stats(cells, "D", syms); U = half_stats(cells, "U", syms); A = half_stats(cells, "A", syms)
    # 全期間 all15 の D とその帰無（銘柄平均）
    obsD = float(np.nanmean([fulls[s]["D"] for s in syms]))
    obsU = float(np.nanmean([fulls[s]["U"] for s in syms]))
    NM = np.vstack([nullD[s] for s in syms]); NU = np.vstack([nullU[s] for s in syms])
    zD, pD = z_of(obsD, np.nanmean(NM, axis=0))
    zU, pU = z_of(obsU, np.nanmean(NU, axis=0))
    verdict, parts = machine_verdict(D, U, zD)

    # ---- 記述: 群別（q=24）
    groups = {}
    for g, gs in GROUPS.items():
        gs2 = [s for s in gs if s in syms]
        if gs2:
            groups[g] = {"D": half_stats(cells, "D", gs2), "U": half_stats(cells, "U", gs2), "A": half_stats(cells, "A", gs2)}

    # ---- 記述: q ∈ Q_DESC、2 本 MA 版（q=24）
    def variant(q, mas):
        cc = []
        for s, df in data.items():
            lab = labels(df["close"].values, mas)
            rows, _, _ = sym_cells(s, df, q, lab)
            cc += rows
        cc = pd.DataFrame(cc)
        return {"D": half_stats(cc, "D", syms), "U": half_stats(cc, "U", syms), "A": half_stats(cc, "A", syms)}

    desc = {f"q{q}_ma3": variant(q, MA3) for q in Q_DESC}
    desc["q24_ma2"] = variant(Q_MAIN, MA3[:2])

    tr = pd.concat(desc_extra, ignore_index=True) if desc_extra else pd.DataFrame(columns=["sym", "year", "trend_bp"])
    trend_side = half_stats(tr, "trend_bp", syms) if len(tr) else {}

    res = {
        "config": {"seal_end": SEAL_END, "syms": syms, "missing": missing, "B": args.B, "q_main": Q_MAIN, "q_desc": Q_DESC, "ma": MA3,
                   "min_start": MIN_START, "min_shift": MIN_SHIFT, "split_year": SPLIT_YEAR, "seed": args.seed},
        "main_all15_q24": {"D": D, "U": U, "A": A, "obs_D_full": f(obsD), "z_D": f(zD), "p_null_below_D": f(pD),
                           "obs_U_full": f(obsU), "z_U_desc": f(zU)},
        "machine_verdict": verdict, "parts": parts,
        "n_tests_judged": 5,
        "describe_groups_q24": groups,
        "describe_variants": desc,
        "describe_trend_fwd24_bp_aligned": trend_side,
        "note": "machine_verdict は事前固定の規則で機械的に付けたもの。解釈は実行者が README の「結果」に書く。",
    }
    csvs = {"cells": cells, "symbols": pd.DataFrame(sym_rows)}
    return res, csvs


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, extra_csv=csvs)
    print("machine_verdict:", res["machine_verdict"], res["parts"])


if __name__ == "__main__":
    main()
