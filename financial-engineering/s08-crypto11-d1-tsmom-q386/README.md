# Q386 暗号資産 11 通貨の D1（H1→D1・UTC 0 時区切り・週末込み）TSMOM L∈{60,120} は規程モード（暗号版）で封印前の前半（〜2020）・後半（2021〜2024-06）とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q386 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=4 の 2 本目（S08・crypto11））。出典: [[検証/_基盤/戦略台帳]] S08／Q262（11 通貨 TSMOM 20/60/120・前半 t<2 で「最初から無い」）／知見 [[暗号資産11通貨H1の24本TSMOMはコスト後も前も効き目がほとんどなくNeely2003-3の日中足トレンド消失が暗号でも成り立つ]]（Q290）／Liu・Tsyvinski・Wu 2022

- スクリプト: `kensho_s08_crypto11_d1_tsmom_q386.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s08_crypto11_d1_tsmom_q386.py --readme` でこの README を再生成）
- データ: CRYPTO 11 通貨の H1_dukascopy（BTC 2017-05・ETH 2017-12・XRP/BCH/EOS 2018-05・LTC 2018-09・XLM 2021-05・ADA/LNK 2021-09・DOT/SOL 2024-03〜）を h1_to_d1（UTC 0 時）で日足に。土日を含む。封印 time<2024-07-01（SealedRunner）。コスト main: 往復 30 bp（全銘柄）。副: 実測スプレッド（spread_<sym>.csv は BTC/ETH のみ・他 9 通貨は 30 bp のまま）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s08_crypto11_d1_tsmom_q386.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q386_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q386_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q386_year_sym_<日時>.csv`

## 状態（2026-10-22）

**実行・解釈済み（Sonnet・2026-10-22）。判定は下の「結果」。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s08_crypto11_d1_tsmom_q386.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q386 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 11 通貨の等リスク束（規程モード）でも関門（前後半 t≥2・max_dd≥−6%）を通らない（Q262 の前半 t<2 が規程モードでも残る）。通るなら BTC/ETH の寄与が alt9 より大きい。main=L60。L120 は副
- 測るもの: 等金額: 11 通貨の年単位平均 bp（コスト 0／30 bp／実測スプレッド）・年単位 t・束ねた t・Sharpe・最大下落。規程モード（暗号版・split 2021）: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（30 bp と実測スプレッド）。部分群 crypto2／alt9 の同じ統計（記述）
- 帰無: 合図の循環シフト（min_shift=120）B=500 → 等金額の年単位 bp の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「altcoin versus Bitcoin time-series momentum daily returns trend following altcoins empirical study」: Zarattini・Pagani・Barbon 2025「Catching Crypto Trends」（BTC の順張りを全通貨へ拡張・Donchian 束・ボラ規模）、Hong 2017（BTC の 1〜8 週の持続）。alt9 と BTC/ETH を同じ規程モードで分けて比べた日足の研究は未確認
- 捨てた案の数: 2（L=20＝Q262 で既出・alt9 だけの別 ID＝台帳の 4 本固定に反するので部分群の記述に留める）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（暗号版・往復 30 bp・split 2021・封印前）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main L60・30 bp）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。実測スプレッド版・L120・alt9／crypto2 の部分群・銘柄別は記述（判定に使わない）。ADA/XLM/LNK は 2021-09〜、DOT/SOL は 2024-03〜で前半に無い（銘柄数が期間で変わる）ことを結果に明記する

## 結果

実行 `results/Q386_result_20261022_050853.json`（B=500・11 通貨とも ok・failed なし・years_dropped は空・null_degenerate=false・n_tests=2 一致）。

- 注意（data_health の gaps）: BCH は 2019-12〜2021-05 の 18 か月、EOS は 2018-12〜2019-07 の 8 か月が欠け、XRP は 2019-01 が欠ける。欠けの銘柄を除いた再計算はしていない（棄却は等金額 z・規程モードとも欠けの影響で符号が変わる大きさではない。記述として残す）。ADA/XLM/LNK は 2021 以降、DOT/SOL は 2024-03 以降のみ＝前半は 6〜8 銘柄、後半は 11 銘柄
- 等金額 main（L60・30 bp）: 全期間 8 年 bp_net 20.4・年単位 t 0.68・z 0.75（perm_p 0.31）・Sharpe −0.03。前半 4 年 t 1.05（z 1.04）・後半 4 年 t −3.44（z −1.88・bp_net −18.2）。Holm 後 p は前 0.38・後 0.99
- 規程モード（暗号版・split 2021・30 bp）: t_all 1.34・t_pre 1.72・t_post −1.60（NW t は pre 2.10・post −0.37）・Sharpe 0.55・**max_dd −23.4%（関門 −6% を大きく超過）**・日次停止 7 回。規則なし（none）は t_all 0.32・max_dd −97%
- L120（副）: 等金額 全期間 t_year 1.26・前半 1.36・後半 −0.05（bp_net −0.4）。どちらの L も後半に効き目がない
- 結論: Q262（前半 t<2）は規程モードでも残り、後半は符号が負。支持の 3 条件（前後半 t≥2・max_dd −6%・z≥2）をどれも満たさず、等金額 z<1 の棄却条件に当たる。Q385（BTC/ETH のみ・t_pre 2.33・t_post 2.13・max_dd −13.4%・未確定）と比べると、alt9 を足すと前後半とも t が下がる（記述。BTC/ETH 対 alt9 の寄与の分解は部分群の記述まで）
- 前後半とも 4 年なので年単位 t は低検出力

判定: **棄却**（機械判定どおり。等金額 全期間 z 0.75<1）
