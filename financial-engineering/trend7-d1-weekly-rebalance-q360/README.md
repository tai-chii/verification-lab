# Q360 TREND7 D1 TSMOM(L=60) を週次（月曜のみ）でリバランスしても、封印前の前後半で年単位 t≥2 を保つか（コスト低減の効果）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q360 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01、Moskowitz et al. (2012) は月次。日足で日次より粗いリバランスがコスト低減に効くかの検証

- スクリプト: `kensho_trend7_d1_weekly_rebalance_q360.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_weekly_rebalance_q360.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_weekly_rebalance_q360.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q360_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q360_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q360_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_weekly_rebalance_q360.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q360 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: raw[t]=tsmom_pos(L=60) を日次に計算し、各 ISO 週の最初の足で raw をラッチして次の週まで固定。段階1コスト後の年単位 bp が pre/post とも t≥2 で正
- 測るもの: 週次リバランスの年単位 bp、露出・取引回数、Q355（日次）との bp 差とコスト差
- 帰無: 合図の循環シフト（min_shift=120）B=500 → 年単位 bp の帰無
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Baltas & Kosowski (2013) は週次・月次でも TSMOM が効くとした。本件は TREND7 日足で日次との差を見る
- 捨てた案の数: 月次リバランス（粗すぎて trend の変化に追従できない）、日中リバランス（コストで死ぬ）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定

## 結果

未実行。
