# Q358 Moskowitz 原著の 12m-1m（L=252、skip=21）TSMOM は、TREND7 D1 で封印前の前後半とも年単位 t≥2 で正か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q358 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: Moskowitz, Ooi & Pedersen (2012) JFE Table 2 — 12m-1m のクロスセクション平均が TSMOM の基準。戦略台帳 S01

- スクリプト: `kensho_trend7_d1_moskowitz_skip1m_q358.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_moskowitz_skip1m_q358.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_moskowitz_skip1m_q358.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q358_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q358_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q358_year_sym_<日時>.csv`

## 状態（2026-10-21）

**完了（2026-10-21 Sonnet）。** B=500 実行済み。判定: 未確定。

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

実行日: 2026-10-21。結果ファイル: `results/Q358_result_20261021_002655.json`、`results/Q358_year_sym_20261021_002655.csv`

| 期間 | bp_net (bp/日) | t_year | z | p_holm |
|---|---|---|---|---|
| 全期間 (2013-2024, 12年) | 3.125 | 1.853 | 1.713 | — |
| 前半 (2013-2016, 4年) | 4.892 | 1.285 | 2.375 | 0.024 |
| 後半 (2017-2024, 8年) | 2.241 | 1.241 | 0.814 | 0.208 |

- years_dropped: [2012]（ウォームアップ 252 日由来）
- null_degenerate: false
- data_health: WTI・UKOIL・US500・USTECH に gaps あり（gap_bars=4、早期データの欠損。主要影響なし）
- Sharpe_net: 全期間 0.470、前半 0.892、後半 0.400
- 最大下落 (net): −9462 bp（後半）

判定: **未確定**

前後半とも bp_net>0 だが、年単位 t が 1.28/1.24 で事前固定の「t≥2」に届かない（支持条件未達）。全期間・前後半とも t≥1 で棄却条件（t<1 または pre/post とも t<1）も不成立。12m-1m スキップは TREND7 D1 で正の方向性はあるが統計的確信は不十分。

知見ノート: `検証/_基盤/知識/知見/Moskowitz2012の12m-1mスキップTSMOMはTREND7D1で正方向だが年単位t2未満で未確定.md`
