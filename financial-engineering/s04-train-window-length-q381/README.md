# Q381 学習窓（4／6／10 年の固定長と拡張）で 48 銘柄プールのリッジ方向予測の年次 IC とコスト後損益は変わるか（6 試行・事前固定 4 年固定長の妥当性）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q381 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 8 本目（S04 前提））。出典: [[検証/_基盤/戦略台帳]] S04／知見 Q326 系／Zhang ほか 2024 arXiv 2406.08041 HARd to Beat

- スクリプト: `kensho_s04_train_window_q381.py`（`fe_core` 土台を直接使う型（fe_core.ml + risk・_s04_common/s04ml.py）。事前登録の内容は `SPEC` に固定。`python3 kensho_s04_train_window_q381.py --readme` でこの README を再生成）
- データ: wide48 D1_fromH1（2008-01〜、封印 2024-07-01）。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s04_train_window_q381.py`（B=20。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q381_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q381_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q381_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s04_train_window_q381.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q381 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 学習窓を長くするほど年ごとの IC の分散は小さくなるが、共通の評価年（2018〜2024-06）の平均 IC と規程モード損益は変わらない＝窓の長さは事前に固定してよい
- 測るもの: 6 本の年ごと IC（平均・標準偏差・年単位 t）と規程モード。共通年 2018〜2024-06 の IC 平均と mean_bp の幅
- 帰無: main（4 年固定長）のラベル並べ替え B=20。比較は共通年の試行間の IC の幅と mean_bp の符号
- 多重比較: 判定は 1 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「rolling versus expanding training window length walk-forward machine learning return prediction stability」: arXiv 2601.08896（NEPSE・XGBoost・両方式）、解説記事多数。多資産 D1 のリッジ方向予測で窓の長さの感度を年次 IC で測った研究は見つからない
- 捨てた案の数: 1（再推定頻度）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持（窓は効かない）: 共通年の年平均 IC の最大−最小が 0.02 未満 かつ 共通年 mean_bp の符号が 6 本で揃う。棄却（窓が効く）: 最大−最小が 0.05 以上、または mean_bp の符号が割れる。ほか → 未確定

## 結果

未実行。
