# Q298 暗号資産 11 通貨 H1 の 3 ルール群（TSMOM24・SMA50・RSI14 の 50 水準順張り）はコスト後に全て前後半で正か（Neely2003-2 の暗号 H1 移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q298 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Neely2003-2_為替テクニカル戦略の収益性は時間とともに減少した]]。関連: 知見「暗号資産11通貨の日足順張りは2022以降もコスト後に残るか」(Q262)・[[Loubaris2026-2_複数指標の確認は個別指標より的中率が高い傾向があるが有意差なし]]。

- スクリプト: `kensho_crypto_h1_rules_battery_q298.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_crypto_h1_rules_battery_q298.py --readme` でこの README を再生成）
- データ: 暗号資産 11 通貨（CRYPTO）H1_dukascopy、2017〜2026-09。往復コストは CRYPTO_COST_RT_REL=30bp。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_crypto_h1_rules_battery_q298.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q298_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q298_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q298_year_sym_<日時>.csv`

## 状態（2026-10-14）

**設計（Claude Opus 4.7（自動運転））とコード（Claude Opus 4.7（自動運転））まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_crypto_h1_rules_battery_q298.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q298 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: TSMOM24（params[0]）・SMA50（params[1]）・RSI14 の 50 水準（params[2]）の 3 ルールがそれぞれ CRYPTO プールの年単位平均 bp（段階1コスト・CRYPTO_COST_RT_REL=30bp）で前後半とも >0。
- 測るもの: CRYPTO プール（全銘柄等加重）の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。3 ルールを summary で並べる。
- 帰無: 合図の循環シフト（min_shift=72）B=500 → CRYPTO プール（all）の年単位 bp の帰無分布 → z・perm_p・Holm（m=6）。
- 多重比較: 判定は 6 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"cryptocurrency hourly technical trading rules battery TSMOM SMA RSI multiple testing Holm empirical"。見つかったもの: Neely-Weller-Dittmar の為替テクニカルの時系列減衰、暗号での MA・RSI 戦略の実務ブログ、Dukascopy 2024 crypto trends。未確認: 11 通貨 H1 で 3 ルール群を循環シフト帰無と Holm 補正（m=6）で判定する実証は未確認（移植）。
- 捨てた案の数: 約4: (i) 2 ルール（Neely は 3 本以上）、(ii) RSI 30/70 の逆張り（Q191 系と重複）、(iii) D1（Q262 と重複）、(iv) BTC 単独。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 3 ルールとも前後半で bp_net>0 かつ Holm 補正後 p<0.05。棄却: 3 ルールとも全期間 z<1。ほか: 未確定。多重比較は 3 ルール × pre/post の 6 本（Holm で m=6）。

## 結果

未実行。
