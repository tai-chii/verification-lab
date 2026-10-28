#!/usr/bin/env python3
"""Q562 合否判定: 価格層 10年以上・欠損率5%未満、需給が2年以上つながる。結果は results/ と 大容量/equities_free/manifest.json。"""
import os, sys, json, datetime as dt
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import equities_free as ef

res = {"generated": dt.datetime.now().isoformat(timespec="seconds"), "gate": "10年以上・欠損率5%未満・需給が2年以上つながる", "prices": {}}
for mkt in ("jp", "us"):
    df = pd.read_parquet(os.path.join(ef.DIR, f"{mkt}_daily.parquet"))
    cal = np.sort(df["date"].unique())                      # 市場の取引日（その市場の全銘柄の日付の和集合）
    cal = pd.DatetimeIndex(cal)
    g = df.groupby("symbol")["date"].agg(["min", "max", "count"])
    # 欠損率 = 自分の初日〜最終日の間の取引日のうち、データが無い日の割合（上場前・廃止後は数えない）
    ncal = np.array([((cal >= r["min"]) & (cal <= r["max"])).sum() for _, r in g.iterrows()])
    g["miss"] = 1 - g["count"] / ncal
    g["years"] = (g["max"] - g["min"]).dt.days / 365.25
    last = cal.max()
    stale = (last - g["max"]).dt.days > 10                   # 最終日が古い＝取得失敗か上場廃止
    n = len(g)
    u = pd.read_csv(os.path.join(ef.DIR, f"universe_{mkt}.csv"))
    ret = df.sort_values(["symbol", "date"]).assign(r=lambda x: x.groupby("symbol")["close"].pct_change())
    px = ef.load(mkt, "close", end=None)
    cnt_by_year = px.notna().sum(axis=1).groupby(px.index.year).median().astype(int).to_dict()
    ok10 = g["years"] >= 10
    res["prices"][mkt] = dict(
        n_universe=int(len(u)), n_with_data=int(n), n_no_data=int(len(u) - n), first=str(cal.min().date()), last=str(last.date()), n_days=int(len(cal)),
        n_10y_plus=int(ok10.sum()), share_10y_plus=round(float(ok10.mean()), 3),
        miss_median=round(float(g["miss"].median()), 5), miss_mean=round(float(g["miss"].mean()), 5),
        share_miss_lt5pct=round(float((g["miss"] < 0.05).mean()), 4), share_miss_lt5pct_among_10y=round(float((g.loc[ok10, "miss"] < 0.05).mean()), 4),
        n_stale=int(stale.sum()), n_abs_ret_gt_50pct=int((ret["r"].abs() > 0.5).sum()), n_zero_close=int((df["close"] <= 0).sum()),
        median_names_per_day_by_year=cnt_by_year,
        gate_prices_pass=bool((g.loc[ok10, "miss"] < 0.05).mean() >= 0.9 and cal.min().year <= 2006 and ok10.sum() >= 0.5 * len(u)))
    g.reset_index().to_csv(os.path.join(ef.DIR, f"manifest_{mkt}_symbols.csv"), index=False)

sm = pd.read_csv(os.path.join(ef.DIR, "jpx", "short_ratio_market.csv"), parse_dates=["asof"])
mg = pd.read_parquet(os.path.join(ef.DIR, "jpx", "margin_by_issue.parquet"))
span = lambda s: round((s.max() - s.min()).days / 365.25, 2)
cal_jp = pd.DatetimeIndex(pd.read_parquet(os.path.join(ef.DIR, "jp_daily.parquet"), columns=["date"])["date"].unique()).sort_values()
exp = ((cal_jp >= sm["asof"].min()) & (cal_jp <= sm["asof"].max())).sum()
res["demand"] = dict(
    short_ratio_market=dict(first=str(sm["asof"].min().date()), last=str(sm["asof"].max().date()), n_days=int(len(sm)), span_years=span(sm["asof"]), missing_vs_jp_calendar=int(exp - len(sm))),
    margin_by_issue=dict(first=str(mg["asof"].min().date()), last=str(mg["asof"].max().date()), n_days=int(mg["asof"].nunique()), span_years=span(mg["asof"]), n_issues_last=int((mg["asof"] == mg["asof"].max()).sum())),
    note="JPX 公式の公開は 空売り=約13か月分のPDF、銘柄別信用残=直近約5営業日分のみ。過去に遡れないので毎日 fetch_jpx.py を回して積み上げる。")
res["demand"]["gate_demand_pass"] = bool(res["demand"]["short_ratio_market"]["span_years"] >= 2 and res["demand"]["margin_by_issue"]["span_years"] >= 2)
res["gate_all_pass"] = bool(all(v["gate_prices_pass"] for v in res["prices"].values()) and res["demand"]["gate_demand_pass"])
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
for p in (os.path.join(HERE, "results", "gate_20261028.json"), os.path.join(ef.DIR, "manifest.json")):
    json.dump(res, open(p, "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
