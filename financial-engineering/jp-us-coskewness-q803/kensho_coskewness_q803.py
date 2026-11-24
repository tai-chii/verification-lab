# -*- coding: utf-8 -*-
"""Q803 日本株・米国株の共歪度（市場の 2 乗との共変動・252 日）の低い方買い高い方売りはコスト後 2006〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q803.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 移植。
【出典】Harvey & Siddique 2000「Conditional skewness in asset pricing tests」（JF は知識から記載・要照合）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「coskewness premium Harvey Siddique replication international Japan out-of-sample」ほか 1 回。Harvey–Siddique 2023 Critical Finance Review（本人による 25 年後の標本外検証・対価は原論文と同程度）、Anghel ほか Critical Finance Review（独立追試・1994〜2019 は多くが再現しないが 5 群中 3 群で対価は正に有意）、Yang–Nguyen 2019 JRFM 12(3):149（日本・中身は未確認）。未確認の点（移植）: 日本の個別株で共歪度の上下 10% L/S・コスト後の結果は見つからない。
【仮説】H1（Harvey・Siddique）: 共歪度の低い下位 10% 買い・高い上位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】市場 m は Q802 と同じ（全銘柄の等金額平均）。共歪度＝E[(r−E r)(m−E m)²]÷（σ_r×σ_m²）を直近 252 営業日（200 日以上）の有効な日で。シグナル＝−共歪度。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（市場モデルの残差で作る原論文の定義。残差を取る回帰が銘柄×日で重い。直接の版で代える）。
【データ・適格・保有・コスト】データ: `作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 適格・保有・コスト（Q576〜Q578・第3弾と同じ。土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を `_eq4_common/eq4.py` 経由で読む）: 判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】252 日の共歪度は推定の誤差が大きい（原論文は 60 か月の月次＝知識から記載・要照合）。MAX（Q701・棄却）と同じ「歪み」の族。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q803.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q803.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_coskewness_q803.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q803"
NOTE = "合図＝−共歪度（E[(r−Er)(m−Em)²]÷(σr×σm²)・窓 252 日）。市場＝全銘柄の等金額平均。"
LOOKBACK = 252; MINOBS = 200


def make_sig(mkt, C, V, R, months, args):
    m = eq4.market_ret(R); mes = [x[0] for x in months]
    mo = eq4.roll_moments(R, m, None, LOOKBACK, at=mes)
    a, b, c, d, e = mo["Er"], mo["Em"], mo["Em2"], mo["Erm"], mo["Erm2"]
    num = e - 2 * b * d + 2 * a * b * b - a * c                    # E[(r−Er)(m−Em)²] を和の形に開いたもの
    vi = mo["Er2"] - a * a; vm = c - b * b
    cosk = (num / (np.sqrt(vi.where(vi > 0)) * vm.where(vm > 0))).where(mo["n"] >= MINOBS)
    return eq4.frame_sig(-cosk)


def run(args, rng):
    return eq4.run_pv(QID, args, rng, make_sig, LOOKBACK, note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q803 日本株・米国株の共歪度（市場の 2 乗との共変動・252 日）の低い方買い高い方売り", run, HERE)
