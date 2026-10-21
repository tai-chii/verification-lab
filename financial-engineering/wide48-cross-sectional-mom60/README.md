# Q371 48 銘柄 wide48 の D1 横断モメンタム L=60（上位1/3買い・下位1/3売り）は封印前の前後半とも年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q371 の行（Opus・/lab-plan ターミナル版 2026-10-21・N=5 の 5 本目（S07 横断））。出典: [[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード系統 [[Asness・Moskowitz・Pedersen 2013 Value and Momentum Everywhere JF]]

- スクリプト: `kensho_wide48_cross_mom60_q371.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_wide48_cross_mom60_q371.py --readme` でこの README を再生成）
- データ: 48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/、それ以外は 検証/_データ/raw/D1/。ok<40 ならデータ待ちで exit 2（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_wide48_cross_mom60_q371.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q371_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q371_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q371_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Opus）とコード（Opus）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_wide48_cross_mom60_q371.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q371 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 各日 t に過去 L=60 日の log リターン ret_L[t,sym] で銘柄をランク付けし、上位 1/3 を +1、下位 1/3 を −1、残り 0。pos[t,sym] の等重き束の年単位 bp が pre（〜2016 末）・post（2017〜2024-06）とも t≥2
- 測るもの: 全48銘柄プール（等重き）の年単位 bp・t・束ねた t・Sharpe・最大下落・露出
- 帰無: 横断ランク pos（±1/0・連続日は保持）を各銘柄独立に循環シフト（min_shift=120・B=500）→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-21「cross-sectional momentum top bottom quintile multi-asset Asness Moskowitz Pedersen value everywhere」。Asness・Moskowitz・Pedersen 2013（JF）が8資産クラスの横断で value/momentum を確認。既存の自検 [[15銘柄の日足で横断モメンタムと時系列モメンタムの差は前後半ともt2未満で...]]（Q約230）は 15 銘柄で差なしの未確定。48 銘柄×2008〜2024-06×独立追試は見つからない
- 捨てた案の数: 0（S07 の横断版・5本中5本目。長短配分は 1/3 固定、L は 60 固定で掃引しない）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Opus 設計 → Opus 実行）

## 判定（事前固定）

pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか → 未確定

## 結果

実行 2026-10-22（Sonnet・B=500）。`results/Q371_result_20261022_013949.json`。48 銘柄すべて year_sym に入っている（`data_health.no_data` は DATA_DIR だけを見るので無視）。ギャップは US500・USTECH・WTI の 2011 年の数か月で、この 3 銘柄を除いても同じ（pre t=-0.40・post t=-2.52）。`years_dropped` なし・`null_degenerate` false・n_tests=2 と一致。

| 期間 | bp_gross | bp_net | t_year(net) | z | p_holm |
|---|---|---|---|---|---|
| 全期間 | 0.70 | -1.58 | -1.87 | 1.81 | - |
| pre | 0.78 | -0.49 | -0.36 | 2.48 | 0.020 |
| post | 0.62 | -2.56 | -2.50 | -0.11 | 0.563 |

グロスは t≈1.0 で弱く、コスト後は負。帰無もコスト分で負側（q025≈-3）に寄るため、pre の z・p が大きく見えるのは帰無との相対で、ネットの優位ではない。支持の条件（bp_net>0）を満たさず、棄却の条件（全期間 z<1）にも当たらない。

判定: **未確定**（解釈: 横断モメンタム L=60 はコスト後に優位なし・支持されず）

## 再判定（Q384・2026-10-22・Sonnet・コスト修正後）

`Runner._cost` の既定（COST_RT に無い銘柄＝往復 30 bp）をスプレッド実測の中央値に直した後、同じスクリプト・同じ B=500 で再実行。結果: `results/Q371_result_20261022_044538.json`（旧 JSON は `results/` に残してある）。

| 項目 | 値（bp/日・全期間） |
|---|---|
| bp_gross | 0.554 |
| bp_net | -0.173 |
| pre bp_net／post bp_net | +0.48／-0.76 |
| 全期間 z | 1.26 |
| rule_mode.gate.pass | False（t_pre≥2・t_post≥2・max_dd≤6% のいずれも未達） |

- 全期間 z=1.26。旧は pre z=2.48・Holm p=0.02 だったが新は z=1.54・p=0.120（旧の有意は 30bp 既定のコストが帰無側に効いた人工物）。post net は -0.76 で負
- 注: 旧結果との粗利の差はコストではなく、データ更新で 2026 年の銘柄×年の行が増えたため（共通の行の粗利は旧と一致）。`data_health` の no_data は DATA_DIR しか見ない既知の誤報で、`year_sym.csv` は 48 銘柄。

判定: **未確定**（判定は旧と同じ。コスト修正で粗利は変わらず、純損益の符号と z だけが動いた）
