# -*- coding: utf-8 -*-
"""Q706 日本株・米国株の中間モメンタム（12-7 か月リターン・上下 10%）はコスト後 2006〜2024-06 に両国で残るか

【出典】Novy-Marx 2012 JFE「Is Momentum Really Momentum?」（12〜7 か月前の成績が直近 6〜2 か月より強く予測）。Gong, Liu & Liu 2011（国際・多くの市場で 12-7 が支配的）。
       Goyal & Wahal 2015 JFE「Is Momentum an Echo?」（米国外 37 か国では 12-7 の優位は無い・反論）。Asness 2011「Momentum in Japan」（日本は例外）。
       先行研究チェック 2026-11-10 WebSearch standard「intermediate horizon momentum 12-7 Novy-Marx 2012 international replication Japan」: Gong ほか 2011 と Novy-Marx 2012 は見つかり、
       日本単独の数字は見つからない（Goyal–Wahal 2015 は知識から記載・実行者が原典と照合）。未確認の点: 日本の 2006〜2024-06・売買代金上位 1,000・コスト後。12-1（Q563）が両国で棄却なので、12-7 が別物かを同じ土台で見る。
【仮説】H1: 12-7 か月リターンの上位 10% 買い・下位 10% 売りは、両国でコスト後 NW t≥2・前後半とも年単位 t≥2。H0: 両国とも NW t<1。
【定義】シグナル = C[t−147]÷C[t−252] − 1（12 か月前から 7 か月前まで・営業日 21 日＝1 か月）。上位 10% 買い・下位 10% 売り・等金額（土台の run_ls そのまま）。
【多重比較・捨てた案】主 2 本（2 国・Holm）。捨てた案: 1（6-2 の直近モメンタムとの対比〔本数が増える・Q563 で近い形は棄却〕）。
【データ】`作業層/大容量/equities_free/{jp,us}_daily.parquet`（yfinance の調整済み OHLC・出来高・2005-01〜・封印 2024-07-01 以降は読まない）。生存バイアスあり（今の構成）。
【適格・保有・コスト】判断日 t＝月末。適格＝株価≥100 円（US 5 ドル）・売買代金 20 日平均の上位 1,000（US 800）・履歴 252 日の 9 割以上。判断日の最低銘柄数 300。
       保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで・等金額。コスト＝片道 JP 10 bp／US 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。前後半の境 2015-01-01。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の日米 8 本 Q700〜Q707 共通）】支持＝両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6%。
       棄却＝両国とも NW t<1。未確定＝それ以外（片方の国だけ通る場合は「未確定（片方: 国名）」）。無料層で落ちた案は有料データで救済しない。支持なら J-Quants Standard での再判定が次段階。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q706.json の per_market.{jp,us} の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_{jp,us}_q706.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_mom_12_7_q706.py（Mac・pandas 3・lightgbm 不要。EQ_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

QID = "Q706"; LOOKBACK = 252

def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"

def run(args, rng):
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]; C, V = B.load_px(mkt, args.smoke, rng); R = C.pct_change(fill_method=None)
        R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, LOOKBACK)
        S = C.shift(147) / C.shift(252) - 1                    # 行 t = C[t−147]÷C[t−252] − 1
        def sig_at(t, el):
            return S.loc[t].reindex(el)
        d = B.run_ls(C, R, sig_at, months, cfg["cost"]); st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["first_day"] = str(d.index.min().date()) if len(d) else None
        st["null"] = B.null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
        d0 = B.run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=QID, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(), note="12-7 か月モメンタム・上下 10%・土台の run_ls そのまま"), csvs

def main():
    args = B.parse_args("Q706 中間モメンタム 12-7（日本株・米国株）"); rng = np.random.default_rng(args.seed); args.out = args.out or os.path.join(HERE, "results")  # 土台の既定は Q578 のフォルダなので上書き
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)

if __name__ == "__main__": main()
