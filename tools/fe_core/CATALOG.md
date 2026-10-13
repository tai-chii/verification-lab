# fe_core 目録（自動生成・手で編集しない）

`python3 tools/gen_fe_core_catalog.py` が各関数の docstring から作る。正本は docstring。**新しい検証スクリプトを書く前にこのファイルを上から読む**: 段階の順に並んでいるので、そのまま検証の骨格になる。

読み込み → 合図 → 損益 → 統計 → 帰無 → 判定 → 保存（共通は冒頭と main）。土台の関数は `from fe_core import *` でそのまま呼べる。

## 定数

| 名前 | 値 | 備考 | 場所 |
|---|---|---|---|
| `WS` | `os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))` | fe_core/ → tools/ → verification-lab/ → 検証/ → ワークスペース | `_paths.py:8` |
| `DATA_DIR` | `_p('検証', '学問', '金融工学', '作業', 'FX', 'システムトレード')` |  | `_paths.py:37` |
| `FX8` | `['EURUSD', 'GBPUSD', 'AUDUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'EURJPY', 'GBPJPY']` |  | `_paths.py:38` |
| `FX6` | `['EURUSD', 'GBPUSD', 'AUDUSD', 'USDJPY', 'USDCHF', 'USDCAD']` | ドル建て先進国（Q019・Q054 と同じ） | `_paths.py:39` |
| `TREND7` | `['XAUUSD', 'XAGUSD', 'WTI', 'UKOIL', 'US500', 'USTECH', 'BTCUSD']` |  | `_paths.py:40` |
| `SYMS` | `FX8 + TREND7` |  | `_paths.py:41` |
| `CRYPTO` | `['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'ADAUSD', 'BCHUSD', 'XLMUSD', 'EOSUSD', 'LNKUSD', 'DOTUSD', 'SOLUSD']` |  | `_paths.py:42` |
| `SPLIT_YEAR` | `2017` |  | `_paths.py:43` |
| `SEED` | `20261010` |  | `_paths.py:44` |
| `GROUPS` | `{'all15': SYMS, 'fx8': FX8, 'trend7': TREND7}` |  | `_paths.py:45` |
| `COST_RT` | `{'EURUSD': 0.0002, 'GBPUSD': 0.0002, 'AUDUSD': 0.0002, 'USDCHF': 0.0002, 'USDCAD': 0.0002, 'USDJPY': 0.02, 'EURJPY': 0.02, 'GBPJPY': 0.02, 'XAUUSD': 0.6, 'XA...` | 往復コスト（価格単位・段階1の保守値。Q136〜Q190 と同じ表） | `costs.py:8` |
| `CRYPTO_COST_RT_REL` | `0.003` | 暗号資産: 往復 30bp の仮置き（Q152 と同じ） | `costs.py:11` |
| `f` | `fmt` | 雛形との互換（91 本が f() を使う） | `metrics.py:162` |

## 段階: 共通

### `_p(*parts)`  — `_paths.py:11`

ワークスペース内のパスを作る。macOS 共有の NFD 名に対応（NFC で無ければ NFD で探す）。

| | |
|---|---|
| 使う場面 | DATA_DIR 以外のワークスペース内ファイルを指すとき |
| 入力 | parts: ワークスペースからの相対パスの各要素 |
| 返り値 | 絶対パス（str） |
| 禁止 | 絶対パスをハードコードしない |

### `script_dir()`  — `_paths.py:25`

呼び出し元スクリプトのフォルダ（雛形の HERE に相当）。対話実行時はカレント。

| | |
|---|---|
| 使う場面 | write_result の既定の出力先 |
| 入力 | なし |
| 返り値 | 絶対パス（str） |
| 禁止 | — |

### `parse_args(default_B=500, extra=None, default_seed=SEED, argv=None)`  — `io.py:16`

共通の引数（--B 帰無の回数、--smoke、--seed）。

| | |
|---|---|
| 使う場面 | main の最初。検証固有の引数は extra(ap) で足す |
| 入力 | default_B（既定 500＝改善判定.md の既定）、extra: ArgumentParser を受けて add_argument する関数、default_seed、argv（テスト用） |
| 返り値 | argparse.Namespace |
| 禁止 | 事前登録した B・seed を結果を見てから変えない |

### `class Spec`  — `runner.py:31`

事前登録の中身。測る前に埋めて固定する（Runner が最初に results/<qid>_spec_<ts>.json へ書く）。

| | |
|---|---|
| 使う場面 | ポジション型の検証スクリプトの冒頭。アイデア候補の行の内容をそのまま写す |
| 入力 | qid、question、hypothesis、reject_if（判定規則の文。3 分岐）、syms、kind（"D1_fromH1"|"H1_dukascopy"|"H1→D1"）、params（掃引する設定の list。1 件なら [{}]）、main_param（判定に使う設定の添字）、n_tests（判定に使う検定の本数＝holm の m）、warmup、per_year、B、split_year、start、null_kind（"circ_shift"|"block_perm"|"none"）、null_block、null_min_shift、cost_rel、discarded、knowledge_cutoff、delegation、README 用の source・data・measure・null_desc・prior_art・batch・designer・coder、settings |
| 返り値 | dataclass |
| 禁止 | 結果を見てから hypothesis・reject_if・n_tests・main_param・B を変えない |

### `class Runner`  — `runner.py:96`

ポジション型の検証の固定された流れ。strategy(df, p, sym) -> pos（長さ len(df) の ±1/0。shift しない）だけを外から受ける。

| | |
|---|---|
| 使う場面 | 日足・時間足で合図→損益→統計→帰無→判定を行う検証。params に設定を並べると掃引し、n_tests を数える |
| 入力 | spec: Spec、strategy: 関数、judge: (res, spec)->str（省略で default_judge）、null: (rng, pos, df, p, sym)->pos（省略で spec.null_kind）、summarize_extra: (cells, spec)->dict（結果に足す記述統計） |
| 返り値 | Runner。run(args, rng) -> (res, csvs)、execute(argv=None) で parse_args から保存まで |
| 禁止 | Runner の中の流れを検証ごとに書き換えない。合図側で shift しない。gap 行・years_dropped・data_health の failed を見ずに「確定」と書かない |


## 段階: 読み込み

### `_read(path)`  — `data.py:33`

CSV を読み、time を datetime にして並べ替え・重複除去する（生の読み込み）。

| | |
|---|---|
| 使う場面 | load_* の中。直接使うのは data_*.csv 以外の表を読むときだけ |
| 入力 | path: CSV のパス（time 列が必要） |
| 返り値 | DataFrame（time 昇順・重複なし・同時刻は最初の行を残す）。df.attrs["n_dup"] に除いた重複の数 |
| 禁止 | 失敗を空の DataFrame で握りつぶさない（例外はそのまま上げる） |

### `load_d1(sym, smoke=False, rng=None)`  — `data.py:53`

UTC 日足（data_<sym>_D1_fromH1.csv）。値動きのない足（high==low）は除く。

| | |
|---|---|
| 使う場面 | 日足の検証の読み込み。--smoke のときは合成データ |
| 入力 | sym: 銘柄、smoke: 合成データにするか、rng: smoke 用の Generator |
| 返り値 | DataFrame（time, open, high, low, close, volume, ret, year, dt_prev_h, gap）。ret は比（bp ではない）。gap=True の行の ret は空白をまたいだ複数日分 |
| 禁止 | ret の単位を変えた列を同じ名前で作らない（旧 q284・q286 で bp 版があり事故の種）。gap 行を除くか残すかを結果に書く |

### `load_csv(name, smoke=False, rng=None, freq='h', n=20000, start='2015-01-01')`  — `data.py:71`

任意の data_<name>.csv（H1/H4/M15/yahoo/ask など）を読む。

| | |
|---|---|
| 使う場面 | load_d1・load_h1 に無い足種や別ソース |
| 入力 | name: data_ の後ろの名前、smoke/rng/freq/n/start: 合成データの設定 |
| 返り値 | DataFrame（生の列。ret・year・gap は付かない） |
| 禁止 | 同じ銘柄を別ソースで混ぜて 1 本の系列にしない |

### `load_h1(sym, smoke=False, rng=None, n=60000, start='2015-01-01')`  — `data.py:84`

UTC 1 時間足（data_<sym>_H1_dukascopy.csv）。値動きのない足は除く（週末の埋め足もこれで落ちる）。

| | |
|---|---|
| 使う場面 | 時間帯・イベント研究・H1 からの日足作成（h1_to_d1） |
| 入力 | sym、smoke、rng、n/start: 合成データの長さと開始 |
| 返り値 | DataFrame（time, open, high, low, close, volume, ret, year, hour, dow, dt_prev_h, gap）。time は足の開始時刻 |
| 禁止 | 読んだ後に health／check_gaps で欠損を点検せずに判定しない。gap=True の行の ret を時刻ラベルの損益に数えない |

### `h1_to_d1(h1, cutoff_hour=0)`  — `data.py:101`

H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。

| | |
|---|---|
| 使う場面 | 日の区切り（NY 17 時など）を変えた日足が要るとき |
| 入力 | h1: load_h1 の返り値、cutoff_hour: 区切りの時刻（UTC 固定。夏時間は追わない） |
| 返り値 | DataFrame（time, close_time, open, high, low, close, volume, nbars, ret, year, dt_prev_h, gap）。本数 6 未満の日は除く |
| 禁止 | cutoff を結果を見てから変えない。別の表（load_d1 など）と結合するときは time ではなく close_time で合わせる（time で合わせると最大 cutoff 時間分の先読みになる） |

### `_smoke_ohlc(sym, rng, n, freq, start)`  — `data.py:121`

合成データ（GBM）。経路の確認用で、判定には使わない。

| | |
|---|---|
| 使う場面 | --smoke。load_* が内部で呼ぶ |
| 入力 | sym（未使用）、rng、n: 本数、freq: pandas の頻度、start: 開始日 |
| 返り値 | DataFrame（time, open, high, low, close, volume） |
| 禁止 | smoke の結果を結果 JSON の判定に使わない（smoke_ 接頭辞で分ける）。rng を渡さないと全銘柄が同じ系列になる |

### `exists_sym(sym, kind='D1_fromH1')`  — `data.py:140`

data_<sym>_<kind>.csv があるか。

| | |
|---|---|
| 使う場面 | 銘柄ループの前。無い銘柄は missing に記録する |
| 入力 | sym、kind: "D1_fromH1" か "H1_dukascopy" など |
| 返り値 | bool |
| 禁止 | 無い銘柄を黙って飛ばさない（JSON の missing に書く） |

### `syms_available(syms, kind='D1_fromH1', smoke=False)`  — `data.py:151`

銘柄リストを「ある／ない」に分ける。

| | |
|---|---|
| 使う場面 | run の最初。ok だけを回し、missing を JSON に入れる |
| 入力 | syms、kind、smoke（True なら全部ある扱い） |
| 返り値 | (ok, missing) |
| 禁止 | missing を空だと仮定しない |

### `check_gaps(df, bar='H1', min_ratio=0.8, gap_hours=None)`  — `data.py:166`

欠損の点検。月ごとの本数の不足と、暦の上の長い空白の両方を見る。load_* の返り値（high==low を除いた後）に使う。

| | |
|---|---|
| 使う場面 | 読み込みの直後。欠けが 1 件でもあれば結果 JSON に残し、欠けた期間を除いた結果も並べる |
| 入力 | df: time 列を持つ DataFrame（load_* の返り値）、bar: "H1"/"M15"/"H4"/"D1"、min_ratio: 本数がこの比を下回る月を欠けとする、gap_hours: これより長い空白を欠けとする [h]（省略で足種の既定: H1/M15/H4=96、D1=168） |
| 返り値 | {"months", "missing_months", "missing": ["2019-03", ...], "worst_ratio", "n_gaps", "max_gap_h", "gaps": [{"from","to","hours"}...上位5], "first", "last"} |
| 禁止 | 欠けを「データなし」と同じに扱わない（2026-09-30 の事故）。生データ（埋め足つき）で点検しない（Q191: 週末の埋め足で比が 1.0 に見える） |

### `health(syms, kind='H1_dukascopy', bar=None, min_ratio=0.8, gap_hours=None)`  — `data.py:203`

銘柄ごとに 成功／データなし／失敗 を区別し、load_* と同じ前処理（high==low を除く）の後で check_gaps をまとめる。

| | |
|---|---|
| 使う場面 | run の最初に 1 回。返り値をそのまま結果 JSON の "data_health" に入れる。failed が 1 件でもあれば結論を「確定」にしない |
| 入力 | syms、kind（"H1_dukascopy"・"D1_fromH1" など）、bar（省略で kind から推定）、min_ratio、gap_hours |
| 返り値 | {"ok", "no_data", "failed": {sym: 例外}, "gaps": {sym: check_gaps の結果（欠けがある銘柄だけ）}, "n_gap_syms", "n_dup": {sym: 重複行数（あれば）}} |
| 禁止 | failed が 1 件でもあるのに結果を「確定」にしない。gaps が空でないのに空白を無視して年単位の平均を取らない |


## 段階: 合図

### `tsmom_pos(close, L)`  — `signals.py:7`

時系列モメンタム: L 本前より高ければ +1、低ければ −1。

| | |
|---|---|
| 使う場面 | 順張りの基準戦略。lookback を振るときは L を params に置く |
| 入力 | close: 長さ n、L: 本数（int） |
| 返り値 | 長さ n の ±1/0（先頭 L 本は 0） |
| 禁止 | 返り値を shift しない（pnl_bp がずらす） |

### `sma_pos(close, n)`  — `signals.py:21`

単純移動平均との位置: 終値が n 本 SMA より上なら +1、下なら −1。

| | |
|---|---|
| 使う場面 | MA 系の順張り・逆張りの基準 |
| 入力 | close: 長さ n、n: 窓（int） |
| 返り値 | 長さ n の ±1/0（SMA が無い先頭は 0） |
| 禁止 | 返り値を shift しない |

### `atr(high, low, close, n=20)`  — `signals.py:36`

ATR（真の値幅の n 本単純平均）。

| | |
|---|---|
| 使う場面 | 損切り幅・ボラ調整・フィルタの閾値 |
| 入力 | high/low/close: 長さ n の配列、n: 窓 |
| 返り値 | 長さ n（先頭 n−1 本は NaN）。価格単位 |
| 禁止 | 返り値を shift しない。pos[t] に ATR[t] を使ってよい（pnl_bp が 1 本ずらす） |

### `rsi(close, n)`  — `signals.py:50`

RSI（Wilder の指数平滑、alpha=1/n）。

| | |
|---|---|
| 使う場面 | 逆張り・過熱の閾値 |
| 入力 | close: 長さ n、n: 期間 |
| 返り値 | 長さ n の 0〜100（先頭は NaN） |
| 禁止 | 返り値を shift しない。pos[t] に RSI[t] を使ってよい（pnl_bp が 1 本ずらす）。下落が無い区間は NaN になる（100 ではない） |


## 段階: 損益

### `cost_bp_oneway(sym, close, rel=None)`  — `costs.py:17`

片道コスト [bp] の列（価格に対する比）。

| | |
|---|---|
| 使う場面 | pnl_bp の直前。段階1は COST_RT の保守値を使う。暗号資産など表に無い銘柄は rel=CRYPTO_COST_RT_REL を渡す |
| 入力 | sym: 銘柄名（COST_RT の鍵）、close: 長さ n の終値、rel: 往復の相対コスト（比。省略で COST_RT） |
| 返り値 | 長さ n の片道コスト [bp] |
| 禁止 | 業者固有のコストをここに足さない（段階2は出口側で判定する） |

### `pnl_bp(pos, close, cost_oneway_bp)`  — `costs.py:30`

ポジションと終値から日次（足ごと）の損益 [bp]。pos[t] は t の終値で決めて t+1 のリターンに効く。

| | |
|---|---|
| 使う場面 | 合図を作った直後。コスト0（cost を 0 列にする）と COST_RT 版の2本を必ず並べる |
| 入力 | pos: 長さ n の ±1/0（t の終値で決めた値をそのまま）、close: 長さ n、cost_oneway_bp: 長さ n [bp]（cost_bp_oneway の返り値） |
| 返り値 | 長さ n の損益 [bp]。pnl[t+1] = pos[t]*ret[t+1]*1e4 − |pos[t]−pos[t−1]|*片道[bp]。先頭は 0 |
| 禁止 | pos 側で shift しない（ここで 1 本ずらすので二重にずれる）。close に未来の値を混ぜない。「保有なし」を NaN で表さない（0 にする。NaN は 0 に置き換えて警告する） |


## 段階: 統計

### `tstat(x)`  — `metrics.py:9`

平均の t 値（iid 前提、ddof=1）。

| | |
|---|---|
| 使う場面 | 年単位平均など、自己相関が無いとみなせる標本。日次損益には nw_t を使う |
| 入力 | x: 1 次元配列（NaN は落とす） |
| 返り値 | float（n<2 か分散 0 なら NaN） |
| 禁止 | 自己相関のある日次系列にそのまま使わない |

### `nw_t(x, lag=5)`  — `metrics.py:23`

Newey-West（Bartlett 核）の t 値。

| | |
|---|---|
| 使う場面 | 日次・時間足の損益や重なりのあるリターンの平均の検定 |
| 入力 | x: 1 次元配列（NaN は落とす）、lag: ラグ数（既定 5。保有期間に合わせる） |
| 返り値 | float（n<3 なら NaN） |
| 禁止 | lag を結果を見てから変えない（事前に固定） |

### `spearman(x, y)`  — `metrics.py:45`

スピアマンの順位相関。

| | |
|---|---|
| 使う場面 | IC（予測と実現の順位相関）、パラメータと成績の単調性の確認 |
| 入力 | x, y: 同じ長さの配列（どちらかが NaN の行は落とす） |
| 返り値 | float（n<3 なら NaN） |
| 禁止 | IC の改善だけで採用しない（本番指標と帰無を併記する） |

### `max_drawdown(pnl)`  — `metrics.py:63`

累積損益のピークからの最大の落ち込み（負の値、pnl と同じ単位）。

| | |
|---|---|
| 使う場面 | 成績の要約。sharpe_ann と並べて書く |
| 入力 | pnl: 長さ n の損益（bp など加算できる単位） |
| 返り値 | float ≤ 0（空なら NaN）。NaN は 0（損益なし）として累積する（sharpe_ann が NaN を落とすのと同じ方針） |
| 禁止 | 複利の資産曲線に使わない（加算の損益用） |

### `sharpe_ann(pnl, per_year=252)`  — `metrics.py:75`

年率シャープ（平均/標準偏差×√per_year、ddof=1）。NaN は落として計算する。

| | |
|---|---|
| 使う場面 | 成績の要約。日足は 252、H1 は 24*260 など足の本数を per_year に渡す |
| 入力 | pnl: 長さ n の損益、per_year: 年あたりの足の本数 |
| 返り値 | float（n≤2 か分散 0 なら NaN） |
| 禁止 | 無リスク金利を引かない（bp の超過損益が前提）。年率 2 超は先読み・リークを疑う。「保有なし」を NaN にしない（落とされて稼働率の分だけ膨らむ。0 にする） |

### `sharpe_ann_n(pnl, per_year=252)`  — `metrics.py:87`

sharpe_ann と同じ値に、使った本数と落とした NaN の数を添える。

| | |
|---|---|
| 使う場面 | 結果 JSON に「何本で計算したか」を残すとき。n_dropped が 0 でなければ理由を書く |
| 入力 | pnl、per_year |
| 返り値 | {"sharpe", "n", "n_dropped"} |
| 禁止 | n_dropped>0 を黙って通さない |

### `qlike(s2_pred, r2)`  — `metrics.py:99`

QLIKE 損失（分散予測の評価。小さいほど良い）。

| | |
|---|---|
| 使う場面 | HAR などボラ予測の比較 |
| 入力 | s2_pred: 予測分散、r2: 実現分散（同じ長さ。どちらかが非正・NaN の行は落とす） |
| 返り値 | float（有効な行が 2 以下なら NaN） |
| 禁止 | 水準の違う銘柄を混ぜて平均しない |

### `by_year_stats(df, col, year_col='year', y0=0, y1=9999, min_rows=20)`  — `metrics.py:112`

年を単位にした平均と t（sym 列があれば年の中で銘柄平均してから）。行数が min_rows 未満の年は数えない。

| | |
|---|---|
| 使う場面 | 期間分割（全期間／前半／後半）の判定値。日次の t より保守的 |
| 入力 | df: year（と sym）と col を持つ DataFrame、col: 集計する列、y0/y1: 年の範囲 [y0, y1)、min_rows: 年あたりの最少行数（既定 20。レビュー H3: 3 日しかない年が全体を −165bp に引っ張った例） |
| 返り値 | {"n_years", "mean", "t", "min_rows_in_year", "years_dropped"} |
| 禁止 | 年数が 5 未満の区間で t を判定に使わない（記述にとどめる）。years_dropped が空でないのに黙って通さない |

### `cluster_t(df, col, by='time', lag=5)`  — `metrics.py:136`

束ねた t（改善判定.md の既定）: by（日付など）ごとに col を平均した系列に nw_t を当てる。銘柄をまたぐ同じ日の相関を 1 本に束ねる。

| | |
|---|---|
| 使う場面 | 複数銘柄の日次損益をまとめて 1 つの t にするとき（銘柄ごとの t を足し合わせない） |
| 入力 | df: by と col を持つ DataFrame、col、by: 束ねる鍵、lag: nw_t のラグ |
| 返り値 | {"t", "n_clusters", "mean"} |
| 禁止 | 銘柄 × 日の行をそのまま tstat に入れない（独立でない） |


## 段階: 帰無

### `null_degenerate(null, min_unique=20)`  — `multiple.py:8`

帰無分布が一点に潰れているか（Q145 の事故: 2.5 点と 97.5 点が同じなのに z=14 が出た）。

| | |
|---|---|
| 使う場面 | z_of・perm_p の内部。自分で帰無を要約するときも先に呼ぶ |
| 入力 | null: 帰無分布、min_unique: これ未満のユニーク値なら退化とみなす |
| 返り値 | bool |
| 禁止 | 退化した帰無の z を判定に使わない |

### `z_of(obs, null)`  — `multiple.py:23`

観測値の帰無分布に対する z と百分位。帰無が退化していれば (nan, nan)。

| | |
|---|---|
| 使う場面 | 並べ替え（perm_within・block_perm・circ_shift）で作った帰無分布と観測値を比べる |
| 入力 | obs: 観測値、null: 帰無分布の配列（B 個。NaN は落とす） |
| 返り値 | (z, pct)。pct は null < obs の割合。帰無の 2.5 点と 97.5 点が同じなら退化として (nan, nan) |
| 禁止 | B<100 の帰無分布で判定しない（経路確認のみ）。z が桁外れ（|z|>20）なら null_summary で分位点を見る |

### `perm_p(obs, null, side='greater')`  — `multiple.py:37`

並べ替え検定の p 値 (1 + #{null が obs 以上}) / (B + 1)（改善判定.md の式）。

| | |
|---|---|
| 使う場面 | holm に渡す p を作るとき。1−pct（0 になりうる）や正規近似で p を作らない |
| 入力 | obs、null、side: "greater"（obs が大きいほど良い）/"less"/"two" |
| 返り値 | float（退化なら nan） |
| 禁止 | side を結果を見てから変えない |

### `null_summary(obs, null)`  — `multiple.py:58`

帰無分布の要約（B・分位点・z・pct・perm_p・退化フラグ）を dict で返す。

| | |
|---|---|
| 使う場面 | 結果 JSON に帰無の形を残すとき（z の桁外れの点検に使う） |
| 入力 | obs、null |
| 返り値 | {"B","q025","q500","q975","z","pct","p_perm","degenerate"} |
| 禁止 | — |

### `perm_within(rng, x, groups)`  — `multiple.py:73`

groups（例: 年）の中で x を並べ替える。

| | |
|---|---|
| 使う場面 | 年ごとの水準を保ったまま日付との対応を壊す帰無 |
| 入力 | rng: np.random.Generator、x: 長さ n、groups: 長さ n のラベル |
| 返り値 | 長さ n の並べ替え後の x |
| 禁止 | rng を毎回作り直さない（seed 固定の rng を渡す） |

### `block_perm(rng, x, block)`  — `multiple.py:88`

block 本ごとの塊を並べ替える（塊の中の順序は保つ）。

| | |
|---|---|
| 使う場面 | 自己相関を保ったまま対応を壊す帰無。block は保有期間の数倍 |
| 入力 | rng、x: 長さ n、block: 塊の長さ（int） |
| 返り値 | 長さ n |
| 禁止 | block を結果を見てから変えない |

### `circ_shift(rng, x, min_shift=1)`  — `multiple.py:102`

循環シフト（合図とリターンの対応を壊し、合図の自己相関は保つ）。

| | |
|---|---|
| 使う場面 | 合図列の帰無。合図の持続性が結果に効くとき |
| 入力 | rng、x: 長さ n、min_shift: 最小のずらし（持続する合図では保有期間の数倍にする） |
| 返り値 | 長さ n。k は [min_shift, n−min_shift] の一様（旧雛形は上限が 1 つ足りなかった。レビュー 2026-10-13） |
| 禁止 | 短い系列（n<10×min_shift）で使わない |


## 段階: 判定

### `holm(pvals)`  — `multiple.py:115`

Holm の段階的補正（補正後 p）。有限な p だけなら雛形 91 本と同じ値。NaN は m に数えるが補正後も NaN。

| | |
|---|---|
| 使う場面 | 複数の判定（銘柄×期間など）を同時に有意と言うとき。n_tests を事前に宣言した数と合わせる |
| 入力 | pvals: p 値の配列 |
| 返り値 | 同じ長さの補正後 p（NaN はそのまま） |
| 禁止 | 検定の数を結果を見てから減らさない |

### `holm_sig(pvals, alpha=0.05)`  — `multiple.py:135`

holm の補正後 p と有意フラグの両方を返す（旧 q147・q153 の形）。

| | |
|---|---|
| 使う場面 | 有意フラグを JSON に入れたいとき |
| 入力 | pvals、alpha: 有意水準 |
| 返り値 | (adj, sig)。sig は bool 配列（NaN は False） |
| 禁止 | alpha を事前登録の値以外にしない |

### `default_judge(res, spec)`  — `runner.py:76`

既定の 3 分岐。main_param のコスト後 bp（all15・年単位）が前後半とも >0 かつ holm 補正後 p<0.05 → 支持。全期間の z<1 → 棄却。ほか → 未確定。

| | |
|---|---|
| 使う場面 | Runner(judge=None) のとき。独自の規則にするなら同じ署名の関数を渡し、規則の文を Spec.reject_if に書く |
| 入力 | res: Runner が組んだ結果 dict、spec |
| 返り値 | str（"支持: …"／"棄却: …"／"未確定: …"） |
| 禁止 | 判定に使う数を結果を見てから変えない |


## 段階: 保存

### `fmt(x, nd=4)`  — `metrics.py:148`

JSON 用の丸め（NaN・None は None）。雛形の f と同じ（f は 1 文字で for 変数に上書きされやすいので新規は fmt を使う）。

| | |
|---|---|
| 使う場面 | 結果 dict に数値を入れるとき |
| 入力 | x: 数値、nd: 小数桁 |
| 返り値 | float か None |
| 禁止 | 計算の途中で使わない（丸め誤差が積もる）。`for f in ...` のような変数名を使わない |

### `_json_default(o)`  — `io.py:33`

numpy・Timestamp を JSON にできる形へ。

| | |
|---|---|
| 使う場面 | write_result の内部。json.dump(default=_json_default) |
| 入力 | o: 任意のオブジェクト |
| 返り値 | bool / int / float / list / str（NaN は None） |
| 禁止 | — |

### `sanitize(o)`  — `io.py:54`

結果 dict を JSON に安全な形へ再帰的に直す（NaN/inf → None、np.bool_ → bool、np.float64 → float、tuple → list）。

| | |
|---|---|
| 使う場面 | write_result の内部。json.dumps(allow_nan=False) を通す前 |
| 入力 | o: dict / list / スカラー |
| 返り値 | 同じ構造 |
| 禁止 | — |

### `write_result(qid, res, smoke, extra_csv=None, out_dir=None, here=None)`  — `io.py:79`

results/<qid>_result_<ts>.json（smoke は smoke_ 接頭辞）と任意の CSV を書く。既存のファイルは上書きしない。

| | |
|---|---|
| 使う場面 | run の返り値を main で保存する。1 回の実行で 1 回 |
| 入力 | qid、res: dict、smoke: bool、extra_csv: {名前: DataFrame}、out_dir: 省略で <here>/results、here: 呼び出し元の __file__ のフォルダ（省略で sys.argv[0] のフォルダ。Runner や Jupyter からは必ず渡す） |
| 返り値 | 書いた JSON のパス |
| 禁止 | 結果を上書きしない（同じ秒なら _1, _2 を付ける）。巨大な配列を JSON に入れない（CSV へ）。res に qid/smoke/generated を入れない（ここで付ける） |

### `render_readme(spec, script, status=None, script_kind='Runner 型', elapsed=None, today=None)`  — `readme.py:47`

Spec から README.md の本文を作る。

| | |
|---|---|
| 使う場面 | /lab-plan のコーディング時（`python3 <script> --readme`）。実行後の結果の節は人が書く |
| 入力 | spec: Spec、script: スクリプトのファイル名、status: 状態の 1 文（省略で「設計とコードまで。実行と解釈は未」）、script_kind: "Runner 型"|"土台を直接使う型"、elapsed: 実行時間のメモ、today: 日付 |
| 返り値 | str（Markdown） |
| 禁止 | 結果の節をここで埋めない（解釈は人） |

