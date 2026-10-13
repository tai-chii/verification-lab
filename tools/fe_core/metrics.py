# -*- coding: utf-8 -*-
"""評価指標と統計量。sharpe_ann は isfinite で NaN を落とす版（多数派 71 本）に統一。"""
import math

import numpy as np
import pandas as pd


def tstat(x):
    """平均の t 値（iid 前提、ddof=1）。
    使う場面: 年単位平均など、自己相関が無いとみなせる標本。日次損益には nw_t を使う
    入力: x: 1 次元配列（NaN は落とす）
    返り値: float（n<2 か分散 0 なら NaN）
    禁止: 自己相関のある日次系列にそのまま使わない
    段階: 統計
    """
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def nw_t(x, lag=5):
    """Newey-West（Bartlett 核）の t 値。
    使う場面: 日次・時間足の損益や重なりのあるリターンの平均の検定
    入力: x: 1 次元配列（NaN は落とす）、lag: ラグ数（既定 5。保有期間に合わせる）
    返り値: float（n<3 なら NaN）
    禁止: lag を結果を見てから変えない（事前に固定）
    段階: 統計
    """
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan")
    e = x - x.mean()
    s = (e ** 2).sum()
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] * e[:-k]).sum()
    if s <= 0:
        return float("nan")  # 定数の系列（tstat と同じく NaN。旧雛形は 5e150 を返した）
    se = math.sqrt(s) / n
    return float(x.mean() / se) if se > 0 else float("nan")


def spearman(x, y):
    """スピアマンの順位相関。
    使う場面: IC（予測と実現の順位相関）、パラメータと成績の単調性の確認
    入力: x, y: 同じ長さの配列（どちらかが NaN の行は落とす）
    返り値: float（n<3 なら NaN）
    禁止: IC の改善だけで採用しない（本番指標と帰無を併記する）
    段階: 統計
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
    if len(x) < 3:
        return float("nan")
    rx = np.array(pd.Series(x).rank().values, float); ry = np.array(pd.Series(y).rank().values, float)
    rx -= rx.mean(); ry -= ry.mean()
    d = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def max_drawdown(pnl):
    """累積損益のピークからの最大の落ち込み（負の値、pnl と同じ単位）。
    使う場面: 成績の要約。sharpe_ann と並べて書く
    入力: pnl: 長さ n の損益（bp など加算できる単位）
    返り値: float ≤ 0（空なら NaN）。NaN は 0（損益なし）として累積する（sharpe_ann が NaN を落とすのと同じ方針）
    禁止: 複利の資産曲線に使わない（加算の損益用）
    段階: 統計
    """
    cum = np.cumsum(np.nan_to_num(np.asarray(pnl, float), nan=0.0)); peak = np.maximum.accumulate(cum)
    return float((cum - peak).min()) if len(cum) else float("nan")


def sharpe_ann(pnl, per_year=252):
    """年率シャープ（平均/標準偏差×√per_year、ddof=1）。NaN は落として計算する。
    使う場面: 成績の要約。日足は 252、H1 は 24*260 など足の本数を per_year に渡す
    入力: pnl: 長さ n の損益、per_year: 年あたりの足の本数
    返り値: float（n≤2 か分散 0 なら NaN）
    禁止: 無リスク金利を引かない（bp の超過損益が前提）。年率 2 超は先読み・リークを疑う。「保有なし」を NaN にしない（落とされて稼働率の分だけ膨らむ。0 にする）
    段階: 統計
    """
    x = np.asarray(pnl, float); x = x[np.isfinite(x)]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(per_year)) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def sharpe_ann_n(pnl, per_year=252):
    """sharpe_ann と同じ値に、使った本数と落とした NaN の数を添える。
    使う場面: 結果 JSON に「何本で計算したか」を残すとき。n_dropped が 0 でなければ理由を書く
    入力: pnl、per_year
    返り値: {"sharpe", "n", "n_dropped"}
    禁止: n_dropped>0 を黙って通さない
    段階: 統計
    """
    x = np.asarray(pnl, float); m = np.isfinite(x)
    return {"sharpe": sharpe_ann(x[m], per_year), "n": int(m.sum()), "n_dropped": int((~m).sum())}


def qlike(s2_pred, r2):
    """QLIKE 損失（分散予測の評価。小さいほど良い）。
    使う場面: HAR などボラ予測の比較
    入力: s2_pred: 予測分散、r2: 実現分散（同じ長さ。どちらかが非正・NaN の行は落とす）
    返り値: float（有効な行が 2 以下なら NaN）
    禁止: 水準の違う銘柄を混ぜて平均しない
    段階: 統計
    """
    s2 = np.asarray(s2_pred, float); r2 = np.asarray(r2, float)
    m = np.isfinite(s2) & np.isfinite(r2) & (s2 > 0) & (r2 > 0)
    return float(np.mean(r2[m] / s2[m] - np.log(r2[m] / s2[m]) - 1)) if m.sum() > 2 else float("nan")


def by_year_stats(df, col, year_col="year", y0=0, y1=9999, min_rows=20):
    """年を単位にした平均と t（sym 列があれば年の中で銘柄平均してから）。行数が min_rows 未満の年は数えない。
    使う場面: 期間分割（全期間／前半／後半）の判定値。日次の t より保守的
    入力: df: year（と sym）と col を持つ DataFrame、col: 集計する列、y0/y1: 年の範囲 [y0, y1)、min_rows: 年あたりの最少行数（既定 20。レビュー H3: 3 日しかない年が全体を −165bp に引っ張った例）
    返り値: {"n_years", "mean", "t", "min_rows_in_year", "years_dropped"}
    禁止: 年数が 5 未満の区間で t を判定に使わない（記述にとどめる）。years_dropped が空でないのに黙って通さない
    段階: 統計
    """
    d = df[(df[year_col] >= y0) & (df[year_col] < y1)]
    if d.empty:
        return {"n_years": 0, "mean": float("nan"), "t": float("nan"), "min_rows_in_year": 0, "years_dropped": []}
    rows = d.groupby(year_col)[col].count()
    drop = [int(y) for y, r in rows.items() if r < min_rows]
    if drop:
        d = d[~d[year_col].isin(drop)]
    if "sym" in d.columns:
        yr = d.groupby([year_col, "sym"])[col].mean().groupby(level=0).mean()
    else:
        yr = d.groupby(year_col)[col].mean()
    yr = yr.dropna()
    return {"n_years": int(len(yr)), "mean": float(yr.mean()) if len(yr) else float("nan"), "t": tstat(yr.values),
            "min_rows_in_year": int(rows[rows >= min_rows].min()) if (rows >= min_rows).any() else 0, "years_dropped": drop}


def cluster_t(df, col, by="time", lag=5):
    """束ねた t（改善判定.md の既定）: by（日付など）ごとに col を平均した系列に nw_t を当てる。銘柄をまたぐ同じ日の相関を 1 本に束ねる。
    使う場面: 複数銘柄の日次損益をまとめて 1 つの t にするとき（銘柄ごとの t を足し合わせない）
    入力: df: by と col を持つ DataFrame、col、by: 束ねる鍵、lag: nw_t のラグ
    返り値: {"t", "n_clusters", "mean"}
    禁止: 銘柄 × 日の行をそのまま tstat に入れない（独立でない）
    段階: 統計
    """
    s = df.groupby(by)[col].mean().dropna()
    return {"t": nw_t(s.values, lag=lag), "n_clusters": int(len(s)), "mean": float(s.mean()) if len(s) else float("nan")}


def fmt(x, nd=4):
    """JSON 用の丸め（NaN・None は None）。雛形の f と同じ（f は 1 文字で for 変数に上書きされやすいので新規は fmt を使う）。
    使う場面: 結果 dict に数値を入れるとき
    入力: x: 数値、nd: 小数桁
    返り値: float か None
    禁止: 計算の途中で使わない（丸め誤差が積もる）。`for f in ...` のような変数名を使わない
    段階: 保存
    """
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


f = fmt  # 雛形との互換（91 本が f() を使う）
