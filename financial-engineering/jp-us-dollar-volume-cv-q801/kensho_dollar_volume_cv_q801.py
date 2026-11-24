# -*- coding: utf-8 -*-
"""Q801 日本株・米国株の売買代金の変動係数（252 日の日次売買代金の標準偏差÷平均）の低い方買い高い方売りはコスト後 2006〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q801.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 追試・移植。
【出典】Chordia, Subrahmanyam & Anshuman 2001 JFE 59(1):3-32「Trading activity and expected stock returns」。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「Chordia Subrahmanyam Anshuman 2001 volatility of trading activity expected returns replication」ほか 1 回。原論文のみ（米国で売買代金・回転率のぶれが大きい銘柄ほど低リターン）。Hou–Xue–Zhang 2020 が売買摩擦系の大半は再現しないと報告（知識から記載・要照合）。未確認の点（追試・移植）: 発表後の標本での再現も日本での再現も見つからない。
【仮説】H1（Chordia ほか）: 売買代金の変動係数の低い下位 10% 買い・高い上位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】売買代金＝終値×出来高（正の日だけ）。変動係数 CV＝直近 252 営業日（200 日以上）の日次売買代金の標準偏差÷平均。シグナル＝−CV。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（原論文の月次売買代金 36 か月の変動係数。履歴が 3 年要り標本が減る）。
【データ・適格・保有・コスト】データ: `作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 適格・保有・コスト（Q576〜Q578・第3弾と同じ。土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を `_eq4_common/eq4.py` 経由で読む）: 判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】原論文は月次 36 か月・回転率も使う（株数が日本に無いので売買代金だけ）。日次の変動係数は決算やニュースの日の出来高の跳びを強く拾う。回転は小さい見込み（知見「回転が小さく宇宙の中に散らばりがある信号だけ残る」に合う形）。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q801.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q801.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_dollar_volume_cv_q801.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q801"
NOTE = "合図＝−（直近 252 日の日次売買代金の標準偏差÷平均）。"
LOOKBACK = 252; MINDAYS = 200


def make_sig(mkt, C, V, R, months, args):
    DV = C * V; DV = DV.where(DV > 0)
    cv = DV.rolling(LOOKBACK, min_periods=MINDAYS).std() / DV.rolling(LOOKBACK, min_periods=MINDAYS).mean()
    return eq4.frame_sig(-cv)


def run(args, rng):
    return eq4.run_pv(QID, args, rng, make_sig, LOOKBACK, note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q801 日本株・米国株の売買代金の変動係数（252 日の日次売買代金の標準偏差÷平均）の低い方買い高い方売り", run, HERE)
