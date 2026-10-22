# Q395 US500 の TSMOM60 符号が負の日は円・フランを買い（USDJPY/USDCHF/AUDJPY/NZDJPY/CADJPY 売り）正の日は逆、のリスクオフ・レジーム戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q395 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 2 本目（S10・安全通貨））。出典: [[検証/_基盤/戦略台帳]] 新 S10（他市場の価格）／Ranaldo・Söderlind 2010 'Safe haven currencies' Review of Finance／Habib・Stracca 2012 JIE／危機アルファ Q207・Q224（順張りは株安局面で正）

- スクリプト: `kensho_s10_safe_haven_q395.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s10_safe_haven_q395.py --readme` でこの README を再生成）
- データ: USDJPY・USDCHF・AUDJPY・NZDJPY・CADJPY の D1_fromH1（2010-01〜・封印 time<2024-07-01。AUDJPY 等 3 本は _データ/raw/D1）。合図の元は US500 の D1_fromH1（同じ UTC 0 時区切り・time で合わせる・先読みなし）。コスト: USDJPY/USDCHF は COST_RT、クロス円 3 本は spread_<sym>.csv の中央値（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s10_safe_haven_q395.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q395_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q395_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q395_year_sym_<日時>.csv`

## 状態（2026-10-22）

**実行済み（2026-10-22・Sonnet）。結果は下の節。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s10_safe_haven_q395.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q395 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Ranaldo・Söderlind 2010: 株安局面で円・フランは対ドル・対資源国通貨で上がる（安全通貨）。この同時相関が株の順張り状態（US500 の 60 日リターン符号）を通じて翌日以降の為替に持ち越されるなら、他市場の価格（株価指数）を 1 つ足した合図が FX 単独の順張り（S07 FX22 ≈0）より関門に近づく。pos = −sign(US500 close[t] − close[t−L])（全 5 ペア共通）。main L=60、副 L=20
- 測るもの: 等金額: 5 ペアの年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出。規程モード: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（全設定）。extra: US500 合図が負の日だけ／正の日だけの bp（安全通貨買いの側が効いているか）
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「equity market trend predicts safe haven currency returns JPY CHF daily out-of-sample trading strategy risk-off regime」: 学術は Ranaldo・Söderlind（同時相関）の要約のみ、ほかは市場解説（BNY・Continuum・Saxo）。株の順張り状態を合図にした予測型の D1 戦略の判定は未確認。解説記事は根拠にしない
- 捨てた案の数: 3（VIX を状態変数にする＝手元に無い／US500 の実現ボラ水準で切る＝ボラは S04b で扱い済み／対ドル 7 ペア全部に同じ合図＝安全通貨の論点から外れる）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main L=60）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副 L=20・銘柄別は記述。S10 の族内試行は Q394・Q395 の 2 本×2 設定＝4

## 結果（Sonnet 実行 2026-10-22・`results/Q395_result_20261022_143649.json`）

- 等金額 main(L=60): 全期間 bp_net=+0.58・年単位 t=0.66・**z=2.75**（p_perm=0.004）／前半 +0.94bp（t=1.13, z=1.81）／後半 +0.26bp（t=0.17, z=2.24, Holm p=0.024）。Sharpe_net 0.30。副 L=20: bp_net −0.69（t=−1.30）。
- 規程モード fintokei: t_all=0.41・t_pre=0.87・t_post=0.05・max_dd=−15.7%・stops=3。ゲート（前後半 t≥2 かつ max_dd≥−6%）は 3 条件とも不通過。
- 銘柄別（記述）: AUDJPY +1.71・NZDJPY +1.24・USDCHF +0.82・CADJPY +0.69・USDJPY −0.05 bp。
- 点検: 5 銘柄とも読めた（missing 空・failed/gaps なし）。null_degenerate=false、years_dropped 空、n_tests=2 一致。2010・2011 は US500 の合図が無く pnl=0・exp=0（構造的なゼロ 2 年）。
- 注意: 帰無の 2.5〜97.5 点が −1.33〜+0.23bp と負側に偏る（合図が「株が上がっていれば円・フランを売る」側に長く傾き、為替側のドリフトと逆になる循環シフトが損に出やすい）。z=2.75 は帰無の偏りで膨らんでいる可能性があり、観測 +0.58bp 自体は年単位 t=0.66 で 0 と区別できない。年別は 2024 が −7.8bp と最大の負け。
- 機械判定: 未確定（z≥2 だが前後半 t<2・max_dd<−6%、棄却条件は非該当）。

判定: **未確定**（全期間 z=2.75 だが年単位 t=0.66・規程 t_all=0.41・max_dd −15.7%。関門不通過。z は帰無の負側偏りで誇張の疑い）
