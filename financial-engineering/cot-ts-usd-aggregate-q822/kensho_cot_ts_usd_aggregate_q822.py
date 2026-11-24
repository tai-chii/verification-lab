# -*- coding: utf-8 -*-
"""Q822 CFTC の通貨先物 7 本を束ねた投機筋のドル持ち高の 156 週 z が極端なとき、ドルの逆に張る（FX 7 本）と、コスト後に残るか
【出典】Q593（銘柄ごとの横断・棄却）の「ドル全体に束ねる」版／dollar-factor-momentum
【仮説】CFTC の通貨先物 7 本を束ねた投機筋のドル持ち高の 156 週 z が極端なとき、ドルの逆に張る（FX 7 本）と、コスト後に残るか（帰無: 合図に情報は無い）
【データ】作業層/大容量/cot/cot_legacy.parquet（CFTC の建玉報告 Legacy・週次・2008〜。2024-06-15 より前だけ）＋ fe_core.load_d1 の日足（MT5 の 17 銘柄・封印 2024-07-01 の前だけ）
【定義】ドル持ち高 = −(7 通貨の投機筋ネット÷建玉の平均)。z = 156 週。7 通貨の先物の持ち高 = +clip(z, ±2)÷2（ドル買いが混めば外貨買い）
【測るもの】Q593 と同じ対応表（17 銘柄）と約定の決まり: 報告日（火曜）+6 日以降の最初の営業日の終値で持ち替え（公表は金曜）。銘柄ごとに年率 10% にそろえて銘柄数で割る・片道コストは段階 1 の仮置き（FX 1bp・指数 2〜3bp・金属 2〜8bp・エネルギー 5〜10bp）・スワップなし・評価 2012-01〜2024-06・前後半の境 2017-01-01。コスト後の日次平均（bp）・NW t・前後半・年別・帰無 z と片側 p
【帰無】合図の週を循環シフト（26 週以上・B=500）。統計量はコスト後の日次平均
【判定（事前固定・変更禁止）】支持（フォワード候補）: コスト後の日次平均 > 0 かつ NW t ≥ 2.0 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 2.0。棄却: 全期間の日次平均 ≤ 0 または 帰無 z < 1.0。それ以外: 未確定。
【多重比較】CFTC 建玉 10 本（Q817〜Q826）。支持が出たら 10 本の p を Holm で補正して解釈する
【捨てた案の数】この回は 20 案を一括で出した（taichi の指示・「1 回 3 案まで」の例外）。合図の定義・窓・しきい値は走らせる前にこの 1 通りに固定し、ほかは試していない
【知識の締め切り】設計 2026-11-24（Fable）。先行研究の検索 2026-11-24: 「COT commercial hedgers small traders non-reportable positions extreme predict futures returns time series」→ 検索では通貨先物を束ねたドル持ち高の検証は見つからなかった（証券会社の解説だけ・根拠にしない）。未確認
【委託の確かめ方】--smoke（合成データ）で経路だけ確認済み。本番は未実行。実行者は冒頭の計画を変えずに走らせる
【実装】下の「共通の土台」は同じ回の 10 本で同じ文面（合図の分岐を KEY で選ぶ）。実行: 作業層/大容量/venv_forward/bin/python kensho_cot_ts_usd_aggregate_q822.py [--B 500]
"""
QID, KEY, SEED = "Q822", "usdagg", 20261946
TITLE = "CFTC の通貨先物 7 本を束ねた投機筋のドル持ち高の 156 週 z が極端なとき、ドルの逆に張る（FX 7 本）と、コスト後に残るか"
import argparse, json, os, sys, tempfile
import numpy as np, pandas as pd

# ============================================================ 共通の土台（第5弾・CFTC 建玉の時系列 lp5t）ここから
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))                 # ワークスペース
COT = os.path.join(WS, "作業層", "大容量", "cot", "cot_legacy.parquet")
# Q593 と同じ対応（MT5 の 17 銘柄・(CFTC コード, 先物の向き→銘柄の向き)）
MAP = {"EURUSD": ("099741", 1), "GBPUSD": ("096742", 1), "AUDUSD": ("232741", 1), "NZDUSD": ("112741", 1), "USDJPY": ("097741", -1), "USDCHF": ("092741", -1), "USDCAD": ("090741", -1),
       "US500": ("13874A", 1), "USTECH": ("209742", 1), "US30": ("124603", 1), "JPN225": ("240741", 1), "XAUUSD": ("088691", 1), "XAGUSD": ("084691", 1), "XPTUSD": ("076651", 1), "XPDUSD": ("075651", 1), "WTI": ("067651", 1), "NATGAS": ("023651", 1)}
FX7 = list(MAP)[:7]
EXTRA = {"VIX": "1170E1", "TNOTE": "043602"}     # 合図にだけ使う建玉（価格は使わない）
# 段階 1 の片道コスト（相対・仮置き。スワップは入れない。支持が出たら Q593 の実スワップ・実コストの表で確かめ直す）
COST1 = {**{s: 1e-4 for s in FX7}, "US500": 2e-4, "USTECH": 2e-4, "US30": 2e-4, "JPN225": 3e-4, "XAUUSD": 2e-4, "XAGUSD": 4e-4, "XPTUSD": 6e-4, "XPDUSD": 8e-4, "WTI": 5e-4, "NATGAS": 10e-4}
COT_CUT = pd.Timestamp("2024-06-15")             # 封印（2024-07-01〜）の前に使う日が収まるように切る（Q593 と同じ）
EVAL, SPLIT = pd.Timestamp("2012-01-01"), pd.Timestamp("2017-01-01"); WIN, MINW = 156, 104
TARGET_VOL = 0.10                                # 銘柄ごとに年率 10% にそろえ、銘柄数で割る


def load_all(smoke, rng):
    """返り値: 週次の建玉の表（項目→週×名前）と日次の終値の表（銘柄の向き）。smoke=True は合成データ"""
    cols = list(MAP)
    if smoke:
        wk = pd.date_range("2008-01-08", "2024-06-11", freq="7D"); idx = pd.bdate_range("2008-01-01", "2024-06-28"); F = {k: {} for k in ("oi", "nc_l", "nc_s", "c_l", "c_s")}
        for s in cols + list(EXTRA):
            oi = np.exp(np.cumsum(rng.normal(0, 0.03, len(wk))) + 12); a = np.cumsum(rng.normal(0, 0.03, len(wk))); a = np.tanh(a - a.mean()) * 0.3; b = rng.normal(0, 0.02, len(wk))
            F["oi"][s] = oi; F["nc_l"][s] = oi * (0.3 + a / 2); F["nc_s"][s] = oi * (0.3 - a / 2); F["c_l"][s] = oi * (0.4 - a / 2 + b); F["c_s"][s] = oi * (0.4 + a / 2 - b)
        PX = pd.DataFrame({s: 100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx)))) for s in cols}, index=idx)
        return {k: pd.DataFrame(v, index=wk) for k, v in F.items()}, PX
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
    from fe_core import load_d1                     # 封印（time < 2024-07-01）は fe_core の既定
    d = pd.read_parquet(COT); codes = {v[0]: k for k, v in MAP.items()}; codes.update({v: k for k, v in EXTRA.items()})
    d = d[d["code"].isin(codes) & (d["date"] < COT_CUT)].copy(); d["sym"] = d["code"].map(codes); d = d.drop_duplicates(["date", "sym"], keep="last")
    F = {k: d.pivot(index="date", columns="sym", values=k).sort_index().astype(float) for k in ("oi", "nc_l", "nc_s", "c_l", "c_s")}
    px = {s: load_d1(s).assign(d=lambda x: pd.to_datetime(x["time"]).dt.tz_localize(None).dt.normalize()).groupby("d")["close"].last() for s in cols}
    PX = pd.DataFrame(px).sort_index(); PX = PX[PX.index < pd.Timestamp("2024-07-01")]
    return F, PX


def zroll(x): return (x - x.rolling(WIN, min_periods=MINW).mean()) / x.rolling(WIN, min_periods=MINW).std()
def clip2(z): return z.clip(-2, 2) / 2


def signal(key, F, LW):
    """週次の持ち高（先物の向き・−1〜+1・NaN は 0 扱い）。LW = 報告日（火曜）+5 日までに確定した終値の対数（先物の向き）。週 i の行は報告日 i の建玉と、公表（金曜）までの価格だけで作る"""
    cols = list(MAP); oi = F["oi"]; spec = ((F["nc_l"] - F["nc_s"]) / oi); comm = ((F["c_l"] - F["c_s"]) / oi)
    mom = lambda k: (LW - LW.shift(k))
    if key == "small":
        S = -clip2(zroll(-(spec + comm)[cols]))
    elif key == "comm":
        pr = comm[cols].rolling(WIN, min_periods=MINW).apply(lambda v: (v[-1] >= v).mean(), raw=True); S = (pr >= 0.9).astype(float) - (pr <= 0.1).astype(float); S[pr.isna()] = np.nan
    elif key == "oigate":
        S = np.sign(mom(13)) * np.sign(oi[cols] / oi[cols].shift(13) - 1)
    elif key == "diverge":
        m = np.sign(mom(13)); ds = np.sign(spec[cols].diff(13)); S = (-m).where(m * ds < 0, 0.0); S[m.isna() | ds.isna()] = np.nan
    elif key == "grossls":
        m = np.sign(mom(4)); dl = (F["nc_l"] / oi)[cols].diff(4); ds = (F["nc_s"] / oi)[cols].diff(4); z0 = dl * 0
        S = z0.copy(); S[(m > 0) & (dl > np.maximum(-ds, z0))] = 1.0; S[(m > 0) & (-ds > np.maximum(dl, z0))] = -1.0; S[(m < 0) & (ds > np.maximum(-dl, z0))] = -1.0; S[(m < 0) & (-dl > np.maximum(ds, z0))] = 1.0
        S[m.isna() | dl.isna() | ds.isna()] = np.nan
    elif key == "usdagg":
        z = clip2(zroll(-spec[FX7].mean(axis=1, skipna=False))); S = pd.DataFrame(0.0, index=oi.index, columns=cols)
        for s in FX7: S[s] = z
    elif key == "vix":
        z = clip2(zroll(spec["VIX"])); S = pd.DataFrame(0.0, index=oi.index, columns=cols); S["US500"] = z; S["USTECH"] = z
    elif key == "tnote":
        z = clip2(zroll(spec["TNOTE"].diff(13))); S = pd.DataFrame(0.0, index=oi.index, columns=cols); S["XAUUSD"] = z; S["USDJPY"] = z   # USDJPY の列は円先物の向き（＋＝円買い）
    elif key == "oispike":
        ev = zroll(oi[cols].pct_change(fill_method=None)) > 2; S = (-np.sign(mom(4))).where(ev).ffill(limit=3).fillna(0.0)
    elif key == "flip":
        sg = np.sign(spec[cols]); fl = (sg != sg.shift(1)) & sg.shift(1).notna() & (sg != 0); S = sg.where(fl).ffill(limit=12).fillna(0.0)
    else:
        raise ValueError(key)
    return S.reindex(columns=cols).astype(float)


def to_daily(S, PX, shift=0):
    """週の持ち高 → 日次のウェイト（銘柄の向き）。適用は 報告日+6 日以降の最初の営業日の終値（Q593 と同じ）。shift は帰無用（週を循環）"""
    cols = list(MAP); idx = PX.index; mult = np.array([MAP[s][1] for s in cols], float); vol = PX.pct_change(fill_method=None).rolling(60, min_periods=40).std().to_numpy() * np.sqrt(252)
    arr = np.nan_to_num(S.to_numpy()); n = len(S); ap = idx.searchsorted(S.index + pd.Timedelta(days=6)); W = np.zeros((len(idx), len(cols))); cur = np.zeros(len(cols)); k = 0
    for t in range(len(idx)):
        while k < n and ap[k] == t:
            v = vol[t]; sc = np.where(np.isfinite(v) & (v > 0), TARGET_VOL / np.where(v > 0, v, 1.0), 0.0); cur = arr[(k - shift) % n] * mult * np.minimum(sc, 5.0) / len(cols); k += 1
        W[t] = cur                                 # t の終値で持ち替え → t+1 の損益から
    return W


def pnl(W, PX):
    R = np.nan_to_num(PX.pct_change(fill_method=None).to_numpy()); c = np.array([COST1[s] for s in MAP]); Wl = np.vstack([np.zeros((1, W.shape[1])), W[:-1]])
    gross = (Wl * R).sum(1); cost = (np.abs(np.diff(np.vstack([np.zeros((1, W.shape[1])), W]), axis=0)) * c).sum(1); cost = np.r_[0.0, cost[:-1]]
    return pd.DataFrame(dict(gross=gross, cost=cost, net=gross - cost), index=PX.index)


def nw_t(x, lag=21):
    x = np.asarray(x, float); n = len(x)
    if n < lag + 5: return float("nan")
    m = x.mean(); e = x - m; s = e @ e / n
    for k in range(1, lag + 1): s += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(m / np.sqrt(s / n)) if s > 0 else float("nan")


def stats(x):
    x = x[x.index >= EVAL]; h1, h2 = x[x.index < SPLIT], x[x.index >= SPLIT]; bp = lambda v: float(v * 1e4)
    return dict(mean_bp=bp(x.mean()), NW_t=nw_t(x), n_days=int(len(x)), sharpe_ann=float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std() > 0 else float("nan"),
                first_half=dict(mean_bp=bp(h1.mean()), NW_t=nw_t(h1), n=int(len(h1))), second_half=dict(mean_bp=bp(h2.mean()), NW_t=nw_t(h2), n=int(len(h2))),
                by_year={str(y): bp(g.mean()) for y, g in x.groupby(x.index.year)})


def verdict(st, z):
    """事前固定・変更禁止（README と同じ文）"""
    a, b = st["first_half"]["mean_bp"], st["second_half"]["mean_bp"]
    if st["mean_bp"] <= 0 or not np.isfinite(z) or z < 1.0: return "棄却"
    if st["NW_t"] >= 2.0 and a > 0 and b > 0 and z >= 2.0: return "支持（フォワード候補）"
    return "未確定"
# ============================================================ 共通の土台（lp5t）ここまで


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=500); ap.add_argument("--seed", type=int, default=SEED); a = ap.parse_args()
    rng = np.random.default_rng(a.seed); F, PX = load_all(a.smoke, rng); cols = list(MAP); mult = pd.Series({s: MAP[s][1] for s in cols})
    wk = F["oi"].index; LW = (np.log(PX.ffill()) * mult).reindex(PX.index.union(wk + pd.Timedelta(days=5))).ffill().reindex(wk + pd.Timedelta(days=5)); LW.index = wk   # 報告日+5 日（日曜）時点＝金曜の終値まで
    S = signal(KEY, F, LW[cols]); df = pnl(to_daily(S, PX), PX); st = stats(df["net"]); m = df.index >= EVAL; obs = df["net"][m].mean(); n = len(S)
    null = np.array([pnl(to_daily(S, PX, shift=int(rng.integers(26, n - 26))), PX)["net"][m].mean() for _ in range(a.B)])   # 帰無: 合図の週を循環シフト（26 週以上ずらす）
    z = float((obs - null.mean()) / null.std(ddof=1)) if null.std() > 0 else float("nan"); p = float((1 + (null >= obs).sum()) / (1 + len(null)))
    look = pnl(to_daily(S.shift(-1), PX), PX)["net"][m].mean()                                                              # 先読みの点検用（1 週先の合図。判定には使わない）
    act = (S.abs() > 0).mean().round(3).to_dict()
    res = dict(qid=QID, key=KEY, title=TITLE, smoke=bool(a.smoke), B=a.B, seed=a.seed, n_weeks=int(n), eval=[str(EVAL.date()), str(df.index.max().date())], split=str(SPLIT.date()),
               net=st, gross_mean_bp=float(df["gross"][m].mean() * 1e4), cost_mean_bp=float(df["cost"][m].mean() * 1e4), active_share_by_symbol=act,
               null=dict(kind="合図の週の循環シフト", mean_bp=float(null.mean() * 1e4), sd_bp=float(null.std(ddof=1) * 1e4), z=z, p_one_sided=p), lookahead_check_mean_bp=float(look * 1e4),
               cost_note="段階 1 の仮置きコスト・スワップなし。支持が出たら Q593 の実スワップ・実コストで確かめ直す",
               multiple_testing="第5弾の CFTC 建玉は 10 本（Q817〜Q826）。支持が出たら 10 本の p を Holm で補正して解釈する（実行者）",
               machine_verdict=verdict(st, z), note="machine_verdict は機械判定。解釈は実行者（/lab）")
    out = tempfile.mkdtemp(prefix="smoke_" + QID + "_") if a.smoke else os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, f"result_{QID.lower()}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); df[m].to_csv(os.path.join(out, f"daily_{QID.lower()}.csv"))
    print(json.dumps({k: res[k] for k in ("qid", "smoke", "n_weeks", "machine_verdict")}, ensure_ascii=False), "active", round(float((S.abs() > 0).to_numpy().mean()), 3), "→", out)


if __name__ == "__main__":
    main()
