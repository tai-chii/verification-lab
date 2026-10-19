#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q346: 15銘柄の時系列モメンタムで、直前の経路が滑らか（R² 高・FIP 連続的）なほど翌月の順張り純損益は大きいか
================================================================================
（Clenow の「90日の対数回帰の傾き×R²」の R² 項と、Da・Gurun・Warachka 2014 の FIP を時系列へ移植・Q345-C1）

【出典・事前登録】
- 計画: 検証/学問/金融工学/知識/文献/アイデア候補.md の 2026-10-19 の行（Q345-C1）と 接続ログ.md 2026-10-19「移植（Q345-C1）」の行。
  判定規則・期間・帰無はそこに書いた文言をそのまま使う（下に写す）。
- 近い既存検証: Q246（ADX(14)>25 フィルタ・棄却）、Q218（TSMOM の定義＝直前252日の符号・21日ごと・段階1コスト）、Q249（合図の強さの3分位）。
- 先行研究チェック: 接続ログ 2026-10-19 Q345-C1（WebSearch standard・検索語4本）。為替・商品・株価指数の TSMOM を R²/FIP で条件付けて翌月純損益を測った研究は見つからない。
  Da ほか 2014 は紹介記事の要約経由（本文未読）。

【仮説（測る前に固定）】
H: 同じ TSMOM の向きでも、読み日の直前の経路が滑らかな（R² が高い／FIP が低い＝連続的な）銘柄・月ほど、翌21日の符号付き純損益は大きい。

【データ】15銘柄 D1_fromH1（2008〜2026-06。事前登録の文言は「2026-07」だが手元の最終日は 2026-06-30）。片道コスト段階1（fe_core.cost_bp_oneway）。ネット不要。

【定義（1通りに固定）】
- 合図（Q218 と同じ）: 直前252日（各銘柄自身の取引日）の対数リターンの符号。21日ごと（全銘柄共通の日付格子・最初の読み日は 252+60 本目）に読み、次の読み日まで持つ。
  読み日にその銘柄の足がない場合は建玉0（Q218 と同じ valid の扱い）。
- 損益: fe_core.pnl_bp（t の終値で決め t+1 のリターンに効く・建玉の変化に片道コスト）。セル＝(銘柄, 読み日) の翌21日の純損益の合計 [bp]。建玉0のセルは除く。
- R²: 直前90本（銘柄自身の取引日）の対数終値を時間に回帰した決定係数（＝相関の2乗）。向きは問わない（事前登録どおり R² 単独）。
- FIP: sign(直前252日リターン)×(直前252本の日次リターンのうち 下げの割合 − 上げの割合)。小さいほど連続的（滑らか）。
  ※ 事前登録の文言は割合を数える窓を明記していなかった。Da ほか 2014 の形成期間＝PRET の窓に合わせ 252 本に固定（実行前に決定）。
- 高低: 各銘柄の過去の読み日の値の中央値（拡張窓・当日を含まない・最低12回分）より R² が高い／FIP が低いセルを「滑らか」。
- 差: 年ごとに全銘柄のセルをプールして mean(滑らか) − mean(滑らかでない) [bp/月]。年を単位に t（年単位 t）。
- 期間: 前半 2008〜2016／後半 2017〜（読み日の年）。記述: 2022〜（Clenow 記事の「2022年以降は R² 項が逆効果」に合わせる）。

【判定（事前固定・変更禁止）】条件は R² と FIP の 2 つだけ。それぞれについて
  前後半とも 差>0 かつ 年単位 t≥2 → 支持。どちらかの期間で 差<0（符号が逆）か、両期間とも |t|<2 → 棄却。それ以外 → 未確定。
多重比較: 判定は 2 条件 × 前後半。両期間の一致を要求するので追加の補正はしない（2 条件のどちらかが支持でも「1/2」と書く）。

【信号の強さとの区別（Q246 に近いため・判定とは別の事前固定の記述）】
R² は経路の傾きの t 値と、FIP は |リターン| と機械的に絡む。そこで (a) 合図の強さ s=|ret252|/(σ60·√252) を同じ拡張中央値で高低に分けた差、
(b) 強さの高低それぞれの中で滑らか−非滑らかの差を出して 2 つを等ウェイト平均した「強さ層別の差」、(c) R²・FIP と s の Spearman、を出す。
読み方（事前に固定）: 主判定が支持でも (b) が前後半どちらかで符号が逆か |t|<2 なら「強さの言い換え」と書く。

【帰無】R²・FIP の日次系列を銘柄内で循環シフト（最小42日・各銘柄の有限区間の中で回す）B=1000 → 期間ごとの差の帰無分布 → z と 2.5/97.5 点。
Q320 の規則（束ねた量に銘柄ごとの並べ替えを使うと帰無が狭い）に従い、全銘柄で同じ k を使う共通シフト版も出す。判定は年単位 t なので z は記述。

【捨てた案の数】約5: 傾き×R² の合成点（Clenow の原形・強さと混ざる）、FIP を90本で数える、3分位、毎日のリバランス、2022〜を判定に入れる。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。データも 2026-06 まで＝全期間が締め切り以前（未来の情報は使えないが、期間中の相場を LLM が知っていた可能性はある）。規則は固定で相場観は使わない。

【委託の確かめ方】設計は接続ログ 2026-10-19（本体）。コード・実行・一次の解釈は本体から委託されたサブエージェント（Opus）。
返すのは結論ではなく JSON のパス・主要な統計量（差・年単位 t・z・件数）。本体は JSON を開いて照合する。

実行: python3 kensho_path_smoothness_q346.py（B=1000）／--B 20／--smoke（合成データ・判定には使わない）
"""
import os, sys, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *  # noqa

QID = "Q346"
LB, H, WIN, VOL_N, MIN_PRIOR, MIN_SHIFT = 252, 21, 90, 60, 12, 42
PERIODS = (("all", 0, 9999), ("pre", 0, SPLIT_YEAR), ("post", SPLIT_YEAR, 9999), ("y2022", 2022, 9999))
T975 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 11: 2.20, 12: 2.18, 13: 2.16, 14: 2.14, 15: 2.13, 16: 2.12, 17: 2.11, 18: 2.10}


def own_features(df):
    """銘柄自身の取引日で R²(90)・FIP(252)・強さ・合図を作る。"""
    c = df["close"].astype(float).values
    lc = pd.Series(np.log(c))
    tt = pd.Series(np.arange(len(c), dtype=float))
    r2 = lc.rolling(WIN).corr(tt) ** 2
    slope_sign = np.sign(lc.rolling(WIN).cov(tt))
    ret252 = lc - lc.shift(LB)
    r = lc.diff()
    up = (r > 0).astype(float).where(r.notna()).rolling(LB).mean()
    dn = (r < 0).astype(float).where(r.notna()).rolling(LB).mean()
    fip = np.sign(ret252) * (dn - up)
    sig60 = r.rolling(VOL_N).std()
    strength = ret252.abs() / (sig60 * math.sqrt(LB))
    out = pd.DataFrame({"R2": r2.values, "FIP": fip.values, "S": strength.values, "sig": np.sign(ret252).values,
                        "slope_sign": slope_sign.values}, index=df["time"].values)
    return out


def labels_from(feat_reads, smooth_low):
    """feat_reads: (読み日数,) の値。拡張中央値（当日除く・最低12）と比べた滑らかフラグ（1/0/nan）。"""
    s = pd.Series(feat_reads)
    med = s.expanding(min_periods=1).median().shift(1)
    cnt = s.notna().cumsum().shift(1)
    lab = (s < med) if smooth_low else (s > med)
    lab = lab.astype(float).where(s.notna() & med.notna() & (cnt >= MIN_PRIOR))
    return lab.values


def year_diff(year_codes, pnl, lab, nY):
    m = np.isfinite(lab)
    hi = m & (lab == 1); lo = m & (lab == 0)
    sh = np.bincount(year_codes[hi], weights=pnl[hi], minlength=nY); ch = np.bincount(year_codes[hi], minlength=nY)
    sl = np.bincount(year_codes[lo], weights=pnl[lo], minlength=nY); cl = np.bincount(year_codes[lo], minlength=nY)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.where((ch > 0) & (cl > 0), sh / np.maximum(ch, 1) - sl / np.maximum(cl, 1), np.nan)
    return d, ch, cl


def strat_diff(year_codes, pnl, lab, slab, nY):
    """強さの高低それぞれの中で滑らか−非滑らか、2層を等ウェイト平均（両層ある年だけ）。"""
    ds = []
    for v in (0.0, 1.0):
        mm = slab == v
        d, _, _ = year_diff(year_codes, pnl, np.where(mm, lab, np.nan), nY)
        ds.append(d)
    return (ds[0] + ds[1]) / 2


def summarize(d, years_u, y0, y1, ch=None, cl=None):
    m = (years_u >= y0) & (years_u < y1) & np.isfinite(d)
    x = d[m]
    n = len(x)
    out = {"n_years": int(n), "diff_bp_per_month": f(x.mean()) if n else None, "t_year": f(tstat(x)) if n > 1 else None}
    if n > 1:
        se = x.std(ddof=1) / math.sqrt(n); q = T975.get(n - 1, 2.10)
        out["ci95"] = [f(x.mean() - q * se), f(x.mean() + q * se)]
    if ch is not None:
        mm = (years_u >= y0) & (years_u < y1)
        out["n_cells_smooth"] = int(ch[mm].sum()); out["n_cells_rough"] = int(cl[mm].sum())
    return out


def verdict(pre, post):
    dp, tp = pre.get("diff_bp_per_month"), pre.get("t_year")
    dq, tq = post.get("diff_bp_per_month"), post.get("t_year")
    if None in (dp, tp, dq, tq):
        return "未確定（期間の数値が欠ける）"
    if dp > 0 and tp >= 2 and dq > 0 and tq >= 2:
        return "支持"
    if dp < 0 or dq < 0 or (abs(tp) < 2 and abs(tq) < 2):
        return "棄却"
    return "未確定"


def run(args, rng):
    syms, missing = syms_available(SYMS, smoke=args.smoke)
    hl = None if args.smoke else health(syms, kind="D1_fromH1")
    data = {s: load_d1(s, args.smoke, rng) for s in syms}
    gap_rows = {s: int(d["gap"].sum()) for s, d in data.items() if "gap" in d}
    feats = {s: own_features(data[s]) for s in syms}
    idx = pd.DatetimeIndex(sorted(set().union(*[set(d["time"]) for d in data.values()])))
    close = pd.DataFrame({s: data[s].set_index("time")["close"].reindex(idx).ffill() for s in syms})
    valid = pd.DataFrame({s: data[s].set_index("time")["close"].reindex(idx).notna() for s in syms})
    F = {k: pd.DataFrame({s: feats[s][k].reindex(idx).ffill() for s in syms}) for k in ("R2", "FIP", "S", "sig", "slope_sign")}
    for k in F:  # 銘柄のデータ終了後の ffill を消す
        F[k] = F[k].where(valid.cummax() & valid[::-1].cummax()[::-1])
    T0 = LB + VOL_N
    reads = np.array([t for t in range(T0, len(idx) - H) if (t - T0) % H == 0])
    # 建玉と損益
    rows = []
    for s in syms:
        sig = F["sig"][s].values; V = valid[s].values
        pos = np.zeros(len(idx)); cur = 0.0
        rset = set(reads.tolist())
        for t in range(len(idx)):
            if t in rset:
                cur = float(sig[t]) if (V[t] and np.isfinite(sig[t])) else 0.0
            pos[t] = cur if t >= T0 else 0.0
        c = close[s].values
        cb = np.nan_to_num(cost_bp_oneway(s, c))
        p = np.nan_to_num(pnl_bp(pos, np.nan_to_num(c, nan=np.nanmean(c)), cb))
        cs = np.r_[0.0, np.cumsum(p)]
        for k, t in enumerate(reads):
            rows.append((s, k, t, idx[t].year, pos[t], cs[t + H + 1] - cs[t + 1]))
    cells = pd.DataFrame(rows, columns=["sym", "k", "t", "year", "pos", "pnl"])
    for kname in ("R2", "FIP", "S", "slope_sign"):
        cells[kname] = [F[kname][s].values[t] for s, t in zip(cells["sym"], cells["t"])]
    # ラベル（読み日すべての値で拡張中央値を作り、建玉0のセルは後で除く）
    def lab_cells(Fk_dict, kname, smooth_low):
        out = np.full(len(cells), np.nan)
        for s in syms:
            ii = np.where(cells["sym"].values == s)[0]
            vals = Fk_dict[s][cells["t"].values[ii]]
            out[ii] = labels_from(vals, smooth_low)
        return out
    base = {s: {k: F[k][s].values for k in ("R2", "FIP", "S")} for s in syms}
    cells["lab_R2"] = lab_cells({s: base[s]["R2"] for s in syms}, "R2", False)
    cells["lab_FIP"] = lab_cells({s: base[s]["FIP"] for s in syms}, "FIP", True)
    cells["lab_S"] = lab_cells({s: base[s]["S"] for s in syms}, "S", False)
    use = cells[(cells["pos"] != 0) & cells["pnl"].notna()].reset_index(drop=True)
    years_u = np.array(sorted(use["year"].unique())); ymap = {y: i for i, y in enumerate(years_u)}; nY = len(years_u)
    yc = use["year"].map(ymap).values.astype(int); pn = use["pnl"].values.astype(float)
    summary = {}
    for kname in ("R2", "FIP", "S"):
        d, ch, cl = year_diff(yc, pn, use[f"lab_{kname}"].values, nY)
        summary[kname] = {pnm: summarize(d, years_u, y0, y1, ch, cl) for pnm, y0, y1 in PERIODS}
        summary[kname]["by_year"] = {int(y): f(v) for y, v in zip(years_u, d)}
    strat = {}
    for kname in ("R2", "FIP"):
        d = strat_diff(yc, pn, use[f"lab_{kname}"].values, use["lab_S"].values, nY)
        strat[kname] = {pnm: summarize(d, years_u, y0, y1) for pnm, y0, y1 in PERIODS}
    base_pnl = {}
    for pnm, y0, y1 in PERIODS:
        yr = use[(use["year"] >= y0) & (use["year"] < y1)].groupby("year")["pnl"].mean()
        base_pnl[pnm] = {"n_years": int(len(yr)), "mean_cell_bp": f(yr.mean()), "t_year": f(tstat(yr.values)), "n_cells": int(((use["year"] >= y0) & (use["year"] < y1)).sum())}
    corr = {"R2_vs_S": f(spearman(use["R2"], use["S"])), "FIP_vs_S": f(spearman(use["FIP"], use["S"])), "R2_vs_FIP": f(spearman(use["R2"], use["FIP"])),
            "slope_agrees_with_sig_frac": f(float((use["slope_sign"] == use["pos"]).mean())),
            "label_overlap_R2_FIP": f(float((use["lab_R2"] == use["lab_FIP"]).mean())), "label_overlap_R2_S": f(float((use["lab_R2"] == use["lab_S"]).mean()))}
    # 帰無
    spans = {}
    for s in syms:
        fin = np.where(np.isfinite(base[s]["R2"]) & np.isfinite(base[s]["FIP"]))[0]
        spans[s] = (fin.min(), fin.max() + 1)
    null = {v: {k: {p[0]: [] for p in PERIODS} for k in ("R2", "FIP")} for v in ("per_sym", "common")}
    for b in range(args.B):
        for variant in ("per_sym", "common"):
            kc = None
            if variant == "common":
                nmin = min(e - a for a, e in spans.values())
                kc = int(rng.integers(MIN_SHIFT, nmin - MIN_SHIFT + 1))
            sh = {}
            for s in syms:
                a, e = spans[s]
                sh[s] = {}
                kk = kc if kc is not None else int(rng.integers(MIN_SHIFT, (e - a) - MIN_SHIFT + 1))
                for kname in ("R2", "FIP"):
                    x = base[s][kname].copy(); x[a:e] = np.roll(x[a:e], kk); sh[s][kname] = x
            for kname, low in (("R2", False), ("FIP", True)):
                lab = lab_cells({s: sh[s][kname] for s in syms}, kname, low)
                lab_use = lab[((cells["pos"] != 0) & cells["pnl"].notna()).values]
                d, _, _ = year_diff(yc, pn, lab_use, nY)
                for pnm, y0, y1 in PERIODS:
                    m = (years_u >= y0) & (years_u < y1) & np.isfinite(d)
                    null[variant][kname][pnm].append(float(d[m].mean()) if m.any() else np.nan)
        if b % 100 == 0:
            print("null", b, flush=True)
    nullsum = {}
    for variant in null:
        nullsum[variant] = {}
        for kname in ("R2", "FIP"):
            nullsum[variant][kname] = {}
            for pnm, _, _ in PERIODS:
                arr = np.array(null[variant][kname][pnm], float); arr = arr[np.isfinite(arr)]
                obs = summary[kname][pnm]["diff_bp_per_month"]
                z, _ = z_of(obs if obs is not None else np.nan, arr)
                nullsum[variant][kname][pnm] = {"z": f(z), "q025": f(np.quantile(arr, .025)) if len(arr) else None,
                                                "q975": f(np.quantile(arr, .975)) if len(arr) else None, "null_mean": f(arr.mean()) if len(arr) else None, "n": int(len(arr))}
    mv = {k: verdict(summary[k]["pre"], summary[k]["post"]) for k in ("R2", "FIP")}
    sv = {k: verdict(strat[k]["pre"], strat[k]["post"]) for k in ("R2", "FIP")}
    res = {"question": "直前の経路が滑らか（R²高・FIP低）なほど翌21日の TSMOM 純損益は大きいか",
           "settings": {"LB": LB, "H": H, "WIN_R2": WIN, "WIN_FIP": LB, "VOL_N": VOL_N, "MIN_PRIOR": MIN_PRIOR, "MIN_SHIFT": MIN_SHIFT, "B": args.B, "seed": args.seed},
           "missing": missing, "data_health": hl, "gap_rows": gap_rows, "data_last": str(idx[-1]), "n_reads": int(len(reads)),
           "baseline_tsmom_cell": base_pnl, "summary": summary, "strength_stratified": strat, "correlations": corr, "null": nullsum,
           "machine_verdict": mv, "machine_verdict_strength_stratified": sv,
           "multiple_comparisons": "判定は R²・FIP の 2 条件×前後半（両期間一致を要求）。強さ層別・S・2022〜・z は記述。"}
    return res, {"cells": use}


def main():
    args = parse_args(default_B=1000)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    write_result(QID, res, args.smoke, csvs, here=HERE)
    print("machine_verdict:", res["machine_verdict"], "strat:", res["machine_verdict_strength_stratified"])


if __name__ == "__main__":
    main()
