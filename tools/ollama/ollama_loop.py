#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ローカル LLM（Ollama）のループ。**Mac のターミナルで動かす**（device_bash の Linux VM からは localhost:11434 に届かない）。

  cd ~/ワークスペース/検証/verification-lab/tools/ollama
  python3 ollama_loop.py --once                 # pending を全部処理して終わる
  python3 ollama_loop.py --watch 120            # 120 秒ごとに pending を見に行く（Ctrl-C で止める）
  python3 ollama_loop.py --once --mock          # Ollama を呼ばず偽の応答で経路と検品を試す（VM でも動く）
  python3 ollama_loop.py --once --model qwen2.5:14b

ジョブは 検証/夜間/llm/pending/*.json（make_job.py が作る）。処理の流れ: running へ移す → 本文を抜く → Ollama にページ束ごとに投げる
→ 返った引用を原文と照合（実在しないものは捨てる）→ 文献/_ローカルLLM/<label>_quotes.{json,md} に書く → done へ（失敗は failed へ、理由つき）。
依存: 標準ライブラリ＋pypdf（PDF 用。無ければ pdftotext）。Ollama は http://localhost:11434。
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import traceback
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_common import JOBS, OUT_DIR, WS, ensure_dirs, move_job, extract_pages, verify_quote, glossary, now  # noqa: E402

DEFAULT_MODEL = "qwen2.5:7b"   # Mac 16GB の既定。14B（q4・約 9GB）は他のアプリを閉じて試す
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
NUM_CTX = 8192                 # 既定の 2048 では 4 ページが入らない
PAGES_PER_CALL = 3
MAX_RETRY = 2


def ollama_chat(model, system, user, mock=False, json_mode=True):
    if mock:
        return _mock(user)
    body = {"model": model, "stream": False, "options": {"temperature": 0.1, "num_ctx": NUM_CTX},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if json_mode:
        body["format"] = "json"
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


def _mock(user):
    """偽の応答: 本文の中の長い文を 2 つ、そのまま引用として返す（検品が通る）＋ 1 つは捏造（検品で落ちる）。"""
    body = user.split("=== 本文 ===", 1)[-1]
    sents = [s.strip() for s in re.split(r"(?<=[.。])\s+", body) if 80 < len(s.strip()) < 400]
    qs = [{"quote": s, "page": None, "gist_ja": "（mock の要点）", "kind": "結果"} for s in sents[:2]]
    qs.append({"quote": "This sentence does not exist in the source and must be rejected by verification.", "page": 1, "gist_ja": "捏造", "kind": "結果"})
    return json.dumps({"quotes": qs}, ensure_ascii=False)


SYSTEM_QUOTES = """あなたは金融工学の文献から「主張の候補になる文」を抜き出す係です。判断や要約はしません。
出力は JSON だけ: {"quotes": [{"quote": "<本文からの逐語の引用（1〜3 文・英語なら英語のまま・改変禁止）>", "page": <ページ番号の整数>, "kind": "<結果|方法|限界|条件>", "gist_ja": "<日本語で 1 文の要点>"}]}
抜く基準: 数値や方向（上がる・下がる・有意・有意でない）を伴う結果、データと期間、コストの扱い、著者が認める限界、成り立つ条件。
抜かない: 先行研究の紹介、一般論、著者の抱負。引用は必ず本文に実在する文字列をそのまま写すこと（言い換え・省略・結合をしない）。"""


def run_quotes(job, model, mock):
    src = os.path.join(WS, job["source"])
    pages = extract_pages(src)
    total_chars = sum(len(t) for _, t in pages)
    if total_chars < 200:
        raise RuntimeError(f"本文がほぼ空（{total_chars} 字）。スキャン PDF か取得失敗の可能性")
    focus = job.get("params", {}).get("focus") or ""
    want = int(job.get("params", {}).get("max_quotes", 12))
    accepted, rejected, calls = [], [], 0
    for i in range(0, len(pages), PAGES_PER_CALL):
        bundle = pages[i:i + PAGES_PER_CALL]
        text = "\n\n".join(f"--- p.{p} ---\n{t}" for p, t in bundle if t.strip())
        if len(text.strip()) < 100:
            continue
        user = (f"文献: {job.get('title','')}\n観点: {focus or '結果・データ・コスト・限界・条件'}\n最大 {max(2, want // max(1, len(pages) // PAGES_PER_CALL))} 件。\n=== 本文 ===\n{text}")
        for attempt in range(MAX_RETRY + 1):
            try:
                raw = ollama_chat(model, SYSTEM_QUOTES, user, mock=mock); calls += 1
                data = json.loads(raw)
                items = data.get("quotes", data if isinstance(data, list) else [])
                break
            except (json.JSONDecodeError, KeyError, TypeError):
                items = []
                if attempt == MAX_RETRY:
                    rejected.append({"reason": "JSON にならない", "pages": [p for p, _ in bundle]})
        for it in items:
            q = str(it.get("quote", "")).strip()
            ok, pno = verify_quote(q, bundle, page_hint=it.get("page"))
            rec = {"quote": q, "page": pno if ok else it.get("page"), "kind": it.get("kind", ""), "gist_ja": it.get("gist_ja", "")}
            (accepted if ok else rejected).append(rec if ok else {**rec, "reason": "本文に実在しない"})
    # 重複を除く
    seen = set(); uniq = []
    for a in accepted:
        k = re.sub(r"\s+", " ", a["quote"].lower())[:120]
        if k not in seen:
            seen.add(k); uniq.append(a)
    label = re.sub(r"[^\w\-]+", "_", job.get("label", job["id"]))[:60]
    odir = os.path.join(OUT_DIR, "_mock") if mock else OUT_DIR  # mock の出力は材料に混ぜない
    os.makedirs(odir, exist_ok=True)
    out_json = os.path.join(odir, f"{label}_quotes.json")
    out_md = os.path.join(odir, f"{label}_quotes.md")
    res = {"job": job["id"], "label": job.get("label"), "inv_id": job.get("inv_id"), "title": job.get("title"), "source": job["source"],
           "model": model if not mock else "mock", "generated": now(), "pages": len(pages), "calls": calls,
           "n_accepted": len(uniq), "n_rejected": len(rejected), "quotes": uniq, "rejected": rejected}
    json.dump(res, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = [f"# ローカルLLM 抜き出し: {job.get('title','')}", "",
         f"- 入荷台帳: {job.get('inv_id','—')} / 本文: `{job['source']}` / モデル: {res['model']} / {now()}",
         f"- 原文に実在すると照合できた引用 {len(uniq)} 件（捨てた {len(rejected)} 件）。**要点はローカル訳（未確認）。主張カードにするかの判断は人（Claude）が行う。**", ""]
    for a in uniq:
        L += [f"## p.{a['page']}（{a['kind']}）", "", f"> {a['quote']}", "", f"要点（ローカル・未確認）: {a['gist_ja']}", ""]
    if rejected:
        L += ["## 捨てたもの（照合に失敗・JSON 不良）", ""] + [f"- {r.get('reason')}: {str(r.get('quote',''))[:100]}" for r in rejected]
    open(out_md, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return {"out_json": os.path.relpath(out_json, WS), "out_md": os.path.relpath(out_md, WS), "n_accepted": len(uniq), "n_rejected": len(rejected), "calls": calls}


SYSTEM_TRANSLATE = """あなたは金融工学の英文を日本語に訳す係です。意味を足さず、原文の語順に近く、訳語表にある語は必ずその訳語を使います。
出力は JSON だけ: {"translations": [{"i": <番号>, "ja": "<訳>"}]}"""


def run_translate(job, model, mock):
    src = os.path.join(WS, job["source"])
    data = json.load(open(src, encoding="utf-8"))
    quotes = data.get("quotes", [])
    g = glossary()
    table = "\n".join(f"- {en} → {ja}" for ja, en in g.items() if en) or "（訳語表なし）"
    out = []
    for i in range(0, len(quotes), 6):
        chunk = quotes[i:i + 6]
        user = "訳語表（原語 → 訳語）:\n" + table + "\n\n原文:\n" + "\n".join(f"[{i + k}] {q['quote']}" for k, q in enumerate(chunk))
        raw = ollama_chat(model, SYSTEM_TRANSLATE, user, mock=mock) if not mock else json.dumps({"translations": [{"i": i + k, "ja": "（mock 訳）"} for k in range(len(chunk))]})
        try:
            tr = {t["i"]: t["ja"] for t in json.loads(raw)["translations"]}
        except Exception:
            tr = {}
        for k, q in enumerate(chunk):
            out.append({**q, "ja": tr.get(i + k, ""), "ja_note": "ローカル訳（未確認）"})
    label = re.sub(r"[^\w\-]+", "_", job.get("label", job["id"]))[:60]
    odir = os.path.join(OUT_DIR, "_mock") if mock else OUT_DIR
    os.makedirs(odir, exist_ok=True)
    out_json = os.path.join(odir, f"{label}_translated.json")
    json.dump({"job": job["id"], "model": model if not mock else "mock", "glossary_terms": len([1 for v in g.values() if v]), "items": out},
              open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"out_json": os.path.relpath(out_json, WS), "n": len(out)}


def process(path, model, mock):
    job = json.load(open(path, encoding="utf-8"))
    rp = move_job(path, "running", {"started": now()})
    t0 = time.time()
    try:
        m = job.get("model") or model
        if job["kind"] == "quotes":
            r = run_quotes(job, m, mock)
        elif job["kind"] == "translate":
            r = run_translate(job, m, mock)
        else:
            raise RuntimeError(f"kind が不明: {job['kind']}")
        move_job(rp, "done", {"result": r, "seconds": round(time.time() - t0, 1), "model_used": m if not mock else "mock"})
        print(f"done  {job['id']} {job.get('label')} {r}")
    except Exception as e:
        move_job(rp, "failed", {"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:], "seconds": round(time.time() - t0, 1)})
        print(f"FAIL  {job['id']} {job.get('label')}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true"); ap.add_argument("--watch", type=int, default=0)
    ap.add_argument("--model", default=DEFAULT_MODEL); ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    ensure_dirs()
    if not a.mock:
        try:
            with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=5) as r:
                names = [m["name"] for m in json.loads(r.read()).get("models", [])]
            if a.model not in names and not any(n.startswith(a.model) for n in names):
                print(f"モデル {a.model} が無い。ollama list: {names}。`ollama pull {a.model}` を実行"); sys.exit(2)
        except Exception as e:
            print(f"Ollama に届かない（{OLLAMA}）: {e}。Mac のターミナルで `ollama serve` が動いているか確認"); sys.exit(2)
    while True:
        pend = sorted(glob.glob(os.path.join(JOBS, "pending", "*.json")))
        for p in pend:
            process(p, a.model, a.mock)
        if a.once or not a.watch:
            break
        time.sleep(a.watch)


if __name__ == "__main__":
    main()
