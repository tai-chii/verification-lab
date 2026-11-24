# -*- coding: utf-8 -*-
"""Q788 米国株の営業利益÷総資産の高い方買い低い方売りは 2010-07〜2024-06 のコスト後に残るか

事前登録: 事前登録_q788.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 連鎖・追試。
【出典】Ball, Gerakos, Linnainmaa & Nikolaev 2015 JFE 117(2):225-248「Deflating profitability」。Fama & French 2015（RMW。分母は自己資本で別定義・知識から記載・要照合）。 連鎖: 知見「米国の売買代金上位 800 で 2010 年以降は価格を分母にする比率と資産成長がコスト前から残らず、会計の量どうしの比であるアクルーアルだけが残る」（Q696〜Q699・封印 Q714）→ 価格を使わない会計比率の族 10 本（Q787〜Q796）を同じ土台で測る。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「operating profitability anomaly Ball Gerakos Linnainmaa Nikolaev post-publication evidence」ほか 1 回。Ball ほか 2015 JFE 117(2)・同 2016 JFE 121(1):28-45（現金ベースにすると発生高アノマリーを吸収）、Robeco の資料（2010〜2019 はファクター不振・運用会社の資料）。CFA Institute のブログ（RMW は一貫してプラス）は根拠にしない。未確認の点（追試）: 2015 年以降の米国で営業利益÷総資産を直接測った査読研究は見つからない。
【仮説】H1（Ball ほか）: 営業利益÷総資産の高い上位 10% 買い・低い下位 10% 売りは、コスト後に NW t≥2.58・前後半とも年単位 t≥2。H0: NW t<1。
【定義】営業利益＝年次の OperatingIncomeLoss。総資産＝同じ会計年度の期末。シグナル＝営業利益÷総資産。
【多重比較・捨てた案】主 1 本（米国のみ）。族 10 本の Bonferroni を通過の線に織り込み済み。捨てた案 1（Ball らの定義＝売上 − 売上原価 − 販管費＋研究開発費。販管費と研究開発費のタグを取っていない）。
【データ・適格・保有・コスト】データ: `作業層/大容量/sec/facts.parquet`（EDGAR XBRL companyfacts・861 銘柄・filed 2009-04〜）を判断時点で読む（`us-sec-value-q696/sec_pit.py`。判断日 t には filed ≤ t の行だけ）＋ `作業層/大容量/equities_free/us_daily.parquet`（調整済み終値・出来高。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 財務の読み方（第4弾の SEC 10 本共通・`_eq4_common/eq4.py` の `Fin`）: 年次だけ使う（fp==FY。フローは期間 330〜400 日、ストックは 10-K の期末）。比を作る 2 つの値は end が 10 日以内で一致するものだけ（会計年度のずれた組を作らない）。1 年前の値＝今の年次の end より 300〜430 日前の end のうち最新（その end の最初に出た値＝当初の報告）。 第4弾で足したタグ: 営業利益 `OperatingIncomeLoss`（718 銘柄）・粗利益 `GrossProfit`（451）・売上原価 `CostOfGoodsAndServicesSold`（463）→`CostOfRevenue`（232）・負債 `Liabilities`（665）。銘柄数は 2026-11-24 に facts.parquet のタグを数えただけの値（財務の値とリターンは見ていない）。 適格・保有・コスト（Q696〜Q699 と同じ・`sec_pit.run_us` をそのまま呼ぶ）: 判断日＝月末。株価≥5 ドル・売買代金 20 日平均の上位 800・履歴 252 日の 9 割以上 ∧ その案に要る財務がそろう。判断日の最低銘柄数 200。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 期間 2010-07-01〜2024-06-30。前後半の境 2017-07-01。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転・銘柄数。副（合否に使わない）: コスト 0 の平均と t、Q698（アクルーアル）の日次 L−S との相関と、Q698 に回帰した残りの平均・NW t（独立の源かどうかの記述・Q710 の教訓）。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第4弾の米国 SEC 10 本 Q787〜Q796 共通・変更禁止）。日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2.58（片側 p<0.005＝族 10 本の Bonferroni）かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。
【限り】OperatingIncomeLoss を出さない銘柄（金融の多く）は落ちる。企業が決めた営業利益で、Ball らの定義とは違う。現金ベース（Q710・営業 CF÷総資産）は棄却済みで、その発生主義の側を測る形。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q788.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q788.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_operating_profit_q788.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q788"
NOTE = "合図＝年次の営業利益（OperatingIncomeLoss）÷総資産。同じ会計年度。"


def make_signal(fin, mes, C):
    return dict(main=eq4.ratio(fin.val("oi"), fin.val("a")))


def run(args, rng):
    return eq4.run_sec(QID, args, rng, make_signal, note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q788 米国株の営業利益÷総資産の高い方買い低い方売り", run, HERE)
