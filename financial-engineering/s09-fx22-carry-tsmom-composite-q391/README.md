# Q391 FX22 D1 でキャリー符号と TSMOM60 符号が一致したときだけ持つ合成（副: スワップ込み総収益指数の TSMOM60）は、キャリー単独・TSMOM 単独より規程モードの封印前の前後半 t≥2 かつ最大下落 −6% 以内を通りやすいか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q391 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=4 の 3 本目（S09・合成））。出典: [[検証/_基盤/戦略台帳]] S09／Q389（キャリー単独）・Q390（TSMOM＋スワップ）／Koijen ほか 2018 'Carry'／Burnside・Eichenbaum・Rebelo 2011 NBER w16942（キャリーとモメンタムの組合せ）／Moskowitz・Ooi・Pedersen 2012（超過収益の TSMOM）

- スクリプト: `kensho_s09_fx22_carry_tsmom_composite_q391.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s09_fx22_carry_tsmom_composite_q391.py --readme` でこの README を再生成）
- データ: FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨・t−1 暦日の値）。スワップ・マークアップ・コストは Q389 と同じ（_s09_common）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s09_fx22_carry_tsmom_composite_q391.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q391_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q391_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q391_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s09_fx22_carry_tsmom_composite_q391.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q391 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: キャリーの弱点は高金利通貨の急落（暴落リスク）で、順張りの弱点はスワップを払う向きの建玉。両者の符号が一致するときだけ持てば、暴落局面（順張りが売りに転じる）でキャリーの買いを外し、順張りの売りがスワップを払う局面も外れる。合成の規程モードの t と max_dd は Q389・Q390 の main より良い。main=一致ゲート（agree）。副=総収益指数（close×Π(1+金利差·日数/365)）の TSMOM60（tr_mom・Moskowitz 流の超過収益モメンタム）
- 測るもの: 等金額: 22 ペアの年単位 bp（スワップ込み net／抜き）・t・束ねた t・Sharpe・最大下落・露出（一致ゲートは露出が下がる）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（スワップ込み・no_swap）
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（スワップ込み net）の帰無分布 → z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「combining carry and momentum currency strategy agreement filter carry-adjusted momentum total return FX」: Menkhoff ほか 2012（横断モメンタムはキャリーと性質が別）、Alpha Architect の要約（キャリーの直近 3 か月が正のときモメンタムとの相関 0.356・負のとき −0.62）、Burnside ほか 2011（月次のキャリーとモメンタムのポートフォリオ）。符号一致ゲート・総収益指数の TSMOM をペア 22・日次・プロップ規程で測った研究は未確認。Alpha Architect はブログなので根拠にしない
- 捨てた案の数: 3（z スコアの和（連続値）＝規模の学習は S04 の枠／不一致のときキャリー側に従う＝Q389 とほぼ同じ／L を 60・120 で掃引＝族内の本数を増やさない）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main agree・スワップ込み）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。Q389・Q390 との比較（t_pre/t_post/max_dd）は記述であり判定に使わない。tr_mom・銘柄別は記述。S09 の族内試行は Q389〜Q392 の 4 本×2 設定＝8 本

## 結果

未実行。
