# Q370 48 銘柄 wide48 の D1 プレーン TSMOM L=250（約12ヶ月・ボラ正規化なし）は封印前の前後半とも年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q370 の行（Opus・/lab-plan ターミナル版 2026-10-21・N=5 の 4 本目（S07 L=250））。出典: [[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード [[Moskowitz2012-1_時系列モメンタムは12か月の予測力を持ち58先物のすべてで正]]

- スクリプト: `kensho_wide48_tsmom_l250_q370.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_wide48_tsmom_l250_q370.py --readme` でこの README を再生成）
- データ: 48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/、それ以外は 検証/_データ/raw/D1/。ok<40 ならデータ待ちで exit 2（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_wide48_tsmom_l250_q370.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q370_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q370_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q370_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Opus）とコード（Opus）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_wide48_tsmom_l250_q370.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q370 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t] = sign(close[t]−close[t−250])。全48銘柄を等重みで束ね、pre（〜2016 末）・post（2017〜2024-06）とも年単位 t≥2
- 測るもの: 全48銘柄プール（等重み）の年単位 bp・t・束ねた t・Sharpe・最大下落・露出
- 帰無: 合図（±1/0）を循環シフト（min_shift=300・B=500）→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-21「time-series momentum 12-month lookback long horizon trend following 250-day」。Moskowitz2012 原典が 12 ヶ月で全58銘柄で正の予測力を報告（最強ホライズン）。post-crisis（2009〜）の後続研究（AQR Insights、Hurst2017）でも 12 ヶ月は頑健。48 銘柄×2008〜2024-06×封印前の独立追試は見つからない
- 捨てた案の数: 0（S07 の L 掃引3本の3本目。試行は本体＋L∈{60,120,250}＋横断の5本に固定）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Opus 設計 → Sonnet 実行）

## 判定（事前固定）

pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか → 未確定

## 結果

未実行。
