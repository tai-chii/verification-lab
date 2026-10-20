# Q357 TREND7 D1 TSMOM(L=60) の収益は商品 4（XAU/XAG/WTI/UKOIL）と株＋BTC 3（US500/USTECH/BTC）のどちらが担うか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q357 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01、知見 Q230（all15 で片方 t<2）・Q261（trend7 の H4 不支持）

- スクリプト: `kensho_trend7_subgroup_carrier_q357.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_subgroup_carrier_q357.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_subgroup_carrier_q357.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q357_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q357_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q357_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_subgroup_carrier_q357.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q357 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 同じ合図規則で TREND7 全体と 2 部分群の年単位 bp を比べる。担い手は『部分群 A は t≥2 かつ bp>0、部分群 B は bp≤0』のとき特定できる
- 測るもの: TREND7 全体の年単位 bp・t・Sharpe、2 部分群の年単位 bp・t（コスト 0／段階1）、期間別の割れ方
- 帰無: 合図の循環シフト（min_shift=120）B=500 → 全体と部分群の年単位 bp の帰無
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Hurst, Ooi & Pedersen (2017) は商品・指数・金利・為替で TSMOM が効くとした。本件は商品 vs 指数＋BTC の切り分け
- 捨てた案の数: FX8 や全部位分割（4+3+8）は本件の 2 群分割と目的が違うため別案（Q355／既存の Q230）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

どちらか一方が t≥2 かつ bp>0 で他方が bp≤0 → その群が担い手として支持。両方が bp>0 → 未確定（分散源）。両方が bp≤0 → 棄却。n_tests=2 の Holm で主判定は TREND7 全体

## 結果

未実行。
