# Q574 事後の記述（判定規則は変えない）: USDCAD の NY 時刻別 1 本平均（BID・bp）と 1 次自己相関。生き残り 2 セルが NY 17:00 ロールオーバーの BID 落ち込みの戻りを拾っているかを見る。
import os, numpy as np, pandas as pd
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 5))
d = pd.read_csv(os.path.join(WS, "検証/学問/金融工学/作業/FX/システムトレード/data_USDCAD_H1_dukascopy.csv"), usecols=["time", "close"])
d["time"] = pd.to_datetime(d["time"]).dt.tz_localize("UTC"); d = d[(d.time < "2024-07-01") & (d.time.dt.dayofweek < 5)].copy()
d["r"] = np.log(d.close).diff() * 1e4; d["ny"] = d.time.dt.tz_convert("America/New_York").dt.hour; d["per"] = np.where(d.time.dt.year < 2017, "pre", "post")
print(d.groupby(["per", "ny"]).r.mean().unstack(0).loc[14:21].round(3))
for p in ["pre", "post"]:
    x = d[d.per == p].set_index("time"); lag = x.r.shift(1)
    print(p, {h: round(x.r[x.ny == h].corr(lag[x.ny == h]), 3) for h in range(16, 21)})
