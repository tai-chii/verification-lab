# -*- coding: utf-8 -*-
"""Q802 日本株・米国株の相対下方ベータ（市場が平均より下の日のベータ − 通常のベータ・252 日）の高い方買い低い方売りはコスト後 2006〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q802.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 条件の穴。
【出典】Ang, Chen & Xing 2006「Downside risk」（NBER WP 11824 を検索で確認。RFS は知識から記載・要照合）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「downside beta Ang Chen Xing replication Atilgan downside beta equity returns around the world」ほか 1 回。Atilgan–Bali–Demirtas–Gunaydin 2018 Journal of Portfolio Management（51 か国で下方ベータは将来リターンを説明しない・米国でも NYSE の等金額加重でしか出ない）、日本の 2010 年の短報（『行動経済学』3 巻・要旨のみ・著者未確認）。未確認の点（条件の穴）: 相対下方ベータ（下方 − 通常）に絞った結果と日本単独の数字は確認できない。
【仮説】H1（Ang ほか）: 相対下方ベータの高い上位 10% 買い・低い下位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0（Atilgan ほか）: 両国とも NW t<1。事前の見立ては H0 寄り。
【定義】市場 m＝その日に値がある全銘柄の日次リターンの等金額平均。ベータ＝直近 252 営業日（200 日以上）の共分散÷分散。下方ベータ＝同じ窓のうち m<0 の日だけ（80 日以上）で同じ計算。シグナル＝下方ベータ − ベータ。副（合否に使わない）: 下方ベータそのもの。題の「市場が平均より下の日」は実装では「m<0 の日」（下の捨てた案を参照）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（市場が窓の平均より下の日で切る原論文の定義。窓ごとに平均が変わり実装が重い。0 で切る版は原論文の頑健性にある＝知識から記載・要照合）。
【データ・適格・保有・コスト】データ: `作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 適格・保有・コスト（Q576〜Q578・第3弾と同じ。土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を `_eq4_common/eq4.py` 経由で読む）: 判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t、下方ベータそのものの L−S。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】市場は全銘柄の等金額平均（時価加重の指数ではない）。BAB（Q708・未確定）と低ボラ（Q545・Q596）の近縁で、差を取ることで水準のベータの効果を除く設計。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q802.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q802.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_downside_beta_q802.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q802"
NOTE = "合図＝下方ベータ（市場<0 の日だけ）− ベータ。窓 252 日。市場＝全銘柄の等金額平均。"
LOOKBACK = 252; MINOBS = 200; MINDOWN = 80


def make_sig(mkt, C, V, R, months, args):
    m = eq4.market_ret(R); mes = [x[0] for x in months]
    b_all = eq4.beta_from(eq4.roll_moments(R, m, None, LOOKBACK, at=mes), MINOBS)
    b_dn = eq4.beta_from(eq4.roll_moments(R, m, (m < 0).values, LOOKBACK, at=mes), MINDOWN)   # 市場<0 の日だけ
    return dict(main=eq4.frame_sig(b_dn - b_all), subs={"downside_beta_level": eq4.frame_sig(b_dn)})


def run(args, rng):
    return eq4.run_pv(QID, args, rng, make_sig, LOOKBACK, note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q802 日本株・米国株の相対下方ベータ（市場が平均より下の日のベータ − 通常のベータ・252 日）の高い方買い低い方売り", run, HERE)
