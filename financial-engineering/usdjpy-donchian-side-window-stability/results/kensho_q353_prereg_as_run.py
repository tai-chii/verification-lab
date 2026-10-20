#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q353（Q352-C1 の出口・a 出口で検証）
================================================================================
USDJPY 日足のドンチャン（20/10・55/20）で、優位な売買方向（Long−Short の1取引あたり純損益差）は
5年窓を1年ずつずらしても符号が保たれるか、それとも窓ごとに後からしか見えないか。

【出典】
- アイデア候補 2026-10-20（Q352-C1）。接続ログ 2026-10-20 Q352-C1。
- hiro_algo（ブログZenn2026hiroRegime-1〜3）: USDJPY ドンチャン 20/10 は 2008〜2012 Short 優位・
  2020〜 Long 優位。端の年（2007・2013）を足すと 2008〜2012 の CI が 0 をまたぐ。
- Q152（USDJPY・ドンチャン 55/20・bp/足）: 前半<2017 Long生 +1.31／Short生 −0.58、
  後半≥2017 Long生 +0.30／Short生 +0.34。ドリフト除去後 前半 Long +1.09／Short −0.37、
  後半 Long −0.27／Short +0.70。
- Q160（確定）: 商品4・トレンド6 の買い側はドリフト除去後も z≥2、売り側は 0 と区別できない。
- 先行研究: Peltomäki・Agerbäck・Gudmundsen-Sinclair (2016, SSRN) は買い側/売り側を金利局面で
  分けるが、単一通貨で窓の切り方への優位側の依存を数えた研究は未確認（WebSearch 2026-10-20）。

【仮説（測る前に固定）】
H1: USDJPY のドンチャンの「優位な売買方向」は実在で安定 ＝ 5年窓をずらしても、
    Long−Short の差の 95% CI が 0 を外す窓が帰無より多く、外す窓の符号はすべて同じ。
対立: 窓ごとに符号が入れ替わる（期間依存・hiro 支持）か、0 を外す窓の数が帰無と同程度（ノイズ）。

【データ・定義（1通りに固定）】
- data_USDJPY_D1_fromH1.csv（2008-02〜2026-06）。往復コスト COST_RT=0.02（Q152 と同じ・段階1）。
- 規則: ドンチャン簡略版 20/10（hiro）と 55/20（Q152）。終値が直前 N 日高値を上抜けで翌足から買い、
  直前 X 日安値を下抜けで手仕舞い、売りは対称、損切りなし。Q160 の donchian_positions を写す。
- 日次純損益 [bp] = pos_{t-1}×ret_t×1e4 − |Δpos|×片道コスト[bp]（片道 = COST_RT/2 ÷ 前日終値）。
- 取引 = pos≠0 の連続区間。取引の純損益 = 区間内の日次純損益の和（建て・手仕舞いのコスト込み）。
  取引は建玉の初日の月に属する。
- 窓: 開始年 Y=2008..2021 の暦 5 年（Y-01-01〜(Y+4)-12-31）。14 窓。2008 窓は 2008-02 から。
  取引は建玉の初日が窓内のものを数える。
- 差 D = Long 取引の平均純損益 − Short 取引の平均純損益 [bp/取引]。
  生（raw）と ドリフト除去後（adj: 各取引の pnl から side × r̄_窓[bp/日] × 保有日数 を引く）の 2 本。
- CI: 窓内の暦月を復元抽出する月ブロック・ブートストラップ B=5,000、2.5〜97.5 点。
  （月 m の重み c_m として D* = Σc_m S^L_m/Σc_m N^L_m − Σc_m S^S_m/Σc_m N^S_m）
- 数えるもの: ① CI が 0 を外す窓の割合（14 窓中）、② 外す窓の符号（全部同符号か混在か）。
- 帰無: 日次リターン系列の月ブロック循環シフト（最小 12 か月、ずらす月数は 12〜(総月数−12) から一様）
  B=1,000。各帰無系列で同じ手順（規則→取引→窓→CI→①）を繰り返し、① の分布と 95 点を出す。
  コスト[bp] は暦日固定（元の前日終値で割る）。Long/Short の取引数が 0 の窓は CI を出さず「外さない」と数える。

【判定（事前固定・変更禁止）】規則2本 × 生/除去 = 4 判定。
- ① > 帰無の 95 点 かつ ② 同符号 → **支持**（方向の優位は実在で安定・固定方向の規則に進める）
- ① > 帰無の 95 点 だが ② 混在 → **期間依存**（hiro 支持・固定方向の規則は作らない）
- ① ≤ 帰無の 95 点 → **ノイズ**（Q160 の「売り側 0」と整合）
- 注: 外す窓が 1 つだけなら ② は自明に同符号。① が帰無 95 点を超えるかで決まる。
- 2014〜2019 を含む窓の結果は記述として必ず載せる（hiro の空白）。

【捨てた案の数】約4
- 1取引あたりでなく bp/足（Q152 と同じ）にする案 → hiro の pips/取引に揃えるため取引あたり。
- 窓幅 3 年・7 年の併記 → 多重比較が増えるので 5 年 1 本。
- 帰無を日次並べ替えにする案 → 自己相関・連を保つため月ブロック循環シフト。
- 損切りあり（hiro は損切りなし）→ なし。

【多重比較】4 判定。14 窓の CI はそれぞれ検定ではなく ① を作る材料。帰無の ① の分布が
「窓を 14 個見れば偶然いくつ外すか」を吸収する。

【知識の締め切り】Claude の知識は 2026-06 まで。USDJPY が 2021〜2024 に大きく円安に動いたことは知って
おり、「後半は Long 優位」の後知恵は排除できない。ドリフト除去後の差で判定するので相場観だけでは答えは出ない。
hiro の結論（期間反転）も知ったうえでの設計なので、判定は数（①・②）で機械的に行う。

【委託の確かめ方】設計・実行・解釈とも本体（Fable、担当列は opus 相当）。実行後に点検するもの:
z が桁外れでないこと、窓ごとの取引数が 0 でないこと、帰無の ① 分布が一点に潰れていないこと。

【実装】自己完結・決定的（乱数は seed 固定）。依存: python3 + numpy/pandas。
実行: python3 kensho_q353.py              （CI B=5000・帰無 B=1000）
      python3 kensho_q353.py --B 500 --null-B 50   （軽い試走）
"""
import argparse, datetime as _dt, json, math, os, sys, time, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

def _p(*parts):
    a = os.path.join(WS, *parts)
    if os.path.exists(a): return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])

DATA = os.path.join(_p("検証", "学問", "金融工学", "作業", "FX", "システムトレード"), "data_USDJPY_D1_fromH1.csv")
OUT = os.path.join(HERE, "results")
COST_RT = 0.02
RULES = {"DON20_10": (20, 10), "DON55_20": (55, 20)}
WINDOW_STARTS = list(range(2008, 2022))   # 2008..2021 → 14 窓
WIN_YEARS = 5
SEED = 20261020
MIN_SHIFT_MONTHS = 12

def load_csv(path):
    d = pd.read_csv(path, parse_dates=["time"])
    d = d[(d.high > d.low) & (d.close > 0)].sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return d

def donchian_positions(c, entry, exit_):
    n = len(c); pos = np.zeros(n); cs = pd.Series(c)
    hiE = cs.rolling(entry).max().shift(1).values; loE = cs.rolling(entry).min().shift(1).values
    hiX = cs.rolling(exit_).max().shift(1).values; loX = cs.rolling(exit_).min().shift(1).values
    p = 0
    for i in range(n):
        if p == 1 and np.isfinite(loX[i]) and c[i] < loX[i]: p = 0
        elif p == -1 and np.isfinite(hiX[i]) and c[i] > hiX[i]: p = 0
        if p == 0:
            if np.isfinite(hiE[i]) and c[i] > hiE[i]: p = 1
            elif np.isfinite(loE[i]) and c[i] < loE[i]: p = -1
        pos[i] = p
    return pos

def daily_net_pnl_bp(ret, signal, cost_bp_day, warm):
    n = len(ret)
    pos_prev = np.concatenate([[0.0], signal[:-1]])
    gross = pos_prev * ret * 1e4
    dpos = np.abs(np.diff(np.concatenate([[0.0], pos_prev])))
    pnl = gross - dpos * cost_bp_day
    pnl[:warm + 1] = 0.0
    return pnl, pos_prev

def trades_from(pos_prev, pnl, ret_bp, years, months):
    """取引表: side, start_idx, n_days, pnl, sum_ret_bp(保有日のリターン和), year, month（建玉初日）"""
    n = len(pos_prev); out = []
    i = 0
    while i < n:
        if pos_prev[i] == 0: i += 1; continue
        s = pos_prev[i]; j = i
        while j < n and pos_prev[j] == s: j += 1
        out.append((s, i, j - i, pnl[i:j].sum(), years[i], months[i]))
        i = j
    return pd.DataFrame(out, columns=["side", "start", "ndays", "pnl", "year", "month"])

def window_stats(tr, ret_bp_daily, years_daily, B, Cs):
    """各窓で D(raw/adj)・CI。Cs[Y] = 月の重み行列 (B×60)。戻り: list of dict"""
    res = []
    for Y in WINDOW_STARTS:
        C = Cs[Y]
        y0, y1 = Y, Y + WIN_YEARS - 1
        mday = (years_daily >= y0) & (years_daily <= y1)
        rbar = float(ret_bp_daily[mday].mean()) if mday.sum() else float("nan")
        w = tr[(tr.year >= y0) & (tr.year <= y1)].copy()
        w["adj"] = w.pnl - w.side * rbar * w.ndays
        nL = int((w.side == 1).sum()); nS = int((w.side == -1).sum())
        row = dict(start=y0, end=y1, n_long=nL, n_short=nS, drift_bp_day=rbar)
        months = np.array(sorted(set((yy * 100 + mm) for yy in range(y0, y1 + 1) for mm in range(1, 13))))
        midx = {m: k for k, m in enumerate(months)}
        for var in ("raw", "adj"):
            col = "pnl" if var == "raw" else "adj"
            if nL == 0 or nS == 0:
                row[var] = dict(D=float("nan"), lo=float("nan"), hi=float("nan"), excl=False, meanL=float("nan"), meanS=float("nan"))
                continue
            L = w[w.side == 1]; S = w[w.side == -1]
            D = float(L[col].mean() - S[col].mean())
            SL = np.zeros(len(months)); NL = np.zeros(len(months)); SS = np.zeros(len(months)); NS = np.zeros(len(months))
            for m, v in zip(L.month, L[col]): SL[midx[m]] += v; NL[midx[m]] += 1
            for m, v in zip(S.month, S[col]): SS[midx[m]] += v; NS[midx[m]] += 1
            dl = C @ NL; ds = C @ NS
            ok = (dl > 0) & (ds > 0)
            Db = (C @ SL)[ok] / dl[ok] - (C @ SS)[ok] / ds[ok]
            lo, hi = (float(np.percentile(Db, 2.5)), float(np.percentile(Db, 97.5))) if len(Db) > 100 else (float("nan"), float("nan"))
            excl = bool(np.isfinite(lo) and (lo > 0 or hi < 0))
            row[var] = dict(D=D, lo=lo, hi=hi, excl=excl, meanL=float(L[col].mean()), meanS=float(S[col].mean()))
        res.append(row)
    return res

def summarize(rows, var):
    ex = [r for r in rows if r[var]["excl"]]
    signs = sorted(set(np.sign(r[var]["D"]) for r in ex))
    frac = len(ex) / len(rows)
    sign_state = "なし" if not ex else ("同符号" if len(signs) == 1 else "混在")
    return dict(frac_excl=frac, n_excl=len(ex), n_windows=len(rows), sign_state=sign_state,
                signs_pos=int(sum(1 for r in ex if r[var]["D"] > 0)), signs_neg=int(sum(1 for r in ex if r[var]["D"] < 0)))

def month_weights(B, rng):
    nm = WIN_YEARS * 12
    return {Y: rng.multinomial(nm, np.full(nm, 1.0 / nm), size=B).astype(float) for Y in WINDOW_STARTS}

def run_once(ret, c_cost, years, months, B, rng):
    """ret: 日次リターン, c_cost: コスト計算用の前日終値（暦日固定）。戻り: {rule: rows}"""
    n = len(ret); Cs = month_weights(B, rng)
    c = np.empty(n); c[0] = 100.0; c[1:] = 100.0 * np.cumprod(1.0 + ret[1:])
    cost_bp_day = np.zeros(n); cost_bp_day[1:] = (COST_RT / 2.0) / c_cost[:-1] * 1e4
    ret_bp = ret * 1e4
    out = {}
    for name, (e, x) in RULES.items():
        pos = donchian_positions(c, e, x)
        pnl, pos_prev = daily_net_pnl_bp(ret, pos, cost_bp_day, e)
        tr = trades_from(pos_prev, pnl, ret_bp, years, months)
        out[name] = window_stats(tr, ret_bp, years, B, Cs)
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=5000); ap.add_argument("--null-B", type=int, default=1000)
    ap.add_argument("--null-from", type=int, default=0); ap.add_argument("--null-to", type=int, default=-1)
    ap.add_argument("--assemble", action="store_true", help="results/null_parts/ を結合して最終結果を書く")
    a = ap.parse_args()
    if a.null_to < 0: a.null_to = a.null_B
    t0 = time.time()
    d = load_csv(DATA)
    c = d.close.values.astype(float); t = d.time
    n = len(c); ret = np.zeros(n); ret[1:] = c[1:] / c[:-1] - 1.0
    years = t.dt.year.values; months = (t.dt.year * 100 + t.dt.month).values
    rng = np.random.default_rng(SEED)
    obs = run_once(ret, c, years, months, a.B, rng)
    PARTS = os.path.join(OUT, "null_parts"); os.makedirs(PARTS, exist_ok=True)
    summ = {r: {v: summarize(obs[r], v) for v in ("raw", "adj")} for r in RULES}
    # 帰無: 月ブロック循環シフト
    um = np.unique(months); M = len(um)
    month_start = {m: int(np.argmax(months == m)) for m in um}
    null_frac = {r: {"raw": [], "adj": []} for r in RULES}
    if not a.assemble:
        part = {r: {"raw": [], "adj": []} for r in RULES}; shifts = []
        for b in range(a.null_from, a.null_to):
            rng_b = np.random.default_rng(SEED + 1 + b)          # 反復 b の乱数は分割の仕方に依らず同じ
            k = int(rng_b.integers(MIN_SHIFT_MONTHS, M - MIN_SHIFT_MONTHS + 1))
            shift_days = month_start[um[k]]; shifts.append(int(k))
            r2 = ret.copy(); r2[1:] = np.roll(ret[1:], -(shift_days - 1))
            o = run_once(r2, c, years, months, a.B, rng_b)
            for r in RULES:
                for v in ("raw", "adj"):
                    part[r][v].append(summarize(o[r], v)["frac_excl"])
            if (b + 1) % 50 == 0: print(f"  null {b+1}/{a.null_B}  {time.time()-t0:.0f}s", flush=True)
        with open(os.path.join(PARTS, f"null_{a.null_from:05d}_{a.null_to:05d}.json"), "w") as f:
            json.dump(dict(frac=part, shift_months=shifts, B=a.B), f)
        if a.null_to < a.null_B:
            print(f"part saved ({a.null_from}..{a.null_to}); run remaining parts then --assemble"); return
    # 結合
    done = set()
    for fn in sorted(os.listdir(PARTS)):
        if not fn.startswith("null_"): continue
        lo, hi = map(int, fn[5:-5].split("_"))
        pj = json.load(open(os.path.join(PARTS, fn)))
        for i, b in enumerate(range(lo, hi)):
            if b in done or b >= a.null_B: continue
            done.add(b)
            for r in RULES:
                for v in ("raw", "adj"): null_frac[r][v].append(pj["frac"][r][v][i])
    print(f"null assembled: {len(done)} / {a.null_B}")
    if len(done) < a.null_B: print("WARNING: null incomplete")
    verdict = {}
    for r in RULES:
        verdict[r] = {}
        for v in ("raw", "adj"):
            nf = np.array(null_frac[r][v]); s = summ[r][v]
            p95 = float(np.percentile(nf, 95)) if len(nf) else float("nan")
            pct = float((nf < s["frac_excl"]).mean()) if len(nf) else float("nan")
            if len(nf) and s["frac_excl"] > p95:
                j = "支持" if s["sign_state"] == "同符号" else "期間依存"
            else:
                j = "ノイズ"
            verdict[r][v] = dict(judgement=j, frac_excl=s["frac_excl"], n_excl=s["n_excl"], sign_state=s["sign_state"],
                                 null_p95=p95, null_mean=float(nf.mean()) if len(nf) else float("nan"),
                                 null_pct_below_obs=pct, null_p2_5=float(np.percentile(nf, 2.5)) if len(nf) else float("nan"),
                                 null_p97_5=float(np.percentile(nf, 97.5)) if len(nf) else float("nan"),
                                 null_distinct=int(len(np.unique(nf))) if len(nf) else 0)
    os.makedirs(OUT, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dict(queue="Q353", data=os.path.basename(DATA), n_days=n, span=[str(t.iloc[0].date()), str(t.iloc[-1].date())],
               B=a.B, null_B=a.null_B, null_done=len(done), seed=SEED, cost_rt=COST_RT, windows=obs, summary=summ, verdict=verdict,
               null_frac=null_frac, elapsed_s=round(time.time() - t0, 1))
    jp = os.path.join(OUT, f"Q353_result_{stamp}.json")
    with open(jp, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    rows = []
    for r in RULES:
        for w in obs[r]:
            rows.append(dict(rule=r, start=w["start"], end=w["end"], n_long=w["n_long"], n_short=w["n_short"], drift_bp_day=w["drift_bp_day"],
                             D_raw=w["raw"]["D"], lo_raw=w["raw"]["lo"], hi_raw=w["raw"]["hi"], excl_raw=w["raw"]["excl"],
                             D_adj=w["adj"]["D"], lo_adj=w["adj"]["lo"], hi_adj=w["adj"]["hi"], excl_adj=w["adj"]["excl"],
                             meanL_raw=w["raw"]["meanL"], meanS_raw=w["raw"]["meanS"]))
    cp = os.path.join(OUT, f"Q353_windows_{stamp}.csv"); pd.DataFrame(rows).to_csv(cp, index=False)
    print(json.dumps(verdict, ensure_ascii=False, indent=1))
    print(pd.DataFrame(rows).to_string(float_format=lambda x: f"{x:.1f}"))
    print("JSON:", jp); print("CSV:", cp); print(f"elapsed {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
