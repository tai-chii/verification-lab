# Q576 日本株・米国株の長期反転（13〜48 か月の負け組買い・勝ち組売り・月次 L/S）

- 事前登録: `事前登録_q576.md`（= スクリプト冒頭の docstring と同文）。コード: `kensho_long_reversal_q576.py`。結果: `results/result_q576.json`・`results/daily_{jp,us}_q576.csv`。
- 出典: DeBondt & Thaler 1985、Chopra-Lakonishok-Ritter 1992、国際比較（Alpha Architect「Overreaction and the cross-section of returns: international evidence」・CXO「Long-Term Reversal for Stocks Everywhere」）。
- データ: Q562 の無料層（`作業層/大容量/equities_free/`・2005-01〜2024-06・封印 2024-07 以降は読まない）。生存バイアスあり（現構成のみ）。
- 探索の地図: バリュー（長期反転）× 日本株・米国株 ◎未（価格だけの代理）（株式無料層 第1弾・N案一括生成 3 件の 1 つ）。

## 状態

**設計とコード（Claude Opus 5.5・2026-10-30）まで。実行と結果の解釈は未。**
- 実行者の手順: `cd 検証/verification-lab/financial-engineering/jp-us-long-reversal-q576 && ../../../../作業層/venv_equities/bin/python kensho_long_reversal_q576.py`（WS 環境変数で ワークスペース を、EQ_DIR でデータ置き場を上書き可）。冒頭の計画を変えずに走らせる。B=200。日本株 3,109 銘柄のピボット込みで Mac で数分〜十数分（Q563 は 3.5 分）。
- `machine_verdict` は機械判定。解釈は実行者が README の「結果」に `判定: **…**` の形で書き、検証キューの結果欄・アイデア候補・知見へ /lab の手順で記録する。
- 試走: `--smoke --B 5`（合成データ・経路確認のみ。結果は `results/smoke_*` に出る＝記録に使わない）。クラウドで 2026-10-30 に通し、smoke 結果は消した。

## 方法（要点）

- 判断日＝月末。シグナル＝−(C[t−252]/C[t−1008]−1)（直近 12 か月を飛ばし、その前 36 か月の騰落の符号反転）。適格・保有・コストは Q563 と同じ（株価≥100 円／5 ドル・売買代金上位 1,000／800・片道 JP 10 bp／US 5 bp × 回転）。最初の判断日は 2009 年。
- 帰無: シグナルの月の循環シフト（k∈[60, N−60]・B=200。36 か月窓で持続性が高いので 13 か月では足りない）。
- 注意: 生存バイアス（消えた負け組が買い側に入らない）は長期反転を**強く見せる**向き。支持でも J-Quants／CRSP での再判定が要る。
- 先行研究チェック（2026-10-30・WebSearch standard・英語「long-term reversal DeBondt Thaler Japan stocks evidence recent decades」: 国際比較 2 件（Alpha Architect・CXO）、大阪大学・立命館の日本株の過剰反応の論文。未確認＝現構成の無料層・2009〜2024-06・コスト後で規程 C1 に届くか（追試＋条件の穴）。）

## 判定（事前固定）

少なくとも 1 国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → **支持**。両国とも NW t<1 → **棄却**。それ以外 → **未確定**。 多重比較: 主 2 本（2 国）を Holm。副は合否に使わない。

## 結果

未実行。
