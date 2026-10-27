#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ローカル LLM のジョブを作る（Claude 側・device_bash から）。実行は Mac の ollama_loop.py。

例:
  python3 make_job.py quotes --inv 95                  # 入荷台帳 ID95 の本文（PDF/Web保存）から主張候補の引用を抜く
  python3 make_job.py quotes --src 検証/学問/金融工学/知識/文献/PDF/xxx.pdf --label Korzan2026
  python3 make_job.py translate --from-quotes <done ジョブの出力 .json>   # 抜いた引用を訳語表に揃えて訳す
  python3 make_job.py list                             # 状態ごとの件数と pending の一覧
"""
import argparse
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_common import JOBS, BUNKEN, WS, STATES, ensure_dirs, write_job, now, _p  # noqa: E402


def find_source(inv_id):
    """入荷台帳の行から本文ファイルを探す（PDF/ か Web保存/ にタイトルの一部で当たるもの）。見つからなければ候補を表示して止まる。"""
    rows = list(csv.DictReader(open(os.path.join(BUNKEN, "入荷台帳.csv"), encoding="utf-8")))
    row = next((r for r in rows if r["ID"] == str(inv_id)), None)
    if not row:
        sys.exit(f"入荷台帳に ID {inv_id} が無い")
    title = row["タイトル"]
    import re as _re
    stop = {"with", "from", "that", "this", "does", "when", "where", "which", "their", "into", "about", "under", "over", "between",
            # 2026-10-27: 分野の一般語は当たりの根拠にしない（ID194 が intraday・trading だけで Neely-Weller 1999 に、ID161 が strategy・selection で Zenn 記事に当たっていた）
            "trading", "trade", "market", "markets", "strategy", "strategie", "financial", "finance", "intraday", "backtest",
            "test", "live", "data", "stock", "research", "study", "forecasting", "forecast", "selection", "returns", "return", "evidence"}
    words = [w for w in _re.findall(r"[A-Za-z][A-Za-z\-]{3,}", title) if w.lower() not in stop]  # 4 文字以上・略語（HSAT 等）も拾う
    words = [w[:-1] if len(w) > 4 and w.lower().endswith("s") else w for w in words]  # 複数形の s を落とす（tests → test）
    # 2026-10-27: 著者の姓で加点（ID87 が題の語「reality check」だけで White 2000 の PDF に当たった。要対応 2026-10-17）
    head = (row.get("要旨") or "")[:160]
    authors = [a for a in _re.findall(r"\b([A-Z][a-z]{3,})\b", head.split("20")[0]) if a.lower() not in stop]
    # arXiv の行は、ファイル名に arXiv の番号が入っているものだけを本文とみなす（無ければ URL から取らせる）
    ax = _re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", row.get("URL", ""))
    if ax:
        hit = [f for sub in ("PDF", "Web保存") for f in glob.glob(os.path.join(BUNKEN, sub, "*")) if ax.group(1) in os.path.basename(f)]
        mp = os.path.join(BUNKEN, "_ローカルLLM", "_sources.json")
        m = json.load(open(mp, encoding="utf-8")).get(str(inv_id)) if os.path.exists(mp) else None
        if m and os.path.exists(os.path.join(WS, m)):
            return row, os.path.join(WS, m)
        return row, (hit[0] if hit else None)
    cands = []
    for sub in ("PDF", "Web保存"):
        for f in glob.glob(os.path.join(BUNKEN, sub, "*")):
            base = os.path.basename(f).lower().replace("-", "").replace("_", "")
            score = sum(w.lower().replace("-", "") in base for w in words)
            score += 2 * sum(a.lower() in base for a in authors)
            if score:
                cands.append((score, f))
    cands.sort(reverse=True)
    # 以前の取得で保存した対応表（inv_id → パス）
    mp = os.path.join(BUNKEN, "_ローカルLLM", "_sources.json")
    if os.path.exists(mp):
        m = json.load(open(mp, encoding="utf-8")).get(str(inv_id))
        if m and os.path.exists(os.path.join(WS, m)):
            return row, os.path.join(WS, m)
    tie = len(cands) > 1 and cands[0][0] == cands[1][0]  # 1 位が並ぶときは選ばない（取り違えを防ぐ）
    if not cands or cands[0][0] < 2 or tie:
        if row.get("URL", "").startswith("http"):
            return row, None  # 本文は Mac 側の loop が URL から取る
        print("本文ファイルを特定できない。候補:", [os.path.basename(c[1]) for c in cands[:5]])
        print("--src でパスを指定する"); sys.exit(2)
    return row, cands[0][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["quotes", "translate", "list"])
    ap.add_argument("--inv", type=int, help="入荷台帳の ID")
    ap.add_argument("--src", help="本文ファイル（ワークスペースからの相対パスか絶対パス）")
    ap.add_argument("--label", help="出力名（省略で入荷台帳の ID か ファイル名）")
    ap.add_argument("--from-quotes", help="translate: quotes ジョブの出力 JSON")
    ap.add_argument("--model", default=None, help="Ollama のモデル名（省略でループ側の既定）")
    ap.add_argument("--max-quotes", type=int, default=12)
    ap.add_argument("--focus", default="", help="抜き出しの観点を 1 文で（例: 取引コスト後の収益・公表後の減衰）")
    a = ap.parse_args()
    ensure_dirs()
    if a.kind == "list":
        for s in STATES:
            fs = sorted(glob.glob(os.path.join(JOBS, s, "*.json")))
            print(f"{s}: {len(fs)}")
            if s in ("pending", "running", "failed"):
                for f in fs:
                    j = json.load(open(f, encoding="utf-8")); print("  ", j["id"], j["kind"], j.get("label"), j.get("error", "")[:80])
        return
    job = {"id": f"llm_{now()}_{a.kind}_{a.inv or os.getpid()}", "kind": a.kind, "model": a.model, "created": now(), "params": {}}
    if a.kind == "quotes":
        if a.inv:
            row, src = find_source(a.inv)
            job["inv_id"] = a.inv; job["label"] = a.label or f"ID{a.inv}"
            job["title"] = row["タイトル"]; job["source_kind"] = row["出典種別"]
        elif a.src:
            src = a.src if os.path.isabs(a.src) else os.path.join(WS, a.src)
            job["label"] = a.label or os.path.splitext(os.path.basename(src))[0][:40]
            job["title"] = job["label"]; job["source_kind"] = ""
        else:
            sys.exit("--inv か --src が必要")
        if src is None:
            job["source"] = None; job["url"] = row["URL"]
        elif not os.path.exists(src):
            sys.exit(f"本文が無い: {src}")
        else:
            job["source"] = os.path.relpath(src, WS)
        job["params"] = {"max_quotes": a.max_quotes, "focus": a.focus}
    elif a.kind == "translate":
        if not a.from_quotes:
            sys.exit("--from-quotes が必要")
        src = a.from_quotes if os.path.isabs(a.from_quotes) else os.path.join(WS, a.from_quotes)
        q = json.load(open(src, encoding="utf-8"))
        job["label"] = a.label or q.get("label", "translate"); job["source"] = os.path.relpath(src, WS)
    path = write_job(job)
    print("作成:", os.path.relpath(path, WS))
    print("Mac で実行: cd ~/ワークスペース/検証/verification-lab/tools/ollama && python3 ollama_loop.py --once")


if __name__ == "__main__":
    main()
