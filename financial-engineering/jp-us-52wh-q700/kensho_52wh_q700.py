# -*- coding: utf-8 -*-
"""Q700 日本株・米国株の 52 週高値への近さ（終値÷52 週高値）の上位 10% 買い・下位 10% 売り（1 か月保有）— 無料層での追試

【出典】George & Hwang 2004 JF「The 52-Week High and Momentum Investing」。Liu, Liu & Ma 2011（20 市場のうち 18 で利益・長期の反転なし）。Du 2008（指数では反転と共存）。
       先行研究チェック 2026-11-10 WebSearch standard「52-week high momentum George Hwang 2004 international evidence Japan replication」: 多国の研究
       （Liu ほか 2011・ポルトガルの修士論文 18 市場中 12 で有意）。日本単独の再現は見つからない（NCU の研究計画が「日本は短期モメンタムが無いので良い試験場」と書くだけ）。
       未確認の点: 日本・2006〜2024-06・売買代金上位 1,000・コスト後。
【仮説】H1: 終値÷52 週高値が高い上位 10% 買い・低い下位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。
       H0: 両国とも NW t<1（日本は 12-1 モメンタムが Q563 で棄却されているので、52 週高値も効かない見込み）。
【定義】シグナル＝C(t) ÷ max(H[t−251..t])（調整済み高値の 252 日最大）。履歴 252 日。高値は equities_free の "high"（smoke は close×(1+|noise|)）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案 1（52 週高値と 12-1 モメンタムの 2 重並べ替え〔本数が増える〕）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜・封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。
【適格・保有・コスト】(Q576〜Q578 と同じ・土台 `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py` を importlib で読む)
       判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。
       保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。等金額。上位 10% 買い・下位 10% 売り。
       コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・
       σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の日米 8 本 Q700〜Q707 共通）】支持＝両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ
       2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6%。棄却＝両国とも NW t<1。未確定＝それ以外（片方の国だけ通る場合は「未確定（片方: 国名）」）。
       無料層で落ちた案は有料データで救済しない。支持なら J-Quants Standard での再判定が次段階。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q700.json の per_market.* の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_*_q700.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_52wh_q700.py（Mac・venv_equities・lightgbm 不要・pandas 3。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"

QID = "Q700"; LOOKBACK = 252

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]
        C, V = B.load_px(mkt, args.smoke, rng)
        if args.smoke:
            H = C * (1 + pd.DataFrame(np.abs(rng.normal(0, 0.01, C.shape)), C.index, C.columns))
        else:
            import equities_free as ef
            if os.environ.get("EQ_DIR"): ef.DIR = os.environ["EQ_DIR"]
            H = ef.load(mkt, "high", end=B.SEAL).reindex(index=C.index, columns=C.columns)
        R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, LOOKBACK)
        Hmax = H.rolling(252, min_periods=int(252 * 0.9)).max()            # 調整済み高値の 252 日最大（t−251..t）
        def sig_at(t, el):
            c, h = C.loc[t].reindex(el), Hmax.loc[t].reindex(el)
            return c / h.where(h > 0)
        d = B.run_ls(C, R, sig_at, months, cfg["cost"]); st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = B.null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        d0 = B.run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(), note="シグナル=C÷max(H,252日)。高値は調整済み OHLC の high。"), csvs

def main():
    args = B.parse_args("Q700 52 週高値への近さ（日本株・米国株）"); rng = np.random.default_rng(args.seed)
    if args.out is None: args.out = os.path.join(HERE, "results")   # 土台は自分のフォルダに書くので、この案の results/ に向ける
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
