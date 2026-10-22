# Q411 15 銘柄 H1→D1 の TSMOM60 を tick 出来高の増加（V20/V250 ≥ 1）の日だけ持つゲートは、ゲートなしより規程モードの前後半 t と最大下落を改善するか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q411 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 1 本目（S14・出来高ゲート））。出典: [[検証/_基盤/戦略台帳]] 新 S14（出来高＝OHLCV の V。入力基準で明示的に可）／Blume・Easley・O'Hara 1994 'Market statistics and technical analysis: the role of volume' JF／Lee・Swaminathan 2000 'Price momentum and trading volume' JF／S01 Q355（trend7 TSMOM60 本体）

- スクリプト: `kensho_s14_volume_gate_q411.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s14_volume_gate_q411.py --readme` でこの README を再生成）
- データ: 15 銘柄 all15 の H1_dukascopy を UTC 0 時区切りで日足に束ねる（h1_to_d1。volume＝H1 の tick 出来高の合計。FX8 2008〜・油/指数 2011-09〜・BTC 2017〜。封印 time<2024-07-01）。出来高の無い日（0）は欠測。コスト: Runner の既定（COST_RT）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s14_volume_gate_q411.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q411_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q411_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q411_year_sym_<日時>.csv`

## 状態（2026-10-22）

**実行・解釈済み（Sonnet・2026-10-22）。判定は下の結果の節。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s14_volume_gate_q411.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q411 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Blume・Easley・O'Hara 1994: 出来高は価格の合図の質（情報の精度）を伝える。Lee・Swaminathan 2000: 株式では出来高の多い銘柄のモメンタムが強く長く続く。OHLCV の V は主目的の入力なのに手元では 48 銘柄の体系的な検証が 1 本も無い（Q235 の出来高確認ブレイクは H1、CGW 型の反転は 15 銘柄で棄却）。参加が増えている（20 日平均出来高 ≥ 250 日平均）ときの順張りだけ持てば、順張りの負け（参加の薄い往来相場）を避けられる。合図は TSMOM60 で S01 と同じなので粗利の増加は見込まず、下落と t の改善が問い。出来高の無い区間（比が NaN）はゲートを掛けない（素の TSMOM60）
- 測るもの: 等金額: 15 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（ゲートで下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（ゲートあり・なしの両設定＝rule_mode.params）。extra: 銘柄ごとのゲート日の割合（比<1 の日）と出来高の無い日の割合
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「tick volume confirmation time series momentum trend following FX futures volume filter study」: 学術研究は見つからず（TradingView の指標説明のみ＝根拠にしない）。出来高を TSMOM の建玉ゲートにした判定は未確認。Lee・Swaminathan 2000 は株式横断・実出来高で、tick 出来高・時系列は条件の穴
- 捨てた案の数: 3（出来高 z>0 のゲート＝比の方が水準の違いに頑健／比の閾値 0.8〜1.2 の掃引＝1.0 に固定／出来高の多い日だけ建て直す＝回転が増えてコストで死ぬ）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）でゲートあり（main）が前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ ゲートあり の max_dd がゲートなし（param 1）より浅く t_all も高く、等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードのゲートありの t_all がゲートなし以下（ゲートが効かない）。ほか → 未確定。銘柄別・ゲート日の割合は記述。S14 の族内試行は Q411（2 設定）・Q412（2 設定）・Q413（前提 1 本）＝5

## 結果（Q411・2026-10-22・Sonnet 実行・`results/Q411_result_20261022_154418.json`）

- 等金額（15 銘柄・コスト後）: 年平均 −0.62bp、年単位 t=−0.96、循環シフト帰無 z=−0.98（perm_p 0.85）。前半 z=−0.09、後半 z=−2.07（符号は逆向き）。露出 0.42
- 規程モード（フィントケイ・封印前・境 2017）: ゲートあり t_all=−0.11（前半 +0.30／後半 −0.47）、max_dd −35%。ゲートなし（param 1）t_all=+1.33、max_dd −17.6%。関門（前後半 t≥2・max_dd −6% 以内）は不通過
- ゲートは悪化させた（t_all も max_dd も）。出来高が増えている日の順張りは、素の TSMOM60 より弱い
- 点検: `data_health` は failed 無し、gaps は WTI・UKOIL・US500・USTECH の欠月（US500/USTECH は約 60 か月）。FX8 だけでもゲートあり t=−0.96／なし t=+0.82 で同じ向きなので、欠月が結論を左右しない。null_degenerate なし、years_dropped なし（main）
- 多重比較: 宣言 n_tests=2（前後半）。Holm p は両方 1.0

判定: **棄却**（事前固定: 等金額の全期間 z<1、かつゲートありの t_all がゲートなし以下）。機械判定と同じ。勝ち寄りの数字は無い。
