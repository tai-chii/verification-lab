# -*- coding: utf-8 -*-
"""Q798 日本株・米国株で情報が小刻みに届いた銘柄だけのモメンタム（frog-in-the-pan・12-1 か月の上げ下げ日数の偏りが小さい半分）はコスト後 2006〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q798.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 移植。
【出典】Da, Gurun & Warachka 2014 RFS「Frog in the pan: Continuous information and momentum」。入荷台帳 ID132（S&P 500 での検証・順番待ち）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「frog in the pan information discreteness momentum international evidence Japan」ほか 1 回。Da–Gurun–Warachka 2014（米国: 6 か月保有のモメンタムが連続 8.86% → 離散 2.91% へ単調に下がる）、Goyal–Jegadeesh–Subrahmanyam 2025 Review of Finance 29(1)（先進国・新興国でも同じ向き）。未確認の点（移植）: 日本だけで情報の離散度別に分けた査読論文は見つからない。
【仮説】H1（Da ほか）: 情報が小刻みに届いた半分の中の 12-1 か月モメンタム上下 10% は、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1（素のモメンタム Q563 と同じくゼロ）。
【定義】PRET＝C[t−21]÷C[t−252]−1。同じ窓（t−251〜t−21 の 231 営業日・200 日以上）で 上げた日の割合 pos・下げた日の割合 neg。情報の離散度 ID＝sign(PRET)×(neg − pos)（小さいほど小刻み）。判断日ごとに適格銘柄の ID の中央値以下の半分だけを残し、その中で PRET の上位 10% 買い・下位 10% 売り。副（合否に使わない）: ID が中央値より上の半分で同じこと。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（原論文の 5×5 の二重並べ替え。1 群の銘柄数が 40 を切る）。
【データ・適格・保有・コスト】データ: `作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 適格・保有・コスト（Q576〜Q578・第3弾と同じ。土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を `_eq4_common/eq4.py` 経由で読む）: 判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t、ID が中央値より上の半分での同じ L−S。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】原論文の二重並べ替えの簡略版（半分に切ってから上下 10%）。対象が半分になるので上下 10% は日本 約 50・米国 約 40 銘柄。モメンタム系は第1〜3弾で 5 本とも残っていない（知見）ので、事前の見立ては低い。smoke は合成 400 銘柄で半分が 200 になるので最低銘柄数 100 で経路だけ確かめる（本番は土台の 300）。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q798.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q798.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_fip_momentum_q798.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q798"
NOTE = "合図＝12-1 か月リターン。情報の離散度 ID＝sign(PRET)×(下げた日の割合 − 上げた日の割合) が中央値以下の半分だけ。"
LOOKBACK = 252; SKIP = 21; WIN = LOOKBACK - SKIP; MINDAYS = 200


def make_sig(mkt, C, V, R, months, args):
    PRET = C.shift(SKIP) / C.shift(LOOKBACK) - 1                   # C[t−21]÷C[t−252] − 1
    cnt = R.notna().astype(float).rolling(WIN, min_periods=1).sum().shift(SKIP)        # 窓 t−251〜t−21 の有効な日数
    pos = (R > 0).astype(float).rolling(WIN, min_periods=1).sum().shift(SKIP) / cnt
    neg = (R < 0).astype(float).rolling(WIN, min_periods=1).sum().shift(SKIP) / cnt
    ID = (np.sign(PRET) * (neg - pos)).where(cnt >= MINDAYS)       # 小さいほど情報が小刻み

    def side(low):
        def sig_at(t, el):
            p, i = PRET.loc[t].reindex(el), ID.loc[t].reindex(el)
            ok = p.notna() & i.notna(); med = i[ok].median()
            return p.where(ok & ((i <= med) if low else (i > med)))
        return sig_at
    return dict(main=side(True), subs={"discrete_half": side(False)})


def run(args, rng):
    return eq4.run_pv(QID, args, rng, make_sig, LOOKBACK, note=NOTE, min_names=(100 if args.smoke else None))


if __name__ == "__main__":
    eq4.main(QID, "Q798 日本株・米国株で情報が小刻みに届いた銘柄だけのモメンタム（frog-in-the-pan・12-1 か月の上げ下げ日数の偏りが小さい半分）", run, HERE)
