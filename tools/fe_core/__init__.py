# -*- coding: utf-8 -*-
"""fe_core — 金融工学の検証スクリプトの共通の土台（2026-10-13 作成）。

雛形（kensho_*_q089〜q286 の「共通の土台ここまで」より上）を切り出したもの。数値の挙動は変えていない
（例外は README の「雛形との違い」。2026-10-13 に Opus の監査を受けて 0.2.0 で固定）。

使い方（検証スクリプトの冒頭）:
    import os, sys
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))   # financial-engineering/<実験>/ から
    from fe_core import *                                           # 雛形と同じ名前がそのまま使える

変更禁止: ここは「固定された土台」。検証ごとの戦略・判定は各スクリプトに書く。土台を変えるときは
tools/fe_core/README.md の手順（既存検証との数値一致を確かめる）に従う。
"""
from ._paths import WS, _p, DATA_DIR, FX8, FX6, TREND7, SYMS, CRYPTO, SPLIT_YEAR, SEED, GROUPS, script_dir
from .costs import COST_RT, CRYPTO_COST_RT_REL, cost_bp_oneway, pnl_bp
from .data import (_read, load_d1, load_csv, load_h1, h1_to_d1, _smoke_ohlc, exists_sym, syms_available,
                   check_gaps, health)
from .signals import tsmom_pos, sma_pos, atr, rsi
from .metrics import tstat, nw_t, spearman, max_drawdown, sharpe_ann, sharpe_ann_n, qlike, by_year_stats, cluster_t, f, fmt
from .multiple import z_of, perm_p, null_summary, null_degenerate, perm_within, perm_dates_within, block_perm, circ_shift, holm, holm_sig
from .io import parse_args, write_result, sanitize, _json_default
from .runner import Spec, Runner, default_judge
from .readme import render_readme, render_idea_row

__version__ = "0.2.0"  # 2026-10-13 Opus レビュー反映・固定
__all__ = [
    "WS", "_p", "DATA_DIR", "FX8", "FX6", "TREND7", "SYMS", "CRYPTO", "SPLIT_YEAR", "SEED", "GROUPS", "script_dir",
    "COST_RT", "CRYPTO_COST_RT_REL", "cost_bp_oneway", "pnl_bp",
    "_read", "load_d1", "load_csv", "load_h1", "h1_to_d1", "_smoke_ohlc", "exists_sym", "syms_available", "check_gaps", "health",
    "tsmom_pos", "sma_pos", "atr", "rsi",
    "tstat", "nw_t", "spearman", "max_drawdown", "sharpe_ann", "sharpe_ann_n", "qlike", "by_year_stats", "cluster_t", "f", "fmt",
    "z_of", "perm_p", "null_summary", "null_degenerate", "perm_within", "block_perm", "circ_shift", "holm", "holm_sig",
    "parse_args", "write_result", "sanitize", "_json_default",
    "Spec", "Runner", "default_judge", "render_readme", "render_idea_row",
]
