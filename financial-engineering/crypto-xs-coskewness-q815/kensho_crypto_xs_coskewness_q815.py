# -*- coding: utf-8 -*-
"""Q815 暗号資産の永久先物で共歪度（BTC の 2 乗リターンとの共変動・60 日）の低い側買い・高い側売りは、コスト・資金調達後に残るか
【出典】Harvey & Siddique (2000) 条件付き歪度
【仮説】暗号資産の永久先物で共歪度（BTC の 2 乗リターンとの共変動・60 日）の低い側買い・高い側売りは、コスト・資金調達後に残るか（帰無: 合図に情報は無い）
【データ】作業層/大容量/crypto_xs/{klines,funding,metrics}/<SYM>.csv（Binance の USDT 建て永久先物・日足。date < 2024-07-01 だけ読む。klines_seal・funding_seal は読まない）
【定義】合図 = −E[e_i·e_m²]÷(σ_i·σ_m²)（60 日・平均を引いたリターン）。BTC 自身は除く。高い側（共歪度が低い）を買う
【測るもの】S68（Q739）と同じ枠: 毎週月曜に組み替え・判断は日曜までの日足・母集団は 30 日の売買代金の上位 30（株や金など暗号資産以外の先物は除く）・合図の高い側 6 本を買い低い側 6 本を売り（各 0.5÷6）・片道 0.10% × 入れ替えた名目・資金調達の受け払い込み・評価 2020-01-06〜2024-06・前後半の境 2022-04-01。コスト後の日次平均（bp）・NW t・前後半・年別・帰無 z と片側 p
【帰無】毎週、母集団の中で合図を並べ替える（B=500）。統計量はコスト・資金調達後の日次平均
【判定（事前固定・変更禁止）】支持（フォワード候補）: コスト後の日次平均 > 0 かつ NW t ≥ 2.0 かつ 前後半とも平均 > 0 かつ 帰無 z ≥ 2.0。棄却: 全期間の日次平均 ≤ 0 または 帰無 z < 1.0。それ以外: 未確定。
【多重比較】暗号資産の横断 10 本（Q807〜Q816）。支持が出たら 10 本の p を Holm で補正して解釈する
【捨てた案の数】この回は 20 案を一括で出した（taichi の指示・「1 回 3 案まで」の例外）。合図の定義・窓・しきい値は走らせる前にこの 1 通りに固定し、ほかは試していない
【知識の締め切り】設計 2026-11-24（Fable）。先行研究の検索 2026-11-24: 「cryptocurrency cross-section idiosyncratic volatility illiquidity skewness coskewness downside beta anomalies」→ 検索では暗号資産の共歪度の横断は見つからなかった。未確認（移植）
【委託の確かめ方】--smoke（合成データ）で経路だけ確認済み。本番は未実行。実行者は冒頭の計画を変えずに走らせる
【実装】下の「共通の土台」は同じ回の 10 本で同じ文面（合図の分岐を KEY で選ぶ）。実行: 作業層/大容量/venv_forward/bin/python kensho_crypto_xs_coskewness_q815.py [--B 500]
"""
QID, KEY, SEED = "Q815", "coskew", 20261939
TITLE = "暗号資産の永久先物で共歪度（BTC の 2 乗リターンとの共変動・60 日）の低い側買い・高い側売りは、コスト・資金調達後に残るか"
import argparse, json, os, sys, tempfile
import numpy as np, pandas as pd

# ============================================================ 共通の土台（第5弾・暗号資産の横断 lp5k）ここから
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))                 # ワークスペース
DATA = os.path.join(WS, "作業層", "大容量", "crypto_xs")
S68 = os.path.join(HERE, "..", "s68-crypto-xs-momentum-q739")
SEAL = pd.Timestamp("2024-07-01")            # 封印: date < 2024-07-01 だけ読む（klines_seal・funding_seal は読まない）
FIRST_REB = pd.Timestamp("2020-01-06"); SPLIT = pd.Timestamp("2022-04-01")
TOPN, NSIDE, WINDOW = 30, 6, 30              # S68 と同じ: 30 日の売買代金の上位 30・片側 6
COST = 0.0010                                # 片道 0.10%（手数料 0.05 + 滑り 0.05）× 入れ替えた名目（S68 と同じ）
TRADFI0 = {"XAUUSDT", "XAGUSDT", "EURUSDT", "TSLAUSDT", "AAPLUSDT", "NVDAUSDT", "COINUSDT", "MSTRUSDT", "CRCLUSDT", "HOODUSDT", "INTCUSDT", "AMZNUSDT", "GOOGLUSDT", "METAUSDT", "QQQUSDT", "SPYUSDT"}


def load_panel(smoke, rng):
    """日次の表（終値 C・始値 O・高値 H・出来高 V・資金調達 F・建玉金額 OI）。smoke=True は合成データ（経路確認だけ）"""
    dates = pd.date_range("2019-09-01", SEAL - pd.Timedelta(days=1), freq="D"); n = len(dates)
    if smoke:
        names = ["BTCUSDT"] + [f"S{i:02d}USDT" for i in range(39)]; m = rng.normal(0, 0.03, n)
        C, O, H, V, F, OI = {}, {}, {}, {}, {}, {}
        for i, s in enumerate(names):
            r = (m if i == 0 else 0.8 * m + rng.standard_t(4, n) * 0.03); c = 100 * np.exp(np.cumsum(r)); start = 0 if i < 25 else int(rng.integers(0, n // 2))
            c[:start] = np.nan; C[s] = c; O[s] = np.r_[c[0], c[:-1]]; H[s] = c * (1 + np.abs(rng.normal(0, 0.01, n)))
            V[s] = np.where(np.isnan(c), np.nan, np.exp(rng.normal(10 + 0.1 * i, 1, n))); F[s] = np.where(np.isnan(c), np.nan, rng.normal(1e-4, 3e-4, n))
            OI[s] = np.where(np.isnan(c), np.nan, np.exp(np.cumsum(rng.normal(0, 0.05, n)) + 15))
        mk = lambda d: pd.DataFrame(d, index=dates)
        return dates, mk(C), mk(O), mk(H), mk(V), mk(F), mk(OI)
    tradfi = set(TRADFI0); fp = os.path.join(S68, "tradfi_symbols_20261116.txt")
    if os.path.exists(fp): tradfi |= set(open(fp).read().split())
    C, O, H, V, F, OI = {}, {}, {}, {}, {}, {}
    for fn in sorted(os.listdir(os.path.join(DATA, "klines"))):
        s = fn[:-4]
        if s in tradfi or not s.endswith("USDT"): continue
        d = pd.read_csv(os.path.join(DATA, "klines", fn), parse_dates=["date"]); d = d[d["date"] < SEAL].set_index("date")
        if len(d) < 60: continue
        C[s] = d["close"]; O[s] = d["open"]; H[s] = d["high"]; V[s] = d["volume"]
        p = os.path.join(DATA, "funding", s + ".csv")
        if os.path.exists(p):
            f = pd.read_csv(p, parse_dates=["time"]); f = f[f["time"] < SEAL]; F[s] = f.groupby(f["time"].dt.normalize())["rate"].sum()
        p = os.path.join(DATA, "metrics", s + ".csv")
        if os.path.exists(p):
            q = pd.read_csv(p, parse_dates=["date"]); q = q[q["date"] < SEAL].set_index("date"); OI[s] = q["oi_value"]
    C = pd.DataFrame(C).reindex(dates); cols = C.columns; mk = lambda d: pd.DataFrame(d).reindex(dates).reindex(columns=cols)
    assert C.index.max() < SEAL
    return dates, C, mk(O), mk(H), mk(V), mk(F), mk(OI)


def nw_t(x, lag=10):
    x = np.asarray(x, float); n = len(x)
    if n < lag + 5: return float("nan")
    m = x.mean(); e = x - m; s = e @ e / n
    for k in range(1, lag + 1): s += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(m / np.sqrt(s / n)) if s > 0 else float("nan")


def _beta(y, x):
    ok = np.isfinite(y) & np.isfinite(x)
    if ok.sum() < 10 or np.var(x[ok]) == 0: return np.nan, None
    xx = x[ok] - x[ok].mean(); b = float(xx @ (y[ok] - y[ok].mean()) / (xx @ xx)); res = (y[ok] - y[ok].mean()) - b * xx
    return b, res


def signal(key, t, U, P):
    """判断は t-1（日曜）までの日足だけ。返り値は「高い側を買う」向きにそろえた合図（NaN は対象外）"""
    CC, Cn, Hn, DV, Fn, OI, btc = P["CC"], P["C"], P["H"], P["DV"], P["F"], P["OI"], P["btc"]
    nU = len(U); out = np.full(nU, np.nan)
    if key in ("ivol", "downbeta", "coskew"):
        win = 28 if key == "ivol" else 60; m = CC[t - win:t, btc]
        for k, j in enumerate(U):
            if j == btc: continue
            y = CC[t - win:t, j]
            if np.isfinite(y).sum() < int(win * 0.7): continue
            if key == "ivol":
                b, res = _beta(y, m); out[k] = np.nan if res is None else -res.std(ddof=1)
            elif key == "downbeta":
                b, _ = _beta(y, m); dn = m < 0; bd, _ = _beta(y[dn], m[dn]); out[k] = bd - b if np.isfinite(b) and np.isfinite(bd) else np.nan
            else:
                ok = np.isfinite(y) & np.isfinite(m); ei = y[ok] - y[ok].mean(); em = m[ok] - m[ok].mean(); den = ei.std() * em.var()
                out[k] = -float((ei * em ** 2).mean() / den) if den > 0 else np.nan
    elif key == "amihud":
        x = np.abs(CC[t - 28:t][:, U]) / DV[t - 28:t][:, U]; x[~np.isfinite(x)] = np.nan
        out = np.where(np.isfinite(x).sum(0) >= 20, np.nanmean(np.where(np.isfinite(x), x, np.nan), axis=0), np.nan)
    elif key == "skew":
        R = CC[t - 28:t][:, U]
        for k in range(nU):
            r = R[:, k][np.isfinite(R[:, k])]
            if len(r) >= 20 and r.std() > 0: out[k] = -float(((r - r.mean()) ** 3).mean() / r.std() ** 3)
    elif key == "nearhigh":
        Hw = Hn[t - 90:t][:, U]; ok = np.isfinite(Hw).sum(0) >= 60
        out = np.where(ok, Cn[t - 1, U] / np.nanmax(np.where(np.isfinite(Hw), Hw, -np.inf), axis=0), np.nan)
    elif key == "volshock":
        a = DV[t - 7:t][:, U]; b = DV[t - 35:t - 7][:, U]; ok = (np.isfinite(a).sum(0) == 7) & (np.isfinite(b).sum(0) >= 20)
        with np.errstate(all="ignore"): out = np.where(ok, np.nanmean(a, 0) / np.nanmean(b, 0), np.nan)
    elif key == "oichg":
        a, b = OI[t - 1, U], OI[t - 8, U]; out = np.where(np.isfinite(a) & np.isfinite(b) & (b > 0), -(a / b - 1), np.nan)
    elif key == "fundchg":
        a = Fn[t - 7:t][:, U]; b = Fn[t - 35:t - 7][:, U]; ok = (np.isfinite(a).sum(0) >= 5) & (np.isfinite(b).sum(0) >= 20)
        with np.errstate(all="ignore"): out = np.where(ok, -(np.nanmean(a, 0) - np.nanmean(b, 0)), np.nan)
    elif key == "fip":
        R = CC[t - 28:t][:, U]; ok = np.isfinite(R).sum(0) >= 20; ret = np.nanprod(1 + np.nan_to_num(R), axis=0) - 1
        with np.errstate(all="ignore"): idv = np.sign(ret) * (np.nanmean(R < 0, 0) - np.nanmean(R > 0, 0))
        idv = np.where(ok, idv, np.nan); med = np.nanmedian(idv); out = np.where(ok & (idv <= med), ret, np.nan)
    else:
        raise ValueError(key)
    return np.asarray(out, float)


def build_weeks(key, dates, P):
    weeks = []
    for D in [d for d in dates if d >= FIRST_REB and d.dayofweek == 0 and d + pd.Timedelta(days=6) <= dates[-1]]:
        t = dates.get_loc(D); w = slice(t - WINDOW, t); full = P["valid"][w].all(axis=0) & np.isfinite(P["DV"][w]).all(axis=0)
        if full.sum() < 2 * NSIDE: continue
        adv = np.where(full, np.nan_to_num(P["DV"][w]).mean(axis=0), -np.inf); U = np.argsort(-adv)[:min(TOPN, int(full.sum()))]
        sg = signal(key, t, U, P); ok = np.isfinite(sg)
        if ok.sum() < 2 * NSIDE: continue
        weeks.append((D, t, U[ok], sg[ok]))
    return weeks


def run_pnl(weeks, P, names, perm_rng=None):
    N = P["C"].shape[1]; prev = np.zeros(N); rows = []
    for D, t, U, sg in weeks:
        s = perm_rng.permutation(sg) if perm_rng is not None else sg
        order = np.lexsort((names[U], s)); w = np.zeros(N); w[U[order[-NSIDE:]]] = 0.5 / NSIDE; w[U[order[:NSIDE]]] = -0.5 / NSIDE   # 合図の高い側を買い・低い側を売り
        prev_eff = np.where(P["valid"][t - 1], prev, 0.0); cost = COST * np.abs(w - prev_eff).sum()
        g = P["RET"][t:t + 7] @ w; f = -(P["FUND"][t:t + 7] @ w); c = np.zeros(len(g)); c[0] = cost
        rows.append(np.c_[g, f, c]); prev = w
    a = np.vstack(rows); idx = np.concatenate([P["dates"][t:t + 7] for _, t, _, _ in weeks])
    df = pd.DataFrame(a, index=pd.DatetimeIndex(idx), columns=["gross", "fund", "cost"]); df["net"] = df["gross"] + df["fund"] - df["cost"]
    return df


def stats(x):
    h1, h2 = x[x.index < SPLIT], x[x.index >= SPLIT]; bp = lambda v: float(v * 1e4)
    return dict(mean_bp=bp(x.mean()), NW_t=nw_t(x), n_days=int(len(x)), sharpe_ann=float(x.mean() / x.std(ddof=1) * np.sqrt(365)) if x.std() > 0 else float("nan"),
                first_half=dict(mean_bp=bp(h1.mean()) if len(h1) else float("nan"), NW_t=nw_t(h1), n=int(len(h1))), second_half=dict(mean_bp=bp(h2.mean()) if len(h2) else float("nan"), NW_t=nw_t(h2), n=int(len(h2))),
                by_year={str(y): bp(g.mean()) for y, g in x.groupby(x.index.year)})


def verdict(st, z):
    """事前固定・変更禁止（README と同じ文）"""
    a, b = st["first_half"]["mean_bp"], st["second_half"]["mean_bp"]
    if st["mean_bp"] <= 0 or not np.isfinite(z) or z < 1.0: return "棄却"
    if st["NW_t"] >= 2.0 and a > 0 and b > 0 and z >= 2.0: return "支持（フォワード候補）"
    return "未確定"
# ============================================================ 共通の土台（lp5k）ここまで


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=500); ap.add_argument("--seed", type=int, default=SEED); a = ap.parse_args()
    rng = np.random.default_rng(a.seed); dates, C, O, H, V, F, OI = load_panel(a.smoke, rng); names = C.columns.values.astype(str)
    Cn, On = C.values, O.values; valid = np.isfinite(Cn); CC = np.full_like(Cn, np.nan); CC[1:] = Cn[1:] / Cn[:-1] - 1
    RET = np.where((dates.dayofweek == 0)[:, None], Cn / On - 1, CC); RET = np.nan_to_num(RET); RET[~valid] = 0.0     # 月曜は始値→終値（S68 と同じ）
    P = dict(dates=dates, C=Cn, H=H.values, DV=V.values * Cn, F=F.values, OI=OI.values, CC=CC, RET=RET, FUND=np.nan_to_num(F.values) * valid, valid=valid, btc=int(np.where(names == "BTCUSDT")[0][0]))
    weeks = build_weeks(KEY, dates, P)
    if len(weeks) < 20: raise SystemExit(f"週が足りない: {len(weeks)}")
    df = run_pnl(weeks, P, names); st = stats(df["net"]); obs = df["net"].mean()
    null = np.array([run_pnl(weeks, P, names, perm_rng=rng)["net"].mean() for _ in range(a.B)])     # 帰無: 毎週、母集団の中で合図を並べ替える
    z = float((obs - null.mean()) / null.std(ddof=1)) if null.std() > 0 else float("nan"); p = float((1 + (null >= obs).sum()) / (1 + len(null)))
    res = dict(qid=QID, key=KEY, title=TITLE, smoke=bool(a.smoke), B=a.B, seed=a.seed, n_weeks=len(weeks), period=[str(df.index.min().date()), str(df.index.max().date())], seal=str(SEAL.date()),
               net=st, gross_mean_bp=float(df["gross"].mean() * 1e4), fund_mean_bp=float(df["fund"].mean() * 1e4), cost_mean_bp=float(df["cost"].mean() * 1e4),
               null=dict(kind="週ごとに母集団内で合図を並べ替え", mean_bp=float(null.mean() * 1e4), sd_bp=float(null.std(ddof=1) * 1e4), z=z, p_one_sided=p),
               multiple_testing="第5弾の暗号資産の横断は 10 本（Q807〜Q816）。支持が出たら 10 本の p を Holm で補正して解釈する（実行者）",
               machine_verdict=verdict(st, z), note="machine_verdict は機械判定。解釈は実行者（/lab）")
    out = tempfile.mkdtemp(prefix="smoke_" + QID + "_") if a.smoke else os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, f"result_{QID.lower()}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); df.to_csv(os.path.join(out, f"daily_{QID.lower()}.csv"))
    print(json.dumps({k: res[k] for k in ("qid", "smoke", "n_weeks", "machine_verdict")}, ensure_ascii=False), "→", out)


if __name__ == "__main__":
    main()
