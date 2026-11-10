# -*- coding: utf-8 -*-
"""Q703 日本株・米国株の Amihud 非流動性プレミアム（|r|÷売買代金の 252 日平均・σ60 の 3 分位内の横断順位の上位 10% 買い・下位 10% 売り・1 か月保有）— 無料層での追試

【出典】Amihud 2002 JFM「Illiquidity and Stock Returns」。Amihud, Hameed, Kang & Zhang 2015 JFE「The Illiquidity Premium: International Evidence」（45 か国・ボラ 3 分位内の並べ替え・月 0.85%）。
       Li, Sun & Wang 2014 EFM（日本 1975〜2006 で流動性は価格づけされる）。
       先行研究チェック 2026-11-10 WebSearch standard「Amihud illiquidity premium international evidence Japan stocks replication」: 上の 3 本と 2019 の NTU Management Review
       （1990〜2015・アジア太平洋 1.05%/月）。未確認の点: 2015 年設計（ボラ 3 分位内）を日本の 2006〜2024-06・売買代金上位 1,000・コスト後に当てた結果は見つからない。
       注意: 売買代金上位 1,000 に絞るので「非流動」は相対的なもの。片道コストは一律なので実際の非流動株のコストを過小に見積もる（限り）。
【仮説】H1: ILLIQ の高い上位 10% 買い・低い下位 10% 売り（σ60 の 3 分位内で並べ替えて合算）は、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1（流動性の高い宇宙では消える）。
【定義】ILLIQ(t)＝mean over d∈[t−251, t] of |r_d| ÷ (C_d × V_d)（売買代金が 0 の日は除く・有効日 200 以上）。σ60＝60 日の日次リターン標準偏差。
       各判断日に σ60 で 3 分位に分け、分位内で ILLIQ の横断順位（0〜1）を取り、それをシグナルにする（上位 10% 買い・下位 10% 売り）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（ボラ統制なしの素の ILLIQ〔2015 年設計と違う〕）。
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
【委託の確かめ方】results/result_q703.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q703.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_amihud_q703.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"

QID = "Q703"; LOOKBACK = 252

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]
        C, V = B.load_px(mkt, args.smoke, rng)
        R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, LOOKBACK)
        dv = (C * V).where((C * V) > 0)                                       # 売買代金 0 の日は除く
        ILLIQ = (R.abs() / dv).rolling(252, min_periods=200).mean()           # 252 日平均（有効日 200 以上）
        SIG60 = R.rolling(60, min_periods=45).std()                           # 60 日 σ（45 日以上で計算＝実装の欠損基準）
        def sig_at(t, el):
            il, sg = ILLIQ.loc[t].reindex(el), SIG60.loc[t].reindex(el)
            ok = il.notna() & sg.notna() & (il > 0)
            il, sg = il[ok], sg[ok]
            if len(il) < 30: return pd.Series(dtype=float)
            terc = pd.qcut(sg.rank(method="first"), 3, labels=False)         # σ60 の 3 分位
            return il.groupby(terc).rank(pct=True)                           # 分位内の ILLIQ 横断順位 0〜1
        d = B.run_ls(C, R, sig_at, months, cfg["cost"]); st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = B.null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        d0 = B.run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(), note="シグナル=σ60の3分位内のILLIQ(252日平均)横断順位。"), csvs

def main():
    args = B.parse_args("Q703 Amihud 非流動性プレミアム（日本株・米国株）"); rng = np.random.default_rng(args.seed)
    if args.out is None: args.out = os.path.join(HERE, "results")   # 土台は自分のフォルダに書くので、この案の results/ に向ける
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
