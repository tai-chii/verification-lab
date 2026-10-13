# Q291 FX8 H1 の 3 指標（TSMOM24・SMA50・RSI14 符号）が同符号のときだけ売買すると、束ねた t はコスト後に単独 TSMOM24 を上回るか（Loubaris2026-2 の H1 移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q291 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Loubaris2026-2_複数指標の確認は個別指標より的中率が高い傾向があるが有意差なし]]。関連: 知見「15銘柄の日足で3つの順張り指標が同符号のときだけ売買する厳しい一致は的中率も持った日あたりの純損益も最良単独を上回らない」。

- スクリプト: `kensho_fx8_h1_triple_indicator_q291.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_fx8_h1_triple_indicator_q291.py --readme` でこの README を再生成）
- データ: FX8 H1_dukascopy、2008〜2026-06。往復コストは COST_RT 既定。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_fx8_h1_triple_indicator_q291.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q291_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q291_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q291_year_sym_<日時>.csv`

## 状態（2026-10-14）

**完了（棄却）。** 設計・コード・実行・解釈とも Claude Opus 4.7（自動運転）。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_fx8_h1_triple_indicator_q291.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q291 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 3 指標同符号フィルタ（params[1]）は単独 TSMOM24（params[0]）より FX8 プールの年単位平均 bp（段階1コスト後）が高く、前後半とも >0。
- 測るもの: FX8 プール（all グループ）の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。params[0]（単独）と params[1]（フィルタ）を summary で並べる。
- 帰無: 合図の循環シフト（min_shift=72）B=500 → FX8 プール（all）の年単位 bp の帰無分布 → z・perm_p・Holm。
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"multiple indicator confirmation technical trading FX H1 TSMOM SMA RSI agreement filter"。見つかったもの: SMA+RSI 組合せの実務記事（TradingView スクリプト・ブログ）。学術的な FX H1 の TSMOM/SMA/RSI 同符号フィルタの束ねた t 比較は未確認（移植）。
- 捨てた案の数: 約3: (i) 2 指標の交互作用（組合せが増え多重比較の本数が爆発）、(ii) RSI の閾値 30/70（Loubaris は符号による）、(iii) MACD（SMA と相関が高い）。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: フィルタ版が前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05、かつ単独より bp_net が高い。棄却: 全期間 z<1。ほか: 未確定。多重比較は main_param=1 の pre/post の 2 本（Holm で m=2）。

## 結果

判定: **棄却**（事前固定の棄却条件「全期間 z<1」に該当。かつ仮説と逆向きで、フィルタ版は単独より悪い）

結果 JSON: `results/Q291_result_20261014_013842.json`・年×銘柄の表: `results/Q291_year_sym_20261014_013842.csv`。

- データの点検（JSON の `data_health`）: ok 8／no_data 0／failed 0／gaps 0。欠損なし。年落ちなし（19年×8銘柄＝全期間 920,362 bars）。
- 単独 TSMOM24（p0, all）: bp_gross=+0.0303・bp_net=-0.1248・t_year=-6.37・t_cluster=-5.32・Sharpe=-1.20・exposure=0.999。
- 3指標同符号フィルタ（p1, all）: bp_gross=-0.0009・bp_net=-0.1556・t_year=-11.85・t_cluster=-7.23・Sharpe=-1.64・exposure=0.802。
- フィルタの帰無分布（循環シフト, min_shift=72, B=500）: 全期間 z=-0.14・perm_p=0.58・pct=0.42。null_degenerate=False。前後半も z<1（pre: z=0.92・p_holm=0.36／post: z=-1.51・p_holm=0.93）。
- 多重比較: 事前宣言 n_tests=2（main_param=1 の pre/post）、Holm で補正。一致。

要点: フィルタは露出を 100% → 80% に下げると同時に、粗利（bp_gross）を +0.030 → -0.001 まで潰す。つまり「3 指標が全部同じ向きの場面」は TSMOM 単独が稼ぐ場面の中で**特に良い部分集合ではない**。結果、保守的なコスト（COST_RT 既定）を引いた純損益は、フィルタのほうが単独より約 0.03 bp／bar 悪い。Loubaris 2026-2 の 1 市場・500 日・日次での「複数指標の確認は単独より有意に勝たない」という構造が、FX8 H1・19 年・880k バー規模でも方向を同じくして現れた。関連知見（15銘柄 D1 の ALL3 フィルタ）と整合。

**知見**: [[検証/_基盤/知識/知見/15銘柄の日足で3つの順張り指標が同符号のときだけ売買する厳しい一致は的中率も持った日あたりの純損益も最良単独を上回らない]] の FX 列を更新（H1 でも同結論）。
