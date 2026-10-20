# Q355 TREND7 の D1 TSMOM 本体（L=60）は、封印前の前後半とも年単位 t≥2 で純損益がコスト後に正か（S01 の中央関門）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q355 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01（_基盤/戦略台帳.md）、知見 Q230（all15 の D1 TSMOM 前後半片方 t<2）・Q261（trend7 の H4 L=60 不支持）・Q292（trend7 の D1 二周期 支持）・Q207/Q224（危機アルファ正）

- スクリプト: `kensho_trend7_d1_tsmom_core_q355.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_tsmom_core_q355.py --readme` でこの README を再生成）
- データ: TREND7（XAUUSD/XAGUSD/WTI/UKOIL/US500/USTECH/BTCUSD）D1_fromH1、2012-02-01〜2024-06-30（封印: 2024-07 以降は読まない）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_tsmom_core_q355.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q355_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q355_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q355_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_tsmom_core_q355.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q355 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t]=sign(close[t]−close[t−60]) を TREND7 7 銘柄に等重みで適用。段階1コスト後の年単位平均 bp が pre（2012-16）・post（2017-24.5）とも t≥2 かつ正
- 測るもの: trend7 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出、前後半の割れ方
- 帰無: 合図の循環シフト（min_shift=120）B=500 回 → trend7 の年単位 bp の帰無分布 → z・perm_p・Holm（pre/post の 2 本）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Moskowitz, Ooi & Pedersen (2012) 'Time Series Momentum' JFE — 本体の原著（原案は 12m lookback）。本件は 60 日版の TREND7 への移植で、Hurst et al. (2017) の trend-following factor は同系統
- 捨てた案の数: 多（S01 までに FX8・all15・短期足など多数の lookback・銘柄群が棄却）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。期間はすべて以前
- 委託の確かめ方: なし（設計 Fable・実行 Sonnet 想定、Opus 見直し）

## 判定（事前固定）

pre・post とも年単位 t≥2 かつ bp_net>0 → 支持（S01 ゲート通過）。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定

## 結果

未実行。
