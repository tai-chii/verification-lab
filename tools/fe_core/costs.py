# -*- coding: utf-8 -*-
"""コスト（段階1の保守値）と損益。雛形 91 本・COST_RT 116 本で一致していた実装。"""
import numpy as np

# 往復コスト（価格単位・段階1の保守値。Q136〜Q190 と同じ表）
COST_RT = {"EURUSD": .0002, "GBPUSD": .0002, "AUDUSD": .0002, "USDCHF": .0002, "USDCAD": .0002,
           "USDJPY": .02, "EURJPY": .02, "GBPJPY": .02, "XAUUSD": 0.6,
           "XAGUSD": 0.04, "WTI": 0.06, "UKOIL": 0.06, "US500": 1.0, "USTECH": 3.0, "BTCUSD": 40.0}
CRYPTO_COST_RT_REL = 30e-4  # 暗号資産: 往復 30bp の仮置き（Q152 と同じ）


def cost_bp_oneway(sym, close, rel=None):
    """片道コスト [bp] の列（価格に対する比）。
    使う場面: pnl_bp の直前。段階1は COST_RT の保守値を使う。暗号資産など表に無い銘柄は rel=CRYPTO_COST_RT_REL を渡す
    入力: sym: 銘柄名（COST_RT の鍵）、close: 長さ n の終値、rel: 往復の相対コスト（比。省略で COST_RT）
    返り値: 長さ n の片道コスト [bp]
    禁止: 業者固有のコストをここに足さない（段階2は出口側で判定する）
    段階: 損益
    """
    if rel is not None:
        return np.full(len(close), rel / 2 * 1e4)
    return COST_RT[sym] / 2 / np.asarray(close, float) * 1e4


def pnl_bp(pos, close, cost_oneway_bp):
    """ポジションと終値から日次（足ごと）の損益 [bp]。pos[t] は t の終値で決めて t+1 のリターンに効く。
    使う場面: 合図を作った直後。コスト0（cost を 0 列にする）と COST_RT 版の2本を必ず並べる
    入力: pos: 長さ n の ±1/0（t の終値で決めた値をそのまま）、close: 長さ n、cost_oneway_bp: 長さ n [bp]（cost_bp_oneway の返り値）
    返り値: 長さ n の損益 [bp]。pnl[t+1] = pos[t]*ret[t+1]*1e4 − |pos[t]−pos[t−1]|*片道[bp]。先頭は 0
    禁止: pos 側で shift しない（ここで 1 本ずらすので二重にずれる）。close に未来の値を混ぜない
    段階: 損益
    """
    c = np.asarray(close, float); pos = np.asarray(pos, float)
    ret = np.zeros(len(c)); ret[1:] = c[1:] / c[:-1] - 1
    held = np.r_[0.0, pos[:-1]]
    prev = np.r_[0.0, held[:-1]]
    cost = np.abs(held - prev) * np.r_[0.0, cost_oneway_bp[:-1]]
    return held * ret * 1e4 - cost
