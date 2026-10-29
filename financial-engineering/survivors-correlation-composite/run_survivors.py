# -*- coding: utf-8 -*-
"""記述（新しい検定ではない）: 生き残り 3 本（S17b・S21 候補形・S23）の日次損益をそろえ、相関・単体と合成のシャープ・最大下落を出す。
- S17b: main13（指数 10＋BUND・UKGILT・XAUUSD）の等金額買い持ち − 保有コスト年 4%（run_q543.py と同じ）
- S21: s21-h1-ml-rr-weekcap-q515/results/trades_q534_E1.csv（候補形 Q533 D2＋Q534 E1）の R を決済日で日次合計（WF の標本外）
- S23: s23-crypto-uptrend-long-q529/results/daily_q529.csv の main（BTC・ETH 半分ずつ・名目 1 倍）
合成: 各本を共通期間の日次σでそろえた等リスク（1/3）。週次（金曜締め）の相関も出す（暗号の週末・時差の影響を見るため）。"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(FE, "..", "tools"))
from fe_core import load_d1
IDX10 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "AUS200", "SUI20"]
M13 = IDX10 + ["BUND", "UKGILT", "XAUUSD"]
R = {}
for s in M13:
    d = load_d1(s); d = d[(d["time"] >= "2012-02-01") & (d["time"] < "2026-07-01")]
    R[s] = pd.Series(d["ret"].to_numpy(), index=pd.DatetimeIndex(d["time"]).tz_localize(None).normalize())
s17b = pd.DataFrame(R).sort_index().mean(axis=1, skipna=True) - 0.04 / 252
t = pd.read_csv(os.path.join(FE, "s21-h1-ml-rr-weekcap-q515", "results", "trades_q534_E1.csv"))
ex = pd.to_datetime(t["exit"], utc=True).dt.tz_localize(None).dt.normalize()
s21 = t.groupby(ex)["R"].sum()
c = pd.read_csv(os.path.join(FE, "s23-crypto-uptrend-long-q529", "results", "daily_q529.csv"), index_col=0, parse_dates=True)
s23 = c["main"]; s23.index = pd.DatetimeIndex(s23.index).normalize()
ser = {"S17b 買い持ち": s17b, "S21 H1 ML": s21, "S23 暗号の上昇時": s23}
span = {k: (str(v.index.min().date()), str(v.index.max().date())) for k, v in ser.items()}
a = max(v.index.min() for v in ser.values()); b = min(v.index.max() for v in ser.values())
idx = pd.date_range(a, b, freq="D")
D = pd.DataFrame({k: v.reindex(idx).fillna(0.0) for k, v in ser.items()})
D = D[D.index.dayofweek < 5].add(D[D.index.dayofweek >= 5].groupby(lambda x: x + pd.Timedelta(days=7 - x.dayofweek)).sum().reindex(D[D.index.dayofweek < 5].index).fillna(0.0), fill_value=0.0)  # 週末の損益は月曜へ
W = D.resample("W-FRI").sum()
Z = D / D.std(ddof=1)  # 等リスク化
Z["合成（1/3 等リスク）"] = Z[list(ser)].mean(axis=1)
pairs = [("S17b 買い持ち", "S21 H1 ML"), ("S17b 買い持ち", "S23 暗号の上昇時"), ("S21 H1 ML", "S23 暗号の上昇時")]
for p in pairs:
    Z["合成 " + " + ".join(x.split()[0] for x in p)] = Z[list(p)].mean(axis=1)
def st(x):
    x = x.dropna(); cum = x.cumsum(); y = x.groupby(x.index.year).mean()
    return {"sharpe": round(float(x.mean() / x.std(ddof=1) * np.sqrt(252)), 3), "maxdd_in_daily_sigma": round(float((cum - cum.cummax()).min() / x.std(ddof=1)), 1),
            "年ごと正の割合": round(float((y > 0).mean()), 2), "years": int(len(y))}
res = {"期間（共通）": [str(a.date()), str(b.date())], "各本の元の期間": span,
       "日次相関": D.corr().round(3).to_dict(), "週次相関": W.corr().round(3).to_dict(),
       "成績（等リスク化後・共通期間）": {k: st(Z[k]) for k in Z.columns},
       "前後半（2021 で分割）": {k: {"前": st(Z[k][Z.index < "2021-01-01"]), "後": st(Z[k][Z.index >= "2021-01-01"])} for k in Z.columns}}
json.dump(res, open(os.path.join(HERE, "results", "survivors_corr.json"), "w"), ensure_ascii=False, indent=1)
Z.to_csv(os.path.join(HERE, "results", "survivors_daily_eqrisk.csv"))
print(json.dumps(res, ensure_ascii=False, indent=1))
