# Q578 日本株・米国株の高出来高プレミアム（月末直近 5 日の出来高ショック上位 10% 買い・下位 10% 売り・1 か月保有）

- 事前登録: `事前登録_q578.md`（= スクリプト冒頭の docstring と同文）。コード: `kensho_high_volume_premium_q578.py`。結果: `results/result_q578.json`・`results/daily_{jp,us}_q578.csv`。
- 出典: Gervais, Kaniel & Mingelgrin 2001（JF）、Kaniel, Ozoguz & Starks 2012（JFE 103(2)・41 か国）。
- データ: Q562 の無料層（`作業層/大容量/equities_free/`・2005-01〜2024-06・封印 2024-07 以降は読まない）。生存バイアスあり（現構成のみ）。
- 探索の地図: イベント × 日本株・米国株 ◎未（決算日が無いので出来高ショックを代理に）（株式無料層 第1弾・N案一括生成 3 件の 1 つ）。

## 状態

**設計とコード（Claude Opus 5.5・2026-10-30）まで。実行と結果の解釈は未。**
- 実行者の手順: `cd 検証/verification-lab/financial-engineering/jp-us-high-volume-premium-q578 && ../../../../作業層/venv_equities/bin/python kensho_high_volume_premium_q578.py`（WS 環境変数で ワークスペース を、EQ_DIR でデータ置き場を上書き可）。冒頭の計画を変えずに走らせる。B=200。Mac で数分〜十数分。
- `machine_verdict` は機械判定。解釈は実行者が README の「結果」に `判定: **…**` の形で書き、検証キューの結果欄・アイデア候補・知見へ /lab の手順で記録する。
- 試走: `--smoke --B 5`（合成データ・経路確認のみ。結果は `results/smoke_*` に出る＝記録に使わない）。クラウドで 2026-10-30 に通し、smoke 結果は消した。

## 方法（要点）

- 判断日＝月末。シグナル＝log(直近 5 日の平均出来高) − log(その前 50 日の平均出来高)。適格・保有・コストは Q563 と同じ。毎月ほぼ全部入れ替わるので、コスト後に残るかが焦点。
- 帰無: シグナルの月の循環シフト（k∈[13, N−13]・B=200）。
- 捨てた: 週次の判断（GKM の原形）は回転が倍。出来高ショック×5 日騰落の符号（決算後ドリフトの代理）は今回が通ったら次段階。
- 先行研究チェック（2026-10-30・WebSearch standard・英語「high-volume return premium Gervais Kaniel Mingelgrin international evidence Japan replication」: GKM 2001、Kaniel-Ozoguz-Starks 2012（JFE）、Pacific-Basin Finance Journal 51（2018）の追試。未確認＝公表後の 2005〜2024-06・月次の回転を払ったコスト後で規程 C1 に届くか（条件の穴＋コストの穴）。）

## 判定（事前固定）

少なくとも 1 国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → **支持**。両国とも NW t<1 → **棄却**。それ以外 → **未確定**。 多重比較: 主 2 本（2 国）を Holm。副は合否に使わない。

## 結果

未実行。
