#!/usr/bin/env python3
"""Q562 (2): JPX 公式の需給データを取得し 作業層/大容量/equities_free/jpx/ に置く（毎日実行すれば伸びる）。
 - 空売り集計（日次 PDF: -m 市場全体, -g 業種別）。サイトが残す約 13 か月分を遡って取得。
 - 銘柄別信用取引残高（日次 mtall.pdf・全銘柄）。サイトが残す直近約 5 営業日分のみ → 毎日取って積み上げる。
 公開日の持ち方: asof=データの日付, pub_date=asof の翌営業日扱いの保守値は読み込み側で +1 営業日（ここは asof だけ記録。mtall は PDF 内の公表日も pub_date に入れる）。
使い方: venv_equities/bin/python fetch_jpx.py [short|margin|all]
"""
import os, re, sys, time
import pandas as pd, requests, pdfplumber

WS = os.path.expanduser("~/ワークスペース")
OUT = os.path.join(WS, "作業層", "大容量", "equities_free", "jpx")
B = "https://www.jpx.co.jp"
H = {"User-Agent": "Mozilla/5.0"}

def get(url, tries=3):
    for _ in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=60)
            if r.status_code == 200: return r.content
        except Exception: pass
        time.sleep(3)
    return None

def fetch_files(kind):
    d = os.path.join(OUT, kind); os.makedirs(d, exist_ok=True); return d

def short():
    d = fetch_files("short_pdf")
    pages = [B + "/markets/statistics-equities/short-selling/index.html"] + [B + f"/markets/statistics-equities/short-selling/00-archives-{i:02d}.html" for i in range(1, 13)]
    links = set()
    for p in pages:
        h = get(p)
        if h: links |= set(re.findall(r'href="(/markets/statistics-equities/short-selling/[^"]*?/(\d{6})-([mg])\.pdf)"', h.decode("utf8", "ignore")))
    print("short links", len(links), flush=True)
    for href, ymd, k in sorted(links, key=lambda x: x[1]):
        f = os.path.join(d, f"{ymd}-{k}.pdf")
        if not os.path.exists(f):
            c = get(B + href)
            if c: open(f, "wb").write(c)
    rm, rg = [], []
    num = lambda s: float(s.replace(",", ""))
    for f in sorted(os.listdir(d)):
        ymd, k = f[:6], f[7]
        date = pd.Timestamp(2000 + int(ymd[:2]), int(ymd[2:4]), int(ymd[4:6]))
        txt = pdfplumber.open(os.path.join(d, f)).pages[0].extract_text()
        pat = re.compile(r"^(\S+?)\s+([\d,]+) ([\d.]+)% ([\d,]+) ([\d.]+)% ([\d,]+) ([\d.]+)% ([\d,]+)$", re.M)
        for m in pat.finditer(txt):
            row = dict(asof=date, a_real=num(m[2]), a_ratio=float(m[3]), b_reg=num(m[4]), b_ratio=float(m[5]), c_noreg=num(m[6]), c_ratio=float(m[7]), total=num(m[8]))
            if k == "m" and m[1].startswith("20"): rm.append(row)
            elif k == "g": rg.append(dict(sector=m[1], **row))
    pd.DataFrame(rm).drop_duplicates("asof").sort_values("asof").to_csv(os.path.join(OUT, "short_ratio_market.csv"), index=False)
    pd.DataFrame(rg).drop_duplicates(["asof", "sector"]).sort_values(["asof", "sector"]).to_csv(os.path.join(OUT, "short_ratio_sector.csv"), index=False)
    print("short parsed", len(rm), len(rg), flush=True)

NUM = re.compile(r"▲?\s?[\d,]+|\*|[\d.]+%")
def parse_margin_pdf(path):
    rows = []; asof = pub = None
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            t = pg.extract_text() or ""
            m = re.search(r"(\d{4}/\d{2}/\d{2})申込み現在.*?(\d{4}/\d{2}/\d{2})", t)
            if m and asof is None: asof, pub = m[1], m[2]
            for ln in t.split("\n"):
                m = re.search(r"(\w{4})0 (JP\w{10})株数 Shs\.\s+(.*)$", ln)
                if not m: continue
                toks = re.findall(r"▲\s?[\d,]+|[\d,.]+%?|\*", m[3])
                v = []
                for tk in toks:
                    if tk == "*": v.append(None); continue
                    if tk.endswith("%"): v.append(float(tk[:-1])); continue
                    neg = tk.startswith("▲"); x = float(tk.replace("▲", "").replace(",", "").strip()); v.append(-x if neg else x)
                # 売(残,前日比,上場比) 買(残,前日比,上場比) 売一般(残,差) 売制度 買一般 買制度
                if len(v) == 14:
                    rows.append(dict(code=m[1], isin=m[2], sell=v[0], sell_chg=v[1], sell_lr=v[2], buy=v[3], buy_chg=v[4], buy_lr=v[5],
                                     sell_neg=v[6], sell_std=v[8], buy_neg=v[10], buy_std=v[12]))
    df = pd.DataFrame(rows); df["asof"] = pd.Timestamp(asof.replace("/", "-")); df["pub_date"] = pd.Timestamp(pub.replace("/", "-"))
    return df

def margin():
    d = fetch_files("margin_pdf")
    h = get(B + "/markets/statistics-equities/margin/01.html").decode("utf8", "ignore")
    for href in sorted(set(re.findall(r'href="(/markets/statistics-equities/margin/[^"]*?/(\d{8})_mtall\.pdf)"', h))):
        f = os.path.join(d, f"{href[1]}_mtall.pdf")
        if not os.path.exists(f):
            c = get(B + href[0])
            if c: open(f, "wb").write(c)
    out = os.path.join(OUT, "margin_by_issue.parquet")
    old = pd.read_parquet(out) if os.path.exists(out) and not os.environ.get("REPARSE") else pd.DataFrame()
    done = set(old["asof"].dt.strftime("%Y%m%d")) if len(old) else set()
    new = []
    for f in sorted(os.listdir(d)):
        if f[:8] in done or not f.endswith(".pdf"): continue
        x = parse_margin_pdf(os.path.join(d, f)); print("margin", f, len(x), flush=True); new.append(x)
    if new:
        pd.concat([old] + new).drop_duplicates(["asof", "code"]).sort_values(["asof", "code"]).to_parquet(out)

if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(OUT, exist_ok=True)
    if w in ("short", "all"): short()
    if w in ("margin", "all"): margin()
