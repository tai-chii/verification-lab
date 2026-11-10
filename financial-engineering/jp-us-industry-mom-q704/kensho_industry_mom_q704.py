# -*- coding: utf-8 -*-
"""Q704 日本株・米国株の業種モメンタム（東証 33 業種／SIC 2 桁の 12-1 か月リターン・上位 3 業種買い下位 3 業種売り）はコスト後 2006〜2024-06 に両国で残るか

【出典】Moskowitz & Grinblatt 1999 JF「Do Industries Explain Momentum?」（20 業種・1963〜1995）。Swinkels 2002（Datastream 40 業種・1973〜2000: 米・欧で有意、日本では有意でない）。
       Titman & Hanauer 2014 IRF「Is Japan Different? Evidence on Momentum and Market Dynamics」（確かめていない・実行者が原典を見る）。
       先行研究チェック 2026-11-10 WebSearch standard「industry momentum Moskowitz Grinblatt 1999 international evidence Japan replication」: 上の 3 本と、米国＋37 か国で業種モメンタムが月 0.40〜0.49% という最近の研究（名称は未確認）。
       未確認の点: 日本の 2006〜2024-06（公表後・Swinkels の後）・東証 33 業種・売買代金上位 1,000・コスト後。
【仮説】H1: 業種の 12-1 か月等金額リターンで並べた上位 3 業種の銘柄買い・下位 3 業種の銘柄売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】業種: 日本は `equities_free/universe_jp.csv` の sector（東証 33 業種）、米国は `sec/sic.csv` の sic2（2 桁・無い銘柄は除く。今の業種なので過去の変更は反映しない＝限り）。
       業種リターン = 適格銘柄の 12-1 か月リターン（C[t−21]÷C[t−252] − 1）の等金額平均（銘柄 5 以上の業種だけ）。上位 3 業種の銘柄を等金額で買い・下位 3 業種の銘柄を等金額で売り（業種間も等金額＝各業種 1/3）。
       業種が 10 未満の判断日は飛ばす。共通の土台の run_ls は上下 10% の銘柄選びなので、この案だけ業種単位の選択のループを書く（回転は L・S それぞれの銘柄集合の対称差で同じ式）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案: 1（業種モメンタムを引いた個別株モメンタム〔Q563 が棄却なので意味が薄い〕）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜・封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。
【適格・保有・コスト】判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。
       保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで・等金額。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。前後半の境 2015-01-01。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の日米 8 本 Q700〜Q707 共通）】支持＝両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6%。
       棄却＝両国とも NW t<1。未確定＝それ以外（片方の国だけ通る場合は「未確定（片方: 国名）」）。無料層で落ちた案は有料データで救済しない。支持なら J-Quants Standard での再判定が次段階。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q704.json の per_market.{jp,us} の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_{jp,us}_q704.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_industry_mom_q704.py（Mac・pandas 3・lightgbm 不要。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

QID = "Q704"; LOOKBACK = 252; MIN_STOCKS_IND = 5; MIN_IND = 10; NTOP = 3
EQ = os.path.join(B.WS, "作業層", "大容量")

def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"


def load_sector(mkt, cols, smoke):
    """銘柄→業種（Series）。日本 universe_jp.csv の sector・米国 sec/sic.csv の sic2（無い銘柄は除く）。smoke は擬似業種 int(name[1:]) % 20。"""
    if smoke:
        return pd.Series({c: int(str(c)[1:]) % 20 for c in cols})
    if mkt == "jp":
        eq = os.environ.get("EQ_DIR") or os.path.join(EQ, "equities_free")
        u = pd.read_csv(os.path.join(eq, "universe_jp.csv")).dropna(subset=["sector"]).drop_duplicates("symbol")
        s = pd.Series(u["sector"].values, index=u["symbol"])
    else:
        u = pd.read_csv(os.path.join(EQ, "sec", "sic.csv")).dropna(subset=["sic2"]).drop_duplicates("ticker")
        s = pd.Series(u["sic2"].astype(int).values, index=u["ticker"])
    return s.reindex(cols).dropna()

def run_ls_ind(C, R, sig_at, months, cost, shift=0):
    """B.run_ls の写し。選択の行だけ変更: 上下 10% の銘柄 → 業種リターン上位 NTOP 業種の銘柄を買い・下位 NTOP 業種の銘柄を売り（各業種 1/NTOP・業種内は等金額）。
    sig_at(t, elig) -> (Lgroups, Sgroups, 銘柄数) か None（業種が MIN_IND 未満）。回転は L・S の銘柄集合の対称差÷その銘柄数の平均。"""
    n = len(months); sigs = [sig_at(t, el) for t, _, _, el in months]
    rows = []; prevL = prevS = set()
    for j in range(n):
        t, e, x, _ = months[j]; g = sigs[(j - shift) % n]
        if g is None or g[2] < B.MIN_NAMES: continue
        Lg, Sg = g[0], g[1]
        days = R.loc[(R.index >= e) & (R.index <= x)]
        if not len(days): continue
        L = sorted({c for m in Lg for c in m}); S = sorted({c for m in Sg for c in m})
        def leg(groups):                                                   # ← 業種内等金額 → 業種間等金額
            return pd.concat([days[[c for c in m if c in days.columns]].mean(axis=1) for m in groups], axis=1).mean(axis=1)
        allc = [c for c in g[3] if c in days.columns]
        ls = leg(Lg) - leg(Sg); mk = days[allc].mean(axis=1)
        turn = (len(set(L) ^ prevL) / len(L) + len(set(S) ^ prevS) / len(S)) / 2
        ls = ls.copy(); ls.iloc[0] -= 2 * cost * turn
        rows.append(pd.DataFrame({"ls": ls, "mkt": mk, "turn": turn, "n": g[2]}))
        prevL, prevS = set(L), set(S)
    return pd.concat(rows) if rows else pd.DataFrame(columns=["ls", "mkt", "turn", "n"])

def null_circ_ind(C, R, sig_at, months, cost, Bn, rng, obs_mean, min_shift=13):
    """B.null_circ の写し（run_ls_ind を使う）。"""
    n = len(months); vals = []
    for _ in range(Bn):
        k = int(rng.integers(min_shift, n - min_shift)); d = run_ls_ind(C, R, sig_at, months, cost, shift=k)
        vals.append(d["ls"].mean())
    vals = np.array(vals, float); sd = vals.std()
    return dict(B=Bn, null_mean_bp=1e4 * vals.mean(), null_sd_bp=1e4 * sd,
                z=(obs_mean - vals.mean()) / sd if sd > 0 else np.nan, p=float((vals >= obs_mean).mean()))

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]; C, V = B.load_px(mkt, args.smoke, rng); R = C.pct_change(fill_method=None)
        R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, LOOKBACK)
        M = C.shift(21) / C.shift(LOOKBACK) - 1                  # 行 t = C[t−21]÷C[t−252] − 1
        sec = load_sector(mkt, C.columns, args.smoke)
        def sig_at(t, el):
            r = M.loc[t].reindex(el).dropna(); s = sec.reindex(r.index).dropna(); r = r.reindex(s.index)   # 業種の無い銘柄は除く
            grp = r.groupby(s)
            cnt = grp.size(); ind = grp.mean()[cnt >= MIN_STOCKS_IND].sort_values()
            if len(ind) < MIN_IND: return None
            members = lambda k: list(s.index[s == k])
            Sg = [members(k) for k in ind.index[:NTOP]]; Lg = [members(k) for k in ind.index[-NTOP:]]
            return Lg, Sg, len(r), list(r.index)
        d = run_ls_ind(C, R, sig_at, months, cfg["cost"]); st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = null_circ_ind(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        d0 = run_ls_ind(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
        st["n_sector_names"] = int(len(sec)); st["n_sectors"] = int(sec.nunique())
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(),
                note="業種モメンタム 12-1・上位 3 業種買い／下位 3 業種売り（各業種 1/3・業種内等金額）。業種は今の分類（過去の変更は反映しない）"), csvs

def main():
    args = B.parse_args("Q704 業種モメンタム（日本株・米国株）"); rng = np.random.default_rng(args.seed); args.out = args.out or os.path.join(HERE, "results")  # 土台の既定は Q578 のフォルダなので上書き
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
