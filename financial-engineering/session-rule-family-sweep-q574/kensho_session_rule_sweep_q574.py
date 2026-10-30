#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q574: 「時間帯ごとにエッジの種類が違う」は本当か — 5 窓（現地時刻）× 4 つの単純ルール族（MA 交差・BB 逆張り・ブレイクアウト・直近モメンタム、順と逆）× 26 銘柄の総当たりで、
コスト後に Holm を抜け、かつ「その窓だから効く」（窓の並べ替え帰無 z ≥ 2）セルは 1 つでもあるか
================================================================================

【出典】
- 計画（事前登録）: taichi「ロンドンは MA、NY はボリンジャーのように時間帯でエッジが異なる可能性」「7 時間を限界まで計算させたい」（2026-10-30 深夜）。設計 Fable。
- 先行: Q153（M15 の 1 次自己相関の符号は時刻で変わらない・Holm 後 0）、Q242（暗号の時刻効果 0）、Q567（2 本 MA の総当たり 2,660 本はスペックに 0 本）、
  Q571（S21 の東京限定は z 1.95 で未確定）、Q572（金アジア時間は棄却）、Q573（東京カット順張りは棄却・全時刻でコスト負け）。
- 読み: 先行はどれも「向きは時刻で変わらない・効きとコストが変わる」。本案はそれを 4 族 × 5 窓で一度に、総当たりの多重比較を Holm で正しく引いて閉じる。
  期待は「0 セル」（棄却）。1 セルでも残れば、その窓・族を S24 の候補にする。

【仮説（測る前に固定）】
H1: 5 窓 × 36 信号（18 ルール × 順/逆）× 26 銘柄 = 4,680 セルのうち、少なくとも 1 セルが
    (a) コスト後の日次損益の t > 0 かつ、両側 p を 4,680 本で Holm 補正して p_holm < 0.05、
    (b) 前後半（<2017／≥2017）ともコスト後の日次平均 > 0、
    (c) 窓の並べ替え帰無（日内で 24 本の窓ラベルを日ごとに並べ替え、B 回）に対するコスト前の 1 本平均の z ≥ 2（＝その窓だから効く）
    を全部満たす。
H0: そのようなセルは 0。
【データ】`学問/金融工学/作業/FX/システムトレード/data_{SYM}_H1_dukascopy.csv`（26 銘柄・BID）。**2024-07-01 以降は封印**。土日（UTC）は落とす。
【定義】
- 5 窓（現地時刻・夏時間込み・Q571 と同じ）: 東京のみ = 東京 9:00 以降かつロンドン 8:00 前／ロンドンのみ = ロンドン 8:00 以降かつ NY 8:00 前／重複 = NY 8:00 以降かつロンドン 17:00 前／
  NY のみ = ロンドン 17:00 以降かつ NY 17:00 前／深夜 = それ以外。足はその足の始値時刻で窓に属する。
- 18 ルール（終値だけで計算。足 t−1 までの情報で足 t の持ち高を決める）:
  MA 交差 7: (5,20)(5,50)(10,50)(10,100)(20,100)(20,200)(50,200) → sign(短期 SMA − 長期 SMA)
  BB 逆張り 4: (n,k)=(20,1)(20,2)(50,1)(50,2) → |z|>k のとき −sign(z)、ほか 0（z=(close−SMA_n)/SD_n）
  ブレイクアウト 3: n=24,72,168 → close > 直前 n 本の最高終値なら +1、最安なら −1、ほか 0
  直近モメンタム 4: k=1,3,6,24 → sign(close_t − close_{t−k})
  各ルールに「逆」（符号反転）を足して 36 信号。
- 持ち高 pos_t = 信号_{t−1} × [足 t が窓に入る]。損益_t = pos_t × (close_t/close_{t−1} − 1)×1e4 − コスト_RT × |pos_t − pos_{t−1}| / 2。
- コスト（往復 bp・Fintokei 相当の保守値）: 非円メジャー 1.0／円ペア 1.8（≒0.02 円）／XAUUSD 4／XAGUSD 8／US500・USTECH 2／UKOIL・WTI 5／BTC・ETH 10／その他暗号 20。
- 日次損益 = UTC 日で合計。日次 t = 持ち高が 1 本でもあった日の平均÷標準誤差。前後半は 2017-01-01 で切る。
- 帰無 z: 日ごとに 24 本の窓ラベルを並べ替え（窓ごとの本数は日内で保存）、各窓のコスト前 1 本平均を B 回。z = (観測 − 帰無平均)/帰無 SD。
  B は持ち時間（環境変数 Q574_HOURS・既定 6.5 時間）に合わせて較正で自動決定（下限 200・上限 1,000,000。z の精度は 1 万回で十分なので、それ以上は持ち時間を使い切るためだけ）。
【測るもの】セルごとの コスト後 bp/日・日次 t（全・前・後）・p_holm・z・年間 Sharpe（記述）。窓別に「t>0 のセル比率」「平均 t」。全時間帯（窓なし）との差。上位 20 セルの表（記述）。
【判定（事前固定・変更禁止）】(a)(b)(c) を全部満たすセル ≥ 1 → 支持（そのセルを列挙）。(a) を満たすセルが 0 → 棄却。(a) を満たすが (b) か (c) で落ちる → 未確定（「ルールは効くが窓は関係ない」か「前後半で不安定」を記述）。
多重比較: (a) は 4,680 本の Holm。(c) の z は (a) を抜けたセルだけに当てる（族を分けない保守側）。
【捨てた案の数】約 4: 窓×族の交互作用の分散分析（セル単位の Holm で代用）、M15 への拡張（USDJPY のみ・次段階）、S21 の学習を窓別に分ける（重い・Q571 が支持になってから）、パラメータ格子の拡大（Q567 で分布は一様と分かっている）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】設計・コードは Fable。実行は taichi の Mac（ターミナル・数時間）、解釈は Opus。実行者は JSON の main・survivors・machine_verdict を返す。
【実装】**計算済みなら再実行しない**（results/Q574_result_*.json があれば読むだけで終わる）。Q574_HOURS=6.5 python3 kensho_session_rule_sweep_q574.py（較正 → 銘柄ごとに並列 → results/partial/*.json → 統合）／--smoke／--fresh（途中結果を捨てる）／--B 固定
"""
import argparse, datetime as _dt, glob, json, math, os, sys, time, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
QID = "Q574"; SEAL = pd.Timestamp("2024-07-01", tz="UTC"); SPLIT = 2017; SEED = 20261030
WIN = ["東京のみ", "ロンドンのみ", "重複", "NYのみ", "深夜"]
SYMS = ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDJPY", "EURJPY", "GBPJPY", "XAUUSD", "XAGUSD", "US500", "USTECH", "UKOIL", "WTI",
        "BTCUSD", "ETHUSD", "ADAUSD", "BCHUSD", "DOTUSD", "EOSUSD", "LNKUSD", "LTCUSD", "SOLUSD", "XLMUSD", "XRPUSD"]
MA = [(5, 20), (5, 50), (10, 50), (10, 100), (20, 100), (20, 200), (50, 200)]; BB = [(20, 1), (20, 2), (50, 1), (50, 2)]; BO = [24, 72, 168]; MOM = [1, 3, 6, 24]


def cost_bp(sym):
    if sym in ("XAUUSD",): return 4.0
    if sym in ("XAGUSD",): return 8.0
    if sym in ("US500", "USTECH"): return 2.0
    if sym in ("UKOIL", "WTI"): return 5.0
    if sym in ("BTCUSD", "ETHUSD"): return 10.0
    if sym.endswith("USD") and sym[:3] not in ("EUR", "GBP", "AUD", "NZD"): return 20.0
    if "JPY" in sym: return 1.8
    return 1.0


def _p(*parts):
    a = os.path.join(WS, *parts); return a if os.path.exists(a) else os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p); adj = np.empty(m); run = 0.0
    for i, k in enumerate(o):
        run = max(run, (m - i) * p[k]); adj[k] = min(1.0, run)
    return adj


def p_two(t):
    from math import erf, sqrt
    return float(2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))) if np.isfinite(t) else 1.0


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def load(sym, smoke, rng):
    if smoke:
        t = pd.date_range("2012-01-01", "2024-06-30", freq="h", tz="UTC"); n = len(t); c = 100 * np.exp(np.cumsum(rng.normal(0, 0.0008, n)))
        return pd.DataFrame({"time": t, "close": c})
    d = pd.read_csv(_p("検証", "学問", "金融工学", "作業", "FX", "システムトレード", f"data_{sym}_H1_dukascopy.csv"), usecols=["time", "close"])
    d["time"] = pd.to_datetime(d["time"]).dt.tz_localize("UTC"); d = d[d["time"] < SEAL]
    return d.drop_duplicates("time").sort_values("time").reset_index(drop=True)


def windows(t):
    lon = t.dt.tz_convert("Europe/London").dt.hour.values; ny = t.dt.tz_convert("America/New_York").dt.hour.values; tok = t.dt.tz_convert("Asia/Tokyo").dt.hour.values
    out = np.full(len(t), 4, dtype=np.int8)
    out[(tok >= 9) & (lon < 8)] = 0
    out[(lon >= 8) & (ny < 8)] = 1
    out[(ny >= 8) & (lon >= 8) & (lon < 17)] = 2
    out[(lon >= 17) & (ny >= 8) & (ny < 17)] = 3
    return out


def signals(close):
    """18 ルール × 順/逆 = 36 列。足 t の値は足 t の終値までで計算（使うときは 1 本ずらす）。"""
    c = pd.Series(close); cols = []; names = []
    for a, b in MA:
        cols.append(np.sign(c.rolling(a).mean() - c.rolling(b).mean()).values); names.append(f"MA{a}/{b}")
    for n, k in BB:
        z = (c - c.rolling(n).mean()) / c.rolling(n).std(ddof=0); s = np.where(z.abs() > k, -np.sign(z), 0.0); cols.append(s); names.append(f"BB{n}k{k}")
    for n in BO:
        hi = c.shift(1).rolling(n).max(); lo = c.shift(1).rolling(n).min(); s = np.where(c > hi, 1.0, np.where(c < lo, -1.0, 0.0)); cols.append(s); names.append(f"BO{n}")
    for k in MOM:
        cols.append(np.sign(c - c.shift(k)).values); names.append(f"MOM{k}")
    S = np.nan_to_num(np.column_stack(cols), nan=0.0); S = np.concatenate([S, -S], axis=1); names = [n + "順" for n in names] + [n + "逆" for n in names]
    return S, names


def grid(d):
    """日×24 の格子に並べる。戻り: 日インデックス, 格子位置 (日番号, 時), 有効マスク。"""
    day = d["time"].dt.floor("D"); days = pd.Index(sorted(day.unique())); di = days.get_indexer(day); hi = d["time"].dt.hour.values
    return days, di, hi


def run_symbol(a):
    sym, B, smoke, seed, outdir = a; t0 = time.time(); rng = np.random.default_rng(seed + sum(ord(ch) for ch in sym))
    d = load(sym, smoke, rng); d = d[d["time"].dt.dayofweek < 5].reset_index(drop=True)
    if len(d) < 3000: return sym, {"skip": f"足が {len(d)} 本"}
    c = d["close"].values; r = np.r_[np.nan, c[1:] / c[:-1] - 1] * 1e4; S, names = signals(c); Sp = np.r_[np.zeros((1, S.shape[1])), S[:-1]]  # 1 本ずらし
    w = windows(d["time"]); cost = cost_bp(sym); days, di, hi = grid(d); D = len(days)
    ok = np.isfinite(r); r0 = np.where(ok, r, 0.0); Z = Sp * r0[:, None]  # コスト前・1 本あたり（T×36）
    year = days.year.values
    cells = []
    # 観測: 窓ごと＋全時間帯
    for wi, wname in enumerate(WIN + ["全時間帯"]):
        m = (w == wi) if wi < 5 else np.ones(len(d), bool); m = m & ok
        pos = Sp * m[:, None]; dpos = np.abs(np.diff(np.r_[np.zeros((1, pos.shape[1])), pos], axis=0))
        pnl = pos * r0[:, None] - cost * dpos / 2  # T×36
        daily = np.zeros((D, pnl.shape[1])); np.add.at(daily, di, pnl); active = np.zeros((D, pnl.shape[1]), bool); np.logical_or.at(active, di, np.abs(pos) > 0)
        gross_mean = Z[m].mean(axis=0) if m.sum() else np.full(Z.shape[1], np.nan)
        for j, nm in enumerate(names):
            act = active[:, j]; x = daily[act, j]; y = year[act]
            if act.sum() < 100: continue
            pre, post = x[y < SPLIT], x[y >= SPLIT]
            cells.append({"sym": sym, "window": wname, "signal": nm, "n_days": int(act.sum()), "bp_day": float(x.mean()), "t": tstat(x), "bp_pre": float(pre.mean()) if len(pre) else float("nan"),
                          "bp_post": float(post.mean()) if len(post) else float("nan"), "t_pre": tstat(pre), "t_post": tstat(post), "gross_bar": float(gross_mean[j]),
                          "sharpe": float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if x.std(ddof=1) > 0 else float("nan"), "n_bars": int(m.sum())})
    # 帰無: 日内で窓ラベルを並べ替え（B 回）。格子 D×24 に戻してから並べ替える。
    Wg = np.full((D, 24), -1, np.int8); Wg[di, hi] = w; Vg = np.zeros((D, 24), bool); Vg[di, hi] = ok
    Zg = np.zeros((D, 24, Z.shape[1])); Zg[di, hi] = Z; Zf = Zg.reshape(D * 24, -1); Vf = Vg.ravel()
    sums = np.zeros((5, Z.shape[1])); sq = np.zeros((5, Z.shape[1])); cnt = 0
    for b in range(B):
        P = np.take_along_axis(Wg, np.argsort(rng.random((D, 24)), axis=1), axis=1).ravel()
        for wi in range(5):
            m = (P == wi) & Vf; n = m.sum()
            if n == 0: continue
            s = m.astype(float) @ Zf / n; sums[wi] += s; sq[wi] += s * s
        cnt += 1
    mu = sums / max(cnt, 1); sd = np.sqrt(np.maximum(sq / max(cnt, 1) - mu * mu, 0)) * math.sqrt(cnt / max(cnt - 1, 1))
    for ce in cells:
        if ce["window"] in WIN:
            wi = WIN.index(ce["window"]); j = names.index(ce["signal"]); ce["z"] = float((ce["gross_bar"] - mu[wi, j]) / sd[wi, j]) if sd[wi, j] > 0 else float("nan")
            ce["null_mu"] = float(mu[wi, j]); ce["null_sd"] = float(sd[wi, j])
        else:
            ce["z"] = None
    res = {"sym": sym, "B": int(cnt), "cost_bp_rt": cost, "n_bars": int(len(d)), "n_days": int(D), "period": [str(days[0].date()), str(days[-1].date())], "sec": round(time.time() - t0, 1), "cells": cells}
    if outdir:
        os.makedirs(outdir, exist_ok=True); json.dump(res, open(os.path.join(outdir, f"{sym}.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    return sym, res


def calibrate(syms, smoke, workers, hours):
    """最大の銘柄で B=20 を測り、全体が持ち時間に収まる B を決める。"""
    big = "EURUSD" if not smoke else syms[0]; t0 = time.time(); _, r = run_symbol((big, 20, smoke, SEED, None)); per_b = (time.time() - t0) / 20
    # 銘柄ごとの重さは足の本数に比例とみなす（暗号は短い）
    nb = {}
    for s in syms:
        try:
            nb[s] = len(load(s, smoke, np.random.default_rng(0)))
        except Exception:
            nb[s] = 0
    total_per_b = per_b * sum(nb.values()) / max(nb.get(big, 1), 1) / max(workers, 1)
    B = int(hours * 3600 / max(total_per_b, 1e-6)); B = max(200, min(1_000_000, B))
    return B, per_b, total_per_b


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=0); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--hours", type=float, default=float(os.environ.get("Q574_HOURS", "6.5"))); ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--syms", default=""); a = ap.parse_args()
    syms = a.syms.split(",") if a.syms else (SYMS[:2] if a.smoke else SYMS)
    done_json = sorted(glob.glob(os.path.join(HERE, "results", f"{QID}_result_*.json")))
    if done_json and not a.smoke and not a.fresh and not a.syms:
        print(f"[{QID}] 計算済み: {os.path.relpath(done_json[-1], HERE)} を読むこと（数時間の計算なので再実行しない。やり直すなら --fresh）"); return
    out = os.path.join(HERE, "results"); part = os.path.join(out, "partial" + ("_smoke" if a.smoke else "")); os.makedirs(part, exist_ok=True)
    if a.fresh:
        for p in glob.glob(os.path.join(part, "*.json")): os.remove(p)
    if a.B > 0:
        B, per_b, tot = a.B, float("nan"), float("nan")
    else:
        B, per_b, tot = calibrate(syms, a.smoke, a.workers, a.hours)
    print(f"[{QID}] B={B} workers={a.workers} 持ち時間={a.hours}h 較正: 1 回あたり {per_b:.3f}s（EURUSD）, 全体 {tot:.3f}s/回 → 見込み {B * tot / 3600:.2f}h", flush=True)
    todo = [s for s in syms if not os.path.exists(os.path.join(part, f"{s}.json"))]; print(f"残り {len(todo)} 銘柄（途中結果 {len(syms) - len(todo)}）", flush=True)
    jobs = [(s, B, a.smoke, SEED, part) for s in todo]; t0 = time.time()
    if a.workers > 1 and len(jobs) > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.workers) as pool:
            for s, r in pool.imap_unordered(run_symbol, jobs):
                print(f"  ✓ {s} {r.get('sec', '')}s  {_dt.datetime.now():%H:%M:%S}", flush=True)
    else:
        for j in jobs:
            s, r = run_symbol(j); print(f"  ✓ {s} {r.get('sec', '')}s", flush=True)
    # 統合
    cells = []; per_sym = {}
    for s in syms:
        p = os.path.join(part, f"{s}.json")
        if not os.path.exists(p): continue
        r = json.load(open(p, encoding="utf-8")); per_sym[s] = {k: r[k] for k in ("B", "cost_bp_rt", "n_bars", "n_days", "period", "sec") if k in r}; cells += r.get("cells", [])
    C = pd.DataFrame(cells)
    if C.empty:
        print("セルなし"); return
    W = C[C["window"].isin(WIN)].copy(); W["p"] = W["t"].apply(p_two); W["p_holm"] = holm(W["p"].values)
    W["a"] = (W["p_holm"] < 0.05) & (W["t"] > 0); W["b"] = (W["bp_pre"] > 0) & (W["bp_post"] > 0) & (W["bp_day"] > 0); W["c"] = W["z"] >= 2
    surv = W[W["a"] & W["b"] & W["c"]]; a_only = W[W["a"]]
    cols = ["sym", "window", "signal", "bp_day", "t", "t_pre", "t_post", "z", "p_holm", "sharpe", "n_days"]
    if len(surv): verdict = f"支持: (a)(b)(c) を満たすセル {len(surv)}"
    elif len(a_only) == 0: verdict = "棄却: Holm を抜けるセル 0（コスト後）"
    else: verdict = f"未確定: Holm を抜けるセル {len(a_only)} だが (b) 前後半 or (c) 窓 z で落ちる"
    by_win = {w: {"cells": int((W.window == w).sum()), "share_t_pos": f((W[W.window == w].t > 0).mean(), 3), "mean_t": f(W[W.window == w].t.mean(), 2), "mean_bp_day": f(W[W.window == w].bp_day.mean(), 3),
                  "max_t": f(W[W.window == w].t.max(), 2), "n_a": int(W[W.window == w].a.sum())} for w in WIN}
    allh = C[C["window"] == "全時間帯"]
    main_ = {"n_cells": int(len(W)), "n_syms": int(W.sym.nunique()), "B": per_sym.get("EURUSD", {}).get("B") or next(iter(per_sym.values()), {}).get("B"), "n_a_holm": int(len(a_only)), "n_ab": int((W["a"] & W["b"]).sum()),
             "n_abc": int(len(surv)), "min_p_holm": f(W.p_holm.min(), 4), "max_t": f(W.t.max(), 2), "max_z": f(W.z.max(), 2), "share_t_pos_all": f((W.t > 0).mean(), 3),
             "allhours_share_t_pos": f((allh.t > 0).mean(), 3), "allhours_max_t": f(allh.t.max(), 2), "wall_sec": round(time.time() - t0, 1)}
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{QID}" if a.smoke else QID
    res = {"qid": QID, "smoke": a.smoke, "generated": ts, "question": "5 窓×36 信号×26 銘柄の総当たりで、コスト後 Holm を抜け・前後半正・窓 z≥2 のセルはあるか",
           "settings": {"windows": WIN, "n_signals": 36, "split": SPLIT, "seal": "2024-07-01", "hours_budget": a.hours, "workers": a.workers, "cost_table": {s: cost_bp(s) for s in syms}},
           "main": main_, "by_window": by_win, "survivors": surv[cols].round(4).to_dict("records"), "holm_a_only": a_only[cols].round(4).sort_values("p_holm").head(50).to_dict("records"),
           "top20_by_t": W.sort_values("t", ascending=False).head(20)[cols].round(4).to_dict("records"), "per_sym": per_sym, "machine_verdict": verdict,
           "multiple_comparisons": "(a) は全セル Holm。(c) の z は (a) を抜けたセルにだけ適用。全時間帯の行は Holm の族に入れない（記述）。"}
    json.dump(res, open(os.path.join(out, f"{pre}_result_{ts}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    C.round(5).to_csv(os.path.join(out, f"{pre}_cells_{ts}.csv"), index=False)
    print("main:", main_); print("by_window:", by_win); print("machine_verdict:", verdict); print("wrote", f"results/{pre}_result_{ts}.json")


if __name__ == "__main__":
    main()
