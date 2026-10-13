# Q292 15 銘柄 D1 の二周期ローテーション規則（L=20 と L=120 の TSMOM が同符号時のみ ±1）は、単独 TSMOM60 より all15 の年単位平均 bp（コスト後）が高いか（Korzan2026-1 の規則の移植）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q292 の行（Claude Opus 4.7（自動運転）・10案一括生成（ターミナル版 2026-10-14））。出典: [[Korzan2026-1_凍結した二周期ローテーション規則の取り置き3年検証は年率22.76パーセントシャープ1.43最大DD11.40でベンチマークを上回った]]。関連: 知見「15銘柄の日足で参照日数20_60_120_250の合図平均は前年までのプールで選んだ最良単一より標本外で前後半とも差のtとzが2未満」(Q253 系)。

- スクリプト: `kensho_dual_lookback_rotation_q292.py`（`fe_core` Runner 型。事前登録の内容は `SPEC` に固定。`python3 kensho_dual_lookback_rotation_q292.py --readme` でこの README を再生成）
- データ: 15 銘柄（SYMS = FX8 + TREND7）D1_fromH1、2008〜2026-06。往復コストは COST_RT 既定。（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_dual_lookback_rotation_q292.py`（B=500。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q292_spec_<日時>.json`（実行前に書かれる事前登録）・`results/Q292_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/Q292_year_sym_<日時>.csv`

## 状態（2026-10-14）

**実行済み（Claude Opus 4.7（自動運転）、Mac 本体）。** B=500、2008〜2026-06、15 銘柄 D1_fromH1。所要 ~12s。
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 kensho_dual_lookback_rotation_q292.py` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー Q292 を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: 二周期ローテーション（params[1]）は単独 TSMOM60（params[0]）より all15 の年単位平均 bp が高く、前後半とも >0。
- 測るもの: all15 の年単位平均 bp（コスト 0 と段階1）、年単位 t、束ねた t、Sharpe、最大下落、露出。params[0]（単独 TSMOM60）と params[1]（二周期）を summary で並べる。
- 帰無: 合図の循環シフト（min_shift=120）B=500 → all15 の年単位 bp の帰無分布 → z・perm_p・Holm。
- 多重比較: 判定は 2 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: WebSearch 2026-10-14・英語・"dual lookback rotation rule time-series momentum 20-day 120-day agreement signal"。見つかったもの: Faber dual momentum (60/120 ROC rotation)、Moskowitz 2012 blended signals、Pomegra wiki。未確認: 15 銘柄パネル D1 で L=20 と L=120 の TSMOM 同符号フィルタを単独 TSMOM60 と比較し、循環シフト帰無と Holm 補正で判定する実証は未確認（移植）。
- 捨てた案の数: 約4: (i) L=10 と L=200（Korzan の 2 周期は中短期と中長期）、(ii) 3 周期の多数決（Q217 の 3 指標一致と重複）、(iii) 月単位の判定（D1 と期間が噛み合わない）、(iv) 損失時休む規則（anti-equity-curve Q254 と重複）。
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない
- 委託の確かめ方: 設計・コード・実行・解釈は Opus 本体の自動運転。委託なし。

## 判定（事前固定）

支持: 二周期版が前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05、かつ単独より bp_net が高い。棄却: 全期間 z<1。ほか: 未確定。多重比較は main_param=1 の pre/post の 2 本（Holm で m=2）。

## 結果

**判定: 支持（確定）**。事前登録の支持条件（前後半ともコスト後 bp>0・Holm 後 p<0.05・単独より bp_net 高）を 5 項目すべて満たす。

- main（all15・params[1]=dual20_120）: 全期間 bp_net=1.8173、t_cluster=2.26、Sharpe=0.48、max_dd=-3904 bp、露出=0.617、z=3.01、p_perm=0.004。
- 前後半（Holm m=2）: pre bp_net=1.8101・z=2.94・p_holm=0.008／post bp_net=1.8238・z=1.73・p_holm=0.0419。両本 <0.05。
- 単独 TSMOM60（params[0]）比較: all15 全期間 1.4169 bp < 1.8173（dual +0.40 bp/日）、Sharpe 0.29 < 0.48、max_dd -6495 bp < -3904 bp（半分の下落）。pre は dual 1.81 vs single 0.44 と大差で勝ち。**post は dual 1.82 vs single 2.30 と bp/日では負けるが、Sharpe は dual 0.54 > single 0.35、max_dd も半分**。「bp/日より下落の軽さと一貫性で勝つ」構図。
- 露出は 0.617 で単独の 0.986 の約 63%。合図不一致で休む日の分だけコストと方向リスクが下がる（Korzan の主張と整合）。

**解釈: 15 銘柄平均で見ると支持だが、群で分かれる。** 
- trend7（商品・指数・金銀・BTC）: 全期間 bp_net=3.447・t_cluster=2.39・post bp_net=4.5623・t_cluster=2.25 と強い（Holm 外・記述扱い）。単独（1.38）に対し +2.07 bp/日。
- fx8（主要通貨 8 本）: 全期間 bp_net=0.46、**post は -0.57 bp/日・t_cluster=-1.34** と負け。単独（-0.33）より悪化。dual フィルタで露出を 61% まで下げても FX の post を救えていない。
- 結論の寄与の大半は trend7。FX のみでの採用には支持を与えない（既知の Q253 系「FX の D1 TSMOM は post で効かない」と整合）。

**data_health の点検**: `no_data` 空・`failed` 空・`null_degenerate=False` のいずれも問題なし。gaps は WTI（3 か月）・UKOIL（7 か月・2011-2013）・US500/USTECH（4 か月・2011 年末-2012 年初）の 4 本で、**すべて pre 期間に収まる**。post 期間（2017〜2026-06）には gap なし（gap_bars=0）、独立標本として p_holm=0.0419 で支持。`years_dropped`=空、`multiple_comparisons` の宣言 n_tests=2 と判定本数が一致。

**捨てた案と知識の締め切り**: SPEC に固定済み。委託なし（Opus 本体の自動運転）。

- 結果 JSON: `results/Q292_result_20261014_014358.json`
- 事前登録 JSON: `results/Q292_spec_20261014_014346.json`
- 年×銘柄: `results/Q292_year_sym_20261014_014358.csv`
