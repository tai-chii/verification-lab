# Q368 48 銘柄 wide48 の D1 プレーン TSMOM L=60（ボラ正規化なし・等重み）は封印前の前後半とも年単位 t≥2 か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q368 の行（Opus・/lab-plan ターミナル版 2026-10-21・N=5 の 2 本目（S07 L=60 プレーン））。出典: [[検証/_基盤/戦略台帳]] S07（2026-10-21・方針D）／主張カード [[Moskowitz2012-1_時系列モメンタムは12か月の予測力を持ち58先物のすべてで正]]

- スクリプト: `kensho_wide48_tsmom_l60_q368.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_wide48_tsmom_l60_q368.py --readme` でこの README を再生成）
- データ: 48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は 検証/学問/金融工学/作業/FX/システムトレード/、それ以外は 検証/_データ/raw/D1/。ok<40 ならデータ待ちで exit 2（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_wide48_tsmom_l60_q368.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q368_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q368_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q368_year_sym_<日時>.csv`

## 状態（2026-10-21）

**設計（Opus）とコード（Opus）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_wide48_tsmom_l60_q368.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q368 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t] = sign(close[t]−close[t−60])。全48銘柄を等重みで束ね、pre（〜2016 末）・post（2017〜2024-06）とも年単位 t≥2
- 測るもの: 全48銘柄プール（等重み）の年単位 bp・t・束ねた t・Sharpe・最大下落・露出
- 帰無: 合図（±1/0）を循環シフト（min_shift=120・B=500）→ 全48銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-21「time-series momentum 60-day lookback multi-asset futures replication」。60日はMoskowitz2012（1〜12か月で正）に含まれるが短期側で、Garleanu・Pedersen 2024（arXiv 2507.15876）のCTA replication は10/20/40/60日の束を使う。48 銘柄×ボラ正規化なしの封印前の独立追試は見つからない
- 捨てた案の数: 0（S07 の L 掃引3本の1本目。本体仕様はそのままで試行は本体＋L∈{60,120,250}＋横断の5本に固定）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Opus 設計 → Sonnet 実行）

## 判定（事前固定）

pre・post とも bp_net>0 かつ Holm 補正後 p<0.05 → 支持。全期間 z<1 → 棄却。ほか → 未確定

## 結果（2026-10-22・Sonnet・B=500・48 銘柄すべて計算に使用）

- 全期間: bp_net −0.66・bp_gross +0.52・t_year −0.93・Sharpe_net 0.01・z 0.43（帰無 2.5〜97.5 点 −1.87〜0.10・退化なし）・p_perm 0.35
- pre（〜2016）: bp_net −1.00・t −1.20・z −0.10・Holm p 0.55。post（2017〜）: bp_net −0.36・t −0.31・z 0.64・Holm p 0.55
- 3 銘柄（US500・USTECH・WTI）を除いても pre −1.06（t −1.25）・post −0.69（t −0.68）で符号は変わらない
- 注意: JSON の `data_health` は fe_core `health()` が `DATA_DIR` しか見ず（`DATA_DIR2` を見ない）、34 銘柄が `no_data` と出る。計算自体は 48 銘柄を使っている（year_sym.csv で確認）が、この 34 銘柄の欠損点検は未実施。`failed` は 0。
- 付記: 同じ日に `--B 2` の確認実行を 1 回余計に走らせた（`results/*_010146/010147`）。判定には使わない。

判定: **棄却**（事前規則「全期間 z<1」。pre・post とも gross はほぼ 0、コスト後は負。年単位 t≥2 には遠い）

