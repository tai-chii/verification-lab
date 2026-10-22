# _s1x_common — S10〜S13（データ源を 1 つ足す新しい S）の共通部

2026-10-22 /lab-plan ターミナル版 N=10（Q394〜Q403）で作成。`fe_core` は書き換えず、Runner 型に薄い層を足す。

| 何 | どこ |
|---|---|
| 封印（time < 2024-07-01）と `loaded[sym]`（クロスアセット・横断の strategy が他銘柄を参照） | `SealedRunner._load` |
| 規程モードを **spec.split_year** で・**全設定**について出す（`rule_mode`＝main、`rule_mode.params`＝設定ごと） | `SealedRunner._rule_mode` |
| 3 分岐の判定（S09 と同じ形: 規程 gate 通過＋等金額 z≥2 → 支持／z<1 or t_all<0 → 棄却） | `judge_gate` |
| 実測スプレッド（`_データ/raw/D1/spread_<sym>.csv`）の日次系列と z | `spread_rel_daily`・`rolling_z` |
| FOMC 定例発表日（**知識から記載・実行者が federalreserve.gov と照合**。`--fomc-csv` で差し替え）、サイクル日、偶数週 | `FOMC_DATES`・`fomc_dates`・`fomc_cycle_day`・`even_week_mask`・`hold_bars_pos` |
| 月替わり（各銘柄の足で営業日を数える） | `tom_offsets_pos` |
| データガード（銘柄が揃わなければ `status=データ待ち`・exit 2） | `data_guard`・`run_main` |

使う側: `s10-*`・`s11-*`・`s13-*`。S12（金利モメンタム）は `_s09_common/s09carry.py` を再利用（金利差・スワップ・封印・判定）。
