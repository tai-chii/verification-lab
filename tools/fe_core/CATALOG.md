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
| `COST_RT` | `{'EURUSD': 0.0002, 'GBPUSD': 0.0002, 'AUDUSD': 0.0002, 'USDCHF': 0.0002, 'USDCAD': 0.0002, 'USDJPY': 0.02, 'EURJPY': 0.02, 'GBPJPY': 0.02, 'XAUUSD': 0.6, 'XA...` | 往復コスト（価格単位・段階1の保守値。Q136〜Q190 と同じ表） | `costs.py:6` |
| `CRYPTO_COST_RT_REL` | `0.003` | 暗号資産: 往復 30bp の仮置き（Q152 と同じ） | `costs.py:9` |

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

### `parse_args(default_B=300, extra=None, default_seed=SEED, argv=None)`  — `io.py:14`

共通の引数（--B 帰無の回数、--smoke、--seed）。

| | |
|---|---|
| 使う場面 | main の最初。検証固有の引数は extra(ap) で足す |
| 入力 | default_B、extra: ArgumentParser を受けて add_argument する関数、default_seed、argv（テスト用） |
| 返り値 | argparse.Namespace |
| 禁止 | 事前登録した B・seed を結果を見てから変えない |


## 段階: 読み込み

### `_read(path)`  — `data.py:12`

CSV を読み、time を datetime にして並べ替え・重複除去する（生の読み込み）。

| | |
|---|---|
| 使う場面 | load_* の中。直接使うのは data_*.csv 以外の表を読むときだけ |
| 入力 | path: CSV のパス（time 列が必要） |
| 返り値 | DataFrame（time 昇順・重複なし） |
| 禁止 | 失敗を空の DataFrame で握りつぶさない（例外はそのまま上げる） |

### `load_d1(sym, smoke=False, rng=None)`  — `data.py:26`

UTC 日足（data_<sym>_D1_fromH1.csv）。値動きのない足（high==low）は除く。

| | |
|---|---|
| 使う場面 | 日足の検証の読み込み。--smoke のときは合成データ |
| 入力 | sym: 銘柄、smoke: 合成データにするか、rng: smoke 用の Generator |
| 返り値 | DataFrame（time, open, high, low, close, ret, year）。ret は比（bp ではない） |
| 禁止 | ret の単位を変えた列を同じ名前で作らない（旧 q284・q286 で bp 版があり事故の種） |

### `load_csv(name, smoke=False, rng=None, freq='h', n=20000, start='2015-01-01')`  — `data.py:44`

任意の data_<name>.csv（H1/H4/M15/yahoo/ask など）を読む。

| | |
|---|---|
| 使う場面 | load_d1・load_h1 に無い足種や別ソース |
| 入力 | name: data_ の後ろの名前、smoke/rng/freq/n/start: 合成データの設定 |
| 返り値 | DataFrame（生の列。ret・year は付かない） |
| 禁止 | 同じ銘柄を別ソースで混ぜて 1 本の系列にしない |

### `load_h1(sym, smoke=False, rng=None, n=60000, start='2015-01-01')`  — `data.py:57`

UTC 1 時間足（data_<sym>_H1_dukascopy.csv）。値動きのない足は除く。

| | |
|---|---|
| 使う場面 | 時間帯・イベント研究・H1 からの日足作成（h1_to_d1） |
| 入力 | sym、smoke、rng、n/start: 合成データの長さと開始 |
| 返り値 | DataFrame（time, open, high, low, close, volume, ret, year, hour, dow） |
| 禁止 | 読んだ後に check_gaps／health で欠損を点検せずに判定しない |

### `h1_to_d1(h1, cutoff_hour=0)`  — `data.py:74`

H1 を「cutoff_hour（UTC）始まり」の日足に束ねる。日付ラベルは区間の開始日。

| | |
|---|---|
| 使う場面 | 日の区切り（NY 17 時など）を変えた日足が要るとき |
| 入力 | h1: load_h1 の返り値、cutoff_hour: 区切りの時刻（UTC） |
| 返り値 | DataFrame（time, open, high, low, close, volume, nbars, ret, year）。本数 6 未満の日は除く |
| 禁止 | cutoff を結果を見てから変えない（Q140 系の「区切り依存」を再現する） |

### `_smoke_ohlc(sym, rng, n, freq, start)`  — `data.py:93`

合成データ（GBM）。経路の確認用で、判定には使わない。

| | |
|---|---|
| 使う場面 | --smoke。load_* が内部で呼ぶ |
| 入力 | sym（未使用）、rng、n: 本数、freq: pandas の頻度、start: 開始日 |
| 返り値 | DataFrame（time, open, high, low, close, volume） |
| 禁止 | smoke の結果を結果 JSON の判定に使わない（smoke_ 接頭辞で分ける） |

### `exists_sym(sym, kind='D1_fromH1')`  — `data.py:112`

data_<sym>_<kind>.csv があるか。

| | |
|---|---|
| 使う場面 | 銘柄ループの前。無い銘柄は missing に記録する |
| 入力 | sym、kind: "D1_fromH1" か "H1_dukascopy" など |
| 返り値 | bool |
| 禁止 | 無い銘柄を黙って飛ばさない（JSON の missing に書く） |

### `syms_available(syms, kind='D1_fromH1', smoke=False)`  — `data.py:123`

銘柄リストを「ある／ない」に分ける。

| | |
|---|---|
| 使う場面 | run の最初。ok だけを回し、missing を JSON に入れる |
| 入力 | syms、kind、smoke（True なら全部ある扱い） |
| 返り値 | (ok, missing) |
| 禁止 | missing を空だと仮定しない |

### `check_gaps(df, bar='H1', min_ratio=0.5)`  — `data.py:141`

月ごとの本数を数え、期待本数の min_ratio 未満の月と行の無い月を「欠け」として返す。

| | |
|---|---|
| 使う場面 | 読み込みの直後。欠けが 1 月でもあれば結果 JSON に残し、欠けた期間を除いた結果も並べる |
| 入力 | df: time 列を持つ DataFrame、bar: "H1"/"M15"/"H4"/"D1"、min_ratio: 欠けと見なす比 |
| 返り値 | {"months", "missing_months", "missing": ["2019-03", ...], "worst_ratio"} |
| 禁止 | 欠けを「データなし」と同じに扱わない（2026-09-30 の事故） |

### `health(syms, kind='H1_dukascopy', bar=None, min_ratio=0.5)`  — `data.py:170`

銘柄ごとに 成功／データなし／失敗 を区別し、欠けのある銘柄の check_gaps をまとめる。

| | |
|---|---|
| 使う場面 | run の最初に 1 回。返り値をそのまま結果 JSON の "data_health" に入れる |
| 入力 | syms、kind、bar（省略で kind から推定）、min_ratio |
| 返り値 | {"ok", "no_data", "failed": {sym: 例外}, "gaps": {sym: check_gaps}, "n_gap_syms"} |
| 禁止 | failed が 1 件でもあるのに結果を「確定」にしない |


## 段階: 損益

### `cost_bp_oneway(sym, close, rel=None)`  — `costs.py:12`

片道コスト [bp] の列（価格に対する比）。

| | |
|---|---|
| 使う場面 | pnl_bp の直前。段階1は COST_RT の保守値を使う。暗号資産など表に無い銘柄は rel=CRYPTO_COST_RT_REL を渡す |
| 入力 | sym: 銘柄名（COST_RT の鍵）、close: 長さ n の終値、rel: 往復の相対コスト（比。省略で COST_RT） |
| 返り値 | 長さ n の片道コスト [bp] |
| 禁止 | 業者固有のコストをここに足さない（段階2は出口側で判定する） |

### `pnl_bp(pos, close, cost_oneway_bp)`  — `costs.py:25`

ポジションと終値から日次（足ごと）の損益 [bp]。pos[t] は t の終値で決めて t+1 のリターンに効く。

| | |
|---|---|
| 使う場面 | 合図を作った直後。コスト0（cost を 0 列にする）と COST_RT 版の2本を必ず並べる |
| 入力 | pos: 長さ n の ±1/0（t の終値で決めた値をそのまま）、close: 長さ n、cost_oneway_bp: 長さ n [bp]（cost_bp_oneway の返り値） |
| 返り値 | 長さ n の損益 [bp]。pnl[t+1] = pos[t]*ret[t+1]*1e4 − |pos[t]−pos[t−1]|*片道[bp]。先頭は 0 |
| 禁止 | pos 側で shift しない（ここで 1 本ずらすので二重にずれる）。close に未来の値を混ぜない |


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

### `spearman(x, y)`  — `metrics.py:43`

スピアマンの順位相関。

| | |
|---|---|
| 使う場面 | IC（予測と実現の順位相関）、パラメータと成績の単調性の確認 |
| 入力 | x, y: 同じ長さの配列（どちらかが NaN の行は落とす） |
| 返り値 | float（n<3 なら NaN） |
| 禁止 | IC の改善だけで採用しない（本番指標と帰無を併記する） |

### `max_drawdown(pnl)`  — `metrics.py:61`

累積損益のピークからの最大の落ち込み（負の値、pnl と同じ単位）。

| | |
|---|---|
| 使う場面 | 成績の要約。sharpe_ann と並べて書く |
| 入力 | pnl: 長さ n の損益（bp など加算できる単位） |
| 返り値 | float ≤ 0（空なら NaN） |
| 禁止 | 複利の資産曲線に使わない（加算の損益用） |

### `sharpe_ann(pnl, per_year=252)`  — `metrics.py:73`

年率シャープ（平均/標準偏差×√per_year、ddof=1）。NaN は落として計算する。

| | |
|---|---|
| 使う場面 | 成績の要約。日足は 252、H1 は 24*260 など足の本数を per_year に渡す |
| 入力 | pnl: 長さ n の損益、per_year: 年あたりの足の本数 |
| 返り値 | float（n≤2 か分散 0 なら NaN） |
| 禁止 | 無リスク金利を引かない（bp の超過損益が前提）。年率 2 超は先読み・リークを疑う |

### `qlike(s2_pred, r2)`  — `metrics.py:85`

QLIKE 損失（分散予測の評価。小さいほど良い）。

| | |
|---|---|
| 使う場面 | HAR などボラ予測の比較 |
| 入力 | s2_pred: 予測分散、r2: 実現分散（同じ長さ。どちらかが非正・NaN の行は落とす） |
| 返り値 | float（有効な行が 2 以下なら NaN） |
| 禁止 | 水準の違う銘柄を混ぜて平均しない |

### `by_year_stats(df, col, year_col='year', y0=0, y1=9999)`  — `metrics.py:98`

年を単位にした平均と t（sym 列があれば年の中で銘柄平均してから）。

| | |
|---|---|
| 使う場面 | 期間分割（全期間／前半／後半）の判定値。日次の t より保守的 |
| 入力 | df: year（と sym）と col を持つ DataFrame、col: 集計する列、y0/y1: 年の範囲 [y0, y1) |
| 返り値 | {"n_years", "mean", "t"} |
| 禁止 | 年数が 5 未満の区間で t を判定に使わない（記述にとどめる） |


## 段階: 帰無

### `z_of(obs, null)`  — `multiple.py:8`

観測値の帰無分布に対する z と百分位。

| | |
|---|---|
| 使う場面 | 並べ替え（perm_within・block_perm・circ_shift）で作った帰無分布と観測値を比べる |
| 入力 | obs: 観測値、null: 帰無分布の配列（B 個。NaN は落とす） |
| 返り値 | (z, pct)。pct は null < obs の割合 |
| 禁止 | B<100 の帰無分布で判定しない（経路確認のみ） |

### `perm_within(rng, x, groups)`  — `multiple.py:22`

groups（例: 年）の中で x を並べ替える。

| | |
|---|---|
| 使う場面 | 年ごとの水準を保ったまま日付との対応を壊す帰無 |
| 入力 | rng: np.random.Generator、x: 長さ n、groups: 長さ n のラベル |
| 返り値 | 長さ n の並べ替え後の x |
| 禁止 | rng を毎回作り直さない（seed 固定の rng を渡す） |

### `block_perm(rng, x, block)`  — `multiple.py:37`

block 本ごとの塊を並べ替える（塊の中の順序は保つ）。

| | |
|---|---|
| 使う場面 | 自己相関を保ったまま対応を壊す帰無。block は保有期間の数倍 |
| 入力 | rng、x: 長さ n、block: 塊の長さ（int） |
| 返り値 | 長さ n |
| 禁止 | block を結果を見てから変えない |

### `circ_shift(rng, x, min_shift=1)`  — `multiple.py:51`

循環シフト（合図とリターンの対応を壊し、合図の自己相関は保つ）。

| | |
|---|---|
| 使う場面 | 合図列の帰無。合図の持続性が結果に効くとき |
| 入力 | rng、x: 長さ n、min_shift: 最小のずらし |
| 返り値 | 長さ n |
| 禁止 | 短い系列（n<10×min_shift）で使わない |


## 段階: 判定

### `holm(pvals)`  — `multiple.py:64`

Holm の段階的補正（補正後 p）。有限な p だけなら雛形 91 本と同じ値。NaN は m に数えるが補正後も NaN。

| | |
|---|---|
| 使う場面 | 複数の判定（銘柄×期間など）を同時に有意と言うとき。n_tests を事前に宣言した数と合わせる |
| 入力 | pvals: p 値の配列 |
| 返り値 | 同じ長さの補正後 p（NaN はそのまま） |
| 禁止 | 検定の数を結果を見てから減らさない |

### `holm_sig(pvals, alpha=0.05)`  — `multiple.py:84`

holm の補正後 p と有意フラグの両方を返す（旧 q147・q153 の形）。

| | |
|---|---|
| 使う場面 | 有意フラグを JSON に入れたいとき |
| 入力 | pvals、alpha: 有意水準 |
| 返り値 | (adj, sig)。sig は bool 配列（NaN は False） |
| 禁止 | alpha を事前登録の値以外にしない |


## 段階: 保存

### `f(x, nd=4)`  — `metrics.py:117`

JSON 用の丸め（NaN・None は None）。

| | |
|---|---|
| 使う場面 | 結果 dict に数値を入れるとき |
| 入力 | x: 数値、nd: 小数桁 |
| 返り値 | float か None |
| 禁止 | 計算の途中で使わない（丸め誤差が積もる） |

### `_json_default(o)`  — `io.py:31`

numpy・Timestamp を JSON にできる形へ。

| | |
|---|---|
| 使う場面 | write_result の内部。json.dump(default=_json_default) |
| 入力 | o: 任意のオブジェクト |
| 返り値 | int / float / list / str（NaN は None） |
| 禁止 | — |

### `write_result(qid, res, smoke, extra_csv=None, out_dir=None)`  — `io.py:50`

results/<qid>_result_<ts>.json（smoke は smoke_ 接頭辞）と任意の CSV を書く。

| | |
|---|---|
| 使う場面 | run の返り値を main で保存する。1 回の実行で 1 回 |
| 入力 | qid、res: dict、smoke: bool、extra_csv: {名前: DataFrame}、out_dir: 省略で <スクリプトのフォルダ>/results |
| 返り値 | 書いた JSON のパス |
| 禁止 | 結果を上書きしない（時刻つきで新規に書く）。巨大な配列を JSON に入れない（CSV へ） |

