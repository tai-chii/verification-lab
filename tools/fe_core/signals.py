# -*- coding: utf-8 -*-
"""合図（ポジション・指標）。雛形で全件一致していた実装。"""
import numpy as np
import pandas as pd


def tsmom_pos(close, L):
    """時系列モメンタム: L 本前より高ければ +1、低ければ −1。
    使う場面: 順張りの基準戦略。lookback を振るときは L を params に置く
    入力: close: 長さ n、L: 本数（int）
    返り値: 長さ n の ±1/0（先頭 L 本は 0）
    禁止: 返り値を shift しない（pnl_bp がずらす）
    段階: 合図
    """
    c = np.asarray(close, float)
    s = np.zeros(len(c))
    s[L:] = np.sign(c[L:] - c[:-L])
    return s


def sma_pos(close, n):
    """単純移動平均との位置: 終値が n 本 SMA より上なら +1、下なら −1。
    使う場面: MA 系の順張り・逆張りの基準
    入力: close: 長さ n、n: 窓（int）
    返り値: 長さ n の ±1/0（SMA が無い先頭は 0）
    禁止: 返り値を shift しない
    段階: 合図
    """
    c = pd.Series(np.asarray(close, float))
    m = c.rolling(n).mean().values
    s = np.sign(c.values - m)
    s[np.isnan(m)] = 0.0
    return s


def atr(high, low, close, n=20):
    """ATR（真の値幅の n 本単純平均）。
    使う場面: 損切り幅・ボラ調整・フィルタの閾値
    入力: high/low/close: 長さ n の配列、n: 窓
    返り値: 長さ n（先頭 n−1 本は NaN）。価格単位
    禁止: 返り値を shift しない。pos[t] に ATR[t] を使ってよい（pnl_bp が 1 本ずらす）
    段階: 合図
    """
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    return pd.Series(tr).rolling(n).mean().values


def rsi(close, n):
    """RSI（Wilder の指数平滑、alpha=1/n）。
    使う場面: 逆張り・過熱の閾値
    入力: close: 長さ n、n: 期間
    返り値: 長さ n の 0〜100（先頭は NaN）
    禁止: 返り値を shift しない。pos[t] に RSI[t] を使ってよい（pnl_bp が 1 本ずらす）。下落が無い区間は NaN になる（100 ではない）
    段階: 合図
    """
    c = pd.Series(np.asarray(close, float))
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).values
