# Q295 15 銘柄 H1 のクラスター t（時刻束ね）は naive パネル t より 30% 以上縮むか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q295 の行（Claude Opus 4.7・10案一括生成 ターミナル版 2026-10-14）。出典: [[GarciaArano2026-3_クラスター標準誤差を使う銘柄数が増えるとtの縮みは小さくなる]]

- スクリプト: `kensho_cluster_t_h1_shrinkage_q295.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: 15 銘柄（SYMS = FX8 + TREND7）H1_dukascopy、2008〜2026-06（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_cluster_t_h1_shrinkage_q295.py`（B=500・約 3 分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q295_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q295_sym_r_<日時>.csv`

## 状態（2026-10-14）

**実行・解釈済み（Opus 4.7・2026-10-14）**

## 方法（要点）

- 仮説: 15 銘柄 H1 の TSMOM24 損益 bp（コスト0）で、プールの r = cluster_t_time / naive_t_pooled ≤ 0.70（30% 以上の縮み）→ 支持。
- 測るもの: プール r（全期間・前後半）、銘柄別の r 分布、r≤0.70 の銘柄数 K。
- 帰無: 銘柄内で bp を循環シフト（min_shift=72、B=500）→ r の帰無分布 → z・perm_p（side="less"）。
- 多重比較: 判定はプール r 1 本。15 銘柄の銘柄別 r は記述。
- 先行研究チェック: WebSearch 2026-10-14・英語・"intraday hourly panel cluster standard errors shrinkage momentum 15 assets daily vs hourly"。Petersen (2009)、Thompson (2011) 2-way clustering、Driscoll-Kraay (1998)。15 銘柄 H1 の TSMOM で時刻束ねの cluster_t を naive と比較する検証は未確認（移植）。
- 捨てた案の数: 約4: (i) D1（Q175 と重複）、(ii) H4（情報量中途半端）、(iii) 2-way クラスタリング（実装が重い）、(iv) ブートストラップ縮み（循環シフトの方が時系列構造を保つ）。
- 知識の締め切り: Claude の知識はおよそ 2026-06。本データの終端も 2026-06。
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: プール r ≤ 0.70 かつ Holm 補正後 p<0.05。棄却: プール r ≥ 0.95（縮まない）。未確定: ほか。

## 結果（2026-10-14・B=500）

- 結果 JSON: `results/Q295_result_20261014_020506.json`、銘柄別 r: `results/Q295_sym_r_20261014_020506.csv`
- `machine_verdict`: 支持（プール r=-0.3658 ≤ 0.70 かつ p_left=0.002 < 0.05）
- プール r（期間別）: all=-0.3658（z=-3.02）／pre=0.8057（z=0.04・有意でない）／post=-0.6149（z=-2.90）
- **銘柄別 r の中央値 = 1.0233**（15 銘柄・all 期間）／r ≤ 0.70 の銘柄数 K = **0 / 15**
- 15 銘柄すべてで r ≈ 1.01〜1.05（最大 XAGUSD=1.0463、最小 WTI=0.9941）
- `data_health`: WTI・UKOIL・US500・USTECH に gaps（US500・USTECH は 2017 以前のデータ欠損多数・BTCUSD は post のみ）→ 不均衡パネル

判定: **支持（機械判定）**／**解釈: ノイズ**

- プール r=-0.3658 は数値アーティファクト。プール naive_t は銘柄×時刻をフラットに並べた平均の t 値、cluster_t は時刻ごとに銘柄平均を取ったあとの NW t 値で、**不均衡パネル**（BTCUSD は post のみ、US500/USTECH は 2017 以前の欠損、WTI/UKOIL に大きなギャップ）では両者が異なる平均を測ってしまい、符号ごと食い違いうる（pre は +0.81、post は -0.61 の符号反転）。
- ロバストな指標は銘柄別 r。15 銘柄すべて 1.00〜1.05 で、**縮まない**。中央値 1.0233。Q175（D1・FX8 中央値 0.6012・ρ̄=0.137）と対照的。
- 原因の仮説: (i) H1 の TSMOM24 損益は時刻内の銘柄間同時相関が D1 より低い（時刻ごとの撹乱が強い）、(ii) NW lag=5 では H1 の pnl の自己相関構造を十分吸収しない、(iii) 不均衡パネルで時刻平均の母集団が時刻ごとに変わる。
- GarciaArano2026-3 の「束ねるときはクラスタ補正を」は D1 では支持（Q175）だが、**同じ補正を H1 の不均衡パネルに素朴に移植すると、プール r が数値不安定になり誤読につながる**という方法論上の注意として記録する。
