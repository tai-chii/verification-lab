# -*- coding: utf-8 -*-
"""帰無分布と多重比較。holm は有限な p に対して多数派（91 本）と同じ値を返し、NaN を安全に扱う。"""
import math

import numpy as np


def null_degenerate(null, min_unique=20):
    """帰無分布が一点に潰れているか（Q145 の事故: 2.5 点と 97.5 点が同じなのに z=14 が出た）。
    使う場面: z_of・perm_p の内部。自分で帰無を要約するときも先に呼ぶ
    入力: null: 帰無分布、min_unique: これ未満のユニーク値なら退化とみなす
    返り値: bool
    禁止: 退化した帰無の z を判定に使わない
    段階: 帰無
    """
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3:
        return True
    q = np.percentile(null, [2.5, 97.5])
    return bool(q[0] == q[1] or len(np.unique(null)) < min(min_unique, len(null)))


def z_of(obs, null):
    """観測値の帰無分布に対する z と百分位。帰無が退化していれば (nan, nan)。
    使う場面: 並べ替え（perm_within・block_perm・circ_shift）で作った帰無分布と観測値を比べる
    入力: obs: 観測値、null: 帰無分布の配列（B 個。NaN は落とす）
    返り値: (z, pct)。pct は null < obs の割合。帰無の 2.5 点と 97.5 点が同じなら退化として (nan, nan)
    禁止: B<100 の帰無分布で判定しない（経路確認のみ）。z が桁外れ（|z|>20）なら null_summary で分位点を見る
    段階: 帰無
    """
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if len(null) < 3 or null.std(ddof=1) == 0 or not np.isfinite(obs) or null_degenerate(null):
        return float("nan"), float("nan")
    return float((obs - null.mean()) / null.std(ddof=1)), float((null < obs).mean())


def perm_p(obs, null, side="greater"):
    """並べ替え検定の p 値 (1 + #{null が obs 以上}) / (B + 1)（改善判定.md の式）。
    使う場面: holm に渡す p を作るとき。1−pct（0 になりうる）や正規近似で p を作らない
    入力: obs、null、side: "greater"（obs が大きいほど良い）/"less"/"two"
    返り値: float（退化なら nan）
    禁止: side を結果を見てから変えない
    段階: 帰無
    """
    null = np.asarray(null, float); null = null[np.isfinite(null)]
    if not np.isfinite(obs) or null_degenerate(null):
        return float("nan")
    B = len(null)
    if side == "greater":
        k = int((null >= obs).sum())
    elif side == "less":
        k = int((null <= obs).sum())
    else:
        c = null.mean(); k = int((np.abs(null - c) >= abs(obs - c)).sum())
    return float((1 + k) / (B + 1))


def null_summary(obs, null):
    """帰無分布の要約（B・分位点・z・pct・perm_p・退化フラグ）を dict で返す。
    使う場面: 結果 JSON に帰無の形を残すとき（z の桁外れの点検に使う）
    入力: obs、null
    返り値: {"B","q025","q500","q975","z","pct","p_perm","degenerate"}
    禁止: —
    段階: 帰無
    """
    n = np.asarray(null, float); n = n[np.isfinite(n)]
    z, pct = z_of(obs, n)
    q = np.percentile(n, [2.5, 50, 97.5]) if len(n) else [np.nan] * 3
    return {"B": int(len(n)), "q025": float(q[0]), "q500": float(q[1]), "q975": float(q[2]),
            "z": z, "pct": pct, "p_perm": perm_p(obs, n), "degenerate": null_degenerate(n)}


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
    入力: rng、x: 長さ n、min_shift: 最小のずらし（持続する合図では保有期間の数倍にする）
    返り値: 長さ n。k は [min_shift, n−min_shift] の一様（旧雛形は上限が 1 つ足りなかった。レビュー 2026-10-13）
    禁止: 短い系列（n<10×min_shift）で使わない
    段階: 帰無
    """
    x = np.asarray(x, float); n = len(x)
    k = int(rng.integers(min_shift, max(min_shift + 1, n - min_shift + 1)))
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
