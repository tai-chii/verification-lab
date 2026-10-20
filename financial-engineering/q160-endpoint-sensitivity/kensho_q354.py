#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q354（Q352-C2 の次段階・方法論・事前登録 2026-10-20 Opus）
================================================================================
問い: Q160 の「確定」（ドンチャン55/20 の買い側ドリフト除去後 z≥2、トレンド6・商品4）は、
評価期間の開始年・終了年を 0／±1 年ずらした 9 通りで何通り保たれるか。

【出典】
- 接続ログ 2026-10-20 Q352-C2（hiro の Zenn: 2008〜2012 に 2007・2013 を足すだけで差が
  −121.68→−59.10 pips に縮み CI が 0 をまたいだ）× 改善判定「期間別を同時に見ればどこか1セルは偶然有意」。
- Q160: verification-lab/financial-engineering/long-short-decomposition/kensho_q160.py
  （全期間 2008-02〜2026-07、トレンド6 買い_adj +0.78bp z+2.45、商品4 +1.69bp z+2.88）。

【仮説（測る前に固定）】
H: Q160 の確定は端点の選び方に依らない（2 群とも 9/9 で買い側ドリフト除去後 z≥2）。

【定義（固定）】
- 期間: 開始 {2008,2009,2010}-01-01 × 終了 {2024,2025,2026}-12-31 の 9 通り。
  データを窓で切ってから Q160 の関数（load_csv・donchian_positions・daily_net_pnl_bp・
  side_series・group_stats・shuffle_common・z_against_null）をそのまま使う
  （窓の頭 56 足はウォームアップで評価外＝Q160 と同じ扱い）。
  (2008,2026) は Q160 と同じデータ範囲＝再現の確認に使う。
- 規則・コスト・ドリフト除去（窓内の平均リターン）・帰無（半年ごとの日時共通並べ替え）・
  B=500・seed=20261009（各セルで同じ seed から開始）は Q160 と同一。
- 数えるもの: 群ごとに、9 通りのうち 買い側ドリフト除去後 z≥2 のセル数 K。
  売り側 |z|<2 は記述（Q160 の H3 の再確認）として併記するが K には入れない。

【判定（事前固定・変更禁止）】
- 群ごと: K=9 → 頑健／K=7〜8 → 未確定（9 通りの z の最小値を記録して保留）／K≤6 → 端点依存。
- 総合（2 群のうち悪い方で決める。接続ログは群の合わせ方を書いていないのでここで固定）:
  - 両群 頑健 → **確定**「Q160 の確定は端点±1年に頑健」（改善判定は変えない）
  - どちらかが 端点依存 → **確定**「Q160 の確定は端点依存」→ 改善判定に
    「確定の前に端点±1年の 9 通りで z を出す」を点検項目として足す。Q160 の知見に注記。
  - それ以外（どちらかが 7〜8）→ **未確定**（最小 z を記録して保留）
- 注意: 9 セルは期間が大きく重なるので独立ではない。K は「端点を振ったときの閾値またぎの数」で、
  検定ではない。z≥2 の閾値近くの群（トレンド6 の z 2.45）は K が小さく出やすいことを予め書いておく。

【捨てた案の数】約3: ±2年まで広げる（25 通り・重い）、閾値を z≥1.96 にする（Q160 と揃えて 2）、
  売り側も K に入れる（問いが買い側の確定なので外す）。
【多重比較】2 群 × 9 = 18 本。判定は群ごとの K 1 本ずつ。商品4 ⊂ トレンド6 で独立でない。
【知識の締め切り】Claude の知識は 2026-06 まで。2025〜2026 の金・銀の急騰は知っている。
  終了 2024 のセルで商品4 の z が下がる方向の後知恵はあり得るが、判定規則は先に固定した。
【委託の確かめ方】設計・実行・解釈とも Opus（Q354・担当 opus）。(2008,2026) が Q160 の z を再現するかで実装を確認。

実行: python3 kensho_q354.py [--B 500] [--cells 2008-2026,2009-2024 ...]
      セルごとに results/Q354_cell_<start>-<end>.json を書き、--aggregate で集計 JSON を出す。
"""
import argparse, datetime as _dt, json, os, sys, warnings, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "long-short-decomposition"))
import kensho_q160 as q  # noqa: E402

OUT = os.path.join(HERE, "results")
STARTS = [2008, 2009, 2010]
ENDS = [2024, 2025, 2026]
q.PERIODS = ["全期間"]  # 判定に使うのは全期間だけ（前半・後半は計算しない）


def run_cell(start, end, B):
    rng = np.random.default_rng(q.SEED)
    series, costs = {}, {}
    lo, hi = pd.Timestamp(f"{start}-01-01"), pd.Timestamp(f"{end}-12-31 23:59:59")
    for sym in q.TREND6:
        f = os.path.join(q.DATA_DIR, f"data_{sym}_D1_fromH1.csv")
        d = q.load_csv(f)
        d = d[(d.time >= lo) & (d.time <= hi)].reset_index(drop=True)
        series[sym] = (d.time.values, d.close.values.astype(float)); costs[sym] = q.COST_RT[sym]
    groups = {"トレンド6": list(q.TREND6), "商品4": list(q.COMMODITIES4)}
    per_sym = {s: q.side_series(c, t, costs[s]) for s, (t, c) in series.items()}
    res = {g: q.group_stats(per_sym, syms, "全期間") for g, syms in groups.items()}
    all_t = np.unique(np.concatenate([series[s][0] for s in series]))
    null = {g: {k: [] for k in q.KEYS} for g in groups}
    for b in range(B):
        sh = q.shuffle_common(series, rng, all_t)
        ps = {s: q.side_series(c, t, costs[s]) for s, (t, c) in sh.items()}
        for g, syms in groups.items():
            gs = q.group_stats(ps, syms, "全期間")
            for k in q.KEYS:
                null[g][k].append(gs[k]["mean"])
    out = dict(start=start, end=end, B=B, seed=q.SEED,
               span={s: [str(pd.Timestamp(series[s][0][0]).date()), str(pd.Timestamp(series[s][0][-1]).date()), int(len(series[s][1]))] for s in series},
               groups={})
    for g in groups:
        r = {"expo_long": res[g].get("expo_long"), "drift_bp": res[g].get("drift_bp")}
        for k in q.KEYS:
            z, pct, nm, ns, p025, p975 = q.z_against_null(res[g][k]["mean"], null[g][k])
            r[k] = dict(mean=res[g][k]["mean"], z=z, null_mean=nm, null_sd=ns, null_p025=p025, null_p975=p975)
        out["groups"][g] = r
    path = os.path.join(OUT, f"Q354_cell_{start}-{end}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    print(f"[Q354] {start}-{end} " + " | ".join(
        f"{g}: L_adj {out['groups'][g]['long_adj']['mean']:+.2f} z{out['groups'][g]['long_adj']['z']:+.2f} (null {out['groups'][g]['long_adj']['null_p025']:+.2f}〜{out['groups'][g]['long_adj']['null_p975']:+.2f}) S_adj z{out['groups'][g]['short_adj']['z']:+.2f}"
        for g in groups))


def cat(K):
    return "頑健" if K == 9 else ("未確定" if K >= 7 else "端点依存")


def aggregate():
    cells = {}
    for p in sorted(glob.glob(os.path.join(OUT, "Q354_cell_*.json"))):
        d = json.load(open(p, encoding="utf-8")); cells[f"{d['start']}-{d['end']}"] = d
    assert len(cells) == 9, f"セルが 9 でない: {sorted(cells)}"
    by = {}
    for g in ["トレンド6", "商品4"]:
        zs = {k: cells[k]["groups"][g]["long_adj"]["z"] for k in cells}
        K = sum(1 for v in zs.values() if np.isfinite(v) and v >= 2.0)
        by[g] = dict(K=K, category=cat(K), z_min=min(zs.values()), z_max=max(zs.values()),
                     long_adj_z=zs, long_adj_mean={k: cells[k]["groups"][g]["long_adj"]["mean"] for k in cells},
                     short_adj_z={k: cells[k]["groups"][g]["short_adj"]["z"] for k in cells})
    cats = [by[g]["category"] for g in by]
    if all(c == "頑健" for c in cats):
        overall = "確定（端点±1年に頑健）"
    elif any(c == "端点依存" for c in cats):
        overall = "確定（Q160 の確定は端点依存 → 改善判定に点検項目を足す）"
    else:
        overall = "未確定（最小 z を記録して保留）"
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dict(queue_id="Q354", run_at=stamp, by_group=by, overall=overall,
               reproduce_Q160={g: cells["2008-2026"]["groups"][g]["long_adj"]["z"] for g in by})
    p = os.path.join(OUT, f"Q354_result_{stamp}.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    for g in by:
        print(g, "K=", by[g]["K"], by[g]["category"], "z_min", round(by[g]["z_min"], 2), "z_max", round(by[g]["z_max"], 2))
    print("総合:", overall); print("JSON:", p)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=q.NULL_B)
    ap.add_argument("--cells", default=""); ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args(); os.makedirs(OUT, exist_ok=True)
    if a.aggregate:
        aggregate(); sys.exit(0)
    cells = [tuple(map(int, c.split("-"))) for c in a.cells.split(",")] if a.cells else [(s, e) for s in STARTS for e in ENDS]
    for s, e in cells:
        run_cell(s, e, a.B)
