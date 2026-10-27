# -*- coding: utf-8 -*-
"""探索（判定に使わない）: 内側期間だけで (A) 勝率 65±2.5% に絞る (B) ZigZag++ の方向を特徴量に足す を比べる。
学習 〜2021-09-30 / 評価 2021-10-01〜2023-09-30。仮判断・最終の期間は読まない。"""
import sys, json, numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, '.'); import kensho_s21_h1_ml_rr_q515 as K

DEPTH = 12  # ZigZag++ の既定 Depth


def zigzag_feats(d, D):
    """ZigZag++ のリアルタイムの向き（直近 DEPTH 本で高値更新→上、安値更新→下）を因果的に再現。
    確定した転換点（向きが変わった時点で確定する前の脚の極値）だけを使う＝描き直しの影響なし。"""
    h, l, c = d['high'].to_numpy(), d['low'].to_numpy(), d['close'].to_numpy()
    n = len(d); atr = D / K.K_ATR
    hh = pd.Series(h).rolling(DEPTH).max().to_numpy(); ll = pd.Series(l).rolling(DEPTH).min().to_numpy()
    dirn = np.zeros(n); since = np.zeros(n); leg_ext = np.full(n, np.nan)
    pivH = [np.nan, np.nan]; pivL = [np.nan, np.nan]; struct = np.zeros(n)
    cur, ext, start = 0, np.nan, 0
    for i in range(n):
        up = h[i] >= hh[i] if np.isfinite(hh[i]) else False
        dn = l[i] <= ll[i] if np.isfinite(ll[i]) else False
        if up and not dn and cur != 1:
            if cur == -1: pivL = [pivL[1], ext]  # 下の脚が終わる＝安値の転換点が確定
            cur, ext, start = 1, h[i], i
        elif dn and not up and cur != -1:
            if cur == 1: pivH = [pivH[1], ext]
            cur, ext, start = -1, l[i], i
        elif cur == 1: ext = max(ext, h[i])
        elif cur == -1: ext = min(ext, l[i])
        dirn[i] = cur; since[i] = i - start
        leg_ext[i] = (c[i] - (ll[start] if cur == 1 else hh[start])) / atr[i] if cur != 0 and np.isfinite(atr[i]) else np.nan
        s = 0
        if np.isfinite(pivH).all() and np.isfinite(pivL).all():
            s = (1 if pivH[1] > pivH[0] else -1) + (1 if pivL[1] > pivL[0] else -1)
        struct[i] = s
    return pd.DataFrame({'zz_dir': dirn, 'zz_since': since, 'zz_leg_atr': leg_ext, 'zz_struct': struct})


def main():
    data = {}
    for s in K.SYMS:
        d = K.load('data', s); R, X, D = K.labels(d, s); F = K.features(d, D, s)
        Z = zigzag_feats(d, D)
        data[s] = dict(time=d['time'].reset_index(drop=True), R=R, X=X, F=F, FZ=pd.concat([F, Z], axis=1))
        print(s, flush=True)
    out = {}
    for name, key in [('基本', 'F'), ('ZigZag追加', 'FZ')]:
        dd = {s: dict(o, F=o[key]) for s, o in data.items()}
        regs, _ = K.train_models(dd, K.INNER_START)
        P = K.predict(regs, dd, K.INNER_START, K.TRAIN_END)
        rows = []
        for th in K.THETAS:
            tr = K.run_policy(dd, P, th); p = K.daily(tr, K.INNER_START, K.TRAIN_END, 1.0)
            rows.append(dict(theta=th, n=len(tr), win=round(float((tr.R > 0).mean()), 3), mean_R=round(float(tr.R.mean()), 4), t=round(K.tstat(p), 2)))
        out[name] = rows
        # (A) 勝率で絞る: 分類器で P(勝ち) を出し、P≥τ の行動のうち予測 R 最大を取る
        Xs, Ys = [], []
        for s, o in dd.items():
            t = o['time']; n = len(t); ok = np.isfinite(o['R']).all(1)
            tx = t.dt.tz_convert(None).to_numpy()[np.clip(o['X'].max(1), 0, n - 1)]
            ok &= tx < K.INNER_START.tz_convert(None).to_datetime64()
            sel = np.where(ok)[0][::3]; Xs.append(o['F'].iloc[sel]); Ys.append(o['R'][sel] > 0)
        Xtr = pd.concat(Xs); Ytr = np.vstack(Ys)
        clfs = [lgb.LGBMClassifier(random_state=1 + a, **{**K.LGB_PARAMS, 'objective': 'binary'}).fit(Xtr, Ytr[:, a]) for a in range(6)]
        Pw = {}
        for s, (idx, pr) in P.items():
            pw = np.column_stack([c.predict_proba(dd[s]['F'].iloc[idx])[:, 1] for c in clfs])
            Pw[s] = (idx, pr, pw)
        rowsA = []
        for tau in [0.55, 0.60, 0.62, 0.65, 0.68, 0.70]:
            PP = {s: (idx, np.where(pw >= tau, pr, -9.0)) for s, (idx, pr, pw) in Pw.items()}
            tr = K.run_policy(dd, PP, -1.0)  # 勝率条件を満たす行動があれば入る（予測 R の符号は問わない）
            p = K.daily(tr, K.INNER_START, K.TRAIN_END, 1.0)
            act = tr.a.map(lambda a: K.ACTIONS[a][1]).value_counts().to_dict() if len(tr) else {}
            rowsA.append(dict(tau=tau, n=len(tr), win=round(float((tr.R > 0).mean()), 3) if len(tr) else None,
                              mean_R=round(float(tr.R.mean()), 4) if len(tr) else None, t=round(K.tstat(p), 2), RR内訳=act))
            # τ と予測 R>θ を両方
            PP2 = {s: (idx, np.where(pw >= tau, pr, -9.0)) for s, (idx, pr, pw) in Pw.items()}
            tr2 = K.run_policy(dd, PP2, 0.0); p2 = K.daily(tr2, K.INNER_START, K.TRAIN_END, 1.0)
            rowsA[-1].update(n_且つR正=len(tr2), win_且つR正=round(float((tr2.R > 0).mean()), 3) if len(tr2) else None,
                             mean_R_且つR正=round(float(tr2.R.mean()), 4) if len(tr2) else None, t_且つR正=round(K.tstat(p2), 2))
        out[name + '_勝率で絞る'] = rowsA
        # 較正: 予測勝率の帯ごとの実現勝率（RR1.0 の行動）
        cal = []
        allp = np.concatenate([pw[:, 0] for _, (_, _, pw) in Pw.items()]); allw = np.concatenate([dd[s]['R'][idx, 0] > 0 for s, (idx, _, _) in Pw.items()])
        for lo, hi in [(0, .45), (.45, .5), (.5, .55), (.55, .6), (.6, .65), (.65, 1)]:
            m = (allp >= lo) & (allp < hi); cal.append(dict(帯=f'{lo}-{hi}', n=int(m.sum()), 実現勝率=round(float(allw[m].mean()), 3) if m.sum() else None))
        out[name + '_較正_買RR1'] = cal
        print(name, 'done', flush=True)
    json.dump(out, open('results/explore_q516_inner.json', 'w'), ensure_ascii=False, indent=1)
    for k, v in out.items():
        print('==', k)
        for r in v: print(r)


if __name__ == '__main__':
    main()
