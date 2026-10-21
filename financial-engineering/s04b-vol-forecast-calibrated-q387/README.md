# Q387 48 銘柄 D1 の翌 5 日実現分散の予測を水準で学習する HAR-RV（銘柄別・Corsi 原型）・プール水準 HAR・EWMA λ0.94・log-HAR スミアリング補正は、較正（実現/予測の平均 0.8〜1.25）を満たした上で QLIKE で σ60 に勝つか（Q376 の中央値偏りの再設計）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q387 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=4 の 3 本目（S04b 補正版・予測））。出典: [[検証/_基盤/戦略台帳]] S04b／Q376（log-HAR の中央値偏り）／Corsi 2009 HAR-RV／Duan 1983 smearing／知見 Q171 系（線形 HAR-RV は木に勝つ）

- スクリプト: `kensho_s04b_vol_forecast_calibrated_q387.py`（`fe_core` 土台を直接使う型（fe_core.ml walk_forward/ridge・qlike・_s04_common/volfc.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04b_vol_forecast_calibrated_q387.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。目的＝翌 5 日の r² 平均（水準・gap 行の ret はそのまま）。評価は各銘柄のウォークフォワード評価窓（2012〜2024-06）だけ（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04b_vol_forecast_calibrated_q387.py`（B=0。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q387_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q387_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q387_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04b_vol_forecast_calibrated_q387.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q387 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: main=har_level_persym は較正を満たし、QLIKE の損失差（σ60−main）が年単位 t≥2 かつ nw_t≥2。Q376 の log-HAR（較正 2.29）はスミアリングで較正が直るが QLIKE では水準版に劣る
- 測るもの: 予測器 5 本の QLIKE（銘柄ごと→平均）、σ60 との損失差の日次 nw_t（lag=5）・年単位 t・年ごと、較正（実現/予測の銘柄平均・中央値）
- 帰無: Diebold–Mariano 型: 損失差の日次 nw_t（lag=5）。並べ替え帰無は使わない（B=0）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「HAR-RV log transformation retransformation bias QLIKE forecast evaluation levels versus log smearing realized volatility」: Clements・Preve 2021「A Practical Guide to harnessing the HAR volatility model」（推定法・変換・QLIKE の比較）、arXiv 2609.21587 Rough HAR（log モデルを対数正規補正で戻す）、arXiv 2208.12264（変換の偏り）。水準・スミアリング・中央値の 3 つを同じ 48 銘柄・5 日先・QLIKE で並べ、較正を関門にした比較は未確認
- 捨てた案の数: 3（QLIKE 直接最小化・Parkinson レンジ・GBM 水準）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: main の較正 OK（実現/予測の銘柄平均 0.8〜1.25）かつ損失差（σ60−main）の年単位 t≥2 かつ nw_t（lag 5）≥2。棄却: main の較正が範囲外、または損失差の年単位 t<0。ほか → 未確定。他 4 予測器は記述（TrialLog 5）

## 結果

未実行。
