# Q292 15 銘柄 D1 の二周期ローテーション規則（L=20 と L=120 の TSMOM が同符号時のみ ±1）は、単独 TSMOM60 より all15 の年単位平均 bp（コスト後）が高いか（Korzan2026-1 の規則の移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q292 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Korzan2026-1_凍結した二周期ローテーション規則の取り置き3年検証は年率22.76パーセントシャープ1.43最大DD11.40でベンチマークを上回った]]。関連: 知見「15銘柄の日足で参照日数20_60_120_250の合図平均は前年までのプールで選んだ最良単一より標本外で前後半とも差のtとzが2未満」(Q253 系)。

- スクリプト: `kensho_dual_lookback_rotation_q292.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_dual_lookback_rotation_q292.py --readme` でこの README を再生成）
- データ: 15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_dual_lookback_rotation_q292.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q292_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q292_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q292_year_sym_<日時>.csv`

## 状態（2026-10-14）

**設計（Claude Opus 4.7（自動運転））とコード（Claude Opus 4.7（自動運転））まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_dual_lookback_rotation_q292.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q292 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 二周期ローテーション（params[1]）は単独 TSMOM60（params[0]）より all15 の年単位平均 bp が高く、前後半とも >0。
- 測るもの: all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。params[0]（単独 TSMOM60）と params[1]（二周期）を summary で並べる。
- 帰無: 合図の循環シフト（min_shift=120）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"dual lookback rotation rule time-series momentum 20-day 120-day agreement signal"。見つかったもの: Faber dual momentum (60/120 ROC rotation)、Moskowitz 2012 blended signals、Pomegra wiki。未確認: 15 銘柄パネル D1 で L=20 と L=120 の TSMOM 同符号フィルタを単独 TSMOM60 と比較し、循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。
- 捨てた案の数: 約4: (i) L=10 と L=200（Korzan の 2 周期は中短期と中長期）、(ii) 3 周期の多数決（Q217 の 3 指標一致と重複）、(iii) 月単位の判定（D1 と期間が噛み合わない）、(iv) 損失時休む規則（anti-equity-curve Q254 と重複）。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 二周期版が前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05、かつ単独より bp_net が高い。棄却: 全期間 z<1。ほか: 未確定。多重比較は main_param=1 の pre/post の 2 本（Holm で m=2）。

## 結果

未実行。
