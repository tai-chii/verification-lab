# -*- coding: utf-8 -*-
"""Q586 S30 の composite 関門: Q583 の日次 L−S（コスト後）を生き残り 3 本（S17b・S21・S23）の等リスク合成に 1/4 で足し、
相関と合成 Sharpe の増分を出す。事前登録: 事前登録_q586.md（変更禁止）。

【判定（事前固定・変更禁止）】通過: (a) 3 本すべてと日次相関 ≤ 0.15 かつ (b) 単体 Sharpe ≥ 0.5 かつ (c) 4 本合成の Sharpe が 3 本合成を
重なり期間の前半・後半（重なりの中央で 2 分）とも下回らない。不通過: どれかを満たさない。
【多重比較】数えない（記述・運用の決まり 2026-10-29 の追加関門）。
実行: python3 kensho_composite_q586.py（Mac・数秒・pandas/numpy のみ）。道具 tools/composite_gate.py の既定の出力（2021 分割）も記述として残す。"""
import datetime, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.join(HERE, ".."); TOOLS = os.path.join(FE, "..", "tools")
sys.path.insert(0, TOOLS)
import composite_gate as G

QID = "Q586"; NAME = "S30 日本株 横断 ML（Q583 L−S・コスト後）"
CAND = os.path.join(FE, "jp-ml-xsec-holdout-q583", "results", "daily_jp_q583.csv")


def main():
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    d = pd.read_csv(CAND, index_col=0, parse_dates=True)
    tool_default = G.gate(d["ls"], NAME)                       # 記述（2021 分割は重なりに前半が無い）
    S = pd.read_csv(G.SURV, index_col=0, parse_dates=True)[G.SURV_COLS]
    c = d["ls"].copy(); c.index = pd.DatetimeIndex(c.index).normalize(); c = c.groupby(c.index).sum()
    idx = S.index.intersection(pd.date_range(c.index.min(), c.index.max()))
    S = S.loc[idx]; cz = c.reindex(idx).fillna(0.0); cz = cz / cz.std(ddof=1)
    mid = idx[len(idx) // 2]
    base = S.mean(axis=1); add = pd.concat([S, cz.rename("S30")], axis=1).mean(axis=1)
    pre = lambda x: x[x.index < mid]; post = lambda x: x[x.index >= mid]
    corr = {k: round(float(cz.corr(S[k])), 3) for k in S}
    W = pd.concat([S, cz.rename("S30")], axis=1).resample("W-FRI").sum()
    corr_w = {k: round(float(W["S30"].corr(W[k])), 3) for k in S}
    res = {"qid": QID, "name": NAME, "重なり期間": [str(idx.min().date()), str(idx.max().date())], "n_days": int(len(idx)), "中央": str(mid.date()),
           "相関（日次）": corr, "相関（週次）": corr_w,
           "単体Sharpe（重なり期間）": {"全": round(G.sh(cz), 2), "前": round(G.sh(pre(cz)), 2), "後": round(G.sh(post(cz)), 2)},
           "合成Sharpe（3本→4本）": {"全": [round(G.sh(base), 2), round(G.sh(add), 2)], "前": [round(G.sh(pre(base)), 2), round(G.sh(pre(add)), 2)],
                                 "後": [round(G.sh(post(base)), 2), round(G.sh(post(add)), 2)]},
           "生き残り各本のSharpe（重なり期間）": {k: round(G.sh(S[k]), 2) for k in S}}
    ok_a = all(v <= 0.15 for v in corr.values()); ok_b = G.sh(cz) >= 0.5
    ok_c = (G.sh(pre(add)) >= G.sh(pre(base))) and (G.sh(post(add)) >= G.sh(post(base)))
    res["関門"] = {"(a) 相関≤0.15": bool(ok_a), "(b) 単体Sharpe≥0.5": bool(ok_b), "(c) 合成が前後半とも下がらない": bool(ok_c)}
    res["machine_verdict"] = "通過" if (ok_a and ok_b and ok_c) else "不通過"
    res["rule"] = "通過: (a) 3 本すべてと日次相関 ≤ 0.15 かつ (b) 単体 Sharpe ≥ 0.5 かつ (c) 4 本合成の Sharpe が 3 本合成を重なり期間の前半・後半とも下回らない。不通過: どれかを満たさない"
    res["道具の既定（2021分割・記述）"] = tool_default
    res["data"] = {"候補": os.path.relpath(CAND, FE), "生き残り": os.path.relpath(G.SURV, FE), "候補の期間": [str(d.index.min().date()), str(d.index.max().date())]}
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    p = os.path.join(out, "result_q586.json"); json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    pd.concat([S, cz.rename("S30"), base.rename("合成3本"), add.rename("合成4本")], axis=1).to_csv(os.path.join(out, "daily_overlap_q586.csv"))
    print(json.dumps({k: res[k] for k in ("重なり期間", "n_days", "相関（日次）", "相関（週次）", "単体Sharpe（重なり期間）", "合成Sharpe（3本→4本）", "関門", "machine_verdict")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
