# Q417 Runner 型の既存結果 JSON を横断し、循環シフト帰無の中心（q025 と q975 の中点）が 0 から 0.5σ 以上ずれる割合と、そのずれが z と年単位 t の食い違いを説明するか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q417 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 7 本目（基盤・帰無の中心））。出典: [[検証/_基盤/知識/検証方法論/失敗パターン集]] 2026-10-22「循環シフト帰無の z が、合図ゼロの区間や片寄った露出で膨らむ」／要対応 2026-10-22 14:39／Jesse・fynance のブートストラップ文書（帰無の 0 中心化）

- スクリプト: `kensho_null_center_bias_q417.py`（`fe_core` 土台を直接使う型。事前登録の内容は冒頭 docstring に固定）
- データ: `financial-engineering/*/results/Q*_result_*.json`（smoke_ を除く・フォルダごとに最新 1 本）のうち main.{all,pre,post} に null_q025・null_q975・z・t_year がある Runner 型の結果。**市場データは読まない**
- 実行: `python3 kensho_null_center_bias_q417.py`（B=2000。pandas/numpy のみ）
- 試走: `--smoke`（新しい 8 フォルダだけで経路を確認。結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q417_result_<日時>.json`（割合・Spearman・perm_p・top10・機械判定 `machine_verdict`）・`results/Q417_rows_<日時>.csv`（結果×期間の表）

## 状態（2026-10-22）

**設計とコードまで。実行と解釈は未。** コードは `--smoke --B 20` の経路確認だけ済み。
Sonnet／Opus が実行するときの手順:

1. 冒頭 docstring を読んでから走らせる（変更しない）。
2. `python3 kensho_null_center_bias_q417.py` を Mac で実行（数秒）。
3. `machine_verdict` は事前固定。解釈は実行者が書く。**支持なら要対応 2026-10-22 14:39 の節に「頻度」を 1 行添える**（fe_core の変更は事後の判断では行わない。次に土台を触る回へ）。
4. 記録先: 知見ノート（基盤・検証方法論）、失敗パターン集 2026-10-22 の項に頻度を 1 行、アイデア候補の状態、検証キュー Q417 を完了へ、`gen_fe_index.py`。

## 方法（要点）

- 仮説: 循環シフトは合図の自己相関を保つが、合図が片寄る（買い持ちが多い・ゼロ区間が長い）とドリフトのある銘柄では帰無の中心が 0 から離れ、z が年単位 t と食い違う。Runner 型の 2 割以上で起きているなら fe_core の変更が要る
- 測るもの: 帰無の中心 c＝(q025+q975)/2、σ̂＝(q975−q025)/3.92、ずれ r＝c/σ̂、食い違い d＝z−t_year。|r|≥0.5 の割合（期間別）、Spearman(r, d)、Spearman(|r|, exposure)、|r| 上位 10 件
- 帰無: r を結果間で並べ替え（B=2000）→ Spearman(r, d) の帰無分布 → perm_p（両側）
- 多重比較: 判定は 1 本。ほかは記述
- 先行研究チェック: WebSearch 2026-10-22「circular shift permutation null distribution bias one-sided exposure trading signal backtest center of null not zero」: 神経科学の循環シフト帰無で自己相関のある信号が非 0 中心の帰無を作る報告、Jesse・fynance の 0 中心化の実装。売買合図の片寄りと帰無の中心の関係は未確認
- 捨てた案の数: 1（各検証の再実行）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持（仕組みの変更が要る）: |r|≥0.5 の割合 ≥0.20、または Spearman(r, d) ≥0.5 かつ perm_p<0.05。棄却: 割合 <0.05 かつ |Spearman|<0.2。ほか → 未確定。

## 結果

未実行。
