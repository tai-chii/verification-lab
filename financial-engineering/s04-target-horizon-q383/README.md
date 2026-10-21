# Q383 翌 k 日（k∈{1,5,20}）リターンのリッジ予測は地平線で IC・コスト後損益が変わるか（embargo=k・3 試行・S04a/c の k=5 の妥当性）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q383 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 10 本目（S04 前提））。出典: [[検証/_基盤/戦略台帳]] S04／知見 Q135 系（短い地平線は信号なし）／Moskowitz・Ooi・Pedersen 2012

- スクリプト: `kensho_s04_target_horizon_q383.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04_target_horizon_q383.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04_target_horizon_q383.py`（B=20。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q383_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q383_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q383_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04_target_horizon_q383.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q383 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: k=1 は IC≈0、k=5・20 は IC>0、コスト後損益は k=20 が最も高い。k=5 は IC 年単位 t≥2 で損益も上位
- 測るもの: 3 本の IC（年ごと・日次 nw_t lag=k）と規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe・gross_median）
- 帰無: main（k=5）のラベル並べ替え B=20。各 k の IC の年単位 t
- 多重比較: 判定は 1 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「forecast horizon 1-day 5-day 20-day return predictability machine learning cross-asset futures information coefficient」: 5 日 IC を使った LLM 特徴の研究（arXiv 2604.10996）、VIX 先物の翌日予測（PLOS One 2024）。多資産 D1 で 1/5/20 日の地平線を同じ特徴量で比べた研究は見つからない
- 捨てた案の数: 1（k=10・60）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持（k=5 でよい）: k=5 の IC 年単位 t≥2 かつ k=5 の規程モード mean_bp が 3 本中 1〜2 位。棄却（k=5 は不適）: k=5 の IC 年単位 t<1、または k=5 の mean_bp が 3 本で最小かつ最大との差が 1bp 超。ほか → 未確定

## 結果

未実行。
