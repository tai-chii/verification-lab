# Q398 FX22 D1 で政策金利差（base − quote）の 90 暦日変化の符号で持つ（金利モメンタム・スワップ込み）戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q398 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 5 本目（S12・金利モメンタム））。出典: [[検証/_基盤/戦略台帳]] 新 S12（金利の変化＝S09 と同じデータ源・別の族）／Chung・Hong 2007 'Model-free evaluation of directional predictability in foreign exchange markets' JAE／Molodtsova・Papell 2009 JIE（テイラールール基礎）／S09 Q389（水準の符号は円の局面に依存）

- スクリプト: `kensho_s12_rate_momentum_q398.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s12_rate_momentum_q398.py --readme` でこの README を再生成）
- データ: FX22 の D1_fromH1（2010-01〜・封印 time<2024-07-01）＋ 政策金利 policy_<CCY>.csv（BIS・8 通貨）。時刻 t の金利差は t−1 暦日、D 日前の値は t−1−D 暦日に実施中の値。スワップ・マークアップ（年 0.75%）・コストは S09 と同じ（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s12_rate_momentum_q398.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q398_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q398_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q398_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s12_rate_momentum_q398.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q398 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 中央銀行の利上げ・利下げは連続する（政策サイクル）ので、金利差の「変化」は持続し、為替はその向きにゆっくり動く（Chung・Hong 2007 JAE: 金利差の履歴が為替の方向を予測）。S09 の水準（キャリー）は円の局面に寄ったが、変化の向きは通貨をまたいで入れ替わるので局面依存が薄い。pos = sign(diff[t] − diff[t−D])、変化 0 なら持たない。main D=90、副 D=180
- 測るもの: 等金額: 22 ペアの年単位 bp（スワップ込み net／抜き）・t・束ねた t・Sharpe・最大下落・露出（変化 0 の期間は 0）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（スワップ込み・no_swap）。分解（値動き／スワップ／マークアップ）
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（スワップ込み net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「change in interest rate differential momentum predicts exchange rate returns monetary policy cycle currency strategy "rate momentum"」: Chung・Hong 2007（金利差の履歴に方向の予測力）、HHS 'Economic momentum and currency returns'（経済モメンタムがキャリーを包含）、BCB WP 630（金利差の弾力性はレジーム依存）。金利差の変化の符号をそのまま建玉にした日次・スワップ込み・規程つきの判定は未確認
- 捨てた案の数: 3（変更イベント後 20 日だけ持つ＝イベント型で別 ID／キャリー符号と変化の符号の一致＝S09 は閉じたので合成しない／3 か月金利の変化＝未取得）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モード（RULES_FINTOKEI・スワップ込み・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main D=90・スワップ込み）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。スワップ抜き（no_swap）・D=180・銘柄別は記述。S12 の族内試行は Q398・Q399 の 2 本×2 設定＝4

## 結果

未実行。
