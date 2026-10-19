# Q289 XAUUSD の WM/Reuters ロンドン fix（16:00 UTC）の前後に V 字はあるか

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q289 の行（Claude Opus 4.7・10案一括生成 ターミナル版 2026-10-14）。出典: [[Krohn2024-1_ドルはフィキシングに向けて上がりその後に下がり一日の中でW字になる]]

- スクリプト: `kensho_xauusd_london_fix_vshape_q289.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: XAUUSD H1_dukascopy、2008〜2026-06（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_xauusd_london_fix_vshape_q289.py`（B=2000・約 1 分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q289_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q289_year_sym_<日時>.csv`

## 状態（2026-10-14）

**実行済み（Opus 4.7、2026-10-14 01:23 UTC）。判定は「未確定」**

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

## 結果（2026-10-14 実行、Opus 4.7）

判定: **未確定**（2026-10-19 Q339: 結果 JSON `results/Q289_result_20261014_012340.json` の機械判定を転記。人の解釈は未）
- 主要な数値（JSON より）: 採用 pre.z=-0.3921（D の z（前後半の小さいほう））；pre.z=-0.3921; post.z=-1.0858

結果 JSON: `results/Q289_result_20261014_012340.json`、日次 CSV: `results/Q289_daily_20261014_012340.csv`。

- data_health: XAUUSD は ok（failed なし・gaps なし・n_dup=0）。期間フィルタ後 n_days=4697、n_years=19。
- 全期間（2008-01〜2026-06）: D = pre − post = **−0.74 bp**、t = −1.01、**z = −1.08**、perm_p_two = 0.30。pre = +0.12 bp、post = +0.51 bp。
- 前半（2008-2016）: D = −0.37 bp、z = **−0.39**、perm_p_two = 0.70、Holm 補正後 = 0.70。
- 後半（2017-2026）: D = −1.08 bp、z = **−1.09**、perm_p_two = 0.28、Holm 補正後 = 0.56。
- 対照（10 時台 − 11 時台）: 全期間 D_ctl = −0.96 bp、t = **−1.92**（15/16 時より大きい）。前半 t = **−2.45**。16 時 fix が「特別」とは言えない。

機械判定: `未確定`（全期間 |z|=1.08 で 1 以上 2 未満。前後半も |z|<2）。

**判定: 未確定**

**解釈**: 符号は Krohn 2024（金ではドルの D>0 ⇔ 金の D<0）の予想どおり負だが、|z| が 2 に届かない。前後半でも有意にならない。対照（10 時台 − 11 時台）の方が全期間・前半とも |t| がむしろ大きく、16 時 UTC の fix 周辺に XAUUSD の V 字が「特別に」観測される証拠は乏しい。関連の Q268（ECB 14:15 CET fix・FX6）が V 字を支持したのとは対照的で、XAUUSD H1 への移植では再現しない。
