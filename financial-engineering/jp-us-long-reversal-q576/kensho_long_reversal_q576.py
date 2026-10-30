# -*- coding: utf-8 -*-
"""Q576 日本株・米国株の長期反転（13〜48 か月の負け組を買い・勝ち組を売る・月次・上下 10%・等金額 L/S）— 無料層での追試

【出典】DeBondt & Thaler 1985「Does the Stock Market Overreact?」（3〜5 年の負け組が勝ち組を上回る）、Chopra-Lakonishok-Ritter 1992、
       国際比較: 「Overreaction and the cross-section of returns: international evidence」（Alpha Architect の紹介）・CXO Advisory
       「Long-Term Reversal for Stocks Everywhere」。探索の地図「バリュー（長期反転）× 日本株・米国株」◎未（財務が無いので価格だけの代理）。
       先行研究チェック 2026-10-30 WebSearch（standard・英語）「long-term reversal DeBondt Thaler Japan stocks evidence recent decades」:
       上の国際比較 2 件と大阪大学・立命館の日本株の過剰反応の論文が見つかる。未確認の点: 現構成（生存バイアスあり）の無料層・
       2009〜2024-06・売買代金上位・コスト後で、規程 C1（前後半とも年単位 t≥2）に届くか（追試＋条件の穴）。
【仮説】H1: 過去 13〜48 か月の負け組（下位 10%）買い・勝ち組（上位 10%）売りは、少なくとも 1 国でコスト後 NW t≥2・前後半とも年単位 t≥2。
       H0: 両国とも NW t<1（無料層・この期間では長期反転は消えている）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（調整済み終値・出来高・2005-01〜2024-06・封印 2024-07-01 以降は読まない）。
       生存バイアスあり（現構成のみ）: 消えた負け組が買い側に入らないので、長期反転を**強く見せる**向き（Q563 とは逆向き）。結果の解釈で必ず触れる。
【定義】判断日 t＝月末。シグナル＝−(C[t−252 営業日]／C[t−1008 営業日]−1)（直近 12 か月を飛ばし、その前 36 か月の騰落の符号反転。
       値が大きい＝負け組）。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 1,008 日の 9 割以上。
       上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。
       コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い（Q562 の注意）。最初の判断日は 2009 年。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半〜2014・後半 2015〜）・市場アルファとベータ・年率シャープ・
       σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[60, N−60]・B=200）。シグナルは 36 か月窓で持続性が高いので、Q563 の 13 か月ではなく 60 か月以上ずらして
       「時間の対応」を壊す（ずらしが短いと帰無が観測と似て z が縮む）。
【判定（事前固定・変更禁止）】少なくとも 1 国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ
       σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。それ以外 → 未確定。
【多重比較の本数】主 2 本（2 国 × 1 設定・Holm）。株式無料層の族（横断 L/S）の試行は Q563・Q564・Q566 に続き 4 件目。
【捨てた案の数】2（48 か月飛ばし 12 か月の他に、60 か月形成〔最初の判断日が 2010 年に遅れ前半が 5 年を切る〕と業種中立化〔Q566 で業種内反転は済✗〕を捨てた）。
【知識の締め切り】設計者の知識（〜2026-06）。対象期間 2009〜2024-06 は既知の結果（長期反転は米国で弱まった）を含む。
【委託の確かめ方】results/result_q576.json の per_market.{jp,us} の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。
       daily_{jp,us}_q576.csv の turn（L・S それぞれの入れ替え銘柄の対称差÷q の平均。全部入れ替わると 2）が月 0.1〜0.4 程度（長い窓なので Q563 の 0.34 以下）か。最初の日付が 2009 年か。
【実装】python3 kensho_long_reversal_q576.py（Mac・venv_equities。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
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
QID = "Q576"; LOOKBACK, SKIP = 1008, 252; NULL_MIN_SHIFT = 60

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = CFG[mkt]; C, V = load_px(mkt, args.smoke, rng); R = C.pct_change(fill_method=None)
        R = R.where(R.abs() < 0.5)
        months = build_months(C, V, cfg, LOOKBACK)
        pos = {t: i for i, t in enumerate(C.index)}
        def sig_at(t, el):
            i = pos[t]; a, b = C.iloc[i - SKIP], C.iloc[i - LOOKBACK]
            return -(a / b - 1).reindex(el)
        d = run_ls(C, R, sig_at, months, cfg["cost"]); st = add_c1(stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean(), min_shift=NULL_MIN_SHIFT if len(months) > 2 * NULL_MIN_SHIFT + 10 else max(1, len(months) // 3))  # 縮むのは smoke だけ（本番は約 184 か月）
        d0 = run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = nw_t(d0["ls"])
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=machine_verdict_c1(per), rule=machine_verdict_c1.__doc__.strip()), csvs

def main():
    args = parse_args("Q576 長期反転 13〜48 か月（日本株・米国株）"); rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
