# Q380 翌 5 日リターン予測で回帰目的（ret）と符号分類目的（sign）はどちらが IC・コスト後損益が高いか（リッジ回帰・GBM 回帰・GBM 分類・リッジ符号回帰の 4 試行）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q380 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 7 本目（S04c 前提））。出典: [[検証/_基盤/戦略台帳]] S04c／知見 Q307 系（向きの精度と損益は別）／arXiv 2607.09426

- スクリプト: `kensho_s04c_reg_vs_clf_q380.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04c_reg_vs_clf_q380.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04c_reg_vs_clf_q380.py`（B=20。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q380_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q380_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q380_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は済（2026-10-22）。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04c_reg_vs_clf_q380.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q380 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 符号分類（p̂−0.5 をスコア）は回帰より雑音を追わない分だけ IC が高く規程モード損益も高い。逆なら大きさの情報が規模に効く
- 測るもの: 4 本の IC（年・日次 nw_t）・分類の AUC・規程モード（t_pre/t_post・mean_bp・max_dd・Sharpe）。ridge の分類−回帰の年ごと IC 差の年単位 t
- 帰無: main（ridge 回帰）のラベル並べ替え B=20。比較は年ごと IC 差の年単位 t
- 多重比較: 判定は 1 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「classification versus regression return prediction machine learning trading direction sign profitability comparison」: arXiv 2607.09426（暗号先物・回帰と分類を別々に評価）、Adegboye ほか 2021 ESA（FX の方向転換）。同じ特徴量・同じ変換で両目的を損益まで比べた統制比較は見つからない
- 捨てた案の数: 1（三値分類）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

分類が勝つ: ridge の分類−回帰の年ごと IC 差が年単位 t≥2 かつ前後半とも分類の mean_bp>回帰。回帰が勝つ: 逆向きに同条件。どちらでもない → 未確定（差は無いと記述）

## 結果

実行 2026-10-22（Mac・Sonnet・B=20・48 銘柄読み込み。`data_health.no_data` は DATA_DIR のみを見るので無視。gaps は US500／USTECH／WTI の 2011 年内の欠損で除外版は未計算）。結果: `results/Q380_result_20261022_045100.json`

- ridge 分類−回帰の年ごと IC 差: 平均 +0.0006、年単位 t=0.09（13 年。符号は年により入れ替わる）。損益は後半のみ分類>回帰（mean_bp_post −1.55 vs −1.63）、前半は回帰>分類（−1.60 vs −0.94）。判定条件は満たさない。
- 全 4 試行がコスト後マイナス（mean_bp −1.4〜−1.8、gate 全部不合格）。main のラベル並べ替え帰無 z=0.78・perm_p=0.14（B=20）、PBO=0.66。
- 記述: GBM 分類だけ IC が正（ic_all 0.0106・年単位 t=2.80・日次 nw_t=2.09・AUC 0.505）だがコスト後は −1.47bp。多重比較・B=20 を考えると信頼できない（探索的）。

判定: **未確定（差は無い）**
