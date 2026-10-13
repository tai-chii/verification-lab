# Q290 暗号資産 11 通貨 H1 の 24 本 TSMOM（L=24）はコスト後に前後半とも正か（Neely2003-3 の暗号 H1 移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q290 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Neely2003-3_為替のトレンドは週次月次では強いが日中足にはない]]。関連: 知見「暗号資産11通貨の日足順張りは2022以降もコスト後に残るか」(Q262)・[[Farag2024-1_暗号資産の5分足の流動性供給の見返りはボラや暴落リスクで期間外でも予測できた]]。

- スクリプト: `kensho_crypto_h1_tsmom_q290.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_crypto_h1_tsmom_q290.py --readme` でこの README を再生成）
- データ: 暗号資産 11 通貨（CRYPTO = BTCUSD・ETHUSD・XRPUSD・LTCUSD・ADAUSD・BCHUSD・XLMUSD・EOSUSD・LNKUSD・DOTUSD・SOLUSD）H1_dukascopy、2017〜2026-09。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_crypto_h1_tsmom_q290.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q290_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q290_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q290_year_sym_<日時>.csv`

## 状態（2026-10-14）

**設計（Claude Opus 4.7（自動運転））とコード（Claude Opus 4.7（自動運転））まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_crypto_h1_tsmom_q290.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q290 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t]=sign(close[t]−close[t−24])。CRYPTO 11 通貨の年単位平均 bp（段階1コスト・CRYPTO_COST_RT_REL=30bp）が前後半とも >0。
- 測るもの: CRYPTO プール（全銘柄等加重）の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。
- 帰無: 合図の循環シフト（min_shift=72）B=500 → CRYPTO プールの年単位 bp の帰無分布 → z・perm_p・Holm。
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"cryptocurrency hourly time series momentum TSMOM 24-bar lookback empirical 11 pairs"。見つかったもの: TSMOM in cryptocurrency markets (Zenodo 19671502, SSRN 4825389) ― 日次 TSMOM の pre/post ETF 期間比較、volume-weighted TSMOM。未確認: 11 通貨 H1 の L=24 TSMOM で、循環シフト帰無 B=500 と Holm 補正で判定する実証は未確認（移植）。
- 捨てた案の数: 約3: (i) L=12（半日・保有が短すぎてコストに負ける）、(ii) H4（Q262 の D1 と中間でメッセージが薄い）、(iii) BTC 単独。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 前後半とも bp_net>0 かつ Holm 補正後 p<0.05。棄却: 全期間 z<1。ほか: 未確定。多重比較は main_param=0 の pre/post の 2 本（Holm で m=2）。

## 結果

未実行。
