#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q301: 強度スプレッドの合図のエントリーをロンドン・NY 重複帯（NY 8〜12 時・8:30 ET の足の確定後）に限ると、
1 トレードのコスト後期待値は即時エントリーとランダム時間窓の帰無を上回るか（全体／前半 3 時間・H1 執行・24 時間保有）
================================================================================

【出典】
- 計画（事前登録）: アイデア候補.md 2026-10-15 の Q301 の行（3案一括生成 通貨強度 第1弾）。
- 背景: taichi と ChatGPT の壁打ち（2026-10-15）「4H で方向を決め、1H で流動性の高い時間帯にだけ入る方が期待値が高いか」。
  taichi の決定: 窓はロンドン・NY 重複帯（JST 21〜26 時＝NY 8〜12 時）、米 8:30 ET 指標の前後 15 分は一律に避ける（簡易版）、
  窓は「全体」と「前半 3 時間」の 2 通りを比べる。
- 関連: 知見「日足の区切り時刻は…半期ごとの順位には残らず」(Q211)・「為替のフィキシング前後のドルのV字は…2020年以降は弱まって」・
  [[Seeck2026-1_ロンドン開始30分の日中モメンタムは円の組で約3.8倍強く期間外でも有意]]・[[Krohn2024-1_ドルはフィキシングに向けて上がりその後に下がり一日の中でW字になる]]。
  合図の定義は Q300 の主設定（L=30・q=5）と同じ。Q300 が棄却でも、時間帯で条件付き期待値が変わるかは別の問い。
- 先行研究チェック（WebSearch 2026-10-15・英語・"FX momentum returns by trading session London New York overlap intraday predictability time-of-day study"）:
  見つかったもの: Krohn-Mueller-Whelan (2018) FX Premia Around the Clock（通貨プレミアの日中パターン）、Andersen-Bollerslev 系の日中ボラ周期性、
  実務ブログ（セッション時間帯・根拠にしない）。
  未確認: 通貨強度スプレッドの合図を重複帯に限ったときの 1 トレード期待値を、毎日ランダムな時間窓の帰無と比べた実証は未確認（条件の穴）。

【仮説（測る前に固定）】
H: 重複帯「全体」（B）の 1 トレードのコスト後 bp（年単位平均）が、pre・post とも 即時エントリー（A）の同期間より大きく、
   かつ「毎日ランダムな開始時刻の同じ長さの窓」の帰無に対し Holm 補正後 p<0.05（片側 greater・m=4: B/C × pre/post）。
H0: B の全期間の z<1。

【データ】
対ドル 6 本（STRAIGHTS）H1_dukascopy（2008〜2026-06）→ 時刻を内部結合。NY 現地時刻は tz_convert("America/New_York")（夏時間を自動で扱う）。

【定義（1 通りに固定）】
- 状態（4H）: Q300 の主設定と同じ。UTC 4 時間境界（足の開始 hour%4==3）の行で、L=30 行のボラ正規化強度 → top/bot/スプレッド → 直前 500 行の五分位 q。
  状態は次の境界まで H1 の各足に引き継ぐ（境界の行を含む）。合図 = q==5。
- 執行: 足の確定（終値）で建て、HOLD=24 行（結合後の H1 行＝約 24 取引時間）後の終値で手仕舞い。合成（top 買い・bot 売り）。
  1 トレードの net bp = [(P_top[t+24]−P_top[t]) − (P_bot[t+24]−P_bot[t])]×1e4 − 往復コスト（USD 以外の脚ごとに COST_RT/close×1e4）。
  保有中は新規に入らない（次の合図は手仕舞い後）。
- モデル（同じ状態・同じ保有・同じコスト。違いはエントリーできる足だけ）:
  A 即時: 4H 境界の行（0/4/8/12/16/20 UTC の確定）で q==5 なら入る。
  B 重複帯 全体: 足の開始の NY 現地時刻 ∈ {8,9,10,11}（確定は 9〜12 時 NY＝12〜16 UTC 夏・13〜17 UTC 冬）で q==5 なら入る。
  C 重複帯 前半 3 時間: NY 現地時刻 ∈ {8,9,10}。
  指標の除外（簡易版）: 8:30 ET は NY 8 時台の足の中。B・C の最初のエントリーはその足の確定（9:00 NY＝発表 30 分後）なので、発表前後 15 分には入らない。
  A は 12:00 UTC（夏の 8:00 NY＝発表 30 分前）に入ることがあるが、±15 分の外なので規則どおり。
- 帰無（B・C）: 毎日（NY 現地日）の開始時刻 h0 を 0〜23 から独立に引き、幅 4（B）／3（C）時間の窓で同じ規則で入る → 1 トレード bp の年単位平均 → B=500。

【測るもの】
A/B/C の 1 トレード net bp（年単位平均・年単位 t）、件数、勝率、1 暦日あたり bp、pre/post。B・C の帰無に対する z・perm_p（greater）・Holm（m=4）。
補助: q==5 の状態にある全 H1 行の、NY 時刻別の 24 時間先 net bp（再入制限なし・記述）。

【判定（事前固定・変更禁止）】
- 支持: B の pre・post とも bp_net_per_trade > A の同期間 かつ Holm 補正後 p<0.05（B の 2 本。m=4）。
- 棄却: B の全期間の z<1。
- 未確定: ほか。C は記述（同じ検定を出すが判定には B だけ使う）。

【捨てた案の数】
約4: (i) 指標カレンダー取り込み（丁寧版。ネット遮断・簡易版で十分）、(ii) 東京時間の窓（JPY ペア限定になり比較が崩れる）、(iii) 1H 強度の変化を特徴量に（ML 段階へ）、
(iv) 固定 JST の窓（夏冬で 1 時間ずれる）。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。本データの終端も 2026-06。規則は固定で相場観は使わない。

【委託の確かめ方】設計は Fable、コードは Fable（クラウド側で --smoke --B 5 のみ）、実行と解釈は後の /lab（Opus）。委託なし。

【実装】自己完結・決定的（乱数は帰無の窓の開始時刻のみ seed 固定）。依存: python3 + numpy/pandas。土台は fe_core（直接使う型）。
実行: python3 kensho_currency_strength_session_q301.py（B=500・数分）／--smoke --B 5
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa: E402,F401,F403

QID = "Q301"
KIND = "H1_dukascopy"
START = "2008-01-01"
DEFAULT_B = 500
MAIN_L, MAIN_Q = 30, 5     # Q300 の主設定
VOL_WIN = 120
RANK_WIN = 500
HOLD = 24                  # H1 行
WINDOWS = {"B_overlap_all": [8, 9, 10, 11], "C_overlap_first3h": [8, 9, 10]}   # NY 現地時刻（足の開始）
CURS = ["USD", "EUR", "GBP", "AUD", "JPY", "CHF", "CAD"]
PAIRS = {"EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"), "AUDUSD": ("AUD", "USD"), "USDJPY": ("USD", "JPY"),
         "USDCHF": ("USD", "CHF"), "USDCAD": ("USD", "CAD"), "EURJPY": ("EUR", "JPY"), "GBPJPY": ("GBP", "JPY")}
STRAIGHTS = [p for p in PAIRS if "USD" in PAIRS[p]]
PAIR_OF = {(PAIRS[p][1] if PAIRS[p][0] == "USD" else PAIRS[p][0]): p for p in STRAIGHTS}


# ---------------------------------------------------------------------------- 通貨強度（Q299〜Q301 で同じ定義）
def align_closes(dfs, syms):
    out = None
    for s in syms:
        d = dfs[s][["time", "close"]].rename(columns={"close": s})
        out = d if out is None else out.merge(d, on="time", how="inner")
    return out.reset_index(drop=True)


def usd_log_prices(tbl):
    T = len(tbl)
    P = np.zeros((T, len(CURS))); close = {}
    for p in STRAIGHTS:
        b, q = PAIRS[p]
        lp = np.log(tbl[p].values.astype(float))
        if b == "USD":
            P[:, CURS.index(q)] = -lp; close[q] = tbl[p].values.astype(float)
        else:
            P[:, CURS.index(b)] = lp; close[b] = tbl[p].values.astype(float)
    return P, close


def strength(P, L, vol_win=VOL_WIN):
    T, K = P.shape
    r = np.full((T, K), np.nan); r[L:] = P[L:] - P[:-L]
    r1 = np.full((T, K), np.nan); r1[1:] = np.diff(P, axis=0)
    sd = pd.DataFrame(r1).rolling(vol_win, min_periods=vol_win // 2).std().values * np.sqrt(L)
    sd[:, CURS.index("USD")] = 1.0
    z = r / sd
    ok = np.isfinite(z).all(axis=1)
    out = np.full_like(z, np.nan)
    out[ok] = z[ok] - z[ok].mean(axis=1, keepdims=True)
    return out


def trailing_quintile(x, win=RANK_WIN):
    arr = np.asarray(x, float)
    out = np.full(len(arr), np.nan)
    for t in range(len(arr)):
        lo = max(0, t - win); ref = arr[lo:t]; ref = ref[np.isfinite(ref)]
        if len(ref) < win // 2 or not np.isfinite(arr[t]):
            continue
        out[t] = min(5, int((ref < arr[t]).mean() * 5) + 1)
    return out


def cost_matrix(close, T):
    C = np.zeros((T, len(CURS)))
    for cur, p in PAIR_OF.items():
        C[:, CURS.index(cur)] = COST_RT[p] / close[cur] * 1e4
    return C


# ---------------------------------------------------------------------------- 状態と執行
def h4_state(tbl):
    """H1 の表 → 各 H1 行の状態（top, bot, q）。4H 境界で計算し次の境界まで引き継ぐ。"""
    T = len(tbl)
    is_b = (tbl["time"].dt.hour % 4 == 3).values
    b_idx = np.where(is_b)[0]
    P4, _ = usd_log_prices(tbl.iloc[b_idx].reset_index(drop=True))
    S = strength(P4, MAIN_L)
    valid = np.isfinite(S).all(axis=1)
    n4 = len(b_idx)
    top4 = np.where(valid, np.argmax(np.where(valid[:, None], S, -np.inf), axis=1), -1)
    bot4 = np.where(valid, np.argmin(np.where(valid[:, None], S, np.inf), axis=1), -1)
    sp4 = np.where(valid, S[np.arange(n4), np.clip(top4, 0, None)] - S[np.arange(n4), np.clip(bot4, 0, None)], np.nan)
    q4 = trailing_quintile(sp4)
    # H1 行 → 直近の境界（その行を含む）
    pos = np.searchsorted(b_idx, np.arange(T), side="right") - 1
    ok = pos >= 0
    top = np.where(ok, top4[np.clip(pos, 0, None)], -1); bot = np.where(ok, bot4[np.clip(pos, 0, None)], -1)
    q = np.where(ok, q4[np.clip(pos, 0, None)], np.nan)
    return top, bot, q, is_b


def trade_returns(P, C, top, bot, hold=HOLD):
    """各 H1 行 t で建てた場合の 1 トレード net bp（hold 行後に手仕舞い）。無効は NaN。"""
    T = P.shape[0]; t = np.arange(T)
    ok = (top >= 0) & (bot >= 0) & (t + hold < T)
    net = np.full(T, np.nan); gross = np.full(T, np.nan)
    tt = t[ok]; a = top[ok]; b = bot[ok]
    gross[ok] = ((P[tt + hold, a] - P[tt, a]) - (P[tt + hold, b] - P[tt, b])) * 1e4
    net[ok] = gross[ok] - C[tt, a] - C[tt, b]
    return gross, net


def select_trades(eligible, hold=HOLD):
    """eligible（bool 配列）の行のうち、保有中でない最初の行から順に取る（貪欲）。返り値: 行番号の配列。"""
    idx = np.where(eligible)[0]
    out = []; nxt = -1
    for i in idx:
        if i >= nxt:
            out.append(i); nxt = i + hold
    return np.asarray(out, int)


def trade_stats(sel, net, gross, year, y0, y1, n_days):
    d = pd.DataFrame({"year": year[sel], "net": net[sel], "gross": gross[sel]})
    d = d[np.isfinite(d["net"])]
    d = d[(d["year"] >= y0) & (d["year"] < y1)]
    if d.empty:
        return {"n_trades": 0, "bp_net_per_trade": None, "t_year": None, "n_years": 0, "win_rate": None, "bp_gross_per_trade": None, "bp_net_per_day": None, "_raw": np.nan}
    st = by_year_stats(d, "net", y0=y0, y1=y1, min_rows=5)
    sg = by_year_stats(d, "gross", y0=y0, y1=y1, min_rows=5)
    return {"n_trades": int(len(d)), "bp_net_per_trade": fmt(st["mean"]), "t_year": fmt(st["t"]), "n_years": st["n_years"], "years_dropped": st["years_dropped"],
            "win_rate": fmt((d["net"] > 0).mean()), "bp_gross_per_trade": fmt(sg["mean"]),
            "bp_net_per_day": fmt(d["net"].sum() / n_days) if n_days else None, "_raw": st["mean"]}


def run(args, rng):
    syms = list(STRAIGHTS)
    hres = None if args.smoke else health(syms, kind=KIND)
    ok, missing = syms_available(syms, kind=KIND, smoke=args.smoke)
    if len(ok) < len(syms):
        return {"question": "強度スプレッドの合図の時間帯別エントリー（Q301）", "missing": missing, "data_health": hres,
                "machine_verdict": "未確定: 対ドル 6 本が揃わない（missing を見る）"}, {}
    dfs = {s: load_h1(s, args.smoke, rng, n=40000, start="2015-01-01") for s in ok}
    tbl = align_closes(dfs, ok)
    tbl = tbl[tbl["time"] >= pd.Timestamp(START)].reset_index(drop=True)
    T = len(tbl)
    ny = tbl["time"].dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    ny_hour = ny.dt.hour.values
    ny_day = ny.dt.tz_localize(None).dt.floor("D").values
    day_id = pd.factorize(ny_day)[0]
    n_days_total = int(day_id.max() + 1)
    year = tbl["time"].dt.year.values
    P, close = usd_log_prices(tbl)
    C = cost_matrix(close, T)
    top, bot, q, is_b = h4_state(tbl)
    gross, net = trade_returns(P, C, top, bot)
    sig = (q == MAIN_Q)
    periods = {"all": (0, 9999), "pre": (0, SPLIT_YEAR), "post": (SPLIT_YEAR, 9999)}
    days_in = {pn: int(len(np.unique(day_id[(year >= y0) & (year < y1)]))) for pn, (y0, y1) in periods.items()}
    # ---------------------------------------------------------------- 観測
    elig = {"A_immediate": sig & is_b}
    for name, hours in WINDOWS.items():
        elig[name] = sig & np.isin(ny_hour, hours)
    sels = {m: select_trades(e) for m, e in elig.items()}
    obs = {m: {pn: trade_stats(s, net, gross, year, *periods[pn], days_in[pn]) for pn in periods} for m, s in sels.items()}
    # ---------------------------------------------------------------- 帰無（B・C: 毎日ランダムな開始時刻の窓）
    null = {m: {pn: [] for pn in periods} for m in WINDOWS}
    if args.B > 0:
        for b in range(args.B):
            h0 = rng.integers(0, 24, size=n_days_total)
            off = (ny_hour - h0[day_id]) % 24
            for m, hours in WINDOWS.items():
                e = sig & (off < len(hours))
                s = select_trades(e)
                for pn, (y0, y1) in periods.items():
                    null[m][pn].append(trade_stats(s, net, gross, year, y0, y1, days_in[pn])["_raw"])
    tests = {}
    pv = []
    for m in WINDOWS:
        for pn in periods:
            o = obs[m][pn]["_raw"]; nl = null[m][pn]
            ns = null_summary(o, nl) if nl else {"z": None, "pct": None, "p_perm": None, "degenerate": None, "B": 0, "q025": None, "q975": None}
            tests[f"{m}_{pn}"] = {"z": fmt(ns["z"]), "pct": fmt(ns["pct"]), "p_perm_greater": fmt(ns["p_perm"]), "null_degenerate": ns["degenerate"],
                                  "null_q025": fmt(ns.get("q025")), "null_q975": fmt(ns.get("q975")), "B": ns["B"]}
            if pn in ("pre", "post"):
                pv.append((f"{m}_{pn}", ns["p_perm"] if ns["p_perm"] is not None else np.nan))
    adj = holm([p for _, p in pv])
    for (k, _), a in zip(pv, adj):
        tests[k]["p_holm"] = fmt(a)
    # ---------------------------------------------------------------- 補助: NY 時刻別の 24h 先 net（q==5・再入制限なし）
    hourly = []
    for pn, (y0, y1) in periods.items():
        m = sig & np.isfinite(net) & (year >= y0) & (year < y1)
        for h in range(24):
            mm = m & (ny_hour == h)
            if mm.sum() == 0:
                continue
            d = pd.DataFrame({"year": year[mm], "net": net[mm]})
            st = by_year_stats(d, "net", y0=y0, y1=y1, min_rows=5)
            hourly.append({"period": pn, "ny_hour_bar_start": h, "n": int(mm.sum()), "bp_net_24h": fmt(st["mean"]), "t_year": fmt(st["t"])})
    # ---------------------------------------------------------------- 判定
    B_ = "B_overlap_all"
    bpre, bpost, ball = obs[B_]["pre"]["_raw"], obs[B_]["post"]["_raw"], obs[B_]["all"]["_raw"]
    apre, apost = obs["A_immediate"]["pre"]["_raw"], obs["A_immediate"]["post"]["_raw"]
    hp, hq = tests[f"{B_}_pre"].get("p_holm"), tests[f"{B_}_post"].get("p_holm")
    za = tests[f"{B_}_all"]["z"]
    vals = [bpre, bpost, apre, apost, hp, hq, za]
    if any(v is None or (isinstance(v, float) and not np.isfinite(v)) for v in vals):
        verdict = "未確定: 計算できない（件数不足か帰無の退化）"
    elif bpre > apre and bpost > apost and hp < 0.05 and hq < 0.05:
        verdict = "支持: 重複帯（全体）の 1 トレード bp_net が前後半とも即時エントリーより大きく、ランダム窓の帰無に対し Holm 補正後 p<0.05"
    elif za < 1:
        verdict = f"棄却: 重複帯（全体）の全期間 z={za:.2f} < 1"
    else:
        verdict = "未確定"
    clean = {m: {pn: {k: v for k, v in d.items() if not k.startswith("_")} for pn, d in dd.items()} for m, dd in obs.items()}
    res = {"question": "強度スプレッドの合図のエントリーをロンドン・NY 重複帯に限ると 1 トレードのコスト後期待値は即時エントリーとランダム窓の帰無を上回るか",
           "settings": {"syms": ok, "start": START, "split_year": SPLIT_YEAR, "state": {"L": MAIN_L, "q": MAIN_Q, "vol_win": VOL_WIN, "rank_win": RANK_WIN},
                        "hold_bars": HOLD, "windows_ny_hour_bar_start": WINDOWS, "release_rule": "8:30 ET の足（NY 8 時台）の確定後に入る（簡易版・毎日）",
                        "n_rows_h1": int(T), "n_days": n_days_total, "B": args.B, "n_tests": 4,
                        "null": "毎日の開始時刻 h0〜U{0..23} の同じ幅の窓（B=4h・C=3h）で同じ規則 → 1 トレード bp の年単位平均",
                        "cost": "COST_RT 往復・USD 以外の脚ごと（最大 2 脚）",
                        "verdict_basis": "B の pre/post とも bp_net_per_trade > A かつ Holm p<0.05（m=4）→ 支持、B の全期間 z<1 → 棄却"},
           "missing": missing, "data_health": hres, "models": clean, "tests": tests, "hourly_24h_net_by_ny_hour": hourly,
           "machine_verdict": verdict,
           "multiple_comparisons": "判定は B の pre/post の 2 本。Holm は B・C × pre/post の 4 本で補正（m=4）。A・時刻別は記述。"}
    if hres and (hres["failed"] or hres["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    rows = [{"model": m, "period": pn, **{k: v for k, v in d.items() if not k.startswith("_")}} for m, dd in obs.items() for pn, d in dd.items()]
    return res, {"models": pd.DataFrame(rows), "hourly": pd.DataFrame(hourly)}


def main():
    args = parse_args(default_B=DEFAULT_B)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res.get("machine_verdict"))


if __name__ == "__main__":
    main()
