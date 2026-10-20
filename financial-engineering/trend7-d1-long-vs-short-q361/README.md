# Q361 TREND7 D1 TSMOM(L=60) を long-only と short-only に分けると、どちらが bp>0 を担うか（long-only で足りるか）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q361 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01、知見 Q207/Q224（下落相場での危機アルファ=short の寄与）、Moskowitz et al. (2012) の long/short 分解

- スクリプト: `kensho_trend7_d1_long_vs_short_q361.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_long_vs_short_q361.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_long_vs_short_q361.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q361_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q361_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q361_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_long_vs_short_q361.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q361 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 合図を long（+1 のみ、−はゼロ）／short（−1 のみ、+はゼロ）／both（Q355 と同じ）の 3 設定で比べる。main_param=long。Holm m=2 の判定対象は long の pre/post
- 測るもの: 3 設定（long/short/both）の年単位 bp・t、各期間の bp と Sharpe、露出の違い
- 帰無: 合図の循環シフト（min_shift=120）B=500 → long の年単位 bp の帰無
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Moskowitz et al. (2012) Table 3 は long/short の寄与を分解。株式では short が公表後に減衰する例が多い（Mclean & Pontiff 2016）
- 捨てた案の数: long/short の非対称な閾値（+1 と −1 で L を変える）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

long が pre・post とも t≥2 かつ bp_net>0 → 支持（long-only で足りる）。long が全期間 t<1 もしくは pre/post とも t<1 → 棄却（short が担い手候補）。ほか → 未確定

## 結果

実行日: 2026-10-21。B=500。結果ファイル: `results/Q361_result_20261021_010323.json`。

| 設定 | all bp_net/t | pre(2012〜2016) bp_net/t | post(2017〜2024) bp_net/t |
|---|---|---|---|
| long-only | 4.09 / 1.82 | **-0.08 / -0.06** | **6.70 / 2.03** |
| short-only | -1.64 / -1.35 | +0.72 / 0.45 | -3.11 / -2.01 |
| both | 2.46 / 1.23 | +0.64 / 0.61 | 3.59 / 1.12 |

- data_health: failed なし、gaps（WTI・UKOIL・US500・USTECH の初期欠損）。pre の gap_bars=4 のみ、post=0。影響軽微
- long の Holm 補正後 p: pre=0.37、post=0.16（いずれも非有意）
- null_degenerate: false（帰無は正常）

**支持条件**（long が pre AND post 両方で t≥2 かつ bp>0）: pre の t=-0.06 で不成立。
**棄却条件**（all t<1 または pre/post 両方 t<1）: post の t=2.03>1 で不成立。

判定: **未確定**（機械判定と一致）

**解釈**: long-only は post（2017〜2024）では t=2.03・bp_net=6.70 と機能するが、pre（2012〜2016）では t=-0.06 でほぼゼロ。short-only は post で悪化（t=-2.01）。前後半の非対称性が大きく、long-only が安定した担い手とは言えない。long-only 化によるコスト削減（short 側の取引除去）は post の結果だけでは正当化できない。
