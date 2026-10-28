# -*- coding: utf-8 -*-
"""equities_free — 日本株・米国株の無料データ層の読み込み（Q562・2026-10-28）。

fe_core は「直さない」決まり（固定 0.2.2）なので、横断用の読み込みは fe_core の外に置く。
使い方: sys.path に verification-lab/tools を足して `import equities_free as ef`。
  px = ef.load("jp", "close")            # 日付 × 銘柄（調整済み終値）。封印 2024-07-01 以降は落とす
  vol = ef.load("jp", "volume")
  sh = ef.load_short_ratio("market")     # 空売り比率（日次・市場全体）。asof に +1 営業日して「使える日」の列 avail を付ける
  mg = ef.load_margin("buy")             # 銘柄別信用買い残（日付 × コード）。蓄積分のみ
注意: 現在の上場銘柄だけ＝生存バイアスあり（小型・反転系は過大評価）。調整済み終値は配当・分割を遡って直した値。
"""
import os
import pandas as pd

WS = os.path.expanduser("~/ワークスペース")
DIR = os.path.join(WS, "作業層", "大容量", "equities_free")
SEAL = pd.Timestamp("2024-07-01")   # ホールドアウト 2024-07〜2026-06。既定ではここ以降を返さない

def load(mkt, field="close", end=SEAL, start=None):
    """日足を 日付×銘柄 の表で返す。

    使う場面: 横断（ポートフォリオ型）の検証の入力。
    入力: mkt "jp"|"us"、field close|open|high|low|volume、end（既定=封印の始まり。None で全期間＝フォワード専用）
    返り値: DataFrame(index=date, columns=symbol)
    禁止: end=None を判定に使う検証で指定しない
    """
    df = pd.read_parquet(os.path.join(DIR, f"{mkt}_daily.parquet"), columns=["date", "symbol", field])
    if end is not None: df = df[df["date"] < pd.Timestamp(end)]
    if start is not None: df = df[df["date"] >= pd.Timestamp(start)]
    out = df.pivot(index="date", columns="symbol", values=field).sort_index()
    if field != "volume":
        out = out.where(out > 0)   # 調整後の価格が 0 になる銘柄（8919.T 等 4 銘柄）を欠損にする
    return out

def _avail(asof):
    return asof + pd.offsets.BDay(1)   # 公表は取引日の引け後。保守的に翌営業日から使える扱い

def load_short_ratio(kind="market", end=SEAL):
    """JPX 空売り集計（日次）。market=市場全体、sector=業種別。avail 列=使える最初の日。"""
    d = pd.read_csv(os.path.join(DIR, "jpx", f"short_ratio_{kind}.csv"), parse_dates=["asof"])
    d["avail"] = d["asof"].map(_avail)
    return d if end is None else d[d["avail"] < pd.Timestamp(end)]

def load_margin(side="buy", end=SEAL):
    """JPX 銘柄別信用取引残高（日次・全銘柄）。side=buy|sell。蓄積した日だけ（過去には遡れない）。"""
    d = pd.read_parquet(os.path.join(DIR, "jpx", "margin_by_issue.parquet"))
    d["avail"] = d["pub_date"]
    if end is not None: d = d[d["avail"] < pd.Timestamp(end)]
    return d.pivot(index="avail", columns="code", values=side)
