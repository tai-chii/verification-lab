# -*- coding: utf-8 -*-
"""Q577 日本株・米国株の距離法ペア取引（12 か月形成・6 か月取引・上位 20 ペア・2σ で建て・収束で閉じる・1 日待ち）— 無料層での追試

【出典】Gatev, Goetzmann & Rouwenhorst 2006「Pairs Trading: Performance of a Relative-Value Arbitrage Rule」（RFS 19(3)・距離法の原典。
       上位 20 ペアで年 11% 前後・後年は低下）。Do & Faff 2010（低下の確認）。探索の地図「統計的裁定（ペア）× 日本株・米国株」◎未。
       先行研究チェック 2026-10-30 WebSearch（standard・英語）「pairs trading distance method Gatev Goetzmann Rouwenhorst declining profitability Japan」:
       GGR 2006（RePEc）、Aalto のフィンランド株 2020-2024 の距離法、台湾の Corporate Management Review 2020 が見つかる。日本株の無料層での追試は見当たらない。
       未確認の点: 2006〜2024-06・売買代金上位・1 日待ち・コスト後で、規程 C1（前後半とも年単位 t≥2）に届くか（追試＋移植＋条件の穴）。
【仮説】H1: 距離法の上位 20 ペアは、少なくとも 1 国でコスト後 NW t≥2・前後半とも年単位 t≥2、かつ同じ規則のランダムなペアより z≥2 で上回る。
       H0: 両国とも NW t<1（公表後・コスト後には消えている）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（調整済み終値・出来高・2005-01〜2024-06・封印 2024-07-01 以降は読まない）。生存バイアスあり
       （上場廃止で発散したペアが入らないので、ペア取引を**強く見せる**向き。解釈で必ず触れる）。
【定義】形成日 t＝毎月末（i＝t の行・i≥252）。適格＝株価≥100 円（US 5 ドル）・形成 252 日に欠損なし・売買代金 20 日平均の上位 500（計算量のため）。
       形成: 各銘柄を形成の初日で 1 に揃えた累積価格 P̃ の差の二乗和（SSD）が小さい順に 20 ペア（同じ銘柄の重複は可・SSD≈0 は除く）。σ＝形成期間の P̃ 差の標準偏差。
       取引: t の翌営業日から 126 営業日。取引開始で 1 に揃え直した差 s＝P̃_a − P̃_b。終値 d で |s|>2σ なら、d の翌営業日の終値で
       高い方を売り・低い方を買う（各 1 円）。終値 d で s の符号が建てたときと変わったら、d の翌営業日の終値で閉じる（1 日待ち＝GGR の頑健性版）。
       再び開くのは可。期間末で閉じる。欠損の日はその足で閉じる。ペアの損益＝r_買い − r_売り。コスト＝建て・閉じのそれぞれで 2 本 × 片道 JP 10 bp／US 5 bp。
       コホートの日次＝20 ペアの和 ÷ 20（使った資本＝committed capital）。全体の日次＝その日に生きている最大 6 コホートの平均（GGR の重なり方式）。
【測るもの】日次の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半〜2014・後半 2015〜）・市場（全銘柄等金額）アルファとベータ・年率シャープ・
       σ0.25%/日 換算の最大 DD・1 ペアあたりの建て回数。副（合否に使わない）: コスト 0 の平均と t、建て日の待ち 0 日版の平均（反転の bid-ask 跳ね返りの大きさの目安）。
【帰無】ラベルの並べ替え: 各コホートで同じ適格銘柄からランダムに 20 ペアを選び、同じ規則（σ も各ランダムペアの形成期間から）で取引（B=200）。
       「距離で選ぶこと」に価値があるかを測る（ランダムなペアでも短期反転は出るので、0 との比較ではなく選び方の比較）。
【判定（事前固定・変更禁止）】少なくとも 1 国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ
       σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。それ以外 → 未確定。
【多重比較の本数】主 2 本（2 国 × 1 設定・Holm）。株式無料層の族の試行は Q563・Q564・Q566・Q576 に続き 5 件目（ペアは族として初）。
【捨てた案の数】2（共和分法〔Engle-Granger〕は形成ごとの検定本数が数万になり計算と多重比較が重い。業種内に限る版は US の業種欄が空で 2 国比較ができない）。
【知識の締め切り】設計者の知識（〜2026-06）。対象期間は公表（1999 の WP・2006 の RFS）後を多く含み、既知の結果（低下）を含む。
【委託の確かめ方】results/result_q577.json の per_market.{jp,us} の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025・opens_per_pair と verdict。
       opens_per_pair が 1〜3（GGR は約 2）の範囲か。daily_{jp,us}_q577.csv の n_cohorts が 6 で安定しているか。null.null_mean_bp が 0 付近〜正か。
【実装】python3 kensho_pairs_distance_q577.py（Mac・venv_equities。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
       B=200 の帰無はコホートごとの日ループ（126 日 × 20 ペアのベクトル）なので Mac で 1 国 5〜15 分の見込み（クラウドの smoke: 400 銘柄・108 コホート・B=5 で 7 秒）。
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
# --- 規程 C1 の関門（2026-10-30 Fable 追記・株式無料層 第1弾 Q576〜Q578 共通）---------------------------
# lab_plan_手順の決まり（2026-10-30）: 「支持」の前後半条件は関門と同じ「前後半とも年単位 t≥2」で書く。
import math

def annual_t(x, min_days=120):
    """年単位 t: 暦年ごとの日次損益の和（日数 min_days 以上の年だけ）の t = 平均/標準偏差×√年数。3 年未満は NaN。"""
    x = pd.Series(x).dropna()
    if not len(x): return np.nan
    g = x.groupby(x.index.year); y = g.sum()[g.size() >= min_days]
    if len(y) < 3 or y.std(ddof=1) <= 0: return np.nan
    return float(y.mean() / y.std(ddof=1) * np.sqrt(len(y)))

def maxdd_scaled(x, sigma=0.0025):
    """全期間の σ で日次 0.25% に揃えたときの最大ドローダウン（単利の累積・事後の尺度＝関門の目安）。"""
    x = pd.Series(x).dropna()
    if len(x) < 30 or x.std() <= 0: return np.nan
    eq = np.cumsum(x.values * sigma / x.std())
    return float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min())

def p_one(t):
    """NW t からの片側 p（正規近似）。"""
    return float(0.5 * math.erfc(t / math.sqrt(2))) if t == t else np.nan

def holm(ps):
    """Holm の調整済み p（dict→dict）。"""
    items = sorted(ps.items(), key=lambda kv: (np.inf if kv[1] != kv[1] else kv[1])); m = len(items); out = {}; run = 0.0
    for k, (name, p) in enumerate(items):
        adj = np.nan if p != p else min(1.0, (m - k) * p); run = max(run, adj if adj == adj else 0.0); out[name] = run if adj == adj else np.nan
    return out

def add_c1(st, ls):
    """stats() の結果に 前後半の年単位 t・σ 0.25% 換算の最大 DD・片側 p を足す。"""
    ls = pd.Series(ls).dropna()
    st["t_year"] = annual_t(ls)
    st["h1_ty"] = annual_t(ls[ls.index < SPLIT]); st["h2_ty"] = annual_t(ls[ls.index >= SPLIT])
    st["maxdd_s025"] = maxdd_scaled(ls); st["p_one"] = p_one(st["t_nw"])
    return st

def machine_verdict_c1(per):
    """事前固定（変更禁止・Q576〜Q578 共通）。少なくとも 1 国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ
    2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。それ以外 → 未確定。"""
    adj = holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2
          and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if ok: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    return "未確定"
# === 共通の土台ここまで ==================================================================
QID = "Q577"; FORM, TRADE, NPAIRS, ENTRY, TOP_ELIG, MAX_COH = 252, 126, 20, 2.0, 500, 6

def trade_cohort(Cv, Rv, i, a, b, cost, wait=1):
    """1 コホート（形成日の行 i・ペア a[k], b[k]）の日次損益（長さ T・20 ペアの和 ÷ NPAIRS）と建て回数。"""
    F = Cv[i - FORM + 1:i + 1]; sig = (F[:, a] / F[0, a] - F[:, b] / F[0, b]).std(0)
    T = min(TRADE, Cv.shape[0] - 1 - i)
    if T <= 1: return np.zeros(0), 0
    pa = Cv[i + 1:i + 1 + T, a] / Cv[i, a]; pb = Cv[i + 1:i + 1 + T, b] / Cv[i, b]; s = pa - pb
    ra = Rv[i + 1:i + 1 + T, a]; rb = Rv[i + 1:i + 1 + T, b]
    P = len(a); pos = np.zeros(P); pend = np.zeros(P); out = np.zeros(T); opens = 0
    for d in range(T):
        r = pos * (rb[d] - ra[d])                 # pos=+1: a を売り b を買い（s>0 のとき）
        bad = np.isnan(r); r[bad] = 0.0; out[d] += r.sum()
        tgt = pend if wait else pos               # wait=1: 前日の終値で決めた建玉をこの終値で執行
        if wait:
            out[d] -= cost * 2 * np.abs(tgt - pos).sum(); opens += int(((pos == 0) & (tgt != 0)).sum()); pos = tgt.copy()
        pos[bad] = 0.0
        sd = s[d]; new = pos.copy()
        op = (pos == 0) & (np.abs(sd) > ENTRY * sig); new[op] = np.sign(sd[op])
        cl = (pos != 0) & (np.sign(sd) != pos); new[cl] = 0.0
        new[np.isnan(sd)] = 0.0
        if d == T - 1: new[:] = 0.0
        if wait: pend = new
        else:
            out[d] -= cost * 2 * np.abs(new - pos).sum(); opens += int(((pos == 0) & (new != 0)).sum()); pos = new
    out[-1] -= cost * 2 * np.abs(pos).sum()       # 期間末に残った建玉（wait=1 で最終日に決めた分）を閉じる
    return out / NPAIRS, opens

def pick_pairs(X, rng=None):
    """X: 形成期間の P̃（銘柄×日）。SSD 最小の NPAIRS ペア（rng を渡すとランダムなペア）。"""
    n = X.shape[0]
    if rng is not None:
        a = rng.integers(0, n, NPAIRS * 3); b = rng.integers(0, n, NPAIRS * 3); k = a != b
        return a[k][:NPAIRS], b[k][:NPAIRS]
    sq = (X ** 2).sum(1); D = sq[:, None] + sq[None, :] - 2 * X @ X.T
    iu = np.triu_indices(n, 1); v = D[iu]; v = np.where(v > 1e-8, v, np.inf)
    k = np.argpartition(v, NPAIRS)[:NPAIRS]; k = k[np.argsort(v[k])]
    return iu[0][k], iu[1][k]

def cohorts(C, V, cfg):
    """形成日ごとの (行 i, 適格の列番号)。"""
    dates = C.index; pos = {t: i for i, t in enumerate(dates)}
    adv = (C * V).rolling(20, min_periods=15).mean(); full = C.notna().rolling(FORM, min_periods=FORM).sum() >= FORM
    out = []
    for t in month_ends(dates):
        i = pos[t]
        if i < FORM or i + 2 >= len(dates): continue
        ok = (C.loc[t] >= cfg["minpx"]) & full.loc[t]
        el = adv.loc[t][ok].dropna().nlargest(TOP_ELIG).index
        if len(el) < 2 * NPAIRS: continue
        out.append((i, np.array([C.columns.get_loc(c) for c in el])))
    return out

def run_pairs(C, R, coh, cost, rng=None, wait=1):
    Cv, Rv = C.values, R.values; T = len(C); acc = np.zeros(T); cnt = np.zeros(T); opens = 0; npairs = 0
    for i, el in coh:
        F = Cv[i - FORM + 1:i + 1, el]; X = (F / F[0]).T
        a, b = pick_pairs(X, rng); out, o = trade_cohort(Cv, Rv, i, el[a], el[b], cost, wait)
        if not len(out): continue
        acc[i + 1:i + 1 + len(out)] += out; cnt[i + 1:i + 1 + len(out)] += 1; opens += o; npairs += len(a)
    m = cnt > 0
    d = pd.DataFrame({"ls": acc[m] / cnt[m], "n_cohorts": cnt[m]}, index=C.index[m])
    return d, (opens / npairs if npairs else np.nan)

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = CFG[mkt]; C, V = load_px(mkt, args.smoke, rng); R = C.pct_change(fill_method=None)
        R = R.where(R.abs() < 0.5); mk = R.mean(axis=1)
        coh = cohorts(C, V, cfg)
        d, opp = run_pairs(C, R, coh, cfg["cost"]); d = d[d["n_cohorts"] >= 1]
        st = add_c1(stats(d["ls"], mk), d["ls"]); st["opens_per_pair"] = opp; st["n_cohorts_total"] = len(coh)
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        vals = np.array([run_pairs(C, R, coh, cfg["cost"], rng=rng)[0]["ls"].mean() for _ in range(args.B)], float); sd = vals.std()
        st["null"] = dict(B=args.B, kind="ランダムなペア（同じ規則）", null_mean_bp=1e4 * vals.mean(), null_sd_bp=1e4 * sd,
                          z=(d["ls"].mean() - vals.mean()) / sd if sd > 0 else np.nan, p=float((vals >= d["ls"].mean()).mean()))
        d0, _ = run_pairs(C, R, coh, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = nw_t(d0["ls"])
        dw, _ = run_pairs(C, R, coh, cfg["cost"], wait=0); st["sub_wait0_bp"] = 1e4 * dw["ls"].mean()
        d["mkt"] = mk.reindex(d.index); per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=machine_verdict_c1(per), rule=machine_verdict_c1.__doc__.strip()), csvs

def main():
    args = parse_args("Q577 距離法ペア取引（日本株・米国株）"); rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
