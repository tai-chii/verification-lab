# -*- coding: utf-8 -*-
"""Q699 米国株の純発行（分割補正後の発行株数の前年比）は買い戻し側を買い増資側を売ると 2010-07〜2024-06 のコスト後に残るか

【出典】Pontiff & Woodgate 2008 JF。Fama & French 2008 JF「Dissecting Anomalies」。McLean, Pontiff & Watanabe 2009 JFE（41 か国）。Lobe & Walkshäusl 2014。
       先行研究チェック 2026-11-10 WebSearch standard: 上の 4 本に加え英国・チリ・豪州の追試。未確認の点: 2010-07〜2024-06・SEC の株数（分割補正）・売買代金上位 800・コスト後での独立の追試は見つからない。
【仮説】H1: 純発行が低い＝買い戻し側の下位 10% 買い・高い＝増資側の上位 10% 売りは、コスト後に NW t≥2・前後半とも年単位 t≥2。H0: NW t<1。
【データ】`作業層/大容量/sec/facts.parquet`（EDGAR XBRL companyfacts・861 銘柄・filed 2009-04〜）のポイントインタイム財務（`us-sec-value-q696/sec_pit.py`）＋
       `作業層/大容量/equities_free/us_daily.parquet`（調整済み終値・出来高・封印 2024-07-01 以降は読まない）。生存バイアスあり。
【定義】株数系列（CommonStockSharesOutstanding → Weighted…Diluted）を分割補正（共通の規則）したあと、純発行＝log(株数(t)) − log(株数(t−1 年))（1 年前＝現在の値の end より 300〜430 日前の end の値）。シグナル＝−純発行。
       分割の判定を外れた跳び（比 1.4 超で整数比に合わない）は純発行としてそのまま数える。
       SEC 財務の読み方（Q696〜Q699 共通）: 判断日 t（月末）には filed ≤ t の行だけ。各タグで end 最大（同じ end なら filed 最新）。フロー＝fp==FY かつ期間 330〜400 日、
       ストック＝end 最大（10-Q 含む）。分割は株数の連続比が ≥1.4（または ≤1/1.4）で整数比 {1.5,2,3,4,5,6,7,8,10,20} の ±5% 以内なら補正（F）。
       適格＝株価≥5 ドル・売買代金 20 日平均の上位 800・履歴 252 日の 9 割以上 ∧ その案に要る財務がそろう。判断日の最低銘柄数 200。期間 2010-07-01〜2024-06-30。前後半の境 2017-07-01。
       上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の米国 SEC 4 本 Q696〜Q699 共通）】日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ
       帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。
【多重比較】主 1 本（米国のみ）。
【捨てた案の数】1（複合発行〔配当・分割を含む Daniel–Titman 2006 の形。配当データが無い〕）。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q699.json の per_market.us の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_us_q699.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_net_issuance_q699.py（lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)
_sp = importlib.util.spec_from_file_location("sec_pit", os.path.join(HERE, "..", "us-sec-value-q696", "sec_pit.py"))
P = importlib.util.module_from_spec(_sp); sys.modules["sec_pit"] = P; _sp.loader.exec_module(P)

QID = "Q699"


def verdict_us(per):
    """事前固定（第3弾 Q696〜Q699 共通・変更禁止）。日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。"""
    r = per["us"]; r["p_holm"] = r["p_one"]
    if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["maxdd_s025"] > -0.06: return "米国で通過（日本の追試待ち）"
    if r["t_nw"] < 1: return "棄却"
    return "未確定"


def make_signal(f, mes, C):
    sh, she, Fe, ev, sf = P.shares_at(f, mes)
    sh0, she0 = P.prior_year(sf, P.TAG_SHARES, mes, she, annual=False, with_end=True)
    Fe0 = P.factor_at_end(ev, she0)
    s1 = (sh * Fe).where(sh > 0); s0 = (sh0 * Fe0).where(sh0 > 0)       # 観測日の分割補正（今の単位に揃える）
    iss = np.log(s1) - np.log(s0)
    return dict(main=P.frame_sig(-iss), subs={}, diag=dict(n_split_events=int(len(ev)), n_tickers=int(f["ticker"].nunique())))


def run(args, rng):
    args.markets = "us"
    return P.run_us(B, args, rng, QID, make_signal, verdict_us, note="Q699 純発行（負号）。")


def main():
    args = B.parse_args("Q699 米国株の純発行"); args.markets = "us"; args.out = args.out or os.path.join(HERE, "results"); rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)


if __name__ == "__main__": main()
