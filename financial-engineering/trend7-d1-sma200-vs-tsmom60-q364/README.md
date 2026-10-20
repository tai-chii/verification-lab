# Q364 TREND7 D1 で TSMOM(L=60) と SMA200 の上下による順張りは、封印前の前後半で年単位 t≥2 を取る合図形式がどちらか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q364 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01、Faber (2007) 'A Quantitative Approach to Tactical Asset Allocation' の SMA10 ルール、Moskowitz et al. (2012)

- スクリプト: `kensho_trend7_d1_sma200_vs_tsmom60_q364.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_sma200_vs_tsmom60_q364.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_sma200_vs_tsmom60_q364.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q364_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q364_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q364_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_sma200_vs_tsmom60_q364.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q364 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 2 設定を並べる: (1) tsmom(L=60)、(2) sma_pos(n=200)。段階1コスト後の年単位 bp を pre/post 2 本（×2 設定）で比較。main_param=TSMOM(L=60)
- 測るもの: TSMOM の年単位 bp・t（判定）、SMA200 の年単位 bp・t（記述）、2 合図の相関と露出
- 帰無: 合図の循環シフト（min_shift=220）B=500 → main=TSMOM の年単位 bp の帰無
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Faber (2007) は SMA10（月次）、Moskowitz et al. (2012) は差分型。両者の等価性に関する議論は Zakamulin (2014)
- 捨てた案の数: SMA クロス（SMA50/SMA200 のゴールデンクロス）、EMA 版（SMA と大差ない見込み）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

main（TSMOM）が pre・post とも t≥2 かつ bp_net>0 → 支持。全期間 t<1 もしくは pre/post とも t<1 → 棄却。ほか → 未確定。SMA200 の値は summary で記述比較

## 結果

実行日: 2026-10-21。結果ファイル: `results/Q364_result_20261021_011337.json`・`results/Q364_year_sym_20261021_011337.csv`

判定: **棄却**
**解釈: TSMOM(L=60) が前後半とも年単位 t<1（pre t=0.61, post t=0.66）。SMA200 はさらに弱く前半は bp_net マイナス（pre t=-0.32, post t=0.40）。TREND7 D1 において差分型・位置型どちらの順張り合図も封印前の前後半で有意な年単位超過リターンを示さない。**

| 設定 | 期間 | bp_net/年 | t_year | t_cluster | sharpe_net |
|---|---|---|---|---|---|
| TSMOM(L=60) | 全期間 | 0.71 | 0.91 | 0.91 | 0.24 |
| TSMOM(L=60) | pre(〜2017) | 0.64 | 0.61 | 0.39 | 0.18 |
| TSMOM(L=60) | post(2017〜) | 0.75 | 0.66 | 0.83 | 0.26 |
| SMA200 | 全期間 | −0.06 | −0.04 | 1.14 | 0.30 |
| SMA200 | pre(〜2017) | −1.16 | −0.32 | 0.68 | 0.31 |
| SMA200 | post(2017〜) | 0.63 | 0.40 | 0.98 | 0.31 |

data_health: failed なし。gaps は WTI・UKOIL・US500・USTECH に 2011-2013 年のギャップ（分析開始 2012-02-01 前または warmup 期間内）→判定に影響なし。
