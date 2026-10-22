# Q397 48 銘柄 D1 で実測スプレッドの 5 日平均 z は翌 5 日の実現ボラ／σ60 の比を予測するか（σ60 に無い情報・年単位 IC の t）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q397 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・N=10 の 4 本目（S11・前提））。出典: [[検証/_基盤/戦略台帳]] 新 S11（スプレッド）／Bollerslev・Melvin 1994 JIE（ボラ → スプレッド）／Q396（スプレッドゲートの前提）／S04b Q387（HAR の σ̂ は σ60 に勝てず）

- スクリプト: `kensho_s11_spread_vol_ic_q397.py`（`fe_core` 土台を直接使う型。事前登録の内容は冒頭 docstring と `SPEC` dict に固定）
- データ: 48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01・`検証/_データ/raw/D1`）＋ `spread_<sym>.csv`（日次 bid/ask 終値 → 往復スプレッド／価格比）。無い銘柄は除いて JSON の `missing`・`no_spread` に。欠損の点検は JSON の `data_health`
- 実行: `python3 kensho_s11_spread_vol_ic_q397.py`（B=500。pandas/numpy のみ。wide48 の D1 が 40 本未満なら `status=データ待ち` を書いて exit 2）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q397_result_<日時>.json`（`main`（all/pre/post の IC 平均・年単位 t・z・perm_p・Holm）・`ic_by_year`・`ref_vol_momentum`（σ20/σ60 の参照 IC）・`per_sym_ic`・`data_health`・機械判定 `machine_verdict`）

## 状態（2026-10-22）

**設計とコードまで。実行と解釈は未。** コードは `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、docstring の【仮説】【判定】【捨てた案の数】【知識の締め切り】【委託の確かめ方】を読んでから走らせる（変更しない）。
2. `python3 kensho_s11_spread_vol_ic_q397.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、アイデア候補の状態、検証キュー Q397 を完了へ、`gen_fe_index.py` で一覧を更新。Q396（ゲート）の解釈にこの結果を添える。

## 方法（要点）

- 仮説: スプレッドはマーケットメイカーの在庫リスクの予想を映す。逆向き（スプレッド → 将来ボラ）が σ60 を超えて残るなら、スプレッドは OHLCV に無いボラ情報を持ち、Q396 のゲートや S04b 型のサイジングの部品になる。x[t]＝直近 5 日のスプレッド平均を 250 日で z 化、y[t]＝sqrt(mean(ret[t+1..t+5]²))／σ60[t]
- 測るもの: 年ごとに全銘柄の (x, y) を束ねたスピアマン IC（年 × 1 本）の平均と t（全期間・前半 <2017・後半）、参照 IC（σ20/σ60）、銘柄別 IC（記述）
- 帰無: 銘柄ごと・年内で x を並べ替え（perm_within・B=500）→ 年単位 IC 平均の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）
- 多重比較: 判定は 2 本（前後半・Holm で補正）。参照・銘柄別は記述。S11 の族内試行は Q396（2 設定）・Q397（1 本）＝3
- 先行研究チェック: WebSearch 2026-10-22「bid-ask spread predicts future realized volatility FX daily data incremental to GARCH HAR」: Bollerslev・Melvin 1994、Wei 1991、Bissoondoyal-Bheenick ほか 2016 はいずれもボラ → スプレッドの向き。スプレッド → 将来の相対ボラの予測力の判定は未確認
- 捨てた案の数: 2（y を実現ボラの水準にする＝σ60 と同じ情報を測ってしまう／HAR を対照にする＝Q387 で σ60 に負けたので σ60 で足りる）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 前後半とも IC の年単位 t≥2 かつ Holm 後 p<0.05 かつ IC 平均>0。棄却: 全期間の年単位 t<1 または z<1。ほか → 未確定。参照 IC・銘柄別は記述。

## 結果

未実行。
