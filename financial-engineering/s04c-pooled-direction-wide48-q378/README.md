# Q378 48 銘柄プールの翌 5 日リターン予測（リッジ→GBM・特徴量 3 組・変換 3 通り・格子 36・PBO）は規程モードの封印前の前後半で S07 本体とゼロをコスト後に上回り年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q378 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 5 本目（S04c 本体））。出典: [[検証/_基盤/戦略台帳]] S04c／[[Bailey2017-1_期間内の最良が期間外で中央値より下になる割合でバックテストの過剰適合の確率を測れる]]／[[Arnott2019-1_試した数と選ばなかった設定を数えないと2シグマは基準にならない]]

- スクリプト: `kensho_s04c_pooled_direction_q378.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04c_pooled_direction_q378.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04c_pooled_direction_q378.py`（B=20。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q378_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q378_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q378_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04c_pooled_direction_q378.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q378 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 48 銘柄プールの翌 5 日リターン予測（mom/vol/range/dow・t まで）を clip 変換した main=(all, ridge α=1, clip) の規程モード損益が、評価期間（2012〜2024-06）の前後半とも S07 等リスク TSMOM60 とゼロをコスト後に上回る
- 測るもの: main の規程モード前後半の年単位 t・mean_bp・max_dd・worst_day・stops・Sharpe。S07・ゼロの同じ鍵。IC（年ごと・日次 nw_t）。36 試行の TrialLog・PBO
- 帰無: ラベル並べ替え（学習窓の目的変数を年内で並べ替えて学習し直す）B=20 → main の規程モード mean_bp の帰無分布 → z・perm_p
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「pooled cross-asset machine learning return prediction futures ridge gradient boosting walk-forward trend following benchmark」: arXiv 2607.00475（16 先物のパラメトリック方策・AI は単純規則に勝つか）、Wang・Zhang 2024 JFM（22 商品・LightGBM 月次）。48 銘柄 D1 プール×リッジ→GBM×規程モード×TSMOM ベースラインの追試は見つからない
- 捨てた案の数: 3（xsec 族・σ60 で割った目的・NN）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行。n_trials=36・pbo・B を JSON で確認）

## 判定（事前固定）

支持: main が前後半とも mean_bp で S07 本体を上回り（かつ >0）、t_pre≥2 かつ t_post≥2、max_dd≥−6%、ラベル並べ替え perm_p<0.05、PBO<0.5。棄却: main が前後半のどちらかで S07 本体を上回らない、または帰無 z<1。ほか → 未確定

## 結果

未実行。
