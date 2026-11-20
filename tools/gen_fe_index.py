#!/usr/bin/env python3
"""financial-engineering/ 配下の検証一覧（INDEX.md）を各ディレクトリの README から自動生成する。

使い方: python3 tools/gen_fe_index.py
- 問い: README の最初の見出し（# ...）。README が無い場合は financial-engineering/README.md の
  「主な検証」表の「対象」列を使う。
- 判定: README 中の「**解釈: …**」を優先し、無ければ「結論: **…**」「判定: **…**」「**結論: …**」「## 判定: …」の最初の一致。
  見つからなければ、「## 結果」の節があれば「記述（判定の行なし）」、無ければ「—」（未実行・未記載）。
- README.md が無いフォルダは README_q<番号>*.md の一番小さい番号を本体として読む（2026-11-20）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "financial-engineering"
OUT = FE / "INDEX.md"
MAXLEN = 60

VERDICT_PATTERNS = [  # 上ほど優先（機械判定より人の解釈を優先する）
    re.compile(r"\*\*解釈[:：]\s*(.+?)\*\*"),
    re.compile(r"\*\*(?:機械)?(?:結論|判定)[:：]\s*(.+?)\*\*"),
    re.compile(r"(?:結論|判定)[:：]\s*\*\*(.+?)\*\*"),
    re.compile(r"^##\s*(?:結論|判定)[:：]\s*(.+)$"),
    re.compile(r"^##\s*判定[（(][^）)]*[）)][:：]\s*\*\*(.+?)\*\*"),   # ## 判定（事前登録）: **棄却**（2026-11-20）
    re.compile(r"\*\*事前登録の結論\*\*[:：]\s*(.+)$"),                 # **事前登録の結論**: …（2026-11-20）
]


def curated_targets():
    """主な検証の表から {dir: 対象} を取る（README が無いディレクトリの補完用）。"""
    p = FE / "README.md"
    out = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*\[([^\]]+)\]\([^)]*\)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def short(s):
    s = re.sub(r"\s+", " ", s.strip()).strip("。 ")
    return s if len(s) <= MAXLEN else s[: MAXLEN - 1] + "…"


def qreadmes(d):
    """README_q<番号>*.md を番号の小さい順に（README.md が無いフォルダの補完用・2026-11-20）。"""
    def key(p):
        m = re.match(r"README_q(\d+)", p.name)
        return (int(m.group(1)) if m else 10 ** 6, p.name)
    return sorted((p for p in d.glob("README_q*.md")), key=key)


def parse(d, fallback):
    readme = d / "README.md"
    extra = ""
    if not readme.exists():
        qs = qreadmes(d)
        if qs:  # 原形の README_q*.md を本体として読み、ほかの件数を添える（S23 の q529 など・2026-11-20）
            readme = qs[0]
            if len(qs) > 1:
                extra = f"（ほか {len(qs) - 1} 件: " + "・".join(p.stem.replace("README_", "") for p in qs[1:4]) + ("…" if len(qs) > 4 else "") + "）"
        elif d.name in fallback:
            return fallback[d.name], "README の「主な検証」表を参照"
        else:
            return "（README なし）", "—"
    lines = readme.read_text(encoding="utf-8").splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), d.name)
    title = re.sub(r"\s*—\s*", "：", title)
    verdict = "—"
    for pat in VERDICT_PATTERNS:
        m = next((pat.search(l) for l in lines if pat.search(l) and "`判定: **" not in l and "`結論: **" not in l), None)  # README 雛形の手順の例文（`判定: **…**`）を拾わない（2026-10-16）
        if m:
            verdict = short(m.group(1))
            break
    if verdict == "—":  # 「## 結論」の見出しの次の行（2026-11-20）
        for i, l in enumerate(lines):
            if re.match(r"^##\s*結論\s*$", l):
                nxt = next((x for x in lines[i + 1:] if x.strip()), "")
                if nxt and not nxt.startswith("#"):
                    verdict = short(re.sub(r"[*`]", "", nxt.lstrip("-  ")))
                break
    if verdict == "—" and any(re.match(r"^##\s*結果", l) for l in lines):
        verdict = "記述（判定の行なし）"  # 弱点の面など、事前に判定を置かない記述の検証（2026-11-20）
    return (title + extra).replace("|", "／"), verdict.replace("|", "／")


def main():
    fallback = curated_targets()
    dirs = sorted(p for p in FE.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
    rows = []
    for d in dirs:
        q, v = parse(d, fallback)
        rows.append(f"| [{d.name}](./{d.name}) | {q} | {v} |")
    text = (
        "# financial-engineering 検証一覧\n\n"
        "> このファイルは `python3 tools/gen_fe_index.py` で自動生成しています。手で編集しないでください。\n\n"
        f"全 {len(rows)} 件。判定の「—」は未実行または README に判定の記載がないもの。"
        "詳細は各ディレクトリの README を参照。\n\n"
        "| ディレクトリ | 問い | 判定 |\n| :--- | :--- | :--- |\n" + "\n".join(rows) + "\n"
    )
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
