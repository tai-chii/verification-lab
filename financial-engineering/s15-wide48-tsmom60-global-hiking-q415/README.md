# Q415 48 銘柄 D1 の TSMOM60 を「8 中銀（USD EUR JPY GBP AUD CAD CHF NZD）のうち直近 180 暦日に利上げした数が 4 以上」の局面だけ持つと、常時持つ S07 本体より規程モードの前後半 t と最大下落が改善するか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q415 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 5 本目（S15・TSMOM60×グローバル利上げ局面））。出典: [[検証/_基盤/戦略台帳]] 新 S15（利上げ局面の事前定義）／Man Group 2024 'Views from the floor 2024-01-23'（BTOP50 と利上げ局面・運用会社の資料＝参考）／Neville ほか 2021 'The best strategies for inflationary times' JPM／S07 Q367（48 銘柄 TSMOM60 本体）／政策金利 `_データ/raw/rates/policy_<CCY>.csv`（BIS・8 通貨）

- スクリプト: `kensho_s15_tsmom_global_hiking_q415.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s15_tsmom_global_hiking_q415.py --readme` でこの README を再生成）
- データ: 48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 8 通貨の政策金利（実施日ベース・t−1 暦日まで）。局面＝直近 180 暦日に上げた中銀の数 ≥4。コスト: Runner の既定（COST_RT／スプレッド中央値／暗号 30 bp）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s15_tsmom_global_hiking_q415.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q415_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q415_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q415_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s15_tsmom_global_hiking_q415.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q415 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Man Group 2024（BTOP50 と FF 金利・1987〜）: 順張りは利上げ局面の大半で正、2022 年は +15%。機構: 金融引き締めは金利・為替・債券に持続的な方向（政策の段階的な変更）を作り、順張りはそれを拾う。緩和・据え置きの局面では往来相場で順張りが負ける。S07（48 銘柄 TSMOM60）は全期間で粗利 ≈0・規程モード max_dd −95% だったが、損失が据え置き局面に集中しているなら、局面で絞れば t と下落が改善する。局面は政策金利（ポイントインタイム・t−1 暦日まで）だけで決め、閾値 4／8 と窓 180 日は事前に固定。局面外は 0（持たない）
- 測るもの: 等金額: 48 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（局面で下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（局面限定・常時の両設定＝rule_mode.params）。extra: 局面の日数（年別）、利上げ中銀数の分布、族別（fx/idx/cmd/bond/crypto）の net bp（局面内）
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）。注意: 局面限定は合図ゼロの区間が長いので、失敗パターン集 2026-10-22 の「循環シフト帰無の中心のずれ」を事後の判断で点検する（Q417 がその頻度を測る）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「trend following performance during global monetary tightening cycles central bank hiking regime trend strategies returns」: Man Group 2024（BTOP50・利上げ局面の大半で正・運用会社の資料で利害あり）、PIMCO・Wellington（債券・株の利上げ局面成績で順張りではない）。独立な学術研究と、非米中銀を含む「利上げ中銀数」の局面定義は未確認
- 捨てた案の数: 3（閾値 2〜6 の掃引＝4（過半）に固定／各銘柄の自国中銀だけで局面を決める＝S12 の金利モメンタムと同じ族／利下げ局面も「持つ」側に入れる＝Man の結果は利上げ側）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）で局面限定（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ 局面限定の max_dd が常時（param 1）より浅く t_all も高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの局面限定の t_all が常時以下（局面が効かない）。ほか → 未確定。局面の日数（年別）・族別の寄与は記述。S15 の族内試行は Q414（2）・Q415（2）＝4

## 結果

未実行。
