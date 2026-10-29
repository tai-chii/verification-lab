# -*- coding: utf-8 -*-
"""Q566 業種内の短期反転（直近 1 か月の業種平均からの超過リターンが低い銘柄を買い・高い銘柄を売る・月次・上下 10%）— 日本株

【出典】Da, Liu & Schaumburg「A Closer Look at the Short-Term Return Reversal」（Management Science 2014／NY Fed Staff Report 513）:
       米国 1982-01〜2009-03 で素の 1 か月反転は 0.53%/月（t 2.66）だが、業種をまたぐ成分（業種モメンタム）が −0.30%/月で足を引っ張る。
       業種内の反転は 0.82%/月（t 5.49）。スプレッドからのコスト推定は約 80.5 bp/月で、コスト後に残るのは DR ニュース版の 0.54%/月。
       先行研究チェック 2026-10-29 WebSearch standard「industry-adjusted short-term reversal weekly Japan stocks Da Liu Schaumburg」:
       NY Fed SR513 の要旨（上の数字）を確認。日本株の業種内反転を無料層・コスト後で測った結果は見つからなかった＝条件の穴（場所の穴）。
       関連する自分の検証: Q544（J-Quants・2024-08〜2026-07・週次の素の反転・売買代金上位 1,000）は −6.7 bp/週（t −0.27）＝反転は無かった。
【仮説】H1: 日本株で、業種内の 1 か月反転の L−S がコスト後 NW t≥2。素の反転（業種で引かない）より強い（副）。
【データ】Q562 無料層（jp_daily.parquet・現構成・2005-01〜2024-06・封印は開けない）。業種＝universe_jp.csv の東証 33 業種（**現在の分類**＝過去の業種変更は反映しない・注記）。
       米国株は無料層に業種が無いので対象外（捨てた案 1）。
【定義】判断日 t＝月末。r1＝t の終値 ÷ 21 営業日前の終値 − 1。シグナル＝−(r1 − 同じ業種の適格銘柄の r1 の平均)（業種の適格銘柄が 5 未満なら欠損）。
       適格・建玉・保有・コスト・帰無は Q563/Q564 と同一（株価≥100 円・売買代金 20 日平均の上位 1,000・履歴 252 日以上・上位 10% 買い・下位 10% 売り・
       等金額・月末翌営業日の終値から・片道 10 bp・循環シフト B=200・NW ラグ 21・前後半 2005〜2014／2015〜2024-06）。
【測るもの】日次 L−S（bp/日・コスト後）・NW t・前後半・市場ベータ・回転。副: 素の 1 か月反転（シグナル＝−r1）の同じ数字（合否に使わない）。
【判定（事前固定・変更禁止）】NW t≥2 かつ前後半とも平均>0 かつ帰無 z≥2 → 支持。t<1 → 棄却。それ以外 → 未確定。主は 1 本（日本・業種内）。
【捨てた案の数】1（米国株＝業種なし）。週次版は回転が約 4 倍でコスト負けが先に見えるので捨てた（2）。
【知識の締め切り】Opus 5.5（〜2026-06）。Da-Liu-Schaumburg の数字は WebFetch で要旨を確認。
【委託の確かめ方】results/result_q566.json の per_market.jp.t_nw・null.z・verdict、sub_raw（素の反転）、turn_mean（月の回転）、n_months。
【事前登録からの変更点】なし（2026-10-29 試走後に結果の保存先を本フォルダの results/ に固定＝判定に無関係）。
【実装】Mac: ../../../../作業層/venv_equities/bin/python kensho_industry_reversal_q566.py（EQ_DIR で置き場を上書き可）。--smoke は合成データで経路確認のみ。
       共通の土台（月次 L/S・帰無・統計）は Q564 のスクリプトから import して変えずに使う。
"""
import os, sys, csv
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jp-us-residual-momentum-q564"))
import kensho_residual_momentum_q564 as B

QID = "Q566"; LOOKBACK, H1M, MIN_IND = 252, 21, 5


def sectors(cols, smoke, rng):
    if smoke:
        return pd.Series(rng.integers(0, 33, len(cols)), index=cols)
    p = os.path.join(os.environ.get("EQ_DIR") or os.path.join(B.WS, "作業層", "大容量", "equities_free"), "universe_jp.csv")
    m = {r["symbol"]: r["sector"] for r in csv.DictReader(open(p, encoding="utf-8"))}
    return pd.Series({c: m.get(c) for c in cols})


def run(args, rng):
    cfg = B.CFG["jp"]; C, V = B.load_px("jp", args.smoke, rng)
    R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    months = B.build_months(C, V, cfg, LOOKBACK); pos = {t: i for i, t in enumerate(C.index)}
    sec = sectors(C.columns, args.smoke, rng)

    def r1(t, el):
        i = pos[t]; x = (C.iloc[i] / C.iloc[i - H1M] - 1).reindex(el)
        return x.where(x.abs() < 1.0)

    def sig_ind(t, el):
        x = r1(t, el); g = sec.reindex(x.index)
        m = x.groupby(g).transform("mean"); n = x.groupby(g).transform("count")
        return (-(x - m)).where((n >= MIN_IND) & g.notna())

    def sig_raw(t, el):
        return -r1(t, el)

    per, csvs, sub = {}, {}, {}
    for name, f in [("jp", sig_ind), ("raw", sig_raw)]:
        d = B.run_ls(C, R, f, months, cfg["cost"]); st = B.stats(d["ls"], d["mkt"])
        st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
        st["null"] = B.null_circ(C, R, f, months, cfg["cost"], args.B, rng, d["ls"].mean())
        csvs[f"daily_{name}"] = d
        if name == "jp": per["jp"] = st
        else: sub = st
    ok = per["jp"]["t_nw"] >= 2 and per["jp"]["h1_bp"] > 0 and per["jp"]["h2_bp"] > 0 and per["jp"]["null"]["z"] >= 2
    verdict = "支持" if ok else ("棄却" if per["jp"]["t_nw"] < 1 else "未確定")
    return dict(qid=QID, per_market=per, sub_raw=sub, verdict=verdict,
                rule="NW t≥2 かつ前後半とも平均>0 かつ帰無 z≥2 → 支持。t<1 → 棄却。それ以外 → 未確定（日本・業種内の 1 本）"), csvs


def main():
    args = B.parse_args("Q566 業種内の短期反転（日本株）")
    if not args.markets or args.markets == "jp,us": args.markets = "jp"
    if args.out is None: args.out = os.path.join(HERE, "results")
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng); B.write_result(QID, res, csvs, args)


if __name__ == "__main__": main()
