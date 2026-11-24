# -*- coding: utf-8 -*-
"""Q800 日本株・米国株の横断モメンタム（Q563 の日次 L−S）を市場の過去 24 か月リターンが負の月に休むと、コスト後 2008〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q800.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 追試。
【出典】Cooper, Gutierrez & Hameed 2004「Market states and momentum」・Daniel & Moskowitz 2016（どちらも引用経由・誌名は知識から記載・要照合）。Hanauer 2014 International Review of Finance 14(1):141-160（日本）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「market states and momentum Cooper Gutierrez Hameed Japan international evidence」ほか 1 回。Hanauer 2014（日本 1986〜2008: 市場が同じ向きに続いた後はプラス・向きが変わった後はマイナスで、転換が米国より多いことが弱さの原因）、Goyal–Jegadeesh–Subrahmanyam 2025、Avramov–Cheng–Hameed（WP・流動性の高い状態の後は日本でも利益）。未確認の点（追試）: Hanauer の標本は 2008 年まで。2009〜2024-06 とコスト後は未確認。
【仮説】H1（Cooper ほか）: 市場の過去 24 か月リターンが負の月にモメンタムを休むと、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】元の系列＝Q799 と同じ Q563 の日次 ls と mkt（適格銘柄の等金額平均）。月ごとの状態＝その月の最初の日より前の直近 504 営業日の mkt の累積（対数の和）が 0 以上なら持つ（w＝1）・負なら休む（w＝0）。504 日そろわない月は入れない。休む月は損益 0。休みに入る月の初日に手仕舞い 2×片道コスト、入り直す月の初日に建て直しの全額（元の系列が引いた回転分に 2×片道コスト×(1−回転) を足す）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 2（36 か月＝原論文の主設定。履歴が 1 年減る／12 か月）。24 か月は原論文の頑健性の設定の 1 つで、事前に 1 本に固定。
【データ・適格・保有・コスト】データ: `jp-us-xs-momentum-q563/results/daily_{jp,us}_q563.csv`（Q563 の本番の結果。列 ls＝コスト後の日次 L−S・mkt＝適格銘柄の等金額平均・turn＝回転。封印 2024-07-01 以降の行は読まない）。元の価格データは読み直さない。 Q563 の適格・保有・コスト（参考）: 判断日＝月末・株価≥100 円（US 5 ドル）・売買代金上位 1,000（US 800）・12-1 か月リターンの上位 10% 買い・下位 10% 売り・等金額・片道 JP 10 bp／US 5 bp × 片側回転。 月の区切り: 土台の保有（月の最初の営業日〜翌月の最初の営業日）ごとのブロック。重みは「その月の最初の日より前」の情報だけで決める。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】重みを掛けた後の日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD。副（合否に使わない）: 重みを掛ける前の同じ月の成績・重みの平均と最小最大・休んだ月の割合。
【帰無】月ごとの重みの列の循環シフト（k∈[13, N−13]・B=200）。重みの分布は同じで、どの月に掛けるかだけを壊す。平均どうしで比べる。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】市場は適格銘柄の等金額平均（指数ではない）。休む月が多いと実質の標本が減る（share_months_off を出す）。Q563 の結果ファイルが無いと本番は動かない。smoke は合成データの市場が上がり続けて休む月が出ないので、市場の平均を引いて経路だけ確かめる（本番は引かない）。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q800.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q800.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_market_state_momentum_q800.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q800"
NOTE = "Q563 の日次 L−S を、直近 504 営業日の市場（適格銘柄の等金額平均）の累積が負の月に休む。帰無は持つ／休むの列の循環シフト。"
MWIN = 504
DEMEAN = False                                                     # smoke だけ True（run で切り替える・本番は False のまま）


def weight_fn(d, blk):
    # 月ごとの状態＝その月の最初の日より前の直近 504 営業日の市場（mkt）の累積（対数の和）が 0 以上なら 1（持つ）・負なら 0（休む）。504 日そろわない月は NaN（系列に入れない）。
    s = d["mkt"].groupby(level=0).mean().sort_index(); w = {}
    if DEMEAN: s = s - s.mean()                                    # smoke の合成データは市場が上がり続けて休む月が出ないので、経路確認のために平均を引く（本番は引かない）
    first = pd.Series(d.index, index=blk.values).groupby(level=0).first()
    for k, D in first.items():
        h = s[s.index < D].tail(MWIN)
        w[int(k)] = np.nan if len(h) < MWIN else (1.0 if float(np.log1p(h).sum()) >= 0 else 0.0)
    return w


def run(args, rng):
    global DEMEAN
    DEMEAN = bool(args.smoke)
    return eq4.run_weighted(QID, args, rng, weight_fn, "onoff", note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q800 日本株・米国株の横断モメンタム（Q563 の日次 L−S）を市場の過去 24 か月リターンが負の月に休むと", run, HERE)
