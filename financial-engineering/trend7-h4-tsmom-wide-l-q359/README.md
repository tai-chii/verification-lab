# Q359 TREND7 の H4 TSMOM で L を広げる（120/240/480 本 ≒ 20/40/80 日）と、Q261 の L=60（≒10 日）不支持は改善するか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q359 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 知見 Q261（H4 L=60 trend7 不支持）、戦略台帳 S01、Moskowitz et al. (2012)

- スクリプト: `kensho_trend7_h4_tsmom_wide_l_q359.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_h4_tsmom_wide_l_q359.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 H4_dukascopy（4 時間足）を _load 上書きで直接読む。2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_h4_tsmom_wide_l_q359.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q359_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q359_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q359_year_sym_<日時>.csv`

## 状態（2026-10-21）

**棄却（確定・2026-10-21）。** 実行・解釈済み。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_h4_tsmom_wide_l_q359.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q359 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t]=sign(close[t]−close[t−L]) を H4 で L=120/240/480 の 3 本に広げ、main_param=L=240 の pre/post 2 本に Holm m=3 を当てる
- 測るもの: 3 本の年単位 bp・t、main の pre/post 2 本の perm_p・Holm、Sharpe・最大下落・露出
- 帰無: 合図の循環シフト（min_shift=500）B=500 → main の年単位 bp の帰無
- 多重比較: 判定は 3 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Hurst, Ooi & Pedersen (2017) の trend-following は日次〜週次。H4 の TSMOM 単独の実証は乏しい
- 捨てた案の数: L=60（Q261 で既に棄却）、L=960（180 日はほぼ日足と同じ）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

main（L=240）が pre・post とも t≥2 かつ bp_net>0 → 支持（lookback 問題）。全期間 t<1 もしくは pre/post とも t<1 → 棄却（H4 の問題）。ほか → 未確定

## 結果

判定: **棄却: 広い L でも全期間 t<1 かつ前後半ともに t<2（H4 自体の問題。lookback 不足ではない）**（2026-10-21 Q359）

- L=120: all t_year=0.92, bp_net=0.25/年; pre t_year=−0.27; post t_year=1.13
- L=240 (main): all t_year=1.00, bp_net=0.40/年; pre t_year=−0.45, z=0.01, p_perm=0.503; post t_year=1.28, z=1.95, p_holm=0.060
- L=480: all t_year=0.56, bp_net=0.23/年; pre t_year=−1.34; post t_year=1.71
- data_health: US500・USTECH に pre 期間の大規模欠損あり（最大 2853h ギャップ）。pre はもともと全 L で負のため棄却に影響なし。
- 結果 JSON: `results/Q359_result_20261021_003027.json`
