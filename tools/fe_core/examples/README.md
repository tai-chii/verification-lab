# EXAMPLE 日足 15 銘柄の時系列モメンタム（L=60）はコスト後に前後半とも正か（Runner の見本）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の EXAMPLE の行（Fable・fe_core Runner の見本（2026-10-13））。出典: 知見 Q136（TSMOM の基準）

- スクリプト: `kensho_example_tsmom_runner.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_example_tsmom_runner.py --readme` でこの README を再生成）
- データ: 15 銘柄 D1_fromH1（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_example_tsmom_runner.py`（B=200。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/EXAMPLE_spec_<日時>.json`（実行前に書かれる事前登録）・`results/EXAMPLE_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/EXAMPLE_year_sym_<日時>.csv`

## 状態（2026-10-13）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_example_tsmom_runner.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー EXAMPLE を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t]=sign(close[t]−close[t−L])。all15 の年単位平均 bp（段階1コスト後）が前後半とも >0
- 測るもの: all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出
- 帰無: 合図の循環シフト（min_shift=120）B 回 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: 見本のため省略
- 捨てた案の数: 0（見本）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 見本のため無し

## 判定（事前固定）

全期間の z<1 → 棄却。前後半とも bp>0 かつ Holm 後 p<0.05 → 支持。ほか → 未確定

## 結果

未実行。
