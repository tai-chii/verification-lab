# Q358 Moskowitz 原著の 12m-1m（L=252、skip=21）TSMOM は、TREND7 D1 で封印前の前後半とも年単位 t≥2 で正か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q358 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: Moskowitz, Ooi & Pedersen (2012) JFE Table 2 — 12m-1m のクロスセクション平均が TSMOM の基準。戦略台帳 S01

- スクリプト: `kensho_trend7_d1_moskowitz_skip1m_q358.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_moskowitz_skip1m_q358.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_moskowitz_skip1m_q358.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q358_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q358_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q358_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_moskowitz_skip1m_q358.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q358 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t]=sign(close[t−21]−close[t−252]) を TREND7 に等重みで適用。段階1コスト後の年単位 bp が pre/post とも t≥2 で正
- 測るもの: TREND7 の年単位 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出
- 帰無: 合図の循環シフト（min_shift=260）B=500 → 年単位 bp の帰無
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: 原著 Moskowitz et al. (2012) の 12m-1m 設定。Baltas & Kosowski (2013) も同じスキップで複数頻度に拡張
- 捨てた案の数: 複数の skip 幅や、原著の月足頻度を飛ばした案（D1 で近似する）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定

## 結果

未実行。
