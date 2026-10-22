# Q401 株価指数 13 の FOMC 前ドリフト（定例発表日の前日の足と当日の足の 2 本を買い持ち・年 8 回）は 2015 年以後も残り、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q401 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 8 本目（S13・FOMC 前））。出典: [[検証/_基盤/戦略台帳]] 新 S13（暦）／Lucca・Moench 2015 'The pre-FOMC announcement drift' JF／Kurov・Wolfe・Gilbert 2021 'The disappearing pre-FOMC announcement drift' FRL／Cieslak・Morse・Vissing-Jorgensen 2019 JF

- スクリプト: `kensho_s13_pre_fomc_q401.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s13_pre_fomc_q401.py --readme` でこの README を再生成）
- データ: 指数 13 の D1_fromH1（2010〜・封印 time<2024-07-01）。FOMC 定例発表日（s1x.FOMC_DATES・知識から記載）。発表日の足が無ければ直後の足を当日とみなす。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（年 8 往復）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s13_pre_fomc_q401.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q401_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q401_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q401_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s13_pre_fomc_q401.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q401 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Lucca・Moench 2015 JF: 1994〜2011 の S&P500 は FOMC 発表前 24 時間に平均 +49 bp（年の超過リターンの大半）で、国際指数にも同じ山がある。Kurov・Wolfe・Gilbert 2021 FRL は 2015 年以後に米国で消えたと報告（不確実性の低下）。国際 13 指数・2010〜封印前で、前半（〜2016）に残り後半（2017〜）に消えるのが文献の予想で、関門を通るには後半も t≥2 が要る。UTC 0 時区切りの D1 では発表（14:00 ET）前 24 時間が前日足と当日足にまたがるので main=2 本（前日・当日）、副=前日 1 本
- 測るもの: 等金額: 13 指数の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈16/252）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）
- 帰無: 合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「pre-FOMC announcement drift disappeared after 2015 international stock indices Lucca Moench Kurov」: 原著（国際指数にも山・Treasury には無し）、Kurov ほか 2021（米国で 2015 以後消失）、quantpedia（IV 高の時だけ 109 bp）。国際 13 指数の 2015 年以後・D1 近似・規程つきの判定は未確認
- 捨てた案の数: 3（H1 で 14:00 ET の前 24 時間を正確に切る＝指数 13 の H1 は手元に無い／VIX 水準で条件付け＝手元に無い／ECB・BoJ の暦を足す＝暦の照合負担が増えるので FOMC だけ）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）。FOMC の暦は Claude の知識から記載（s1x.FOMC_DATES・2010〜2026 定例のみ・2020-03 の緊急は除外）。**実行者は federalreserve.gov の FOMC calendars と照合し、違えば CSV を --fomc-csv で渡す**

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定（文献どおり前半だけ正なら「公表後に消えた」と記述）。副 1 本・銘柄別は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8

## 結果

未実行。
