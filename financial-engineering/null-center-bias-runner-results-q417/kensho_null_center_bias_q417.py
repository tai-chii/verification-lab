#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q417 基盤: Runner 型の既存結果 JSON を横断し、循環シフト帰無の中心（q025 と q975 の中点）が 0 から 0.5σ 以上ずれる割合と、そのずれが z と年単位 t の食い違いを説明するか。

【出典】[[検証/_基盤/知識/検証方法論/失敗パターン集]] 2026-10-22「循環シフト帰無の z が、合図ゼロの区間や片寄った露出で膨らむ（Q394/Q407・Q395）」／要対応 2026-10-22 14:39（fe_core に帰無の中央値・null_biased を足す提案）／Jesse・fynance のブートストラップ文書（帰無を 0 に中心化してから p を読む）
【仮説】循環シフトは合図の自己相関を保つが、合図が片寄る（買い持ちが多い・ゼロ区間が長い）とドリフトのある銘柄では帰無の中心が 0 から離れる。離れた帰無で測った z は年単位 t と食い違う（Q395: z 2.75 対 t 0.66）。これが Runner 型の結果の 2 割以上で起きているなら fe_core の変更（中心のずれの報告・中心化した z の併記）が要る。
【データ】`financial-engineering/*/results/Q*_result_*.json`（smoke_ を除く・フォルダごとに最新 1 本）のうち main.{all,pre,post} に null_q025・null_q975・z・t_year・bp_net・exposure がある Runner 型の結果（2026-10-13 の fe_core 以降）。市場データは読まない。
【定義】帰無の中心 c＝(q025+q975)/2、帰無の σ̂＝(q975−q025)/3.92、ずれ r＝c/σ̂。食い違い d＝z − t_year（どちらも標準化された統計量で、帰無が 0 中心・年単位 t と同じ分散なら近い）。
【測るもの】(1) |r|≥0.5 の割合（期間別 all/pre/post と全体）。(2) Spearman(r, d) とその並べ替え p（B=2000・r を結果間で並べ替え）。(3) 露出 exposure と |r| の Spearman。(4) r が最も大きい 10 件の一覧（qid・期間・r・z・t_year）。
【帰無】r を結果間で並べ替え（B 回）→ Spearman(r, d) の帰無分布 → perm_p（両側）。
【判定（事前固定・変更禁止）】支持（仕組みの変更が要る）: |r|≥0.5 の割合 ≥0.20、または Spearman(r, d) ≥0.5 かつ perm_p<0.05。棄却: 割合 <0.05 かつ |Spearman|<0.2。ほか → 未確定。
【捨てた案の数】1（各検証を再実行して帰無の全分布を取る＝重い。中点と幅で近似する）。
【知識の締め切り】Claude の知識の締め切りはおよそ 2026-06。
【委託の確かめ方】なし（Fable 設計 → Sonnet 実行）。
【実装】fe_core（spearman・perm_p・write_result）。--smoke は同じ計算を smoke_ 接頭辞で保存するだけ（合成データは無い）。
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from fe_core import spearman, parse_args, write_result, fmt  # noqa: E402

QID = "Q417"
FE = os.path.join(HERE, "..")


def _latest_results():
    out = []
    for folder in sorted(glob.glob(os.path.join(FE, "*", "results"))):
        fs = [f for f in glob.glob(os.path.join(folder, "Q*_result_*.json")) if not os.path.basename(f).startswith("smoke_")]
        if not fs:
            continue
        out.append(max(fs, key=os.path.getmtime))
    return out


def run(args, rng):
    rows = []; n_files = 0; n_runner = 0
    files = _latest_results()
    if args.smoke:
        files = files[-8:]   # 経路確認だけ（本番の答えを出さない。新しい 8 フォルダ＝Runner 型の形を持つもの）
    for f in files:
        n_files += 1
        try:
            r = json.load(open(f, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        main = r.get("main") or {}
        if not isinstance(main, dict) or "all" not in main or not isinstance(main.get("all"), dict) or "null_q025" not in main["all"]:
            continue
        n_runner += 1
        for pn in ("all", "pre", "post"):
            b = main.get(pn)
            if not isinstance(b, dict):
                continue
            q0, q1, z, t = b.get("null_q025"), b.get("null_q975"), b.get("z"), b.get("t_year")
            if None in (q0, q1, z, t) or q1 <= q0:
                continue
            c = (q0 + q1) / 2; sd = (q1 - q0) / 3.92
            rows.append({"qid": r.get("qid"), "folder": os.path.basename(os.path.dirname(os.path.dirname(f))), "period": pn, "center": c, "null_sd": sd, "r": c / sd,
                         "z": z, "t_year": t, "d": z - t, "bp_net": b.get("bp_net"), "exposure": b.get("exposure"), "null_kind": (r.get("spec") or {}).get("null_kind")})
    df = pd.DataFrame(rows)
    if df.empty:
        return {"n_files": n_files, "n_runner_results": n_runner, "machine_verdict": "未確定: 対象の結果が無い"}, {"rows": df}
    frac = {pn: fmt(float((d["r"].abs() >= 0.5).mean())) for pn, d in df.groupby("period")}
    frac_all = float((df["r"].abs() >= 0.5).mean())
    rho = spearman(df["r"].values, df["d"].values); rho_exp = spearman(df["r"].abs().values, df["exposure"].values)
    B = int(args.B); null = np.array([spearman(rng.permutation(df["r"].values), df["d"].values) for _ in range(B)]) if B > 0 else np.array([])
    p = float((1 + np.sum(np.abs(null) >= abs(rho))) / (B + 1)) if B > 0 else None
    top = df.reindex(df["r"].abs().sort_values(ascending=False).index).head(10)[["qid", "period", "r", "z", "t_year", "exposure", "bp_net"]]
    if frac_all >= 0.20 or (rho is not None and rho >= 0.5 and p is not None and p < 0.05):
        verdict = "支持（仕組みの変更が要る）: 帰無の中心のずれ |r|≥0.5 が 2 割以上、または r と z−t の相関 ≥0.5 で有意"
    elif frac_all < 0.05 and (rho is None or abs(rho) < 0.2):
        verdict = "棄却: ずれは 5% 未満で z−t とも無相関"
    else:
        verdict = "未確定"
    return {"question": __doc__.splitlines()[0].split(": ", 1)[-1], "n_files": n_files, "n_runner_results": n_runner, "n_rows": int(len(df)),
            "frac_abs_r_ge_0_5": {"all_rows": fmt(frac_all), **frac}, "r_quantiles": {k: fmt(v) for k, v in df["r"].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).items()},
            "spearman_r_vs_z_minus_t": fmt(rho), "perm_p_two_sided": fmt(p), "B": B, "spearman_abs_r_vs_exposure": fmt(rho_exp),
            "by_null_kind": {str(k): {"n": int(len(d)), "frac": fmt(float((d["r"].abs() >= 0.5).mean()))} for k, d in df.groupby("null_kind", dropna=False)},
            "top10": top.round(3).to_dict(orient="records"), "machine_verdict": verdict}, {"rows": df}


if __name__ == "__main__":
    args = parse_args(default_B=2000)
    rng = np.random.default_rng(args.seed)
    res, csvs = run(args, rng)
    print("machine_verdict:", res["machine_verdict"], "| rows", res.get("n_rows"))
    write_result(QID, res, args.smoke, csvs, here=HERE)
