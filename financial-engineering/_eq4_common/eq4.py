# -*- coding: utf-8 -*-
"""eq4 — 株式無料層 第4弾（Q787〜Q806・2026-11-24 Fable）の共通部品。

土台は 2 つをそのまま読む（書き換えない）:
- B = `jp-us-high-volume-premium-q578/kensho_high_volume_premium_q578.py`（月次 L/S・適格・コスト・帰無・統計）
- P = `us-sec-value-q696/sec_pit.py`（SEC 財務の判断時点読み・米国だけのドライバ run_us）
ここに置くのは「判定の規則・共通ドライバ・財務と価格の小さな部品」だけ。合図の定義は各案の kensho_*.py と 事前登録_q*.md にある。
判定の規則（verdict_both・verdict_us_fam10）は事前固定・変更禁止。
"""
import importlib.util, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FE = os.path.dirname(HERE)


def _load(name, *parts):
    sp = importlib.util.spec_from_file_location(name, os.path.join(FE, *parts))
    m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m)
    return m


B = _load("base578", "jp-us-high-volume-premium-q578", "kensho_high_volume_premium_q578.py")
P = _load("sec_pit", "us-sec-value-q696", "sec_pit.py")


# ---- 判定の規則（事前固定・変更禁止）---------------------------------------------------------
def verdict_both(per):
    """事前固定（第3弾 Q700〜Q707 と同じ規則・第4弾の日米 10 本 Q797〜Q806 共通・変更禁止）。両国とも 全期間 NW t≥2 かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ 2 国の Holm 調整後 p<0.05 かつ σ0.25%/日 換算の最大 DD > −6% → 支持。両国とも NW t<1 → 棄却。片方の国だけ通る → 未確定（片方: 国名）。それ以外 → 未確定。"""
    adj = B.holm({m: r["p_one"] for m, r in per.items()})
    for m, r in per.items(): r["p_holm"] = adj[m]
    ok = [m for m, r in per.items() if r["t_nw"] >= 2 and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["p_holm"] < 0.05 and r["maxdd_s025"] > -0.06]
    if len(ok) == len(per) and len(per) >= 2: return "支持"
    if all(r["t_nw"] < 1 for r in per.values()): return "棄却"
    if ok: return "未確定（片方: " + ",".join(ok) + "）"
    return "未確定"


T_FAM = 2.58      # 片側 p<0.005 ＝ 族 10 本の Bonferroni（0.05÷10）


def verdict_us_fam10(per):
    """事前固定（第4弾の米国 SEC 10 本 Q787〜Q796 共通・変更禁止）。日本は無料層の財務が 2 年分しか無いので「支持」は出さない。米国で 全期間 NW t≥2.58（片側 p<0.005＝族 10 本の Bonferroni）かつ 前後半とも年単位 t≥2 かつ 帰無 z≥2 かつ σ0.25%/日 換算の最大 DD > −6% → 米国で通過（日本の追試待ち）。米国で NW t<1 → 棄却。それ以外 → 未確定。"""
    r = per["us"]; r["p_holm"] = min(1.0, 10 * r["p_one"]) if r["p_one"] == r["p_one"] else np.nan   # 族 10 本の Bonferroni 調整後 p
    if r["t_nw"] >= T_FAM and r["h1_ty"] >= 2 and r["h2_ty"] >= 2 and r["null"]["z"] >= 2 and r["maxdd_s025"] > -0.06: return "米国で通過（日本の追試待ち）"
    if r["t_nw"] < 1: return "棄却"
    return "未確定"


# ---- 小さな部品 ------------------------------------------------------------------------------
def cached(fn):
    """sig_at(t, elig) の結果を判断日ごとに覚える（帰無の循環シフトで同じ月を何度も計算しないため。適格銘柄は判断日ごとに固定）。"""
    memo = {}

    def g(t, el):
        if t not in memo: memo[t] = fn(t, el)
        return memo[t]
    return g


def frame_sig(S):
    """date × 銘柄 の表を sig_at(t, elig) にする（±inf は欠損）。"""
    S = S.replace([np.inf, -np.inf], np.nan)
    return lambda t, el: S.loc[t].reindex(el)


def _turn_mean(d):
    return float(d.groupby(d.index.to_period("M"))["turn"].first().mean()) if len(d) else None


def _stat(d):
    """日次の表 d（ls・mkt・turn・n）から土台の統計＋規程 C1 の量。空なら NaN。"""
    if not len(d):
        return dict(mean_bp=np.nan, t_nw=np.nan, n_days=0, h1_bp=np.nan, h1_t=np.nan, h2_bp=np.nan, h2_t=np.nan, alpha_bp=np.nan, beta=np.nan,
                    sharpe=np.nan, t_year=np.nan, h1_ty=np.nan, h2_ty=np.nan, maxdd_s025=np.nan, p_one=np.nan, turn_mean=None, n_months=0,
                    first_day=None, names_mean=None)
    d = d[d["ls"].notna().values]                                         # 土台の stats は ls の欠損を落とす。先に落として、日付の重複（月の境の日）があっても同じ並びで渡す
    st = B.add_c1(B.stats(d["ls"], d["mkt"]), d["ls"])
    st["turn_mean"] = _turn_mean(d); st["n_months"] = int(d.index.to_period("M").nunique())
    st["first_day"] = str(d.index.min().date()); st["names_mean"] = float(d["n"].mean())
    return st


def _sub(d):
    s = _stat(d)
    return {k: s[k] for k in ("mean_bp", "t_nw", "h1_ty", "h2_ty", "maxdd_s025", "beta", "turn_mean", "n_days")}


# ---- 価格と出来高だけの月次 L/S（日本・米国）の共通ドライバ -----------------------------------
def run_pv(qid, args, rng, make_sig, lookback=252, note="", min_names=None, verdict=verdict_both):
    """make_sig(mkt, C, V, R, months, args) -> sig_at か dict(main=sig_at, subs={名前: sig_at}, diag={})。
    適格・保有・コスト・帰無は土台 B（Q578）のまま。min_names を渡すと判断日の最低銘柄数（土台の既定 300）をその案だけ変える（事前登録に書いた案だけ）。"""
    if min_names is not None: B.MIN_NAMES = int(min_names)
    per, csvs, diag = {}, {}, {}
    for mkt in args.markets.split(","):
        cfg = B.CFG[mkt]; C, V = B.load_px(mkt, args.smoke, rng)
        R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        months = B.build_months(C, V, cfg, lookback)
        sg = make_sig(mkt, C, V, R, months, args)
        if not isinstance(sg, dict): sg = dict(main=sg)
        sig_at = cached(sg["main"])
        d = B.run_ls(C, R, sig_at, months, cfg["cost"]); st = _stat(d)
        st["null"] = (B.null_circ(C, R, sig_at, months, cfg["cost"], args.B, rng, d["ls"].mean()) if len(d) and args.B > 0
                      else dict(B=0, z=np.nan, p=np.nan))
        d0 = B.run_ls(C, R, sig_at, months, 0.0)
        st["sub_cost0_bp"] = 1e4 * d0["ls"].mean() if len(d0) else np.nan; st["sub_cost0_t"] = B.nw_t(d0["ls"]) if len(d0) else np.nan
        subs = {name: _sub(B.run_ls(C, R, cached(sa), months, cfg["cost"])) for name, sa in (sg.get("subs") or {}).items()}
        if subs: st["sub"] = subs
        if sg.get("diag"): diag[mkt] = sg["diag"]
        per[mkt] = st; csvs[f"daily_{mkt}"] = d
    return dict(qid=qid, per_market=per, verdict=verdict(per), rule=verdict.__doc__.strip(), note=note, diag=diag,
                min_names=int(B.MIN_NAMES)), csvs


# ---- 既にある日次 L−S の系列に月ごとの重みを掛ける案（Q799・Q800）の部品 -----------------------
def month_blocks(d):
    """土台 run_ls の日次の表を保有月のブロック番号に分ける。保有は「月の最初の営業日〜翌月の最初の営業日」で、境の日は 2 回出る
    （1 回目＝前の月の最後の日、2 回目＝次の月の最初の日）。1 行だけのブロックは前のブロックに付ける。"""
    idx = pd.DatetimeIndex(d.index); per = idx.to_period("M")
    first_of_dup = pd.Series(idx).duplicated(keep="last").values          # 重複の 1 回目
    code = np.array([p.ordinal for p in per]) - first_of_dup.astype(int)
    last_alone = (~first_of_dup) & (np.r_[code[1:] != code[:-1], True]) & (np.r_[True, code[1:] != code[:-1]])
    code = np.where(last_alone, code - 1, code)                           # 末尾の 1 行（最後の保有の最終日）は前のブロックへ
    return pd.Series(code, index=d.index)


def weighted_series(d, w_by_block, cost, mode="scale"):
    """d: 土台の日次の表（ls はコスト後・turn つき）。w_by_block: ブロック番号 → 重み（判断日までの情報で決めたもの）。
    mode="scale": 損益 = w×ls − 2×cost×|w − 前の w|（残る建玉の大きさ直しの分・初日に引く）。
    mode="onoff": w∈{0,1}。休む月は損益 0。入り直す月は建て直しの全額（2×cost×(1−turn) を足して合計 2×cost）、休みに入る月は手仕舞い 2×cost を初日に引く。"""
    blk = month_blocks(d); out = []; prev_w = None
    for b, g in d.groupby(blk.values, sort=True):
        w = w_by_block.get(b, np.nan)
        if w != w: continue                                               # 重みが決まらない月（履歴不足）は系列に入れない
        ls = g["ls"].astype(float).copy()
        if mode == "scale":
            ls = w * ls
            if prev_w is not None: ls.iloc[0] -= 2 * cost * abs(w - prev_w)
        else:
            if w == 0:
                ls = ls * 0.0
                if prev_w == 1: ls.iloc[0] -= 2 * cost
            elif prev_w == 0:
                ls.iloc[0] -= 2 * cost * max(0.0, 1.0 - float(g["turn"].iloc[0]))
        out.append(pd.DataFrame({"ls": ls, "mkt": g["mkt"], "turn": g["turn"], "n": g["n"], "w": w, "blk": b}))
        prev_w = w
    return pd.concat(out) if out else pd.DataFrame(columns=["ls", "mkt", "turn", "n", "w", "blk"])


def null_weight_shift(d, w_by_block, cost, mode, Bn, rng, obs_mean, min_shift=13):
    """帰無: 月ごとの重みの列を循環シフト（k∈[13, N−13]）。重みの分布は同じで、どの月に掛けるかだけを壊す。"""
    keys = sorted(k for k, v in w_by_block.items() if v == v); n = len(keys)
    if Bn <= 0 or n < 2 * min_shift + 2: return dict(B=0, z=np.nan, p=np.nan)
    vals = []
    for _ in range(Bn):
        k = int(rng.integers(min_shift, n - min_shift))
        wb = {keys[i]: w_by_block[keys[(i - k) % n]] for i in range(n)}
        vals.append(weighted_series(d, wb, cost, mode)["ls"].mean())
    vals = np.array(vals, float); sd = vals.std()
    return dict(B=Bn, null_mean_bp=1e4 * vals.mean(), null_sd_bp=1e4 * sd, z=(obs_mean - vals.mean()) / sd if sd > 0 else np.nan,
                p=float((vals >= obs_mean).mean()))


def base_momentum_daily(mkt, args, rng):
    """Q563 の横断モメンタム（12-1 か月・上下 10%・等金額）の日次の表。本番は Q563 の結果ファイルを読む（定義を写し直さない）。
    smoke は合成データに同じ形の合図（C[t−21]÷C[t−252]−1）を当てて作る。"""
    cfg = B.CFG[mkt]
    if args.smoke:
        C, V = B.load_px(mkt, True, rng); R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.5)
        M = C.shift(21) / C.shift(252) - 1
        return B.run_ls(C, R, frame_sig(M), B.build_months(C, V, cfg, 252), cfg["cost"]), cfg["cost"]
    p = os.path.join(FE, "jp-us-xs-momentum-q563", "results", f"daily_{mkt}_q563.csv")
    d = pd.read_csv(p, index_col=0, parse_dates=True)
    return d[d.index < B.SEAL], cfg["cost"]


def run_weighted(qid, args, rng, weight_fn, mode, note=""):
    """Q799・Q800 共通。weight_fn(d, blk) -> {ブロック番号: 重み}（判断日＝前のブロックの最後の日までの情報だけで決める）。"""
    per, csvs = {}, {}
    for mkt in args.markets.split(","):
        d, cost = base_momentum_daily(mkt, args, rng)
        blk = month_blocks(d); wb = weight_fn(d, blk)
        s = weighted_series(d, wb, cost, mode)
        nul = null_weight_shift(d, wb, cost, mode, args.B, rng, s["ls"].mean()) if len(s) else dict(B=0, z=np.nan, p=np.nan)   # 帰無は大きさをそろえる前の平均どうしで比べる（z は倍率に依らない）
        if mode == "scale" and len(s) and s["ls"].std() > 0:               # 比べやすいよう、全期間の σ を元の系列（同じ月）にそろえる（t・z・DD の判定には影響しない）
            k = float(d["ls"][blk.isin(set(s["blk"])).values].std() / s["ls"].std())
            s["ls"] = s["ls"] * k
            for key in ("null_mean_bp", "null_sd_bp"):
                if key in nul: nul[key] = nul[key] * k
        st = _stat(s)
        st["null"] = nul
        base_same = d[blk.isin(set(s["blk"])).values] if len(s) else d.iloc[:0]
        st["sub"] = dict(base_same_months=_sub(base_same))                  # 記述: 重みを掛ける前（同じ月）
        if len(s):
            w = s.groupby("blk")["w"].first(); st["w_mean"] = float(w.mean()); st["w_min"] = float(w.min()); st["w_max"] = float(w.max())
            st["share_months_off"] = float((w == 0).mean()) if mode == "onoff" else None
        per[mkt] = st; csvs[f"daily_{mkt}"] = s
    return dict(qid=qid, per_market=per, verdict=verdict_both(per), rule=verdict_both.__doc__.strip(), note=note), csvs


# ---- 価格の部品: 市場との共変動（直近 win 日・銘柄ごとに有効な日だけ）---------------------------
def market_ret(R):
    """等金額の市場リターン（その日に値がある全銘柄の平均）。"""
    return R.mean(axis=1).fillna(0.0)


def roll_moments(R, m, cond=None, win=252, at=None):
    """直近 win 日の窓で、銘柄 i の有効な日（cond があればその日だけ）の和から平均を作る。at（判断日の並び）を渡すとその行だけ返す（メモリの節約）。
    返り値 dict: n, Er, Em, Er2, Em2, Erm, Erm2（E は窓の中の有効な日の平均）。"""
    m = pd.Series(np.asarray(m, float), index=R.index).fillna(0.0)
    okf = R.notna().astype(float)
    if cond is not None: okf = okf.mul(pd.Series(np.asarray(cond, float), index=R.index), axis=0)
    X = R.fillna(0.0) * okf

    def rs(F):
        out = F.rolling(win, min_periods=1).sum()
        return out if at is None else out.loc[list(at)]
    n = rs(okf); n = n.where(n > 0)
    return dict(n=n, Er=rs(X) / n, Em=rs(okf.mul(m, axis=0)) / n, Er2=rs(X * X) / n, Em2=rs(okf.mul(m * m, axis=0)) / n,
                Erm=rs(X.mul(m, axis=0)) / n, Erm2=rs(X.mul(m * m, axis=0)) / n)


def beta_from(mo, minobs):
    cov = mo["Erm"] - mo["Er"] * mo["Em"]; var = mo["Em2"] - mo["Em"] ** 2
    return (cov / var.where(var > 0)).where(mo["n"] >= minobs)


# ---- SEC 財務（年次・判断時点）の部品 ---------------------------------------------------------
TAGS = dict(ni=P.TAG_NI, rev=P.TAG_REV, ocf=P.TAG_OCF, a=P.TAG_ASSETS, eq=P.TAG_EQ, oi=["OperatingIncomeLoss"], gp=["GrossProfit"],
            cogs=["CostOfGoodsAndServicesSold", "CostOfRevenue"], liab=["Liabilities"])
EXTRA_TAGS = TAGS["oi"] + TAGS["gp"] + TAGS["cogs"] + TAGS["liab"]


def same_fy(e1, e2, days=10):
    """2 つの end（date × 銘柄）が同じ会計年度（days 日以内）か。片方にしか無い銘柄・NaT は False。"""
    e1, e2 = e1.align(e2, join="outer")
    return (e1.apply(pd.to_datetime) - e2.apply(pd.to_datetime)).abs() <= pd.Timedelta(days=days)


class Fin:
    """年次（fp==FY・フローは期間 330〜400 日・ストックは 10-K の期末）の値を判断時点（filed ≤ t）で読む。Q696 の sec_pit をそのまま呼ぶ。"""

    def __init__(self, f, mes):
        self.f, self.mes, self._c = f, list(mes), {}

    def fy(self, k, lag=0):
        """(値, その end)。lag=0 は今の年次、lag=n は n 年前（1 つ新しい年次の end より 300〜430 日前の end のうち最新・当初の報告）。"""
        if (k, lag) not in self._c:
            if lag == 0:
                v, e = P.pit_value(self.f, TAGS[k], self.mes, annual=True, with_end=True)
            else:
                _, e0 = self.fy(k, lag - 1)
                v, e = P.prior_year(self.f, TAGS[k], self.mes, e0, annual=True, with_end=True)
            self._c[(k, lag)] = (v.astype(float), e.apply(pd.to_datetime))
        return self._c[(k, lag)]

    def val(self, k, lag=0, ref="a"):
        """値。ref（既定＝総資産）の同じ lag の年次と end が 10 日以内で一致するものだけ（会計年度のずれた組を作らない）。"""
        v, e = self.fy(k, lag)
        if ref is None or ref == k: return v
        _, er = self.fy(ref, lag)
        return v.where(same_fy(e, er).reindex(index=v.index, columns=v.columns, fill_value=False))


def ratio(num, den, positive_den=True):
    num, den = num.align(den, join="outer")
    if positive_den: den = den.where(den > 0)
    return (num / den).replace([np.inf, -np.inf], np.nan)


def d_roa(fin):
    """ROA（純利益÷総資産・同じ年度）の前年差。"""
    return ratio(fin.val("ni"), fin.val("a")) - ratio(fin.val("ni", 1), fin.val("a", 1))


def d_ato(fin):
    """資産回転率（売上÷総資産・同じ年度）の前年差。"""
    return ratio(fin.val("rev"), fin.val("a")) - ratio(fin.val("rev", 1), fin.val("a", 1))


def d_margin(fin):
    """営業利益率（営業利益÷売上・同じ年度）の前年差。"""
    pm = lambda k: ratio(fin.val("oi", k, ref="rev"), fin.val("rev", k, ref=None))
    return pm(0) - pm(1)


def d_leverage(fin):
    """負債比率（負債÷総資産・同じ年度）の前年差。負債は Liabilities タグ（今年と 1 年前の両方にあるとき）。無い銘柄は 総資産 − 株主資本 で両年とも代える（年の途中で数え方を変えない）。"""
    a0, a1 = fin.val("a"), fin.val("a", 1)
    tag = ratio(fin.val("liab"), a0) - ratio(fin.val("liab", 1), a1)
    alt = ratio(a0 - fin.val("eq"), a0) - ratio(a1 - fin.val("eq", 1), a1)
    tag, alt = tag.align(alt, join="outer")
    return tag.combine_first(alt)


def _synth_ext(df, rng):
    """smoke 用: sec_pit の合成データに、第4弾で足したタグ（営業利益・粗利益・売上原価・負債）の行を足す。"""
    rev = df[df["tag"] == "Revenues"]; a = df[(df["tag"] == "Assets") & (df["form"] != "10-K/A")]

    def clone(src, tag, mult):
        d = src.copy(); d["tag"] = tag; d["val"] = d["val"].values * mult; return d
    gm = rng.uniform(0.2, 0.6, len(rev))
    return pd.concat([df, clone(rev, "GrossProfit", gm), clone(rev, "CostOfGoodsAndServicesSold", 1 - gm),
                      clone(rev, "OperatingIncomeLoss", rng.normal(0.10, 0.05, len(rev))),
                      clone(a, "Liabilities", rng.uniform(0.3, 0.7, len(a)))], ignore_index=True)


def run_sec(qid, args, rng, make_signal, note="", start=None, split=None):
    """米国 SEC の 1 案を測る。make_signal(fin, mes, C) -> dict(main=表(date×銘柄) か sig_at, subs={...}, diag={...})。
    sec_pit.run_us（Q696〜Q699 と同じ適格・保有・コスト・帰無・期間 2010-07〜2024-06・境 2017-07）をそのまま呼ぶ。
    start・split は事前登録に書いた案だけが変える。記述として Q698（アクルーアル）の日次 L−S との相関と、Q698 に回帰した残りを足す（合否に使わない）。"""
    args.markets = "us"
    P.ALL_TAGS = list(dict.fromkeys(P.ALL_TAGS + EXTRA_TAGS))
    _orig = P._synth
    P._synth = lambda r, n=400: _synth_ext(_orig(r, n), r)
    if start is not None: P.START = pd.Timestamp(start)
    if split is not None: P.SPLIT_BOUNDARY = pd.Timestamp(split)

    def _mk(f, mes, C):
        sg = make_signal(Fin(f, mes), mes, C)
        wrap = lambda s: cached(s if callable(s) else P.frame_sig(s))
        return dict(main=wrap(sg["main"]), subs={k: wrap(v) for k, v in (sg.get("subs") or {}).items()},
                    diag=dict(sg.get("diag") or {}, n_tickers=int(f["ticker"].nunique())))
    res, csvs = P.run_us(B, args, rng, qid, _mk, verdict_us_fam10, note=note)
    res["family"] = "第4弾の米国 SEC 10 本（Q787〜Q796）。通過の線 NW t≥2.58＝族 10 本の Bonferroni"
    p698 = os.path.join(FE, "us-sec-accruals-q698", "results", "daily_us_q698.csv")
    d = csvs["daily_us"]
    if len(d) and os.path.exists(p698) and not args.smoke:
        q = pd.read_csv(p698, index_col=0, parse_dates=True)["ls"]
        j = pd.concat([d["ls"].groupby(level=0).mean(), q.groupby(level=0).mean()], axis=1, keys=["x", "q"]).dropna()
        if len(j) > 250 and j["q"].var() > 0:
            b = j["x"].cov(j["q"]) / j["q"].var(); resid = j["x"] - b * j["q"]
            res["sub_vs_q698"] = dict(corr=float(j["x"].corr(j["q"])), slope=float(b), resid_mean_bp=1e4 * float(resid.mean()),
                                      resid_t_nw=B.nw_t(resid), n_days=int(len(j)))
    return res, csvs


def main(qid, desc, run, here):
    args = B.parse_args(desc); rng = np.random.default_rng(args.seed)
    args.out = args.out or os.path.join(here, "results")
    res, csvs = run(args, rng); B.write_result(qid, res, csvs, args)
