# -*- coding: utf-8 -*-
"""帰無分布と多重比較。holm は有限な p に対して多数派（91 本）と同じ値を返し、NaN を安全に扱う。"""
import math

import numpy as np


def z_of(obs, null):
    """観測値の帰無分布に対する z と百分位。
    使う場面: 並べ替え（perm_within・block_perm・circ_shift）で作った帰無分布と観測値を比べる
    入力: obs: 観測値、null: 帰無分布の配列（B 個。NaN は落とす）
    返り値: (z, pct)。pct は null < obs の割合
    禁止: B<100 の帰無分布で判定しない（経路確認のみ）
    段階: 帰無
    """
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null < obs).mean())


def perm_within(rng, x, groups):
    """groups（例: 年）の中で x を並べ替える。
    使う場面: 年ごとの水準を保ったまま日付との対応を壊す帰無
    入力: rng: np.random.Generator、x: 長さ n、groups: 長さ n のラベル
    返り値: 長さ n の並べ替え後の x
    禁止: rng を毎回作り直さない（seed 固定の rng を渡す）
    段階: 帰無
    """
    x = np.asarray(x, float).copy(); g = np.asarray(groups)
    for v in np.unique(g):
        idx = np.where(g == v)[0]
        x[idx] = x[rng.permutation(idx)]
    return x


def block_perm(rng, x, block):
    """block 本ごとの塊を並べ替える（塊の中の順序は保つ）。
    使う場面: 自己相関を保ったまま対応を壊す帰無。block は保有期間の数倍
    入力: rng、x: 長さ n、block: 塊の長さ（int）
    返り値: 長さ n
    禁止: block を結果を見てから変えない
    段階: 帰無
    """
    x = np.asarray(x, float); n = len(x); nb = int(math.ceil(n / block))
    order = rng.permutation(nb)
    out = np.concatenate([x[b * block:(b + 1) * block] for b in order])
    return out[:n]


def circ_shift(rng, x, min_shift=1):
    """循環シフト（合図とリターンの対応を壊し、合図の自己相関は保つ）。
    使う場面: 合図列の帰無。合図の持続性が結果に効くとき
    入力: rng、x: 長さ n、min_shift: 最小のずらし
    返り値: 長さ n
    禁止: 短い系列（n<10×min_shift）で使わない
    段階: 帰無
    """
    x = np.asarray(x, float); n = len(x)
    k = int(rng.integers(min_shift, max(min_shift + 1, n - min_shift)))
    return np.roll(x, k)


def holm(pvals):
    """Holm の段階的補正（補正後 p）。有限な p だけなら雛形 91 本と同じ値。NaN は m に数えるが補正後も NaN。
    使う場面: 複数の判定（銘柄×期間など）を同時に有意と言うとき。n_tests を事前に宣言した数と合わせる
    入力: pvals: p 値の配列
    返り値: 同じ長さの補正後 p（NaN はそのまま）
    禁止: 検定の数を結果を見てから減らさない
    段階: 判定
    """
    p = np.asarray(pvals, float); m = len(p)
    fin = np.isfinite(p)
    pf = np.where(fin, p, np.inf)
    order = np.argsort(pf, kind="stable"); adj = np.full(m, np.nan)
    run = 0.0
    for i, k in enumerate(order):
        if not fin[k]:
            continue
        run = max(run, (m - i) * p[k]); adj[k] = min(1.0, run)
    return adj


def holm_sig(pvals, alpha=0.05):
    """holm の補正後 p と有意フラグの両方を返す（旧 q147・q153 の形）。
    使う場面: 有意フラグを JSON に入れたいとき
    入力: pvals、alpha: 有意水準
    返り値: (adj, sig)。sig は bool 配列（NaN は False）
    禁止: alpha を事前登録の値以外にしない
    段階: 判定
    """
    adj = holm(pvals)
    return adj, np.isfinite(adj) & (adj < alpha)
