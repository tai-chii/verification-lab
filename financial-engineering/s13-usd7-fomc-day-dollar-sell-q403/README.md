# Q403 対ドル 7 ペア（EURUSD・GBPUSD・AUDUSD・NZDUSD・USDJPY・USDCHF・USDCAD）で FOMC 定例発表日にドルを売る（当日の足 1 本・年 8 回）戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q403 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 10 本目（S13・FOMC 日のドル売り））。出典: [[検証/_基盤/戦略台帳]] 新 S13（暦）／Mueller・Tahbaz-Salehi・Vedolin 2017 'Exchange rates and monetary policy uncertainty' JF 72(3)／Lucca・Moench 2015 JF／Q401（株側）

- スクリプト: `kensho_s13_fomc_dollar_q403.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s13_fomc_dollar_q403.py --readme` でこの README を再生成）
- データ: 対ドル 7 ペアの D1_fromH1（2010〜・封印 time<2024-07-01。NZDUSD は _データ/raw/D1）。USD が quote のペア（EURUSD 等）は +1、USD が base のペア（USDJPY 等）は −1。コスト: FX8 の 6 本は COST_RT（往復 2 pips）、NZDUSD は spread_<sym>.csv の中央値（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s13_fomc_dollar_q403.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q403_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q403_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q403_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s13_fomc_dollar_q403.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q403 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Mueller・Tahbaz-Salehi・Vedolin 2017 JF: ドル売り・他通貨買いは定例 FOMC 発表日に有意に大きい超過収益を得る（金融政策の不確実性への対価。金利差の大きい通貨・緩和局面でさらに大きい）。暦だけで決まる 1 日の建玉で、年 8 回しか出入りしないのでコストは小さい。main=当日の足 1 本（前日終値→当日終値）、副=前日と当日の 2 本
- 測るもの: 等金額: 7 ペアの年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈8/252）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）
- 帰無: 合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「dollar depreciates on FOMC announcement days currency excess returns Mueller Tahbaz-Salehi Vedolin after 2015」: 原著（JF 2017・LSE/Warwick の版）。標本期間の末尾と 2015 年以後の有無は要旨から確認できず、7 ペア・2010〜・D1・規程つきの判定は未確認
- 捨てた案の数: 3（金利差で重みを付ける＝S09 の部品を混ぜない／H1 で 14:00 ET 前後を切る＝対ドル 7 ペアの H1 は FX8 分しか無く NZDUSD が欠ける／スワップ込み＝1 日の保有では無視できる）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）。FOMC の暦は Claude の知識から記載（s1x.FOMC_DATES）。**実行者は federalreserve.gov と照合し、違えば --fomc-csv で差し替える**

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副 2 本・銘柄別は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8

## 結果

実行: `results/Q403_result_20261022_145954.json`（B=500・7 ペア ok・failed／gaps なし・years_dropped なし・null_degenerate なし・n_tests=2 一致）。FOMC 暦は federalreserve.gov と Q401・Q402 の実行者が 2010〜2026 の全年を照合済み（全一致・2020-03 の臨時会合は除外）。

| 項目 | 全期間 | 前半(〜2016) | 後半(2017〜) |
|---|---|---|---|
| 等金額 main(当日ドル売り) net bp/日 | 0.30 | −0.03 | 0.59 |
| 年単位 t | 1.72 | −0.10 | 3.49 |
| 循環シフト z（Holm p） | **5.74** | 0.50（0.32） | 8.21（0.004） |
| 規程モード(fintokei) t | 1.63 | −0.17 | 3.32 |

露出 3%（FOMC 日 1 本 ≈ 1 ペア 1 日あたり 平均 約 +10 bp／後半 約 +20 bp、前半 ≈ 0）。規程モード fintokei: max_dd −11.6%（基準 −6% 超過）・stops 1。副（前日＋当日）は全期間 net 0.24bp・t_year 1.16（当日だけより弱い）。ペア別の年合計 net（単位は bp 合計）は USDJPY 0.9 が最小で他は 2.4〜6.6。年別は 2014 が −9.9 と突出して負、2023・2024 が正に突出。

判定: **未確定**（機械判定と同じ）。等金額の全期間 z=5.74 は支持側だが、前半 t=−0.10（z=0.5）・規程の max_dd −11.6% で関門は不通過。棄却条件（全期間 z<1、t_all<0）には当たらない。

**Sonnet 実行のため結論は書かず Opus 見直し（escalate）へ**: 前半と後半で大きさが大きく変わる（前半 ≈ 0、後半に集中）。「公表後に消えた」ではなく逆向きで、後半（特に 2022〜2024）が強い。2014 年の負と 2023〜24 年の正が全体を動かしており、期間依存・FOMC の暦の機構（2022 以後の利上げ局面）・多重比較（S13 族 8 本）を点検してから判断する。
