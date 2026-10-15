# Q300 7 通貨の強度ランキングの最強−最弱スプレッド（4H・L=30 本・ボラ正規化）の上位五分位は、翌 6 本（1 日）の合成リターンがコスト後に継続か反転か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q300 の行（Fable・3案一括生成 通貨強度 第1弾 2026-10-15）。出典: taichi と ChatGPT の壁打ち（2026-10-15・Top×Bottom の強度スプレッド案）。Fable の整理: Menkhoff-Sarno-Schmeling-Schrimpf (2012, JFE) の通貨クロスセクション・モメンタムの 4H 移植。関連: 知見 Q218・Q208・[[Neely2003-3_為替のトレンドは週次月次では強いが日中足にはない]]。前提の整合性は Q299

- スクリプト: `kensho_currency_strength_spread_q300.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: 対ドル 6 本（EURUSD・GBPUSD・AUDUSD・USDJPY・USDCHF・USDCAD）H1_dukascopy、2008〜2026-06 → 時刻を内部結合 → UTC 4 時間境界の行だけを 4H の観測点にする（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は `missing`、欠損の点検は `data_health`）
- 実行: `python3 kensho_currency_strength_spread_q300.py`（B=500・数分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke --B 5`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q300_result_<日時>.json`（設定・`main`（主設定の前後半 z・perm_p・Holm）・`grid`（L×N×q×期間）・`data_health`・機械判定 `machine_verdict`）・`results/Q300_grid_<日時>.csv`

## 状態（2026-10-15）

**実行済み・棄却。2026-10-15 Fable（担当 opus 扱い）。**
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. Q299 の結果を先に見る（クロスが冗長でなければ、この検証の強度の定義（対ドル 6 本のみ）に注記が要る）。
3. `python3 kensho_currency_strength_spread_q300.py` を Mac で実行。
4. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く。`data_health` に failed／gaps があれば除いた結果も見る。`years_dropped`・`null_degenerate` も確かめる。`grid` の q=1..5 の単調性（`spearman_q_fwd`）と、主設定以外の 8 通りの (L,N) の符号の揃い方を記述に書く（判定には使わない）。
5. 記録先: 知見ノート、アイデア候補の状態、FX 改善ログ、検証キュー Q300 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説（両側）: 主設定（L=30 本・N=6 本・スプレッド上位五分位 q=5）で、最強通貨買い・最弱通貨売りの合成リターン（段階1コスト後・bp）の年単位平均が、前後半とも同符号で Holm 補正後 p<0.05。正なら継続（弱いものがさらに弱くなる）、負なら反転。
- 定義: 対ドル対数価格 P_c（USD=0）。L 行リターンを各ペアの 4H 対数リターンの直前 120 行 std × sqrt(L) で割り、7 通貨で中心化 → 強度。top=argmax・bot=argmin・sp=差。分位は直前 500 行の分布（先読みなし）。fwd=合成の N 行先リターン（bp）。コストは USD 以外の脚ごとに COST_RT 往復（最大 2 脚・クロスを直接使わない保守値）。
- 測るもの: (L∈{6,30,120}) × (N∈{1,6,24}) × (q∈{1..5, 全体}) × (all/pre/post) の net の年単位平均 bp・年単位 t・NW t（ラグ N）・件数、q と fwd の Spearman。
- 帰無: (top,bot,q) のラベル列の循環シフト（min_shift=500 行）→ 同じ規則で net → B=500 → 主設定 q=5 の年単位 bp の分布。両側 perm_p。
- 多重比較: 判定は主設定の前後半 2 本（Holm m=2）。ほかの 8 (L,N) × q は記述。
- 先行研究チェック: WebSearch 2026-10-15・英語・"cross-sectional currency momentum intraday hourly 4-hour long strongest short weakest currency reversal study"。Menkhoff ほか (2012) Currency Momentum Strategies（月次）、Aalto 修論「Momentary loss: The disappearance of cross-sectional currency momentum」、Krohn-Mueller-Whelan (2018) FX Premia Around the Clock。7 通貨の 4H 強度ランキングで最強−最弱スプレッドの分位別に翌 1 日の条件付き期待値を循環シフト帰無で判定した実証は未確認（移植: 月次 → 4H）。
- 捨てた案の数: 約5: (i) 事後の分位（先読み）、(ii) 2 対 1 ルール（3 通貨のみ）、(iii) Core/Satellite、(iv) クロス込み最小二乗、(v) ML。
- 知識の締め切り: Claude の知識はおよそ 2026-06。本データの終端も 2026-06。
- 委託の確かめ方: 設計は Fable、コードは Fable（--smoke のみ）、実行と解釈は後の /lab（Opus）。委託なし。

## 判定（事前固定）

主設定（L=30・N=6・q=5）の年単位 bp_net: 支持（継続）: pre・post とも >0 かつ Holm 補正後 p<0.05。支持（反転）: pre・post とも <0 かつ Holm 補正後 p<0.05。棄却: 全期間の |z|<1。未確定: ほか（符号が前後半で割れる場合を含む）。

## 結果

判定: **棄却**（事前固定「全期間の |z|<1」に合致。z=−0.67・両側 perm_p=0.51・pre/post Holm 後 p=0.51／0.57）

- 4H 行数 28,654（対ドル 6 本の内部結合）。data_health: failed なし・gaps なし。帰無は退化なし（q025..q975 = [−7.6, +0.5] と、コストぶん負に寄った分布の中に観測値 −4.8 が入る）。
- 主設定（L=30・N=6・q=5・n=5,860）: bp_gross=−1.41・bp_net=−4.78・t_year=−1.48。pre −7.62（z=−1.16）・post −2.21（z=+0.60）。コスト以前にほぼ 0 で、コスト（2 脚で約 3.3 bp）を引くと負。
- 単調性: q（乖離の五分位）と先行リターンの Spearman は 9 通りの (L,N) すべてで負（−0.006〜−0.028）。乖離が大きいほど続きにくく、わずかに反転寄り。
- 掃引（記述）: 粗利が最も負なのは L=120・N=24・q=5（bp_gross=−12.6・t_year=−2.1、pre −17.4・post −8.3 と同符号）。長い窓・長い保有で「最強買い最弱売り」は逆に動く（短期反転の方向）が、主設定ではなく事前固定の判定には使わない。N=1（4 時間）は全 q で粗利 ≈ 0・コスト後 −3〜−4 bp。
- 無条件（q=0・全観測）でも粗利は −0.2〜−3.6 bp で、通貨クロスセクション・モメンタムは 4H〜1 日の時間軸には無い。Neely2003-3「為替のトレンドは週次月次では強いが日中足にはない」と整合、Menkhoff 2012 の月次モメンタムは 4H に移植できない。
- 結果: `results/Q300_result_20261015_115031.json`・`results/Q300_grid_*.csv`
