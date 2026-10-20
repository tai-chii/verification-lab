# Q360 TREND7 D1 TSMOM(L=60) を週次（月曜のみ）でリバランスしても、封印前の前後半で年単位 t≥2 を保つか（コスト低減の効果）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q360 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01、Moskowitz et al. (2012) は月次。日足で日次より粗いリバランスがコスト低減に効くかの検証

- スクリプト: `kensho_trend7_d1_weekly_rebalance_q360.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_weekly_rebalance_q360.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_weekly_rebalance_q360.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q360_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q360_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q360_year_sym_<日時>.csv`

## 状態（2026-10-21）

**実行完了（Sonnet）。未確定。**

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

実行日: 2026-10-21、B=500、TREND7 全 7 銘柄（gaps: WTI・UKOIL・US500・USTECH、gap_bars=4、start以前の欠損が主体で影響軽微）

| 期間 | bp_net | t_year | z | p_perm |
|---|---|---|---|---|
| all (13y) | 1.94 | 1.17 | 0.82 | 0.23 |
| pre (5y, 〜2017) | 0.45 | 0.31 | -0.01 | 0.50 |
| post (8y, 2017〜) | 2.87 | 1.13 | 0.89 | 0.21 |

参考: Q355（日次）all bp_net=2.46 / t=1.23、pre bp_net=0.64 / t=0.61、post bp_net=3.59 / t=1.12

判定: **未確定**（pre t=0.31・post t=1.13 — 支持条件 t≥2 に届かず、棄却条件 t<1 にも該当せず）

**解釈:** 週次リバランスは日次（Q355）より bp_net が低下（全期間 -0.52 bp、後半 -0.72 bp）。コスト低減より機会損失が大きく、日次の t 値も元から低いため改善余地は限定的。Baltas & Kosowski (2013) では週次でも効いたが、TREND7 日足では日次よりむしろ悪化している。
