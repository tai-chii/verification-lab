# fe_core — 検証スクリプトの共通の土台（2026-10-13 作成・同日 Opus 監査を経て 0.2.0 で固定）

`financial-engineering/*/kensho_*_q089〜q286.py` の 91 本が同じ雛形（「共通の土台ここまで」より上の約 300 行）をコピーしていた
（調査: `tools/重複関数調査_20261013.md`、道具: `tools/dup_scan.py`・`tools/dup_diff.py`）。その土台をここに切り出した。

## 構成

| ファイル | 中身 |
|---|---|
| `_paths.py` | `WS`・`_p`（NFD 対応）・`DATA_DIR`・銘柄表 `FX8/FX6/TREND7/SYMS/CRYPTO`・`SPLIT_YEAR`・`SEED`・`GROUPS` |
| `data.py` | `_read`・`load_d1`・`load_h1`・`load_csv`・`h1_to_d1`・`_smoke_ohlc`・`exists_sym`・`syms_available` ＋ **新規** `check_gaps`・`health`（欠損月の点検、成功／データなし／失敗の区別） |
| `costs.py` | `COST_RT`（段階1の往復コスト）・`CRYPTO_COST_RT_REL`・`cost_bp_oneway`・`pnl_bp`（1 本ずらしはここで行う） |
| `metrics.py` | `tstat`・`nw_t`・`spearman`・`max_drawdown`・`sharpe_ann`・`qlike`・`by_year_stats`・`f` |
| `multiple.py` | `z_of`・`perm_within`・`block_perm`・`circ_shift`・`holm`・`holm_sig` |
| `io.py` | `parse_args`・`write_result`（出力先は呼び出し元の `results/`）・`_json_default` |

## 目録（CATALOG.md・catalog.json）

`python3 tools/gen_fe_core_catalog.py` が各関数の docstring から **`CATALOG.md`（LLM が読む用・段階の順）** と `catalog.json`（機械用）を作る。
**新しい検証を書く前に CATALOG.md を上から読む**。手で編集しない。正本は docstring で、書式は
「1 行目: 一言／使う場面:／入力:／返り値:／禁止:／段階: 読み込み|合図|損益|統計|帰無|判定|保存|共通」。
関数を足したり変えたりしたら docstring を同じ書式で書き、生成し直す（`--check` で最新かだけ確かめられる）。

## 使い方（新しい検証スクリプトの冒頭）

```python
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import *   # 雛形と同じ名前がそのまま使える
```
以下は雛形の「共通の土台ここまで」より下（QID・定義・run・main）だけを書く。`/lab-plan` の雛形もこの形に替える。

## 固定（0.2.0）

2026-10-13 に作者とは別の Opus がコードを読んで手計算・実行で監査し（`REVIEW_20261013.md`）、必須の指摘をすべて反映した上で **固定**した。
固定後に土台を変えるときは、(1) 変更理由を REVIEW か改善ログに書く、(2) `kensho_ecb_fix_q268_fecore.py` と旧 `kensho_ecb_fix_q268.py` を同 seed で走らせて JSON・CSV が一致することを確かめる、(3) `gen_fe_core_catalog.py` を回す。

## 雛形との違い（意図した変更のみ）

- `sharpe_ann`: `x[np.isfinite(x)]` あり版に統一（20 本は無し版だった。NaN が 1 つで全体が NaN になるため）。
- `holm`: 有限な p だけなら同じ値。NaN は m に数えるが補正後も NaN（有意にならない）。`holm_sig(p, alpha)` で有意フラグも返せる。
- `write_result(..., out_dir=None)`: 既定は `<スクリプトのフォルダ>/results`（雛形の `OUT` と同じ）。
- `parse_args(..., default_seed=SEED, argv=None)`: seed の既定を渡せる。
- 追加: `check_gaps(df, bar)`・`health(syms, kind)`。結果 JSON の `data_health` に入れる想定（失敗パターン集 2026-09-30・Q108 の再発防止）。
- 0.2.0（監査の反映）: `z_of` は退化した帰無で (nan, nan)。`perm_p`・`null_summary`・`null_degenerate`・`cluster_t`・`sharpe_ann_n`・`sanitize`・`fmt` を追加。load_* に `dt_prev_h`・`gap` 列、`h1_to_d1` に `close_time` 列。`by_year_stats(min_rows=20)`。`pnl_bp` は pos の NaN を 0 にして警告、スカラーの cost も受ける。`_read` は安定ソート＋`attrs["n_dup"]`。`circ_shift` の上限を 1 増やした。`nw_t` は定数で NaN。`max_drawdown` は NaN を 0 扱い。`parse_args` の B の既定 500。`write_result` は上書きせず連番、`here=` を受ける。詳細は `REVIEW_20261013.md`。

## 照合（移植が正しいことの証拠）

Q268（`ecb-fix-vshape/kensho_ecb_fix_q268.py` → `kensho_ecb_fix_q268_fecore.py`、463 行 → 159 行）を同じ seed・B=300 で両方実行し、
結果 JSON（`generated` 以外）と daily CSV が**完全一致**。実行時間 旧 1.33 s／新 1.26 s。出力は `ecb-fix-vshape/results/_fecore照合_20261013/`。

## 守ること

- **ここは固定の土台。検証ごとの戦略・判定は書かない。** docstring を変えたら `gen_fe_core_catalog.py` を回す。 変えるときは、雛形由来の既存スクリプト 1 本以上を `fe_core` 版にして数値一致を確かめてから。
- 既存 385 本は書き換えない。新規の検証からこの土台を使う。古い検証は再走が必要になったときに移植する。
- 未来の行に触れない: `pnl_bp` が 1 本ずらすので、合図側で `shift` しない。
- Python のまま（numpy のベクトル演算が本体）。遅い 1 関数が見つかったときだけ Rust（PyO3）を検討する。

## 次の候補

- 監査で見送った低優先: `block_perm` のランダムな開始位置、`GROUPS`/`SYMS` の tuple 化、`h1_to_d1` の tz 引数（夏時間）、`perm_within` の NaN グループ。

- `Runner`（事前登録 → 読み込み＋health → 合図 → pnl → 期間分割 → 統計 → judge → write）を 1 つの型にする。`SPEC.params` に設定を並べれば掃引を自動で回し、`n_tests` を数える。
- `walk_forward`・`events`（イベント研究）の型を揃える。
- 結果 JSON の列を lab-ops の `summary.json` と揃え、`labsummary.py` で横断集計する。
