# Q568 VIX の期間構造の逆転（VIX/VIX3M ≥ 1）の後 20 営業日は、株価指数 10 本の平均リターンが高いか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q568 の行（Opus 2026-10-29・無料の新しい源 2 案 第1弾）。出典: Fassas & Hourvouliades 2019（JRFM 12(3):113）、連鎖元 Q473（S19 の VIX 水準ゲートは棄却・高 VIX の日の指数はむしろ +8.6 bp/日）。

- スクリプト: `kensho_vix_term_inversion_q568.py`（冒頭に仮説・定義・判定・捨てた案の数・知識の締め切り・委託の確かめ方）
- データ: CBOE 公式 CDN の VIX・VIX3M（`検証/_データ/raw/vol/cboe_*.csv`、取得 `_データ/fetch/fetch_cboe_vix_term.py`・無料）、指数 10 本の D1（fe_core.load_d1・S17b と同じ）。2009-10〜2024-06（**2024-07 以降は封印**）
- 実行: `python3 kensho_vix_term_inversion_q568.py`（B=1000・1 分以内）。試走 `--smoke`（合成データ・判定に使わない）
- 結果: `results/Q568_result_<日時>.json`（main・by_year・strategy・sensitivity・composite_gate・machine_verdict）、`results/Q568_daily_<日時>.csv`

## 状態（2026-10-29）

**設計（Opus）とコード（Claude Opus 5.5）まで。実行と結果の解釈は未。** クラウド側で `--smoke --B 20` の経路確認だけ済み。
実行者（Opus）は冒頭の計画を変えずに走らせ、`machine_verdict` は機械判定として、解釈を「結果」に `判定: **…**` の形で書く。記録先: 知見ノート＋知見一覧.jsonl・アイデア候補の状態・戦略台帳（エッジの源の地図「リスクオフ・局面の情報」の行）・検証キュー Q568 を完了・`gen_fe_index.py`。

## 方法（要点）

- 合図: 指数の日 t に、t−1 暦日以前で最新の VIX/VIX3M。≥ 1.0 を逆転日。窓: 逆転日の翌日から 20 指数営業日。
- (a) 窓の中と外の指数 10 本等金額リターンの差（年ごとの差 → 年単位 t）、逆転日の列の循環シフト（min 250 日・B=1000）で z。
- (b) 窓の中だけ持つ戦略 B（保有コスト年 4%）と常に持つ（S17b の指数部分）の Sharpe、合成の追加関門（`tools/composite_gate.py`・記述）。
- 感度（記述）: 閾値 0.95・1.05、窓 10・40 日。
- 先行研究チェック: WebSearch 2026-10-29「VIX term structure backwardation predicts future S&P 500 returns VIX/VIX3M ratio market timing study」: Fassas-Hourvouliades 2019（期間構造は逆張りのタイミング指標。要旨に向き・地平の記載なし）、Macrosynergy・CXO Advisory（ブログ・根拠にしない）。指数 10 本（米欧日豪）・CFD の保有コスト込み・循環シフト帰無・S19 の連鎖という形は未確認（条件の穴＋移植）。

## 判定（事前固定）

(a) の差が 前半・後半とも > 0 かつ 年単位 t ≥ 2（全期間）かつ z ≥ 2 → **支持: 逆転の後は指数を持つと稼げる**。
(a) の全期間の差 ≤ 0、または z < 1 → **棄却**。それ以外 → 未確定。

## 結果

未実行。
