# -*- coding: utf-8 -*-
"""Q696 米国株のバリュー合成（B/P・E/P・S/P・CF/P の順位平均）は 2010-07〜2024-06 のコスト後に残るか

【出典】Fama & French 1992・1993（B/M）、Fama & French 2020「The Value Premium」（1963-07〜2019-06 を半分に分けると大型のバリュープレミアムは月 0.36% → 0.05%）、Gonçalves & Leonard 2023 JFE。
       先行研究チェック 2026-11-10 WebSearch standard: Fama–French 2020・Gonçalves–Leonard 2023・Hasler 2021 ほか。未確認の点: 2010-07〜2024-06 を SEC のポイントインタイム財務と無料の価格・売買代金上位 800・コスト後・4 比率の合成で独立に測った結果は見つからない。
【仮説】H1: 4 比率の順位平均が高い（割安）上位 10% 買い・下位 10% 売りは、コスト後に NW t≥2・前後半とも年単位 t≥2。H0: NW t<1（2010 年以降の低迷が続いている）。
【データ】`作業層/大容量/sec/facts.parquet`（EDGAR XBRL companyfacts・861 銘柄・filed 2009-04〜）のポイントインタイム財務（`us-sec-value-q696/sec_pit.py`）＋
       `作業層/大容量/equities_free/us_daily.parquet`（調整済み終値・出来高・封印 2024-07-01 以降は読まない）。生存バイアスあり。
【定義】B/P＝株主資本÷株数÷F÷調整済み終値。E/P＝年次純利益÷株数÷F÷終値。S/P＝年次売上÷株数÷F÷終値。CF/P＝年次営業 CF÷株数÷F÷終値。
       合成＝4 比率それぞれの横断順位（適格銘柄の中の 0〜1・高いほど割安）の平均（3 つ以上そろえば計算・2 つ以下は欠損）。負の E/P・CF/P はそのまま低い順位。
       主の判定は合成 1 本。単独 4 本は同じ規則で測り記述だけ（res["sub"]・合否に使わない・多重比較に数えない）。
       SEC 財務の読み方（Q696〜Q699 共通）: 判断日 t（月末）には filed ≤ t の行だけ。各タグで end 最大（同じ end なら filed 最新）。フロー＝fp==FY かつ期間 330〜400 日、
       ストック＝end 最大（10-Q 含む）。分割は株数の連続比が ≥1.4（または ≤1/1.4）で整数比 {1.5,2,3,4,5,6,7,8,10,20} の ±5% 以内なら補正（F）。
       適格＝株価≥5 ドル・売買代金 20 日平均の上位 800・履歴 252 日の 9 割以上 ∧ その案に要る財務がそろう。判断日の最低銘柄数 200。期間 2010-07-01〜2024-06-30。前後半の境 2017-07-01。
       上位 10% 買い・下位 10% 売り・等金額。保有＝t の翌営業日の終値から次の月末の翌営業日の終値まで。コスト＝片道 5 bp × 片側回転（初日に差し引く）。±50% 超の日次リターンは欠損扱い。
【測るもの】日次 L−S の平均（bp/日）・NW t（ラグ 21）・年単位 t（全期間・前半・後半）・市場アルファとベータ・年率シャープ・σ0.25%/日 換算の最大 DD・回転。副（合否に使わない）: コスト 0 の平均と t。
【帰無】シグナルの月の循環シフト（k∈[13, N−13]・B=200）。時間の対応だけを壊す（銘柄の並べ替えは使わない・Q545 の教訓）。
【判定（事前固定・変更禁止・第3弾の米国 SEC 4 本 Q696〜Q699 共通）】日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ
       帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。
【多重比較】主 1 本（米国のみ）。株式無料層の第3弾は主 12 本。
【捨てた案の数】2（時価総額加重〔無料層の等金額の土台に合わない〕、EV/EBITDA〔負債・現金のタグがそろわない〕）。
【知識の締め切り】設計者（Fable）の知識は 2026-06 まで。対象期間は公表後で、既知の結果を含む。
【委託の確かめ方】results/result_q696.json の per_market.us の t_nw・h1_ty・h2_ty・null.z・p_holm・maxdd_s025 と verdict。daily_us_q696.csv の turn が設計の回転と合うか。--smoke --B 5 が合成データで通ること（本番データでは実行者が 1 回だけ）。
【実装】PYTHONUTF8=1 作業層/venv_equities/bin/python kensho_value_q696.py（lightgbm 不要・pandas 3。EQ_DIR・SEC_DIR でデータ置き場を上書き可）。--smoke は合成データで経路確認のみ。
"""
import importlib.util, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base578", os.path.join(HERE, "..", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)
_sp = importlib.util.spec_from_file_location("sec_pit", os.path.join(HERE, "..", "us-sec-value-q696", "sec_pit.py"))
P = importlib.util.module_from_spec(_sp); sys.modules["sec_pit"] = P; _sp.loader.exec_module(P)

QID = "Q696"


def verdict_us(per):
    """事前固定（第3弾 Q696〜Q699 共通・変更禁止）。日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。"""
    r = per["us"]; r["p_holm"] = r["p_one"]
    if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["maxdd_s025"] > -0.06: return "米国で通過（日本の追試待ち）"
    if r["t_nw"] < 1: return "棄却"
    return "未確定"


def make_signal(f, mes, C):
    px = C.loc[mes]
    sh, she, Fe, ev, _ = P.shares_at(f, mes)
    eq = P.pit_value(f, P.TAG_EQ, mes)
    ni = P.pit_value(f, P.TAG_NI, mes, annual=True)
    rev = P.pit_value(f, P.TAG_REV, mes, annual=True)
    ocf = P.pit_value(f, P.TAG_OCF, mes, annual=True)
    ratios = {"BP": P.ratio_to_price(eq, sh, Fe, px), "EP": P.ratio_to_price(ni, sh, Fe, px),
              "SP": P.ratio_to_price(rev, sh, Fe, px), "CFP": P.ratio_to_price(ocf, sh, Fe, px)}
    ratios = {k: v.replace([np.inf, -np.inf], np.nan) for k, v in ratios.items()}

    def comp(t, el):
        R = pd.DataFrame({k: v.loc[t].reindex(el) for k, v in ratios.items()})
        out = R.rank(pct=True).mean(axis=1)
        return out.where(R.notna().sum(axis=1) >= 3)
    subs = {k: P.frame_sig(v) for k, v in ratios.items()}
    return dict(main=comp, subs=subs, diag=dict(n_split_events=int(len(ev)), n_tickers=int(f["ticker"].nunique())))


def run(args, rng):
    args.markets = "us"
    return P.run_us(B, args, rng, QID, make_signal, verdict_us, note="Q696 バリュー合成。単独 4 本は sub に記述のみ。")


def main():
    args = B.parse_args("Q696 米国株のバリュー合成"); args.markets = "us"; args.out = args.out or os.path.join(HERE, "results"); rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)


if __name__ == "__main__": main()
