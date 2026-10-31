# -*- coding: utf-8 -*-
"""Q591 のスワップの感度（判定の規則・銘柄・パラメータは Q591 のまま。記述）。
シナリオ: スワップ 0／FX マークアップ 0・CFD 0／0.75%（Q591 と同じ）／1.5%／3%、それに --specs があれば実スワップ。
実スワップの当て方: MT5 が返すのは今の値だけなので、銘柄ごとに「今の金利差 − 今の実スワップ」で業者のマークアップを買い・売り別に求め、過去の金利差から引く（CFD は通貨の金利の変化だけ動かす）。
使い方: 作業層/venv_grid/bin/python swap_scenarios_q591.py [--specs lab-ops/trade/winnote/symbol_specs_*.csv] [--B 200]"""
import argparse, csv, importlib.util, json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sp = importlib.util.spec_from_file_location("q591", os.path.join(HERE, "kensho_traprepeat_q591.py")); Q = importlib.util.module_from_spec(sp); sp.loader.exec_module(Q)
CFD_CCY = {"XAUUSD": "USD", "US500": "USD", "USTECH": "USD", "GER40": "EUR", "JPN225": "JPY"}
ALIAS = {"US500": ["US500Cash", "US500"], "USTECH": ["US100Cash", "USTECH", "NAS100"], "GER40": ["GER40Cash", "GER40", "DE40Cash"], "JPN225": ["JP225Cash", "JPN225", "JP225"], "XAUUSD": ["GOLD", "XAUUSD"]}


def annual(mode, v, r, usdjpy_deposit):
    """MT5 のスワップ値 → 名目に対する年率。3 倍デーで週 7 晩ぶんを払うので 1 晩平均 ×365"""
    price = (float(r["bid"]) + float(r["ask"])) / 2; pt = float(r["point"]); cs = float(r["contract_size"])
    if mode == "POINTS": return v * pt / price * 365
    if mode.startswith("INTEREST") or mode.startswith("REOPEN"): return v / 100
    if mode in ("CURRENCY_SYMBOL", "CURRENCY_MARGIN", "CURRENCY_PROFIT"): return v / (cs * price) * 365
    if mode == "CURRENCY_DEPOSIT":
        tv, ts = float(r["tick_value"]), float(r["tick_size"]); notional_dep = cs * price * tv / (ts * cs) if tv and ts else np.nan   # 1 ロットの名目（口座通貨）
        return v / notional_dep * 365
    return 0.0


def load_specs(path):
    T = {}
    for r in csv.DictReader(open(path, encoding="utf-8")): T[r["name"]] = r
    return T


def find(T, s):
    for n in ALIAS.get(s, [s]):
        for k in (n, n + "#", n + ".", n + "."):
            if k in T: return T[k]
    c = [k for k in T if k.upper().startswith(s)]
    return T[c[0]] if c else None


def real_markups(T, R):
    now = np.array([np.datetime64("2026-10-31", "D").astype(np.int64)]); out = {}
    for s in sorted(set(sum(Q.FAM.values(), []))):
        r = find(T, s)
        if r is None: out[s] = None; continue
        al, ash = annual(r["swap_mode_name"], float(r["swap_long"]), r, None), annual(r["swap_mode_name"], float(r["swap_short"]), r, None)
        if s in CFD_CCY: b = float(Q.rate_at(R, CFD_CCY[s], now)[0]); out[s] = dict(name=r["name"], mode=r["swap_mode_name"], long=al, short=ash, rate_now=b)
        else:
            d = float(Q.rate_at(R, s[:3], now)[0] - Q.rate_at(R, s[3:6], now)[0]); out[s] = dict(name=r["name"], mode=r["swap_mode_name"], long=al, short=ash, diff_now=d, m_long=d - al, m_short=-d - ash)
    return out


def swap_fn(sc, R, real):
    def f(s, days):
        n = len(days)
        if sc == "real":
            k = real[s]
            if s in CFD_CCY: dr = Q.rate_at(R, CFD_CCY[s], days) - k["rate_now"]; return k["long"] - dr, k["short"] + dr
            d = Q.rate_at(R, s[:3], days) - Q.rate_at(R, s[3:6], days); return d - k["m_long"], -d - k["m_short"]
        if s in Q.CFD5:
            return (np.full(n, -0.04), np.full(n, -0.01)) if sc == 0.0075 or isinstance(sc, float) and sc > 0 else (np.zeros(n), np.zeros(n))
        d = Q.rate_at(R, s[:3], days) - Q.rate_at(R, s[3:6], days); return d - sc, -d - sc
    return f


def one(fam, data, R, ct, pay, rng, B):
    """F2 の方向は常に Q591 と同じ（0.75% 後のスワップが正の方向）。実シナリオだけ実スワップの向きで決める"""
    dirf = swap_fn(0.0075, R, None)
    def net(x, p, s):
        pl, ps = (np.zeros(p["D"]), np.zeros(p["D"])) if pay is None else pay(s, p["days"])
        dl, ds = dirf(s, p["days"]) if pay is None else (pl, ps)
        D = p["D"]; none = np.zeros(D, bool)
        if fam == "F1": mode = np.full(D, 2, np.int64); mode[~(p["sma"] > 0)] = 0; reset = p["reset"]
        elif fam == "F2": mode = np.where(dl > 0, 1, np.where(ds > 0, -1, 0)).astype(np.int64); reset = p["reset"]
        else: mode = p["trend"]; reset = none
        d, _, _ = Q.to_df(Q.sim(x["o"], x["h"], x["l"], x["c"], p["bar"], D, mode, reset, p["atr"], p["sma"], Q.K, Q.N, fam == "F1", ct["rel"][s], pl / 365.0, ps / 365.0, p["nights"]), p["days"])
        return d["g"] - d["c"] + d["s"]
    obs = pd.concat([net(*data[s], s) for s in Q.FAM[fam]], axis=1, sort=True).mean(axis=1); obs = obs[obs.index >= Q.EVAL]; st = Q.stats(obs); vals = []
    for _ in range(B):
        fr = []
        for s in Q.FAM[fam]:
            x = Q.synth(data[s][0], rng, data[s][0]["sig"]); fr.append(net(x, Q.prep(x), s))
        m = pd.concat(fr, axis=1, sort=True).mean(axis=1); vals.append(float(m[m.index >= Q.EVAL].mean()))
    vals = np.array(vals); z = float((obs.mean() - vals.mean()) / vals.std()); c = Q.G.gate(obs, fam)
    return dict(mean_bp=st["mean_bp"], t_nw=st["t_nw"], pf=st["pf"], h1_bp=st["h1_bp"], h2_bp=st["h2_bp"], z=z, null_mean_bp=1e4 * float(vals.mean()), null_sd_bp=1e4 * float(vals.std()), composite=c["関門"]["通過"], verdict=Q.verdict(st, z, c))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--specs"); ap.add_argument("--B", type=int, default=200); a = ap.parse_args()
    ct = Q.cost_table(); R = Q.rate_series(); data = {}
    for s in sorted(set(sum(Q.FAM.values(), []))):
        x = Q.add_sig(Q.load_sym(s)); data[s] = (x, Q.prep(x))
    res = {}; real = None
    SC = [("スワップ 0", None), ("マークアップ 0", 0.0), ("0.75%（Q591）", 0.0075), ("1.5%", 0.015), ("3%", 0.03)]
    if a.specs:
        real = real_markups(load_specs(a.specs), R); res["実スワップの換算"] = real; miss = [k for k, v in real.items() if v is None]; res["見つからない銘柄"] = miss
        print("見つからない銘柄", miss); [print(k, {q: (round(w, 4) if isinstance(w, float) else w) for q, w in v.items()}) for k, v in real.items() if v]
        if miss: raise SystemExit("銘柄名の対応が足りない。ALIAS を直す")
        SC = [("実スワップ", "real")]
    for name, sc in SC:
        rng = np.random.default_rng(20261031); pay = None if sc is None else swap_fn(sc, R, real); res[name] = {}
        for fam in Q.FAM:
            r = one(fam, data, R, ct, pay, rng, a.B); res[name][fam] = r
            print(f"{name:14} {fam} 平均 {r['mean_bp']:+.3f} t {r['t_nw']:+.2f} PF {r['pf']:.3f} 前後 {r['h1_bp']:+.2f}/{r['h2_bp']:+.2f} z {r['z']:+.2f} 帰無 {r['null_mean_bp']:+.3f}±{r['null_sd_bp']:.3f} composite {r['composite']} → {r['verdict']}", flush=True)
    json.dump(res, open(os.path.join(HERE, "results", "swap_real_q591.json" if a.specs else "swap_scenarios_q591.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
