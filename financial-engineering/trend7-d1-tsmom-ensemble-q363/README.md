# Q363 TREND7 D1 で TSMOM 符号の等重みアンサンブル（L=20/60/120/250 の平均）は、単発 L=60 と比べて封印前の前後半で年単位 t≥2 を取りやすいか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q363 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: Baltas & Kosowski (2013) 'Momentum Strategies in Futures Markets and Trend-following Funds' — 複数頻度の平均。戦略台帳 S01

- スクリプト: `kensho_trend7_d1_tsmom_ensemble_q363.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_tsmom_ensemble_q363.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_tsmom_ensemble_q363.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q363_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q363_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q363_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_tsmom_ensemble_q363.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q363 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t] = mean( sign(close[t]-close[t-L]) for L in {20,60,120,250} )。連続値（-1〜1）で等重み平均。段階1コスト後の年単位 bp が pre/post とも t≥2
- 測るもの: アンサンブルの年単位 bp・t・Sharpe、L=60 単発（Q355）に対する差、露出と取引回数
- 帰無: 合図の循環シフト（min_shift=260）B=500 → 年単位 bp の帰無
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Baltas & Kosowski (2013) は複数の lookback の平均で Sharpe が単発より高いと報告。Hurst et al. (2017) も同系統
- 捨てた案の数: 重みを lookback 長で変える（短期を重く／長期を重く）、符号ではなく z-score の平均
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定

## 結果

実行日: 2026-10-21、B=500、`results/Q363_result_20261021_011120.json`

| 期間 | bp_net | t_year | Sharpe_net | z | p_perm |
|---|---|---|---|---|---|
| 全期間（12年、2012除外） | 1.71 | 1.82 | 0.50 | 1.37 | 0.090 |
| pre（〜2016、4年、2012除外） | 1.69 | 0.70 | 0.39 | 1.20 | 0.128 |
| post（2017〜、8年） | 1.71 | 1.88 | 0.55 | 0.93 | 0.196 |

- data_health: gaps (WTI・UKOIL・US500・USTECH、2011〜2012年初。2012年は全銘柄 years_dropped)。gap_bars(pre)=4 で軽微。failed=なし
- Q355（L=60単発）比: pre 0.61→0.70、post 1.12→1.88。アンサンブルは post で顕著に改善するが pre は依然弱い
- 多重比較(Holm): p_holm(pre)=0.256, p_holm(post)=0.256

判定: **未確定**（pre t=0.70 < 2、post t=1.88 < 2。支持・棄却のいずれにも当たらない。アンサンブルは post を大幅改善したが前半が弱いまま）
