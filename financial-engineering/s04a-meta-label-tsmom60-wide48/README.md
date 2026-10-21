# Q374 48 銘柄 D1 の TSMOM60 合図にメタラベリング（k=5・族 mom/vol/range/dow・リッジ→GBM・予測→規模 3 通り・格子 27）を重ねると、規程モードの封印前の前後半で S07 本体とゼロをコスト後に上回り年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q374 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 1 本目（S04a 本体））。出典: [[検証/_基盤/戦略台帳]] S04a／López de Prado 2018 AFML ch.3／[[Bailey2017-1_期間内の最良が期間外で中央値より下になる割合でバックテストの過剰適合の確率を測れる]]

- スクリプト: `kensho_s04a_meta_label_q374.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04a_meta_label_q374.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01 で切る）。既存 15 銘柄は FX/システムトレード、それ以外は 検証/_データ/raw/D1。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04a_meta_label_q374.py`（B=20。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q374_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q374_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q374_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04a_meta_label_q374.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q374 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: メタラベル y=1{TSMOM60 に乗った t→t+5 の損益>0} を特徴量（t まで）で予測し p̂→乗る規模 [0,1]×合図。main=(all, ridge α=1, clip) の規程モード損益が評価期間（2012〜2024-06）の前後半とも S07 等リスク TSMOM60 とゼロをコスト後に上回る
- 測るもの: main の規程モード（RULES_FINTOKEI）: 前半 2012〜2016・後半 2017〜2024-06 の年単位 t・mean_bp・max_dd・worst_day・stops・Sharpe。同じ鍵で S07 本体（等リスク TSMOM60）とゼロ。IC・AUC・等金額版・27 試行の TrialLog・PBO（CSCV S=8）
- 帰無: ラベル並べ替え（学習窓のメタラベルを年内で並べ替えて学習し直す）B=20 → main の規程モード mean_bp の帰無分布 → z・perm_p
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「meta-labeling time series momentum trend following gradient boosting futures bet sizing」: 近いのは Nousiainen 2022（Donchian × RF・サイズを確率で）、Insper の meta-labeling 追試（改善は弱い）、Lim・Zohren・Roberts 2019 DMN（深層でサイズ学習）。48 銘柄 D1・TSMOM60・規程モード（固定最大損失）の下での独立追試は見つからない
- 捨てた案の数: 3（GBM を main にする・k=20・負の規模を許す）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行。trials n=27・pbo・B を JSON で確認）

## 判定（事前固定）

支持: main の規程モードが前後半とも mean_bp で S07 本体を上回り（かつ >0）、t_pre≥2 かつ t_post≥2、max_dd≥−6%、ラベル並べ替え perm_p<0.05、PBO<0.5。棄却: main が前後半のどちらかで S07 本体を上回らない、または帰無 z<1。ほか → 未確定

## 結果

2026-10-22 Sonnet 実行（`results/Q374_result_20261022_014053.json`・B=20・23 秒）。48 銘柄すべて読めた（`n_syms`=48・`missing`=[]。`data_health.no_data` の 34 件は DATA_DIR しか見ない既知の表示で、データ待ちではない）。gaps は US500/USTECH/WTI の 2011 年の欠けのみで評価期間（2012〜）にはほぼ影響なし。`null_degenerate`=false・trials n=27・PBO=0.21。

- main（all|ridge:1|clip）規程モード mean_bp: 前半 +0.31（S07 +0.50）・後半 −2.05（S07 −1.49）。t_pre=0.32・t_post=−4.99・max_dd −46%・stops 4。**前後半とも S07 本体を下回る**（ゼロも後半は下回る）。27 格子のどれも t_pre≥2 に届かず、規程モードの mean_bp は全て負（−0.85〜−1.65）。
- 帰無（ラベル並べ替え）: 帰無中央 −1.68 に対し main −1.25、z=1.47・perm_p=0.14（有意でない）。規程なしでは main +0.53bp（t=0.77）で S07 +0.69bp とほぼ同じ。
- 予測力は弱いがある: IC 0.034（年単位 t=3.37）・AUC 0.52。ただし損益に変換できていない（コスト・規程の損切りで消える）。
- メモ: spec の n_tests=2 と JSON の「判定は main 1 本」が不一致だが、棄却は Holm 前の素の条件で成立するので判定に影響しない。

判定: **棄却**（事前固定の棄却条件「前後半のどちらかで S07 本体を上回らない」に該当。機械判定と同じ）

