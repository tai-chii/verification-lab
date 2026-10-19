#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q333: WFO の「プラスの窓が60%以上」の関門は、腕のない順張りを何%通し、本物の優位を何%落とすか
================================================================================
【出典】ブログ hiro_algo (Zenn, 2026-10-09)「FX戦略は利益が出ても不採用？WFOで+606pipsでも見送った理由」
  主張カード ブログZenn2026hiroWFO-1・2（学習180日・検証30日・30日刻み、関門: PF>1.20・DD15%以内・プラス窓60%以上・近傍の過半プラス）。
  手元: 知見 Q184（窓損益は窓のドリフトで大半説明され腕と局面を分離できない）、Q188（台地選択は効かない）。
  計画: アイデア候補.md 2026-10-19 の行（Q331-C1、接続ログ 2026-10-19）。

【仮説（測る前に固定）】30日窓の勝率は窓のドリフト（局面）に支配されるので、「プラス窓≥60%」の関門は
腕のない順張りもかなりの率で通し、日次1bp程度の本物の優位はほとんど検出しない（使えない）と予想する。

【データ】15銘柄 data_<SYM>_D1_fromH1.csv。日次純損益は Q139/Q326 の pnl_matrix と同一（TSMOM・片道コスト段階1）。

【定義（1通り）】
- 戦略 A: L=60 固定。戦略 B: WFO。学習＝直前180暦日の純損益平均が最大の L∈{5..300}（60本）、検証＝次の30暦日。
- 検証窓: 全 L が定義される最初の日から180暦日後を起点に30暦日ずつ（両戦略で同じ窓）。窓の日数が10未満は捨てる。
- 窓がプラス＝窓内の日次純損益の和 > 0。
- 関門（銘柄×期間ごと）: G1 プラス窓率 ≥ 0.6、G2 合計 > 0、G3 PF（日次の利益和/損失和）> 1.2、
  G4 近傍の過半（戦略 A のみ: L∈{50,55,65,70} のうち 3本以上が同じ検証日で合計 > 0）。
- 期間: 前半（窓の起点 < 2017-01-01）／後半（≥ 2017）。
- 腕なし帰無: 価格の日次対数リターンを、検証窓と同じ30暦日ブロックの中で並べ替え（各ブロックのドリフトを保つ）、
  戦略を作り直す（B は選択もやり直す）。B=300、seed 20261019。誤採用率＝帰無で関門を通る (銘柄,b) の割合。
- 検出力: 帰無の系列の日次純損益に k∈{0.5,1,2} bp/日を足した（本物の優位の合成）ときに関門を通る割合。
- 実データ: 関門を通る銘柄の数（記述）。

【判定（事前固定・変更禁止）】G1（60%関門）について、全15・戦略 A と B のそれぞれで:
- 使えない: 前後半とも、腕なし通過率 > 10% または k=1bp の検出力 < 50%。
- 使える: 前後半とも、腕なし通過率 ≤ 5% かつ k=1bp の検出力 ≥ 80%。
- ほかは未確定。A と B で割れたら未確定。G2〜G4 は記述（同じ表に並べる）。

【捨てた案の数】約4: 窓を取引日30本にする案（記事は暦日）、帰無を年内並べ替えにする案（局面を保つのが目的なので窓内）、
k を窓単位で足す案（日次に足すほうが優位の定義として自然）、記事と同じ54窓の区間で切る案（期間の取り方が恣意的）。
【知識の締め切り】Claude はおよそ 2026-06。データは 2026-07 まで。関門の誤り率は特定年の相場観では作れない。
【委託の確かめ方】設計・コード・実行・解釈とも Opus 本体。委託なし。
【事前登録からの変更点】なし（実行の都合で銘柄ごとに分割し、乱数の種を SEED+銘柄番号に固定。試走 B=5 の結果 JSON は results/ に残す。アイデア候補の行の「腕なしの通過率」「k=1bp の検出力」の基準を、戦略 A・B のそれぞれに当てた）。
"""
import argparse, datetime as _dt, json, math, os, unicodedata
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
def _p(*parts):
    a = os.path.join(WS, *parts)
    return a if os.path.exists(a) else os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])
DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
OUT = os.path.join(HERE, "results")
FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
TREND7 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL", "US500", "USTECH", "BTCUSD"]
SYMS = FX8 + TREND7
COST_RT = {"EURUSD": .0002, "GBPUSD": .0002, "AUDUSD": .0002, "USDCHF": .0002, "USDCAD": .0002,
           "USDJPY": .02, "EURJPY": .02, "GBPJPY": .02, "XAUUSD": 0.6,
           "XAGUSD": 0.04, "WTI": 0.06, "UKOIL": 0.06, "US500": 1.0, "USTECH": 3.0, "BTCUSD": 40.0}
LS = list(range(5, 305, 5)); NC = len(LS); I60 = LS.index(60); NB = [LS.index(x) for x in (50, 55, 65, 70)]
TRAIN, TEST, MINW = 180, 30, 10
KS = [0.5, 1.0, 2.0]; SPLIT = np.datetime64("2017-01-01"); SEED = 20261019
GATES = ["G1_win60", "G2_total", "G3_pf12", "G4_nbr"]

def load_daily(sym):
    d = pd.read_csv(os.path.join(DATA_DIR, f"data_{sym}_D1_fromH1.csv"), parse_dates=["time"])
    return d[(d.high > d.low) & (d.close > 0)].sort_values("time").drop_duplicates("time").reset_index(drop=True)

def pnl_matrix(c, cost_rt):
    n = len(c); ret = np.zeros(n); ret[1:] = c[1:] / c[:-1] - 1.0
    cost_bp = np.zeros(n); cost_bp[1:] = (cost_rt / 2.0) / c[:-1] * 1e4
    M = np.full((n, NC), np.nan)
    for j, L in enumerate(LS):
        s = np.full(n, np.nan); s[L:] = np.sign(c[L:] - c[:-L])
        pos_prev = np.concatenate([[np.nan], s[:-1]]); pp = np.where(np.isfinite(pos_prev), pos_prev, 0.0)
        dpos = np.abs(np.diff(np.concatenate([[0.0], pp])))
        pnl = pp * ret * 1e4 - dpos * cost_bp; pnl[:L + 1] = np.nan; M[:, j] = pnl
    return M

def windows(t):
    """検証窓 [(start_idx, end_idx_exclusive, train_start_idx, start_date)]。"""
    t = t.values.astype("datetime64[D]")
    first = t[LS[-1] + 1] + np.timedelta64(TRAIN, "D")
    out = []; s = first
    while s < t[-1]:
        e = s + np.timedelta64(TEST, "D")
        a, b = np.searchsorted(t, s), np.searchsorted(t, e)
        tr = np.searchsorted(t, s - np.timedelta64(TRAIN, "D"))
        if b - a >= MINW: out.append((a, b, tr, s))
        s = e
    return out

def blocks(t):
    """並べ替えのブロック（窓と同じ30暦日の区切り、全期間）。"""
    t = t.values.astype("datetime64[D]")
    first = t[LS[-1] + 1] + np.timedelta64(TRAIN, "D")
    k = np.floor((t - first).astype(int) / TEST).astype(int)
    return k

def shuffled(c, blk, rng):
    r = np.zeros(len(c)); r[1:] = np.log(c[1:] / c[:-1]); r2 = r.copy()
    for k in np.unique(blk):
        idx = np.flatnonzero(blk == k); idx = idx[idx >= 1]
        if len(idx) > 1: r2[idx] = r[rng.permutation(idx)]
    return np.exp(np.log(c[0]) + np.cumsum(r2))

def strategy_daily(M, W):
    """戦略 A・B と近傍の検証日の純損益（窓ごとのリスト）。"""
    A, B, NBR = [], [], []
    for a, b, tr, s in W:
        A.append(M[a:b, I60]); NBR.append(M[a:b][:, NB])
        mu = np.nanmean(M[tr:a], 0); k = int(np.nanargmax(mu)); B.append(M[a:b, k])
    return A, B, NBR

def gates(wins, nbr=None, k=0.0):
    w = [np.nan_to_num(x) + k for x in wins]
    sums = np.array([x.sum() for x in w]); allp = np.concatenate(w)
    pos = allp[allp > 0].sum(); neg = -allp[allp < 0].sum()
    g = dict(G1_win60=bool((sums > 0).mean() >= 0.6), G2_total=bool(sums.sum() > 0),
             G3_pf12=bool(neg > 0 and pos / neg > 1.2), winrate=float((sums > 0).mean()), n_win=len(w))
    if nbr is not None:
        tot = np.array([sum(np.nan_to_num(x[:, j]).sum() + k * len(x) for x in nbr) for j in range(len(NB))])
        g["G4_nbr"] = bool((tot > 0).sum() >= 3)
    return g

def split(W, lists):
    f = [i for i, x in enumerate(W) if x[3] < SPLIT]; s = [i for i, x in enumerate(W) if x[3] >= SPLIT]
    return {"前半": [[L[i] for i in f] for L in lists], "後半": [[L[i] for i in s] for L in lists]}

def evaluate(M, W):
    A, B, NBR = strategy_daily(M, W); out = {}
    for per, (a, b, nb) in split(W, [A, B, NBR]).items():
        if len(a) < 5: continue
        out[per] = {"A": {str(k): gates(a, nb, k) for k in [0.0] + KS}, "B": {str(k): gates(b, None, k) for k in [0.0] + KS}}
    return out

def run_sym(sym, B):
    rng = np.random.default_rng(SEED + SYMS.index(sym))   # 銘柄ごとに固定の種（分割実行でも同じ結果）
    d = load_daily(sym); c = d.close.values.astype(float); W = windows(d.time); blk = blocks(d.time)
    real = evaluate(pnl_matrix(c, COST_RT[sym]), W)
    null = [evaluate(pnl_matrix(shuffled(c, blk, rng), COST_RT[sym]), W) for _ in range(B)]
    os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
    json.dump(dict(sym=sym, B=B, n_win=len(W), real=real, null=null), open(os.path.join(OUT, "parts", f"{sym}.json"), "w"))
    print(sym, len(W), flush=True)

def combine():
    real, null = {}, {}; Bs = set()
    for sym in SYMS:
        d = json.load(open(os.path.join(OUT, "parts", f"{sym}.json"))); real[sym] = d["real"]; null[sym] = d["null"]; Bs.add(d["B"])
    summ = {}
    for gname, syms in {"全15": SYMS, "FX8": FX8, "トレンド7": TREND7}.items():
        for per in ("前半", "後半"):
            for st in ("A", "B"):
                row = {}
                for gate in GATES:
                    if gate == "G4_nbr" and st == "B": continue
                    for k in [0.0] + KS:
                        v = [r[per][st][str(k)][gate] for s in syms for r in null[s] if per in r]
                        row[f"{gate}|k={k}"] = float(np.mean(v)) if v else float("nan")
                    row[f"{gate}|real_pass"] = int(sum(real[s][per][st]["0.0"][gate] for s in syms if per in real[s]))
                wr = [r[per][st]["0.0"]["winrate"] for s in syms for r in null[s] if per in r]
                row["null_winrate_p50_p95"] = [float(np.percentile(wr, 50)), float(np.percentile(wr, 95))]
                row["real_winrate"] = {s: real[s][per][st]["0.0"]["winrate"] for s in syms if per in real[s]}
                row["n_win_median"] = float(np.median([real[s][per][st]["0.0"]["n_win"] for s in syms if per in real[s]]))
                summ[f"{gname}|{per}|{st}"] = row
    verdict = {}
    for st in ("A", "B"):
        rs = [summ[f"全15|{p}|{st}"] for p in ("前半", "後半")]
        unusable = all(r["G1_win60|k=0.0"] > 0.10 or r["G1_win60|k=1.0"] < 0.50 for r in rs)
        usable = all(r["G1_win60|k=0.0"] <= 0.05 and r["G1_win60|k=1.0"] >= 0.80 for r in rs)
        verdict[st] = "使えない" if unusable else ("使える" if usable else "未確定")
    final = verdict["A"] if verdict["A"] == verdict["B"] else "未確定（A と B で割れた）"
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    p = os.path.join(OUT, f"Q333_result_{stamp}.json")
    json.dump(dict(question="Q333", B=sorted(Bs), verdict=final, verdict_by_strategy=verdict, summary=summ),
              open(p, "w"), ensure_ascii=False, indent=1, default=float)
    print("verdict:", final, verdict); print(p)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=300)
    ap.add_argument("--syms", default=""); ap.add_argument("--combine", action="store_true"); a = ap.parse_args()
    if a.combine: return combine()
    for sym in (a.syms.split(",") if a.syms else SYMS): run_sym(sym, a.B)

if __name__ == "__main__":
    main()
