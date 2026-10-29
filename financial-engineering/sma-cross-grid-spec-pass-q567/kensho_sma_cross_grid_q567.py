#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q567: 2 本 SMA クロスの総当たり（190 組）を 15 銘柄×D1/H4 で回すと、bot 目標スペック §1 を前後半とも通る組は偶然の期待数を超えず、
前半 Sharpe 上位 5 組の等ウェイトは後半で全 190 組の等ウェイトに勝たないか
================================================================================

【出典】
- 計画（事前登録）: 1 案一括生成（Fable 2026-10-29）。アイデア候補.md の該当行。taichi のチャット「MA2 本を 10〜200 で総当たりして指標ごとの分布を出せば
  いい bot や論文が作れそう」→「各指標 TOP5 の MA ペアを動かす bot は強いか」への答えを数字で出す。
- 目標値: `検証/_基盤/知識/bot目標スペック_月利2%.md` §1（バックテスト: 年率 Sharpe≥2・最大 DD≤10%・月次σ≤3.5%）。
- 先行: Brock, Lakonishok & LeBaron (1992) J. Finance（MA 規則の DJIA 検定）、Sullivan, Timmermann & White (1999) J. Finance（7,846 規則の Reality Check）、
  Bailey & López de Prado (2014) DSR。手元の知見: [[為替の4時間足のMAクロスは500万通りから選んだ最良も補正後に運と区別できず、前半の上位は後半でむしろ劣る]]
  （EURUSD・USDJPY の H4 のみ・`ma-cross-eurusd/`）、Q171/Q188（参照日数の PBO 0.88・台地選択は最良 1 点に勝たない）、Q260（DSR 補正後 0/14）。
  → 本案は (i) 15 銘柄（指数・商品・BTC を含む）× D1/H4 への横展開、(ii) ATR サイズで月次に直した「スペック合格率」とその帰無、(iii) 「前半 TOP5 の等ウェイト」
  という bot の作り方そのものを後半で検証、の 3 点が未確認。

【仮説（測る前に固定）】
H1（選択は無意味）: (A) スペック §1 を前後半とも通る組の数（15 銘柄の合計）は、建玉系列の循環シフト帰無の 95 点以下。
                    (C) 前半（<2017）の Sharpe 上位 5 組を等ウェイトで束ねた後半（≥2017）の純損益は、全 190 組の等ウェイトと差が無い（年単位 t<2）。
H0（選択に価値あり）: (C) の差が t≥2 かつ z≥2（D1・H4 とも）で、(A) が帰無の 99 点超。

【データ】15 銘柄（FX8＋TREND7）。D1_fromH1（2008-02〜）と H4_dukascopy（4 時間足）。**封印: 2024-07-01 以降は読まない**（戦略台帳の OOS 関門まで）。
前半 <2017／後半 ≥2017（SPLIT_YEAR）。暖機: 長期 200 本。

【定義（1 通りに固定）】
- 格子: 短期 S∈{10,20,…,190}、長期 L∈{20,…,200}、S<L の 190 組。SMA は終値の単純平均。
- 建玉: pos[t] = sign(SMA_S[t] − SMA_L[t])。常時どちらかを持つドテン。利確・損切りは置かない（変数を増やさない）。
- 約定: 土台の pnl_bp の決まり（t の終値で決めて t+1 のリターンに効く＝合図の足の終値で約定。遅れは入れない。Q156）。コスト: COST_RT（段階 1）。
- 2 種の損益:
  (a) bp 損益 pnl_bp（土台と同じ・年単位 t 用）
  (b) サイズつき損益（スペック用）: 1 回のリスク 0.5%・仮のストップ幅 2×ATR20（前足まで）→ 建玉比率 w[t] = 0.005 / (2·ATR20[t]/close[t])、上限 3（レバ 3 倍）。
      r_eq[t+1] = pos[t]·w[t]·ret[t+1] − |pos[t]−pos[t−1]|·w[t]·片道コスト。資産曲線は複利。月次に束ねて 月次σ・最悪月・負け月割合、資産曲線で 最大 DD（%）、
      年率 Sharpe（足の損益から・D1 は 252、H4 は 252×6）、カルマー（年率平均÷最大 DD）、取引単位で PF・勝率・月間回数。
- スペック §1 合格（1 組・1 銘柄・1 期間）: 年率 Sharpe ≥ 2.0 かつ 最大 DD ≤ 10% かつ 月次σ ≤ 3.5%。「再現合格」= 前半と後半の両方で合格。
  実運用水準（記述のみ）: Sharpe ≥ 1.5 かつ 最大 DD ≤ 20%。
- (B) 順位相関（記述）: 銘柄ごとに 190 組の前半 Sharpe と後半 Sharpe の Spearman → 15 銘柄の中央値。
- (C) TOP5: 銘柄ごとに前半 Sharpe 上位 5 組（同点は S・L の小さい順）。後半で「TOP5 等ウェイトの bp 損益」−「190 組等ウェイトの bp 損益」を
  年×銘柄のセル → 年ごとに銘柄平均 → 年単位の t（all15・後半のみ）。カルマー上位 5 も同じ形で記述。
- 台地（記述）: 15 銘柄の中央値 Sharpe を S×L の表で出す（前半・後半・全期間）。合格組の S・L の分布も出す。
- 帰無: 銘柄ごとに **190 組の建玉行列を同じ k で循環シフト**（組どうしの相関と自己相関を保つ・min_shift=250 本）して同じ手順（(A)(B)(C)）を B 回
  → (A) 再現合格数の帰無分布、(B) 中央値の帰無、(C) 差の年単位平均の帰無 → z。

【測るもの】
(A) 再現合格数（観測・帰無の 95/99 点・z）、(B) Spearman 中央値（観測・z）、(C) 差の bp/本・t・z。D1 と H4 で別々。
記述: 各指標の分布（中央値・95 点・最良）、合格組の S・L、台地表、実運用水準の合格数、カルマー TOP5。

【判定（事前固定・変更禁止）】
D1・H4 の両方で [(A) 観測 ≤ 帰無 95 点] かつ [(C) t<2 または z<2] → **支持: 総当たりの合格は偶然の範囲で TOP5 bot は等ウェイトに勝たない**。
D1・H4 の両方で [(C) t≥2 かつ z≥2] かつ [(A) 観測 > 帰無 99 点] → **棄却: 選択に価値がある**。
それ以外 → 未確定（D1 と H4 で食い違う場合も未確定。どちらが合うかは記述）。
多重比較: 判定は D1・H4 の (C) の t と z の 4 本＋(A) の 2 本。(B)・各指標の分布・台地・カルマー TOP5 は記述。

【捨てた案の数】約 6: EMA も入れる（ma-cross-eurusd で済み）、3 本 MA、ATR 損切りつき（別 ID で・基本形の分布を見てから）、刻み 5（190→780 組・分布の形は変わらない）、
買いのみ、各指標の TOP5 全部で bot を組む（選択回数が指標の数だけ増える・Sharpe と カルマーの 2 つに絞った）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。

【委託の確かめ方】設計・コードは Fable（2026-10-29）。実行と解釈は後で Opus。実行者は JSON の `main`（D1/H4 の A・B・C）と `machine_verdict`、
`distributions` の中央値を返す。cells CSV（銘柄×足×組×期間）が bot目標スペック §4 の「誤合格率」の記入元。

【実装】自己完結。実行: python3 kensho_sma_cross_grid_q567.py（B=200・D1 数分＋H4 10〜30 分の見込み・4 コアなら --jobs 4）／--B 20／--smoke --B 5／--tf D1
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

QID = "Q567"
DEFAULT_B = 200
SHORTS = list(range(10, 200, 10))          # 10..190
LONGS = list(range(20, 210, 10))           # 20..200
PAIRS = [(s, l) for s in SHORTS for l in LONGS if s < l]   # 190
WARMUP = 200
SEAL_END = pd.Timestamp("2024-07-01")
RISK = 0.005          # 1 回のリスク 0.5%
ATR_N, ATR_K = 20, 2.0
W_MAX = 3.0
SPEC_BT = {"sharpe": 2.0, "mdd": 0.10, "msig": 0.035}
SPEC_LIVE = {"sharpe": 1.5, "mdd": 0.20}
TOPN = 5
MIN_SHIFT = 250
TFS = {"D1": {"per_year": 252, "kind": "D1_fromH1"}, "H4": {"per_year": 252 * 6, "kind": "H4_dukascopy"}}


# ----------------------------------------------------------------------------- データ
def load_tf(sym, tf, smoke, rng):
    if tf == "D1":
        df = load_d1(sym, smoke, rng) if not smoke else load_d1(sym, True, rng)
        if smoke:
            df = _smoke_ohlc(sym, rng, n=4000, freq="D", start="2010-01-01"); df = df[df["high"] != df["low"]].reset_index(drop=True)
    else:
        df = load_csv(f"{sym}_H4_dukascopy", smoke, rng, freq="4h", n=20000, start="2010-01-01")
        df = df[df["high"] != df["low"]].reset_index(drop=True)
    df = df[df["time"] < SEAL_END].reset_index(drop=True)
    df["ret"] = df["close"].pct_change(); df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.to_period("M").astype(str)
    return df


def sma_matrix(close, periods):
    c = pd.Series(np.asarray(close, float))
    return np.column_stack([c.rolling(n).mean().values for n in periods])


def pos_matrix(close):
    """(n, 190) の建玉行列。暖機（長期 200 本）未満は 0。"""
    per = sorted(set(SHORTS) | set(LONGS)); idx = {p: i for i, p in enumerate(per)}
    M = sma_matrix(close, per)
    P = np.column_stack([np.sign(M[:, idx[s]] - M[:, idx[l]]) for s, l in PAIRS])
    P[np.isnan(P)] = 0.0; P[:WARMUP, :] = 0.0
    return P


# ----------------------------------------------------------------------------- 損益（行列）
def pnl_bp_matrix(P, close, cost_oneway_bp):
    """pnl_bp の行列版。P: (n, k)。戻り (n, k) bp。"""
    c = np.asarray(close, float); n = len(c)
    ret = np.zeros(n); ret[1:] = c[1:] / c[:-1] - 1
    held = np.vstack([np.zeros((1, P.shape[1])), P[:-1]])
    prev = np.vstack([np.zeros((1, P.shape[1])), held[:-1]])
    cost = np.abs(held - prev) * np.r_[0.0, cost_oneway_bp[:-1]][:, None]
    return held * ret[:, None] * 1e4 - cost


def weight_vec(df):
    a = atr(df["high"].values, df["low"].values, df["close"].values, ATR_N)
    w = RISK / (ATR_K * a / df["close"].values)
    w = np.where(np.isfinite(w), np.minimum(w, W_MAX), 0.0)
    return w


def r_eq_matrix(P, close, w, cost_oneway_bp):
    """サイズつき損益（資産比）。r[t+1] = pos[t]·w[t]·ret[t+1] − |pos[t]−pos[t−1]|·w[t]·片道。"""
    c = np.asarray(close, float); n = len(c)
    ret = np.zeros(n); ret[1:] = c[1:] / c[:-1] - 1
    held = np.vstack([np.zeros((1, P.shape[1])), P[:-1]]); prev = np.vstack([np.zeros((1, P.shape[1])), held[:-1]])
    wl = np.r_[0.0, w[:-1]][:, None]
    cost = np.abs(held - prev) * wl * (np.r_[0.0, cost_oneway_bp[:-1]] / 1e4)[:, None]
    return held * wl * ret[:, None] - cost


def metrics_block(R, PB, P, months, per_year, light=False):
    """R: 資産比損益 (n,k)、PB: bp 損益 (n,k)、P: 建玉 (n,k)、months: 月ラベル (n,)。1 期間の指標を組ごとに返す dict of arrays。"""
    n, k = R.shape
    out = {}
    mu = R.mean(0); sd = R.std(0, ddof=1); sd[sd == 0] = np.nan
    out["sharpe"] = mu / sd * math.sqrt(per_year)
    eq = np.cumprod(1 + R, axis=0); peak = np.maximum.accumulate(eq, axis=0)
    out["mdd"] = ((peak - eq) / peak).max(0)
    yrs = n / per_year
    out["cagr"] = eq[-1] ** (1 / yrs) - 1 if yrs > 0 else np.full(k, np.nan)
    out["calmar"] = np.where(out["mdd"] > 0, out["cagr"] / out["mdd"], np.nan)
    # 月次
    mdf = pd.DataFrame(np.log1p(R)); mdf["m"] = months
    mret = np.expm1(mdf.groupby("m").sum().values)       # (n_months, k)
    out["msig"] = mret.std(0, ddof=1) if len(mret) > 2 else np.full(k, np.nan)
    out["mmean"] = mret.mean(0); out["worst_m"] = mret.min(0); out["lose_m"] = (mret < 0).mean(0)
    n_months = len(mret)
    # 取引単位（ドテン 1 回を 1 取引）: 建玉が変わった足で区切る（reduceat で列ごとに合計）
    pf = np.full(k, np.nan); wr = np.full(k, np.nan); ntr = np.zeros(k)
    if not light:
        held = np.vstack([np.zeros((1, k)), P[:-1]]); chg = np.vstack([np.ones((1, k), bool), held[1:] != held[:-1]])
        for j in range(k):
            st = np.flatnonzero(chg[:, j])
            if len(st) < 2:
                continue
            s = np.add.reduceat(PB[:, j], st)[1:]   # 先頭（暖機・建玉 0）の塊を除く
            g = s[s > 0].sum(); l = -s[s < 0].sum()
            pf[j] = g / l if l > 0 else np.nan; wr[j] = (s > 0).mean(); ntr[j] = len(s)
    out["pf"] = pf; out["winrate"] = wr; out["trades_pm"] = ntr / max(n_months, 1)
    out["bp_per_bar"] = PB.mean(0)
    out["pass_bt"] = (out["sharpe"] >= SPEC_BT["sharpe"]) & (out["mdd"] <= SPEC_BT["mdd"]) & (out["msig"] <= SPEC_BT["msig"])
    out["pass_live"] = (out["sharpe"] >= SPEC_LIVE["sharpe"]) & (out["mdd"] <= SPEC_LIVE["mdd"])
    return out


def halves(df):
    y = df["year"].values
    return {"pre": y < SPLIT_YEAR, "post": y >= SPLIT_YEAR, "all": np.ones(len(y), bool)}


def evaluate(P, df, w, cb, per_year, light=False):
    """1 銘柄・1 建玉行列 → 期間ごとの指標と、(C) 用の年×組の bp 表。"""
    c = df["close"].values; R = r_eq_matrix(P, c, w, cb); PB = pnl_bp_matrix(P, c, cb); months = df["month"].values
    res = {}
    for nm, m in halves(df).items():
        if m.sum() < WARMUP + 50:
            continue
        res[nm] = metrics_block(R[m], PB[m], P[m], months[m], per_year, light)
    year_bp = pd.DataFrame(PB).groupby(df["year"].values).mean()   # 年×組（bp/本）
    return res, year_bp


def top_select(pre_metric):
    order = np.lexsort(([l for _, l in PAIRS], [s for s, _ in PAIRS], -np.nan_to_num(pre_metric, nan=-1e9)))
    return order[:TOPN]


def c_cells(year_bp, pre_sharpe, pre_calmar, sym):
    """(C): 後半の年ごとに TOP5 等ウェイト − 190 等ウェイト（bp/本）。"""
    post = year_bp[year_bp.index >= SPLIT_YEAR]
    ew = post.mean(1)
    rows = []
    for nm, met in (("sharpe", pre_sharpe), ("calmar", pre_calmar)):
        sel = top_select(met); top = post.iloc[:, sel].mean(1)
        for y in post.index:
            rows.append({"year": int(y), "sym": sym, "metric": nm, "diff": float(top[y] - ew[y]), "top": float(top[y]), "ew": float(ew[y])})
    return rows


def year_t(rows, metric="sharpe"):
    d = pd.DataFrame(rows); d = d[d["metric"] == metric]
    if d.empty:
        return {"diff_bp": float("nan"), "t": float("nan"), "n_years": 0}
    yr = d.groupby(["year", "sym"])["diff"].mean().groupby(level=0).mean()
    return {"diff_bp": float(yr.mean()), "t": tstat(yr.values), "n_years": int(len(yr)), "top_bp": float(d["top"].mean()), "ew_bp": float(d["ew"].mean())}


# ----------------------------------------------------------------------------- 本体
def run_tf(tf, syms, args, rng):
    per_year = TFS[tf]["per_year"]
    data = {}
    for s in syms:
        df = load_tf(s, tf, args.smoke, rng)
        if len(df) < WARMUP + 300:
            continue
        cb = cost_bp_oneway(s, df["close"].values); w = weight_vec(df)
        if args.smoke:
            w = np.minimum(w * 1.0, W_MAX)
        data[s] = (df, cb, w, pos_matrix(df["close"].values))
    # 観測
    cells = []; crow = []; rep_pass = 0; live_pass = 0; sp = []; heat = {"pre": [], "post": [], "all": []}
    for s, (df, cb, w, P) in data.items():
        res, ybp = evaluate(P, df, w, cb, per_year)
        if "pre" not in res or "post" not in res:
            continue
        for nm in ("pre", "post", "all"):
            if nm in res:
                heat[nm].append(res[nm]["sharpe"])
                for j, (S, L) in enumerate(PAIRS):
                    cells.append({"tf": tf, "sym": s, "period": nm, "S": S, "L": L, **{k: (float(v[j]) if not isinstance(v[j], (bool, np.bool_)) else bool(v[j])) for k, v in res[nm].items()}})
        rep = res["pre"]["pass_bt"] & res["post"]["pass_bt"]; rep_pass += int(rep.sum())
        live_pass += int((res["pre"]["pass_live"] & res["post"]["pass_live"]).sum())
        sp.append(spearman(res["pre"]["sharpe"], res["post"]["sharpe"]))
        crow += c_cells(ybp, res["pre"]["sharpe"], res["pre"]["calmar"], s)
    obs = {"A_rep_pass": rep_pass, "A_live_rep_pass": live_pass, "B_spearman_median": float(np.nanmedian(sp)) if sp else float("nan"),
           "C_sharpe": year_t(crow, "sharpe"), "C_calmar": year_t(crow, "calmar"), "n_syms": len(sp)}
    # 帰無: 建玉行列を銘柄ごとに同じ k で循環シフト
    nullA, nullB, nullC = [], [], []
    for b in range(args.B):
        rp = 0; sps = []; cr = []
        for s, (df, cb, w, P) in data.items():
            n = len(P); k = int(rng.integers(MIN_SHIFT, max(MIN_SHIFT + 1, n - MIN_SHIFT)))
            Ps = np.roll(P, k, axis=0)
            res, ybp = evaluate(Ps, df, w, cb, per_year, light=True)
            if "pre" not in res or "post" not in res:
                continue
            rp += int((res["pre"]["pass_bt"] & res["post"]["pass_bt"]).sum())
            sps.append(spearman(res["pre"]["sharpe"], res["post"]["sharpe"]))
            cr += c_cells(ybp, res["pre"]["sharpe"], res["pre"]["calmar"], s)
        nullA.append(rp); nullB.append(float(np.nanmedian(sps)) if sps else np.nan); nullC.append(year_t(cr, "sharpe")["diff_bp"])
        if b % 20 == 0:
            print(tf, "null", b, flush=True)
    zA, _ = z_of(obs["A_rep_pass"], nullA); zB, _ = z_of(obs["B_spearman_median"], nullB); zC, _ = z_of(obs["C_sharpe"]["diff_bp"], nullC)
    nA = np.asarray(nullA, float)
    main = {"A_rep_pass_obs": obs["A_rep_pass"], "A_null_mean": f(nA.mean()), "A_null_p95": f(np.percentile(nA, 95)) if len(nA) else None,
            "A_null_p99": f(np.percentile(nA, 99)) if len(nA) else None, "A_z": f(zA), "A_live_rep_pass_obs": obs["A_live_rep_pass"],
            "B_spearman_median": f(obs["B_spearman_median"]), "B_z": f(zB),
            "C_top5_sharpe_minus_ew_bp": f(obs["C_sharpe"]["diff_bp"]), "C_t": f(obs["C_sharpe"]["t"]), "C_z": f(zC), "C_n_years": obs["C_sharpe"]["n_years"],
            "C_top5_bp": f(obs["C_sharpe"].get("top_bp")), "C_ew_bp": f(obs["C_sharpe"].get("ew_bp")),
            "C_calmar_top5_minus_ew_bp": f(obs["C_calmar"]["diff_bp"]), "C_calmar_t": f(obs["C_calmar"]["t"]), "n_syms": obs["n_syms"]}
    # 記述: 分布と台地
    cdf = pd.DataFrame(cells)
    dist = {}
    for nm in ("pre", "post", "all"):
        d = cdf[cdf["period"] == nm]
        if d.empty:
            continue
        dist[nm] = {k: {"median": f(d[k].median()), "p05": f(d[k].quantile(.05)), "p95": f(d[k].quantile(.95)), "best": f(d[k].max())}
                    for k in ("sharpe", "mdd", "calmar", "pf", "winrate", "trades_pm", "msig", "worst_m", "lose_m", "bp_per_bar")}
        dist[nm]["pass_bt_count"] = int(d["pass_bt"].sum()); dist[nm]["pass_live_count"] = int(d["pass_live"].sum()); dist[nm]["n_cells"] = int(len(d))
    heat_tbl = []
    for nm, arrs in heat.items():
        if arrs:
            med = np.nanmedian(np.vstack(arrs), axis=0)
            for j, (S, L) in enumerate(PAIRS):
                heat_tbl.append({"tf": tf, "period": nm, "S": S, "L": L, "median_sharpe": float(med[j])})
    passed = cdf[cdf["pass_bt"]].groupby(["S", "L"]).size().reset_index(name="n").sort_values("n", ascending=False).head(20)
    return main, dist, cdf, pd.DataFrame(heat_tbl), passed


def verdict_of(mains):
    tfs = [t for t in ("D1", "H4") if t in mains]
    if len(tfs) < 2:
        return "未確定: D1 と H4 の両方が計算できない"
    g = lambda m, k: m.get(k) if m.get(k) is not None else float("nan")
    sup = all(g(mains[t], "A_rep_pass_obs") <= g(mains[t], "A_null_p95") and (g(mains[t], "C_t") < 2 or g(mains[t], "C_z") < 2) for t in tfs)
    rej = all(g(mains[t], "C_t") >= 2 and g(mains[t], "C_z") >= 2 and g(mains[t], "A_rep_pass_obs") > g(mains[t], "A_null_p99") for t in tfs)
    if sup:
        return "支持: 総当たりの合格は偶然の範囲で TOP5 bot は等ウェイトに勝たない"
    if rej:
        return "棄却: 選択に価値がある"
    return "未確定"


def run(args, rng):
    tfs = [args.tf] if args.tf else list(TFS)
    mains, dists, cells, heats, passes, missing = {}, {}, [], [], {}, {}
    for tf in tfs:
        syms, miss = syms_available(SYMS, kind=TFS[tf]["kind"], smoke=args.smoke); missing[tf] = miss
        m, d, c, h, p = run_tf(tf, syms, args, rng)
        mains[tf] = m; dists[tf] = d; cells.append(c); heats.append(h); passes[tf] = p.to_dict("records")
    res = {"question": "2 本 SMA クロス総当たり（190 組×15 銘柄×D1/H4）: スペック §1 の再現合格数は帰無の範囲か・前半 TOP5 の等ウェイトは後半で 190 組等ウェイトに勝つか",
           "settings": {"pairs": len(PAIRS), "shorts": SHORTS, "longs": LONGS, "warmup": WARMUP, "seal_end": str(SEAL_END.date()), "split_year": SPLIT_YEAR,
                        "risk": RISK, "atr": [ATR_N, ATR_K], "w_max": W_MAX, "spec_bt": SPEC_BT, "spec_live": SPEC_LIVE, "topn": TOPN, "B": args.B, "min_shift": MIN_SHIFT},
           "missing": missing, "main": mains, "distributions": dists, "most_passed_pairs": passes,
           "machine_verdict": verdict_of(mains) if not args.tf else "未確定: --tf 指定（片方だけ）",
           "multiple_comparisons": "判定は D1・H4 の (C) の t と z の 4 本と (A) の 2 本。(B)・分布・台地・カルマー TOP5・実運用水準は記述。"}
    return res, {"cells": pd.concat(cells, ignore_index=True), "heat": pd.concat(heats, ignore_index=True)}


def main():
    args = parse_args(default_B=DEFAULT_B, extra=lambda ap: ap.add_argument("--tf", choices=list(TFS), default=None, help="片方の足だけ（判定は付かない）"))
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs)
    print("machine_verdict:", res.get("machine_verdict"))
    for tf, m in res["main"].items():
        print(tf, {k: m[k] for k in ("A_rep_pass_obs", "A_null_p95", "A_z", "B_spearman_median", "C_t", "C_z")})


if __name__ == "__main__":
    main()
