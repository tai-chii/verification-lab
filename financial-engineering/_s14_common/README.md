# _s14_common — S14（tick 出来高）・S15（利上げ局面の事前定義）の共通部

2026-10-22 /lab-plan ターミナル版 N=10（2 回目・Q411〜Q418）で作成。`fe_core` は書き換えず、`_s1x_common/s1x.py` の SealedRunner（封印・全設定の規程モード・judge_gate）に薄い層を足す。

| 何 | どこ |
|---|---|
| 出来高の比（V20/V250）・log 出来高 z・出来高加重 TSMOM | `volume_ratio`・`volume_z`・`vw_tsmom_pos` |
| 利上げ局面（直近 W 暦日に政策金利の上げがあったか・8 中銀のうち上げた数。t−1 暦日までの情報） | `hike_within`・`n_hiking`（`_s09_common/s09carry.load_policy` を再利用） |
| kind="H1→D1" でも動くデータガード＋ SealedRunner の入口 | `run_main` |

- **出来高は 15 銘柄の H1 だけ**（`学問/金融工学/作業/FX/システムトレード/data_<sym>_H1_dukascopy.csv` の volume 列＝Dukascopy の tick 出来高）。`_データ/raw/D1` の 48 銘柄 D1 には volume 列が無い。S14 は kind="H1→D1"（UTC 0 時区切り）で 15 銘柄。
- 使う側: `s14-*`（Q411・Q412）、`s15-*`（Q414・Q415）。Q413（出来高の前提）・Q416〜Q418（基盤）は土台を直接使う型で、ここの関数だけ借りる。
- 土台に移したい候補: 上の 5 関数（出来高族を `signals.py` に足すときは CATALOG に載せる）。
