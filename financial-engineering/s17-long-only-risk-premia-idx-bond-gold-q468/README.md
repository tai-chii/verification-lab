# Q468 S17 多資産ロングオンリー（株価指数 10＋債券 2＋金）の等リスク買い持ちは、保有コスト年 4% 込みで C1 関門（規程モード σ0.25%/日・封印前の前後半 t≥2・max_dd −6% 以内）を通るか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q468 の行（Fable・/lab-plan 2026-10-23（Fable・★C1 決定後・N=1））。出典: [[検証/_基盤/戦略台帳]] S17（2026-10-23・★C1 後の最初の S・族は新規「リスクプレミアム」）／Harvey・Hoyle・Korgaonkar・Rattray・Sargaison・van Hemert 2018「The Impact of Volatility Targeting」(JPM)／Boyd ほか「Simple Dynamic Stock/Bond/Gold Portfolios」(Stanford)／Q416・Q428（C1 の通過確率）

- スクリプト: `kensho_s17_long_only_rp_q468.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s17_long_only_rp_q468.py --readme` でこの README を再生成）
- データ: 13 銘柄 D1（検証/_データ/raw/D1 の IDX10＋BUND・UKGILT、XAUUSD は既存 15 銘柄）。2012-02-01〜2024-06-30（封印は Spec.end で切る・2026-10-23 実装）。債券 2 本は 2016-05／2017-12 開始なので前半はほぼ指数＋金だけ（記述に残す）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s17_long_only_rp_q468.py`（B=0。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q468_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q468_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q468_year_sym_<日時>.csv`

## 状態（2026-10-23）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s17_long_only_rp_q468.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q468 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t]=+1（常時買い持ち）。規模は規程モード（size_weights: σ60 で 1 銘柄 3σ=1.5% 上限・ポート σ 目標 0.25%/日・レバ 2・日次 −2.5% 停止）が決める。株式・債券・金のリスクプレミアムは正で、等リスク束は分散で下落が浅くなる（Harvey ほか 2018 のボラ目標、Boyd ほかの株・債券・金）。封印前（2012-02〜2024-06）の前後半（境 2017）とも規程モード年単位 t≥2、max_dd ≥ −6%
- 測るもの: 規程モード C1 の年単位 t（all/pre/post）・mean_bp・σ・max_dd・worst_day・stops（判定）。等金額の年単位 bp・t・Sharpe（記述）。extra: 族別（idx/bond/gold）の年単位 bp と t、保有コスト 7% は --hold 0.07 で別 JSON
- 帰無: none。常時 +1 の合図は循環シフトで不変なので帰無分布を作らない。検定は年単位 t（pre 5 年・post 7.5 年）
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-23「multi-asset long-only risk parity equity bond gold volatility targeting Sharpe ratio 2010-2024 evidence」: Harvey ほか 2018（ボラ目標は株式・クレジットでシャープを上げ、債券・商品では効果が小さい）、Boyd ほか（株・債券・金の単純な動的配分）。未確認: CFD の保有コスト込み・プロップの固定最大損失（−6%）の下での通過可否、および 2012〜2024-06 の前後半分割での再現。ブログ（Quantpedia 要約）は根拠にしない
- 捨てた案の数: 3（族内の試行は params の 3 本に固定・掃引しない）。捨てた案: 全 48 銘柄の買い持ち（FX・商品は無条件の正のプレミアムが無い）、NLD25/EUSTX50/HKG33/USTBOND を含める（穴が年 ±20〜165 bp を作る・S13 の記録）、2010 年開始（US500/USTECH の 2011-12 の穴を跨ぐ）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行 → Opus 見直し）。実行者は data_health の gaps と year_sym の 2012〜13 を見て穴の混入が無いことだけ点検する

## 判定（事前固定）

判定は規程モード（rule_set=fintokei_c1・保有コスト 4% 込み）の main_param=0 のみ。gate.pass（t_pre≥2 かつ t_post≥2 かつ max_dd≥−6%）→ 支持。規程モード t_all<1 または max_dd<−10% → 棄却。ほか → 未確定。等金額（RULES_NONE）の数字・params 1〜2（指数のみ／指数＋金）・保有コスト 7% は記述で判定に使わない。帰無は none（常時買い持ちは循環シフトで変わらないため）。年単位 t が検定

## 結果

未実行。
