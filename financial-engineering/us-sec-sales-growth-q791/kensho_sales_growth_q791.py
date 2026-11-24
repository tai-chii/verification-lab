# -*- coding: utf-8 -*-
"""Q791 米国株の売上成長（年次売上の前年比）の低い方買い高い方売りは 2010-07〜2024-06 のコスト後に残るか

事前登録: 事前登録_q791.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 連鎖・条件の穴。
【出典】Lakonishok, Shleifer & Vishny 1994 JF 49(5):1541-78「Contrarian Investment, Extrapolation, and Risk」。 連鎖: 知見「米国の売買代金上位 800 で 2010 年以降は価格を分母にする比率と資産成長がコスト前から残らず、会計の量どうしの比であるアクルーアルだけが残る」（Q696〜Q699・封印 Q714）→ 価格を使わない会計比率の族 10 本（Q787〜Q796）を同じ土台で測る。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「sales growth anomaly Lakonishok Shleifer Vishny post-publication replication」ほか 1 回。Dechow–Sloan 1997 JFE（過去の成長の単純な外挿を示す体系的な証拠はない）、Hou–Xue–Zhang「Replicating Anomalies」（5 年売上成長は有意でない側）、Chen–Zimmermann 2022 Critical Finance Review 11(2)。未確認の点（条件の穴）: 原論文は 5 年の売上成長順位。XBRL は 2009 年からで 5 年分が取れないので 1 年成長に置き換える＝原論文とは別条件。
【仮説】H1（Lakonishok ほか）: 売上成長の低い下位 10% 買い・高い上位 10% 売りは、コスト後に NW t≥2.58・前後半とも年単位 t≥2。H0: NW t<1。
【定義】売上成長＝年次売上（Revenues→RevenueFromContractWithCustomerExcludingAssessedTax→SalesRevenueNet）÷ 1 年前の年次売上 − 1（1 年前の売上が正のものだけ）。シグナル＝−売上成長。
【多重比較・捨てた案】主 1 本（米国のみ）。族 10 本の Bonferroni を通過の線に織り込み済み。捨てた案 1（原論文の 5 年の売上成長順位。XBRL が 2009 年からで 2010-07 に 5 年分そろわない）。
【データ・適格・保有・コスト】データ: `作業層/大容量/sec/facts.parquet`（EDGAR XBRL companyfacts・861 銘柄・filed 2009-04〜）を判断時点で読む（`us-sec-value-q696/sec_pit.py`。判断日 t には filed ≤ t の行だけ）＋ `作業層/大容量/equities_free/us_daily.parquet`（調整済み終値・出来高。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 財務の読み方（第4弾の SEC 10 本共通・`_eq4_common/eq4.py` の `Fin`）: 年次だけ使う（fp==FY。フローは期間 330〜400 日、ストックは 10-K の期末）。比を作る 2 つの値は end が 10 日以内で一致するものだけ（会計年度のずれた組を作らない）。1 年前の値＝今の年次の end より 300〜430 日前の end のうち最新（その end の最初に出た値＝当初の報告）。 第4弾で足したタグ: 営業利益 `OperatingIncomeLoss`（718 銘柄）・粗利益 `GrossProfit`（451）・売上原価 `CostOfGoodsAndServicesSold`（463）→`CostOfRevenue`（232）・負債 `Liabilities`（665）。銘柄数は 2026-11-24 に facts.parquet のタグを数えただけの値（財務の値とリターンは見ていない）。 適格・保有・コスト（Q696〜Q699 と同じ・`sec_pit.run_us` をそのまま呼ぶ）: 判断日＝月末。株価≥5 ドル・売買代金 20 日平均の上位 800・履歴 252 日の 9 割以上 ∧ その案に要る財務がそろう。判断日の最低銘柄数 200。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 期間 2010-07-01〜2024-06-30。前後半の境 2017-07-01。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転・銘柄数。副（合否に使わない）: コスト 0 の平均と t、Q698（アクルーアル）の日次 L−S との相関と、Q698 に回帰した残りの平均・NW t（独立の源かどうかの記述・Q710 の教訓）。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第4弾の米国 SEC 10 本 Q787〜Q796 共通・変更禁止）。日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2.58（片側 p<0.005＝族 10 本の Bonferroni）かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。
【限り】原論文（5 年）と違う 1 年成長。売上タグの切り替わり（2018 年の新基準）は「end の新しいものを優先」で吸収するが、タグをまたぐ前年比に定義の差が混ざりうる。資産成長（Q697・コスト後ほぼゼロ）と似た源の可能性。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q791.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q791.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_sales_growth_q791.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q791"
NOTE = "合図＝−（年次売上 ÷ 1 年前の年次売上 − 1）。売上成長の低い方を買う。"


def make_signal(fin, mes, C):
    g = eq4.ratio(fin.val("rev", 0, ref=None), fin.val("rev", 1, ref=None)) - 1
    return dict(main=-g)


def run(args, rng):
    return eq4.run_sec(QID, args, rng, make_signal, note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q791 米国株の売上成長（年次売上の前年比）の低い方買い高い方売り", run, HERE)
