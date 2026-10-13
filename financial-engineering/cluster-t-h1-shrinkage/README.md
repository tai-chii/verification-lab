# Q295 15 銘柄 H1 のクラスター t（時刻束ね）は naive パネル t より 30% 以上縮むか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q295 の行（Claude Opus 4.7・10案一括生成 ターミナル版 2026-10-14）。出典: [[GarciaArano2026-3_クラスター標準誤差を使う銘柄数が増えるとtの縮みは小さくなる]]

- スクリプト: `kensho_cluster_t_h1_shrinkage_q295.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: 15 銘柄（SYMS = FX8 + TREND7）H1_dukascopy、2008〜2026-06（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_cluster_t_h1_shrinkage_q295.py`（B=500・約 3 分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q295_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q295_sym_r_<日時>.csv`

## 状態（2026-10-14）

**設計とコードまで。実行と解釈は未**
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_cluster_t_h1_shrinkage_q295.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く。`data_health` に failed／gaps があれば除いた結果も見る。
4. 記録先: 知見ノート、出典の主張カードの `自分の検証`、アイデア候補の状態、検証キュー Q295 を完了へ、`gen_fe_index.py` で一覧を更新。

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

## 結果

未実行。
