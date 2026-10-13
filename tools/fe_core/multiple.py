# -*- coding: utf-8 -*-
"""帰無分布と多重比較。holm は有限な p に対して多数派（91 本）と同じ値を返し、NaN を安全に扱う。"""
import math

import numpy as np


def z_of(obs, null):
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null < obs).mean())


def perm_within(rng, x, groups):
    """groups（例: 年）の中で x を並べ替える。"""
    x = np.asarray(x, float).copy(); g = np.asarray(groups)
    for v in np.unique(g):
        idx = np.where(g == v)[0]
        x[idx] = x[rng.permutation(idx)]
    return x


def block_perm(rng, x, block):
    """block 本ごとの塊を並べ替える（塊の中の順序は保つ）。"""
    x = np.asarray(x, float); n = len(x); nb = int(math.ceil(n / block))
    order = rng.permutation(nb)
    out = np.concatenate([x[b * block:(b + 1) * block] for b in order])
    return out[:n]


def circ_shift(rng, x, min_shift=1):
    """循環シフト（合図とリターンの対応を壊し、合図の自己相関は保つ）。"""
    x = np.asarray(x, float); n = len(x)
    k = int(rng.integers(min_shift, max(min_shift + 1, n - min_shift)))
    return np.roll(x, k)


def holm(pvals):
    """Holm の段階的補正。補正後 p を返す。
    有限な p だけなら雛形 91 本と同じ値。NaN は m に数えるが補正後も NaN（有意にしない）。"""
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
    """holm の補正後 p と有意フラグの両方を返す（旧 q147・q153 の形）。"""
    adj = holm(pvals)
    return adj, np.isfinite(adj) & (adj < alpha)
