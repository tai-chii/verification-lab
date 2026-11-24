# -*- coding: utf-8 -*-
"""Q797 日本株・米国株の業種の 1 か月モメンタム（東証 33 業種／SIC 2 桁の直近 1 か月リターン・上位 3 業種買い下位 3 業種売り）はコスト後 2006〜2024-06 に両国で規程 C1 を通るか

事前登録: 事前登録_q797.md（2026-11-24 18:55 JST・結果を見る前に固定・変更禁止）。株式無料層 第4弾・20 案一括生成（Q787〜Q806）。型: 条件の穴・移植。
【出典】Moskowitz & Grinblatt 1999「Do industries explain momentum?」（JF は知識から記載・要照合。米国では 1 か月で最も強い）。Q704（12-1 か月版・日本 t 1.3 で未確定）。
【先行研究チェック】2026-11-24 WebSearch standard（英語・1 案 2 回）。検索語「one-month industry momentum Moskowitz Grinblatt short-term industry momentum Japan evidence」ほか 1 回。Grundy–Martin 2001（買値売値の跳ね返りと 1 か月ずらしに弱いという反論・誌名は要照合）、Swinkels 2002（日本は 6〜12 か月版の業種モメンタムが有意でない・要照合）、日本の個別株は 1 か月リバーサルが強いという Springer 収録章（著者は要照合）。未確認の点（移植）: 日本で 1 か月版の業種モメンタムを直接検証した論文は見つからない。
【仮説】H1: 直近 1 か月の業種リターン上位 3 業種買い・下位 3 業種売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】業種: 日本は東証 33 業種（universe_jp.csv の sector）、米国は SIC 2 桁（sec/sic.csv。無い銘柄は除く）。業種リターン＝適格銘柄の直近 21 営業日リターン C[t]÷C[t−21]−1 の業種内の単純平均（5 銘柄以上の業種だけ・業種数 10 以上）。上位 3 業種の全銘柄を買い・下位 3 業種の全銘柄を売り（各業種 1/3・業種内等金額）。Q704（12-1 か月）の実装（run_ls_ind・null_circ_ind・load_sector）をそのまま使い、参照期間だけ変える。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（1 か月ずらした版〔t−42..t−21〕。Grundy–Martin の反論の確かめだが本数が増えるので、通ったら次段階）。
【データ・適格・保有・コスト】データ: `作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜。封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。 適格・保有・コスト（Q576〜Q578・第3弾と同じ。土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を `_eq4_common/eq4.py` 経由で読む）: 判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。上位 3 業種の全銘柄を買い・下位 3 業種の全銘柄を売り（各業種 1/3・業種内等金額）。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損。 前後半の境: 2015-01-01（Q578 と同じ）。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止）】事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。
【限り】業種は今の分類（過去の変更は反映しない）。毎月ほぼ全部入れ替わるので回転が大きい（Q704 の 12-1 か月版より大きい見込み）。Q704 の参照期間違いなので、族としては同じ源。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q797.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q797.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_industry_mom_1m_q797.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。共通部品は ../_eq4_common/eq4.py（判定の規則もそこにある）。
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "_eq4_common"))
import eq4
B, P = eq4.B, eq4.P

QID = "Q797"
NOTE = "業種の 1 か月モメンタム・上位 3 業種買い／下位 3 業種売り（各業種 1/3・業種内等金額）。業種は今の分類。"
I = eq4._load("q704", "jp-us-industry-mom-q704", "kensho_industry_mom_q704.py")   # Q704 の実装（業種の読み込み・業種の L/S・帰無）をそのまま使う
LOOKBACK = 252; FORM = 21


def run(args, rng):
    Bq = I.B                                                       # Q704 が読んだ土台（Q578 と同じファイル）
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = Bq.CFG[mkt]; C, V = Bq.load_px(mkt, args.smoke, rng)
        R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        months = Bq.build_months(C, V, cfg, LOOKBACK)
        M = C / C.shift(FORM) - 1                                  # 行 t = C[t]÷C[t−21] − 1（直近 1 か月・ずらしなし）
        sec = I.load_sector(mkt, C.columns, args.smoke)

        def sig_at(t, el, M=M, sec=sec):
            r = M.loc[t].reindex(el).dropna(); s = sec.reindex(r.index).dropna(); r = r.reindex(s.index)   # 業種の無い銘柄は除く
            grp = r.groupby(s); cnt = grp.size(); ind = grp.mean()[cnt >= I.MIN_STOCKS_IND].sort_values()
            if len(ind) < I.MIN_IND: return None
            members = lambda k: list(s.index[s == k])
            return [members(k) for k in ind.index[-I.NTOP:]], [members(k) for k in ind.index[:I.NTOP]], len(r), list(r.index)
        sig_at = eq4.cached(sig_at)
        d = I.run_ls_ind(C, R, sig_at, months, cfg["cost"]); st = eq4._stat(d)
        st["null"] = (I.null_circ_ind(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean()) if len(d) and args.B > 0
                      else dict(B=0, z=np.nan, p=np.nan))
        d0 = I.run_ls_ind(C, R, sig_at, months, 0.0)
        st["sub_cost0_bp"] = 1e4 * d0["ls"].mean() if len(d0) else np.nan; st["sub_cost0_t"] = B.nw_t(d0["ls"]) if len(d0) else np.nan
        st["n_sector_names"] = int(len(sec)); st["n_sectors"] = int(sec.nunique())
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=eq4.verdict_both(per), rule=eq4.verdict_both.__doc__.strip(), note=NOTE), csvs


if __name__ == "__main__":
    eq4.main(QID, "Q797 日本株・米国株の業種の 1 か月モメンタム（東証 33 業種／SIC 2 桁の直近 1 か月リターン・上位 3 業種買い下位 3 業種売り）", run, HERE)
