# Q356 TREND7 D1 TSMOM の L ∈ {20,60,120,250} の掃引で、main（L=60）は Holm m=4 補正後も封印前の前後半で t≥2 を保つか（S01 の lookback 頑健性）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q356 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01、Moskowitz ほか (2012) の表3（1〜12m lookback の広がり）、Q355 の本体

- スクリプト: `kensho_trend7_d1_tsmom_lookback_sensitivity_q356.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_tsmom_lookback_sensitivity_q356.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_tsmom_lookback_sensitivity_q356.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q356_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q356_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q356_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_tsmom_lookback_sensitivity_q356.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q356 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 同じ合図規則で L を 20/60/120/250 の 4 本に広げ、main_param=L=60 の pre/post 2 本に Holm m=4 を当てる。L=60 が結果を見てからの選択でないことを示す目的で、全 4 本の年単位 t を併記
- 測るもの: 4 本の年単位 bp・t、main の pre/post 2 本の perm_p・Holm、L × 期間の表
- 帰無: 合図の循環シフト（min_shift=260）B=500 → main の年単位 bp の帰無分布 → Holm 補正
- 多重比較: 判定は 4 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Moskowitz et al. (2012) は 1〜12m（約 20〜250 日）で広く効くことを示した。本件は TREND7・封印前への移植
- 捨てた案の数: L=10・L=500 を事前の文献範囲外として捨てた（Moskowitz 系の典型は 1〜12 か月）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

main（L=60）が pre・post とも t≥2 かつ bp_net>0 → 支持（頑健）。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定

## 結果

未実行。
