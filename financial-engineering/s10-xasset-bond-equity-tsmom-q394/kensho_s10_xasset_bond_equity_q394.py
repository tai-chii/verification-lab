#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q394 S10: 株価指数 13＋債券 3 の D1 クロスアセット TSMOM（債券の 250 日リターン符号で株を持ち・株の 250 日リターンの逆符号で債券を持つ）は規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（封印・spec.split_year の規程モード・loaded は _s1x_common/s1x.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s10_xasset_bond_equity_q394.py（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec  # noqa: E402
import s1x as X  # noqa: E402

# 相手の割り当て（自国債券が無い指数は USTBOND を世界の代理にする＝事前固定）
BOND_OF = {"US500": "USTBOND", "USTECH": "USTBOND", "US30": "USTBOND", "JPN225": "USTBOND", "AUS200": "USTBOND", "HKG33": "USTBOND",
           "GER40": "BUND", "FRA40": "BUND", "ESP35": "BUND", "EUSTX50": "BUND", "NLD25": "BUND", "SUI20": "BUND", "UK100": "UKGILT"}
EQUITY_OF = {"USTBOND": "US500", "BUND": "EUSTX50", "UKGILT": "UK100"}

SPEC = Spec(
    qid="Q394",
    question="株価指数 13＋債券 3 の D1 で、債券の 250 日リターン符号で株を持ち・株の 250 日リターンの逆符号で債券を持つクロスアセット TSMOM は規程モードで封印前の前後半（境 2021）とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="Pitkäjärvi・Suominen・Vaittinen 2020 JFE: 20 か国で過去の債券リターンは株の将来リターンを正に、過去の株リターンは債券の将来リターンを負に予測し、クロスアセット TSMOM は TSMOM より Sharpe が 45% 高い（遅い資本の移動）。手元の 48 銘柄のうち指数 13・債券 3 で同じ向きが D1 でも出るなら、OHLCV のみで粗利 ≈0 だった S07 と違い、他市場の価格（債券↔株）という入力を 1 つ足した分だけ関門の数字が上がる。main=cross（相手の符号だけ）。副=catsmom（自分の TSMOM と相手の合図が一致したときだけ持つ）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2021）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main cross）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。債券 3 本は 2016-05（BUND）・2017-12（USTBOND・UKGILT）からで前半（〜2020）が 5 年未満のため、前半の t は記述扱い（判定の文は変えない。通らなければ未確定で止まり、前向き標本で再判定）。副 catsmom・銘柄別・指数のみ／債券のみは記述。S10 の族内試行は Q394・Q395 の 2 本×2 設定＝4",
    syms=X.IDX13 + X.BOND3, kind="D1_fromH1",
    params=[{"L": 250, "mode": "cross"}, {"L": 250, "mode": "catsmom"}], main_param=0, n_tests=2, warmup=250, per_year=252,
    B=500, split_year=2021, null_kind="circ_shift", null_min_shift=120,
    discarded="3（月次リバランス＝原著の形だが日次の方が手元の型に合う／L を 20〜250 で掃引＝原著の 1〜12 か月の中から 12 か月に固定／相手を複数の債券の平均にする＝国の対応が崩れる）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S10（他市場の価格＝入力基準改定後 2 つ目のデータ源）／Pitkäjärvi・Suominen・Vaittinen 2020 'Cross-asset signals and time series momentum' JFE 136(1) 63–85／Moskowitz・Ooi・Pedersen 2012／S07 Q367（指数・債券を含む 48 銘柄 TSMOM は棄却）",
    data="指数 13（US500・UK100・JPN225 は 2010〜、GER40 等は 2013-09〜）＋債券 3（BUND 2016-05〜、USTBOND・UKGILT 2017-12〜）の D1_fromH1（_データ/raw/D1・封印 time<2024-07-01）。相手の割り当ては BOND_OF／EQUITY_OF（自国債券の無い指数は USTBOND を代理）。相手の終値は同じ UTC 0 時区切りの足を time で合わせる（先読みなし）。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（Runner の既定）",
    measure="等金額: 16 銘柄の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出。規程モード（境 2021）: t_all/t_pre/t_post・nw_t・mean_bp・max_dd・worst_day・stops（全設定）。extra: 指数のみ／債券のみの年単位 bp と t（相手ごとの寄与）",
    null_desc="合図の循環シフト（min_shift=120・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「cross-asset time series momentum bond returns predict equity index returns Pitkäjärvi Suominen Vaittinen 2020 Journal of Financial Economics international」: 原著（1980〜2016・20 か国・月次・Sharpe +45%）と alphaarchitect／quantpedia の紹介。2016 年以後の標本外・日次・CFD の債券先物・プロップ規程・封印つきの判定は未確認。紹介記事は根拠にしない",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 1 本目（S10・クロスアセット）", designer="Fable", coder="Fable",
    settings={"seal": str(X.SEAL.date()), "bond_of": BOND_OF, "equity_of": EQUITY_OF, "s10_family_trials": "Q394・Q395 の 2 本×2 設定＝4",
              "note_sample": "債券 3 本は 2016〜2017 開始。前半（〜2020）は 5 年未満で t は記述扱い"},
)
RUNNER = {"obj": None}


def _partner_sign(df, partner, L):
    """相手銘柄の L 本リターンの符号を df の time に合わせる（相手の足を ffill。無ければ 0）。"""
    r = RUNNER["obj"]
    if r is None or partner not in r.loaded:
        return np.zeros(len(df))
    pdf = r.loaded[partner]
    s = pd.Series(pdf["close"].values, index=pd.to_datetime(pdf["time"]).values)
    a = s.reindex(pd.to_datetime(df["time"]).values, method="ffill").values
    out = np.zeros(len(df)); out[L:] = np.sign(a[L:] - a[:-L])
    return np.nan_to_num(out)


def strategy(df, p, sym):
    """合図: 指数は相手債券の符号、債券は相手指数の逆符号（cross）。catsmom は自分の TSMOM と一致したときだけ。shift しない。"""
    L = p["L"]; c = df["close"].values
    own = np.zeros(len(df)); own[L:] = np.sign(c[L:] - c[:-L])
    if sym in BOND_OF:
        cross = _partner_sign(df, BOND_OF[sym], L)
    elif sym in EQUITY_OF:
        cross = -_partner_sign(df, EQUITY_OF[sym], L)
    else:
        return np.zeros(len(df))
    if p["mode"] == "cross":
        return cross
    return np.where(own == cross, cross, 0.0)


def make_extra(spec):
    def _extra(cells, sp):
        from fe_core import by_year_stats, fmt
        m = cells[cells["param"] == sp.main_param]; out = {}
        for g, members in (("idx13", X.IDX13), ("bond3", X.BOND3)):
            d = m[m["sym"].isin(members)]; out[g] = {}
            for pn, (y0, y1) in {"all": (0, 9999), "pre": (0, sp.split_year), "post": (sp.split_year, 9999)}.items():
                dd = d[(d["year"] >= y0) & (d["year"] < y1)]
                if dd.empty:
                    continue
                b = by_year_stats(dd, "pnl_net", y0=y0, y1=y1)
                out[g][pn] = {"bp_net": fmt(b["mean"]), "t_year": fmt(b["t"]), "n_years": b["n_years"], "years_dropped": b["years_dropped"]}
        out["per_sym_bp_net"] = {s: fmt(float(np.nanmean(m.loc[m["sym"] == s, "pnl_net"]))) for s in sorted(m["sym"].unique())}
        return out
    return _extra


if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=12, summarize_extra=make_extra(SPEC), runner_holder=RUNNER)
