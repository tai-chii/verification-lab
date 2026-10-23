# -*- coding: utf-8 -*-
"""パスと定数。雛形（kensho_*_q089〜q286）の冒頭部をそのまま移したもの。数値は変えていない。"""
import os
import sys
import unicodedata

# fe_core/ → tools/ → verification-lab/ → 検証/ → ワークスペース
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))


def _p(*parts):
    """ワークスペース内のパスを作る。macOS 共有の NFD 名に対応（NFC で無ければ NFD で探す）。
    使う場面: DATA_DIR 以外のワークスペース内ファイルを指すとき
    入力: parts: ワークスペースからの相対パスの各要素
    返り値: 絶対パス（str）
    禁止: 絶対パスをハードコードしない
    段階: 共通
    """
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    return os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])


def script_dir():
    """呼び出し元スクリプトのフォルダ（雛形の HERE に相当）。対話実行時はカレント。
    使う場面: write_result の既定の出力先
    入力: なし
    返り値: 絶対パス（str）
    禁止: —
    段階: 共通
    """
    a = sys.argv[0] if sys.argv and sys.argv[0] else ""
    return os.path.dirname(os.path.abspath(a)) if a else os.getcwd()


DATA_DIR = _p("検証", "学問", "金融工学", "作業", "FX", "システムトレード")
# 2026-10-21: 幅を広げた銘柄（S07・48 銘柄）の日足は 検証/_データ/raw/D1 にある。DATA_DIR に無い銘柄だけここを探す（既存 15 銘柄の入力は変えない）
DATA_DIR2 = _p("検証", "_データ", "raw", "D1")


def data_path(sym, kind="D1_fromH1"):
    """data_<sym>_<kind>.csv の実パス。DATA_DIR → DATA_DIR2 の順に探し、無ければ DATA_DIR 側のパスを返す（存在しない）。
    使う場面: load_d1 / exists_sym。S07 の広い銘柄（指数・債券・FX クロス）を読むとき
    入力: sym、kind
    返り値: 絶対パス（str）
    禁止: 既存 15 銘柄の正本を DATA_DIR2 で上書き解決しない（順序を変えない）
    段階: 読み込み
    """
    for d in (DATA_DIR, DATA_DIR2):
        a = os.path.join(d, f"data_{sym}_{kind}.csv")
        if os.path.exists(a):
            return a
    return os.path.join(DATA_DIR, f"data_{sym}_{kind}.csv")

FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
FX6 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD"]  # ドル建て先進国（Q019・Q054 と同じ）
TREND7 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL", "US500", "USTECH", "BTCUSD"]
SYMS = FX8 + TREND7
CRYPTO = ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "ADAUSD", "BCHUSD", "XLMUSD", "EOSUSD", "LNKUSD", "DOTUSD", "SOLUSD"]
SPLIT_YEAR = 2017
SEED = 20261010
# 2026-10-21 S07: 幅を広げた 48 銘柄（_データ/fetch/fetch_dukascopy_d1.py の SYMBOLS と同じ名前）
FX22 = FX8 + ["NZDUSD", "EURGBP", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY", "EURAUD", "EURCAD", "EURCHF", "GBPAUD", "GBPCAD", "GBPCHF", "AUDNZD", "AUDCAD"]
IDX13 = ["US500", "USTECH", "US30", "GER40", "JPN225", "UK100", "FRA40", "ESP35", "EUSTX50", "AUS200", "HKG33", "SUI20", "NLD25"]
CMD8 = ["XAUUSD", "XAGUSD", "WTI", "BRENT", "COPPER", "NATGAS", "XPDUSD", "XPTUSD"]
BOND3 = ["BUND", "USTBOND", "UKGILT"]
CRYPTO2 = ["BTCUSD", "ETHUSD"]
WIDE48 = FX22 + IDX13 + CMD8 + BOND3 + CRYPTO2
GROUPS = {"all15": SYMS, "fx8": FX8, "trend7": TREND7,
          "wide48": WIDE48, "fx22": FX22, "idx13": IDX13, "cmd8": CMD8, "bond3": BOND3}
