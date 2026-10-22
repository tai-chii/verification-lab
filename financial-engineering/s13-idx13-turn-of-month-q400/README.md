# Q400 株価指数 13 の D1 月替わり効果（各銘柄の足で数えた月の最終営業日と翌月の最初の 3 営業日の 4 本だけ買い持ち）は 2010 年以後も残り、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q400 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 7 本目（S13・月替わり））。出典: [[検証/_基盤/戦略台帳]] 新 S13（暦）／McConnell・Xu 2008 'Equity returns at the turn of the month' FAJ／Lakonishok・Smidt 1988 RFS／Etula・Rinne・Suominen・Vaittinen 2020 'Dash for cash' RFS／Q181・Q285・Q286（前倒し窓は見えない・株固有）

- スクリプト: `kensho_s13_idx13_tom_q400.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s13_idx13_tom_q400.py --readme` でこの README を再生成）
- データ: 指数 13 の D1_fromH1（US500・UK100・JPN225 等は 2010〜、GER40 等は 2013-09〜・封印 time<2024-07-01・_データ/raw/D1）。営業日は各銘柄の足で数える。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（月 1 往復）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s13_idx13_tom_q400.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q400_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q400_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q400_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s13_idx13_tom_q400.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q400 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: McConnell・Xu 2008 FAJ: 米株の超過リターンは月替わり 4 日（−1〜+3）に集中し、国際指数にもある（Lakonishok・Smidt 1988 の窓）。Etula ほか 2020 RFS は月末の資金需要（dash for cash）を機構にする。暦は入力基準で明示的に可のデータ源で、手元の過去検証は Girgin の「前倒し窓」（Q181・Q284〜Q286）だけで古典窓そのものの関門判定は無い。13 指数を同じ暦で持てば月 4 日×13 本の露出で規程モードの t が出るか。main=(−1,+3)。副=(−4,+3)（前倒し窓を含めた参照）
- 測るもの: 等金額: 13 指数の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈4/21）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）
- 帰無: 合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「turn-of-the-month effect international stock indices after 2010 out-of-sample McConnell Xu Etula dash for cash」: Aalto 修士論文（43 か国 1990〜2012・37 か国で検出・サブ期間で米・スイス等は消失）、SSRN 2011（マレーシア・韓国・日本）、20 か国 GARCH 研究。2010 年以後の 13 指数 CFD・日次・規程つきの判定は未確認。修士論文は参考にとどめる
- 捨てた案の数: 3（月末前の空売り（dash for cash の負の窓）＝窓の位置が文献で一定でない／FX・商品を足す＝Q286 で株固有と判明／暦日で数える＝休場日で崩れる）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副窓・銘柄別は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8

## 結果

未実行。
