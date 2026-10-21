# Q375 48 銘柄 D1 の TSMOM60 メタラベル（k∈{5,10,20}）は族の切除（mom／vol／range／dow／全部）のリッジで AUC・IC がラベル並べ替え帰無より高いか（メタラベルはそもそも当てられるか）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q375 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 2 本目（S04a 前提））。出典: [[検証/_基盤/戦略台帳]] S04a／López de Prado 2018 AFML ch.3／知見 [[過去リターンとMA乖離と実現ボラだけを入力にした木モデルの12時間先予測はEURUSDの1時間足で順位情報も損益も取り出せずコスト以前に信号がない]]

- スクリプト: `kensho_s04a_meta_predictability_q375.py`（`fe_core` 土台を直接使う型（fe_core.ml・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04a_meta_predictability_q375.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04a_meta_predictability_q375.py`（B=50。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q375_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q375_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q375_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04a_meta_predictability_q375.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q375 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: main=(all, k=5) のリッジの評価窓 AUC がラベル並べ替え帰無より高く、前後半とも年平均 AUC>0.5。族の切除で寄与する族（mom／vol／range／dow）が分かる
- 測るもの: 15 試行の AUC（評価窓全体・年ごと）、IC と日次 IC の nw_t、main のラベル並べ替え帰無の AUC 分布（z・perm_p）。参考: main の clip 変換の規程モード損益
- 帰無: ラベル並べ替え（学習窓のメタラベルを年内で並べ替えて学習し直す）B=50 → main の AUC の帰無分布
- 多重比較: 判定は 1 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「meta-labeling predictability feature importance trend following secondary model AUC」: Hudson & Thames の特徴量重要度の解説、Insper の追試（二次モデルの性能は弱い）。AUC の値と族の切除を順張り合図で系統的に報告した研究は見つからない
- 捨てた案の数: 2（GBM を含める・xsec 族を足す）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: main の AUC の perm_p<0.05 かつ 年ごとの AUC>0.5 の年が 2/3 以上 かつ 前後半とも年平均 AUC>0.5。棄却: main の帰無 z<1、または前後半のどちらかで年平均 AUC≤0.5。ほか → 未確定

## 結果

未実行。
