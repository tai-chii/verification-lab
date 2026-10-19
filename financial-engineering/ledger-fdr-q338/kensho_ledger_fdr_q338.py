#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証キュー Q338: 手元の検証の全体を1つの探索と見て、判定に使った t を集め BH／BY（q=10%）で補正すると「効果あり」のうち何本残るか
================================================================================
【出典】Chang・Chuang・Kuan (2026) "Superior or Spurious?" §2.1・§3.3（p3–4, p9）。主張カード ChangChuangKuan2026-1・2。
  計画: アイデア候補.md 2026-10-19 の行（Q336-C3、接続ログ 2026-10-19）。

【仮説】事前登録しても、何百本の検証の全体では「効果あり」の一部は偶然。BY で半分以上残るか。

【抜き出しの規則（事前固定・抜き出しの前に書いた）】
- 単位: financial-engineering/ の実験フォルダのうち README に判定（`判定: **…**`）があるもの。この Q338 自身と、判定が他の行の再判定だけのもの（例: common-perm-rejudge-q322）は、元の行と二重になるので除外（除外は理由つきで記録）。
- 効果ありの主張（positive）: README の結論（機械判定、人の解釈があれば解釈を優先）が「仮説の効果が存在する」と言うもの（支持・確定・有意・使える・効く等）。棄却・ノイズ・未確定・効果なし（帰無側の支持）・部分支持は positive=0。
  注: 「効果なしを支持」「関門は使えない」のように帰無側・否定側の結論は 0。Q333 のような較正（関門が使えない）は効果の主張でないので 0。
- 主の判定量: 事前登録の判定規則が使う t（年単位 t・NW t・日クラスタ t など）か帰無に対する z。前半・後半の両方を要求する規則なら |値| の小さいほう（拘束する側）。t と z を両方要求するなら |値| の小さいほう。
  判定規則が t/z を使わない（相関係数・比・割合だけ等）なら extractable=0（理由を記録）。
- p 値: 両側、正規近似 p = 2(1 − Φ(|v|))。
- 抜き出しは Sonnet の下請けが README を読んで行い（1フォルダ1行、根拠の原文を1行引用）、Opus が無作為10行を照合する。不一致が3行以上なら抜き出しをやり直す。

【補正と判定（事前固定・変更禁止）】
- extractable=1 の全行（positive も 0 も）の p で、BH と Benjamini–Yekutieli を q=0.10 で当てる。
- 主の量: positive=1 かつ extractable=1 のうち BY で残る割合 S_BY。
  S_BY ≥ 50% →「手元の効果ありはおおむね頑健」、S_BY < 25% →「効果ありの多くは探索の量で説明できる」、間は未確定。
- positive=1 のうち extractable=0 が 30% を超えたら判定しない（記述だけ）。
- 記述: BH での割合、出口別（FX／株／暗号資産等は README の市場から）、帰無の z だけの行と t の行の別。

【捨てた案の数】約3: 全期間の t を使う案（前後半の規則と合わない）、最大 |t| を使う案（甘くなる）、
Storey の π0 推定で FDR を出す案（行数が少なく不安定）。
【知識の締め切り】Claude はおよそ 2026-06。対象は手元の検証記録のみ。
【委託の確かめ方】抜き出し: Sonnet 4体（フォルダ名の辞書順で4分割）。照合: Opus が無作為10行（seed 20261019）。設計・補正・解釈: Opus。
【事前登録からの変更点】なし。

使い方: python3 kensho_ledger_fdr_q338.py   （results/extract_part*.csv を読み、補正して JSON を書く）
"""
import csv, glob, json, math, os, datetime as _dt
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "results"); Q = 0.10

def pval(v): return math.erfc(abs(v) / math.sqrt(2))

def bh(p, q, by=False):
    p = np.asarray(p); m = len(p); o = np.argsort(p); c = sum(1 / i for i in range(1, m + 1)) if by else 1.0
    thr = q * np.arange(1, m + 1) / (m * c); ok = p[o] <= thr
    k = np.max(np.flatnonzero(ok)) + 1 if ok.any() else 0
    rej = np.zeros(m, bool); rej[o[:k]] = True; return rej

def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "extract_part*.csv"))):
        rows += list(csv.DictReader(open(f, encoding="utf-8")))
    inc = [r for r in rows if r.get("included", "1") == "1"]
    ex = [r for r in inc if r["extractable"] == "1"]
    for r in ex: r["p"] = pval(float(r["value"]))
    p = [r["p"] for r in ex]; rb = bh(p, Q); ry = bh(p, Q, by=True)
    for r, a, b in zip(ex, rb, ry): r["BH"] = bool(a); r["BY"] = bool(b)
    pos = [r for r in inc if r["positive"] == "1"]; pos_ex = [r for r in pos if r["extractable"] == "1"]
    share_noex = 1 - len(pos_ex) / len(pos) if pos else float("nan")
    S_BY = np.mean([r["BY"] for r in pos_ex]) if pos_ex else float("nan")
    S_BH = np.mean([r["BH"] for r in pos_ex]) if pos_ex else float("nan")
    if share_noex > 0.30: verdict = "判定しない（効果ありの抜き出せない割合が30%超）"
    elif S_BY >= 0.5: verdict = "手元の効果ありはおおむね頑健"
    elif S_BY < 0.25: verdict = "効果ありの多くは探索の量で説明できる"
    else: verdict = "未確定"
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dict(question="Q338", n_rows=len(rows), n_included=len(inc), n_extractable=len(ex), n_positive=len(pos),
               n_positive_extractable=len(pos_ex), share_positive_not_extractable=share_noex,
               S_BY=S_BY, S_BH=S_BH, n_BY=int(sum(ry)), n_BH=int(sum(rb)), verdict=verdict,
               positive_rows=[{k: r.get(k) for k in ("dir", "Q", "stat_name", "value", "p", "BH", "BY")} for r in pos_ex],
               positive_not_extractable=[{k: r.get(k) for k in ("dir", "Q", "reason")} for r in pos if r["extractable"] != "1"])
    p_ = os.path.join(OUT, f"Q338_result_{stamp}.json"); json.dump(out, open(p_, "w"), ensure_ascii=False, indent=1, default=float)
    print("verdict:", verdict, "S_BY", S_BY, "S_BH", S_BH, len(pos_ex), "/", len(pos)); print(p_)

if __name__ == "__main__": main()
