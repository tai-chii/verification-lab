import ast, sys, hashlib, os, collections, difflib
root='financial-engineering'
funcs=collections.defaultdict(list); tmpl=0; tmpl_files=[]
for dp,dn,fn in os.walk(root):
    if '__pycache__' in dp: continue
    for f in fn:
        if not f.endswith('.py'): continue
        p=os.path.join(dp,f)
        try: src=open(p,encoding='utf-8').read(); tree=ast.parse(src)
        except Exception: continue
        names=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.FunctionDef):
                names.add(node.name)
                seg=ast.get_source_segment(src,node) or ''
                h=hashlib.md5(ast.dump(ast.Module(body=node.body,type_ignores=[]),annotate_fields=False).encode()).hexdigest()[:8]
                funcs[node.name].append((os.path.relpath(p,root),h,seg))
        if {'_json_default','tsmom_pos','cost_bp_oneway','max_drawdown'} <= names: tmpl+=1; tmpl_files.append(os.path.relpath(p,root))
print("テンプレ由来（_json_default+tsmom_pos+cost_bp_oneway+max_drawdown を全部持つ）:", tmpl, "ファイル")
print("  先頭3:", tmpl_files[:3]); print("  末尾2:", tmpl_files[-2:])
for n in sys.argv[1:]:
    g=collections.defaultdict(list)
    for f,h,seg in funcs[n]: g[h].append((f,seg))
    items=sorted(g.items(), key=lambda kv:-len(kv[1]))
    base_f,base=items[0][1][0]
    print(f"\n==== {n}: {len(funcs[n])}定義 / {len(items)}種類。多数派 {len(items[0][1])}件（例 {base_f}）")
    print(base)
    for h,lst in items[1:]:
        print(f"--- 少数派 {len(lst)}件: " + ", ".join(f[0] for f in lst[:4]) + (" ..." if len(lst)>4 else ""))
        d=list(difflib.unified_diff(base.splitlines(),lst[0][1].splitlines(),lineterm='',n=0))
        print("\n".join(d[2:][:40]))
