# _s04_common — S04（ML 層）の検証スクリプト共通部（検証フォルダではない）

`s04ml.py` は Q374〜Q383（2026-10-22 の /lab-plan ターミナル版 N=10）が共用する薄い層。`fe_core/ml.py`・`fe_core/risk.py` を組み合わせて
「読み込み → 特徴量 → 封印（2024-07-01）→ 年次ウォークフォワード → 予測→規模（sign／clip／kelly）→ 規程モード損益（RULES_NONE／RULES_FINTOKEI）→ 統計」を 1 本の流れにしたもの。
`gen_fe_index.py` は `_` で始まるフォルダを飛ばすので INDEX には載らない。

- `fe_core` は書き換えない。土台に足したい関数が出たら `tools/fe_core/` に移して CATALOG に載せる（候補: `WIDE48_COST_REL`・`direction_experiment`・`convert_direction`／`convert_meta`・`auc`）。
- **コストの注意（2026-10-22 判明）**: `fe_core.COST_RT` に無い wide48 の 34 銘柄（為替クロス 14・株価指数 11・商品 5・債券 3・ETH）は、既定だと `CRYPTO_COST_RT_REL`（往復 30bp）に落ちる。
  Q367〜Q371（S07）はこの既定で走っている。ここでは `WIDE48_COST_REL`（往復・比。知識から記載の概数・保守側）を使う。実行者は `検証/_データ/raw/D1/spread_<sym>.csv` と照合すること。
- 判定（judge）は各スクリプトが持つ。`judge_vs_s07` は S04c 系の既定の 3 分岐（Q374 と同じ文）。
- 使い方: 各スクリプトの冒頭で `sys.path.insert(0, os.path.join(HERE, "..", "_s04_common"))` → `import s04ml as M`。`M.ml_main(SPEC, HERE, run)` が `--readme`／`--idea-row`／データガード／smoke の B 制限／保存を担う。
