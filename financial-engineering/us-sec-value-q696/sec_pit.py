# -*- coding: utf-8 -*-
"""sec_pit — SEC 財務（EDGAR XBRL companyfacts）のポイントインタイム読み込み・分割補正・合成データ・共通ドライバ（Q696〜Q699 共通・2026-11-10）

仕様の本体は `事前登録_q696.md` の「SEC 財務の読み方」。要点:
- ポイントインタイム: 判断日 t には filed ≤ t の行だけ使う。各タグで end が最大の値（同じ end ならタグの優先順位・filed 最新）。複数タグは「end が最新のもの」を採り、
  同じ end なら優先順の高いタグ（タグの切り替わりで古い値に張り付かないため）。
- フロー（純利益・売上・営業 CF）: fp=="FY" かつ 期間 330〜400 日（annual=True）。ストック（総資産・株主資本・株数）: end 最大（10-Q を含む）。
- 1 年前の値 prior_year: 現在の値の end より 300〜430 日前の end のうち最新（その end の最初に出た値＝当初の報告）。
- 株数: CommonStockSharesOutstanding → WeightedAverageNumberOfDilutedSharesOutstanding（銘柄ごとに系列を 1 本に固定。優先タグの end が 8 本以上あればそれ・無ければ次）。
- 分割: 連続する株数の比 r が ≥1.4 または ≤1/1.4 で、r か 1/r が {1.5,2,3,4,5,6,7,8,10,20} の ±5% 以内なら分割（比は名目値に丸める）。事象の日付＝分割後の最初の観測の end。
  F(t)＝t より後（event 日 > t）の分割の積。ratio の計算では「株数の観測日 end」での F を使う（factor_at_end・README に差を書く）。
- 比率 = 財務 ÷ 株数 ÷ F ÷ 調整済み終値。

使い方: 各 kensho_*.py が importlib で読む。`python sec_pit.py --selftest`（合成データの自己試験）／ `--peek`（本物の MMM の Assets の pit 値を 2 日分表示・読むだけ）。
"""
import argparse, os, sys, json, datetime
import numpy as np, pandas as pd

WS = os.environ.get("WS") or os.path.expanduser("~/ワークスペース")
FACTS_PATH = os.path.join(os.environ.get("SEC_DIR") or os.path.join(WS, "作業層", "大容量", "sec"), "facts.parquet")

TAG_NI = ["NetIncomeLoss", "ProfitLoss"]
TAG_REV = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"]
TAG_EQ = ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
TAG_OCF = ["NetCashProvidedByUsedInOperatingActivities"]
TAG_ASSETS = ["Assets"]
TAG_SHARES = ["CommonStockSharesOutstanding", "WeightedAverageNumberOfDilutedSharesOutstanding"]
ALL_TAGS = TAG_NI + TAG_REV + TAG_EQ + TAG_OCF + TAG_ASSETS + TAG_SHARES

START, END = pd.Timestamp("2010-07-01"), pd.Timestamp("2024-06-30")   # 評価期間
SPLIT_BOUNDARY = pd.Timestamp("2017-07-01")                            # 前後半の境
MIN_NAMES_SEC = 200
SPLIT_NOMINAL = [1.5, 2, 3, 4, 5, 6, 7, 8, 10, 20]


# ---- 読み込み ------------------------------------------------------------------------------
def _prep(f):
    for c in ("start", "end", "filed"):
        f[c] = pd.to_datetime(f[c])
    f["dur"] = (f["end"] - f["start"]).dt.days      # 瞬間項目は start が NaT → NaN
    return f.reset_index(drop=True)


def load_facts(smoke=False, rng=None, tickers=None):
    """facts（列 ticker, tag, unit, start, end, fy, fp, form, filed, val + dur）。smoke なら合成データ。"""
    if smoke:
        return _prep(_synth(rng if rng is not None else np.random.default_rng(0)))
    flt = [("tag", "in", ALL_TAGS)]
    if tickers is not None: flt.append(("ticker", "in", list(tickers)))
    f = pd.read_parquet(FACTS_PATH, filters=flt)
    return _prep(f)


# ---- ポイントインタイム ---------------------------------------------------------------------
def _tag_frame(f, tags, annual):
    d = f[f["tag"].isin(tags)]
    if annual:
        d = d[(d["fp"] == "FY") & (d["start"].isna() | d["dur"].between(330, 400))]
    d = d.copy()
    d["prio"] = -d["tag"].map({t: i for i, t in enumerate(tags)}).astype(int)   # 先頭のタグほど大
    return d


def _frame_from(dct, mes):
    out = pd.DataFrame.from_dict(dct, orient="index")
    return out.reindex(pd.DatetimeIndex(mes))


def pit_value(f, tags, month_ends, annual=False, with_end=False):
    """判断日ごとの値（date × ticker）。filed ≤ t の行だけ・end 最大（同じ end ならタグ優先・filed 最新）。
    annual=True: fp=="FY" かつ 期間 330〜400 日。with_end=True なら (値, その end) を返す。"""
    d = _tag_frame(f, tags, annual).sort_values(["end", "prio", "filed"], kind="stable")
    fl = d["filed"].values
    vals, ends = {}, {}
    for t in month_ends:
        sub = d[fl <= np.datetime64(t)]
        last = sub.groupby("ticker", sort=False).tail(1).set_index("ticker")
        vals[t] = last["val"]; ends[t] = last["end"]
    V = _frame_from(vals, month_ends)
    return (V, _frame_from(ends, month_ends)) if with_end else V


def prior_year(f, tags, month_ends, cur_end, annual=False, lo=300, hi=430, with_end=False):
    """cur_end（date × ticker・現在の値の end）より lo〜hi 日前の end のうち最新の値（その end の最初に出た値）。filed ≤ t のみ。"""
    d = _tag_frame(f, tags, annual)
    d["nf"] = -d["filed"].astype("int64")                      # 大きいほど filed が古い
    d = d.sort_values(["end", "prio", "nf"], kind="stable")
    fl = d["filed"].values
    vals, ends = {}, {}
    for t in month_ends:
        ce = cur_end.loc[t].dropna()
        sub = d[(fl <= np.datetime64(t))]
        sub = sub[sub["ticker"].isin(ce.index)]
        gap = (sub["ticker"].map(ce) - sub["end"]).dt.days
        sub = sub[gap.between(lo, hi)]
        last = sub.groupby("ticker", sort=False).tail(1).set_index("ticker")
        vals[t] = last["val"]; ends[t] = last["end"]
    V = _frame_from(vals, month_ends)
    return (V, _frame_from(ends, month_ends)) if with_end else V


# ---- 株数と分割 -----------------------------------------------------------------------------
def shares_frame(f):
    """株数の行だけを、銘柄ごとにタグ 1 本へ固定して返す（優先タグの end が 8 本以上あればそれ・無ければ次・全部無ければ最多）。
    Weighted… は 3 か月または年次の期間だけ（YTD の累計期間は除く）。"""
    d = f[f["tag"].isin(TAG_SHARES)]
    d = d[(d["tag"] == TAG_SHARES[0]) | (d["dur"] <= 110) | d["dur"].between(330, 400)]
    cnt = d.groupby(["ticker", "tag"])["end"].nunique().unstack().reindex(columns=TAG_SHARES).fillna(0)
    pick = {}
    for tk, row in cnt.iterrows():
        ok = [t for t in TAG_SHARES if row[t] >= 8]
        pick[tk] = ok[0] if ok else row.idxmax()
    return d[d["tag"] == d["ticker"].map(pick)].copy()


def split_events(sf):
    """分割の事象（ticker, date=分割後の最初の観測の end, ratio=名目値。縮小は 1/名目値）。当初の報告（最初に出た filed）の系列で判定する。"""
    h = sf.sort_values(["ticker", "end", "filed"]).drop_duplicates(["ticker", "end"], keep="first")
    h = h[h["val"] > 0].copy()
    h["prev"] = h.groupby("ticker")["val"].shift()
    r = h["val"] / h["prev"]
    c = h[r.notna() & ((r >= 1.4) | (r <= 1 / 1.4))].copy()
    c["r"] = r[c.index]
    rows = []
    for tk, e, rr in zip(c["ticker"], c["end"], c["r"]):
        x = rr if rr >= 1 else 1 / rr
        near = [n for n in SPLIT_NOMINAL if abs(x / n - 1) <= 0.05]
        if near:
            n = min(near, key=lambda n: abs(x / n - 1))
            rows.append((tk, e, float(n if rr >= 1 else 1 / n)))
    return pd.DataFrame(rows, columns=["ticker", "date", "ratio"])


def split_factor(sf, dates, events=None, tickers=None):
    """F(t)（date × ticker）= t より後（event 日 > t）の分割の積。"""
    ev = split_events(sf) if events is None else events
    cols = list(tickers) if tickers is not None else sorted(sf["ticker"].unique())
    F = pd.DataFrame(1.0, index=pd.DatetimeIndex(dates), columns=cols)
    for tk, g in ev.groupby("ticker"):
        if tk not in F.columns: continue
        m = g["date"].values[None, :] > F.index.values[:, None]
        F[tk] = np.prod(np.where(m, g["ratio"].values[None, :], 1.0), axis=1)
    return F


def factor_at_end(events, end_df):
    """観測日 end（date × ticker）での F（end より後の分割の積）。観測した株数を『今の単位』に直す係数。end が NaT なら 1。"""
    F = pd.DataFrame(1.0, index=end_df.index, columns=end_df.columns)
    for tk, g in events.groupby("ticker"):
        if tk not in F.columns: continue
        e = end_df[tk].values
        m = (g["date"].values[None, :] > e[:, None]) & ~np.isnat(e)[:, None]
        F[tk] = np.prod(np.where(m, g["ratio"].values[None, :], 1.0), axis=1)
    return F


def shares_at(f, month_ends):
    """(株数 pit, その end, 観測日 end での F, 分割事象)。"""
    sf = shares_frame(f)
    sh, she = pit_value(sf, TAG_SHARES, month_ends, annual=False, with_end=True)
    ev = split_events(sf)
    return sh, she, factor_at_end(ev, she), ev, sf


def ratio_to_price(fin, sh, F, px):
    """財務 ÷ 株数 ÷ F ÷ 調整済み終値（px の列に揃える）。株数・終値が 0 以下なら欠損。"""
    cols = px.columns
    fin, sh, F = (x.reindex(index=px.index, columns=cols) for x in (fin, sh, F))
    r = fin / sh.where(sh > 0) / F / px.where(px > 0)
    return r.replace([np.inf, -np.inf], np.nan)


def frame_sig(S):
    """date × ticker の表を run_ls の sig_at(t, elig) にする。"""
    S = S.replace([np.inf, -np.inf], np.nan)
    return lambda t, el: S.loc[t].reindex(el)


# ---- 共通ドライバ（Q696〜Q699）---------------------------------------------------------------
def run_us(B, args, rng, qid, make_signal, verdict_fn, note=""):
    """米国だけを測る。make_signal(f, mes, C) -> dict(main=sig_at, subs={名前: sig_at}, diag={})。B は Q578 の土台モジュール。"""
    B.SPLIT = SPLIT_BOUNDARY; B.MIN_NAMES = MIN_NAMES_SEC
    cfg = B.CFG["us"]
    C, V = B.load_px("us", args.smoke, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
    months = [m for m in B.build_months(C, V, cfg, 252) if m[1] >= START and m[2] <= END + pd.Timedelta(days=5)]
    mes = [m[0] for m in months]
    f = load_facts(args.smoke, rng)
    sig = make_signal(f, mes, C)
    sig_at = sig["main"]
    d = B.run_ls(C, R, sig_at, months, cfg["cost"])
    st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
    st["turn_mean"] = float(d.groupby(d.index.to_period("M"))["turn"].first().mean()); st["n_months"] = int(d.index.to_period("M").nunique())
    st["first_day"] = str(d.index.min().date()) if len(d) else None
    st["names_mean"] = float(d["n"].mean()) if len(d) else None
    st["null"] = B.null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean())
    d0 = B.run_ls(C, R, sig_at, months, 0.0); st["sub_cost0_bp"] = 1e4 * d0["ls"].mean(); st["sub_cost0_t"] = B.nw_t(d0["ls"])
    per = {"us": st}; csvs = {"daily_us": d}
    res = dict(qid=qid, per_market=per, verdict=verdict_fn(per), rule=verdict_fn.__doc__.strip(), note=note, diag=sig.get("diag", {}))
    subs = {}
    for name, sa in (sig.get("subs") or {}).items():
        ds = B.run_ls(C, R, sa, months, cfg["cost"])
        s = B.add_c1(B.stats(ds["ls"], ds["mkt"]), ds["ls"])
        subs[name] = dict(mean_bp=s["mean_bp"], t_nw=s["t_nw"], h1_ty=s["h1_ty"], h2_ty=s["h2_ty"], maxdd_s025=s["maxdd_s025"],
                          turn_mean=float(ds.groupby(ds.index.to_period("M"))["turn"].first().mean()))
    if subs: res["sub"] = subs
    return res, csvs


# ---- 合成データ（smoke 用）------------------------------------------------------------------
def _synth(rng, n=400):
    """銘柄 S0..S{n-1}（B.load_px の合成の列名と同じ）・2008-12〜2024-06 の四半期。S7 に 2:1（2016-06）・S11 に 4:1（2019-03）・S13 に分割でない 1.7 倍の跳び、
    S9 系は株数が Weighted… だけ。10-K/A の再提出も混ぜる。"""
    qe = pd.date_range("2008-12-31", "2024-06-30", freq="QE"); nq = len(qe)
    is_fy = (qe.month == 12)
    fp = np.where(is_fy, "FY", np.char.add("Q", (qe.month // 3).astype(str)))
    form = np.where(is_fy, "10-K", "10-Q")
    filed = qe + pd.to_timedelta(np.where(is_fy, 60, 45), "D")
    parts = []

    def blk(tk, tag, mask, vals, start=None, filed_=None, form_=None, fp_=None):
        m = np.asarray(mask)
        k = int(m.sum())
        return pd.DataFrame(dict(ticker=tk, tag=tag, unit="USD", start=(start[m] if start is not None else pd.NaT),
                                 end=qe[m], fy=qe[m].year, fp=(fp_ if fp_ is not None else fp)[m],
                                 form=(form_ if form_ is not None else form)[m], filed=(filed_ if filed_ is not None else filed)[m],
                                 val=np.asarray(vals)[m]))
    start_fy = qe - pd.to_timedelta(364, "D")
    start_q = qe - pd.to_timedelta(89, "D")
    allq = np.ones(nq, bool)
    for i in range(n):
        tk = f"S{i}"
        A = np.exp(rng.normal(7, 1)) * 1e6 * np.exp(np.cumsum(rng.normal(0.02, 0.05, nq)))
        E = 0.4 * A * np.exp(rng.normal(0, 0.1, nq))
        sh = np.exp(rng.normal(18, 1)) * np.exp(np.cumsum(rng.normal(0, 0.01, nq)))
        if i == 7: sh = sh * np.where(qe >= pd.Timestamp("2016-06-30"), 2.0, 1.0)
        if i == 11: sh = sh * np.where(qe >= pd.Timestamp("2019-03-31"), 4.0, 1.0)
        if i == 13: sh = sh * np.where(qe >= pd.Timestamp("2018-03-31"), 1.7, 1.0)
        NI = E * rng.normal(0.08, 0.05, nq); REV = A * np.exp(rng.normal(-0.2, 0.3, nq)); OCF = NI + A * rng.normal(0, 0.03, nq)
        parts += [blk(tk, "Assets", allq, A), blk(tk, "StockholdersEquity", allq, E)]
        parts.append(blk(tk, "WeightedAverageNumberOfDilutedSharesOutstanding" if i % 10 == 9 else "CommonStockSharesOutstanding",
                         allq, sh, start=(start_q if i % 10 == 9 else None)))
        parts += [blk(tk, "NetIncomeLoss", is_fy, NI, start=start_fy), blk(tk, "Revenues", is_fy, REV, start=start_fy),
                  blk(tk, "NetCashProvidedByUsedInOperatingActivities", is_fy, OCF, start=start_fy),
                  blk(tk, "EarningsPerShareDiluted", is_fy, NI / sh, start=start_fy),
                  blk(tk, "NetIncomeLoss", ~is_fy, NI / 4, start=start_q)]           # 四半期の純利益（annual では除かれるはず）
        if i % 20 == 0:                                                              # 10-K/A の再提出（総資産を 1% 直す）
            parts.append(blk(tk, "Assets", is_fy, A * 1.01, filed_=qe + pd.to_timedelta(150, "D"),
                             form_=np.full(nq, "10-K/A")))
    return pd.concat(parts, ignore_index=True)


# ---- 自己試験 -------------------------------------------------------------------------------
def selftest():
    ok = True

    def chk(name, cond, info=""):
        nonlocal ok
        print(("OK  " if cond else "NG  ") + name + (f"  {info}" if info else ""))
        ok = ok and bool(cond)
    qe = pd.date_range("2012-03-31", "2021-12-31", freq="QE")
    rows = []

    def add(tk, tag, end, filed, val, fp="Q1", start=pd.NaT, form="10-Q"):
        rows.append(dict(ticker=tk, tag=tag, unit="shares", start=start, end=end, fy=end.year, fp=fp, form=form, filed=filed, val=val))
    # AAPL 型: 7:1（2014-06）と 4:1（2020-09 に初出）。自社株買いで毎期 -0.5%
    v = 900e6
    for e in qe:
        v *= 0.995
        if e == pd.Timestamp("2014-06-30"): v *= 7
        if e == pd.Timestamp("2020-09-30"): v *= 4
        add("AAA", "CommonStockSharesOutstanding", e, e + pd.Timedelta(days=35), v)
    v = 500e6                                                  # 増資の跳び 1.7（分割でない）と 1.3（閾値未満）
    for e in qe:
        if e == pd.Timestamp("2015-06-30"): v *= 1.7
        if e == pd.Timestamp("2017-06-30"): v *= 1.3
        add("BBB", "CommonStockSharesOutstanding", e, e + pd.Timedelta(days=35), v)
    v = 100e6                                                  # 1 対 10 の併合（縮小）
    for e in qe:
        if e == pd.Timestamp("2016-12-31"): v /= 10
        add("CCC", "CommonStockSharesOutstanding", e, e + pd.Timedelta(days=35), v)
    # PIT 用: DDD の Assets（10-K と 10-K/A の再提出）・純利益（四半期と年次）
    d0 = pd.Timestamp
    add("DDD", "Assets", d0("2019-12-31"), d0("2020-02-20"), 100.0, fp="FY", form="10-K")
    add("DDD", "Assets", d0("2019-12-31"), d0("2020-09-01"), 101.0, fp="FY", form="10-K/A")
    add("DDD", "Assets", d0("2020-12-31"), d0("2021-02-20"), 120.0, fp="FY", form="10-K")
    add("DDD", "Assets", d0("2020-06-30"), d0("2020-08-05"), 110.0, fp="Q2")
    add("DDD", "NetIncomeLoss", d0("2020-12-31"), d0("2021-02-20"), 10.0, fp="FY", start=d0("2020-01-01"), form="10-K")
    add("DDD", "NetIncomeLoss", d0("2021-03-31"), d0("2021-05-05"), 3.0, fp="FY", start=d0("2021-01-01"))   # fp=FY でも期間 89 日 → 除外
    add("DDD", "ProfitLoss", d0("2019-12-31"), d0("2020-02-20"), 8.0, fp="FY", start=d0("2019-01-01"), form="10-K")
    f = _prep(pd.DataFrame(rows))
    sf = f[f["tag"] == "CommonStockSharesOutstanding"]
    ev = split_events(sf)
    e = {tk: g.sort_values("date") for tk, g in ev.groupby("ticker")}
    chk("AAA は 2 件（7 と 4）", list(e["AAA"]["ratio"]) == [7.0, 4.0], str(list(e["AAA"]["ratio"])))
    chk("AAA の事象日", list(e["AAA"]["date"]) == [d0("2014-06-30"), d0("2020-09-30")])
    chk("BBB（1.7・1.3 倍）は分割でない", "BBB" not in e)
    chk("CCC の 1 対 10 併合は ratio=0.1", "CCC" in e and abs(e["CCC"]["ratio"].iloc[0] - 0.1) < 1e-12)
    ts = pd.DatetimeIndex(["2013-12-31", "2014-05-31", "2014-06-30", "2015-12-31", "2020-09-30", "2021-12-31"])
    F = split_factor(sf, ts, events=ev)
    exp = [28.0, 28.0, 4.0, 4.0, 1.0, 1.0]
    chk("F(t) AAA", np.allclose(F["AAA"].values, exp), str(F["AAA"].tolist()))
    chk("F(t) CCC（併合）は併合の前 0.1・後 1", np.allclose(split_factor(sf, pd.DatetimeIndex(["2016-06-30", "2017-03-31"]), events=ev)["CCC"].values, [0.1, 1.0]))
    chk("F(t) BBB は常に 1", np.allclose(F["BBB"].values, 1.0))
    # 観測日 end での F と、分割補正した株数が 1 本の滑らかな系列になること
    mes = list(pd.date_range("2012-06-30", "2021-12-31", freq="QE"))
    sh, she, Fe, ev2, _ = shares_at(f[f["ticker"].isin(["AAA"])], mes)
    adj = (sh["AAA"] * Fe["AAA"]).astype(float)
    chk("分割補正後の AAA の株数は期ごとに ±3% 以内（跳びなし）", (adj / adj.shift()).dropna().sub(1).abs().max() < 0.03,
        f"max={((adj / adj.shift()).dropna().sub(1).abs().max()):.4f}")
    # PIT: filed ≤ t だけ
    D = f[f["ticker"] == "DDD"]
    A = pit_value(D, TAG_ASSETS, [d0("2020-03-31"), d0("2020-07-31"), d0("2020-12-31"), d0("2021-01-31"), d0("2021-03-31")], annual=True)["DDD"]
    chk("pit(FY・Assets): 2020-03→100, 2020-07→100, 2020-12→101(10-K/A), 2021-01→101(2020 年次は未提出), 2021-03→120",
        A.tolist() == [100.0, 100.0, 101.0, 101.0, 120.0], str(A.tolist()))
    A2 = pit_value(D, TAG_ASSETS, [d0("2020-08-31"), d0("2020-09-10")], annual=False)["DDD"]
    chk("pit(ストック・10-Q も可): 2020-08-31→110(Q2 end 2020-06-30)、2020-09-10→110", A2.tolist() == [110.0, 110.0], str(A2.tolist()))
    chk("filed > t の行は使わない（2021-01-31 に 120 が出ない）", A.iloc[3] != 120.0)
    V, VE = pit_value(D, TAG_ASSETS, [d0("2021-03-31")], annual=True, with_end=True)
    P = prior_year(D, TAG_ASSETS, [d0("2021-03-31")], VE, annual=True)["DDD"]
    chk("prior_year: 2021-03 の現在値 120（end 2020-12-31）の 1 年前は 100（当初の報告）", P.iloc[0] == 100.0, str(P.tolist()))
    N = pit_value(D, TAG_NI, [d0("2021-03-31"), d0("2021-06-30")], annual=True)["DDD"]
    chk("annual: 期間 89 日の fp=FY 行は除く（NI=10）", N.tolist() == [10.0, 10.0], str(N.tolist()))
    N0 = pit_value(D, TAG_NI, [d0("2020-03-31")], annual=True)["DDD"]
    chk("タグの優先: 2020-03 時点は ProfitLoss(end 2019-12-31)=8 のみ", N0.tolist() == [8.0], str(N0.tolist()))
    N1 = pit_value(D, TAG_NI, [d0("2021-03-31")], annual=True)["DDD"]
    chk("end が新しい NetIncomeLoss(2020-12-31) が古い ProfitLoss(2019) より優先", N1.iloc[0] == 10.0)
    # 合成データ（smoke 用）で分割が検出されること
    fs = load_facts(True, np.random.default_rng(1))
    _, _, _, evs, _ = shares_at(fs, [d0("2023-12-31")])
    got = sorted((r.ticker, r.ratio) for r in evs.itertuples())
    chk("smoke 合成: 分割は S7=2・S11=4 の 2 件だけ", got == [("S11", 4.0), ("S7", 2.0)], str(got))
    print("ALL OK" if ok else "FAILED")
    return ok


def peek(tk="MMM"):
    f = load_facts(False, tickers=[tk])
    ds = [pd.Timestamp("2015-06-30"), pd.Timestamp("2022-12-30")]
    V, VE = pit_value(f, TAG_ASSETS, ds, annual=False, with_end=True)
    Va = pit_value(f, TAG_ASSETS, ds, annual=True)
    P = prior_year(f, TAG_ASSETS, ds, VE, annual=False)
    print(tk, "Assets の pit 値（読むだけ）")
    for t in ds:
        print(f"  t={t.date()}  最新(10-Q 含む)={V.loc[t, tk]:,.0f} (end {VE.loc[t, tk].date()})  年次={Va.loc[t, tk]:,.0f}  1年前={P.loc[t, tk]:,.0f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--peek", action="store_true")
    a = ap.parse_args()
    if a.selftest: sys.exit(0 if selftest() else 1)
    if a.peek: peek()
