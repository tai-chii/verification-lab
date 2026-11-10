# -*- coding: utf-8 -*-
"""Q705 日本株・米国株の個別株の時系列モメンタム（自分の 12-1 か月リターンの符号で買い／売り・等金額）はコスト後 2006〜2024-06 に両国で残るか

【出典】Moskowitz, Ooi & Pedersen 2012 JFE（先物の時系列モメンタム）。Lim, Wang & Yao 2018「Time-Series Momentum in Nearly 100 Years of Individual Stock Returns」（米国個別株 1927〜2017・市場の状態に依存）。
       Goyal & Jegadeesh 2017 RFS（時系列と横断は別の源ではなく、純ロングの市場露出の差）。
       先行研究チェック 2026-11-10 WebSearch standard「time series momentum individual stocks Moskowitz Ooi Pedersen single stock evidence」: 上の 3 本と、米国株 1962〜2013 で単純なトレンド規則は個別株で見込み薄とする研究。
       未確認の点: 日本の個別株・2006〜2024-06・コスト後。横断の 12-1（Q563）は両国で棄却済みなので、Goyal–Jegadeesh の指摘どおり「時系列版の差は純ロング露出」かを市場アルファで見る。
【仮説】H1: 自分の 12-1 か月リターンが正の銘柄を全部買い・負の銘柄を全部売り（等金額・L と S を各 1 単位）は、両国でコスト後 NW t≥2・前後半とも年単位 t≥2・市場アルファも正。H0: 両国とも NW t<1。
【定義】シグナル = sign(C[t−21]÷C[t−252] − 1)。買い＝正の全銘柄の等金額・売り＝負の全銘柄の等金額（上下 10% ではない。片側が 30 銘柄未満の判断日は飛ばす）。この案だけ符号で選ぶループを書く（土台の run_ls を写して選択の行だけ変える）。
       記述（res["sub"]）: 純ロング露出（買いの数 − 売りの数）÷全体の平均と、市場アルファ（土台の stats が出す）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案: 1（ボラ目標の規模調整〔MOP の形・無料層の等金額の土台に合わない〕）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜・封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。
【適格・保有・コスト】判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。
       保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで・等金額。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。前後半の境 2015-01-01。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の日米 8 本 Q700〜Q707 共通）】支持＝両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6%。
       棄却＝両国とも NW t<1。未確定＝それ以外（片方の国だけ通る場合は「未確定（片方: 国名）」）。無料層で落ちた案は有料データで救済しない。支持なら J-Quants Standard での再判定が次段階。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q705.json の per_market.{jp,us} の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_{jp,us}_q705.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_stock_tsmom_q705.py（Mac・pandas 3・lightgbm 不要。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

QID = "Q705"; LOOKBACK = 252; MIN_SIDE = 30

def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"


def run_ls_sign(C, R, sig_at, months, cost, shift=0):
    """B.run_ls の写し。選択の行だけ変更: 上下 10% → シグナル>0 を全部買い・<0 を全部売り（片側 MIN_SIDE 未満の月は飛ばす）。
    回転は L・S それぞれ「自分の銘柄数」で割った対称差の平均。nL・nS は純ロング露出の記述用。"""
    n = len(months); sigs = [sig_at(t, el) for t, _, _, el in months]
    rows = []; prevL = prevS = set()
    for j in range(n):
        t, e, x, _ = months[j]; v = sigs[(j - shift) % n].dropna()
        if len(v) < B.MIN_NAMES: continue
        L, S = list(v.index[v.values > 0]), list(v.index[v.values < 0])                      # ← ここだけ run_ls と違う
        if len(L) < MIN_SIDE or len(S) < MIN_SIDE: continue
        days = R.loc[(R.index >= e) & (R.index <= x)]
        if not len(days): continue
        cols = [c for c in v.index if c in days.columns]
        ls = days[L].mean(axis=1) - days[S].mean(axis=1); mk = days[cols].mean(axis=1)
        turn = (len(set(L) ^ prevL) / len(L) + len(set(S) ^ prevS) / len(S)) / 2
        ls = ls.copy(); ls.iloc[0] -= 2 * cost * turn
        rows.append(pd.DataFrame({"ls": ls, "mkt": mk, "turn": turn, "n": len(v), "nL": len(L), "nS": len(S)}))
        prevL, prevS = set(L), set(S)
    return pd.concat(rows) if rows else pd.DataFrame(columns=["ls", "mkt", "turn", "n", "nL", "nS"])

def null_circ_sign(C, R, sig_at, months, cost, Bn, rng, obs_mean, min_shift=13):
    """B.null_circ の写し（run_ls_sign を使う）。"""
    n = len(months); vals = []
    for _ in range(Bn):
        k = int(rng.integers(min_shift, n - min_shift)); d = run_ls_sign(C, R, sig_at, months, cost, shift=k)
        vals.append(d["ls"].mean())
    vals = np.array(vals, float); sd = vals.std()
    return dict(B=Bn, null_mean_bp=1e4 * vals.mean(), null_sd_bp=1e4 * sd,
                z=(obs_mean - vals.mean()) / sd if sd > 0 else np.nan, p=float((vals >= obs_mean).mean()))

def run(args, rng):
    per, csvs, sub = {}, {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]; C, V = B.load_px(mkt, args.smoke, rng); R = C.pct_change(fill_method=None)
        R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, LOOKBACK)
        M = C.shift(21) / C.shift(LOOKBACK) - 1                  # 行 t = C[t−21]÷C[t−252] − 1
        def sig_at(t, el):
            return np.sign(M.loc[t].reindex(el))
        d = run_ls_sign(C, R, sig_at, months, cfg["cost"]); st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = null_circ_sign(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        d0 = run_ls_sign(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
        m = d.groupby(d.index.to_period("M"))[["nL", "nS"]].first()
        sub[mkt] = dict(net_long_exposure=float(((m["nL"] - m["nS"]) / (m["nL"] + m["nS"])).mean()), nL_mean=float(m["nL"].mean()), nS_mean=float(m["nS"].mean()),
                        alpha_bp=st["alpha_bp"], beta=st["beta"])
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(), sub=sub,
                note="個別株の時系列モメンタム（符号で全銘柄）。sub.*.net_long_exposure＝(買い数−売り数)÷(買い数+売り数) の月平均"), csvs

def main():
    args = B.parse_args("Q705 個別株の時系列モメンタム（日本株・米国株）"); rng = np.random.default_rng(args.seed); args.out = args.out or os.path.join(HERE, "results")  # 土台の既定は Q578 のフォルダなので上書き
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
