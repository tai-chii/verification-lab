# Q376 48 銘柄 D1 の翌 5 日実現ボラ予測（σ20・σ60・HAR・リッジ全特徴・GBM 全特徴）は QLIKE で σ60 に勝ち、σ̂ を size_weights に渡すと S07 TSMOM60 の規程モードで最大下落が浅くシャープが上がるか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q376 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 3 本目（S04b 本体））。出典: [[検証/_基盤/戦略台帳]] S04b／知見 Q205（ボラ・ターゲティング）／知見 Q171 系（HAR-RV は木に勝つ）／Corsi 2009 HAR-RV

- スクリプト: `kensho_s04b_vol_forecast_sizing_q376.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04b_vol_forecast_sizing_q376.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04b_vol_forecast_sizing_q376.py`（B=50。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q376_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q376_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q376_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04b_vol_forecast_sizing_q376.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q376 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: main=HAR（log vol_5/20/60 のリッジ）の log(RV5) 予測は QLIKE で σ60 素朴予測に勝ち、σ̂ を size_weights の σ に渡した S07 TSMOM60 規程モードは σ60 版より max_dd が浅く Sharpe が高い
- 測るもの: 予測器 5 本の QLIKE（全体・年）、σ60 との損失差の年単位 t・nw_t（lag=5）。各 σ̂ で S07 TSMOM60 の規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe）と σ60 版との差
- 帰無: (1) DM 型: 損失差の日次 nw_t。(2) σ̂ を銘柄ごとに年内で並べ替えた σ̂_perm で同じ損益 B=50 回 → max_dd・Sharpe の帰無分布
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「machine learning realized volatility forecast volatility targeting trend following drawdown HAR comparison QLIKE」: HARd to Beat（arXiv 2406.08041・1455 株で ML は HAR に勝てない）、Fed 2025 サーベイ、HARNet。予測を size_weights に渡して順張りの最大下落を測る研究は見つからない
- 捨てた案の数: 2（Parkinson レンジ・k=20）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: HAR の QLIKE 損失差（σ60−HAR）が年単位 t≥2 かつ nw_t≥2、かつ HAR サイジングの max_dd が σ60 版より浅く Sharpe が高く、σ̂ 並べ替え帰無の max_dd より浅い側 5% 以内。棄却: HAR の QLIKE が σ60 に勝たない（損失差 t<0）、または HAR サイジングの max_dd が σ60 版より深い。ほか → 未確定

## 結果

実行 2026-10-22（`results/Q376_result_20261022_014329.json`・48 銘柄すべて `_データ/raw/D1/` に有り。`data_health.no_data` は DATA_DIR しか見ないので無視。gaps の US500・USTECH・WTI は 2011 年で評価開始 2012 より前）。

**事前登録からの変更点**: 損失差の日次計算が QLIKE を逆比（予測/実現）で書いていた（`qlike_mean` は正しい実現/予測）。実現/予測に直して再実行。修正前は `results/kensho_s04b_vol_forecast_sizing_q376_before_fix_20261022.py`・`Q376_result_20261022_014257_before_fix.json`。判定規則は不変。

| 予測器 | QLIKE | 損失差(σ60−x) nw_t | 年t | max_dd | Sharpe |
|---|---|---|---|---|---|
| σ60（基準） | 0.9575 | – | – | -0.362 | -0.333 |
| σ20 | 0.9594 | -0.47 | -0.18 | -0.390 | -0.416 |
| HAR（main） | 1.2097 | -1.85 | -1.54 | -0.383 | -0.375 |
| リッジ全特徴 | 1.1166 | -2.20 | -1.90 | -0.383 | -0.379 |
| GBM 全特徴 | 1.1929 | -1.76 | -1.43 | -0.398 | -0.405 |

HAR は QLIKE で σ60 に負け（損失差 t<0）、サイジングも max_dd が 2.0pt 深く Sharpe も低い。σ̂ 並べ替え帰無は退化せず（σ̂ を崩すと更に悪化。ただし σ60 に勝つ根拠にはならない）。5 本とも σ60 を上回らない。

判定: **棄却**（HAR は σ60 に勝たず、サイジングでも改善しない。HARd to Beat と整合しない側＝この 48 銘柄 D1 では σ60 が最強の素朴基準）


### 見直し（事後の判断・Opus・2026-10-22 01:50）

- **見つけた問題**: HAR・リッジ・GBM は目的を log(RV5) にして `exp(予測)` で戻している。この戻し方だと平均ではなく中央値を予測することになり、分散を系統的に小さく見る。QLIKE は小さく見た予測を強く罰するので、HAR が負けた分の大半はこの偏りから来ていた。診断（`results/diag_logbias_q376_20261022.py`・判定には使わない）では、評価窓の 実現/予測 の平均は σ60 が 1.70、HAR が 2.29（中央値は 0.76 と 1.03）。
- **実時間で使える補正**（前年までの評価窓の 実現/予測 の平均を掛けるだけ）を入れて、評価初年を除いた QLIKE を出した: σ60 1.005／HAR 補正なし 1.276／HAR 補正あり 1.077。差の約 4 分の 3 は偏りの分だが、**補正しても σ60 に勝たない**。棄却条件のうち QLIKE の方（損失差 t<0）は補正後も当たるので、**判定は棄却のまま**にする。
- **サイジングの方（max_dd・Sharpe）は未判定とする**。偏りで σ̂ が小さいぶん建玉が大きくなっており、max_dd が深いのはその影響を含む。σ̂ を偏り補正してサイジングを比べるのは別の Q（S04b の再設計）で行う。Q377（σ_used=max(σ̂_HAR, σ60)）も同じ偏りの上に設計されているので保留にした。
