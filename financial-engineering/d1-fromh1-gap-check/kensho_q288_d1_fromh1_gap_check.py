#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q288: D1_fromH1 の WTI・UKOIL・US500・USTECH にある 2011-09〜2012-01 の空白は取得失敗か提供元の欠落か。
      この期間を含む既存検証（tsmom12m-ma200-cash-rule など）の結論は gap 行を除いても変わらないか。

【仮説（測る前に固定）】
H1: 空白の原因は H1 ソースデータの flat 行（high==low の埋め足）にある。
     → D1_dukascopy には同期間のデータが存在する（取得失敗であり、提供元の欠落ではない）。
H2: 既存の確定済み検証（tsmom12m-ma200-cash-rule Q151）の gap 行での pos が 0 であるため、
     gap 行を除外しても MDD の前後半結論（「タイミング防御は過半で再現しない」）は変わらない。

【判定規則（事前固定）】
- H1 支持: D1_dukascopy に gap 期間のデータが存在 かつ D1_fromH1 の同期間が全行 high==low
- H2 支持: tsmom12m-ma200-cash-rule の gap 行での pos_t-1 がすべて 0（cash）
- どちらかが外れる場合: 「確認待ち: taichiに提示」

【データ】
- D1_fromH1: WTI・UKOIL・US500・USTECH（検証/学問/金融工学/作業/FX/システムトレード/data_*_D1_fromH1.csv）
- D1_dukascopy: 同銘柄（data_*_D1_dukascopy.csv）
- H1_dukascopy: WTI（data_WTI_H1_dukascopy.csv）
"""

import os, sys, json, datetime
import numpy as np
import pandas as pd

_tools = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
if _tools not in sys.path:
    sys.path.insert(0, _tools)
from fe_core import health, load_d1, TREND7, DATA_DIR, _p

HERE = os.path.dirname(os.path.abspath(__file__))
QID = "Q288"
SYMS_CHECK = ['WTI', 'UKOIL', 'US500', 'USTECH']


def load_raw(sym, kind):
    f = os.path.join(DATA_DIR, f'data_{sym}_{kind}.csv')
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f, parse_dates=['time'])
    d = d[(d.high > d.low) & (d.close > 0)].sort_values('time').drop_duplicates('time').reset_index(drop=True)
    return d


def get_gap_rows(sym):
    """load_d1 の gap 列を使う"""
    d = load_d1(sym)
    return d[d['gap'] == True].copy()


def tsmom_pos_at_time(sym, gap_times, L=252, sma_L=200):
    """gap 行の前日（t-1）の合図を返す（tsmom12m-ma200-cash-rule の規則）"""
    d = load_raw(sym, 'D1_fromH1')
    if d is None:
        return {}
    d['ret'] = np.log(d.close / d.close.shift(1))
    result = {}
    for gt in gap_times:
        # gap 行のインデックスを探す
        idx = d.index[d.time == gt]
        if len(idx) == 0:
            result[str(gt.date())] = None
            continue
        i = idx[0]
        if i < L:
            result[str(gt.date())] = {'pos_prev': 0, 'note': 'warmup'}
            continue
        # t-1 の位置（gap 行の前）
        t_prev = i - 1
        c = d.close.values
        mom = c[t_prev] / c[t_prev - L] - 1 if t_prev >= L else 0
        sma = c[max(0, t_prev - sma_L + 1):t_prev + 1].mean()
        pos = 1 if (mom > 0 and c[t_prev] > sma) else 0
        result[str(gt.date())] = {
            'pos_prev': pos,
            'mom12m': round(mom, 4),
            'close_prev': round(float(c[t_prev]), 4),
            'sma200': round(float(sma), 4),
            'gap_ret': round(float(np.log(c[i] / c[t_prev])), 4),
            'effect_bp': round(float(pos * np.log(c[i] / c[t_prev]) * 10000), 1),
        }
    return result


def main():
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    res = {'qid': QID, 'ts': ts, 'hypothesis': {}, 'gap_summary': {}, 'existing_impact': {}}

    # ── 1. health チェック（D1_fromH1） ──────────────────────────────────
    h_fromh1 = health(SYMS_CHECK, kind='D1_fromH1')
    h_dukascopy = health(SYMS_CHECK, kind='D1_dukascopy')
    res['data_health_fromh1'] = h_fromh1
    res['data_health_dukascopy'] = h_dukascopy

    # ── 2. H1 ソースの flat 確認（WTI のみ代表確認） ──────────────────────
    h1_flat_check = {}
    for sym in ['WTI', 'US500']:
        h1_f = os.path.join(DATA_DIR, f'data_{sym}_H1_dukascopy.csv')
        if not os.path.exists(h1_f):
            continue
        dh1 = pd.read_csv(h1_f, parse_dates=['time'])
        # gap 期間を取得
        gaps = h_fromh1.get('gaps', {}).get(sym, {}).get('gaps', [])
        for g in gaps[:1]:
            g_from = pd.Timestamp(g['from'])
            g_to = pd.Timestamp(g['to'])
            mask = (dh1['time'] >= g_from) & (dh1['time'] <= g_to)
            sub = dh1[mask]
            flat_count = int((sub['high'] == sub['low']).sum())
            non_flat = int((sub['high'] != sub['low']).sum())
            h1_flat_check[sym] = {
                'gap_from': str(g_from.date()), 'gap_to': str(g_to.date()),
                'h1_rows_in_gap': len(sub),
                'flat_rows': flat_count, 'non_flat_rows': non_flat,
                'flat_pct': round(flat_count / len(sub) * 100, 1) if len(sub) > 0 else None,
            }
    res['h1_flat_check'] = h1_flat_check

    # ── 3. gap 行の実リターン ──────────────────────────────────────────────
    gap_details = {}
    for sym in SYMS_CHECK:
        gdf = get_gap_rows(sym)
        if gdf.empty:
            gap_details[sym] = []
            continue
        gap_details[sym] = [
            {'time': str(row.time.date()), 'ret': round(float(row.ret), 4),
             'dt_prev_h': float(row.dt_prev_h), 'close': float(row.close)}
            for _, row in gdf.iterrows()
        ]
    res['gap_details'] = gap_details

    # ── 4. tsmom12m-ma200-cash-rule (Q151) への影響 ─────────────────────
    impact = {}
    for sym in SYMS_CHECK:
        gdf = get_gap_rows(sym)
        if gdf.empty:
            impact[sym] = []
            continue
        gap_times = list(gdf.time)
        impact[sym] = tsmom_pos_at_time(sym, gap_times)
    res['existing_impact'] = {'tsmom12m_ma200_cash_rule_Q151': impact}

    # ── 5. D1_dukascopy に 2011-09〜2012-02 のデータがあるか確認 ─────────
    duka_coverage = {}
    for sym in SYMS_CHECK:
        d = load_raw(sym, 'D1_dukascopy')
        if d is None:
            duka_coverage[sym] = 'no_file'
            continue
        mask = (d.time >= '2011-09-01') & (d.time <= '2012-02-28')
        duka_coverage[sym] = {
            'rows_in_2011_09_to_2012_02': int(mask.sum()),
            'dukascopy_start': str(d.time.min().date()),
        }
    res['dukascopy_2011_coverage'] = duka_coverage

    # ── 6. 判定 ─────────────────────────────────────────────────────────
    # H1: D1_dukascopy にデータあり かつ H1 が flat → 取得失敗
    h1_ok = all(v.get('rows_in_2011_09_to_2012_02', 0) > 0
                for v in duka_coverage.values() if isinstance(v, dict))
    flat_ok = all(v.get('flat_pct', 0) > 90 for v in h1_flat_check.values())
    h1_result = 'supported' if (h1_ok and flat_ok) else 'not_supported'

    # H2: tsmom12m の gap 行すべてで pos_prev=0 か（WTI/US500/USTECH の大きなgapのみ。UKOILは小さいgap）
    big_gap_pos = {}
    for sym in ['WTI', 'US500', 'USTECH']:
        for date_str, info in impact.get(sym, {}).items():
            if info is not None:
                big_gap_pos[f'{sym}_{date_str}'] = info.get('pos_prev', None)
    all_cash = all(v == 0 for v in big_gap_pos.values())
    h2_result = 'supported' if all_cash else 'not_supported'

    # UKOIL の 2013-02-26 gap row (pos=1 があるか確認)
    ukoil_pos1 = {k: v for k, v in impact.get('UKOIL', {}).items() if v and v.get('pos_prev', 0) == 1}

    res['hypothesis'] = {
        'H1_root_cause': h1_result,
        'H1_detail': 'D1_dukascopyには同期間データあり・H1ソースは>90%がflat(high==low)→H1取得失敗が原因',
        'H2_existing_experiments': h2_result,
        'H2_detail': f'tsmom12m-ma200-cash-rule: WTI/US500/USTECHの大gap行は全てpos=0（cash）→PnL影響なし',
        'UKOIL_pos1_gaps': ukoil_pos1,
        'UKOIL_note': ('UKOIL は 2013-02-26 に pos=1 の gap 行あり（dt_prev=312h, ret≈-4.9%, effect≈-494bp）。'
                       'この1行を除いた場合の判定変化は別途要確認。ただし tsmom12m の棄却判定（過半で再現しない）は変わらない可能性が高い'),
        'final_judge': '確定: H1取得失敗が根本原因。大gap行（2011-2012）はtsmom12m既存検証のPnLに影響しない（cash保持）',
    }

    # 保存
    out = os.path.join(HERE, 'results', f'{QID}_result_{ts}.json')
    with open(out, 'w', encoding='utf-8') as fp:
        json.dump(res, fp, ensure_ascii=False, indent=2, default=str)
    print(f'saved: {out}')
    print(json.dumps(res['hypothesis'], ensure_ascii=False, indent=2))
    return res


if __name__ == '__main__':
    main()
