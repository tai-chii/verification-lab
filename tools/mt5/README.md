# mt5_fetch.py — Windows のターミナルから MT5 の足データを取る（2026-10-27）

MT5 の Python 連携（`MetaTrader5` パッケージ）は Windows 専用。MT5 が入っている Windows PC で動かす。**読むだけで売買はしない。**

## 最初の 1 回

```powershell
cd $env:USERPROFILE\verification-lab
git pull
pip install MetaTrader5 pandas pyarrow
```

MT5 側: 起動して口座にログインしておく。「ツール → オプション → チャート → チャートの最大バー数」を **Unlimited** にする（しないと古い足が切れる）。

## 使い方

```powershell
cd $env:USERPROFILE\verification-lab\tools\mt5
python mt5_fetch.py s21                        # S21 の 19 銘柄・H1・2018〜今（引数なしでも同じ）
python mt5_fetch.py USDJPY EURUSD --tf H1,D1   # 銘柄と時間足を指定
python mt5_fetch.py s21 --tf M15 --from 2024-01-01
python mt5_fetch.py crypto                     # BTCUSD / ETHUSD
python mt5_fetch.py --list GER                 # 業者の銘柄名を探す
python mt5_fetch.py s21 --map GER40=DE40.cash  # 自動で見つからない名前を手で指定
python mt5_fetch.py s21 --csv                  # CSV も書く
```

- 2 回目からは保存済みの最後の足から先だけ取り足す（`--full` で全部取り直し）。
- 保存先: `%USERPROFILE%\mt5_data\<口座のサーバー名>\<時間足>\<銘柄>.parquet`（業者ごとに分かれる。`--out` で変更可）。
- 列: `time`（UTC）・`time_server`（MT5 のサーバー時間・秒）・`symbol`（業者の実名）・`open high low close tick_volume spread real_volume`。ファイル名は S21 の名前（US500 など）にそろえる。
- 終了コード: 0 = 全部取れた / 2 = 見つからない銘柄あり（タスクスケジューラで使うとき用）。

## 時刻について（大事）

MT5 の時刻は UTC ではなく業者のサーバー時間。`--tz auto`（既定）は、今のずれが +2/+3 時間なら「NY 引け基準」（米国夏時間中 +3・それ以外 +2。XM など多くの業者）とみなして過去にもさかのぼって当てる。それ以外の業者は今のずれを固定で使う。業者が違う方式なら `--tz 0`（UTC）、`--tz 2`（固定）、`--tz server`（直さない）で指定する。Dukascopy（UTC）と混ぜる前に、同じ時刻の終値が合うか一度だけ照合すること。

## 毎日自動で取る（任意）

タスクスケジューラで「操作: プログラムの開始」→ プログラム `python`、引数 `mt5_fetch.py s21`、開始 `%USERPROFILE%\verification-lab\tools\mt5`。MT5 が起動・ログインしている時間帯に設定する。
