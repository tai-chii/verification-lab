# -*- coding: utf-8 -*-
"""Q564 残差モメンタム（市場に回帰した残差の 12-1 か月・残差 σ で割る・月次・上下 10%）— 素のモメンタムが弱い日本株での追試（米国株も同じコード）

【出典】Blitz, Huij & Martens 2011「Residual Momentum」（JEF: 残差モメンタムは素のモメンタムより安定・日本でも機能）、
       Chang, Ko, Nakano & Rhee 2018「Residual momentum in Japan」（J. Empirical Finance 45: 日本で残差モメンタムが有意・素は無意味）。
       先行研究チェック 2026-10-28 WebSearch「residual momentum Japan Blitz Huij Martens」: 上記 2 本と「Residual Momentum and Investor
       Underreaction in Japan」（厦門大セミナー）が見つかる。未確認の点: 先行研究は Fama-French 3 因子の残差・月次・1990 年代〜2010 年代。
       ここでは因子が無料で取れないので**市場 1 因子**の残差（条件の穴）・2005〜2024-06・現構成の無料層・コスト後で「両国 t≥2」に届くか。
【仮説】H1: 日本株で残差モメンタムの L−S がコスト後 NW t≥2（素のモメンタム Q563 が未確定でも）。米国株でも t≥2。
【データ】Q563 と同じ（Q562 無料層・2005-01〜2024-06・封印は開けない）。
【定義】月次リターン＝月末終値の比。判断日 t＝月末。回帰窓＝過去 36 か月（最低 24 か月）の月次リターンを、同じ期間の市場（適格全銘柄の等金額平均）に
       OLS（切片あり）。残差 e_s。シグナル＝Σ e_s（t−12〜t−2 の 11 か月・直近 1 か月を飛ばす）÷ sd(e_s 同期間)。適格・建玉・保有・コストは Q563 と同一
       （株価≥100 円／5 ドル・売買代金上位 1,000／800・上位 10% 買い・下位 10% 売り・等金額・月末翌営業日の終値から・片道 JP 10 bp／US 5 bp）。
【測るもの】Q563 と同じ（日次 L−S bp/日・NW t ラグ 21・前後半・市場アルファとベータ・年率シャープ・回転）。副: 素のモメンタム（Q563 の定義）との
       シグナル順位相関（Spearman・月ごとの平均）を参考に出す（合否に使わない）。
【帰無】Q563 と同じ循環シフト（月・k∈[13, N−13]・B=200）。
【判定（事前固定・変更禁止）】両国で NW t≥2 かつ前後半とも平均>0 かつ帰無 z≥2 → 支持。両国とも t<1 → 棄却。それ以外 → 未確定。
       多重比較: 主は 2 国 × 1 設定 = 2 本（AND 判定）。Q563 とは別の問い（残差 vs 素）として登録し、2 件で Holm はかけない（判定は各々独立）。
【捨てた案の数】0。
【知識の締め切り】Fable の知識（〜2026-06）。
【委託の確かめ方】results/result_q564.json の per_market.{jp,us}.t_nw・null.z・verdict、sub_rank_corr_raw（素との順位相関が 0.3〜0.7 なら別物として成立）。
【事前登録からの変更点】2026-10-29 Q564 実行時: 副の Spearman を「順位のピアソン」に置換（venv に scipy が無く落ちたため・同値・判定に無関係）。修正前は results/kensho_residual_momentum_q564_修正前.py。
【実装】python3 kensho_residual_momentum_q564.py（Mac・venv_equities。EQ_DIR で置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
# === 共通の土台（日本株・米国株の横断・月次 L/S・2026-10-28 Fable）=======================
import argparse, json, os, sys, datetime
import numpy as np, pandas as pd

WS = os.environ.get("WS") or os.path.expanduser("~/ワークスペース")
sys.path.insert(0, os.path.join(WS, "検証", "verification-lab", "tools"))
SEAL = pd.Timestamp("2024-07-01")          # ホールドアウト 2024-07〜2026-06 は開けない（equities_free の既定）
SPLIT = pd.Timestamp("2015-01-01")         # 前半 2005〜2014／後半 2015〜2024-06
CFG = {"jp": dict(cost=0.0010, minpx=100.0, topn=1000),   # 片道コスト・最低株価・売買代金上位
       "us": dict(cost=0.0005, minpx=5.0,   topn=800)}
FRAC, NW_LAG, MIN_NAMES = 0.10, 21, 300    # 上下 10%・NW のラグ・判断日の最低銘柄数

def load_px(mkt, smoke=False, rng=None):
    """終値・出来高（日付×銘柄）。smoke=True なら合成（ランダムウォーク・モメンタム無し）。"""
    if smoke:
        n, T = 400, 2600; idx = pd.bdate_range("2014-01-01", periods=T)
        r = rng.normal(0.0003, 0.02, (T, n)); c = pd.DataFrame(1000 * np.exp(np.cumsum(r, 0)), idx, [f"S{i}" for i in range(n)])
        v = pd.DataFrame(np.exp(rng.normal(12, 1, (T, n))), idx, c.columns)
        return c, v
    import equities_free as ef
    if os.environ.get("EQ_DIR"): ef.DIR = os.environ["EQ_DIR"]
    return ef.load(mkt, "close", end=SEAL), ef.load(mkt, "volume", end=SEAL)

def month_ends(dates):
    s = pd.Series(dates, index=dates)
    return [g.index[-1] for _, g in s.groupby(dates.to_period("M"))]

def nw_t(x, lag=NW_LAG):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 10: return np.nan
    m = x.mean(); e = x - m; s = e @ e
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[:-k] @ e[k:])
    return m / np.sqrt(s / n / n) if s > 0 else np.nan

def stats(ls, mk):
    """日次 L−S（bp/日）・NW t・前後半・市場に回帰したアルファ（bp/日）とベータ・年率シャープ。"""
    ls = ls.dropna(); mk = mk.reindex(ls.index)
    b = np.cov(ls, mk)[0, 1] / np.var(mk) if len(ls) > 30 else np.nan
    a = ls.mean() - b * mk.mean() if len(ls) > 30 else np.nan
    h1, h2 = ls[ls.index < SPLIT], ls[ls.index >= SPLIT]
    return dict(mean_bp=1e4 * ls.mean(), t_nw=nw_t(ls), n_days=int(len(ls)),
                h1_bp=1e4 * h1.mean(), h1_t=nw_t(h1), h2_bp=1e4 * h2.mean(), h2_t=nw_t(h2),
                alpha_bp=1e4 * a, beta=b, sharpe=np.sqrt(252) * ls.mean() / ls.std() if ls.std() > 0 else np.nan)

def run_ls(C, R, sig_at, months, cost, shift=0):
    """months: [(判断日 t, 保有の最初の日 e, 最後の日 x, 適格銘柄)]。sig_at(t, elig) -> Series(銘柄→シグナル)。
    shift: 帰無用。k 月ずれたシグナル（月 j のシグナルを月 j+k の保有に使う・循環）。"""
    n = len(months); sigs = [sig_at(t, el) for t, _, _, el in months]
    rows = []; prevL = prevS = set()
    for j in range(n):
        t, e, x, _ = months[j]; v = sigs[(j - shift) % n].dropna()
        if len(v) < MIN_NAMES: continue
        o = np.argsort(v.values); q = max(1, int(len(v) * FRAC))
        L, S = list(v.index[o[-q:]]), list(v.index[o[:q]])
        days = R.loc[(R.index >= e) & (R.index <= x)]
        if not len(days): continue
        cols = [c for c in v.index if c in days.columns]
        ls = days[L].mean(axis=1) - days[S].mean(axis=1); mk = days[cols].mean(axis=1)
        turn = (len(set(L) ^ prevL) / q + len(set(S) ^ prevS) / q) / 2
        ls = ls.copy(); ls.iloc[0] -= 2 * cost * turn     # 往復×片側回転（両側の建て替え分）
        rows.append(pd.DataFrame({"ls": ls, "mkt": mk, "turn": turn, "n": len(v)}))
        prevL, prevS = set(L), set(S)
    return pd.concat(rows) if rows else pd.DataFrame(columns=["ls", "mkt", "turn", "n"])

def build_months(C, V, cfg, lookback_days):
    """判断日＝月末。保有＝翌営業日の終値から次の月末翌営業日の終値まで。適格＝株価≥minpx・売買代金 20 日平均の上位 topn・履歴 lookback 日以上。"""
    dates = C.index; pos = {t: i for i, t in enumerate(dates)}; me = month_ends(dates)
    adv = (C * V).rolling(20, min_periods=15).mean(); hist = C.notna().rolling(lookback_days, min_periods=1).sum()
    out = []
    for k, t in enumerate(me[:-1]):
        i = pos[t]
        if i + 1 >= len(dates) or i < lookback_days: continue
        e = dates[i + 1]; j = pos[me[k + 1]]; x = dates[j + 1] if j + 1 < len(dates) else dates[-1]
        ok = (C.loc[t] >= cfg["minpx"]) & (hist.loc[t] >= lookback_days * 0.9)
        elig = adv.loc[t][ok].dropna().nlargest(cfg["topn"]).index
        out.append((t, e, x, list(elig)))
    return out

def null_circ(C, R, sig_at, months, cost, B, rng, obs_mean, min_shift=13):
    n = len(months); vals = []
    for _ in range(B):
        k = int(rng.integers(min_shift, n - min_shift)); d = run_ls(C, R, sig_at, months, cost, shift=k)
        vals.append(d["ls"].mean())
    vals = np.array(vals, float); sd = vals.std()
    return dict(B=B, null_mean_bp=1e4 * vals.mean(), null_sd_bp=1e4 * sd,
                z=(obs_mean - vals.mean()) / sd if sd > 0 else np.nan, p=float((vals >= obs_mean).mean()))

def parse_args(desc):
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--markets", default="jp,us"); ap.add_argument("--B", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261028); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    return ap.parse_args()

def write_result(qid, res, csvs, args):
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(out, exist_ok=True); tag = "smoke_" if args.smoke else ""
    p = os.path.join(out, f"{tag}result_{qid.lower()}.json")
    res["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); res["smoke"] = bool(args.smoke)
    json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    for name, df in csvs.items(): df.to_csv(os.path.join(out, f"{tag}{name}_{qid.lower()}.csv"))
    print(p); print(json.dumps({k: v for k, v in res.items() if k in ("verdict", "per_market")}, ensure_ascii=False, indent=1, default=float))

def machine_verdict(per):
    """事前固定（変更禁止）。両国で t_nw≥2 かつ前後半とも平均>0 かつ帰無 z≥2 → 支持。両国とも t_nw<1 → 棄却。それ以外 → 未確定。"""
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_bp"] > 0 and r["h2_bp"] > 0 and r["null"]["z"] >= 2]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    return "未確定"
# === 共通の土台ここまで ==================================================================
QID = "Q564"; LOOKBACK, WIN, MINW, SKIP_M = 252, 36, 24, 1

def resid_signal(M, t_idx, el):
    """M: 月次リターン（月末×銘柄）。t_idx: 判断月の位置。市場に回帰した残差の直近 11 か月（t−12..t−2）の和÷sd。"""
    Y = M.iloc[t_idx - WIN + 1:t_idx + 1][el]                       # 36 か月（判断月を含む）
    mk = Y.mean(axis=1); x = mk.values - np.nanmean(mk.values)
    ok = Y.notna().sum() >= MINW; Yv = Y.values
    ym = np.nanmean(Yv, 0); yc = Yv - ym
    xx = np.nansum((x[:, None] * np.where(np.isnan(yc), 0, 1)) ** 2, 0)
    b = np.nansum(x[:, None] * yc, 0) / np.where(xx > 0, xx, np.nan)
    e = yc - b * x[:, None]
    e11 = e[-(SKIP_M + 11):-SKIP_M] if SKIP_M else e[-11:]
    s = np.nansum(e11, 0) / np.nanstd(e11, 0, ddof=1)
    out = pd.Series(s, index=el); out[~ok.values] = np.nan
    return out

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = CFG[mkt]; C, V = load_px(mkt, args.smoke, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        months = build_months(C, V, cfg, LOOKBACK)
        me = month_ends(C.index); Cm = C.loc[me]; M = Cm.pct_change(fill_method=None); M = M.where(M.abs() < 1.0)
        mpos = {t: i for i, t in enumerate(me)}; pos = {t: i for i, t in enumerate(C.index)}
        months = [m for m in months if mpos[m[0]] >= WIN]
        def sig_at(t, el): return resid_signal(M, mpos[t], el)
        def raw_at(t, el):
            i = pos[t]; return (C.iloc[i - 21] / C.iloc[i - LOOKBACK] - 1).reindex(el)
        d = run_ls(C, R, sig_at, months, cfg["cost"]); st = stats(d["ls"], d["mkt"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["null"] = null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        rc = [sig_at(t, el).rank().corr(raw_at(t, el).rank()) for t, _, _, el in months[::3]]   # Spearman＝順位のピアソン（scipy 無し）
        st["sub_rank_corr_raw"] = float(np.nanmean(rc))
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=machine_verdict(per), rule=machine_verdict.__doc__.strip()), csvs

def main():
    args = parse_args("Q564 残差モメンタム（日本株・米国株）"); rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
