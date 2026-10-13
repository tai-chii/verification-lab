#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fe_core の目録を docstring から自動生成する（手で編集しない）。

出力: tools/fe_core/CATALOG.md（LLM が読む用・段階の順）と tools/fe_core/catalog.json（機械用）。
正本は各関数の docstring。書式:
    1 行目: 一言
    使う場面: … / 入力: … / 返り値: … / 禁止: … / 段階: 読み込み|合図|損益|統計|帰無|判定|保存|共通
実行: python3 tools/gen_fe_core_catalog.py        （--check で、生成物が最新かだけ確かめて差があれば exit 1）
"""
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "fe_core")
STAGES = ["共通", "読み込み", "合図", "損益", "統計", "帰無", "判定", "保存"]
FIELDS = ["使う場面", "入力", "返り値", "禁止", "段階"]
MODULES = ["_paths", "data", "signals", "costs", "metrics", "multiple", "io", "runner"]


def parse_doc(doc):
    d = {"一言": "", **{k: "" for k in FIELDS}}
    if not doc:
        return d
    lines = [l.strip() for l in doc.strip().splitlines()]
    d["一言"] = lines[0]
    for l in lines[1:]:
        for k in FIELDS:
            if l.startswith(k + ":"):
                d[k] = l[len(k) + 1:].strip()
    return d


def collect():
    exported = set()
    init = ast.parse(open(os.path.join(PKG, "__init__.py"), encoding="utf-8").read())
    for n in ast.walk(init):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets):
            exported = {ast.literal_eval(e) for e in n.value.elts}
    funcs, consts = [], []
    for mod in MODULES:
        path = os.path.join(PKG, mod + ".py")
        src = open(path, encoding="utf-8").read(); tree = ast.parse(src)
        moddoc = (ast.get_docstring(tree) or "").splitlines()[0] if ast.get_docstring(tree) else ""
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in exported:
                d = parse_doc(ast.get_docstring(n))
                sig = f"{n.name}({ast.unparse(n.args)})" if isinstance(n, ast.FunctionDef) else f"class {n.name}"
                funcs.append({"name": n.name, "module": mod, "signature": sig,
                              "line": n.lineno, **d})
            elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in exported:
                val = ast.unparse(n.value)
                # 行末コメントを拾う
                line = src.splitlines()[n.lineno - 1]
                comment = line.split("#", 1)[1].strip() if "#" in line else ""
                if not comment and n.lineno >= 2:
                    prev = src.splitlines()[n.lineno - 2].strip()
                    if prev.startswith("#"):
                        comment = prev.lstrip("# ").strip()
                consts.append({"name": n.targets[0].id, "module": mod, "value": val if len(val) <= 160 else val[:157] + "...",
                               "note": comment, "line": n.lineno})
        _ = moddoc
    return funcs, consts


def render_md(funcs, consts):
    L = ["# fe_core 目録（自動生成・手で編集しない）\n",
         "`python3 tools/gen_fe_core_catalog.py` が各関数の docstring から作る。正本は docstring。**新しい検証スクリプトを書く前にこのファイルを上から読む**: 段階の順に並んでいるので、そのまま検証の骨格になる。\n",
         "読み込み → 合図 → 損益 → 統計 → 帰無 → 判定 → 保存（共通は冒頭と main）。土台の関数は `from fe_core import *` でそのまま呼べる。\n",
         "## 定数\n", "| 名前 | 値 | 備考 | 場所 |", "|---|---|---|---|"]
    for c in consts:
        L.append(f"| `{c['name']}` | `{c['value']}` | {c['note']} | `{c['module']}.py:{c['line']}` |")
    for st in STAGES:
        fs = [f for f in funcs if f["段階"] == st]
        if not fs:
            continue
        L += ["", f"## 段階: {st}\n"]
        for f in fs:
            L += [f"### `{f['signature']}`  — `{f['module']}.py:{f['line']}`\n", f"{f['一言']}\n",
                  "| | |", "|---|---|",
                  f"| 使う場面 | {f['使う場面']} |", f"| 入力 | {f['入力']} |", f"| 返り値 | {f['返り値']} |", f"| 禁止 | {f['禁止']} |", ""]
    other = [f for f in funcs if f["段階"] not in STAGES]
    if other:
        L += ["", "## 段階が未記入（docstring を直す）\n"] + [f"- `{f['signature']}` ({f['module']})" for f in other]
    return "\n".join(L) + "\n"


def main():
    funcs, consts = collect()
    funcs.sort(key=lambda f: (STAGES.index(f["段階"]) if f["段階"] in STAGES else 99, MODULES.index(f["module"]), f["line"]))
    md = render_md(funcs, consts)
    js = json.dumps({"generated_from": "docstrings of tools/fe_core/*.py", "stages": STAGES,
                     "constants": consts, "functions": funcs}, ensure_ascii=False, indent=1) + "\n"
    out_md, out_js = os.path.join(PKG, "CATALOG.md"), os.path.join(PKG, "catalog.json")
    if "--check" in sys.argv:
        cur_md = open(out_md, encoding="utf-8").read() if os.path.exists(out_md) else ""
        cur_js = open(out_js, encoding="utf-8").read() if os.path.exists(out_js) else ""
        if cur_md == md and cur_js == js:
            print("catalog up to date"); return 0
        print("catalog is stale: run gen_fe_core_catalog.py"); return 1
    open(out_md, "w", encoding="utf-8").write(md); open(out_js, "w", encoding="utf-8").write(js)
    missing = [f["name"] for f in funcs if not all(f[k] for k in ["一言", "使う場面", "入力", "返り値", "段階"])]
    print(f"wrote {os.path.relpath(out_md, HERE)} / {os.path.relpath(out_js, HERE)}: {len(funcs)} functions, {len(consts)} constants")
    if missing:
        print("docstring が不足:", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
