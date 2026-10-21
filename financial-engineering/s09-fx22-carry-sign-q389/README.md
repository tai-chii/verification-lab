# Q389 FX22 D1 のキャリー単独（政策金利差の符号で高金利通貨を買う・スワップ＝金利差 − 年 0.75% マークアップを損益に含む）は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q389 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=4 の 1 本目（S09・キャリー単独））。出典: [[検証/_基盤/戦略台帳]] S09（入力基準の改定 2026-10-22・最初に足すデータ源＝キャリー）／Koijen・Moskowitz・Pedersen・Vrugt 2018 'Carry' JFE／Lustig・Roussanov・Verdelhan 2011 RFS／Burnside・Eichenbaum・Rebelo 2011（NBER w16942）／S07 Q367（FX22 スワップなし TSMOM 棄却）

- スクリプト: `kensho_s09_fx22_carry_sign_q389.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s09_fx22_carry_sign_q389.py --readme` でこの README を再生成）
- データ: FX22（8 通貨の 22 ペア）の D1_fromH1（2010-01〜・封印 time<2024-07-01）。政策金利: 検証/_データ/raw/rates/policy_<CCY>.csv（BIS WS_CBPOL・実施日ベース・8 通貨）。時刻 t の金利差は t−1 暦日に実施中の値。スワップ: held×金利差×暦日数/365（週末またぎ 3 日）、マークアップ年 0.75% は常に払う。コスト: FX8 は COST_RT（往復 2 pips）、14 クロスは spread_<sym>.csv の中央値（Runner の既定）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s09_fx22_carry_sign_q389.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q389_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q389_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q389_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s09_fx22_carry_sign_q389.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q389 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: OHLCV だけの D1 順張りは FX22 で粗利 ≈0（S07）。FX で最も頑健な要因キャリー（高金利通貨の買い持ち）は OHLCV から出ないので、政策金利差の符号 sign(i_base − i_quote) をそのまま建玉にすると、値動き＋スワップの総収益がコスト（スプレッド＋マークアップ）後に正で、規程モードの関門を通る。main=帯なし（band 0）。副=|金利差|≤0.5pp は持たない（band 0.5）
- 測るもの: 等金額: 22 ペアの年単位平均 bp（gross＝値動き＋金利差／net＝−スプレッド−マークアップ）・年単位 t・束ねた t・Sharpe・最大下落、値動き／スワップ／マークアップの分解（extra.decomposition_main）。規程モード: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（スワップ込みと no_swap の両方）
- 帰無: 銘柄ごとの符号反転（各ペアの pos に独立な ±1・B=500。金利差の向きは総収益の向きを知らない、が帰無）→ 等金額の年単位 bp の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）。循環シフトは符号が年単位で動かないキャリーでは帰無が観測と一致しうるため使わない
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「currency carry trade sign of policy rate differential daily rebalancing G10 pairs transaction costs returns after 2010 out-of-sample」: Georges 2014 の G10 金利差戦略の再現（bsic.it・2011 以降に効かなくなった）、Jurek 2014（暴落リスクが超過収益の約 1/3）、NTU 論文（上位 3・下位 3 の G10 キャリーの標本外）、Reuters 2026-05（先進国キャリーは金融危機後に稼いでいないという Citi の談）。22 ペア・ペア単位の符号・日次・プロップ規程・封印つきの判定は未確認。ブログ（bsic）は根拠にしない
- 捨てた案の数: 3（3 か月金利・フォワードポイントを源にする＝未取得／通貨レベルで上位 3・下位 3 を組む＝ペアへの写像が一意でない／マークアップを 0.5〜1% で掃引＝固定して感度は事後に記述）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main band 0・スワップ込み）の全期間 z≥2（銘柄ごとの符号反転帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。スワップ抜き（no_swap）・band 0.5・銘柄別は記述（判定に使わない）。S09 の族内試行は Q389〜Q392 の 4 本×2 設定＝8 本と数える

## 結果

未実行。
