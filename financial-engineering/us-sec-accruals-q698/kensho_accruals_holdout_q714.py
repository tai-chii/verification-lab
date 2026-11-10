# -*- coding: utf-8 -*-
"""Q714 封印ホールドアウト判定（1 回）: Q698 アクルーアル（米国・同一定義）は 2024-07〜2026-06 の 24 か月でもコスト後に残るか

【出典】Q698（`kensho_accruals_q698.py`・事前登録 2026-11-10 15:05・開発 2010-08〜2024-06: コスト後 +2.33 bp/日・NW t 2.62・判定 未確定）。事後の判断 `自動実行/ログ/夜間_20261109/事後の判断_第3弾_1110.md`。
       事前登録 `事前登録_q714.md`（下書き 18:25・taichi「A 開ける」19:45 で登録・結果を見る前に固定）。
【仮説】H1: アクルーアルの低い下位 10% 買い・高い上位 10% 売り（Q698 と同一定義）は、2024-07〜2026-06 のコスト後平均が開発の半分（+1.16 bp/日）以上。H0: 平均 ≤ 0。
【データ】`作業層/大容量/equities_free/us_daily.parquet`（2026-10-27 まで）・`作業層/大容量/sec/facts.parquet`（filed 2026-10-30 まで）。
       **封印の例外**: 2024-07〜2026-06 を読む（taichi 承認・この 1 回・Q714／Q715 の 2 本だけ）。開けた後の新しい封印は 2026-07-01。
【定義】Q698 と同一・1 字も変えない: シグナル・SEC の読み方・適格（株価≥5 ドル・売買代金上位 800・履歴 252 日の 9 割・財務あり・最低 200）・上下 10% 等金額・月末判断・翌営業日終値から次の月末翌営業日終値・片道 5 bp×片側回転・±50% 欠損。
       実装は `kensho_accruals_q698.py` の `make_signal` と土台 `kensho_high_volume_premium_q578.py` の `build_months`／`run_ls` をそのまま呼ぶ。期間だけ呼ぶ側で絞る:
       保有日が 2024-07-01〜2026-07-01（判断日 2024-06-28〜2026-05-29・最後の保有日は 2026-06 月末の翌営業日 2026-07-01）。土台の `SEAL` 定数はファイルを変えず、このスクリプトの中で `B.SEAL` を上書きして読む範囲を伸ばす。
       開発期間（〜2024-06）の値は読み直さない（開発の値は `results/result_q698.json` のまま。β 中立の記述だけ `results/daily_us_q698.csv` の既出の系列を β の推定に使う）。
【測るもの】主: 日次 L−S のコスト後平均（bp/日）。副（記述・合否に使わない）: NW t（ラグ 21）・年単位 t・コスト前平均・回転・市場 α と β・年率シャープ・σ0.25% 換算 DD・銘柄数・月ごとの L−S・2024H2／2025／2026H1 の平均。
       記述（事後の読み替えに当たるので合否に使わない・同時に 1 回だけ）: (a) コスト片道 10 bp、(b) サイズ中立版＝売買代金 20 日平均の 3 分位の中で順位を取って合算、(c) β 中立版＝過去 504 日の β（t−1 まで）で市場を引いた h。
【帰無】走らせない（24 か月では月の循環シフト k∈[13, N−13] が成り立たない・事前登録）。B=0・記述もしない。
【判定（事前固定・変更禁止・1 回だけ）】コスト後平均 ≥ +1.16 bp/日（開発 +2.33 の半分）→ 米国で通過（日本の追試待ち）。≤ 0 → 棄却。0 < 平均 < +1.16 → 未確定（打ち止め）。t・z は合否に使わない（24 か月の期待 t ≈ 0.96・検出力が無い）。
【多重比較】同時に開ける 2 本（Q714・Q715）で Holm m=2 を記述として出す（記録側で計算）。合否は閾値のみ。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は知識の中だが、閾値は結果を見る前に固定。
【委託の確かめ方】results/result_q714.json の per_market.us.mean_bp（主）・first_day ≥ 2024-07-01・n_days 480〜520・turn_mean（開発 0.18 と同じ桁）・verdict。daily_us_q714.csv の最初の日が 2024-07-01 以降（封印前を読んでいない証拠）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_accruals_holdout_q714.py（本番 1 回・帰無なしなので数分）。--smoke は合成データで経路確認のみ（合成の日付を 2026-07-01 終わりにずらす）。
"""
import importlib.util, json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_sq = importlib.util.spec_from_file_location("q698", os.path.join(HERE, "kensho_accruals_q698.py"))
Q = importlib.util.module_from_spec(_sq); _sq.loader.exec_module(Q)
B, P = Q.B, Q.P                                         # 土台（Q578）と SEC の読み込み（Q696）。Q698 が読んだものをそのまま使う

QID = "Q714"
START, END = pd.Timestamp("2024-07-01"), pd.Timestamp("2026-07-01")   # 保有日の範囲（END＝2026-06 月末の翌営業日・最後の保有日）
THRESH_BP = 1.16                                                       # 開発 +2.33 bp/日 の半分（事前登録・変更禁止）


def verdict_holdout(per):
    """事前固定（Q714・変更禁止・1 回だけ）。コスト後平均 ≥ +1.16 bp/日（開発 +2.33 の半分）→ 米国で通過（日本の追試待ち）。≤ 0 → 棄却。0 < 平均 < +1.16 → 未確定（打ち止め）。t・z は合否に使わない。"""
    m = per["us"]["mean_bp"]
    if m >= THRESH_BP: return "米国で通過（日本の追試待ち）"
    if m <= 0: return "棄却"
    return "未確定（打ち止め）"


def _desc(d, B_):
    return dict(mean_bp=1e4 * d["ls"].mean(), t_nw=B_.nw_t(d["ls"]), n_days=int(d["ls"].notna().sum()),
                turn_mean=float(d.groupby(d.index.to_period("M"))["turn"].first().mean()) if len(d) else None)


def run(args, rng):
    B.SPLIT = P.SPLIT_BOUNDARY; B.MIN_NAMES = P.MIN_NAMES_SEC   # Q698 の run_us と同じ上書き
    B.SEAL = END + pd.Timedelta(days=1)                        # 封印の例外（この 1 回）。load_px は date < SEAL を読むので END まで
    cfg = B.CFG["us"]
    C, V = B.load_px("us", args.smoke, rng)
    if args.smoke:                                             # 合成データ（2014 年始まり）の日付を 2026-07-01 終わりにずらして経路を通す
        idx = pd.bdate_range(end=END, periods=len(C)); C.index = idx; V.index = idx
    R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    months_all = B.build_months(C, V, cfg, 252)
    months = [m for m in months_all if m[1] >= START and m[2] <= END]
    mes = [m[0] for m in months]
    f = P.load_facts(args.smoke, rng)
    sig = Q.make_signal(f, mes, C); sig_at = sig["main"]
    d = B.run_ls(C, R, sig_at, months, cfg["cost"])
    st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
    st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()) if len(d) else None
    st["n_months"] = int(d.index.to_period("M").nunique()); st["first_day"] = str(d.index.min().date()) if len(d) else None
    st["last_day"] = str(d.index.max().date()) if len(d) else None; st["names_mean"] = float(d["n"].mean()) if len(d) else None
    st["null"] = dict(B=0, z=None, p=None, note="24 か月では月の循環シフト（k∈[13, N−13]）が成り立たないので走らせない（事前登録）")
    d0 = B.run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
    st["se_bp"] = 1e4 * d["ls"].std() / np.sqrt(len(d)) if len(d) else None          # 単純な標準誤差（記述）
    per = {"us": st}
    # --- 記述（合否に使わない・次の設計の材料）---
    sub = {}
    sub["cost10bp"] = _desc(B.run_ls(C, R, sig_at, months, 0.0010), B)
    adv = (C * V).rolling(20, min_periods=15).mean()
    def sig_size(t, el):                                       # サイズ中立: 売買代金 20 日平均の 3 分位の中で順位
        s = sig_at(t, el).dropna(); a = adv.loc[t].reindex(s.index); ok = a.notna(); s, a = s[ok], a[ok]
        if len(s) < 30: return pd.Series(dtype=float)
        terc = pd.qcut(a.rank(method="first"), 3, labels=False)
        return s.groupby(terc).rank(pct=True)
    sub["size_neutral"] = _desc(B.run_ls(C, R, sig_size, months, cfg["cost"]), B)
    dev_csv = os.path.join(HERE, "results", "daily_us_q698.csv")
    if len(d) and os.path.exists(dev_csv) and not args.smoke:  # β 中立: 過去 504 日の β（t−1 まで）。開発の既出の日次系列を β の推定に使う
        dev = pd.read_csv(dev_csv, index_col=0, parse_dates=True)[["ls", "mkt"]]
        full = pd.concat([dev[dev.index < d.index.min()], d[["ls", "mkt"]]]).sort_index()
        full = full.groupby(level=0).mean()                    # 月の境の日は run_ls が 2 回数える（前月の最終日＝当月の初日）ので、β の推定では日ごとに 1 行にする（2026-11-10 本番 1 回目で重複ラベルのエラー → 記述部分だけ直した・主判定の定義は不変）
        beta = (full["ls"].rolling(504, min_periods=252).cov(full["mkt"]) / full["mkt"].rolling(504, min_periods=252).var()).shift(1)
        bh = beta.reindex(d.index); h = (d["ls"] - bh * d["mkt"]).dropna()
        sub["beta_neutral"] = dict(mean_bp=1e4 * h.mean(), t_nw=B.nw_t(h), n_days=int(len(h)), beta_mean=float(bh.mean()))
    monthly = (d["ls"].groupby(d.index.to_period("M")).mean() * 1e4) if len(d) else pd.Series(dtype=float)
    def _per(lo, hi):
        x = d["ls"][(d.index >= lo) & (d.index < hi)]; return dict(mean_bp=1e4 * x.mean(), n_days=int(len(x))) if len(x) else None
    period = {"2024H2": _per("2024-07-01", "2025-01-01"), "2025": _per("2025-01-01", "2026-01-01"), "2026H1": _per("2026-01-01", "2026-07-02")}
    res = dict(qid=QID, per_market=per, verdict=verdict_holdout(per), rule=verdict_holdout.__doc__.strip(),
               note="Q698 と同一定義・封印 2024-07〜2026-06 を 1 回だけ読んだ（taichi 承認 2026-11-10）。帰無なし。閾値 +1.16 bp/日＝開発 +2.33 の半分。",
               dev=dict(qid="Q698", mean_bp=2.328, t_nw=2.624, threshold_bp=THRESH_BP), seal=dict(opened="2024-07-01〜2026-07-01", new_seal="2026-07-01"),
               sub=sub, monthly_bp={str(k): float(v) for k, v in monthly.items()}, period_bp=period, diag=sig.get("diag", {}))
    return res, {"daily_us": d}


def main():
    args = B.parse_args("Q714 封印ホールドアウト判定（Q698 アクルーアル・米国）"); args.markets = "us"; args.B = 0
    args.out = args.out or os.path.join(HERE, "results"); rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)


if __name__ == "__main__": main()
