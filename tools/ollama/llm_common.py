# -*- coding: utf-8 -*-
"""ローカル LLM（Ollama）ジョブの共通部: パス・ジョブの読み書き・本文の抽出・引用の照合。
Mac のターミナル（ollama_loop.py）と、Claude 側の device_bash（make_job.py）の両方から使う。"""
import json
import os
import re
import subprocess
import unicodedata
import datetime as _dt

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # tools/ollama → tools → verification-lab → 検証 → ワークスペース


def _p(*parts):
    a = os.path.join(WS, *parts)
    if os.path.exists(a):
        return a
    b = os.path.join(WS, *[unicodedata.normalize("NFD", x) for x in parts])
    return b if os.path.exists(b) else a


JOBS = _p("検証", "自動実行", "llm")
STATES = ("pending", "running", "done", "failed")
BUNKEN = _p("検証", "学問", "金融工学", "知識", "文献")
GAINEN = _p("検証", "_基盤", "知識", "概念")
OUT_DIR = os.path.join(BUNKEN, "_ローカルLLM")  # 抜き出し・訳の置き場（論文ノートではない。材料）


def ensure_dirs():
    for s in STATES:
        os.makedirs(os.path.join(JOBS, s), exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)


def now():
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def write_job(job):
    ensure_dirs()
    path = os.path.join(JOBS, "pending", job["id"] + ".json")
    with open(path, "x", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=1)
    return path


def move_job(path, to, extra=None):
    job = json.load(open(path, encoding="utf-8"))
    if extra:
        job.update(extra)
    dst = os.path.join(JOBS, to, os.path.basename(path))
    os.replace(path, dst)  # 移動（削除ではなく rename。device_bash の VM でも通る）
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=1)
    return dst


# ----------------------------------------------------------------------------- 本文の抽出
def extract_pages(src):
    """PDF / md / txt / html → [(page_no, text)]。PDF は pypdf → pdftotext の順に試す。md 等は 1 ページ扱い（見出しで区切らない）。"""
    ext = os.path.splitext(src)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            r = PdfReader(src)
            return [(i + 1, (pg.extract_text() or "")) for i, pg in enumerate(r.pages)]
        except ImportError:
            pass
        try:
            out = subprocess.run(["pdftotext", "-layout", src, "-"], capture_output=True, text=True, check=True).stdout
            return [(i + 1, t) for i, t in enumerate(out.split("\f")) if t.strip()]
        except Exception as e:
            raise RuntimeError(f"PDF を読めない（pypdf も pdftotext も無い）: {e}。Mac で `pip3 install --user pypdf` を実行")
    text = open(src, encoding="utf-8", errors="replace").read()
    if ext in (".html", ".htm"):
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
    # 長い md は 3000 字ごとに疑似ページにする（照合の単位）
    chunk = 3000
    return [(i + 1, text[i * chunk:(i + 1) * chunk]) for i in range((len(text) + chunk - 1) // chunk)] or [(1, "")]


def norm(s):
    """照合用の正規化: 全角→半角、空白・改行・ハイフン改行を潰す、引用符を揃える、小文字。"""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("-\n", "").replace("‐\n", "")
    s = re.sub(r"[‘’]", "'", s); s = re.sub(r"[“”]", '"', s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def verify_quote(quote, pages, page_hint=None):
    """引用が本文に実在するか。返り値: (ok, page_no)。page_hint の前後 1 ページを先に見る。
    完全一致（正規化後）→ ok。なければ、引用の先頭 60 字と末尾 60 字が同じページにあれば ok（OCR の揺れ対策）。"""
    q = norm(quote)
    if len(q) < 20:
        return False, None
    order = list(pages)
    if page_hint:
        order.sort(key=lambda pt: abs(pt[0] - page_hint))
    for pno, text in order:
        t = norm(text)
        if q in t:
            return True, pno
    head, tail = q[:60], q[-60:]
    for pno, text in order:
        t = norm(text)
        if head in t and tail in t:
            return True, pno
    return False, None


def glossary():
    """概念ノートの名前 → 訳語表（原語 → 訳語）。ノート名が「訳語」で、本文 1 行目付近に英語名がある前提。無ければ名前だけ返す。"""
    g = {}
    if not os.path.isdir(GAINEN):
        return g
    for f in sorted(os.listdir(GAINEN)):
        if not f.endswith(".md"):
            continue
        name = f[:-3]
        try:
            head = open(os.path.join(GAINEN, f), encoding="utf-8").read(1500)
        except Exception:
            continue
        m = re.search(r"(?:英語|原語|English)\s*[:：]\s*([A-Za-z][A-Za-z0-9 \-/()]+)", head) or re.search(r"\*\*([A-Z][A-Za-z \-]+)\*\*", head)
        g[name] = m.group(1).strip() if m else ""
    return g
