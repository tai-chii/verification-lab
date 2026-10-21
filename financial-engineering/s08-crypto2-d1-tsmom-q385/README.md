# Q385 BTC＋ETH の D1（H1→D1・UTC 0 時区切り・週末込み）TSMOM L∈{60,120} は規程モード（暗号版）で封印前の前半（〜2020）・後半（2021〜2024-06）とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q385 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=4 の 1 本目（S08・crypto2））。出典: [[検証/_基盤/戦略台帳]] S08／知見 [[順張りの売り側はドリフトを引くとどの群でも0と区別できず、買い側に残る分は暗号資産と商品とBTCに偏り、規則と期間で揺れる]]／Q262（11 通貨 TSMOM 前半 t<2）／Q367 族別 crypto2 粗利 +4.38 bp／Moskowitz・Ooi・Pedersen 2012

- スクリプト: `kensho_s08_crypto2_d1_tsmom_q385.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s08_crypto2_d1_tsmom_q385.py --readme` でこの README を再生成）
- データ: BTCUSD（H1 2017-05〜）・ETHUSD（H1 2017-12〜）の H1_dukascopy を h1_to_d1（UTC 0 時）で日足に。土日を含む。封印 time<2024-07-01（SealedRunner）。コスト main: 往復 30 bp（CRYPTO_COST_RT_REL・BTC も COST_RT の 40 USD でなく相対 30 bp）。副: _データ/raw/D1/spread_<sym>.csv の日次スプレッド（往復とみなす・BTC/ETH 中央値 約 36〜38 bp）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s08_crypto2_d1_tsmom_q385.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q385_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q385_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q385_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s08_crypto2_d1_tsmom_q385.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q385 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: S07 の族別で粗利が出ている唯一の族（crypto2 +4.38 bp/日・コスト後 +4.08）は、2 銘柄だけの等リスク束でも規程モードの関門（前後半 t≥2・max_dd≥−6%）を通る。main=L60。L120 は副
- 測るもの: 等金額: 2 銘柄の年単位平均 bp（コスト 0／30 bp／実測スプレッド）・年単位 t・束ねた t・Sharpe・最大下落。規程モード（暗号版・split 2021）: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops・gross_median（30 bp と実測スプレッドの両方）
- 帰無: 合図の循環シフト（min_shift=120）B=500 → 等金額の年単位 bp の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「cryptocurrency time series momentum daily Bitcoin Ethereum volatility scaled trend following transaction costs out-of-sample 2024」: arXiv 2602.11708（150 通貨・2022〜2024・ボラ目標 TSMOM Sharpe 1.83）、AUT「Time Series and Cross Sectional Momentum in the Cryptocurrency Market」、Han・Kang・Ryu（コストと日中の清算を入れると多くが消える）。BTC＋ETH の 2 銘柄・D1・プロップ規程（σ0.5%・日次停止・最大下落 −6%）・封印つきの判定は未確認
- 捨てた案の数: 2（L=20 を足す＝Q262 で前半 t<2 の既出・横断版＝2 銘柄では定義できない）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（暗号版・往復 30 bp・split 2021・封印前）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main L60・30 bp）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。実測スプレッド版・L120・銘柄別は記述（判定に使わない）。前後半の年数は 4 前後なので年単位 t は低い検出力であることを結果に明記する

## 結果

未実行。
