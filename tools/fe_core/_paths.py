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
FX8 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD", "EURJPY", "GBPJPY"]
FX6 = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCHF", "USDCAD"]  # ドル建て先進国（Q019・Q054 と同じ）
TREND7 = ["XAUUSD", "XAGUSD", "WTI", "UKOIL", "US500", "USTECH", "BTCUSD"]
SYMS = FX8 + TREND7
CRYPTO = ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "ADAUSD", "BCHUSD", "XLMUSD", "EOSUSD", "LNKUSD", "DOTUSD", "SOLUSD"]
SPLIT_YEAR = 2017
SEED = 20261010
GROUPS = {"all15": SYMS, "fx8": FX8, "trend7": TREND7}
