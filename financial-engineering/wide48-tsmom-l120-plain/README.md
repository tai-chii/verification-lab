# Q369 48 銘柄 wide48 の D1 プレーン TSMOM L=120（約6ヶ月・ボラ正規化なし）は封印前の前後半とも年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q369 の行（Opus・/lab-plan ターミナル版 2026-10-21・N=5 の 3 本目（S07 L=120））。出典: [[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード [[Moskowitz2012-1_時系列モメンタムは12か月の予測力を持ち58先物のすべてで正]]

- スクリプト: `kensho_wide48_tsmom_l120_q369.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_wide48_tsmom_l120_q369.py --readme` でこの README を再生成）
- データ: 48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/、それ以外は 検証/_データ/raw/D1/。ok<40 ならデータ待ちで exit 2（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_wide48_tsmom_l120_q369.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q369_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q369_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q369_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Opus）とコード（Opus）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_wide48_tsmom_l120_q369.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q369 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t] = sign(close[t]−close[t−120])。全48銘柄を等重みで束ね、pre（〜2016 末）・post（2017〜2024-06）とも年単位 t≥2
- 測るもの: 全48銘柄プール（等重み）の年単位 bp・t・束ねた t・Sharpe・最大下落・露出
- 帰無: 合図（±1/0）を循環シフト（min_shift=180・B=500）→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-21「time-series momentum 120-day 6-month lookback trend-following robustness」。Hurst・Ooi・Pedersen 2017 の 1/3/12 ヶ月束に 3ヶ月（約60日）が含まれるが、6ヶ月単独はAlpha Architect の Trend-Following refresh（2023）で頑健性チェックの一部。48 銘柄×6ヶ月単独×封印前の独立追試は見つからない
- 捨てた案の数: 0（S07 の L 掃引3本の2本目。試行は本体＋L∈{60,120,250}＋横断の5本に固定）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Opus 設計 → Sonnet 実行）

## 判定（事前固定）

pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか → 未確定

## 結果

実行 2026-10-22（結果 `results/Q369_result_20261022_010434.json`。01:03 の初回と同一内容）。48 銘柄すべて計算（`missing: []`）。

| 区間 | 年数 | bp_net | t_year | z | p_holm |
|---|---|---|---|---|---|
| 全期間 | 19 | 0.19 | 0.23 | 1.38 | — |
| pre（〜2016） | 9 | 0.76 | 0.49 | 1.75 | 0.080 |
| post（2017〜） | 10 | −0.32 | −0.47 | 0.02 | 0.505 |

- gross は全期間 1.00bp（t_gross 1.34）で小さく、コスト後は pre・post とも t_year が 2 から遠い。帰無は退化なし（null_degenerate=false）、years_dropped なし、gap_bars は 16/175761。
- **data_health の注意**: `fe_core.data.check_data_health` が `DATA_DIR` しか見ず（`data_path` を使わない）、`_データ/raw/D1` の 34 銘柄が `no_data` と出る。報告だけの不具合で、計算には全48が使われた（CSV の sym=48）。欠損月は別途確認: US500・USTECH・EUSTX50・HKG33・NLD25（46 か月）・USTBOND（12 か月）・WTI・BRENT・JPN225・SUI20・UK100 などに欠け。gap 行は損益から除かれている。`tools/fe_core/` は直さない決まりなので、修正は別行で。
- 事前登録からの変更点: なし。

判定: **未確定**（機械判定と同じ。規則上は「ほか」。実質は pre・post とも年単位 t≪2 で仮説の「両方 t≥2」は成り立たない。Q368 の L=60 と同様に、プレーン TSMOM の幅広プールは小さな gross を持つが検出力不足）

## 再判定（Q384・2026-10-22・Sonnet・コスト修正後）

`Runner._cost` の既定（COST_RT に無い銘柄＝往復 30 bp）をスプレッド実測の中央値に直した後、同じスクリプト・同じ B=500 で再実行。結果: `results/Q369_result_20261022_044334.json`（旧 JSON は `results/` に残してある）。

| 項目 | 値（bp/日・全期間） |
|---|---|
| bp_gross | 0.917 |
| bp_net | 0.716 |
| pre bp_net／post bp_net | +1.33／+0.16 |
| 全期間 z | 1.31 |
| rule_mode.gate.pass | False（t_pre≥2・t_post≥2・max_dd≤6% のいずれも未達） |

- pre z=1.68・Holm p=0.108、post z=-0.16。旧: net +0.19・post net -0.32 → 新: net +0.72・post +0.16。年単位 t は 0.90／0.30 で t≥2 に遠い
- 注: 旧結果との粗利の差はコストではなく、データ更新で 2026 年の銘柄×年の行が増えたため（共通の行の粗利は旧と一致）。`data_health` の no_data は DATA_DIR しか見ない既知の誤報で、`year_sym.csv` は 48 銘柄。

判定: **未確定**（判定は旧と同じ。コスト修正で粗利は変わらず、純損益の符号と z だけが動いた）
