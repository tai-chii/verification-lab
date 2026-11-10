# -*- coding: utf-8 -*-
"""Q702 日本株・米国株の同月季節性（保有月と同じ暦月の過去 1〜5 年の月次リターン平均の上位 10% 買い・下位 10% 売り・1 か月保有）— 無料層での追試（2010-01〜）

【出典】Heston & Sadka 2008 JFE「Seasonality in the Cross-Section of Stock Returns」（1963〜2002・同じ暦月に高い／低いリターンが続く）。
       Heston & Sadka 2010 JFQA「…The International Evidence」（カナダ・日本・欧州 12 か国で季節性の戦略が非季節性より月 1% 超上回る）。Keloharju, Linnainmaa & Nyberg 2016 JF「Return Seasonalities」。
       先行研究チェック 2026-11-10 WebSearch standard「Heston Sadka 2008 seasonality same calendar month returns international replication Japan」: 日本は 2010 年の国際版に含まれるが
       日本単独の数字は見つからない。未確認の点: 2010〜2024-06（公表後）・売買代金上位・コスト後・1〜5 年の平均（原形は 1〜20 年の個別ラグ）。
【仮説】H1: 保有月と同じ暦月の過去 1〜5 年のリターン平均が高い上位 10% 買い・低い下位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】月次リターン R_m＝月末終値の比−1。保有月を m とし、シグナル＝mean(R_{m−12k}, k=1..5)（3 年以上そろえば計算）。判断日 t は m の前の月末なので未来は混ざらない。
       期間は 2005 年開始のデータから 5 年貯めて 2010-01〜（保有月が 2010-01 以降の判断だけ使う）。**前後半の境は 2017-07-01**（期間が短いため・この案だけ。コードで B.SPLIT を上書き）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 2（ラグ 1〜20 年の個別検定〔標本が短い〕、非同月の平均を引く Keloharju 型〔本数が増える〕）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜・封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。
【適格・保有・コスト】(Q576〜Q578 と同じ・土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を importlib で読む)
       判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。
       保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。等金額。上位 10% 買い・下位 10% 売り。
       コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・
       σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の日米 8 本 Q700〜Q707 共通）】支持＝両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ
       2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6%。棄却＝両国とも NW t<1。未確定＝それ以外（片方の国だけ通る場合は「未確定（片方: 国名）」）。
       無料層で落ちた案は有料データで救済しない。支持なら J-Quants Standard での再判定が次段階。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q702.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q702.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_seasonality_q702.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)
B.SPLIT = pd.Timestamp("2017-07-01")          # この案だけ: 期間 2010-01〜が短いので前後半の境を 2017-07-01 にする（B の関数はこのモジュール変数を読む）
START = pd.Timestamp("2010-01-01")                # 保有月の開始

def load_smoke(rng):
    """smoke 用: 2005 年開始・5000 営業日の合成（B.load_px の 2014 年開始 2600 日では 5 年貯められない）。"""
    n, T = 400, 5000; idx = pd.bdate_range("2005-01-03", periods=T)
    r = rng.normal(0.0003, 0.02, (T, n)); c = pd.DataFrame(1000 * np.exp(np.cumsum(r, 0)), idx, [f"S{i}" for i in range(n)])
    v = pd.DataFrame(np.exp(rng.normal(12, 1, (T, n))), idx, c.columns)
    return c, v

def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"

QID = "Q702"; LOOKBACK = 252
MIN_YEARS, MAX_YEARS = 3, 5
def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]
        C, V = load_smoke(rng) if args.smoke else B.load_px(mkt, False, rng)
        R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, LOOKBACK)
        months = [m for m in months if m[1] >= START]                          # 保有の最初の日が 2010-01 以降（≈ 判断日 2009-12-31 から）
        me = B.month_ends(C.index); Cm = C.loc[me]; Cm.index = pd.PeriodIndex(Cm.index, freq="M")
        Rm = Cm.pct_change(fill_method=None)                                   # 月次リターン R_m（月末終値の比−1）・PeriodIndex
        def sig_at(t, el):
            m = pd.Period(t, freq="M") + 1                                    # 保有月
            X = Rm.reindex([m - 12 * k for k in range(1, MAX_YEARS + 1)])[list(el)] if len(el) else Rm.iloc[:0]
            return X.mean(axis=0).where(X.notna().sum(axis=0) >= MIN_YEARS)
        d = B.run_ls(C, R, sig_at, months, cfg["cost"]); st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = B.null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        d0 = B.run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(), note="シグナル=保有月と同じ暦月の過去1〜5年の月次リターン平均(3年以上)。保有月2010-01〜・前後半の境2017-07-01。"), csvs

def main():
    args = B.parse_args("Q702 同月季節性（日本株・米国株）"); rng = np.random.default_rng(args.seed)
    if args.out is None: args.out = os.path.join(HERE, "results")   # 土台は自分のフォルダに書くので、この案の results/ に向ける
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
