# -*- coding: utf-8 -*-
"""Q591 用: レンジ通貨ペア 5 本の H1（Bid/Ask）を Dukascopy から取得（既存の fetch_dukascopy.py の取得関数を使う）。
出力: 作業層/大容量/market_data/H1_cross/<sym>.parquet（time・open/high/low/close＝Bid・spread＝ask_close−close）。再実行は安全（月キャッシュ）。"""
import datetime as dt, importlib.util, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sp = importlib.util.spec_from_file_location("fd", os.path.join(WS, "検証", "学問", "金融工学", "作業", "ML自動売買", "fetch_dukascopy.py"))
FD = importlib.util.module_from_spec(sp); sp.loader.exec_module(FD)
SYMS = ["AUDNZD", "AUDCAD", "NZDCAD", "EURCHF", "CADCHF"]; OUT = os.path.join(FD.OUT, "H1_cross"); os.makedirs(OUT, exist_ok=True)
today = dt.date.today(); months = [(y, m) for y in range(2010, today.year + 1) for m in range(1, 13) if (y, m) < (today.year, today.month)]
jobs = [(s, s, side, y, m) for s in SYMS for side in FD.SIDES for y, m in months]
print("リクエスト", len(jobs), flush=True); res = {}; fail = 0
with ThreadPoolExecutor(4) as ex:
    fs = [ex.submit(FD.ensure_month, *j) for j in jobs]
    for i, f in enumerate(as_completed(fs), 1):
        n, side, y, m, data = f.result()
        if data is None: fail += 1
        else: res[(n, side, y, m)] = data
        if i % 200 == 0: print(i, "/", len(jobs), "失敗", fail, flush=True)
for s in SYMS:
    fr = {}
    for side in FD.SIDES:
        rows = []
        for y, m in months: rows += FD.decode(res.get((s, side, y, m), b""), y, m)
        d = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"]).drop_duplicates("time").set_index("time").sort_index()
        fr[side] = d
    k = 1e5 if fr["BID"]["close"].median() > 1000 else 1.0
    b, a = fr["BID"] / k, fr["ASK"] / k
    d = b[["open", "high", "low", "close"]].copy(); d["volume"] = fr["BID"]["volume"]; d["spread"] = (a["close"] - b["close"]).reindex(d.index)
    d = d[d["volume"] > 0].reset_index(); d.to_parquet(os.path.join(OUT, f"{s}.parquet"), index=False)
    print(s, len(d), d["time"].min(), d["time"].max(), "close 中央値", round(d["close"].median(), 4), "spread 中央値", round(d["spread"].median(), 6), flush=True)
print("完了 失敗", fail)
