#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q571: S21 を東京時間（0〜7 UTC）のエントリーに限ると、全時間帯より 1 件あたり R と日次 t が上がり、円クロス 4 本を足しても保たれ、深夜窓（21〜24 UTC）は Fintokei のコストを引くと消えるか
================================================================================

【出典】
- 計画（事前登録）: 東京時間 10 案の 1・8・10（Fable 2026-10-30 深夜・taichi「寝ている間に検証するコード」）。README_session_20261030.md（事後の切り分け: 5 窓で東京が 3 データとも正・重複と NY が負）。
- 知見: S21 の効いている入力は前日の実体・値幅（アブレーション）。取引量が多い時間ほど弱い（重複が最悪）。
- 運用の決まり 2026-10-29: 合成の追加関門（tools/composite_gate.py）を記述で見る。S21 本体は凍結・変えない（別 ID）。

【仮説（測る前に固定）】
H1a（東京限定）: WF 15 銘柄（q534 E1）で、東京窓（現地 9:00〜ロンドン 8:00 の前）のエントリーだけに限ると、R/件と日次 t が全時間帯より高く、前半（<2021）・後半（≥2021）とも R/件 > 0。
H1b（円クロス）: 銘柄外の円クロス 4 本（q524）でも東京窓の R/件 > 0 で、15 銘柄＋円クロス 4 の東京限定の日次 t ≥ 2（全期間）。
H1c（深夜）: 深夜窓（NY 17:00〜東京 9:00）は後半（≥2021）で R/件 ≤ 0、または q539 の Fintokei コスト（c 列・R 単位）を追加で引くと全期間で R/件 ≤ 0。
H0: 東京限定の R/件が全時間帯と差がない（z<2）。

【データ】`s21-h1-ml-rr-weekcap-q515/results/` の取引明細: trades_q534_E1.csv（WF 15 銘柄 2014-10〜2025-09）、trades_q524_new4.csv（円クロス 4・同期間）、
trades_final_q527.csv（最終 1 年 2025-10〜2026-09・**規程で 1 回だけ開けたものの再利用＝参考値**）、trades_cost_q539.csv.gz（c 列 = Fintokei の平均スプレッド＋手数料を R 単位に直したもの・i_match で q534 に対応）。
封印: 取引明細は 2025-09 まで（q527 は参考）。新しい売買はしない。

【定義（1 通りに固定）】
- 5 窓（現地時刻・夏時間込み）: 東京のみ = 東京 9:00 以降かつロンドン 8:00 前／ロンドンのみ = ロンドン 8:00 以降かつ NY 8:00 前／重複 = NY 8:00 以降かつロンドン 17:00 前／
  NY のみ = ロンドン 17:00 以降かつ NY 17:00 前／深夜 = それ以外。取引はエントリー時刻の窓に属する。
- R/件 = 取引の R の平均。日次 t = 決済日で R を合計した日次系列の t（√n 倍）。前半 <2021-01-01・後半 ≥。
- 帰無（H1a）: 各取引の窓ラベルを「同じ週の中」で並べ替え（週内の取引数・R の分布を保ち、窓との対応だけ壊す）B=1000 回 → 東京の R/件の帰無 → z。
- 深夜の Fintokei コスト: q539 の c を i_match=True の取引に当て、R_fin = R − c（Dukascopy のコストはすでに R に入っているので二重引き＝保守側）。

【測るもの】窓別 R/件・件数・日次 t（全・前・後）、東京限定と全時間帯の差と z、円クロスを足した東京限定の日次 t、深夜の R と R_fin、
合成の追加関門（東京限定の日次 R・記述）、年別の東京 R/件（記述）、最終 1 年の窓別（参考）。

【判定（事前固定・変更禁止）】
H1a: 東京限定の R/件 > 全時間帯 かつ z ≥ 2 かつ 前後半とも東京 R/件 > 0 → 支持。東京 R/件 ≤ 全時間帯 または z < 1 → 棄却。ほか未確定。
H1b・H1c は記述（H1a の支持のときに S21t の対象と境界を決める材料）。
多重比較: 判定は H1a の 1 本（z と前後半）。5 窓の表・円クロス・深夜・年別は記述。

【捨てた案の数】約 4: 窓の境界の格子（6〜8 時台を動かす）、ロンドンのみも足す、時刻 1 時間単位の選択、最終 1 年を判定に使う（規程違反）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】設計・コードは Fable（2026-10-30 深夜）。実行と解釈は Opus。実行者は JSON の main（東京 vs 全・z・前後半）と machine_verdict を返す。
【実装】python3 kensho_s21_tokyo_q571.py（B=1000・1 分）／--smoke（合成・判定に使わない）
"""
import argparse, datetime as _dt, gzip, json, math, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "s21-h1-ml-rr-weekcap-q515", "results")
QID = "Q571"; SPLIT = pd.Timestamp("2021-01-01", tz="UTC"); SEED = 20261030
WIN_ORDER = ["東京のみ", "ロンドンのみ", "重複", "NYのみ", "深夜"]


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def f(x, nd=4):
    try:
        return None if x is None or not np.isfinite(x) else round(float(x), nd)
    except Exception:
        return None


def windows(t):
    lon = t.dt.tz_convert("Europe/London").dt.hour; ny = t.dt.tz_convert("America/New_York").dt.hour; tok = t.dt.tz_convert("Asia/Tokyo").dt.hour
    out = np.full(len(t), "深夜", dtype=object)
    out[(tok >= 9) & (lon < 8)] = "東京のみ"
    out[(lon >= 8) & (ny < 8)] = "ロンドンのみ"
    out[(ny >= 8) & (lon >= 8) & (lon < 17)] = "重複"
    out[(lon >= 17) & (ny >= 8) & (ny < 17)] = "NYのみ"
    return out


def load(name, smoke, rng):
    if smoke:
        n = 20000; t = pd.date_range("2014-10-01", periods=n, freq="4h", tz="UTC")
        return pd.DataFrame({"sym": rng.choice(["EURUSD", "USDJPY"], n), "entry": t, "exit": t + pd.Timedelta(hours=6), "R": rng.normal(0.04, 1.0, n)})
    p = os.path.join(RES, name)
    d = pd.read_csv(p, compression="gzip" if p.endswith(".gz") else None)
    d["entry"] = pd.to_datetime(d["entry"], utc=True); d["exit"] = pd.to_datetime(d["exit"], utc=True)
    return d


def daily(d):
    return d.groupby(d["exit"].dt.tz_convert(None).dt.normalize())["R"].sum()


def table(d):
    out = {}
    for w in WIN_ORDER + ["全時間帯"]:
        x = d if w == "全時間帯" else d[d["win"] == w]
        if len(x) < 5:
            continue
        r = {"n": int(len(x)), "R_per_trade": f(x["R"].mean()), "t_trade": f(tstat(x["R"]), 2), "t_daily": f(tstat(daily(x)), 2)}
        for nm, m in (("pre", x["entry"] < SPLIT), ("post", x["entry"] >= SPLIT)):
            y = x[m]; r[f"R_{nm}"] = f(y["R"].mean()) if len(y) > 5 else None; r[f"t_daily_{nm}"] = f(tstat(daily(y)), 2) if len(y) > 20 else None
        out[w] = r
    return out


def run(args):
    rng = np.random.default_rng(args.seed)
    wf = load("trades_q534_E1.csv", args.smoke, rng); wf["win"] = windows(wf["entry"])
    jp = load("trades_q524_new4.csv", args.smoke, rng); jp["win"] = windows(jp["entry"])
    fin = load("trades_final_q527.csv", args.smoke, rng); fin["win"] = windows(fin["entry"])
    res = {"wf15": table(wf), "jpy4": table(jp), "final_year_ref": table(fin)}
    # H1a: 東京 vs 全・帰無（週内で窓ラベルを並べ替え）
    tok = wf[wf["win"] == "東京のみ"]; obs = float(tok["R"].mean() - wf["R"].mean())
    wk = wf["entry"].dt.tz_convert(None).dt.to_period("W").astype(str).values; lab = wf["win"].values.copy(); Rv = wf["R"].values
    groups = pd.Series(np.arange(len(wf))).groupby(wk).indices
    null = []
    for _ in range(args.B):
        lb = lab.copy()
        for idx in groups.values():
            if len(idx) > 1:
                lb[idx] = lb[rng.permutation(idx)]
        null.append(float(Rv[lb == "東京のみ"].mean() - Rv.mean()))
    null = np.asarray(null); z = float((obs - null.mean()) / null.std(ddof=1)) if null.std(ddof=1) > 0 else float("nan")
    # H1b: 15＋円クロス 4 の東京限定
    both = pd.concat([tok, jp[jp["win"] == "東京のみ"]], ignore_index=True)
    h1b = {"n": int(len(both)), "R_per_trade": f(both["R"].mean()), "t_daily_all": f(tstat(daily(both)), 2),
           "t_daily_pre": f(tstat(daily(both[both["entry"] < SPLIT])), 2), "t_daily_post": f(tstat(daily(both[both["entry"] >= SPLIT])), 2),
           "jpy4_tokyo_R": f(jp[jp["win"] == "東京のみ"]["R"].mean())}
    # H1c: 深夜と Fintokei コスト
    h1c = {}
    try:
        c = load("trades_cost_q539.csv.gz", args.smoke, rng) if not args.smoke else None
        if c is not None and "c" in c.columns:
            c = c[c.get("i_match", True) == True]; c["win"] = windows(c["entry"])
            for w in WIN_ORDER:
                x = c[c["win"] == w]
                h1c[w] = {"n": int(len(x)), "R": f(x["R"].mean()), "c_mean": f(x["c"].mean()), "R_minus_c": f((x["R"] - x["c"]).mean()),
                          "R_minus_c_post": f((x[x["entry"] >= SPLIT]["R"] - x[x["entry"] >= SPLIT]["c"]).mean())}
    except Exception as e:
        h1c = {"error": str(e)}
    late = res["wf15"].get("深夜", {})
    h1c["verdict_desc"] = ("深夜は後半で R≤0" if (late.get("R_post") is not None and late["R_post"] <= 0) else "深夜は後半も R>0") + \
        ("・Fintokei コスト後も R>0" if h1c.get("深夜", {}).get("R_minus_c", 0) and h1c["深夜"]["R_minus_c"] > 0 else "")
    # 年別（記述）
    by_year = {int(y): {"tokyo_R": f(g[g["win"] == "東京のみ"]["R"].mean()), "all_R": f(g["R"].mean()), "n_tokyo": int((g["win"] == "東京のみ").sum())}
               for y, g in wf.groupby(wf["entry"].dt.year)}
    main = {"tokyo_R": f(tok["R"].mean()), "all_R": f(wf["R"].mean()), "diff": f(obs), "z": f(z, 2), "null_mean": f(null.mean()), "null_sd": f(null.std(ddof=1)),
            "tokyo_R_pre": res["wf15"]["東京のみ"].get("R_pre"), "tokyo_R_post": res["wf15"]["東京のみ"].get("R_post"),
            "tokyo_t_daily": res["wf15"]["東京のみ"].get("t_daily"), "all_t_daily": res["wf15"]["全時間帯"].get("t_daily")}
    g = lambda k: main[k] if main.get(k) is not None else float("nan")
    if g("tokyo_R") > g("all_R") and g("z") >= 2 and g("tokyo_R_pre") > 0 and g("tokyo_R_post") > 0:
        verdict = "支持: 東京限定は全時間帯より R/件が高く、前後半とも正"
    elif g("tokyo_R") <= g("all_R") or g("z") < 1:
        verdict = "棄却"
    else:
        verdict = "未確定"
    out = {"question": "S21 を東京時間のエントリーに限ると成績は上がるか（＋円クロス・深夜のコスト）", "settings": {"B": args.B, "split": str(SPLIT.date()), "windows": "現地時刻 5 窓（README_session_20261030.md）"},
           "main": main, "H1b_jpy": h1b, "H1c_late": h1c, "tables": res, "by_year_wf15": by_year, "machine_verdict": verdict,
           "multiple_comparisons": "判定は H1a の 1 本（z・前後半）。H1b・H1c・5 窓の表・年別・最終 1 年は記述。"}
    tok_daily = daily(both).rename("S21t")
    return out, tok_daily


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=1000); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(); res, td = run(a)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True); ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{QID}" if a.smoke else QID
    p = os.path.join(out, f"{pre}_result_{ts}.json")
    if not a.smoke:
        try:
            import sys; sys.path.insert(0, os.path.join(HERE, "..", "..", "tools")); from composite_gate import gate
            res["composite_gate"] = gate(td, "S21t 東京限定（15＋円クロス 4）")
        except Exception as e:
            res["composite_gate"] = f"失敗: {e}"
    json.dump({"qid": QID, "smoke": a.smoke, "generated": ts, **res}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    td.to_csv(os.path.join(out, f"{pre}_daily_S21t_{ts}.csv"))
    print("wrote", os.path.relpath(p, HERE)); print("main:", res["main"]); print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
