# -*- coding: utf-8 -*-
"""
検証キュー Q569: 暗号資産の四半期先物の年率ベーシスが直近 365 日の 80 分位を超えた日に S23 を休むと、S23 の損益は上がるか
================================================================================

【出典】
- 計画（事前登録）: 無料の新しい源 2 案 第1弾（Opus 2026-10-29）。アイデア候補.md の該当行。taichi「まずは無料分で進めて」。
- Schmeling, Schrimpf & Todorov (2023) BIS Working Paper 1087「Crypto carry」: 先物と現物の差（キャリー）は年 60% に達することもあり、
  **高いキャリーは将来の暴落を予測する**（要旨）。予測の地平は要旨に書かれていない。
- 対照: Q551（S26）は永久先物の資金調達率（7 日平均）で同じ形のゲートを当て、休んだ日 +40.6 bp/日・帰無 z −2.48 で棄却（混んだ日はトレンドの最強の日）。
  → 本案は「四半期先物（満期まで 30〜90 日）の年率ベーシス」という、資金調達率より長い地平の混み具合で同じことが起きるか。
- 運用の決まり 2026-10-29: 合成の追加関門も記述で見る。

【仮説（測る前に固定）】
H1: S23 の保有日のうち、年率ベーシスが直近 365 日の 80 分位を超えた日を休む（S27 候補）と、S23 より Sharpe が上がり、最大下落は悪化せず、
    休んだ日の S23 の損益は負で、ゲートの位置は循環シフトの帰無より良い（z ≥ 2）。
H0: S26 と同じく、休んだ日はむしろ稼ぐ日（休んだ日の平均 > 0）。

【データ】
- ベーシス: Binance COIN-M（dapi）の BTCUSD・ETHUSD の連続足 CURRENT_QUARTER・NEXT_QUARTER と指数価格の日足（`_データ/raw/crypto_basis/<PAIR>_D1.csv`・fetch_binance_basis.py）。2020-06／07 から。
- S23 の価格: run_q529.py と同じ Binance 現物 H1（`--h1`・営業日の日足 21:00 UTC 区切り・次の 1 時間足の始値で執行・片道 BTC 2bp／ETH 7.5bp）。
- 評価期間: 2021-01-08〜2024-06-30（**2024-07-01 以降は封印**。開始は S26 と同じ＝365 日の分位が作れる最初の日）。前半 <2022-10-01・後半 ≥2022-10-01（記述）。

【定義（1 通りに固定）】
- 年率ベーシス b[d] = (F/I − 1) × 365 / 満期までの日数。F は CURRENT_QUARTER の終値（満期まで 30 日未満の日は NEXT_QUARTER）、I は指数価格の終値。d は UTC 日足、値の確定は d+1 日 00:00 UTC。
- ゲート: S23 の日足 t の `end` までに確定した最新の b を当て（merge_asof・backward）、その b が「t より前の 365 日（closed=left・min_periods 200）の 80 分位」を超えたら休む。
  コインごとに自分のベーシスで判定（BTC は BTCUSD、ETH は ETHUSD）。
- S23: pos = TSMOM60（終値 > 60 営業日前）・ロングのみ・BTC と ETH 半分ずつ（run_q529.py の tsmom・backtest・combine をそのまま使う）。S27 候補 = ゲートの日だけ pos=0。
- 帰無: コインごとにゲートの列を循環シフト（30 日以上）して同じ手順を B=500 回 → S27 候補の Sharpe の帰無 → z。

【測るもの】S23 と S27 候補の Sharpe・最大下落、休んだ日の S23 の平均 bp・翌 5 日の合計、帰無の z。
記述: 前後半、コイン別、ベーシスと資金調達率（--funding を渡したとき・Q551 と同じ f7）の Spearman、ベーシスの水準と翌 30 日の最大下落（SST の「暴落」）の Spearman、合成の追加関門。

【判定（事前固定・変更禁止・Q551 と同じ形）】
Sharpe が上がる かつ 最大下落が悪化しない かつ 休んだ日の平均 < 0 かつ z ≥ 2 → **支持**。
休んだ日の平均 > 0、または Sharpe が上がらない → **棄却**。それ以外 → 未確定。
多重比較: 判定は 1 本（閾値 80 分位・窓 365 日は S26 と同じに固定）。ほかは記述。

【捨てた案の数】約 4: ベーシスの変化（水準でなく）・分位 90%・ショートに回す（Fintokei の CFD は売れるが S23 はロングのみの設計）・期限構造の傾き（CQ と NQ の差）。

【検出力の注意】評価期間は 3.5 年と短い。支持の 4 条件を全部満たすのは難しく、未確定に落ちやすい。

【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】設計・コードは Opus（2026-10-29）。実行と解釈は後で Opus。実行者は result_q569.json の S23・S27c・off_mean_bp_all・null.z・verdict を返す。

【実装】s23-crypto-uptrend-long-q529/run_q529.py と s22-crypto-ml-fintokei-q528/crypto_core.py を読む（Q551 と同じ）。
実行: python3 run_q569.py --h1 <作業層/大容量/crypto_h1_hist> --basis <_データ/raw/crypto_basis> --out results [--funding <作業層/大容量/crypto_funding>]
試走: python3 run_q569.py --smoke --out results（合成データ・判定に使わない）
"""
import argparse, json, os, sys, types
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (pd.Timestamp("2021-01-08"), pd.Timestamp("2024-07-01")); HALF_SPLIT = pd.Timestamp("2022-10-01")
B = 500; SEED = 20261029; Q_THR = 0.80; MIN_DAYS = 30
PAIR = {"BTC": "BTCUSD", "ETH": "ETHUSD"}


def load_Q():
    sys.path.insert(0, os.path.join(HERE, "..", "s22-crypto-ml-fintokei-q528"))
    sys.path.insert(0, os.path.join(HERE, "..", "s23-crypto-uptrend-long-q529"))
    sys.modules.setdefault("lightgbm", types.ModuleType("lightgbm"))
    import run_q529 as Q
    return Q


class SmokeQ:
    """合成データ用の最小の代役（run_q529 の tsmom・backtest・combine と同じ式）。"""
    HALF = {"BTC": 0.0002, "ETH": 0.00075}

    @staticmethod
    def tsmom(b, L):
        c = b["close"].to_numpy(float); s = np.zeros(len(c)); s[L:] = (c[L:] > c[:-L]).astype(float); return s

    @staticmethod
    def backtest(b, pos, half):
        px = b["exec_px"].to_numpy(float); ret = np.zeros(len(b)); ret[:-1] = px[1:] / px[:-1] - 1
        p = np.asarray(pos, float); return pd.Series(p * ret - np.abs(np.diff(np.r_[0, p])) * half, index=b["day"].to_numpy())

    @staticmethod
    def combine(parts):
        return pd.concat(parts, axis=1).fillna(0.0).mean(axis=1)


def basis_series(path):
    d = pd.read_csv(path, parse_dates=["date", "cq_expiry", "nq_expiry"])
    dcq = (d["cq_expiry"] - d["date"]).dt.days; dnq = (d["nq_expiry"] - d["date"]).dt.days
    use_nq = (dcq < MIN_DAYS) & d["nq_close"].notna()
    F = np.where(use_nq, d["nq_close"], d["cq_close"]); days = np.where(use_nq, dnq, dcq)
    b = (F / d["index_close"] - 1) * 365 / days
    known = (d["date"] + pd.Timedelta(days=1)).dt.tz_localize("UTC").astype("datetime64[us, UTC]")
    return pd.DataFrame({"time": known, "basis": b.astype(float)}).dropna().sort_values("time").reset_index(drop=True)


def smoke_data(rng):
    bs, bas = {}, {}
    days = pd.bdate_range("2020-06-01", "2024-07-31", tz="UTC") + pd.Timedelta(hours=21)
    for c in ("BTC", "ETH"):
        r = rng.normal(0.001, 0.035, len(days)); cl = 10000 * np.exp(np.cumsum(r))
        b = pd.DataFrame({"day": days, "end": days, "close": cl, "exec_px": cl * (1 + rng.normal(0, 0.002, len(days))), "high": cl * 1.01})
        bs[c] = b
        t = pd.date_range("2020-06-01", "2024-07-31", freq="D", tz="UTC").astype("datetime64[us, UTC]")
        bas[c] = pd.DataFrame({"time": t, "basis": 0.08 + 0.1 * np.sin(np.arange(len(t)) / 60) + rng.normal(0, 0.03, len(t))})
    return bs, bas


def st(p):
    p = p[(p.index >= EV[0]) & (p.index < EV[1])]
    eq = (1 + p).cumprod()
    return dict(sharpe=round(float(p.mean() / p.std() * np.sqrt(252)), 3), max_dd=round(float((eq / eq.cummax() - 1).min()), 3),
                cagr=round(float(eq.iloc[-1] ** (252 / len(p)) - 1), 3), total=round(float(eq.iloc[-1] - 1), 3), n=int(len(p)))


def halves(p):
    return {"pre": st(p[p.index < HALF_SPLIT]), "post": st(p[p.index >= HALF_SPLIT])}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h1"); ap.add_argument("--basis"); ap.add_argument("--funding"); ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--B", type=int, default=B); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); rng = np.random.default_rng(SEED)
    if a.smoke:
        Q = SmokeQ; raw_b, raw_basis = smoke_data(rng)
    else:
        Q = load_Q(); raw_b = {c: Q.daily_series(a.h1, c) for c in PAIR}; raw_basis = {c: basis_series(os.path.join(a.basis, f"{PAIR[c]}_D1.csv")) for c in PAIR}
    bs, pos, gate, bval = {}, {}, {}, {}
    for c in PAIR:
        b = raw_b[c]; bb = raw_basis[c]
        x = pd.merge_asof(b[["end"]].astype("datetime64[us, UTC]").sort_values("end"), bb.rename(columns={"time": "end"}), on="end", direction="backward")
        bv = pd.Series(x["basis"].to_numpy(), index=b["day"].dt.tz_convert(None))
        thr = bv.rolling("365D", min_periods=200, closed="left").quantile(Q_THR)
        b = b.set_index(b["day"].dt.tz_convert(None), drop=False); b["day"] = b.index
        bs[c] = b; pos[c] = Q.tsmom(b, 60); bval[c] = bv
        gate[c] = (bv > thr).to_numpy() & np.isfinite(thr.to_numpy())
    res = {"eval": f"{EV[0].date()}〜{(EV[1] - pd.Timedelta(days=1)).date()}", "smoke": a.smoke}
    s23p = {c: Q.backtest(bs[c], pos[c], Q.HALF[c]) for c in bs}
    s27pos = {c: np.where(gate[c], 0.0, pos[c]) for c in bs}
    s27p = {c: Q.backtest(bs[c], s27pos[c], Q.HALF[c]) for c in bs}
    S23, S27 = Q.combine(list(s23p.values())), Q.combine(list(s27p.values()))
    res["S23"] = st(S23); res["S27c"] = st(S27); res["halves"] = {"S23": halves(S23), "S27c": halves(S27)}
    off = {}
    for c in bs:
        idx = bs[c].index; inev = (idx >= EV[0]) & (idx < EV[1]); m = (pos[c] == 1) & gate[c] & inev; held = (pos[c] == 1) & inev
        r = s23p[c].to_numpy()
        off[c] = dict(off_days=int(m.sum()), held_days=int(held.sum()), off_share=round(float(m.sum() / max(held.sum(), 1)), 3),
                      off_mean_bp=round(float(r[m].mean() * 1e4), 2) if m.any() else None, held_not_off_mean_bp=round(float(r[held & ~m].mean() * 1e4), 2),
                      off_next5_mean_bp=round(float(np.mean([r[i + 1:i + 6].sum() for i in np.where(m)[0] if i + 6 <= len(r)]) * 1e4), 2) if m.any() else None)
        res[f"by_coin_{c}"] = dict(S23=st(s23p[c]), S27c=st(s27p[c]))
    res["off_days"] = off
    off_all = np.concatenate([s23p[c].to_numpy()[(pos[c] == 1) & gate[c] & (bs[c].index >= EV[0]) & (bs[c].index < EV[1])] for c in bs])
    res["off_mean_bp_all"] = round(float(off_all.mean() * 1e4), 2) if len(off_all) else None
    null = []
    for _ in range(a.B):
        pp = []
        for c in bs:
            n = len(gate[c]); g = np.roll(gate[c], int(rng.integers(30, n - 30)))
            pp.append(Q.backtest(bs[c], np.where(g, 0.0, pos[c]), Q.HALF[c]))
        null.append(st(Q.combine(pp))["sharpe"])
    null = np.array(null); z = float((res["S27c"]["sharpe"] - null.mean()) / null.std(ddof=1))
    res["null"] = dict(B=a.B, sharpe_mean=round(float(null.mean()), 3), sd=round(float(null.std(ddof=1)), 3), p2_5=round(float(np.percentile(null, 2.5)), 3),
                       p97_5=round(float(np.percentile(null, 97.5)), 3), z=round(z, 2))
    oma = res["off_mean_bp_all"] if res["off_mean_bp_all"] is not None else float("nan")
    crit = dict(sharpe_up=res["S27c"]["sharpe"] > res["S23"]["sharpe"], dd_not_worse=res["S27c"]["max_dd"] >= res["S23"]["max_dd"],
                off_days_lose=oma < 0, null_z_ge_2=z >= 2)
    res["criteria"] = crit
    res["verdict"] = "支持" if all(crit.values()) else ("棄却" if (oma > 0 or not crit["sharpe_up"]) else "未確定")
    # 記述: ベーシスと翌 30 日の最大下落（SST の暴落）、資金調達率との相関
    desc = {}
    for c in bs:
        b = bs[c]; px = b["exec_px"].to_numpy(float); n = len(px)
        fdd = np.full(n, np.nan)
        for i in range(n - 31):
            w = px[i + 1:i + 31] / px[i]; fdd[i] = float((w / np.maximum.accumulate(np.r_[1.0, w])[1:] - 1).min())
        m = (b.index >= EV[0]) & (b.index < EV[1]) & np.isfinite(bval[c].to_numpy()) & np.isfinite(fdd)
        desc[c] = {"spearman_basis_next30_maxdd": round(float(pd.Series(bval[c].to_numpy()[m]).corr(pd.Series(fdd[m]), method="spearman")), 4),
                   "next30_maxdd_gate_on": round(float(np.nanmean(fdd[m & gate[c]])), 4) if (m & gate[c]).any() else None,
                   "next30_maxdd_gate_off": round(float(np.nanmean(fdd[m & ~gate[c]])), 4)}
        if a.funding and not a.smoke:
            f = pd.read_csv(os.path.join(a.funding, f"funding_{c}.csv")); f["time"] = pd.to_datetime(f["time"], format="ISO8601", utc=True).astype("datetime64[us, UTC]")
            f = f.sort_values("time"); f["f7"] = f["rate"].rolling(21, min_periods=21).mean()
            xf = pd.merge_asof(b[["end"]].astype("datetime64[us, UTC]").reset_index(drop=True).sort_values("end"), f[["time", "f7"]].rename(columns={"time": "end"}), on="end", direction="backward")["f7"].to_numpy()
            mm = m & np.isfinite(xf)
            desc[c]["spearman_basis_vs_funding_f7"] = round(float(pd.Series(bval[c].to_numpy()[mm]).corr(pd.Series(xf[mm]), method="spearman")), 4)
    res["describe"] = desc
    pre = "smoke_" if a.smoke else ""
    pd.DataFrame({"S23": S23, "S27c": S27}).to_csv(os.path.join(a.out, f"{pre}daily_q569.csv"))
    if not a.smoke:
        try:
            sys.path.insert(0, os.path.join(HERE, "..", "..", "tools")); from composite_gate import gate as cg
            res["composite_gate"] = cg(S27[(S27.index >= EV[0]) & (S27.index < EV[1])], "Q569 S27 候補（S23＋ベーシスゲート）")
        except Exception as e:
            res["composite_gate"] = f"失敗: {e}"
    json.dump(res, open(os.path.join(a.out, f"{pre}result_q569.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: res[k] for k in ("S23", "S27c", "off_mean_bp_all", "null", "criteria", "verdict")}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
