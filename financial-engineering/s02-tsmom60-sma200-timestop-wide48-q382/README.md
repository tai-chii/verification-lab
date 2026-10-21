# Q382 48 銘柄 D1 の TSMOM60 × SMA200 同符号ゲート × 時間ストップ 20 日の合成（部品は既存値で固定・掃引なし）は規程モードの封印前の前後半で t≥2 かつ最大下落 −6% 以内か

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q382 の行（Fable・/lab-plan ターミナル版 2026-10-22・N=10 の 9 本目（S02 合成））。出典: [[検証/_基盤/戦略台帳]] S02／知見 [[日足順張りの建玉を直前60日の実現ボラの逆数で規模調整すると年ごとのシャープが約0.09上がる]]（Q205 確定）／知見 [[株価指数の200日線と12か月モメンタムの保有現金規則だけが同じ露出の無作為なタイミングより最大下落が浅く、商品と為替では下落の軽さは露出の低さで説明できる]]（Q151 確定）／Q251（時間ストップは下落を浅くするが純損益は上げない・支持）

- スクリプト: `kensho_s02_composite_q382.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_s02_composite_q382.py --readme` でこの README を再生成）
- データ: 48 銘柄 D1（FX22＋IDX13＋CMD8＋BOND3＋CRYPTO2）。既存 15 銘柄は FX/システムトレード、それ以外は 検証/_データ/raw/D1。ok<40 ならデータ待ちで exit 2。コスト: 段階1 COST_RT（価格単位）＋COST_RT に無い wide48 の 34 銘柄は _s04_common/s04ml.py の WIDE48_COST_REL（往復・比。知識から記載・実行者が 検証/_データ/raw/D1/spread_<sym>.csv と照合）。既定（fe_core）だとこの 34 銘柄は往復 30bp に落ちるので使わない（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_s02_composite_q382.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q382_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q382_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q382_year_sym_<日時>.csv`

## 状態（2026-10-22）

**設計（Fable）とコード（Fable）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。****
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_s02_composite_q382.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q382 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: pos[t] = sign(close[t]−close[t−60]) を、sign(close[t]−SMA200[t]) と同符号のときだけ採用（違えば 0）。同じ向きを 20 日持ったら 0 にし、TSMOM60 の符号が反転するまで再建玉しない（Q251 の時間ストップ）。ボラ・ターゲティング（Q205）は規程モードの size_weights（σ60 等リスク・σ目標 0.5%）が当てる。合成の規程モード損益が封印前の前後半とも年単位 t≥2 で、最大下落が −6% 以内
- 測るもの: 生（等金額）の年単位 bp（コスト 0 と段階1）・t・Sharpe・最大下落・露出と、規程モード（rule_mode.fintokei: t_pre/t_post・max_dd・worst_day・stops）。族別（fx22/idx13/cmd8/bond3）は extra に記述
- 帰無: 合図の循環シフト（min_shift=120・B=500）→ 全 48 銘柄プールの年単位 bp の帰無分布 → z・perm_p・Holm
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-22「time series momentum 200-day moving average agreement filter time stop composite multi-asset drawdown」: Quantpedia（商品の絶対トレンドフィルタ）、Alpha Architect（TSMOM の下落）、Antonacci の dual momentum。TSMOM60×SMA200 同符号×時間ストップの 3 部品を 48 銘柄 D1 で合成し固定最大損失の下で測った研究は見つからない
- 捨てた案の数: 2（MA200 を株価指数だけに当てる案＝Q151 の確定範囲だが族で分けると掃引になる、時間ストップ N=10/40＝Q251 の副次）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持: 規程モードの gate.pass（t_pre≥2 かつ t_post≥2 かつ max_dd≥−6%）かつ 生（等金額）の pre・post bp_net>0 かつ Holm 後 p<0.05。棄却: 全期間 z<1、または規程モードの max_dd<−20%（S07 本体 Q367 の −95% と同じ型＝部品で救えない）。ほか → 未確定

## 結果

未実行。
