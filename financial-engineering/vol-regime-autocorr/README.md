# Q294 15 銘柄 D1 の 1 次自己相関は高ボラ月で低ボラ月より高いか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q294 の行（Claude Opus 4.7・10案一括生成 ターミナル版 2026-10-14）。出典: [[Loubaris2026-3_GARCHで分けた高ボラ局面は衝撃の持続性が高い]]

- スクリプト: `kensho_vol_regime_autocorr_q294.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: 15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_vol_regime_autocorr_q294.py`（B=1000・約 2 分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q294_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q294_symbols_<日時>.csv`

## 状態（2026-10-14）

**設計とコードまで。実行と解釈は未**
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_vol_regime_autocorr_q294.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。
4. 記録先: 知見ノート、出典の主張カードの `自分の検証`、アイデア候補の状態、検証キュー Q294 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 15 銘柄のうち、ρ_high − ρ_low > 0 かつ Holm 補正後に有意（m=15、α=0.05）な銘柄が ≥ 4 本（1/4 弱）→ 支持。高ボラ局面で衝撃持続性が高い。
- 測るもの: 各銘柄の Δρ=ρ_high−ρ_low（全期間・前後半）、Holm 補正後 p、15 銘柄中の有意本数 K。
- 帰無: 銘柄内で月のラベル（high/low）を並べ替え（B=1000）→ 各並べ替えで Δρ を再計算 → 観測との z・片側 p_right。
- 多重比較: 判定は全期間 Δρ の p_right を 15 銘柄分 Holm（m=15）。前後半は記述。
- 先行研究チェック: WebSearch 2026-10-14・英語・"daily return autocorrelation volatility regime GARCH shock persistence 15 assets cross-section"。Cont (2001) "Volatility Clustering"（絶対値・二乗の自己相関は長期）、Zivot GARCH 実務ノート。15 銘柄 D1 で符号つき 1 次自己相関を循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。
- 捨てた案の数: 約4: (i) 絶対値や二乗の自己相関（Cont 2001 と重複）、(ii) GARCH モデル推定（計算重い）、(iii) 3 分位、(iv) 時間足 H1（Q252 の M15 と重複）。
- 知識の締め切り: Claude の知識はおよそ 2026-06。本データの終端も 2026-06。
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: K ≥ 4。棄却: K ≤ 1。未確定: K ∈ {2, 3}。補助情報: 前後半それぞれの Δρ の符号（判定は変えない）。

## 結果

未実行。
