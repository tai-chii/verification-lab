# Q413 15 銘柄の日次 tick 出来高 z は高値安値レンジ z と冗長か（Spearman）、σ20 とレンジを条件づけても翌 5 日の |ret| を予測するか（出来高に OHLC 以外の情報があるか）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q413 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 3 本目（S14 前提））。出典: [[検証/_基盤/戦略台帳]] 新 S14（出来高）の前提／Blume・Easley・O'Hara 1994 JF／Clark 1973・Tauchen・Pitts 1983（混合分布仮説）／Parkinson 1980

- スクリプト: `kensho_s14_volume_information_q413.py`（`fe_core` 土台を直接使う型。事前登録の内容は冒頭 docstring に固定）
- データ: 15 銘柄 all15 の H1_dukascopy を UTC 0 時区切りで日足に束ねる（volume＝tick 出来高の日次合計。FX8 2008〜・油/指数 2011-09〜・BTC 2017〜。封印 time<2024-07-01）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s14_volume_information_q413.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q413_result_<日時>.json`（銘柄別の相関・IC、年単位 t、帰無、機械判定 `machine_verdict`）・`results/Q413_ic_sym_year_<日時>.csv`

## 状態（2026-10-22）

**設計とコードまで。実行と解釈は未。** コードは `--smoke --B 20` の経路確認だけ済み（合成データ・判定には使わない）。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、冒頭 docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s14_volume_information_q413.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`per_sym.zero_volume_frac_by_year`（出来高の欠け）も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、アイデア候補の状態、検証キュー Q413 を完了へ、`gen_fe_index.py` で一覧を更新。**S14 本体（Q411・Q412）の解釈に使う**: 冗長（棄却）なら Q411・Q412 は実現ボラ族の言い換えとして読む。

## 方法（要点）

- 仮説: 混合分布仮説が強く成り立つなら tick 出来高 z はレンジ z とほぼ同じ情報（相関 ≥0.8）で、S14 の出来高ゲート・加重は実現ボラ族の言い換え。出来高に独立な情報があるなら、レンジ z と σ20 z を取り除いた出来高 z の残差が翌 5 日の |ret|（対数）を正に予測する
- 測るもの: 銘柄ごとの Spearman(vz, rz) と中央値、生 IC・部分 IC（銘柄×年 → 年の中で銘柄平均 → 年単位 t・全期間／前半／後半）、出来高 0 の日の割合（銘柄×年）
- 帰無: 残差 e を年の中で並べ替え（perm_within・銘柄ごと独立・B=500）→ 部分 IC の年単位平均の帰無分布 → z・perm_p（全期間・前半・後半）・Holm（m=2）
- 多重比較: 判定は部分 IC の pre/post の 2 本（Holm で補正）。ほかは記述
- 先行研究チェック: WebSearch 2026-10-22「FX tick volume predicts realized volatility beyond range high-low Dukascopy tick volume information content study」: 学術研究は見つからず（Dukascopy の出来高は SWFX の板の流動性＝1 業者の値、という仕様の記述のみ）。tick 出来高のレンジに対する増分情報は未確認
- 捨てた案の数: 3（翌 1 日の |ret|／出来高の水準そのもの／翌 5 日の符号つき ret）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持（出来高に独立な情報がある）: Spearman(vz, rz) の中央値 <0.6 かつ 部分 IC の年単位 t≥2 が前後半とも かつ 帰無 z≥2。棄却（冗長）: Spearman(vz, rz) の中央値 ≥0.8、または部分 IC の全期間 年単位 t<0。ほか → 未確定。

## 結果

未実行。
