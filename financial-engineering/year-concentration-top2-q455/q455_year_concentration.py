"""Q455 年別寄与の上位2年を除く集中度（アイデア候補 Q454-C1）

== 事前登録（計算前に固定・2026-10-22 21:45・Opus） ==
問い: 日足戦略の封印前の純損益は特定の年に集中しているか。
前提の訂正: アイデア候補の「確定・採用済みの日足戦略」は戦略台帳に 1 本も無い（2026-10-22 時点）。
  代わりに対象を次の 10 本に固定する（S07 の 5 本＝アイデア候補が名指し、＋ 台帳で「弱い正」として
  残った未確定の主要 5 本）。掃引しない。n_tests=10。
  S07: Q367 Q368 Q369 Q370 Q371（スプレッド実測コストの 04:4x 版）
  弱い正: Q385(BTC/ETH TSMOM60) Q389(キャリー符号) Q408(FOMC前・穴除外) Q403(FOMC日ドル売り) Q414(利上げ局面版)
  2 設定あるファイルは param=0（主設定）だけを使う。
データ: 各実験の results/*_year_sym_*.csv の pnl_net（コスト後）。
年の損益: その年に行のある銘柄の pnl_net の単純平均（等金額）。
封印: year<=2023 のみ（year_sym は年単位なので 2024 上半期は切り捨てる＝保守側）。
指標: 総和>0 の戦略について、上位 1・2 年の寄与割合＝上位 k 年の和/総和。上位 1・2 年を除いた年単位 t
  （平均/(sd/√n)）と符号。
帰無: 銘柄ごとに年ラベルを循環シフト（銘柄の有効年の中で、シフト量を一様に）→ 再集計した上位 2 年寄与割合、
  B=500・seed=455。銘柄間の同時性（同じ年に揃って勝つ）を壊す帰無。総和≤0 になった帰無標本は除く。
判定（戦略ごと・アイデア候補の固定どおり）:
  集中なし＝上位2年寄与割合 ≤ 帰無95点 かつ 除外後 t≥2
  集中あり＝寄与割合 > 帰無95点 または 除外後 t<2
  総和≤0 の戦略は「対象外（総和≤0）」。
  記述フラグ: 全年 t<2 の戦略は「除外後 t<2」の枝が自明に満たされるので、そのときは寄与割合の枝だけを
  「実質の判定」として併記する（判定規則は変えない）。
全体の判定: 対象 10 本に確定・採用済みが無いので、問いへの答えは「未確定」を上限とし、
  記述（どの戦略が何年に寄っているか）を知見として残す。
棄てた案: 0（年ラベルの集計後シフトは上位寄与割合が不変で帰無にならないので、銘柄別シフトを最初から採る）。
LLM の知識の締め切り: 2026-06（使っていない。計算は既存 CSV のみ）。
委託の確かめ方: 委託なし。
事前登録からの変更点: pnl_net が NaN の銘柄年（Q370 の L=250 の助走など・持ち高なし）を行ごと除く（初回は NaN が
  年平均に混ざり Q370 が nan になった。判定規則は不変。修正前は results/q455_year_concentration_before_fix_*.py）。
"""
import json, glob, os, sys
import numpy as np, pandas as pd
from datetime import datetime

FE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = {
    "Q367": "wide48-tsmom60-vol-target/results/Q367_year_sym_20261022_044131.csv",
    "Q368": "wide48-tsmom-l60-plain/results/Q368_year_sym_20261022_044235.csv",
    "Q369": "wide48-tsmom-l120-plain/results/Q369_year_sym_20261022_044334.csv",
    "Q370": "wide48-tsmom-l250-plain/results/Q370_year_sym_20261022_044435.csv",
    "Q371": "wide48-cross-sectional-mom60/results/Q371_year_sym_20261022_044538.csv",
    "Q385": "s08-crypto2-d1-tsmom-q385/results/Q385_year_sym_20261022_050806.csv",
    "Q389": "s09-fx22-carry-sign-q389/results/Q389_year_sym_20261022_134936.csv",
    "Q408": "s13-idx13-pre-fomc-drift-q401/results/Q408_year_sym_20261022_150457.csv",
    "Q403": "s13-usd7-fomc-day-dollar-sell-q403/results/Q403_year_sym_20261022_145954.csv",
    "Q414": "s15-fomc-dollar-sell-hiking-regime-q414/results/Q414_year_sym_20261022_154923.csv",
}
LAST_YEAR, B, SEED = 2023, 500, 455


def tstat(x):
    x = np.asarray(x, float)
    if len(x) < 3 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def year_series(d):
    return d.groupby("year")["pnl_net"].mean().sort_index()


def top_share(s, k):
    tot = s.sum()
    return float(np.sort(s.values)[::-1][:k].sum() / tot) if tot > 0 else float("nan")


def shifted(d, rng):
    out = []
    for sym, g in d.groupby("sym"):
        g = g.sort_values("year")
        v = np.roll(g["pnl_net"].values, rng.integers(len(g)))
        out.append(pd.DataFrame({"sym": sym, "year": g["year"].values, "pnl_net": v}))
    return pd.concat(out)


def main():
    rng = np.random.default_rng(SEED)
    rows = {}
    for q, rel in TARGETS.items():
        d = pd.read_csv(os.path.join(FE, rel))
        d = d[(d["param"] == 0) & (d["year"] <= LAST_YEAR)].dropna(subset=["pnl_net"])
        s = year_series(d)
        r = {"file": rel, "n_sym": int(d["sym"].nunique()), "years": [int(s.index.min()), int(s.index.max())],
             "n_years": int(len(s)), "year_pnl": {int(k): round(float(v), 4) for k, v in s.items()},
             "total": float(s.sum()), "mean": float(s.mean()), "t_all": tstat(s)}
        order = s.sort_values(ascending=False)
        r["top_years"] = [int(y) for y in order.index[:2]]
        for k in (1, 2):
            r[f"share_top{k}"] = top_share(s, k)
            rest = s.drop(order.index[:k])
            r[f"t_excl_top{k}"] = tstat(rest)
            r[f"mean_excl_top{k}"] = float(rest.mean())
        if r["total"] <= 0:
            r["verdict"] = "対象外（総和≤0）"
        else:
            null = []
            for _ in range(B):
                ns = year_series(shifted(d, rng))
                if ns.sum() > 0:
                    null.append(top_share(ns, 2))
            null = np.array(null)
            r["null_n"] = int(len(null))
            r["null_q"] = {p: float(np.quantile(null, p / 100)) for p in (2.5, 50, 95, 97.5)}
            r["null_p_share"] = float((1 + (null >= r["share_top2"]).sum()) / (1 + len(null)))
            r["null_degenerate"] = bool(r["null_q"][97.5] - r["null_q"][2.5] < 1e-9)
            share_hi = r["share_top2"] > r["null_q"][95]
            t_lo = not (r["t_excl_top2"] >= 2)
            r["verdict"] = "集中あり" if (share_hi or t_lo) else "集中なし"
            r["share_branch_only"] = "寄与割合が帰無95点超" if share_hi else "寄与割合は帰無95点以下"
            r["t_branch_trivial"] = bool(not (r["t_all"] >= 2))
        rows[q] = r
    out = {"qid": "Q455", "generated": datetime.now().isoformat(timespec="seconds"),
           "last_year": LAST_YEAR, "B": B, "seed": SEED, "n_tests": len(TARGETS),
           "multiple_comparisons": {"n_tests": len(TARGETS), "note": "戦略ごとの記述。全体判定は未確定が上限"},
           "results": rows}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", f"Q455_result_{ts}.json")
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    for q, r in rows.items():
        nq = r.get("null_q", {})
        print(f"{q} n_sym={r['n_sym']} yrs={r['years']} tot={r['total']:+.2f} t_all={r['t_all']:+.2f} "
              f"top={r['top_years']} sh1={r['share_top1']:.2f} sh2={r['share_top2']:.2f} "
              f"null95={nq.get(95, float('nan')):.2f} p={r.get('null_p_share', float('nan')):.3f} "
              f"t_ex1={r['t_excl_top1']:+.2f} t_ex2={r['t_excl_top2']:+.2f} -> {r['verdict']}")
    print(p)


if __name__ == "__main__":
    main()
