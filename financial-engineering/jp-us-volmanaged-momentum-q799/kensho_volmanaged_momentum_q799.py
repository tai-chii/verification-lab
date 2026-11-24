# -*- coding: utf-8 -*-
"""Q799 日本株・米国株の横断モメンタム（Q563 の日次 L−S）を直近 126 日の実現ボラの逆数で規模調整すると、コスト後 2006-07〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q799.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 条件の穴。
【出典】Barroso & Santa-Clara 2015 JFE 116(1):111-120「Momentum has its moments」。Q563（素の横断モメンタム・両国 t≈0・2009 年に崩落）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「volatility-managed momentum Barroso Santa-Clara Japan international out-of-sample」ほか 1 回。Barroso–Santa-Clara 2015（米国 1927–2011 でシャープがほぼ倍・急落がほぼ消える）、Daniel–Moskowitz（NBER WP 20439）、Cederburg ほか 2020（ボラ管理一般は標本外で元の戦略に劣ることが多い・誌名は要照合）、Bianchi ほか 2022（SSRN・モメンタムは例外寄り）。日本でも効くという記述は二次要約だけなので根拠にしない。未確認の点（条件の穴）: 2006 年以降・コスト後の日本の結果は確認できない。
【仮説】H1（Barroso・Santa-Clara）: Q563 の横断モメンタムの日次 L−S を直近 126 日の実現ボラの逆数で月ごとに規模調整すると、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】元の系列＝Q563 の結果ファイル `jp-us-xs-momentum-q563/results/daily_{jp,us}_q563.csv` の ls（コスト後・12-1 か月・上下 10%。定義は写し直さず読む。封印 2024-07-01 以降の行は読まない）。月ごとの重み w＝0.5%÷（その月の最初の日より前の直近 126 営業日の ls の標準偏差）。126 日そろわない月は入れない。損益＝w×ls − 2×片道コスト×|w − 前月の w|（大きさ直しの分・月の初日）。比べやすいよう全期間の σ を元の系列（同じ月）にそろえる（判定には影響しない）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 2（日次の規模調整＝回転が増える／下方の分散だけで割る版）。
【データ・適格・保有・コスト】データ: `jp-us-xs-momentum-q563/results/daily_{jp,us}_q563.csv`（Q563 の本番の結果。列 ls＝コスト後の日次 L−S・mkt＝適格銘柄の等金額平均・turn＝回転。封印 2024-07-01 以降の行は読まない）。元の価格データは読み直さない。 Q563 の適格・保有・コスト（参考）: 判断日＝月末・株価≥100 円（US 5 ドル）・売買代金上位 1,000（US 800）・12-1 か月リターンの上位 10% 買い・下位 10% 売り・等金額・片道 JP 10 bp／US 5 bp × 片側回転。 月の区切り: 土台の保有（月の最初の営業日〜翌月の最初の営業日）ごとのブロック。重みは「その月の最初の日より前」の情報だけで決める。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】重みを掛けた後の日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD。副（合否に使わない）: 重みを掛ける前の同じ月の成績・重みの平均と最小最大。
【帰無】月ごとの重みの列の循環シフト（k∈[13, N−13]・B=200）。重みの分布は同じで、どの月に掛けるかだけを壊す。平均どうしで比べる。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】元の系列は月の境の日を 2 回数える土台の決まりのまま（Q563 と同じ）。重みに上限を置かない（原論文どおり）。Q563 自体が両国 t≈0 なので、ボラ管理は「2009 年の崩落を削れるか」の確かめ。Q563 の結果ファイルが無いと本番は動かない。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q799.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q799.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_volmanaged_momentum_q799.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q799"
NOTE = "Q563 の日次 L−S に、月ごとの重み＝0.5%÷直近 126 日の実現ボラ を掛ける。帰無は重みの列の循環シフト。"
VWIN = 126; TARGET = 0.005


def weight_fn(d, blk):
    # 月ごとの重み＝0.5%÷（その月の最初の日より前の直近 126 営業日の日次 L−S の標準偏差）。境の日（2 行ある日）は 1 日にまとめてから数える。126 日そろわない月は NaN（系列に入れない）。
    s = d["ls"].groupby(level=0).mean().sort_index(); w = {}
    first = pd.Series(d.index, index=blk.values).groupby(level=0).first()
    for k, D in first.items():
        h = s[s.index < D].tail(VWIN)
        sd = h.std() if len(h) >= VWIN else np.nan
        w[int(k)] = TARGET / sd if sd == sd and sd > 0 else np.nan
    return w


def run(args, rng):
    return eq4.run_weighted(QID, args, rng, weight_fn, "scale", note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q799 日本株・米国株の横断モメンタム（Q563 の日次 L−S）を直近 126 日の実現ボラの逆数で規模調整すると", run, HERE)
