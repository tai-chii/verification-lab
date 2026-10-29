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

**設計（Opus）とコード（Claude Opus 5.5）まで。実行と結果の解釈は未。** クラウド側で `--smoke --B 10` の経路確認だけ済み。
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

## 結果

未実行。
