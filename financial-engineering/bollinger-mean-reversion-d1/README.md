# Q293 15 銘柄 D1 のボリンジャー平均回帰（+2σ 売り・−2σ 買い、SMA20 戻りで決済）は all15 の年単位平均 bp（コスト後）が前後半とも正か（Coakley2016-2 の D1 移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q293 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Coakley2016-2_ボリンジャーとRSIのルールはFX22通貨で補正後も両期間に残った]]。関連: 知見「先進国通貨の日足テクニカルは2016年以降も補正後に有意なルールが0本」(Hsu 系)。

- スクリプト: `kensho_bollinger_mean_reversion_d1_q293.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_bollinger_mean_reversion_d1_q293.py --readme` でこの README を再生成）
- データ: 15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_bollinger_mean_reversion_d1_q293.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q293_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q293_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q293_year_sym_<日時>.csv`

## 状態（2026-10-14）

**実行と解釈まで完了。判定: 棄却**（Claude Opus 4.7 自動運転・Mac で B=500 実行、1 分弱）。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_bollinger_mean_reversion_d1_q293.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q293 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: Bollinger(20, 2σ) の mean-reversion（終値が上バンドを超えたら −1、下バンドを割ったら +1、SMA20 戻りで 0）は、all15 の年単位平均 bp（コスト後）が前後半とも >0。
- 測るもの: all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。
- 帰無: 合図の循環シフト（min_shift=60）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"Bollinger Bands mean reversion daily FX 15 assets cross-section Holm correction"。見つかったもの: 実務ブログの Bollinger mean reversion 解説（Interactive Brokers、Luxalgo など）。未確認: 15 銘柄 D1 でボリンジャー 20・2σ の mean-reversion を循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。
- 捨てた案の数: 約4: (i) 窓 10 日・50 日（Coakley の既定 20 日に揃える）、(ii) 1.5σ・3σ（Coakley の 2σ に揃える）、(iii) 順張り版（Bollinger breakout は別仮説）、(iv) FX のみ（Coakley は FX22 通貨だが手元は 15 銘柄パネル）。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05。棄却: 全期間 z<1。ほか: 未確定。多重比較は pre/post の 2 本（Holm で m=2）。

## 結果

判定: **棄却**（事前固定「全期間 z<1 → 棄却」に合致。コスト前も bp_net<0 で単純に効かない）。

- all15 全期間（n_bars=66,082・n_years=19・gap_bars=8・years_dropped=[]）: bp_gross=-0.419、bp_net=-0.6013、t_year=-1.023、t_cluster=-1.306、Sharpe_net=-0.28、max_dd_net=-15,258 bp、露出=0.515、z=-0.6559、p_perm=0.7345、帰無 q025..q975=[-1.149, +0.585]、null_degenerate=False。
- pre（2008–2016・n_years=9・gap_bars=8）: bp_net=-0.5366、t_cluster=-0.933、Sharpe_net=-0.30、z=-0.6232、p_perm=0.7226、p_holm=1.0。
- post（2017–2026-06・n_years=10・gap_bars=0）: bp_net=-0.6595、t_cluster=-1.093、Sharpe_net=-0.31、z=-0.3444、p_perm=0.6407、p_holm=1.0。
- data_health: ok 全 15 銘柄・failed 空・no_data 空。gaps は WTI(3 月)・UKOIL(7 月)・US500(4 月)・USTECH(4 月) いずれも 2011-2014 で pre 期間のみ。gap_bars は pre の 8 本（0.03%）で結論に影響なし。post は独立に bp_net<0・z<0。
- 多重比較: main_param=0・all15 の pre/post 2 本（Holm m=2）。宣言どおり n_tests=2。

**読み方**: Bollinger(20, 2σ) の mean-reversion 1 本を 15 銘柄 D1・2008-2026 で測ると、コスト前後ともシグナルが負（しかも粗利でも ≈ 0）で、循環シフト帰無の中央値（-0.3 bp 付近）に対して観測値は右裾でも左裾でもない。Coakley2016-2 の「ボリンジャーは FX22 通貨・両期間で補正後も有意」は 15 銘柄 D1・SMA20 戻り決済・片道段階1コストでは再現しない。Hsu 系の知見「先進国通貨の日足テクニカルは 2016 年以降 0 本」の延長（12 ルール取り合わせの 1 本ずつ検定ではなく、代表 1 本のパネル検定）に積み重なった。

結果: `results/Q293_result_20261014_015221.json`。帰無分布は null_degenerate=False、両期間とも null_q025 と null_q975 が符号をまたぎ、観測値が内側に収まる＝「ランダムに合図をずらしたものと見分けがつかない」。
