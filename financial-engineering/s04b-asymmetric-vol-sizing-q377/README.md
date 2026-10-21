# Q377 予測ボラを上振れだけ使う非対称サイジング（σ_used=max(σ̂_HAR, σ60)）は対称版・σ60 版より S07 TSMOM60 の規程モードで最大下落が浅く、シャープを落とさないか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q377 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 4 本目（S04b 派生））。出典: [[検証/_基盤/戦略台帳]] S04b／Bongaerts・Kang・van Dijk 2020 FAJ Conditional Volatility Targeting／知見 Q205

- スクリプト: `kensho_s04b_asymmetric_sizing_q377.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04b_asymmetric_sizing_q377.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04b_asymmetric_sizing_q377.py`（B=100。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q377_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q377_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q377_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04b_asymmetric_sizing_q377.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q377 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 固定最大損失の下ではボラ予測の価値は規模を落とす側にある。非対称 σ_used=max(σ̂_HAR, σ60) は σ60 版より max_dd が浅く Sharpe は 0.9 倍以上を保つ
- 測るもの: 3 本（σ60・対称・非対称）の規程モード t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe・gross_median。非対称−σ60 の max_dd 差・Sharpe 比
- 帰無: σ̂_HAR を銘柄ごとに年内で並べ替えて非対称版を B=100 回 → max_dd・Sharpe の帰無分布
- 多重比較: 判定は 1 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「asymmetric volatility targeting only de-leverage when forecast volatility rises trend following drawdown」: Bongaerts ほか 2020（条件つきボラ目標で最大下落 54→20%）、Fanous 2026 arXiv 2605.09123（非対称ボラ管理の枠組み）。「予測>実現のときだけ落とす」規則を順張り×固定最大損失で測った研究は見つからない
- 捨てた案の数: 1（閾値つきの段階版）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 非対称の max_dd が σ60 版より浅く、Sharpe が σ60 版の 0.9 倍以上、かつ σ̂ 並べ替え帰無の max_dd より浅い側 5% 以内。棄却: 非対称の max_dd が σ60 版より深い、または Sharpe が σ60 版の 0.9 倍未満。ほか → 未確定

## 結果

未実行。
