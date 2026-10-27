# Q555 — S21 の学習窓: 直近に寄せて毎月学習し直すと、翌月はよく勝つか

- 事前登録: `事前登録_q555.md`（S21・凍結モデル・フォワードは変えない。S21 系の試行に 9 本）。コード: `kensho_s21_trainwin_q555.py`（直接型・S21 系）。
- 実行: `python3 kensho_s21_trainwin_q555.py DATA_DIR OUT_DIR [--arms W1,W3,...] [--smoke]`（腕×月ごとに `OUT_DIR/q555/<腕>/<YYYY-MM>.pkl` を保存・再実行は続きから。全腕 4 時間前後）。
- 注意: この Mac の pandas 2.3 では tz つき `to_numpy()` が object になり `K.labels` が落ちるため、スクリプト内の `_compat_tz_to_numpy()` で補っている（値は変わらない）。
- 出力: `result_q555.json`・`trades_q555.csv.gz`。

## 結果

未実行。
