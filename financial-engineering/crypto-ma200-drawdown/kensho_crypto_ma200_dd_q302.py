#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q302: 暗号資産 11 通貨日足の 200 日線の最大下落は同じ露出の循環シフトより浅いか（Q097/Q098 の暗号資産への移植）
================================================================================
事前登録の正本は下の SPEC（fe_core の Spec を事前登録の入れ物として使う「土台を直接使う型」）。
種: ローカル LLM（qwen3:8b）のアイデア 2026-10-15「200日線は CRYPTO D1 の最大下落を、無作為タイミングより有意に浅く抑えるか」を Opus が選別・設計。
実行: python3 kensho_crypto_ma200_dd_q302.py（B=1000）／ --smoke --B 5（経路確認）／ --readme ／ --idea-row
"""
import datetime as _dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import (Spec, CRYPTO, CRYPTO_COST_RT_REL, parse_args, write_result, syms_available, health,  # noqa: E402
                     load_h1, h1_to_d1, fmt, holm)
from fe_core.readme import render_readme, render_idea_row  # noqa: E402

MA = 200
SPLIT = pd.Timestamp("2022-01-01")
MIN_SHIFT = 126

SPEC = Spec(
    qid="Q302",
    question="暗号資産 11 通貨日足の 200 日線（終値>SMA200 で買い・下で現金）の最大下落は同じ露出の循環シフトより浅いか（Q097/Q098 の暗号資産への移植）",
    hypothesis="合図 s[t]=1{close[t]>SMA200[t]}（t の終値で決め t+1 から保有・空売りなし・現金は 0%）。等加重の暗号資産束の最大下落の深さ |MDD| は、"
               "各通貨の合図を期間内で循環シフトした（露出と切り替え回数を保つ）帰無の |MDD| の 5% 点より浅い（前後半とも）",
    reject_if="支持: 前半（〜2021）・後半（2022〜）とも |MDD_実際| < 帰無 |MDD| の 5% 点（帰無の 95% より浅い）。"
              "棄却: 前後半とも |MDD_実際| ≥ 帰無 |MDD| の 10% 点（浅い側 10% に入らない）。それ以外 → 未確定。"
              "（両期間とも通ることを求める交差検定なので多重比較の補正はしない）",
    syms=list(CRYPTO), kind="H1→D1", params=[{"MA": MA}], n_tests=2, warmup=MA, per_year=365, B=1000,
    null_kind="circ_shift", null_min_shift=MIN_SHIFT,
    discarded="約3: ボラ目標の併用（Q098 型・別案に回す）、SMA100/50 の掃引（判定 1 本に絞るため記述も省略）、BTC 単独（Q097 の株と同じ形だが 1 銘柄で検出力不足）",
    knowledge_cutoff="Claude の知識の締め切りはおよそ 2026-06。データは 2017-05〜2026-09（2026-07 以降の 3 か月は締め切り後）。規則は固定で相場観は使わない",
    delegation="設計とコードは Opus（2026-10-16）。実行と記録は Sonnet（怪しければ escalate）。結論ではなく JSON のパス・|MDD| と帰無の 5%/10% 点・百分位を返させ、本体が確かめる",
    source="知見「株価指数の200日線と12か月モメンタムの保有現金規則だけが同じ露出の無作為なタイミングより最大下落が浅く、商品と為替では下落の軽さは露出の低さで説明できる」（Q097/Q098）、"
           "知見「トレンドフォローの最大下落の軽さは市場滞在時間が同じ無作為なタイミングより浅い」、[[ブログQuanterLab2026b-2_SPY全期間ではボラティリティターゲティングが買い持ちをわずかに上回り200日線は最大下落を抑える]]。"
           "種: ローカル LLM アイデア 2026-10-15",
    data="暗号資産 11 通貨 H1_dukascopy → h1_to_d1（UTC 0 時区切り・週末込み）。開始は BTC 2017-05・ETH 2017-12・XRP/BCH/EOS 2018-05・LTC 2018-09・XLM 2021-05・ADA/LNK 2021-09・DOT/SOL 2024-03。"
         "前半（〜2021）は実質 6 通貨",
    measure="等加重束（その日に合図が定義された通貨の平均）の複利の最大下落（コスト後・往復 30bp）を前後半で。記述: 買い持ちの最大下落、露出、通貨ごとの帰無百分位、年率リターン",
    null_desc=f"通貨ごと・期間ごとに合図列を循環シフト（k∈[{MIN_SHIFT}, n−{MIN_SHIFT}]）B 回 → 束の |MDD| の帰無分布 → 実際の百分位（浅い側から）",
    prior_art="WebSearch 2026-10-16・standard・検索語 \"200-day moving average cryptocurrency drawdown reduction timing versus exposure random timing test\"。"
              "見つかったもの: Unger Academy のブログ（BTC のトレンド規則で下落 1/3）、TradingView の 200 日 EMA の図、arXiv 2303.02613（下落制御の再起動機構・別問題）。"
              "未確認: 露出をそろえた循環シフト帰無で 200 日線の下落の軽さが『タイミング』か『露出』かを暗号資産の複数通貨で分けた検証は見当たらない（移植）。ブログは根拠にしない",
    batch="4案一括生成（ローカル LLM アイデアの選別 2026-10-16）", designer="Opus", coder="Claude（Opus）",
    settings={"MA": MA, "split": str(SPLIT.date()), "cost_rt_rel": CRYPTO_COST_RT_REL, "cutoff_hour_utc": 0},
)


def max_dd(r):
    """r: 日次の単利リターン（小数）。2 次元 (B,T) 可。最大下落（負の値）。"""
    w = np.cumprod(1.0 + r, axis=-1)
    peak = np.maximum.accumulate(np.maximum(w, 1.0), axis=-1)
    return (w / peak - 1.0).min(axis=-1)


def coin_returns(d, sig, cost_ow):
    """sig: 0/1（t の終値で決定）。保有 pos[t]=sig[t-1]。r[t]=pos[t]*ret[t] − cost*|Δpos|。gap 行の ret は 0 扱い。"""
    ret = np.nan_to_num(d["ret"].values.astype(float))
    if "gap" in d:
        ret = np.where(d["gap"].values, 0.0, ret)
    pos = np.r_[0.0, sig[:-1]]
    dpos = np.abs(np.diff(pos, prepend=0.0))
    return pos * ret - cost_ow * dpos, pos


def load_coins(syms, args, rng):
    out = {}
    for s in syms:
        h1 = load_h1(s, args.smoke, rng, n=60000, start="2018-01-01")
        d = h1_to_d1(h1, 0).reset_index(drop=True)
        c = d["close"].values.astype(float)
        sma = pd.Series(c).rolling(MA).mean().values
        sig = np.where(np.isnan(sma), 0.0, (c > sma).astype(float))
        d = d.iloc[MA:].reset_index(drop=True); sig = sig[MA:]
        out[s] = (d, sig)
    return out


def period_mask(times, name):
    t = pd.to_datetime(times)
    return (t < SPLIT) if name == "pre" else (t >= SPLIT)


def basket(coins, sigs_by_coin, name, cost_ow):
    """期間 name の等加重束の日次リターン（日付の和集合で揃え、その日に居る通貨の平均）。"""
    cols = {}; exps = []
    for s, (d, _) in coins.items():
        m = period_mask(d["time"].values, name)
        if m.sum() < 30:
            continue
        sig = sigs_by_coin[s][m]
        r, pos = coin_returns(d[m], sig, cost_ow)
        cols[s] = pd.Series(r, index=pd.to_datetime(d["time"].values[m]))
        exps.append(pos.mean())
    if not cols:
        return None, None, []
    df = pd.concat(cols, axis=1).sort_index()
    return df.mean(axis=1, skipna=True).values, float(np.mean(exps)), list(cols)


def run(args, rng):
    syms, missing = syms_available(SPEC.syms, kind="H1_dukascopy", smoke=args.smoke)
    dh = None if args.smoke else health(syms, kind="H1_dukascopy")
    coins = load_coins(syms, args, rng)
    cost_ow = CRYPTO_COST_RT_REL / 2
    obs_sigs = {s: sig for s, (_, sig) in coins.items()}
    res = {"question": SPEC.question, "spec": SPEC.as_dict(), "missing": missing, "data_health": dh, "periods": {}}
    for name in ("pre", "post"):
        r, exp, members = basket(coins, obs_sigs, name, cost_ow)
        if r is None:
            res["periods"][name] = None; continue
        mdd = float(max_dd(r))
        bh_sigs = {s: np.ones_like(sig) for s, sig in obs_sigs.items()}
        rbh, _, _ = basket(coins, bh_sigs, name, 0.0)
        null = []
        for _ in range(args.B):
            ns = {}
            for s, (d, sig) in coins.items():
                m = period_mask(d["time"].values, name); sg = sig.copy(); idx = np.where(m)[0]
                n = len(idx)
                if n > 2 * MIN_SHIFT:
                    k = int(rng.integers(MIN_SHIFT, n - MIN_SHIFT + 1)); sg[idx] = np.roll(sig[idx], k)
                ns[s] = sg
            rn, _, _ = basket(coins, ns, name, cost_ow)
            null.append(float(max_dd(rn)))
        depth = np.abs(np.array(null)); d_obs = abs(mdd)
        q05, q10 = (float(np.quantile(depth, 0.05)), float(np.quantile(depth, 0.10))) if len(depth) else (None, None)
        pct_shallower = float(np.mean(depth <= d_obs)) if len(depth) else None  # 帰無のうち実際以下の深さの割合（小さいほど実際が浅い）
        per_coin = {}
        for s, (d, sig) in coins.items():
            m = period_mask(d["time"].values, name)
            if m.sum() < 30:
                continue
            rc, pc = coin_returns(d[m], sig[m], cost_ow)
            per_coin[s] = {"n_days": int(m.sum()), "mdd": fmt(max_dd(rc)), "mdd_bh": fmt(max_dd(np.nan_to_num(d[m]["ret"].values))),
                           "exposure": fmt(pc.mean()), "ann_ret": fmt(float(np.prod(1 + rc) ** (365.0 / len(rc)) - 1))}
        res["periods"][name] = {"members": members, "n_days": int(len(r)), "mdd": fmt(mdd), "mdd_buyhold": fmt(max_dd(rbh)),
                                "exposure_mean": fmt(exp), "ann_ret": fmt(float(np.prod(1 + r) ** (365.0 / len(r)) - 1)),
                                "null_B": len(null), "null_depth_q05": fmt(q05), "null_depth_q10": fmt(q10),
                                "null_depth_q50": fmt(float(np.median(depth))) if len(depth) else None,
                                "pct_null_shallower_or_equal": fmt(pct_shallower), "per_coin": per_coin}
    res["machine_verdict"] = judge(res)
    if dh and (dh["failed"] or dh["gaps"]):
        res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
    res["multiple_comparisons"] = "判定は前後半 2 本の交差（両方を要求）。通貨ごとの百分位・買い持ちは記述"
    return res


def judge(res):
    p = res["periods"]
    if any(p.get(k) is None or p[k].get("null_depth_q05") is None for k in ("pre", "post")):
        return "未確定: 計算できない（期間・通貨の不足）"
    sup = all(abs(p[k]["mdd"]) < p[k]["null_depth_q05"] for k in ("pre", "post"))
    rej = all(abs(p[k]["mdd"]) >= p[k]["null_depth_q10"] for k in ("pre", "post"))
    if sup:
        return "支持: 前後半とも実際の |MDD| が帰無の 5% 点より浅い"
    if rej:
        return "棄却: 前後半とも実際の |MDD| が帰無の浅い側 10% に入らない（下落の軽さは露出で説明できる）"
    return "未確定"


def main():
    av = sys.argv[1:]; script = os.path.basename(__file__)
    if "--readme" in av:
        open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write(render_readme(SPEC, script, script_kind="土台を直接使う型"))
        print("wrote README.md"); return
    if "--idea-row" in av:
        print(render_idea_row(SPEC, folder=os.path.basename(HERE)).replace("fe_core Runner 型", "fe_core 土台を直接使う型")); return
    args = parse_args(default_B=SPEC.B)
    rng = np.random.default_rng(args.seed)
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S"); pre = f"smoke_{SPEC.qid}" if args.smoke else SPEC.qid
    with open(os.path.join(out, f"{pre}_spec_{ts}.json"), "w", encoding="utf-8") as fh:
        json.dump({"qid": SPEC.qid, "registered": ts, "B": args.B, "seed": args.seed, **SPEC.as_dict()}, fh, ensure_ascii=False, indent=1)
    res = run(args, rng)
    res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
    write_result(SPEC.qid, res, args.smoke, here=HERE)
    print("machine_verdict:", res["machine_verdict"])


if __name__ == "__main__":
    main()
