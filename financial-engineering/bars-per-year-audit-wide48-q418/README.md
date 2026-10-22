# Q418 48 銘柄 D1_fromH1 の銘柄×年の足の本数の一覧と、本数 126 未満の年を年単位 t から除くと TSMOM60 等金額の前後半 t がどれだけ動くか（by_year_stats の min_rows 既定の見直し）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q418 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 8 本目（基盤・データ監査））。出典: [[検証/_基盤/知識/検証方法論/失敗パターン集]] 2026-10-22 15:13 の訂正（「4 本だけの年」）／要対応 2026-10-22 14:54／fe_core.by_year_stats（min_rows=20）

- スクリプト: `kensho_bars_per_year_audit_q418.py`（`fe_core` 土台を直接使う型（Runner._cells を借りる）。事前登録の内容は冒頭 docstring に固定）
- データ: 48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）（`検証/_データ/raw/D1/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_bars_per_year_audit_q418.py`（帰無なし。pandas/numpy のみ・数十秒）
- 試走: `--smoke`（合成データ・銘柄 3・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q418_result_<日時>.json`（`short_cells_126`・`t_all_cells`・`t_excluding`・`delta_t`・機械判定 `machine_verdict`）・`results/Q418_cells_sym_year_<日時>.csv`（銘柄×年の本数・gap・平均 bp）

## 状態（2026-10-22）

**設計とコードまで。実行と解釈は未。** コードは `--smoke` の経路確認だけ済み。
Sonnet／Opus が実行するときの手順:

1. 冒頭 docstring を読んでから走らせる（変更しない）。
2. `python3 kensho_bars_per_year_audit_q418.py` を Mac で実行。
3. `machine_verdict` は事前固定。解釈は実行者が書く。**支持なら要対応 2026-10-22 14:54 の節に「本数<126 のセルの数と Δt」を 1 行添える**（fe_core の変更は事後の判断では行わない。次に土台を触る回へ）。S07 の過去の結果は再計算しない（台帳）。
4. 記録先: 知見ノート（基盤・検証方法論）、失敗パターン集 15:13 の訂正の項に数を 1 行、アイデア候補の状態、検証キュー Q418 を完了へ、`gen_fe_index.py`。

## 方法（要点）

- 仮説: by_year_stats の min_rows=20 は束ねた年の行数に掛かるので、1 銘柄の短い年（開始年・穴の年）は落ちずに年の中の銘柄平均に等重みで入り、年単位 t を上下に動かす。本数 126 未満のセルを除いて t が 0.3 以上動くなら、year_sym に本数を出し min_rows をセル単位で掛ける土台の変更が要る
- 測るもの: セル（銘柄, 年）の一覧（n_bars・gap_bars・mean_bp）、n_bars<126／<200 のセルの数と割合、全期間／前半／後半の年単位 t（全セル・<126 除外・<200 除外）と Δt、短いセルの |mean_bp| の中央値と全セルの比
- 帰無: なし（監査）
- 多重比較: 判定は 1 本（Δt の前半・後半の大きい方）
- 先行研究チェック: WebSearch 2026-10-22「partial year observations bias annual mean t-statistic minimum observations per year backtest evaluation」: CEPR（年次データの部分年の偏り）、シャープと t の小標本の偏り（arXiv 1808.04233）。年あたりの最少本数の規則は見つからず、手元の年単位 t への影響は未確認
- 捨てた案の数: 1（S07〜S13 の全スクリプトの再計算）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持（既定を変える）: n_bars<126 のセルが全セルの 3% 以上 かつ 前半または後半の |Δt|≥0.3。棄却: n_bars<126 のセルが 1% 未満 かつ |Δt|<0.1。ほか → 未確定。

## 結果

未実行。
