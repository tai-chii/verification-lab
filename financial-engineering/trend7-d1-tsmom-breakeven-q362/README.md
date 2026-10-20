# Q362 TREND7 D1 TSMOM(L=60) は段階1コストの何倍までコスト後に正か（本番で許されるコストの余裕）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q362 の行（Fable・/lab-plan 10 案一括（2026-10-20））。出典: 戦略台帳 S01『粗利が保守的コストの 2 倍を超えない案は切る』、_基盤/CLAUDE.md のコスト 2 段階

- スクリプト: `kensho_trend7_d1_tsmom_breakeven_q362.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_trend7_d1_tsmom_breakeven_q362.py --readme` でこの README を再生成）
- データ: TREND7 7 銘柄 D1_fromH1、2012-02-01〜2024-06-30（封印）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_trend7_d1_tsmom_breakeven_q362.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q362_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q362_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q362_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Fable）とコード（Claude）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_trend7_d1_tsmom_breakeven_q362.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q362 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 同じ合図規則でコストを {0, 0.5, 1, 2, 3}× 段階1 の 5 本に広げ、全期間の bp_net の正負を見る。main_param=1×（段階1そのもの）
- 測るもの: 5 水準の全期間 bp_net・t、ゼロ跨ぎの倍率、取引回数、年単位の値動き
- 帰無: 合図の循環シフト（min_shift=120）B=500 → main=1× の年単位 bp の帰無。帰無は main でのみ計算（コスト倍率は帰無と独立）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: Hurst et al. (2017) は TSMOM のコスト余裕を 2〜4× とした。本件は TREND7 封印前の実測
- 捨てた案の数: コスト 5× 以上（現実のスプレッド拡大の目安を超える）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし

## 判定（事前固定）

3× でも bp>0 → 支持（余裕大）。2× で bp>0・3× で bp≤0 → 支持（限定）。1× で bp>0・2× で bp≤0 → 未確定（きつい）。1× で bp≤0 → 棄却

## 結果

未実行。
