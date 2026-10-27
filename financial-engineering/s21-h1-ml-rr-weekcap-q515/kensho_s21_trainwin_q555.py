# -*- coding: utf-8 -*-
"""Q555: S21 の学習窓 — 直近に寄せて毎月学習し直すと、翌月はよく勝つか（事前登録_q555.md）。
事前登録 事前登録_q555.md と同一・変更禁止。

【仮説】相場は非定常なので、直近 N か月だけで毎月学習し直したモデルのほうが、拡大窓（WX）より翌 1 か月の成績が良い。
【判定】（多重比較: WX との比較 8 本〔W1・W3・W6・W12・W36・W1a・W3a・W6a〕に Holm）
- 支持（直近に寄せるほうが翌月勝つ）: 短い窓 6 本（W1・W3・W6・W1a・W3a・W6a）のうち少なくとも 1 本で、Δ（月次 R の腕−WX の 108 本）の片側 p が
  Holm 補正後 < 0.05、かつ その腕自身の日次 t ≥ 2。→ その腕を「S21-W」として別 ID で凍結し、フォワードで S21 と並べる案を taichi に ★ で出す。
- 棄却（直近に寄せても翌月は勝てない）: 短い窓 6 本すべてで Δ の平均 ≤ 0。
- 未確定: それ以外。W12・W36 は多重比較には数えるが「短い窓」には入れない。どの結果でも S21 とフォワードは変えない。
【多重比較の本数】8（試行は S21 系に 9 本。Y は数えない）

使い方: python3 kensho_s21_trainwin_q555.py DATA_DIR OUT_DIR [--arms W1,W3,...] [--smoke]
評価月 2016-10〜2025-09 の 108 か月（閾値用に 2016-09 も学習・予測、売買には数えない）。2025-10-01 以降は読まない。
"""
import argparse, json, os, pickle, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
from scipy import stats as sps
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "_データ", "fetch"))  # convert_histdata_m15（q524 が import）
import kensho_s21_h1_ml_rr_q515 as K
import kensho_s21_walkforward_q518 as W
import kensho_s21d_relthr_wf_q519 as Q
import kensho_s21f_newjpy_q524 as J
import kensho_s21_noweekend_q533 as Z
import kensho_s21_reopen_q534 as E
from fe_core.multiple import holm

UTC = lambda s: pd.Timestamp(s, tz="UTC")
EVAL0, EVAL1 = UTC("2016-10-01"), UTC("2025-10-01")      # 評価期間（終端は含まない）
FIRST = UTC("2016-09-01")                                # 閾値用の 1 か月前
AGGR = dict(K.LGB_PARAMS, min_child_samples=50)
# 腕: (窓の月数 None=拡大, params, step)
ARMS = {"W1": (1, K.LGB_PARAMS, 3), "W3": (3, K.LGB_PARAMS, 3), "W6": (6, K.LGB_PARAMS, 3), "W12": (12, K.LGB_PARAMS, 3),
        "W36": (36, K.LGB_PARAMS, 3), "WX": (None, K.LGB_PARAMS, 3),
        "W1a": (1, AGGR, 1), "W3a": (3, AGGR, 1), "W6a": (6, AGGR, 1)}
SHORT = ["W1", "W3", "W6", "W1a", "W3a", "W6a"]
COMP = ["W1", "W3", "W6", "W12", "W36", "W1a", "W3a", "W6a"]


def _compat_tz_to_numpy():
    """この環境（pandas 2.3・numpy 1.26/2.x）では tz つき Series.to_numpy() が object になり K.labels が落ちる。
    tz つきのときだけ datetime64 を返す（K・Z・Q 本体は書き換えない）。値は変わらない。"""
    if str(pd.Series(pd.to_datetime(["2020-01-01"], utc=True)).to_numpy().dtype) != "object":
        return
    orig = pd.Series.to_numpy

    def to_numpy(self, *args, **kw):
        if not args and not kw and isinstance(self.dtype, pd.DatetimeTZDtype):
            return self.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
        return orig(self, *args, **kw)
    pd.Series.to_numpy = to_numpy


def train_win(data, end, start, step, params):
    """Q.train_window と同じ中身（end より前に決済まで終わる行だけ）。params を受け取れる版。"""
    Xs, Ys = [], []
    for s, o in data.items():
        t = o["time"]; n = len(t); tn = t.dt.tz_convert(None).to_numpy()
        ok = np.isfinite(o["R"]).all(1); xmax = o["X"].max(1)
        ok &= (xmax >= 0) & (tn[np.clip(xmax, 0, n - 1)] < end.tz_convert(None).to_datetime64())
        if start is not None:
            ok &= tn >= start.tz_convert(None).to_datetime64()
        sel = np.where(ok)[0][::step]
        Xs.append(o["F"].iloc[sel]); Ys.append(o["R"][sel])
    Xtr = pd.concat(Xs); Ytr = np.vstack(Ys); models = []
    for a in range(len(K.ACTIONS)):
        m = lgb.LGBMRegressor(random_state=K.SEED + a, **params); m.fit(Xtr, np.clip(Ytr[:, a], -3, 3)); models.append(m)
    return models, len(Xtr)


def months(first, last_excl):
    out = []; m = first
    while m < last_excl:
        out.append(m); m = m + pd.DateOffset(months=1)
    return out


def cached(path, fn):
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    v = fn(); os.makedirs(os.path.dirname(path), exist_ok=True)
    pickle.dump(v, open(path + ".tmp", "wb")); os.replace(path + ".tmp", path)
    return v


def concat_P(parts):
    out = {}
    for s in parts[0]:
        out[s] = (np.concatenate([p[s][0] for p in parts]), np.vstack([p[s][1] for p in parts]))
    return out


def arm_predictions(dataw, arm, mlist, cdir):
    """学習外の予測（月ごとの P）をつなげる。月ごとに pkl 保存・再実行は飛ばす。"""
    parts = []
    if arm == "Y":
        for Y in range(mlist[0].year - 1, mlist[-1].year + 1):   # 毎年 10-01 に拡大窓で学習
            s0, s1 = W.TS(Y), W.TS(Y + 1)
            if s1 <= mlist[0] or s0 >= mlist[-1] + pd.DateOffset(months=1):
                continue
            lo, hi = max(s0, mlist[0]), min(s1, mlist[-1] + pd.DateOffset(months=1))
            def f(s0=s0, lo=lo, hi=hi):
                m, _ = train_win(dataw, s0, None, 3, K.LGB_PARAMS)
                return K.predict(m, dataw, lo, hi)
            parts.append(cached(os.path.join(cdir, "Y", f"{Y}.pkl"), f))
        return concat_P(parts)
    nm, params, step = ARMS[arm]
    for s0 in mlist:
        s1 = s0 + pd.DateOffset(months=1)
        assert s1 <= EVAL1
        def f(s0=s0, s1=s1):
            st = None if nm is None else s0 - pd.DateOffset(months=nm)
            m, _ = train_win(dataw, s0, st, step, params)
            return K.predict(m, dataw, s0, s1)
        t0 = time.time(); parts.append(cached(os.path.join(cdir, arm, f"{s0:%Y-%m}.pkl"), f))
        print(f"  {arm} {s0:%Y-%m} {time.time()-t0:.0f}s", flush=True)
    return concat_P(parts)


def arm_trades(dataw, P):
    PP = J.apply_thr(dataw, P, J.thr_series(dataw, P), EVAL0)
    return K.run_policy(dataw, E.block(PP, dataw, 1), 0.0)


def monthly_R(tr, evm):
    e = tr["entry"].dt.tz_convert(None).dt.to_period("M")
    s = tr.groupby(e)["R"].sum()
    return s.reindex(pd.PeriodIndex([m.tz_convert(None).to_period("M") for m in evm]), fill_value=0.0)


def describe(tr, mR, s0, s1):
    p = K.daily(tr, s0, s1, 1.0); cum = p.cumsum()
    return dict(n=int(len(tr)), mean_R=round(float(tr["R"].mean()), 4) if len(tr) else None, total_R=round(float(tr["R"].sum()), 1),
                t_daily=round(K.tstat(p), 2), max_dd_R=round(float((cum - cum.cummax()).min()), 1), pos_month_share=round(float((mR > 0).mean()), 3),
                monthly_mean_R=round(float(mR.mean()), 3))


def sub(mR, a, b):
    x = mR[(mR.index >= pd.Period(a)) & (mR.index <= pd.Period(b))]
    return dict(months=int(len(x)), sum_R=round(float(x.sum()), 1), mean_R=round(float(x.mean()), 3), pos_share=round(float((x > 0).mean()), 3))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("out")
    ap.add_argument("--arms", default=None); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
    _compat_tz_to_numpy()
    out = os.path.join(a.out, "smoke_q555") if a.smoke else a.out; os.makedirs(out, exist_ok=True); t00 = time.time()
    arms = a.arms.split(",") if a.arms else list(ARMS) + ["Y"]
    syms = list(J.SYMS15); mlist = months(FIRST, EVAL1)
    if a.smoke:
        syms = ["EURUSD", "USDJPY"]; arms = ["W3", "WX", "Y"]; mlist = mlist[:3]
    dataw = {}
    for s in syms:
        o = J.make(K.load(a.data, s), s); Rw, Xw = Z.labels_wk(o["d"], s)
        dataw[s] = dict(o, R=Rw, X=Xw, _sr=E.since_reopen(o["d"]))
    print(f"データ準備 済 {time.time()-t00:.0f}s 腕={arms} 月={len(mlist)}", flush=True)
    evm = [m for m in mlist if m >= EVAL0]; end_eval = evm[-1] + pd.DateOffset(months=1)
    assert end_eval <= EVAL1
    cdir = os.path.join(out, "q555"); TR = {}; MR = {}; res = dict(qid="Q555", run_at=time.strftime("%Y-%m-%d %H:%M"), smoke=a.smoke, arms={})
    for arm in arms:
        P = arm_predictions(dataw, arm, mlist, cdir)
        tr = arm_trades(dataw, P); tr = tr[tr["entry"] >= EVAL0]
        TR[arm] = tr; MR[arm] = monthly_R(tr, evm)
        d = describe(tr, MR[arm], EVAL0, end_eval)
        d["periods"] = {"2016-10_2020-09": sub(MR[arm], "2016-10", "2020-09"), "2020-10_2025-09": sub(MR[arm], "2020-10", "2025-09"),
                        "2021-10_2023-09": sub(MR[arm], "2021-10", "2023-09")}
        res["arms"][arm] = d
        print(arm, json.dumps(d, ensure_ascii=False), f"| {time.time()-t00:.0f}s", flush=True)
    # 主: WX との差
    if "WX" in MR:
        pv, comp = [], [c for c in COMP if c in MR]
        for c in COMP:
            if c not in MR:
                pv.append(np.nan); continue
            dlt = (MR[c] - MR["WX"]).to_numpy(); n = len(dlt)
            sd = dlt.std(ddof=1) if n > 2 else 0.0
            t = float(dlt.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
            p = float(sps.t.sf(t, n - 1)) if sd > 0 else np.nan
            res["arms"][c]["delta_vs_WX"] = dict(mean=round(float(dlt.mean()), 4), t=round(t, 2), p_one_sided=p); pv.append(p)
        adj = holm(pv)
        for c, ap_ in zip(COMP, adj):
            if c in MR:
                res["arms"][c]["delta_vs_WX"]["p_holm"] = None if not np.isfinite(ap_) else float(ap_)
        if "Y" in MR:
            dy = (MR["WX"] - MR["Y"]).to_numpy()
            res["WX_minus_Y"] = dict(mean=round(float(dy.mean()), 4), note="記述のみ（年 1 回→毎月の効果）")
        sup = [c for c in SHORT if c in MR and (res["arms"][c]["delta_vs_WX"].get("p_holm") or 1) < 0.05 and res["arms"][c]["t_daily"] >= 2]
        full = all(c in MR for c in SHORT)
        if sup:
            v = "支持"
        elif full and all(res["arms"][c]["delta_vs_WX"]["mean"] <= 0 for c in SHORT):
            v = "棄却"
        else:
            v = "未確定"
        res["verdict"] = v if full else v + "（腕が足りない: 参考）"; res["supported_arms"] = sup
    res["rule_mode"] = "R単位（サイズ無関係）"; res["n_trials"] = 9; res["n_tests"] = 8
    res["gate"] = "n/a（R 単位・フォワード用の凍結ではない）"
    res["max_dd"] = {k: v["max_dd_R"] for k, v in res["arms"].items()}
    res["worst_day"] = {k: round(float(K.daily(t, EVAL0, end_eval, 1.0).min()), 2) for k, t in TR.items()}
    res["stops"] = "SL 1.5×ATR24・時間切れ 120 本・週末前決済（Z.labels_wk）"
    json.dump(res, open(os.path.join(out, "result_q555.json"), "w"), ensure_ascii=False, indent=1, default=str)
    pd.concat([t.assign(arm=k, month=t["entry"].dt.tz_convert(None).dt.to_period("M").astype(str)) for k, t in TR.items()]).to_csv(
        os.path.join(out, "trades_q555.csv.gz"), index=False, compression="gzip")
    print("判定", res.get("verdict"), "| done", round(time.time() - t00), flush=True)


if __name__ == "__main__":
    main()
