# Q387 48 銘柄 D1 の翌 5 日実現分散の予測を水準で学習する HAR-RV（銘柄別・Corsi 原型）・プール水準 HAR・EWMA λ0.94・log-HAR スミアリング補正は、較正（実現/予測の平均 0.8〜1.25）を満たした上で QLIKE で σ60 に勝つか（Q376 の中央値偏りの再設計）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q387 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=4 の 3 本目（S04b 補正版・予測））。出典: [[検証/_基盤/戦略台帳]] S04b／Q376（log-HAR の中央値偏り）／Corsi 2009 HAR-RV／Duan 1983 smearing／知見 Q171 系（線形 HAR-RV は木に勝つ）

- スクリプト: `kensho_s04b_vol_forecast_calibrated_q387.py`（`fe_core` 土台を直接使う型（fe_core.ml walk_forward/ridge・qlike・_s04_common/volfc.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04b_vol_forecast_calibrated_q387.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。目的＝翌 5 日の r² 平均（水準・gap 行の ret はそのまま）。評価は各銘柄のウォークフォワード評価窓（2012〜2024-06）だけ（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04b_vol_forecast_calibrated_q387.py`（B=0。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q387_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q387_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q387_year_sym_<日時>.csv`

## 状態（2026-10-22）

**実行・解釈済み（Sonnet・2026-10-22）。判定は未確定。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
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

実行 2026-10-22（Sonnet・`results/Q387_result_20261022_050927.json`）。48 銘柄を読み込み（QLIKE 集計は 46 銘柄・評価 2012〜2024-06・115,123 行）。`data_health.no_data` の 34 銘柄は DATA_DIR しか見ない仕様の見かけで、実際は `_データ/raw/D1/` から読めている。gaps は US500・USTECH・WTI の 2011 年欠損（評価窓の前〜冒頭）。failed なし。B=0（DM 型）。

| 予測器 | QLIKE 平均 | σ60−予測器 の損失差 | nw_t | 年単位 t | 較正 平均 | 較正 中央値 |
|---|---|---|---|---|---|---|
| naive60（σ60） | 1.083 | 0 | — | — | 1.77 | 0.76 |
| ewma94 | 1.213 | −0.046 | −0.75 | −0.64 | 1.91 | 0.77 |
| **har_level_persym（main）** | **0.537** | +0.553 | 1.17 | 1.00 | **1.016（OK）** | 0.62 |
| har_level_pool | 1.580 | −0.416 | −7.36 | −2.31 | 1.97 | 0.55 |
| loghar_smear | 1.022 | +0.047 | 0.40 | 0.36 | 1.29 | 0.48 |

- main の較正は 1.016 で関門を通った（σ60 は 1.77 と過大側にずれる）。QLIKE 平均は σ60 の半分だが、損失差の年単位 t=1.0・nw_t=1.17 で規則の t≥2 に届かず。
- 損失差は 2015 年（+7.68）1 年に集中。2015 を除く 12 年の平均は −0.002（t=−0.07、正の年 6/12）。2015 は CHF ショック（2015-01）の年に当たるが、原因銘柄の内訳は未確認（推測）。HAR 側の勝ちが平常時の優位でなくショック局面に寄っている可能性がある。
- プール水準 HAR は σ60 に有意に負け（年単位 t=−2.31）。銘柄別でないと効かない。log-HAR スミアリングは較正 2.29→1.29 に改善したが QLIKE は σ60 とほぼ同じ。
- 点検: 較正が中央値で 0.62 と低い（平均は極端な日に引っ張られる）。null_degenerate は B=0 のため該当なし。z の桁外れなし。

判定: **未確定**（機械判定どおり: 較正 OK・年単位 t=1.0<2。棄却条件（較正範囲外・年単位 t<0）にも当たらない）。**解釈: 2015 年 1 年への依存が強く、残り 12 年では σ60 と差がない。平均 QLIKE の半減は 2015 の外れ値が主因。**
