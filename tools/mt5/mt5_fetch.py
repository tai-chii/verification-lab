# -*- coding: utf-8 -*-
"""MT5 から足データを取って parquet / CSV に保存する（Windows のターミナル用・読むだけ・売買しない）。

使い方（PowerShell / コマンドプロンプト）:
  python mt5_fetch.py USDJPY EURUSD                 # H1・2018-01-01〜今
  python mt5_fetch.py s21 --tf H1                   # S21 の 19 銘柄まとめて
  python mt5_fetch.py s21 --tf M15 --from 2024-01-01
  python mt5_fetch.py --list USD                    # 業者の銘柄名を探す（"USD" を含むもの）
  python mt5_fetch.py s21 --csv                     # parquet に加えて CSV も

- 2 回目からは保存済みファイルの最後の足から先だけ取り足す（毎日回しても速い）。
- 業者の銘柄名の違い（USDJPY# / USDJPY.f / US500→SP500 など）は自動で探す。見つからなければ --map で指定。
- 時刻: MT5 の time は「サーバー時間」。time_server（そのまま）と time（UTC）の 2 列を書く。
  UTC への直し方は --tz で選ぶ（auto / nyclose / eet / server / 整数）。既定 auto: 今のずれが +2/+3 なら、
  米国と EU の夏時間が食い違う時期（3 月・10〜11 月の数週）に、どちらに従っているかを判定して保存し、過去にも当てる
  （XM は 2026-10-28 の実測で EU 側＝eet）。判別できない時期は保存済みの判定、無ければ nyclose を仮に使う。
- 出力: 既定は %USERPROFILE%\\mt5_data\\<口座のサーバー名>\\<TF>\\<銘柄>.parquet
"""
import argparse, datetime as dt, os, re, sys, time

try:
    import MetaTrader5 as mt5
except ImportError:
    sys.exit("MetaTrader5 が入っていません →  pip install MetaTrader5 pandas pyarrow")
import pandas as pd
try:
    import pyarrow  # noqa: F401  parquet の読み書きに要る
except ImportError:
    sys.exit("pyarrow が入っていません →  pip install pyarrow")

S21 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY", "EURGBP",
       "XAUUSD", "US500", "USTECH", "GER40", "JPN225", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"]
PRESETS = {"s21": S21, "crypto": ["BTCUSD", "ETHUSD"], "s21+crypto": S21 + ["BTCUSD", "ETHUSD"]}
# 業者ごとに名前が違いやすいもの（上から順に試す）
ALIASES = {
    "US500": ["US500", "SP500", "SPX500", "US500Cash", "USA500", "S&P500", "SPX"],
    "USTECH": ["USTECH", "NAS100", "USTEC", "US100", "NDX100", "US100Cash", "NASDAQ100", "USTECHCash"],
    "GER40": ["GER40", "DE40", "DAX40", "GER40Cash", "DE40Cash", "GER30", "DE30", "DAX"],
    "JPN225": ["JPN225", "JP225", "Japan225", "JP225Cash", "NIKKEI225", "N225", "JPN225Cash"],
    "XAUUSD": ["XAUUSD", "GOLD"],
    "BTCUSD": ["BTCUSD", "BTCUSDT", "Bitcoin"],
    "ETHUSD": ["ETHUSD", "ETHUSDT", "Ethereum"],
}
TF = {k: getattr(mt5, "TIMEFRAME_" + k) for k in
      ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]}
TF_SEC = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600, "H4": 14400, "D1": 86400, "W1": 604800, "MN1": 2592000}
CHUNK_DAYS = {"M1": 20, "M5": 90, "M15": 240, "M30": 480}   # 細かい足は分けて取る（1 回の上限対策）


def die(msg):
    mt5.shutdown(); sys.exit(msg)


def resolve(name, all_names, manual):
    """業者の実際の銘柄名を探す。見つからなければ None。"""
    if name in manual:
        return manual[name] if manual[name] in all_names else None
    cands = ALIASES.get(name, [name])
    for c in cands:                                   # 完全一致
        if c in all_names:
            return c
    for c in cands:                                   # 接尾辞・接頭辞つき（USDJPY# / USDJPY.f / mUSDJPY など）
        pat = re.compile(r"^[a-z#._-]{0,3}" + re.escape(c) + r"[#._\-a-zA-Z0-9]{0,6}$", re.I)
        hits = sorted([n for n in all_names if pat.match(n)], key=len)
        if hits:
            return hits[0]
    return None


def us_dst(t):
    """米国夏時間か（3 月第 2 日曜〜11 月第 1 日曜）。t は naive datetime（日付だけ見る）"""
    y = t.year
    mar = dt.datetime(y, 3, 8); start = mar + dt.timedelta(days=(6 - mar.weekday()) % 7)
    nov = dt.datetime(y, 11, 1); end = nov + dt.timedelta(days=(6 - nov.weekday()) % 7)
    return start <= t < end


def eu_dst(t):
    """EU 夏時間か（3 月最終日曜〜10 月最終日曜）。XM などはこちらで +2/+3 を切り替える"""
    y = t.year
    mar = dt.datetime(y, 3, 31); start = mar - dt.timedelta(days=(mar.weekday() + 1) % 7)
    octo = dt.datetime(y, 10, 31); end = octo - dt.timedelta(days=(octo.weekday() + 1) % 7)
    return start <= t < end


def pick_mode(cur_off, now=None):
    """auto のとき: 今のずれから NY 引け基準（米国の夏時間）か EET（EU の夏時間）かを決める。
    両者が食い違う時期（3 月・10〜11 月の数週）なら判別できる。同じ時期なら前回の判定（保存）を使う。"""
    if cur_off not in (2, 3):
        return None
    now = now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    us, eu = (3 if us_dst(now) else 2), (3 if eu_dst(now) else 2)
    if us != eu:
        return "nyclose" if cur_off == us else "eet"
    return "same"


def detect_offset(sym):
    """今のサーバー時間と UTC のずれ（時間）。市場が閉まっていると測れないので None。"""
    tick = mt5.symbol_info_tick(sym)
    if tick is None or tick.time == 0:
        return None
    diff = tick.time - time.time()
    if abs(diff - round(diff / 3600) * 3600) > 600:   # 最後のティックが古い（休場中）
        return None
    return int(round(diff / 3600))


def to_utc(server_times, mode, cur_off):
    s = pd.to_datetime(server_times, unit="s")        # サーバー時間（naive）
    if mode == "server":
        off = pd.Series(0, index=s.index)
    elif mode == "nyclose":
        off = s.map(lambda t: 3 if us_dst(t) else 2)
    elif mode == "eet":
        off = s.map(lambda t: 3 if eu_dst(t) else 2)
    elif mode == "auto":
        off = pd.Series(cur_off, index=s.index)
    else:
        off = pd.Series(int(mode), index=s.index)
    return (s - pd.to_timedelta(off, unit="h")).dt.tz_localize("UTC")


def fetch(sym, tf, t_from, t_to):
    step = dt.timedelta(days=CHUNK_DAYS.get(tf, 100000))
    parts, a = [], t_from
    while a < t_to:
        b = min(a + step, t_to)
        r = mt5.copy_rates_range(sym, TF[tf], a, b)
        if r is not None and len(r):
            parts.append(pd.DataFrame(r))
        a = b
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts).drop_duplicates("time").sort_values("time").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description="MT5 から足データを取る（読むだけ）")
    ap.add_argument("symbols", nargs="*", help="銘柄名 or プリセット（s21 / crypto / s21+crypto）")
    ap.add_argument("--tf", default="H1", help="M1 M5 M15 M30 H1 H4 D1 W1 MN1（カンマ区切りで複数可）")
    ap.add_argument("--from", dest="f", default="2018-01-01", help="開始日（初回のみ使う。既定 2018-01-01）")
    ap.add_argument("--to", default=None, help="終了日（既定 今）")
    ap.add_argument("--out", default=os.path.join(os.path.expanduser("~"), "mt5_data"))
    ap.add_argument("--tz", default="auto", help="auto / nyclose / eet / server / 整数（固定のずれ・時間）")
    ap.add_argument("--map", default="", help="名前の手動指定 例: US500=SPX500.cash,GER40=DE40")
    ap.add_argument("--full", action="store_true", help="保存済みを無視して最初から取り直す")
    ap.add_argument("--csv", action="store_true", help="CSV も書く")
    ap.add_argument("--list", metavar="WORD", help="WORD を含む銘柄名を一覧して終わる")
    ap.add_argument("--path", default=None, help="terminal64.exe の場所（MT5 が複数あるとき）")
    ap.add_argument("--login", type=int); ap.add_argument("--password"); ap.add_argument("--server")
    a = ap.parse_args()

    # 再配布の防止: 業者のデータは個人利用のみ。Git リポジトリの中（GitHub に上がりうる場所）には保存しない
    p = os.path.abspath(a.out)
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            sys.exit(f"--out が Git リポジトリ（{p}）の中です。業者のデータを GitHub に上げないよう、リポジトリの外を指定してください。")
        if os.path.dirname(p) == p:
            break
        p = os.path.dirname(p)

    kw ={k: v for k, v in dict(path=a.path, login=a.login, password=a.password, server=a.server).items() if v}
    if not mt5.initialize(**kw):
        sys.exit(f"MT5 に接続できません: {mt5.last_error()}\n→ MT5 を起動して口座にログインしてから、もう一度。")
    acc, info = mt5.account_info(), mt5.terminal_info()
    if acc is None:
        die("口座にログインしていません。MT5 でログインしてから、もう一度。")
    print(f"接続: {acc.server} / 口座 {acc.login}（{'デモ' if acc.trade_mode == 0 else '実口座'}）  最大バー数={info.maxbars:,}")

    all_names = {s.name for s in (mt5.symbols_get() or [])}
    if a.list is not None:
        for n in sorted(x for x in all_names if a.list.lower() in x.lower()):
            print(" ", n)
        die(None)

    want = []
    for s in a.symbols or ["s21"]:
        want += PRESETS.get(s.lower(), [s.upper() if s.isascii() else s])
    manual = dict(kv.split("=", 1) for kv in a.map.split(",") if "=" in kv)
    tfs = [t.strip().upper() for t in a.tf.split(",")]
    for t in tfs:
        if t not in TF:
            die(f"--tf が不正: {t}（{' '.join(TF)}）")
    t_to = dt.datetime.fromisoformat(a.to).replace(tzinfo=dt.timezone.utc) if a.to else dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
    t_from0 = dt.datetime.fromisoformat(a.f).replace(tzinfo=dt.timezone.utc)
    srv = re.sub(r'[\\/:*?"<>|]', "_", acc.server)

    cur_off, mode, missing, ok = None, None, [], 0
    for name in want:
        real = resolve(name, all_names, manual)
        if real is None:
            print(f"[{name}] 見つからない → python mt5_fetch.py --list {name[:3]} で名前を探し、--map {name}=<名前>")
            missing.append(name); continue
        mt5.symbol_select(real, True)
        if mode is None:
            cur_off = detect_offset(real)
            mode = a.tz
            if a.tz == "auto":
                mf = os.path.join(a.out, srv, "tz_mode.txt")
                saved = open(mf).read().strip() if os.path.exists(mf) else None
                got = pick_mode(cur_off)
                if got in ("nyclose", "eet"):
                    mode = got
                    os.makedirs(os.path.dirname(mf), exist_ok=True); open(mf, "w").write(mode)
                elif got == "same":
                    mode = saved or "nyclose"
                else:
                    mode = saved or ("nyclose" if cur_off is None else str(cur_off))
                note = "" if got in ("nyclose", "eet") or saved else "（今の時期は判別できないので仮。3 月・10〜11 月に回すと確定する）"
            else:
                note = ""
            how = {"nyclose": "米国の夏時間で +3/+2（NY 引け基準）", "eet": "EU の夏時間で +3/+2（EET）",
                   "server": "直さない"}.get(mode, f"固定 {mode} 時間")
            print(f"サーバー時間のずれ: {'測れず（休場中）' if cur_off is None else f'{cur_off:+d} 時間'} → UTC へは {how} で直す{note}")
        for tf in tfs:
            d = os.path.join(a.out, srv, tf); os.makedirs(d, exist_ok=True)
            fp = os.path.join(d, f"{name}.parquet")
            old = pd.read_parquet(fp) if os.path.exists(fp) and not a.full else None
            t_from = t_from0
            if old is not None and len(old):
                t_from = dt.datetime.fromtimestamp(int(old["time_server"].max()) - TF_SEC[tf] * 3, dt.timezone.utc)
            t0 = time.time()
            new = fetch(real, tf, t_from, t_to)
            if new.empty and old is None:
                print(f"[{name}/{tf}] 0 本（{real}）— 期間に足が無いか、最大バー数の制限。MT5 のオプションで「チャートの最大バー数」を Unlimited に")
                continue
            if not new.empty:
                new = new.rename(columns={"time": "time_server"})
                new.insert(0, "time", pd.NaT)
                new.insert(2, "symbol", real)
            df = new if old is None else pd.concat([old, new]).drop_duplicates("time_server", keep="last")
            df = df.sort_values("time_server").reset_index(drop=True)
            df["time"] = to_utc(df["time_server"], mode, cur_off)   # 毎回全体を直し直す（直し方を変えても揃う）
            df.to_parquet(fp, index=False)
            if a.csv:
                df.to_csv(fp[:-8] + ".csv", index=False)
            first = pd.to_datetime(df["time"].iloc[0]).strftime("%Y-%m-%d")
            last = pd.to_datetime(df["time"].iloc[-1]).strftime("%Y-%m-%d %H:%M")
            add = len(df) - (0 if old is None else len(old))
            print(f"[{name}/{tf}] {real}: {len(df):,} 本（+{add:,}） {first} 〜 {last} UTC  {time.time()-t0:.1f}s")
            ok += 1
    print(f"\n保存先: {os.path.join(a.out, srv)}   完了 {ok} 件" + (f" / 見つからない {len(missing)}: {','.join(missing)}" if missing else ""))
    mt5.shutdown()
    sys.exit(2 if missing else 0)


if __name__ == "__main__":
    main()
