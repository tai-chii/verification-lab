# Q367 48 銘柄 wide48 の D1 TSMOM60（σ60 ボラ正規化・等リスク束）は封印前（〜2024-06）の前後半とも年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q367 の行（Opus・/lab-plan ターミナル版 2026-10-21・N=5 の 1 本目（S07 本体））。出典: [[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード [[Moskowitz2012-1_時系列モメンタムは12か月の予測力を持ち58先物のすべてで正]]（原典 Moskowitz・Ooi・Pedersen 2012）

- スクリプト: `kensho_wide48_tsmom60_voltarget_q367.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_wide48_tsmom60_voltarget_q367.py --readme` でこの README を再生成）
- データ: 48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/data_*_D1_fromH1.csv、それ以外は 検証/_データ/raw/D1/data_*_D1_fromH1.csv。ok<40 ならデータ待ちで実行しない（status=データ待ち で exit 2）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_wide48_tsmom60_voltarget_q367.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q367_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q367_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q367_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Opus）とコード（Opus）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_wide48_tsmom60_voltarget_q367.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q367 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t] = sign(close[t]−close[t−60]) × target_vol/σ60[t]（target_vol=0.10 年率、σ60 は直近 60 本の日次 log リターンの標準偏差を年率化）。等重みで全銘柄を束ね、pre（〜2016 末）・post（2017〜2024-06）とも年単位 t≥2
- 測るもの: 全48銘柄プール（等重み）の年単位平均 bp（コスト0と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。族別（fx22/idx13/cmd8/bond3）の寄与は extra に記述（判定には使わない）
- 帰無: 合図（±target_vol/σ60 の連続量）を各銘柄独立に循環シフト（min_shift=120・B=500）→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-21「Moskowitz Ooi Pedersen time series momentum 58 futures volatility scaling 2012」で原典 Moskowitz・Ooi・Pedersen (2012, JFE) と後継（Baltas・Kosowski 2020、Garleanu・Pedersen 2024 arXiv 2507.15876 CTA replication）を確認。48 銘柄×σ60 ボラ正規化×等リスク束の封印前 2008〜2024-06 期間での独立追試は見つからない（原典は 1965〜2009）
- 捨てた案の数: 0（S07 の最初の実装。本体仕様はそのままで試行は本体＋L∈{60,120,250}＋横断の5本に固定）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Opus 設計 → Sonnet 実行）

## 判定（事前固定）

pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか（符号条件・t 条件のどちらかで未達） → 未確定

## 結果

実行 2026-10-22（Sonnet・B=500・48 銘柄すべて D1 読込）。結果: `results/Q367_result_20261022_010001.json`

| 区間 | bp_gross | bp_net | 年単位 t(net) | z | Holm p |
|---|---|---|---|---|---|
| 全期間(19年) | 0.52 | -0.70 | -1.71 | 0.62 | - |
| pre(〜2016) | 0.72 | -0.34 | -0.48 | 1.03 | 0.307 |
| post(2017〜2024-06) | 0.34 | -1.02 | -2.21 | -0.54 | 0.701 |

- 粗利は小さく正（Sharpe_gross 0.30）だがコスト後は負（Sharpe_net -0.28）。年単位 t≥2 は pre・post とも未達。
- 点検: `data_health` の `no_data` 34 銘柄は H1 健全性チェックの対象外（D1 は 48 すべて読めている・族別 n_syms 22/13/8/3 で確認）。failed なし。gaps は US500・USTECH・WTI の 2011 年の欠け（数か月）。この 3 銘柄を除いても pre -0.37（t -0.52）・post -1.24（t -2.85）で結論は変わらない。`null_degenerate`=false・`years_dropped`=[]・n_tests=2 一致。
- 族別: fx22 の post が -2.3bp（t -5.3）と最も悪い。idx13 は pre -1.6bp（t -2.1）・post +0.2bp。
- 成績が悪い方向の結果で、リーク疑いの合図（良すぎる成績・期間で符号反転の大きな食い違い）には当たらないため Opus 見直しは不要。

判定: **棄却**（全期間 z=0.62<1。事前固定の規則どおり）


## 再判定（Q384・2026-10-22・Sonnet・コスト修正後）

`Runner._cost` の既定（COST_RT に無い銘柄＝往復 30 bp）をスプレッド実測の中央値に直した後、同じスクリプト・同じ B=500 で再実行。結果: `results/Q367_result_20261022_044131.json`（旧 JSON は `results/` に残してある）。

| 項目 | 値（bp/日・全期間） |
|---|---|
| bp_gross | 0.420 |
| bp_net | 0.215 |
| pre bp_net／post bp_net | +0.54／-0.08 |
| 全期間 z | 0.36 |
| rule_mode.gate.pass | False（t_pre≥2・t_post≥2・max_dd≤6% のいずれも未達） |

- 全期間 z=0.36<1。旧: net -0.70・post t -2.21 → 新: net +0.22・post t -0.23
- 注: 旧結果との粗利の差はコストではなく、データ更新で 2026 年の銘柄×年の行が増えたため（共通の行の粗利は旧と一致）。`data_health` の no_data は DATA_DIR しか見ない既知の誤報で、`year_sym.csv` は 48 銘柄。

判定: **棄却**（判定は旧と同じ。コスト修正で粗利は変わらず、純損益の符号と z だけが動いた）
