#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kensho_s21_結合.py — 状態ラベルの点検（§2）と、S21 の学習外の取引への最初の結合（§3）。事前登録_状態ラベル.md のまま（2026-11-13 19:57 固定）。

点検（成績は見ない・2014-10〜2025-09）: 切り替わりが軸ごとに年 8 回以下（超えた軸だけ連続 5→10 に 1 回だけ直す。それでも超えたら使わない）、
  少ない側の状態が日数の 15% 以上（届かない軸は結合に使わない）、軸どうしの φ 係数、定義どおりに動いているかの日付。
結合（記述・規則は変えない）: 19 銘柄の WF の取引（2014〜2024 年度）。軸ごとに 2 つの状態の 1 件の平均 R の差。t は銘柄×週でまとめた標準誤差（Q721 と同じ）。Holm。
  見込みの向き: 荒さ 高 > 低、株の向き 上 > 下、方向感 強 > 弱。
  読み方: Holm 後 p ≤ 0.05 → 「その軸で差がある」（記述どまり・前向きの予約）。どれも届かない → 「この 3 軸では分かれない」。

使い方:  <venv_forward の python> kensho_s21_結合.py --check    # 点検だけ（成績を読まない）
         <venv_forward の python> kensho_s21_結合.py            # 点検 → 結合
"""
import argparse, datetime as dt, json, math, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); FE = os.path.dirname(HERE); sys.path.insert(0, HERE)
import make_states as MS

T0, T1 = "2014-10-01", "2025-09-30"
MAX_SW, MIN_SHARE, PHI_MAX = 8.0, 0.15, 0.6
ANCHORS = [("2020-03-16", "荒さ", "高"), ("2020-03-23", "株の向き", "下"), ("2022-06-16", "株の向き", "下"), ("2017-06-30", "株の向き", "上"), ("2021-06-30", "株の向き", "上")]
GROUPS = {"FX 主要 7": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD", "EURGBP"],
          "円 7": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"], "指数と金 5": ["US500", "USTECH", "GER40", "JPN225", "XAUUSD"]}


def check(cal, R, us):
    """§2。返り値: (ラベルの表, 点検の結果, 使う軸)。"""
    N = dict(MS.N_DEFAULT); res = {"期間": [T0, T1], "軸": {}}; lab = MS.build(cal, R, us, N)
    def stats(lab, ax):
        w = lab.loc[T0:T1]; w = w[w[ax].notna()]; years = len(w) / 252.0
        sw = int(w[f"{ax}_切り替わり"].sum()); sh = w[ax].value_counts(normalize=True)
        return {"年あたりの切り替わり": round(sw / years, 2), "切り替わりの回数": sw, "日数の割合": {k: round(float(v), 3) for k, v in sh.items()}, "少ない側の割合": round(float(sh.min()), 3) if len(sh) == 2 else 0.0}
    use = []
    for ax in MS.AXES:
        s = stats(lab, ax); s["連続"] = N[ax]
        if s["年あたりの切り替わり"] > MAX_SW:           # 1 回だけ 5 → 10 に直す
            N[ax] = 10; lab = MS.build(cal, R, us, N); s2 = stats(lab, ax); s2["連続"] = 10; s2["直す前（連続5）"] = s; s = s2
        s["切り替わりは多すぎない"] = bool(s["年あたりの切り替わり"] <= MAX_SW); s["偏りすぎていない"] = bool(s["少ない側の割合"] >= MIN_SHARE)
        s["使う"] = bool(s["切り替わりは多すぎない"] and s["偏りすぎていない"]); res["軸"][ax] = s
        if s["使う"]: use.append(ax)
    w = lab.loc[T0:T1]; w = w[w["組み合わせ"].notna()]; phi = {}
    axes = list(MS.AXES)
    for i in range(3):
        for j in range(i + 1, 3):
            a = (w[axes[i]] == MS.AXES[axes[i]][0]).astype(float); b = (w[axes[j]] == MS.AXES[axes[j]][0]).astype(float)
            v = float(np.corrcoef(a, b)[0, 1]); phi[f"{axes[i]}×{axes[j]}"] = {"φ": round(v, 3), "別々の発見として数えない": bool(abs(v) > PHI_MAX)}
    res["軸どうしの重なり"] = phi
    res["組み合わせの日数の割合"] = {k: round(float(v), 3) for k, v in w["組み合わせ"].value_counts(normalize=True).items()}
    anc = []
    for d, ax, want in ANCHORS:
        i = lab.index.searchsorted(pd.Timestamp(d)); got = lab[ax].iloc[i] if i < len(lab) else "範囲外"; anc.append({"日": d, "軸": ax, "期待": want, "実際": got, "一致": bool(got == want)})
    res["定義どおりに動いているか"] = anc; res["すべて一致"] = bool(all(x["一致"] for x in anc)); res["連続（最終）"] = N; res["使う軸"] = use
    return lab, res, use


def m_se(x):
    g = x.groupby(["sym", "week"])["R"].agg(["sum", "size"]); n = g["size"].sum()
    if n == 0: return float("nan"), float("nan"), 0
    m = g["sum"].sum() / n
    return float(m), float(np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / n), int(n)


def diff(X, ax):
    hi, lo = MS.AXES[ax]; a, sa, na = m_se(X[X[ax] == hi]); b, sb, nb = m_se(X[X[ax] == lo])
    se = math.sqrt(sa ** 2 + sb ** 2) if na and nb else float("nan"); t = (a - b) / se if se and se == se else float("nan")
    p = math.erfc(abs(t) / math.sqrt(2)) if t == t else float("nan")
    return {hi: {"平均R": round(a, 4), "件数": na}, lo: {"平均R": round(b, 4), "件数": nb}, f"差（{hi}−{lo}）": round(a - b, 4), "t": round(t, 2), "p": p}


def holm(ps):
    order = sorted(ps, key=ps.get); m = len(order); out = {}; prev = 0.0
    for r, k in enumerate(order):
        adj = min(1.0, max(prev, (m - r) * ps[k])); out[k] = adj; prev = adj
    return out


def attach(tr, lab):
    """日 d の取引に、d の前の営業日の状態を当てる。"""
    cal = lab.index.values; d = tr["entry"].dt.tz_convert("UTC").dt.tz_localize(None).dt.normalize().values
    idx = np.searchsorted(cal, d, side="left") - 1
    for ax in list(MS.AXES) + ["組み合わせ"]:
        v = lab[ax].values; tr[ax] = [v[i] if i >= 0 else None for i in idx]
    return tr


def join(lab, use):
    Rd = os.path.join(FE, "s21-h1-ml-rr-weekcap-q515", "results")
    W = pd.concat([pd.read_csv(os.path.join(Rd, "trades_q534_E1.csv")), pd.read_csv(os.path.join(Rd, "trades_q524_new4.csv"))], ignore_index=True)   # S21 の WF の取引（Q716〜Q721 と同じ表）
    W["entry"] = pd.to_datetime(W["entry"], utc=True); W["fy"] = np.where(W["entry"].dt.month >= 10, W["entry"].dt.year, W["entry"].dt.year - 1)
    W = W[(W.fy >= 2014) & (W.fy <= 2024)].copy(); W = attach(W, lab); n0 = len(W); W = W[W["組み合わせ"].notna()].copy()
    W["向き"] = np.where(W["a"] <= 2, "買い", "売り"); W["群"] = W["sym"].map({s: g for g, ss in GROUPS.items() for s in ss}); W["年"] = W["entry"].dt.year
    a, sa, n = m_se(W)
    out = {"件数": n, "状態が付かなかった件数": int(n0 - len(W)), "全体": {"平均R": round(a, 4), "t": round(a / sa, 2)}, "主": {}}
    ps = {}
    for ax in use:
        out["主"][ax] = diff(W, ax); ps[ax] = out["主"][ax]["p"]
    hp = holm(ps) if ps else {}
    for ax in use:
        d = out["主"][ax]; d["p_Holm"] = hp[ax]; hi, lo = MS.AXES[ax]; dv = d[f"差（{hi}−{lo}）"]
        d["読み"] = ("その軸で差がある（見込みどおり）" if dv > 0 else "その軸で差がある（見込みと逆）") if hp[ax] <= 0.05 else "差は見えない"
    hits = [ax for ax in use if hp[ax] <= 0.05]
    out["判定"] = ("差がある軸: " + "・".join(hits) + "（記述どまり・前向きの予約）") if hits else "この 3 軸では S21 の成績は分かれない"
    # ---- 記述（数えない）
    desc = {"軸×銘柄の群": {}, "軸×買い売り": {}}
    for ax in use:
        desc["軸×銘柄の群"][ax] = {g: diff(W[W["群"] == g], ax) for g in GROUPS}
        desc["軸×買い売り"][ax] = {s: diff(W[W["向き"] == s], ax) for s in ("買い", "売り")}
    cell_all = W.groupby("組み合わせ")["R"].agg(["mean", "size"])
    desc["組み合わせ別（切るのには使わない）"] = {k: {"平均R": round(float(r["mean"]), 4), "件数": int(r["size"])} for k, r in cell_all.iterrows()}
    in_ = W["年"].between(2017, 2020); oth = W[~in_]; tgt = W[in_]
    cm = oth.groupby("組み合わせ")["R"].mean(); pred = float(tgt["組み合わせ"].map(cm).fillna(oth["R"].mean()).mean())
    act, base = float(tgt["R"].mean()), float(oth["R"].mean())
    desc["2017〜2020 年（暦年）の突出"] = {"その 4 年の平均R": round(act, 4), "ほかの年の平均R": round(base, 4), "状態の内訳からの見込み（ほかの年の状態別の平均を当てはめ）": round(pred, 4),
                                   "状態の内訳で説明できる割合": round((pred - base) / (act - base), 3) if abs(act - base) > 1e-9 else None}
    yt = {}
    for y, g in W.groupby("年"):
        yt[int(y)] = {"件数": int(len(g)), "平均R": round(float(g["R"].mean()), 4), **{f"{ax}＝{MS.AXES[ax][0]}の割合": round(float((g[ax] == MS.AXES[ax][0]).mean()), 2) for ax in MS.AXES}}
    desc["年ごと（暦年）"] = yt
    fp = os.path.join(FE, "..", "..", "トレード", "forward", "S21", "記録", "trades_latest.csv")
    if os.path.exists(fp):
        F = pd.read_csv(fp); F = F[F["status"] == "closed"].copy(); F["entry"] = pd.to_datetime(F["entry"], utc=True); F = attach(F, lab)
        desc["フォワードの記録（件数が少ないので読まない）"] = {"件数": int(len(F)), **{ax: {str(k): {"件数": int(len(g)), "平均R": round(float(g["R"].mean()), 3)} for k, g in F.groupby(ax)} for ax in MS.AXES}}
    out["記述"] = desc
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    cal, R, us, report = MS.load(a.smoke)
    od = os.path.join(HERE, "results", "_smoke") if a.smoke else os.path.join(HERE, "results"); os.makedirs(od, exist_ok=True)
    lab, chk, use = check(cal, R, us)
    keep = lab[lab["組み合わせ"].notna()].copy(); keep.index.name = "date"
    cols = list(MS.AXES) + ["組み合わせ"] + [f"{ax}_切り替わり" for ax in MS.AXES] + ["荒さ_値", "株の向き_値", "方向感_値", "方向感_基準"]
    keep[cols].round(4).to_csv(os.path.join(od, "状態ラベル.csv"), encoding="utf-8")
    json.dump(chk, open(os.path.join(od, "点検.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 点検 ==="); print(json.dumps(chk, ensure_ascii=False, indent=1))
    if a.check or a.smoke: return
    if not chk["すべて一致"]: print("定義どおりに動いていない日がある → 結合しない（コードを直す）"); sys.exit(2)
    out = {"実行": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "事前登録": "事前登録_状態ラベル.md（2026-11-13 19:57）", "使った軸": use, "点検": chk, **join(lab, use)}
    json.dump(out, open(os.path.join(od, "S21_結合.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("=== 結合 ==="); print(json.dumps({k: out[k] for k in ("件数", "状態が付かなかった件数", "全体", "主", "判定", "記述")}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
