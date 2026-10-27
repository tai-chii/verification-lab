# -*- coding: utf-8 -*-
"""MT5 の「仕様」のスワップ値から、S23（BTC・ETH）と S17b（指数・債券・金）の期待値を出し直す（2026-10-27・taichi 待ち 1 の受け皿）。
検証ではない（規則も判定も変えない・試行に数えない）。結果は「スワップ込みの感度」として戦略台帳・README に書く。

使い方（Mac。pyarrow のある venv_forward で）:
  いちばん楽: MT5 で S21_SymbolSpecs.mq5 を走らせ、出た CSV を渡すだけ（スワップの型・値・桁・契約サイズを全部読む）
  $PY swap_from_mt5.py --h1 ~/ワークスペース/作業層/大容量/crypto_h1_hist --specs <MQL5/Files/symbol_specs_….csv>
  手で入れるとき:
  PY=~/ワークスペース/作業層/大容量/venv_forward/bin/python
  $PY swap_from_mt5.py --h1 ~/ワークスペース/作業層/大容量/crypto_h1_hist \\
      --swap BTCUSD=points:-25.5:0.01 --swap ETHUSD=points:-3.2:0.01 --swap US500=points:-1.8:0.01
  （S17b だけなら --h1 を省く。S23 だけなら US500 を省く）

--swap 記号=型:値[:補助]   MT5 の「仕様」の「スワップの計算方法」「買いスワップ」をそのまま写す。値は MT5 の符号のまま（負＝払う）。
  points:値:point      ポイント建て（1 ロット 1 晩あたり 値×point の価格幅）。point は「仕様」の小数点以下の桁から（例 0.01）
  pct:値               年率 %（現在価格／建値に対して）。MT5 の「パーセント」系はこれ
  money:値:契約サイズ  1 ロット 1 晩あたりの金額（口座通貨。口座が USD 前提。JPY 口座なら --usdjpy で換算）
  annual:値            年率 % をそのまま（手で換算済みのとき）
--price 記号=価格   points・money の換算に使う価格（省略時はデータの最後の終値）
--nights 365        1 年あたりの課金の晩数（3 倍デーで週末を払う方式でも 365。課金が平日 5 晩だけなら 260）
S17b の他 12 銘柄は、値が無ければ US500 と同じ年率を仮に使う（出力に「仮」と出す）。
"""
import argparse, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "s22-crypto-ml-fintokei-q528"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))


def annual_cost(spec, price, nights, usdjpy=None):
    """MT5 の買いスワップ → 年率の保有コスト（名目に対する比率。正＝払う）。"""
    kind, *v = spec.split(":")
    val = float(v[0])
    if kind == "annual" or kind == "pct":
        return -val / 100.0
    if kind == "points":
        point = float(v[1]); return -(val * point / price) * nights
    if kind == "money":
        cs = float(v[1]); amt = val / usdjpy if usdjpy else val
        return -(amt / (cs * price)) * nights
    raise SystemExit(f"型が分からない: {kind}")


ALIASES = {"US500": ["US500", "SPX500", "SP500", "US500.cash"], "USTECH": ["USTECH", "US100", "NAS100", "USTEC", "NDX100"],
           "US30": ["US30", "DJ30", "WS30", "US30.cash"], "GER40": ["GER40", "DE40", "DAX40", "GER30", "DE30"],
           "JPN225": ["JPN225", "JP225", "NIKKEI225", "JPN225.cash"], "UK100": ["UK100", "FTSE100"], "FRA40": ["FRA40", "FR40", "CAC40"],
           "ESP35": ["ESP35", "SPA35", "ES35"], "AUS200": ["AUS200", "AU200"], "SUI20": ["SUI20", "SWI20", "CH20"],
           "BUND": ["BUND", "EUBUND", "DE10YB", "BUND.f"], "UKGILT": ["UKGILT", "UK10YB", "GILT"], "XAUUSD": ["XAUUSD", "GOLD"],
           "BTCUSD": ["BTCUSD"], "ETHUSD": ["ETHUSD"]}


def resolve(names, want):
    """業者の銘柄名から、こちらの名前（US500 など）に当たるものを探す。1) 一致 2) 先頭一致（+6 字まで）。"""
    up = {n.upper(): n for n in names}
    for a in ALIASES.get(want, [want]):
        if a.upper() in up:
            return up[a.upper()]
    for a in ALIASES.get(want, [want]):
        for n in names:
            if n.upper().startswith(a.upper()) and len(n) <= len(a) + 6:
                return n
    return None


def rate_from_spec(r, nights):
    """S21_SymbolSpecs.mq5 の 1 行 → 年率の保有コスト（買い・正＝払う）。"""
    mode, val = r["swap_mode_name"], float(r["swap_long"])
    px = (float(r["bid"]) + float(r["ask"])) / 2 or float(r["ask"]) or float(r["bid"])
    cs, pt = float(r["contract_size"]), float(r["point"])
    tv, ts = float(r["tick_value"]), float(r["tick_size"])
    if mode == "DISABLED":
        return 0.0
    if mode == "POINTS":
        return -(val * pt / px) * nights
    if mode.startswith("INTEREST"):
        return -val / 100.0
    if mode in ("CURRENCY_SYMBOL", "CURRENCY_MARGIN"):          # 基軸通貨で 1 ロットあたり
        return -(val / cs) * nights
    if mode == "CURRENCY_PROFIT":                                # 決済通貨で 1 ロットあたり
        return -(val / (cs * px)) * nights
    if mode == "CURRENCY_DEPOSIT":                               # 口座通貨で 1 ロットあたり。名目（口座通貨）= 価格 × tick_value / tick_size
        return -(val / (px * tv / ts)) * nights
    raise SystemExit(f"{r['name']}: 換算できない型 {mode}（{val}）。--swap で手で入れる")


def from_specs(path, nights):
    import csv
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig", errors="replace")))
    names = [r["name"] for r in rows]; by = {r["name"]: r for r in rows}
    rates, table = {}, []
    for want in ALIASES:
        n = resolve(names, want)
        if not n:
            table.append((want, "（見つからない）", "", "", "")); continue
        r = by[n]
        try:
            rates[want] = rate_from_spec(r, nights)
            table.append((want, n, r["swap_mode_name"], r["swap_long"], f"{rates[want]*100:+.2f}%/年"))
        except SystemExit as e:
            table.append((want, n, r["swap_mode_name"], r["swap_long"], str(e)))
    return rates, table


def s23(h1dir, rates):
    import run_q529 as R
    bs = {c: R.daily_series(h1dir, c) for c in ["BTC", "ETH"]}
    for c in bs:
        bs[c] = bs[c].set_index(bs[c]["day"].dt.tz_convert(None), drop=False); bs[c]["day"] = bs[c].index
    out = {}
    for label, rr in [("スワップ0", {"BTC": 0.0, "ETH": 0.0})] + [(f"年率{int(x*100)}%（両方）", {"BTC": x, "ETH": x}) for x in (0.10, 0.20, 0.30)] + [("MT5の値", rates)]:
        parts, bh = [], []
        for c, b in bs.items():
            idx = pd.DatetimeIndex(b.index)
            gap = np.r_[np.diff(idx.values).astype("timedelta64[h]").astype(float) / 24.0, 1.0]   # 次の行までの暦日（週末を含む）
            chg = rr[c] * gap / 365.0
            pos = R.tsmom(b, 60)
            parts.append(R.backtest(b, pos, R.HALF[c]) - pos * chg)
            ones = np.ones(len(b)); bh.append(R.backtest(b, ones, R.HALF[c]) - ones * chg)
        m, h = R.stats(R.combine(parts), "S23"), R.stats(R.combine(bh), "買って持つ")
        out[label] = {"S23": {k: round(m[k], 3) for k in ("sharpe", "cagr", "max_dd", "t")},
                      "買って持つ": {k: round(h[k], 3) for k in ("sharpe", "cagr", "max_dd")}, "年率コスト": {k: round(v, 4) for k, v in rr.items()}}
    return out


def s17b(rates_by_sym, default):
    from fe_core import load_d1
    IDX10 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "AUS200", "SUI20"]
    syms = IDX10 + ["BUND", "UKGILT", "XAUUSD"]
    DEV = (pd.Timestamp("2012-02-01"), pd.Timestamp("2024-07-01")); HO = (pd.Timestamp("2024-07-01"), pd.Timestamp("2026-07-01"))
    P = {}
    for s in syms:
        d = load_d1(s); d = d[(d["time"] >= DEV[0]) & (d["time"] < HO[1])]
        P[s] = pd.Series(d["ret"].to_numpy(), index=pd.DatetimeIndex(d["time"]).normalize())
    P = pd.DataFrame(P).sort_index()
    used = {s: rates_by_sym.get(s, default) for s in syms}
    cost = pd.Series(used) / 252.0
    p = (P[syms] - cost).mean(axis=1, skipna=True)
    res = {"年率コスト": {s: round(v, 4) for s, v in used.items()}, "仮に US500 の値を使った銘柄": [s for s in syms if s not in rates_by_sym]}
    for per, (a, b) in (("開発 2012-02〜2024-06", DEV), ("ホールドアウト 2024-07〜2026-06", HO)):
        x = p[(p.index >= a) & (p.index < b)].dropna(); cum = x.cumsum()
        res[per] = dict(mean_bp=round(float(x.mean() * 1e4), 2), t_daily=round(float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))), 2),
                        annual_pct=round(float(x.mean() * 252 * 100), 1), max_dd=round(float((cum - cum.cummax()).min()), 3))
    dv, ho = res["開発 2012-02〜2024-06"]["mean_bp"], res["ホールドアウト 2024-07〜2026-06"]["mean_bp"]
    res["事前登録の合格条件（ホールドアウトが正かつ開発の 1/2 以上）"] = "満たす" if (ho > 0 and ho >= 0.5 * dv) else "満たさない"
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h1"); ap.add_argument("--swap", action="append", default=[]); ap.add_argument("--price", action="append", default=[])
    ap.add_argument("--specs", help="S21_SymbolSpecs.mq5 が書いた symbol_specs_*.csv"); ap.add_argument("--nights", type=float, default=365.0); ap.add_argument("--usdjpy", type=float); ap.add_argument("--out", default=os.path.join(HERE, "results"))
    a = ap.parse_args()
    prices = {k: float(v) for k, v in (x.split("=") for x in a.price)}
    specs = dict(x.split("=", 1) for x in a.swap)
    last = {}
    if a.h1:
        import crypto_core as C
        for c in ("BTC", "ETH"):
            last[c + "USD"] = float(C.load_h1(a.h1, c)["close"].iloc[-1])
    if any(k not in ("BTCUSD", "ETHUSD") for k in specs):
        from fe_core import load_d1
        for k in specs:
            if k not in ("BTCUSD", "ETHUSD"):
                last[k] = float(load_d1(k)["close"].iloc[-1])
    rates = {k: annual_cost(v, prices.get(k, last.get(k, np.nan)), a.nights, a.usdjpy) for k, v in specs.items()}
    out = {"入力": specs, "換算に使った価格": {k: prices.get(k, last.get(k)) for k in specs}}
    if a.specs:
        r2, table = from_specs(a.specs, a.nights)
        r2.update(rates); rates = r2                       # --swap で渡した値が優先
        out["仕様CSV"] = {"file": a.specs, "対応": [dict(zip(["こちら", "業者の名前", "型", "買いスワップ", "年率"], t)) for t in table]}
        print("銘柄の対応とスワップ:"); [print("  ", *t) for t in table]
    out["年率コスト（正＝払う）"] = {k: round(v, 4) for k, v in rates.items()}
    if a.h1:
        out["S23"] = s23(a.h1, {"BTC": rates.get("BTCUSD", 0.0), "ETH": rates.get("ETHUSD", 0.0)})
    if "US500" in rates:
        try:
            out["S17b"] = s17b({k: v for k, v in rates.items() if k not in ("BTCUSD", "ETHUSD")}, rates["US500"])
        except Exception as e:                      # fe_core・D1 データが無い環境でも S23 の結果は残す
            out["S17b"] = f"計算できなかった: {e!r}"
    os.makedirs(a.out, exist_ok=True)
    fn = os.path.join(a.out, "swap_from_mt5.json")
    json.dump(out, open(fn, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str)); print("→", fn)


if __name__ == "__main__":
    main()
