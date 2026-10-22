#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q402 S13: 株価指数 13 の FOMC サイクル偶数週（発表日 −1〜+3・+9〜+13・+19〜+23・+29〜+33 営業日）の買い持ちは規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（封印・規程モード・FOMC の暦とサイクル日は _s1x_common/s1x.py。暦は知識から記載・実行者が原典と照合・--fomc-csv で差し替え）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s13_fomc_cycle_q402.py [--fomc-csv path]（本番 B=500）／ --readme
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec  # noqa: E402
import s1x as X  # noqa: E402

SPEC = Spec(
    qid="Q402",
    question="株価指数 13 の FOMC サイクル偶数週（定例発表日を 0 として −1〜+3・+9〜+13・+19〜+23・+29〜+33 営業日）だけ買い持ちする戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="Cieslak・Morse・Vissing-Jorgensen 2019 JF: 1994〜2016 の株式プレミアムは FOMC サイクルの偶数週にだけ発生し（奇数週は ≈0）、3 つのサブ期間と米国外の株式市場でも成り立つ（Fed の非公式な情報流出の 2 週周期）。暦（FOMC 日程）だけで決まり判断時点に既知。13 指数・2010〜封印前で偶数週買い（露出 ≈1/2）が関門を通るか。main=偶数週だけ買い、副=偶数週買い・奇数週（4〜8・14〜18・24〜28）売り",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副（long/short）・銘柄別・偶数週と奇数週の bp の差は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8",
    syms=list(X.IDX13), kind="D1_fromH1", start="2010-01-01",
    params=[{"mode": "long_even"}, {"mode": "long_even_short_odd"}], main_param=0, n_tests=2, warmup=0, per_year=252,
    B=500, null_kind="circ_shift", null_min_shift=60,
    discarded="2（週 0 を 0〜4 にずらす＝原著の −1〜3 に固定／偶数週のうち週 0 だけ＝Q401 と重なる）",
    delegation="なし（Fable 設計 → Sonnet 実行）。FOMC の暦は Claude の知識から記載（s1x.FOMC_DATES）。**実行者は federalreserve.gov と照合し、違えば --fomc-csv で差し替える**",
    source="[[検証/_基盤/戦略台帳]] 新 S13（暦）／Cieslak・Morse・Vissing-Jorgensen 2019 'Stock returns over the FOMC cycle' JF 74(5)／Lucca・Moench 2015 JF／Q401（週 0 の前半）",
    data="指数 13 の D1_fromH1（2010〜・封印 time<2024-07-01）。サイクル日は各銘柄の足で数えた直前の発表日からの営業日数（発表前日は −1）。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（週ごとの出入りで年 ≈16 往復）",
    measure="等金額: 13 指数の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈1/2）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）。extra: 偶数週・奇数週それぞれの平均日次リターン（bp）",
    null_desc="合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「FOMC cycle even weeks stock returns Cieslak Morse Vissing-Jorgensen out-of-sample after 2015 replication」: 原著（1994〜2016・国際にも）、AEA 2021 の派生（週の機構）。2016 年以後の標本外・国際 13 指数・日次 CFD・規程つきの判定は未確認（独立の追試は見つからず）",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 9 本目（S13・FOMC サイクル）", designer="Fable", coder="Fable",
    settings={"seal": str(X.SEAL.date()), "fomc_source": "s1x.FOMC_DATES（知識から記載・要照合）", "fomc_override_arg": "--fomc-csv", "s13_family_trials": "Q400〜Q403 の 4 本×2 設定＝8"},
)


def _odd_mask(c):
    m = np.zeros(len(c), bool)
    for lo, hi in ((4, 8), (14, 18), (24, 28)):
        m |= (c >= lo) & (c <= hi)
    return m


def strategy(df, p, sym):
    """合図: 足 j のサイクル日が偶数週なら足 j のリターンを取る（pos[j−1]=+1）。副は奇数週に −1。shift しない。"""
    c = X.fomc_cycle_day(df); n = len(df)
    take = X.even_week_mask(np.nan_to_num(c, nan=-99)).astype(float)
    if p["mode"] == "long_even_short_odd":
        take = take - _odd_mask(np.nan_to_num(c, nan=-99)).astype(float)
    pos = np.zeros(n); pos[:-1] = take[1:]
    return pos


def make_extra(spec):
    def _extra(cells, sp):
        from fe_core import fmt
        r = RUNNER["obj"]; ev, od = [], []
        if r is not None:
            for s, df in r.loaded.items():
                c = np.nan_to_num(X.fomc_cycle_day(df), nan=-99); ret = df["ret"].values
                ev.append(np.nanmean(ret[X.even_week_mask(c)]) * 1e4); od.append(np.nanmean(ret[_odd_mask(c)]) * 1e4)
        return {"fomc_source": X.fomc_source(), "mean_bp_even_week": fmt(float(np.nanmean(ev))) if ev else None,
                "mean_bp_odd_week": fmt(float(np.nanmean(od))) if od else None}
    return _extra


RUNNER = {"obj": None}

if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=10, summarize_extra=make_extra(SPEC), runner_holder=RUNNER)
