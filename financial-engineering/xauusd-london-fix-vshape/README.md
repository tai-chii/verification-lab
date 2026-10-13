# Q289 XAUUSD の WM/Reuters ロンドン fix（16:00 UTC）の前後に V 字はあるか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q289 の行（Claude Opus 4.7・10案一括生成 ターミナル版 2026-10-14）。出典: [[Krohn2024-1_ドルはフィキシングに向けて上がりその後に下がり一日の中でW字になる]]

- スクリプト: `kensho_xauusd_london_fix_vshape_q289.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: XAUUSD H1_dukascopy、2008〜2026-06（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_xauusd_london_fix_vshape_q289.py`（B=2000・約 1 分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q289_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q289_year_sym_<日時>.csv`

## 状態（2026-10-14）

**設計とコードまで。実行と解釈は未**
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_xauusd_london_fix_vshape_q289.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、検証キュー Q289 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: XAUUSD H1 の 15:00〜16:00 UTC（fix 直前 1 時間）の log リターンは正、16:00〜17:00 UTC（fix 直後 1 時間）の log リターンは負、D = pre − post > 0。前後半（2008-2016／2017-2026）とも |z|≥2 かつ符号が仮説どおり。
- 測るもの: D の年単位 t と z（全期間・前後半）、pre と post それぞれの平均。
- 帰無: 日ごとに pre/post のラベルを入れ替える（符号並べ替え）B=2000 → D の帰無分布 → z。
- 多重比較: 判定は 2 本（Holm で補正、m=2）。
- 先行研究チェック: WebSearch 2026-10-14・英語・"WM Reuters 4pm London gold fix behaviour around fixing time intraday hourly pattern XAUUSD"。Krohn 2024 と Evans 2018 の fix 周り、BIS 2022 Mueller スライド。XAUUSD 単独の 4pm fix の V 字検証は未確認（移植）。
- 捨てた案の数: 約4: (i) FX6 で既に Q268 がある、(ii) 15 分足（XAUUSD H1 のみ）、(iii) 月末だけ（Q229 と混ざる）、(iv) PM fix（10:30 UTC は時刻が暗黙）。
- 知識の締め切り: Claude の知識はおよそ 2026-06。本データの終端も 2026-06。
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 前後半とも D>0 かつ z≥2。棄却: 全期間 z<1。それ以外: 未確定。

## 結果

未実行。
