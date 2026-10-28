#!/usr/bin/env python3
"""Q562 (1): yfinance で日本株・米国株の日足を取得し 作業層/大容量/equities_free/ に parquet で置く。
基盤整備（検証ではない）。合否は check_gate.py で「10年以上・欠損率5%未満・需給が2年以上つながる」。
使い方: venv_equities/bin/python fetch_prices.py jp|us
- 銘柄表: JP=JPX data_j.xlsx のプライム＋スタンダード（内国株）／US=S&P500+S&P400（Wikipedia 現構成。Russell1000 は無料で現構成表が取れず代用）
- 現在の上場銘柄のみ＝生存バイアスあり（README に注記）。調整済み終値（auto_adjust=True）。
- 再開可能: chunks/ に 100 銘柄ごとの parquet を置き、あれば飛ばす。
"""
import os, sys, time, datetime as dt
from io import StringIO
import pandas as pd, requests, yfinance as yf

WS = os.path.expanduser("~/ワークスペース")
OUT = os.path.join(WS, "作業層", "大容量", "equities_free")
START = "2005-01-01"
H = {"User-Agent": "Mozilla/5.0"}

def universe(mkt):
    if mkt == "jp":
        r = requests.get("https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xlsx", headers=H, timeout=60)
        p = os.path.join(OUT, "_src_data_j.xlsx"); open(p, "wb").write(r.content)
        d = pd.read_excel(p, dtype={"コード": str})
        d = d[d["市場・商品区分"].isin(["プライム（内国株式）", "スタンダード（内国株式）"])]
        return pd.DataFrame({"symbol": d["コード"].str.strip() + ".T", "name": d["銘柄名"], "market": d["市場・商品区分"], "sector": d["33業種区分"]})
    out = []
    for url, tag in [("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", "SP500"), ("https://en.wikipedia.org/wiki/List_of_S%26P_400_companies", "SP400")]:
        t = pd.read_html(StringIO(requests.get(url, headers=H, timeout=60).text))[0]
        sc = "Symbol" if "Symbol" in t.columns else [c for c in t.columns if "Ticker" in str(c) or "Symbol" in str(c)][0]
        nc = "Security" if "Security" in t.columns else t.columns[1]
        out.append(pd.DataFrame({"symbol": t[sc].astype(str).str.replace(".", "-", regex=False), "name": t[nc], "market": tag, "sector": ""}))
    return pd.concat(out).drop_duplicates("symbol").reset_index(drop=True)

def main():
    mkt = sys.argv[1]
    os.makedirs(os.path.join(OUT, "chunks", mkt), exist_ok=True)
    u = universe(mkt); u.to_csv(os.path.join(OUT, f"universe_{mkt}.csv"), index=False)
    syms = u["symbol"].tolist(); print(mkt, len(syms), flush=True)
    for i in range(0, len(syms), 100):
        cp = os.path.join(OUT, "chunks", mkt, f"{i:05d}.parquet")
        if os.path.exists(cp): continue
        ch = syms[i:i+100]
        for attempt in range(3):
            try:
                d = yf.download(ch, start=START, auto_adjust=True, progress=False, threads=True, group_by="ticker")
                break
            except Exception as e:
                print("retry", i, e, flush=True); time.sleep(20)
        else:
            continue
        rows = []
        for s in ch:
            try: x = d[s].dropna(how="all")
            except KeyError: continue
            if len(x) == 0: continue
            x = x.reset_index().rename(columns=str.lower)
            x["symbol"] = s; rows.append(x[["date", "symbol", "open", "high", "low", "close", "volume"]])
        if rows: pd.concat(rows).to_parquet(cp)
        else: pd.DataFrame(columns=["date"]).to_parquet(cp)
        print("chunk", i, len(rows), time.strftime("%H:%M:%S"), flush=True)
    parts = [pd.read_parquet(os.path.join(OUT, "chunks", mkt, f)) for f in sorted(os.listdir(os.path.join(OUT, "chunks", mkt)))]
    df = pd.concat([p for p in parts if len(p)]); df["date"] = pd.to_datetime(df["date"])
    df.to_parquet(os.path.join(OUT, f"{mkt}_daily.parquet"))
    g = df.groupby("symbol")["date"].agg(["min", "max", "count"])
    g.to_csv(os.path.join(OUT, f"manifest_{mkt}_symbols.csv"))
    print("done", mkt, len(g), "symbols", len(df), "rows", flush=True)

if __name__ == "__main__":
    main()
