# Q569 暗号資産の四半期先物の年率ベーシスが高い日に S23 を休むと、S23 の損益は上がるか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q569 の行（Opus 2026-10-29・無料の新しい源 2 案 第1弾）。出典: Schmeling, Schrimpf & Todorov 2023（BIS WP 1087「Crypto carry」・高キャリーは将来の暴落を予測）、対照 Q551（S26・資金調達率ゲートは棄却・休んだ日 +40.6 bp/日）。

- スクリプト: `run_q569.py`（冒頭に仮説・定義・判定。Q551 と同じく `s23-crypto-uptrend-long-q529/run_q529.py` と `s22-crypto-ml-fintokei-q528/crypto_core.py` を読む）
- データ: Binance COIN-M の BTCUSD・ETHUSD 四半期先物の連続足と指数価格の日足（`検証/_データ/raw/crypto_basis/<PAIR>_D1.csv`、取得 `_データ/fetch/fetch_binance_basis.py`・無料・キー不要・2020-06/07〜）、S23 の価格は Binance 現物 H1（`作業層/大容量/crypto_h1_hist`）
- 評価期間: 2021-01-08〜2024-06-30（**2024-07 以降は封印**）。3.5 年と短く、未確定に落ちやすい
- 実行（`検証/` から）:
  `python3 verification-lab/financial-engineering/crypto-basis-gate-s23-q569/run_q569.py --h1 ../作業層/大容量/crypto_h1_hist --basis _データ/raw/crypto_basis --funding ../作業層/大容量/crypto_funding --out verification-lab/financial-engineering/crypto-basis-gate-s23-q569/results`
  （B=500・数分。`crypto_h1_hist` に BTC・ETH の parquet、`crypto_funding` に funding_BTC/ETH.csv があることを 2026-10-29 に確認済み）。試走 `--smoke --out results`（合成データ・判定に使わない）
- 結果: `results/result_q569.json`（S23・S27c・halves・off_days・null・criteria・verdict・describe・composite_gate）、`results/daily_q569.csv`

## 状態（2026-10-29）

**実行済み（Opus・2026-10-30・B=500）。** 事前登録からの変更点: 計算の中身はなし。実行場所のみ変更（Mac の Linux 環境に parquet の読み込み部品が無く空き容量も無いため、同じファイルをクラウドに移して同じコードで実行し、結果を `results/` に戻した）。S23 の再現は `s23-crypto-uptrend-long-q529/results/daily_q529.csv` の main と評価期間で完全一致（相関 1.0・差 0）。
実行者（Opus）は冒頭の計画を変えずに走らせ、`verdict` は機械判定として、解釈を「結果」に `判定: **…**` の形で書く。記録先: 知見ノート＋知見一覧.jsonl・アイデア候補の状態・戦略台帳（S23 の行と「暗号資産の需給」の行）・検証キュー Q569 を完了・`gen_fe_index.py`。

## 方法（要点）

- 年率ベーシス = (先物/指数 − 1) × 365 / 満期までの日数。満期まで 30 日未満は次の限月。値の確定は日足の翌 00:00 UTC。
- S23 の日足 t の `end` までに確定した最新のベーシスが、t より前の 365 日の 80 分位を超えたら、そのコインを休む（S27 候補）。それ以外は S23 と同じ。
- Q551 と同じ物差し: Sharpe・最大下落・休んだ日の S23 の平均・ゲートの循環シフト帰無の z。
- 記述: 前後半（2022-10 で分割）、コイン別、ベーシスと翌 30 日の最大下落の Spearman（SST の「暴落」）、ベーシスと資金調達率の Spearman（S26 と別の情報か）、合成の追加関門。S27c は S23 の置き換え候補なので、追加関門の相関は S23 と高く出て当然（記述のみ）。
- 先行研究チェック: WebSearch 2026-10-29「Schmeling Schrimpf Todorov crypto carry futures basis predicts returns crash risk」: BIS WP 1087（2023）・CEPR DP 20719・VoxEU コラム。四半期先物の年率ベーシスを順張り（S23）のゲートに使い、資金調達率ゲート（S26）と同じ物差しで比べた形は未確認（条件の穴）。

## 判定（事前固定・Q551 と同じ形）

Sharpe が上がる かつ 最大下落が悪化しない かつ 休んだ日の平均 < 0 かつ z ≥ 2 → **支持**。
休んだ日の平均 > 0、または Sharpe が上がらない → **棄却**。それ以外 → 未確定。

## 結果（2026-10-30・Opus・`results/result_q569.json`）

判定: **棄却（機械判定どおり）**

| | Sharpe 全 | 前（〜2022-09） | 後（2022-10〜） | 最大下落 |
|---|---|---|---|---|
| S23 | 0.76 | 0.37 | 1.32 | −52% |
| S27 候補（ベーシスゲート） | **0.40** | 0.45 | 0.40 | −52% |

- 休んだ日の S23 の平均 **+32 bp/日**（BTC +29・ETH +36。休まなかった保有日は +23・+15）。保有日の休んだ割合 BTC 46%・ETH 36%。
- ゲートの循環シフト帰無（B=500）: Sharpe の帰無 0.73（2.5〜97.5 点 0.48〜0.96）に対して **z −2.84**＝無作為に休むより悪い。
- 記述: ベーシスと翌 30 日の最大下落の Spearman BTC −0.28・ETH −0.14（高キャリーの後は下落が深い＝SST の向き）だが、平均リターンの高さに負ける。**ベーシスと資金調達率の Spearman 0.80・0.85**＝S26 とほぼ同じ情報で、同じ理由（混んだ日はトレンドの最強の日）で棄却。
- 合成の追加関門（記述）: S23 と相関 0.86（置き換え候補なので当然）、合成 Sharpe 1.09→0.97。
- 知見: `_基盤/知識/知見/暗号資産の四半期先物の年率ベーシスが直近1年の8割を超えた日に上昇トレンドの買いを休むと稼ぐ日を捨ててシャープが0.76から0.40に下がりベーシスは資金調達率とほぼ同じ情報.md`。
