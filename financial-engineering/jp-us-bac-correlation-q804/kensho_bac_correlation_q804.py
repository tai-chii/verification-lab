# -*- coding: utf-8 -*-
"""Q804 日本株・米国株の市場との相関（252 日）の低い方買い高い方売り（ボラ 5 分位の中で順位・betting against correlation）はコスト後 2006〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q804.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 条件の穴。
【出典】Asness, Frazzini, Gormsen & Pedersen 2020 JFE 135(3):629-652「Betting against correlation」。Q708（BAB・未確定）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「betting against correlation Asness Frazzini Gormsen Pedersen international Japan replication」ほか 1 回。Asness ほか 2020（米国と国際サンプルで強い・信用取引残高と連動）、Jensen–Kelly–Pedersen 2023 JF 78(5):2465-2518（93 か国・153 ファクターの公開データ）。Alpha Architect の解説は使わない。未確認の点（条件の穴）: 等金額の上下 10%・レバレッジなし・コスト後の結果と日本単独の数字は確認できない（原論文は順位加重＋ベータ中立のレバレッジ＝知識から記載・要照合）。
【仮説】H1（Asness ほか）: ボラ 5 分位の中で市場との相関が低い上位 10% 買い・高い下位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】市場 m は Q802 と同じ。相関 ρ・ボラ σ＝直近 252 営業日（200 日以上）の日次リターンで。判断日ごとに適格銘柄を σ の 5 分位に分け、分位の中で ρ の順位（0〜1）を取る。シグナル＝−順位（どのボラ分位からも相関の低い銘柄を同じ割合で買う）。副（合否に使わない）: ボラで分けない −ρ。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 2（原論文の相関 5 年・3 日重ねリターン／脚ごとにベータ 1 にそろえるレバレッジ。土台の等金額と違う作りになる）。
【データ・適格・保有・コスト】データ: `作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 適格・保有・コスト（Q576〜Q578・第3弾と同じ。土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を `_eq4_common/eq4.py` 経由で読む）: 判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t、ボラで分けない相関の L−S。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】原論文はベータ中立（低相関側にレバレッジ）。本案は等金額なので L−S は負のベータを持つ見込み（知見「低 β 側を買う形では L−S が負の β」）。ベータは結果に出るので読むときに使う。BAB（Q708）をボラと相関に分けた片方。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q804.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q804.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_bac_correlation_q804.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q804"
NOTE = "合図＝−（ボラ 5 分位の中での市場との相関の順位）。窓 252 日。市場＝全銘柄の等金額平均。"
LOOKBACK = 252; MINOBS = 200; NQ = 5


def make_sig(mkt, C, V, R, months, args):
    m = eq4.market_ret(R); mes = [x[0] for x in months]
    mo = eq4.roll_moments(R, m, None, LOOKBACK, at=mes)
    cov = mo["Erm"] - mo["Er"] * mo["Em"]; vi = mo["Er2"] - mo["Er"] ** 2; vm = mo["Em2"] - mo["Em"] ** 2
    vi = vi.where(vi > 0); vm = vm.where(vm > 0)
    rho = (cov / np.sqrt(vi * vm)).where(mo["n"] >= MINOBS); vol = np.sqrt(vi).where(mo["n"] >= MINOBS)

    def sig_at(t, el):
        r, s = rho.loc[t].reindex(el), vol.loc[t].reindex(el); ok = r.notna() & s.notna(); r, s = r[ok], s[ok]
        if len(r) < 10 * NQ: return pd.Series(np.nan, index=el)
        q = pd.qcut(s.rank(method="first"), NQ, labels=False)      # ボラの 5 分位
        return (-r.groupby(q).rank(pct=True)).reindex(el)          # 分位の中で相関の低い順
    return dict(main=sig_at, subs={"corr_no_vol_groups": eq4.frame_sig(-rho)})


def run(args, rng):
    return eq4.run_pv(QID, args, rng, make_sig, LOOKBACK, note=NOTE)


if __name__ == "__main__":
    eq4.main(QID, "Q804 日本株・米国株の市場との相関（252 日）の低い方買い高い方売り（ボラ 5 分位の中で順位・betting against correlation）", run, HERE)
