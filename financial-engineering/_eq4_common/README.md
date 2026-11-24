# _eq4_common — 株式無料層 第4弾（Q787〜Q806）の共通部

2026-11-24 の /lab-plan 20（Fable）で作成。土台の 2 本（`jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py`・`us-sec-value-q696/sec_pit.py`）は書き換えず、`eq4.py` が importlib で読んで薄い層を足す。

| 何 | どこ |
|---|---|
| 判定の規則（事前固定・変更禁止） | `verdict_both`（日米 10 本 Q797〜Q806・第3弾 Q700〜Q707 と同じ）／`verdict_us_fam10`（米国 SEC 10 本 Q787〜Q796・通過の線 NW t≥2.58＝族 10 本の Bonferroni） |
| 価格と出来高の月次 L/S のドライバ | `run_pv`（適格・保有・コスト・帰無は土台のまま。合図は各案の `make_sig`） |
| 既にある日次 L−S に月ごとの重みを掛ける案（Q799・Q800） | `month_blocks`・`weighted_series`・`null_weight_shift`・`run_weighted`（元の系列は Q563 の結果ファイル） |
| 市場との共変動（ベータ・共歪度・相関） | `market_ret`・`roll_moments`・`beta_from` |
| SEC 財務の年次の読み方 | `Fin`（年次だけ・同じ会計年度の組だけ・1 年前は当初の報告）・`d_roa`・`d_ato`・`d_margin`・`d_leverage` |
| 米国 SEC のドライバ | `run_sec`（`sec_pit.run_us` をそのまま呼ぶ。足したタグ: 営業利益・粗利益・売上原価・負債。記述として Q698 との相関を足す） |

- 試走: 各案の `kensho_*.py --smoke --B 5`（合成データ。SEC の合成には `_synth_ext` が足したタグの行を足す）。
- このフォルダは INDEX の対象外（名前が `_` で始まる）。
