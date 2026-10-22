# Q402 株価指数 13 の FOMC サイクル偶数週（定例発表日を 0 として −1〜+3・+9〜+13・+19〜+23・+29〜+33 営業日）だけ買い持ちする戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q402 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 9 本目（S13・FOMC サイクル））。出典: [[検証/_基盤/戦略台帳]] 新 S13（暦）／Cieslak・Morse・Vissing-Jorgensen 2019 'Stock returns over the FOMC cycle' JF 74(5)／Lucca・Moench 2015 JF／Q401（週 0 の前半）

- スクリプト: `kensho_s13_fomc_cycle_q402.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s13_fomc_cycle_q402.py --readme` でこの README を再生成）
- データ: 指数 13 の D1_fromH1（2010〜・封印 time<2024-07-01）。サイクル日は各銘柄の足で数えた直前の発表日からの営業日数（発表前日は −1）。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（週ごとの出入りで年 ≈16 往復）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s13_fomc_cycle_q402.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q402_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q402_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q402_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s13_fomc_cycle_q402.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q402 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Cieslak・Morse・Vissing-Jorgensen 2019 JF: 1994〜2016 の株式プレミアムは FOMC サイクルの偶数週にだけ発生し（奇数週は ≈0）、3 つのサブ期間と米国外の株式市場でも成り立つ（Fed の非公式な情報流出の 2 週周期）。暦（FOMC 日程）だけで決まり判断時点に既知。13 指数・2010〜封印前で偶数週買い（露出 ≈1/2）が関門を通るか。main=偶数週だけ買い、副=偶数週買い・奇数週（4〜8・14〜18・24〜28）売り
- 測るもの: 等金額: 13 指数の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈1/2）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）。extra: 偶数週・奇数週それぞれの平均日次リターン（bp）
- 帰無: 合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「FOMC cycle even weeks stock returns Cieslak Morse Vissing-Jorgensen out-of-sample after 2015 replication」: 原著（1994〜2016・国際にも）、AEA 2021 の派生（週の機構）。2016 年以後の標本外・国際 13 指数・日次 CFD・規程つきの判定は未確認（独立の追試は見つからず）
- 捨てた案の数: 2（週 0 を 0〜4 にずらす＝原著の −1〜3 に固定／偶数週のうち週 0 だけ＝Q401 と重なる）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）。FOMC の暦は Claude の知識から記載（s1x.FOMC_DATES）。**実行者は federalreserve.gov と照合し、違えば --fomc-csv で差し替える**

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副（long/short）・銘柄別・偶数週と奇数週の bp の差は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8

## 結果

未実行。
