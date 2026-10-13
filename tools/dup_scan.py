import ast, sys, hashlib, os, collections, re
root = sys.argv[1]; out_md = sys.argv[2]
files = []
for dp, dn, fn in os.walk(root):
    if '__pycache__' in dp or 'venv' in dp or '/.git' in dp: continue
    for f in fn:
        if f.endswith('.py'): files.append(os.path.join(dp, f))
files.sort()
funcs = collections.defaultdict(list); total_defs = 0
for path in files:
    try:
        src = open(path, encoding='utf-8').read(); tree = ast.parse(src)
    except Exception: continue
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            total_defs += 1
            seg = ast.get_source_segment(src, node) or ''
            norm = ast.dump(ast.Module(body=node.body, type_ignores=[]), annotate_fields=False)
            h = hashlib.md5(norm.encode()).hexdigest()[:8]
            funcs[node.name].append((os.path.relpath(path, root), h, seg, ast.unparse(node.args)))
rows = sorted([(n, len(v), len({h for _,h,_,_ in v})) for n,v in funcs.items() if len(v) >= 5], key=lambda r:-r[1])
L = [f"# 重複関数の調査（financial-engineering、{len(files)} ファイル・{total_defs} 関数定義、2026-10-13）\n",
     "同名の関数が5ファイル以上に出るもの。「実装の種類」は本体のASTが一致するものを1種類と数えた（変数名・定数が違えば別種類）。\n",
     "| 関数名 | 定義数 | 実装の種類 | 引数の種類 |","|---|---|---|---|"]
for n,c,k in rows:
    L.append(f"| `{n}` | {c} | {k} | {len({a for *_,a in funcs[n]})} |")
L.append("")
for n in ['load_d1','load_h1','load_csv','load_daily','max_drawdown','cost_bp_oneway','ann_sharpe','sharpe','load_data','load_sym']:
    v = funcs.get(n)
    if not v: continue
    groups = collections.defaultdict(list)
    for f,h,seg,a in v: groups[h].append((f,seg,a))
    L.append(f"\n## `{n}`（{len(v)} 定義・{len(groups)} 種類）\n")
    for h,items in sorted(groups.items(), key=lambda kv:-len(kv[1])):
        f,seg,a = items[0]
        L.append(f"### 種類 {h}: {len(items)} ファイル（例: `{f}`）\n"); L.append(f"引数: `{a}`\n")
        if len(items) <= 3: L.append("ファイル: " + ", ".join(f"`{x[0]}`" for x in items) + "\n")
        L.append("```python\n" + (seg if len(seg) < 1800 else seg[:1800] + "\n# ...（省略）") + "\n```\n")
open(out_md,'w',encoding='utf-8').write("\n".join(L))
print("\n".join(L[:len(rows)+5]))
print("\ncost_bp_oneway 引数:", dict(collections.Counter(a for *_,a in funcs.get('cost_bp_oneway',[]))))
ann = collections.Counter()
for n in ['ann_sharpe','sharpe']:
    for f,h,seg,a in funcs.get(n,[]): ann[(n, tuple(re.findall(r'sqrt\(([^)]*)\)', seg)))] += 1
print("sharpe 年率化:", dict(ann))
