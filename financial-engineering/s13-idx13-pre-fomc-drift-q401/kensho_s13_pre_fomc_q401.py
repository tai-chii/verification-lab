#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q401 S13: 株価指数 13 の FOMC 前ドリフト（発表前日と発表日の 2 本を買い持ち）は 2015 年以後も残り規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（封印・規程モード・FOMC の暦は _s1x_common/s1x.py。暦は知識から記載・実行者が原典と照合・--fomc-csv で差し替え）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s13_pre_fomc_q401.py [--fomc-csv path]（本番 B=500）／ --readme
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec  # noqa: E402
import s1x as X  # noqa: E402

SPEC = Spec(
    qid="Q401",
    question="株価指数 13 の FOMC 前ドリフト（定例発表日の前日の足と当日の足の 2 本を買い持ち・年 8 回）は 2015 年以後も残り、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="Lucca・Moench 2015 JF: 1994〜2011 の S&P500 は FOMC 発表前 24 時間に平均 +49 bp（年の超過リターンの大半）で、国際指数にも同じ山がある。Kurov・Wolfe・Gilbert 2021 FRL は 2015 年以後に米国で消えたと報告（不確実性の低下）。国際 13 指数・2010〜封印前で、前半（〜2016）に残り後半（2017〜）に消えるのが文献の予想で、関門を通るには後半も t≥2 が要る。UTC 0 時区切りの D1 では発表（14:00 ET）前 24 時間が前日足と当日足にまたがるので main=2 本（前日・当日）、副=前日 1 本",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定（文献どおり前半だけ正なら「公表後に消えた」と記述）。副 1 本・銘柄別は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8",
    syms=list(X.IDX13), kind="D1_fromH1", start="2010-01-01",
    params=[{"offsets": [-1, 0]}, {"offsets": [-1]}], main_param=0, n_tests=2, warmup=0, per_year=252,
    B=500, null_kind="circ_shift", null_min_shift=60,
    discarded="3（H1 で 14:00 ET の前 24 時間を正確に切る＝指数 13 の H1 は手元に無い／VIX 水準で条件付け＝手元に無い／ECB・BoJ の暦を足す＝暦の照合負担が増えるので FOMC だけ）",
    delegation="なし（Fable 設計 → Sonnet 実行）。FOMC の暦は Claude の知識から記載（s1x.FOMC_DATES・2010〜2026 定例のみ・2020-03 の緊急は除外）。**実行者は federalreserve.gov の FOMC calendars と照合し、違えば CSV を --fomc-csv で渡す**",
    source="[[検証/_基盤/戦略台帳]] 新 S13（暦）／Lucca・Moench 2015 'The pre-FOMC announcement drift' JF／Kurov・Wolfe・Gilbert 2021 'The disappearing pre-FOMC announcement drift' FRL／Cieslak・Morse・Vissing-Jorgensen 2019 JF",
    data="指数 13 の D1_fromH1（2010〜・封印 time<2024-07-01）。FOMC 定例発表日（s1x.FOMC_DATES・知識から記載）。発表日の足が無ければ直後の足を当日とみなす。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（年 8 往復）",
    measure="等金額: 13 指数の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈16/252）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）",
    null_desc="合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「pre-FOMC announcement drift disappeared after 2015 international stock indices Lucca Moench Kurov」: 原著（国際指数にも山・Treasury には無し）、Kurov ほか 2021（米国で 2015 以後消失）、quantpedia（IV 高の時だけ 109 bp）。国際 13 指数の 2015 年以後・D1 近似・規程つきの判定は未確認",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 8 本目（S13・FOMC 前）", designer="Fable", coder="Fable",
    settings={"seal": str(X.SEAL.date()), "fomc_source": "s1x.FOMC_DATES（知識から記載・要照合）", "fomc_override_arg": "--fomc-csv", "s13_family_trials": "Q400〜Q403 の 4 本×2 設定＝8"},
)


def strategy(df, p, sym):
    """合図: FOMC 発表日の足 j に対し offsets（−1=前日・0=当日）の足のリターンを取る +1。shift しない。"""
    return X.hold_bars_pos(df, X.fomc_day_index(df), p["offsets"])


def make_extra(spec):
    def _extra(cells, sp):
        return {"fomc_source": X.fomc_source(), "n_fomc_dates": int(len(X.fomc_dates()))}
    return _extra


if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=10, summarize_extra=make_extra(SPEC))
