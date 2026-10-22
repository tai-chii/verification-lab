# Q416 関門（σ0.5%/日・14 年の最大下落 −6% 以内＋前後半 t≥2）は年率シャープ S がいくら以上の戦略を何割通すか（S07 規程モード損益の 20 日ブロック・ブートストラップで S を 0〜3 に合わせて測る）

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の Q416 の行（Fable・/lab-plan ターミナル版 2026-10-22 夜・2 回目 N=10 の 6 本目（基盤・関門の較正））。出典: [[検証/_基盤/戦略台帳]] 段階と関門／要対応 2026-10-22 13:55「関門の DD 条件が今の探索の律速」／Man Group 'You're fired'（IID 模擬: 10 年・シャープ 0.5 で 2σ の下落に 43%）／Bailey・López de Prado 2014

- スクリプト: `kensho_gate_pass_probability_q416.py`（`fe_core` 土台を直接使う型。事前登録の内容は冒頭 docstring に固定）
- データ: 48 銘柄 wide48 の D1_fromH1（2010-01〜・封印 time<2024-07-01）。TSMOM60（S07 本体）→ RULES_FINTOKEI の size_weights → simulate_portfolio（コストは Runner._cost と同じ）→ 日次損益 port（`検証/_データ/raw/D1/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 kensho_gate_pass_probability_q416.py`（B=2000 経路。pandas/numpy のみ）
- 試走: `--B 100`。経路の確認だけなら `--smoke`（合成データ・銘柄 3・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/Q416_result_<日時>.json`（`observed_s07_fintokei`・`table.block`／`table.iid`（S ごとの P(dd ok)・P(t ok)・P(pass)）・`required_sharpe`・機械判定 `machine_verdict`）

## 状態（2026-10-22）

**設計とコードまで。実行と解釈は未。** コードは `--smoke --B 20` の経路確認だけ済み。
Sonnet／Opus が実行するときの手順:

1. 冒頭 docstring（仮説・判定・捨てた案の数）を読んでから走らせる（変更しない）。
2. `python3 kensho_gate_pass_probability_q416.py` を Mac で実行（2000 経路 × 7 S × 2 版。数分）。
3. `machine_verdict` は事前固定の規則で機械的に付けたもの。解釈は実行者が書く。**結果は要対応 2026-10-22 13:55 の ★（A/B/C）の節に「関門の通過確率の表」として 1 行で添える**（C の判断材料。関門の置き方そのものは taichi が決める。結果を見てから σ 目標を掃引しない）。
4. 記録先: 知見ノート（基盤・検証方法論）、アイデア候補の状態、検証キュー Q416 を完了へ、`gen_fe_index.py`。

## 方法（要点）

- 仮説: 関門の「最大下落 −6% 以内」は σ 目標 0.5%/日の下では年率シャープ 1.5 を超えないと半分も通らず、現在の探索（単一族・シャープ 0〜0.5）では方法の良し悪しに関係なく通らない。これが本当なら関門は選別ではなく「探索の停止」として働いている
- 測るもの: S∈{0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0} ごとに P(max_dd ≥ −6%)、P(t_pre≥2 かつ t_post≥2)、P(両方＝通過)。P=0.5／0.9 になる S を線形補間。S07 本体の実現値（シャープ・max_dd・t）を併記
- 帰無: 模擬（ブロック再標本・20 日・B=2000 経路。偏差 e＝port−mean に m_S＝S·sd/√252 を足す）。IID 正規版は比較
- 多重比較: 判定は 1 本（S=1.0 と 1.5 の 2 点の P）。ほかは記述
- 先行研究チェック: WebSearch 2026-10-22「probability maximum drawdown exceeds threshold as function of Sharpe ratio proprietary trading firm drawdown limits block bootstrap」: Man Group 'You're fired'（IID 模擬の表）、CME の下落指標のブロック・ブートストラップ、HackerNoon（ブロック長の感度・ブログ＝根拠にしない）。手元の規程（σ0.5%・−6%・14 年・前後半 t）の通過確率は未確認
- 捨てた案の数: 2（年ブロック／σ 目標の掃引）
- 知識の締め切り: Claude の知識の締め切りはおよそ 2026-06
- 委託の確かめ方: なし（Fable 設計 → Sonnet 実行）

## 判定（事前固定）

支持（関門は現実的）: ブロック版で P(通過 | S=1.0) ≥ 0.5。棄却（関門が律速）: ブロック版で P(通過 | S=1.5) < 0.5。ほか → 未確定。IID 版は記述。

## 結果

未実行。
