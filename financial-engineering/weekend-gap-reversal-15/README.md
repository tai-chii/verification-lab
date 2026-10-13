# Q296 15 銘柄 D1 の月曜ギャップ逆張り（金曜終値→月曜始値のギャップと逆方向に月曜のみ ±1、火曜以降 0）は all15 の年単位平均 bp（コスト後）が前後半とも正か（Dao2016-2 の 15 銘柄移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q296 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Dao2016-2_週末ギャップは月曜に逆張りで利益が出る]]。関連: 知見「FX8の日足で月曜のモメンタムは火〜金より弱く符号が反転する傾向」(Q180 系)。

- スクリプト: `kensho_weekend_gap_reversal_15_q296.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_weekend_gap_reversal_15_q296.py --readme` でこの README を再生成）
- データ: 15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_weekend_gap_reversal_15_q296.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q296_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q296_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q296_year_sym_<日時>.csv`

## 状態（2026-10-14）

**設計（Claude Opus 4.7（自動運転））とコード（Claude Opus 4.7（自動運転））まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_weekend_gap_reversal_15_q296.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q296 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 金→月のギャップ（gap = open_mon − close_fri）が正なら月曜に −1、負なら +1、ギャップがなければ 0。月曜のみ保有し、火曜に 0 に戻す。all15 の年単位平均 bp（コスト後）が前後半とも >0。
- 測るもの: all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。
- 帰無: 合図の循環シフト（min_shift=20）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"weekend gap reversal Monday open close Friday mean reversion 15 markets daily cross-section"。見つかったもの: Dao の月曜効果、Chen 2016 Monday return reversal、Lakonishok-Smidt 1988 day-of-week。未確認: 15 銘柄 D1 で金→月のギャップ逆張り（月曜のみ保有）を循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。
- 捨てた案の数: 約4: (i) 木→金のギャップ（週末要因が入らない）、(ii) 順張り版（月曜ギャップは逆張りが Dao の主）、(iii) 保有を 1 週間に延長（別仮説）、(iv) FX のみ（Dao は 15 市場だが手元 15 銘柄パネルで統一）。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05。棄却: 全期間 z<1。ほか: 未確定。多重比較は pre/post の 2 本（Holm で m=2）。

## 結果

未実行。
