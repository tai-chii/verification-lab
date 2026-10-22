# Q412 15 銘柄 H1→D1 の出来高加重 TSMOM60（直近 60 日の Σ ret_i × v_i/v̄_250 の符号）は素の TSMOM60 より規程モードの前後半 t≥2・最大下落 −6% 以内に近づくか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q412 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 2 本目（S14・出来高加重 TSMOM））。出典: [[検証/_基盤/戦略台帳]] 新 S14（出来高）／Blume・Easley・O'Hara 1994 JF／Lee・Swaminathan 2000 JF／Moskowitz・Ooi・Pedersen 2012 'Time series momentum' JFE（素の TSMOM）／Q411（ゲート版）

- スクリプト: `kensho_s14_vw_tsmom_q412.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s14_vw_tsmom_q412.py --readme` でこの README を再生成）
- データ: 15 銘柄 all15 の H1_dukascopy を UTC 0 時区切りで日足に束ねる（h1_to_d1。volume＝tick 出来高の日次合計。封印 time<2024-07-01）。出来高の無い区間は重み 1（素の TSMOM と同じ）。コスト: Runner の既定（COST_RT）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s14_vw_tsmom_q412.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q412_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q412_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q412_year_sym_<日時>.csv`

## 状態（2026-10-22）

**実行済み（2026-10-22・Sonnet）。結果は下の「結果」の節。**
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s14_vw_tsmom_q412.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q412 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Blume・Easley・O'Hara 1994 の読み替え: 出来高の多い日の値動きは情報を含み、少ない日の値動きはノイズ。素の TSMOM60 は全日を等重みで足す（close[t]−close[t−60]）が、出来高で重み付けすると「参加の多い日の向き」を合図にできる。株式の文献（Lee・Swaminathan 2000）は横断・銘柄単位の出来高で、時系列・日単位の重み付けは手元では未検証。Q411（ゲート）と違い露出は変えずに合図の向きだけ変えるので、改善が出れば合図の質の差になる
- 測るもの: 等金額: 15 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（両設定＝rule_mode.params）。extra: 銘柄ごとの出来高加重と素の合図の一致率・回転（符号変化の回数）の比
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「volume-weighted time series momentum futures currencies paper」: Moskowitz・Ooi・Pedersen 2012（出来高は合図に使っていない）、TradingView の出来高加重 TSI 指標（根拠にしない）。出来高で日次リターンを重み付けた TSMOM の判定は未確認
- 捨てた案の数: 3（重みを √v にする＝事前に 1 通りに固定／L を 20・120 でも掃引＝S01 で L 選択は効かなかった／VWAP との位置＝MA 位置型は S01 Q364 で差が無かった）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）で出来高加重（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ 出来高加重の t_all が素の TSMOM60（param 1）より高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの出来高加重の t_all が素の TSMOM60 以下。ほか → 未確定。合図の一致率（extra）は記述。S14 の族内試行は Q411（2）・Q412（2）・Q413（1）＝5

## 結果（Q412・2026-10-22・Sonnet 実行・`results/Q412_result_20261022_154519.json`）

- 等金額（15 銘柄・コスト後）: 年平均 +2.17bp、年単位 t=0.97、循環シフト帰無 z=+2.51（perm_p 0.008）。前半 z=+2.78、後半 z=+0.03。Sharpe 0.31。素の TSMOM60（param 1）は年平均 +0.25bp・年単位 t=0.43・Sharpe 0.37
- 規程モード（フィントケイ・封印前・境 2017）: 出来高加重 t_all=1.35（前半 1.50／後半 0.38）、max_dd −19.5%。素の TSMOM60 は t_all=1.33（前半 1.19／後半 0.63）、max_dd −17.6%。関門（前後半 t≥2・max_dd −6% 以内）は不通過
- 出来高加重の t_all は素より 0.02 高いだけ（棄却条件の「以下」は外れ、支持条件の前後半 t≥2 も満たさない）。差は誤差の範囲。z=2.51 は前半に集中（後半 z=0.03）で、帰無は循環シフトのため年単位 t が 0.97 しかない点とも合わない（年内の符号の揃い方が帰無と違う可能性）
- 合図の一致率（出来高加重 vs 素）は FX・金属で 0.88〜0.92、指数 0.69〜0.76（US500・USTECH は欠月が多い）。回転比は 0.71〜1.46
- 点検: `data_health` は failed 無し、gaps は WTI・UKOIL・US500・USTECH の欠月（US500/USTECH は約 60 か月）。FX8 だけでは出来高加重 t=0.93／素 t=0.82 で同じ向き。指数 13 を除いても結論は変わらない。null_degenerate なし、years_dropped なし（main）
- 多重比較: 宣言 n_tests=2（前後半）。Holm p は前半 0.008・後半 0.493

判定: **未確定**（事前固定: 支持にも棄却にも当たらない）。機械判定の文言は data_health の gaps に由来するが、解釈は同じ。勝ち寄りの数字（z=2.51）を含むが前半だけで関門は不通過。

