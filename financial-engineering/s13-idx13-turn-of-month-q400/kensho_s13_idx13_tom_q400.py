#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q400 S13: 株価指数 13 の D1 月替わり効果（最終営業日〜翌月第 3 営業日の買い持ち）は 2010 年以後も残り規程モードの関門を通るか。
事前登録の正本は SPEC。Runner 型（封印・規程モード・月替わりの数え方は _s1x_common/s1x.py）。
実行: --smoke --B 5（経路確認）／ python3 kensho_s13_idx13_tom_q400.py（本番 B=500）／ --readme
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "_s1x_common"))
from fe_core import Spec  # noqa: E402
import s1x as X  # noqa: E402

SPEC = Spec(
    qid="Q400",
    question="株価指数 13 の D1 月替わり効果（各銘柄の足で数えた月の最終営業日と翌月の最初の 3 営業日の 4 本だけ買い持ち）は 2010 年以後も残り、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か",
    hypothesis="McConnell・Xu 2008 FAJ: 米株の超過リターンは月替わり 4 日（−1〜+3）に集中し、国際指数にもある（Lakonishok・Smidt 1988 の窓）。Etula ほか 2020 RFS は月末の資金需要（dash for cash）を機構にする。暦は入力基準で明示的に可のデータ源で、手元の過去検証は Girgin の「前倒し窓」（Q181・Q284〜Q286）だけで古典窓そのものの関門判定は無い。13 指数を同じ暦で持てば月 4 日×13 本の露出で規程モードの t が出るか。main=(−1,+3)。副=(−4,+3)（前倒し窓を含めた参照）",
    reject_if="支持: 規程モード（RULES_FINTOKEI・封印前・境 2017）の前後半とも年単位 t≥2 かつ max_dd≥−6%、かつ等金額（Runner main）の全期間 z≥2（循環シフト帰無）。棄却: 等金額の全期間 z<1、または規程モードの t_all<0。ほか → 未確定。副窓・銘柄別は記述。S13 の族内試行は Q400〜Q403 の 4 本×2 設定＝8",
    syms=list(X.IDX13), kind="D1_fromH1", start="2010-01-01",
    params=[{"last": 1, "first": 3}, {"last": 4, "first": 3}], main_param=0, n_tests=2, warmup=0, per_year=252,
    B=500, null_kind="circ_shift", null_min_shift=60,
    discarded="3（月末前の空売り（dash for cash の負の窓）＝窓の位置が文献で一定でない／FX・商品を足す＝Q286 で株固有と判明／暦日で数える＝休場日で崩れる）",
    delegation="なし（Fable 設計 → Sonnet 実行）",
    source="[[検証/_基盤/戦略台帳]] 新 S13（暦）／McConnell・Xu 2008 'Equity returns at the turn of the month' FAJ／Lakonishok・Smidt 1988 RFS／Etula・Rinne・Suominen・Vaittinen 2020 'Dash for cash' RFS／Q181・Q285・Q286（前倒し窓は見えない・株固有）",
    data="指数 13 の D1_fromH1（US500・UK100・JPN225 等は 2010〜、GER40 等は 2013-09〜・封印 time<2024-07-01・_データ/raw/D1）。営業日は各銘柄の足で数える。コスト: US500/USTECH は COST_RT、他は spread_<sym>.csv の中央値（月 1 往復）",
    measure="等金額: 13 指数の年単位平均 bp（コスト 0／後）・年単位 t・束ねた t・Sharpe・最大下落・露出（≈4/21）。規程モード: t_all/t_pre/t_post・max_dd・worst_day・stops（全設定）",
    null_desc="合図の循環シフト（min_shift=60・B=500）→ 等金額の年単位 bp（net）の帰無分布（全期間・前半・後半）→ z・perm_p・Holm（m=2）",
    prior_art="WebSearch 2026-10-22「turn-of-the-month effect international stock indices after 2010 out-of-sample McConnell Xu Etula dash for cash」: Aalto 修士論文（43 か国 1990〜2012・37 か国で検出・サブ期間で米・スイス等は消失）、SSRN 2011（マレーシア・韓国・日本）、20 か国 GARCH 研究。2010 年以後の 13 指数 CFD・日次・規程つきの判定は未確認。修士論文は参考にとどめる",
    batch="/lab-plan ターミナル版 2026-10-22 夜・N=10 の 7 本目（S13・月替わり）", designer="Fable", coder="Fable",
    settings={"seal": str(X.SEAL.date()), "s13_family_trials": "Q400〜Q403 の 4 本×2 設定＝8"},
)


def strategy(df, p, sym):
    """合図: 月の最後の last 営業日と翌月の最初の first 営業日のリターンを取る +1。shift しない（s1x.tom_offsets_pos が pos[j−1] に置く）。"""
    return X.tom_offsets_pos(df, last=p["last"], first=p["first"])


if __name__ == "__main__":
    X.run_main(SPEC, strategy, HERE, min_syms=10)
