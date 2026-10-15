# Q301 強度スプレッドの合図のエントリーをロンドン・NY 重複帯（NY 8〜12 時・8:30 ET の足の確定後）に限ると、1 トレードのコスト後期待値は即時エントリーとランダム時間窓の帰無を上回るか（全体／前半 3 時間・H1 執行・24 時間保有）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q301 の行（Fable・3案一括生成 通貨強度 第1弾 2026-10-15）。出典: taichi と ChatGPT の壁打ち（2026-10-15・「4H で方向、1H で流動性の高い時間帯に入る」案。taichi の決定: 重複帯 JST 21〜26 時、8:30 ET 前後 15 分は一律回避、窓は全体と前半 3 時間）。関連: 知見 Q211・[[Seeck2026-1_ロンドン開始30分の日中モメンタムは円の組で約3.8倍強く期間外でも有意]]・[[Krohn2024-1_ドルはフィキシングに向けて上がりその後に下がり一日の中でW字になる]]。合図は Q300 の主設定と同じ

- スクリプト: `kensho_currency_strength_session_q301.py`（`fe_core` 土台を直接使う型。事前登録の内容は docstring に固定）
- データ: 対ドル 6 本 H1_dukascopy、2008〜2026-06 → 時刻を内部結合。NY 現地時刻は `tz_convert("America/New_York")`（夏時間を自動で扱う）（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は `missing`、欠損の点検は `data_health`）
- 実行: `python3 kensho_currency_strength_session_q301.py`（B=500・数分。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke --B 5`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q301_result_<日時>.json`（設定・`models`（A/B/C × all/pre/post）・`tests`（B・C の帰無・Holm）・`hourly_24h_net_by_ny_hour`・`data_health`・機械判定 `machine_verdict`）・`results/Q301_models_<日時>.csv`・`results/Q301_hourly_<日時>.csv`

## 状態（2026-10-15）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 20` の経路確認だけ済み（合成データ・判定には使わない）。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. Q300 の結果を先に見る（Q300 が棄却でも時間帯で条件付き期待値が変わるかは別の問いなので、この検証は走らせる）。
3. `python3 kensho_currency_strength_session_q301.py` を Mac で実行。
4. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く。`data_health` に failed／gaps があれば除いた結果も見る。`years_dropped`・`null_degenerate`・`n_trades`（窓を限ると件数が減る）も確かめる。`hourly_24h_net_by_ny_hour` で窓の後半（NY 11 時台＝ロンドンフィックス付近）が落ちていないかを記述に書く。
5. 記録先: 知見ノート、アイデア候補の状態、FX 改善ログ、検証キュー Q301 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 重複帯「全体」（B: 足の開始が NY 8〜11 時台＝確定 9〜12 時 NY）の 1 トレードのコスト後 bp（年単位平均）が、pre・post とも即時エントリー（A: 4H 境界で入る）より大きく、「毎日ランダムな開始時刻の同じ幅の窓」の帰無に対し Holm 補正後 p<0.05。C（前半 3 時間: NY 8〜10 時台）は同じ検定を出すが記述。
- 定義: 状態は Q300 の主設定（4H 境界で L=30・ボラ正規化・直前 500 行の五分位）を次の境界まで H1 に引き継ぐ。合図 = q=5。執行は足の確定で建て、24 行後の確定で手仕舞い。保有中は入らない。コストは USD 以外の脚ごとに COST_RT 往復。指標の除外（簡易版）: 8:30 ET は NY 8 時台の足の中なので、B・C の最初のエントリー（その足の確定＝9:00 NY）は発表 30 分後。A の 12:00 UTC（夏の 8:00 NY）は発表 30 分前で ±15 分の外。
- 測るもの: A/B/C × all/pre/post の 1 トレード net bp（年単位平均・t）、件数、勝率、1 暦日あたり bp。補助: q=5 の全 H1 行の NY 時刻別 24h 先 net（再入制限なし）。
- 帰無: 毎日（NY 現地日）の開始時刻 h0〜U{0..23} の幅 4（B）／3（C）の窓で同じ規則 → 1 トレード bp の年単位平均 → B=500。片側 greater。
- 多重比較: 判定は B の pre/post の 2 本。Holm は B・C × pre/post の 4 本（m=4）。A・時刻別は記述。
- 先行研究チェック: WebSearch 2026-10-15・英語・"FX momentum returns by trading session London New York overlap intraday predictability time-of-day study"。Krohn-Mueller-Whelan (2018) FX Premia Around the Clock、Andersen-Bollerslev 系の日中ボラ周期性、実務ブログ（根拠にしない）。強度スプレッドの合図を重複帯に限ったときの 1 トレード期待値をランダム窓の帰無と比べた実証は未確認（条件の穴）。
- 捨てた案の数: 約4: (i) 指標カレンダー取り込み（丁寧版）、(ii) 東京時間の窓、(iii) 1H 強度の変化を特徴量に（ML 段階）、(iv) 固定 JST の窓。
- 知識の締め切り: Claude の知識はおよそ 2026-06。本データの終端も 2026-06。
- 委託の確かめ方: 設計は Fable、コードは Fable（--smoke のみ）、実行と解釈は後の /lab（Opus）。委託なし。

## 判定（事前固定）

支持: B の pre・post とも bp_net_per_trade > A の同期間 かつ Holm 補正後 p<0.05（m=4）。棄却: B の全期間の z<1。未確定: ほか。

## 結果

未実行。
