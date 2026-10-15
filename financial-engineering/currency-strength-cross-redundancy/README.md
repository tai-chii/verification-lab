# Q299 通貨強度（対ドル 6 本の L 本リターン平均・7 通貨）は、クロス 2 本（EURJPY・GBPJPY）を足した最小二乗版と H1 の L=24/120/480 時間で相関 0.99 以上か（クロスは冗長か）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q299 の行（Fable・3案一括生成 通貨強度 第1弾 2026-10-15）。出典: taichi と ChatGPT の壁打ち（2026-10-15・通貨強度の Top×Bottom 案）に対する Fable の指摘「三角裁定からクロスは冗長」。関連: 知見 Q208・Q255

- スクリプト: `kensho_currency_strength_redundancy_q299.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: FX8 H1_dukascopy、2008〜2026-06（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。8 本の時刻を内部結合。無い銘柄は JSON の `missing`、欠損の点検は `data_health`）
- 実行: `python3 kensho_currency_strength_redundancy_q299.py`（帰無なし・約 1 分。pandas/numpy のみ）
- 試走: 経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**。合成データは 8 本が独立なので「棄却」が出るのが正常）
- 結果: `results/Q299_result_<日時>.json`（設定・`summary`・`triangular_residual`・`judge_cells`・機械判定 `machine_verdict`）・`results/Q299_cells_<日時>.csv`（通貨 × L × 期間 × 正規化の相関）・`results/Q299_triangular_<日時>.csv`

## 状態（2026-10-15）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke` の経路確認と、整合した合成市場（クロス＝対ドルの差）で corr(a,b)=1.000 になることの確認だけ済み。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_currency_strength_redundancy_q299.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く。`data_health` に failed／gaps があれば除いた結果も見る。`triangular_residual` の `std_resid_over_std_cross` が L で縮むか（短い L ほどミクロ構造ノイズで大きいはず）も書く。
4. 記録先: 知見ノート、アイデア候補の状態、検証キュー Q299 を完了へ、`gen_fe_index.py` で一覧を更新。Q300・Q301 の前提なので結果を両方の README の冒頭に 1 行で引く。

## 方法（要点）

- 仮説: 対ドル 6 本の平均で作った 7 通貨の強度 (a) と、クロス 2 本を足した最小二乗 (b)（Σs=0）は、L=24/120/480 時間・7 通貨・前後半（2017 分割）の 42 セル全部で相関 ≥ 0.99（＝クロスは冗長・情報量を決めるのは通貨の数）。
- 測るもの: corr((a),(b))・corr((c)強度メーター型,(b))・corr((a),(c))、RMSE 比、三角残差 e = r_cross − (r_base − r_quote) の std 比と相関。生の版とボラ正規化版（直前 480 本の 1h std × sqrt(L)）。
- 帰無: なし（測定の整合性の検証・閾値判定）。
- 多重比較: 検定なし。42 セルの最小値で判定。
- 先行研究チェック: WebSearch 2026-10-15・英語・"currency strength index triangular arbitrage redundancy cross rates least squares currency factor decomposition intraday"。Aiba-Hatano ほか (arXiv 2002.02583) の三角裁定とクロス相関のエージェント模型、実務の強度メーター（根拠にしない）。対ドル平均と 8 本最小二乗の一致度を L 別・前後半で報告した実証は未確認（条件の穴）。
- 捨てた案の数: 約3: (i) 10 ペア以上（手元は FX8 のみ）、(ii) NZD（データなし）、(iii) 予測力の比較（情報量の差が先）。
- 知識の締め切り: Claude の知識はおよそ 2026-06。本データの終端も 2026-06。
- 委託の確かめ方: 設計は Fable、コードは Fable（--smoke のみ）、実行と解釈は後の /lab（Opus）。委託なし。

## 判定（事前固定）

支持（クロスは冗長）: 生の版の corr((a),(b)) が 7 通貨 × 3 L × pre/post の 42 セル全部で ≥ 0.99。棄却: どこかで < 0.95。未確定: ほか。

## 結果

未実行。
