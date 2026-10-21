# Q388 水準 HAR-RV（銘柄別 OLS）の σ̂ を size_weights の σ に渡した S07 TSMOM60 の規程モードは、σ60 版より最大下落が浅く Sharpe が高いか（較正を前提条件とし σ̂ 並べ替え帰無で判定。Q376 の偏りを除いた再判定・Q377 の前提）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q388 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=4 の 4 本目（S04b 補正版・サイジング））。出典: [[検証/_基盤/戦略台帳]] S04b／Q376／Q377（保留）／知見 [[日足順張りの建玉を直前60日の実現ボラの逆数で規模調整すると年ごとのシャープが約0.09上がる]]（Q205）／Harvey・Hoyle・Korgaonkar・Rattray・Sargaison・Van Hemert 2018

- スクリプト: `kensho_s04b_vol_sizing_calibrated_q388.py`（`fe_core` 土台を直接使う型（fe_core.risk・ml・_s04_common/volfc.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04b_vol_sizing_calibrated_q388.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: s04ml.WIDE48_COST_REL（COST_RT に無い 34 銘柄は知識から記載・実行者が spread_<sym>.csv と照合）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04b_vol_sizing_calibrated_q388.py`（B=50。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q388_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q388_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q388_year_sym_<日時>.csv`

## 状態（2026-10-22）

**実行・解釈済み（Sonnet・2026-10-22）。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04b_vol_sizing_calibrated_q388.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q388 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 較正された σ̂（har_level_persym）を規程モードの σ に渡すと、σ60 版より max_dd が浅く Sharpe が高く、σ̂ を年内で並べ替えた帰無より浅い
- 測るもの: σ60 版と σ̂ 版の規程モード（t_pre/t_post・mean_bp・max_dd・worst_day・stops・Sharpe・gross_median）、差、較正・QLIKE 損失差（前提）
- 帰無: σ̂ を銘柄ごとに年内で並べ替えた σ̂_perm で同じ損益 B=50 回 → max_dd・Sharpe の帰無分布。帰無の max_dd より浅い側の割合
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「volatility forecast HAR-RV volatility targeting trend following drawdown reduction realized volatility sizing multi-asset」: Harvey ほか 2018（60 資産超でボラ目標は極端な損失の確率を下げる・推定器は半減期 20 日の EWMA）、Quantpedia のまとめ。HAR-RV の予測を規程モード（1 銘柄上限・日次停止）の σ に渡して最大下落を測った研究は未確認
- 捨てた案の数: 2（非対称版＝Q377・port_vol_window 側）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

棄却: σ̂ の較正が範囲外（実現/予測の銘柄平均 0.8〜1.25 の外）、または QLIKE 損失差（σ60−σ̂）の年単位 t<0、または σ̂ 版の max_dd が σ60 版より深い。支持: 前提 OK かつ σ̂ 版の max_dd が σ60 版より浅く Sharpe が高く、σ̂ 並べ替え帰無の max_dd より浅い側 5% 以内（B≥20）。ほか → 未確定

## 結果

実行: `results/Q388_result_20261022_051014.json`（B=50・48 銘柄読込・封印 2024-07-01・評価 2012〜）。

- 前提: 較正 実現/予測の銘柄平均 1.016（範囲内・中央値 0.62）、QLIKE 損失差（σ60−σ̂）の年単位 t=+1.00（>0・ただし 2015 年の +7.68 が平均を引っ張り 12 年中 6 年は負）。
- 規程モード（fintokei）: σ60 版 max_dd −0.3526／Sharpe −0.298 に対し σ̂ 版 −0.3955／−0.401。**σ̂ 版のほうが最大下落が 4.3pt 深く Sharpe も低い**（差 max_dd −0.0429・Sharpe −0.102・mean_bp −0.23）。ゲートはどちらも不合格。
- σ̂ 並べ替え帰無（B=50）: 帰無の max_dd 中央値 −0.483・帰無より浅い側 100%（p_perm 0.02）。ただし基準の σ60 版との比較が棄却条件に先に当たる。帰無は退化していない。
- 点検: `data_health.failed` なし。gaps は US500・USTECH などの 2011-09〜2012-01 の欠損（評価開始 2012-01 の直前・影響は小さい）。`no_data` は DATA_DIR のみの判定で 14/48 だが n_syms=48 で読めている。
- 事前登録の棄却条件「σ̂ 版の max_dd が σ60 版より深い」に該当。成績が良すぎる・期間で符号反転・境界の迷いはなく Opus 見直しは不要。

判定: **棄却**（較正された HAR-RV の σ̂ は σ60 より最大下落を浅くしない。σ̂ は無意味ではない（並べ替え帰無よりは良い）が、σ60 を上回る根拠はない）
