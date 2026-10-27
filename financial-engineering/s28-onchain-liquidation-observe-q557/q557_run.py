"""Q557 本体: 読み取り専用の観測（送信・署名・清算関数は一切使わない。RPC は q557_lib の許可リストのみ）。
事前登録: 事前登録_q557.md（2026-10-27 18:55 固定）。このスクリプトは 2026-10-28 に引き継いだセッション（Opus）が書いた。

【事前登録からの変更点（実装の明確化。判定規則は変えていない）】
1. セル数: 条件（10 チェーン × Aave V2/V3・Compound V2 系 × チェーン別 TVL 10万〜5000万ドル）を満たすセルが 25 しかなく、上限 60 未満なので全数を調べた（乱数抽出は不要）。
2. 住所: DefiLlama-Adapters の多くが registries/aave.js・registries/compound.js に移っていたので、そこと projects/<module> から取った。
3. 見込み純益の上限: 返済できる額×(ボーナス−1) が担保の総額を超えるとき（不良債権）は、受け取れる担保は担保総額まで（seize = min(返済額×ボーナス, 担保総額)）。Compound は最大の借入 1 市場・最大の担保 1 市場で計算。
4. 90 日前のブロックは DefiLlama の block API（coins.llama.fi/block）で決めた（RPC の許可リストに getBlock が無いため）。
5. ガス代は L2 の L1 データ手数料を含まない（eth_gasPrice × 700,000 のみ。事前登録どおり）。
8. 副A（記述・判定に使わない）: 環境変数 Q557_ADD_LIQ=1 で、借り手の集合に「直近 90 日に清算された借り手」を加える（部分清算のあと残った貸付けを拾うため。2026-10-28 追加）。
7. 副（記述・判定に使わない）: 借り手の集合を直近 365 日の Borrow に広げた版も `--days 365` で走らせる。旧版の市場で放置されやすいのは 90 日より前の借り手のため（2026-10-28 の試運転で Scroll Aave V3 が凍結・90 日の Borrow 0 件と分かって追加）。判定は 90 日版だけで行う。
6. 凍結・停止の判定（Aave）: 予約の active=0・frozen=1・paused=1 のどれか。Compound: その市場で mint と borrow の両方が停止、または全体の seize 停止。関数が無いフォークは「停止なし」として数え、セル表に記録する。
"""
import json, os, sys, time, math, statistics, threading, urllib.request, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q557_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
WS = HERE.split('/検証/')[0]
DATA = os.path.join(WS, '作業層/大容量/onchain/q557')
RES = os.path.join(HERE, 'results'); os.makedirs(RES, exist_ok=True)
T0 = time.time(); DEADLINE = T0 + float(os.environ.get('Q557_BUDGET', 3 * 3600))  # 1 回の呼び出しの持ち時間（区切って再実行し、ログは区間ごとにキャッシュ）
ADD_LIQ = os.environ.get('Q557_ADD_LIQ') == '1'
SNAP = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

RPCS = {
 'Arbitrum': (['https://arb1.arbitrum.io/rpc', 'https://gateway.tenderly.co/public/arbitrum'], 100000),
 'Base': (['https://gateway.tenderly.co/public/base', 'https://base-rpc.publicnode.com'], 500),  # publicnode は 2026-10-28 に getLogs が 403 に
 'Optimism': (['https://gateway.tenderly.co/public/optimism'], 100000),
 'Polygon': (['https://gateway.tenderly.co/public/polygon'], 100000),
 'BSC': (['https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 'https://bsc-rpc.publicnode.com'], 50000),  # chainlist 掲載の公開キー
 'Avalanche': (['https://gateway.tenderly.co/public/avalanche', 'https://avalanche-c-chain-rpc.publicnode.com'], 10000),
 'Gnosis': (['https://rpc.gnosischain.com'], 100000),
 'Linea': (['https://rpc.linea.build'], 10000),
 'Scroll': (['https://rpc.scroll.io'], 100000),
 'Mantle': (['https://gateway.tenderly.co/public/mantle', 'https://mantle-rpc.publicnode.com'], 100000),
}
LLAMA_CHAIN = {'Arbitrum': 'arbitrum', 'Base': 'base', 'Optimism': 'optimism', 'Polygon': 'polygon', 'BSC': 'bsc', 'Avalanche': 'avax',
               'Gnosis': 'xdai', 'Linea': 'linea', 'Scroll': 'scroll', 'Mantle': 'mantle'}
TVL_KEY = {'Arbitrum': 'Arbitrum', 'Base': 'Base', 'Optimism': 'Optimism', 'Polygon': 'Polygon', 'BSC': 'Binance', 'Avalanche': 'Avalanche',
           'Gnosis': 'xDai', 'Linea': 'Linea', 'Scroll': 'Scroll', 'Mantle': 'Mantle'}
NATIVE = {'Arbitrum': 'ethereum', 'Base': 'ethereum', 'Optimism': 'ethereum', 'Linea': 'ethereum', 'Scroll': 'ethereum', 'Polygon': 'polygon-ecosystem-token',
          'BSC': 'binancecoin', 'Avalanche': 'avalanche-2', 'Gnosis': 'xdai', 'Mantle': 'mantle'}
# セル: (チェーン, slug, 系統, 住所の種)  住所の出典は README に記録
CELLS = [
 ('Arbitrum', 'radiant-v1', 'Aave V2', ['0x7BB843f889e3a0B307299c3B65e089bFfe9c0bE0']),
 ('Arbitrum', 'radiant-v2', 'Aave V2', ['0xDd109cb6F2B2aEeBcE01727a31d99E3149aa7e41']),
 ('Arbitrum', 'tender-finance', 'Compound V2', ['0xeed247Ba513A8D6f78BE9318399f5eD1a4808F8e']),
 ('Arbitrum', 'venus-core-pool', 'Compound V2', ['0x317c1A5739F39046E20b08ac9BeEa3f10fD43326']),
 ('Avalanche', 'aave-v2', 'Aave V2', ['0x4235E22d9C3f28DCDA82b58276cb6370B01265C2']),
 ('BSC', 'apeswap-lending', 'Compound V2', ['0xad48b2c9dc6709a560018c678e918253a65df86e']),
 ('BSC', 'avalon-finance', 'Aave V3', ['0x5395201A4DD625a0d69b99D917282f75928416c1', '0x672b19DdA450120C505214D149Ee7F7B6DEd8C39', '0xb1C93Ba1286b6CCA1496C266f0eBfCe94b0C0cc0',
     '0x58c937fa2D147117dB43d187f9411151edfFf03c', '0xF828A73cB00072843241C6294ed778F26854fe5C', '0x56F817eF5D1945E0772496020ff0F72c3984B351', '0xA34F1a928024E3609C8968fEA90C747e8D1fA20f',
     '0x2c4aEB7C9f0D196a51136B3c7bec49cB2DBD1966', '0x5157f63bE7808DEB090Eee7762e917745896A09E', '0x5b9b3C211B81627Cc6b46824CB26829F31A587dc', '0x7788a3538c5fc7f9c7c8a74eac4c898fc8d87d92',
     '0x9515dC23bBE46f9C9885D24Fa276745A11b7f9D8', '0xf3527ef8de265eaa3716fb312c12847bfba66cef']),
 ('BSC', 'cream-lending', 'Compound V2', ['0x589DE0F0Ccf905477646599bb3E5C622C84cC0BA']),
 ('BSC', 'demeter', 'Compound V2', ['0x3632E78219227b172F0aaF56F92FB08D87C94379']),
 ('BSC', 'kinza-finance', 'Aave V3', ['0x37D7Eb561E189895E5c8601Cd03EEAB67C269189', '0x09ddc4ae826601b0f9671b9edffdf75e7e6f5d61']),
 ('Base', 'extra-finance-xlend', 'Aave V3', ['0x1566DA4640b6a0b32fF309b07b8df6Ade40fd98D']),
 ('Base', 'moonwell-lending', 'Compound V2', ['0xfBb21d0380beE3312B33c4353c8936a0F13EF26C']),
 ('Base', 'seamless-v1', 'Aave V3', ['0x90C5055530C0465AbB077FA016a3699A3F53Ef99', '0x2A0979257105834789bC6b9E1B00446DFbA8dFBa']),
 ('Base', 'zebradao', 'Compound V2', ['0xBEA1D596Ae022fae90d84ffaF0907E38a25Ed6E7']),
 ('Gnosis', 'realt-rmm-marketplace-v2', 'Aave V3', ['0xC6c4b123e731819AC5f7F9E0fe3A118e9b1227Cd', '0x11B45acC19656c6C52f93d8034912083AC7Dd756']),
 ('Gnosis', 'sparklend', 'Aave V3', ['0x49d24798d3b84965F0d1fc8684EF6565115e70c1', '0x2a002054A06546bB5a264D57A81347e23Af91D18']),
 ('Linea', 'aave-v3', 'Aave V3', ['0x2D97F8FA96886Fd923c065F5457F9DDd494e3877']),
 ('Linea', 'mendi-finance', 'Compound V2', ['0x1b4d3b0421dDc1eB216D230Bc01527422Fb93103']),
 ('Mantle', 'lendle-pooled-markets', 'Aave V2', ['0x30D990834539E1CE8Be816631b73a534e5044856']),
 ('Optimism', 'aave-v3', 'Aave V3', ['0x7F23D86Ee20D869112572136221e173428DD740B']),
 ('Optimism', 'extra-finance-xlend', 'Aave V3', ['0xCC61E9470B5f0CE21a3F6255c73032B47AaeA9C0']),
 ('Optimism', 'moonwell-lending', 'Compound V2', ['MOONWELL_OP']),
 ('Polygon', 'aave-v2', 'Aave V2', ['0x3ac4e9aa29940770aeC38fe853a4bbabb2dA9C19']),
 ('Polygon', 'rnt-lend', 'Aave V3', ['0x717c2a6fa0820b04b9d4793daca33a229aec85ca']),
 ('Scroll', 'aave-v3', 'Aave V3', ['0xe2108b60623C6Dcf7bBd535bD15a451fd0811f7b']),
]
STABLES = {'USDC', 'USDT', 'DAI', 'USDC.E', 'USDBC', 'USDT0', 'USD₮0', 'BUSD', 'FDUSD', 'WXDAI', 'XDAI', 'USD1', 'AXLUSDC', 'USDT.E', 'DAI.E', 'USDC.M', 'USDT.M'}
WNATIVE = {'WETH', 'WBNB', 'WAVAX', 'WMATIC', 'WPOL', 'WMNT', 'WXDAI'}

T = {k: topic(v) for k, v in {
  'b2': 'Borrow(address,address,address,uint256,uint256,uint256,uint16)', 'b3': 'Borrow(address,address,address,uint256,uint8,uint256,uint16)',
  'bc': 'Borrow(address,uint256,uint256,uint256)', 'la': 'LiquidationCall(address,address,address,uint256,uint256,address,bool)',
  'lc': 'LiquidateBorrow(address,address,uint256,address,uint256)'}.items()}
def lj(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)
def addrw(b):  # 32 バイト語から住所
    return '0x' + b[12:32].hex() if len(b) >= 32 and int.from_bytes(b[:32], 'big') and int.from_bytes(b[:12], 'big') == 0 else None
def get_json(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90))

# ---------- 発見 ----------
def discover_aave(rpc, seeds):
    pools = {}; seen = set(); q = [s.lower() for s in seeds]
    while q:
        a = q.pop(0)
        if a in seen: continue
        seen.add(a)
        probes = ['getAddressesProvidersList()', 'ADDRESSES_PROVIDER()', 'getPool()', 'getLendingPool()', 'getPriceOracle()']
        r = rpc.multicall([(a, call_data(p)) for p in probes])
        lst = dec_addr_array(r[0][1]) if r[0][0] else None
        if lst: q += [x for x in lst if int(x, 16)]
        ap = addrw(r[1][1]) if r[1][0] else None
        if ap: q.append(ap)
        p3 = addrw(r[2][1]) if r[2][0] and len(r[2][1]) == 32 else None
        p2 = addrw(r[3][1]) if r[3][0] and len(r[3][1]) == 32 else None
        orc = addrw(r[4][1]) if r[4][0] and len(r[4][1]) == 32 else None
        if (p3 or p2) and orc:
            pool = p3 or p2
            pools[pool] = {'provider': a, 'oracle': orc, 'v': 3 if p3 else 2}
    return pools
def discover_comp(rpc, seeds):
    out = {}
    for s in seeds:
        r = rpc.multicall([(s, call_data('getAllMarkets()')), (s, call_data('oracle()'))])
        mk = dec_addr_array(r[0][1]) if r[0][0] else None
        if mk: out[s.lower()] = {'markets': [m.lower() for m in mk], 'oracle': addrw(r[1][1]) if r[1][0] else None}
    return out

def symbols(rpc, addrs):
    r = rpc.multicall([(a, call_data('symbol()')) for a in addrs])
    return [dec_string(b).strip() if ok else '' for ok, b in r]

# ---------- Aave の 1 プール ----------
def aave_pool(rpc, pool, meta, users, gas_usd):
    v = meta['v']
    ok, b = rpc.multicall([(pool, call_data('getReservesList()'))])[0]
    res = [x.lower() for x in (dec_addr_array(b) or [])] if ok else []
    if not res: return None
    cfg = rpc.multicall([(pool, call_data('getConfiguration(address)', a)) for a in res])
    rd = rpc.multicall([(pool, call_data('getReserveData(address)', a)) for a in res])
    px = rpc.multicall([(meta['oracle'], call_data('getAssetPrice(address)', a)) for a in res])
    sy = symbols(rpc, res)
    R = {}
    for i, a in enumerate(res):
        c = word(cfg[i][1], 0) if cfg[i][0] and len(cfg[i][1]) >= 32 else 0
        rid = word(rd[i][1], 11 if v == 2 else 7) if rd[i][0] and len(rd[i][1]) >= 32 * 12 else None
        R[a] = {'sym': sy[i], 'bonus': ((c >> 32) & 0xFFFF) / 1e4, 'active': (c >> 56) & 1, 'frozen': (c >> 57) & 1, 'paused': (c >> 60) & 1 if v == 3 else 0,
                'id': rid, 'price': word(px[i][1], 0) if px[i][0] and len(px[i][1]) >= 32 else 0}
    stp = [R[a]['price'] for a in R if R[a]['sym'].upper() in STABLES and R[a]['price'] > 0]
    if stp: usd_per_unit = 1.0 / statistics.median(stp); base_src = 'stable'
    else:
        wn = [R[a]['price'] for a in R if R[a]['sym'].upper() in WNATIVE and R[a]['price'] > 0]
        if not wn: return {'error': 'no base price', 'reserves': len(res)}
        usd_per_unit = gas_usd['native'] / statistics.median(wn); base_src = 'native'
    byid = {R[a]['id']: a for a in R if R[a]['id'] is not None}
    frozen_cell = all((not R[a]['active']) or R[a]['frozen'] or R[a]['paused'] for a in R)
    users = sorted(users)
    acc = rpc.multicall([(pool, call_data('getUserAccountData(address)', u)) for u in users])
    uc = rpc.multicall([(pool, call_data('getUserConfiguration(address)', u)) for u in users])
    pos = []; n_liq = 0
    for i, u in enumerate(users):
        ok, b = acc[i]
        if not ok or len(b) < 192: continue
        coll, debt, hf = word(b, 0), word(b, 1), word(b, 5)
        if debt == 0 or hf >= 10 ** 18: continue
        n_liq += 1
        m = word(uc[i][1], 0) if uc[i][0] else 0
        col_a = [byid[k] for k in byid if (m >> (2 * k + 1)) & 1]; bor_a = [byid[k] for k in byid if (m >> (2 * k)) & 1]
        blocked = any((not R[a]['active']) or R[a]['frozen'] or R[a]['paused'] for a in col_a + bor_a)
        bonus = max([R[a]['bonus'] for a in col_a] or [1.0])
        debt_usd = debt * usd_per_unit; coll_usd = coll * usd_per_unit
        cf = 1.0 if (v == 3 and hf < 0.95e18) else 0.5
        repay = debt_usd * cf
        seize = min(repay * bonus, coll_usd)
        net = seize - repay - gas_usd['liq'] - repay * 0.0009
        pos.append({'user': short(u), 'hf': hf / 1e18, 'debt_usd': debt_usd, 'coll_usd': coll_usd, 'bonus': bonus, 'cf': cf, 'net_usd': net,
                    'blocked': int(blocked), 'profitable': int(net > 1 and not blocked),
                    'collateral': '/'.join(R[a]['sym'] for a in col_a), 'debt': '/'.join(R[a]['sym'] for a in bor_a)})
    return {'reserves': len(res), 'frozen_cell': frozen_cell, 'base_src': base_src, 'n_users': len(users), 'n_liquidatable': n_liq, 'positions': pos}

# ---------- Compound の 1 comptroller ----------
def comp_ctrl(rpc, ct, meta, users, gas_usd):
    mk = meta['markets']; orc = meta['oracle']
    g = rpc.multicall([(ct, call_data('closeFactorMantissa()')), (ct, call_data('liquidationIncentiveMantissa()')), (ct, call_data('seizeGuardianPaused()'))])
    cf = word(g[0][1], 0) / 1e18 if g[0][0] and len(g[0][1]) >= 32 else 0.5
    li = word(g[1][1], 0) / 1e18 if g[1][0] and len(g[1][1]) >= 32 else 1.08
    seize_paused = word(g[2][1], 0) if g[2][0] and len(g[2][1]) >= 32 else 0
    pause_known = g[2][0] and len(g[2][1]) >= 32
    px = rpc.multicall([(orc, call_data('getUnderlyingPrice(address)', m)) for m in mk]) if orc else [(False, b'')] * len(mk)
    ex = rpc.multicall([(m, call_data('exchangeRateStored()')) for m in mk])
    mp = rpc.multicall([(ct, call_data('mintGuardianPaused(address)', m)) for m in mk])
    bp = rpc.multicall([(ct, call_data('borrowGuardianPaused(address)', m)) for m in mk])
    sy = symbols(rpc, mk)
    M = {}
    for i, m in enumerate(mk):
        M[m] = {'sym': sy[i], 'price': word(px[i][1], 0) if px[i][0] and len(px[i][1]) >= 32 else 0,
                'ex': word(ex[i][1], 0) if ex[i][0] and len(ex[i][1]) >= 32 else 0,
                'frozen': int((word(mp[i][1], 0) if mp[i][0] and len(mp[i][1]) >= 32 else 0) and (word(bp[i][1], 0) if bp[i][0] and len(bp[i][1]) >= 32 else 0))}
    frozen_cell = all(M[m]['frozen'] for m in M) or bool(seize_paused)
    users = sorted(users)
    al = rpc.multicall([(ct, call_data('getAccountLiquidity(address)', u)) for u in users])
    short_users = [u for i, u in enumerate(users) if al[i][0] and len(al[i][1]) >= 96 and word(al[i][1], 0) == 0 and word(al[i][1], 2) > 0]
    pos = []
    if short_users:
        calls = []
        for u in short_users:
            for m in mk: calls += [(m, call_data('borrowBalanceStored(address)', u)), (m, call_data('balanceOf(address)', u))]
        r = rpc.multicall(calls); k = 0
        for u in short_users:
            bor = {}; col = {}
            for m in mk:
                bb = word(r[k][1], 0) if r[k][0] and len(r[k][1]) >= 32 else 0
                ba = word(r[k + 1][1], 0) if r[k + 1][0] and len(r[k + 1][1]) >= 32 else 0
                k += 2
                if bb: bor[m] = bb * M[m]['price'] / 1e36
                if ba: col[m] = ba * M[m]['ex'] / 1e18 * M[m]['price'] / 1e36
            if not bor: continue
            bm = max(bor, key=bor.get); cm = max(col, key=col.get) if col else None
            repay = bor[bm] * cf; seize = min(repay * li, col.get(cm, 0) if cm else 0)
            net = seize - repay - gas_usd['liq'] - repay * 0.0009
            blocked = bool(seize_paused) or M[bm]['frozen'] or (M[cm]['frozen'] if cm else 0)
            pos.append({'user': short(u), 'hf': None, 'debt_usd': sum(bor.values()), 'coll_usd': sum(col.values()), 'bonus': li, 'cf': cf, 'net_usd': net,
                        'blocked': int(blocked), 'profitable': int(net > 1 and not blocked),
                        'collateral': M[cm]['sym'] if cm else '', 'debt': M[bm]['sym']})
    return {'reserves': len(mk), 'frozen_cell': frozen_cell, 'pause_fn': int(pause_known), 'cf': cf, 'li': li, 'n_users': len(users),
            'n_liquidatable': len(short_users), 'positions': pos}

# ---------- 1 チェーン ----------
def run_chain(chain, cells, ctx, out):
    urls, span = RPCS[chain]; rpc = Rpc(urls)
    try:
        latest = cache_json(os.path.join(DATA, f'snap_{chain}_d{ctx["days"]}.json.gz'), lambda: rpc.block()); gp = rpc.gas_price()
        nat = ctx['native'][NATIVE[chain]]
        gas_usd = {'native': nat, 'liq': gp * 700000 / 1e18 * nat, 'gwei': gp / 1e9}
        frm = ctx['block90'][chain]
        disc = {}
        for (ch, slug, fam, seeds) in cells:
            seeds = [ctx['moonwell_op'] if s == 'MOONWELL_OP' else s for s in seeds]
            try:
                d = discover_comp(rpc, seeds) if fam == 'Compound V2' else discover_aave(rpc, seeds)
            except Exception as e:
                d = {}; lj(chain, slug, 'discover error', str(e)[:120])
            disc[slug] = d
            lj(chain, slug, fam, 'found', {k: (len(v['markets']) if 'markets' in v else v['v']) for k, v in d.items()})
        addrs = sorted({p for d in disc.values() for p in d} | {m for d in disc.values() for v in d.values() for m in v.get('markets', [])})
        logs = []
        if addrs:
            h = hashlib.sha1(','.join(addrs).encode()).hexdigest()[:8]; SEG = max(span * 10, 50000)
            def seg(a0):
                a1 = min(latest, a0 + SEG - 1)
                def fetch():
                    L = []
                    for s in range(0, len(addrs), 200):
                        L += rpc.logs(addrs[s:s + 200], [T['b2'], T['b3'], T['bc'], T['la'], T['lc']], a0, a1, span, DEADLINE)
                    return L
                return cache_json(os.path.join(DATA, 'seg', f'logs_{chain}_{h}_{a0}_{a1}.json.gz'), fetch)
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(6 if chain == 'Base' else 3) as ex:  # 区間を 3 本並列（1 口あたりの上限 4 件/秒は q557_lib の間引きで守る）
                for L in ex.map(seg, range(frm, latest + 1, SEG)): logs += L
        lj(chain, 'logs', len(logs), 'blocks', frm, latest, 'rpc calls', rpc.n)
        for (ch, slug, fam, seeds) in cells:
            d = disc.get(slug) or {}
            row = {'chain': chain, 'slug': slug, 'family': fam, 'tvl_now': ctx['tvl'][(chain, slug)]['now'], 'tvl_max365': ctx['tvl'][(chain, slug)]['max365'],
                   'gas_gwei': gas_usd['gwei'], 'gas_usd_per_liq': gas_usd['liq'], 'from_block': frm, 'to_block': latest, 'contracts': len(d)}
            row['state'] = '旧版' if row['tvl_now'] <= 0.2 * row['tvl_max365'] else '現役'
            if not d:
                row['status'] = '住所不明'; out.append((row, [])); continue
            try:
                allpos = []; liqs = []; nu = 0; nl = 0; fz = []; extra = {}
                for c, meta in d.items():
                    own = {c} | set(meta.get('markets', []))
                    lg = [x for x in logs if x['address'].lower() in own]
                    if fam == 'Compound V2':
                        us = {('0x' + x['topics'][1][-40:]) if len(x['topics']) > 1 else ('0x' + x['data'][2 + 24:2 + 64]) for x in lg if x['topics'][0] == T['bc']}
                        lq = [(('0x' + x['topics'][1][-40:]) if len(x['topics']) > 1 else ('0x' + x['data'][2 + 24:2 + 64])) for x in lg if x['topics'][0] == T['lc']]
                        if ADD_LIQ: us |= {(('0x' + x['topics'][2][-40:]) if len(x['topics']) > 2 else ('0x' + x['data'][2 + 64 + 24:2 + 128])) for x in lg if x['topics'][0] == T['lc']}
                        r = comp_ctrl(rpc, c, meta, us, gas_usd); extra = {'cf': r['cf'], 'li': r['li'], 'pause_fn': r['pause_fn']}
                    else:
                        us = {'0x' + x['topics'][2][-40:] for x in lg if x['topics'][0] in (T['b2'], T['b3']) and len(x['topics']) > 2}
                        lq = ['0x' + x['data'][2 + 64 * 2 + 24:2 + 64 * 3] for x in lg if x['topics'][0] == T['la']]
                        if ADD_LIQ: us |= {'0x' + x['topics'][3][-40:] for x in lg if x['topics'][0] == T['la'] and len(x['topics']) > 3}
                        r = aave_pool(rpc, c, meta, us, gas_usd)
                        if r is None: continue
                        if 'error' in r: extra['error'] = r['error']; continue
                        extra['base_src'] = r['base_src']
                    liqs += lq; nu += r['n_users']; nl += r['n_liquidatable']; fz.append(r['frozen_cell'])
                    for p in r['positions']: p['contract'] = short(c)
                    allpos += r['positions']
                prof = [p for p in allpos if p['profitable']]
                from collections import Counter
                cnt = Counter(liqs)
                row.update({'status': '調べた' if fz else '住所不明', 'frozen': int(bool(fz) and all(fz)), 'borrowers_90d': nu, 'liquidatable': nl,
                            'profitable_n': len(prof), 'profit_sum': sum(p['net_usd'] for p in prof), 'profit_median': statistics.median([p['net_usd'] for p in prof]) if prof else 0,
                            'liq_events_90d': len(liqs), 'liquidators_90d': len(cnt), 'top1_share': (cnt.most_common(1)[0][1] / len(liqs)) if liqs else None, **extra})
                if row['frozen']: row['state'] = '凍結'
                for p in allpos: p.update({'chain': chain, 'slug': slug})
                out.append((row, allpos))
                lj(chain, slug, row['state'], 'users', nu, 'liq-able', nl, 'profitable', len(prof), 'liquidators', len(cnt))
            except Exception as e:
                row['status'] = '時間切れ' if isinstance(e, TimeoutError) else 'RPC失敗'; row['error'] = str(e)[:200]; out.append((row, []))
                lj(chain, slug, 'FAIL', str(e)[:200])
    except Exception as e:
        lj(chain, 'CHAIN FAIL', str(e)[:200])
        for (ch, slug, fam, seeds) in cells:
            if not any(o[0]['slug'] == slug and o[0]['chain'] == chain for o in out):
                t = ctx['tvl'][(chain, slug)]
                out.append(({'chain': chain, 'slug': slug, 'family': fam, 'tvl_now': t['now'], 'tvl_max365': t['max365'],
                             'state': '旧版' if t['now'] <= 0.2 * t['max365'] else '現役', 'status': '時間切れ' if isinstance(e, TimeoutError) else 'RPC失敗', 'error': str(e)[:200]}, []))

def main():
    args = sys.argv[1:]; days = 90
    if '--days' in args: i = args.index('--days'); days = int(args[i + 1]); del args[i:i + 2]
    only = args  # 試し: チェーン名を渡すとそのチェーンだけ
    cells = [c for c in CELLS if not only or c[0] in only]
    ctx = {'tvl': {}, 'block90': {}, 'days': days}
    now = int(time.time())
    for ch, slug, fam, _ in cells:
        p = cache_json(os.path.join(DATA, f'protocol_{slug}_{time.strftime("%Y%m%d")}.json.gz'), lambda: get_json('https://api.llama.fi/protocol/' + slug))
        ser = p['chainTvls'][TVL_KEY[ch]]['tvl']
        ser = [x for x in ser if x['date'] >= now - 365 * 86400]
        ctx['tvl'][(ch, slug)] = {'now': ser[-1]['totalLiquidityUSD'], 'max365': max(x['totalLiquidityUSD'] for x in ser)}
    for ch in {c[0] for c in cells}:
        ctx['block90'][ch] = cache_json(os.path.join(DATA, f'from_{ch}_d{days}.json.gz'), lambda: get_json(f'https://coins.llama.fi/block/{LLAMA_CHAIN[ch]}/{now - days * 86400}')['height'])
    ids = ','.join('coingecko:' + v for v in set(NATIVE.values()))
    pr = get_json('https://coins.llama.fi/prices/current/' + ids)['coins']
    ctx['native'] = {k.split(':')[1]: v['price'] for k, v in pr.items()}
    reg = open(os.path.join(DATA, 'adapters/registry_compound.js')).read()
    i = reg.index("'moonwell'"); j = reg.index('optimism', i); ctx['moonwell_op'] = reg[j:j + 200].split("comptroller: '")[1][:42]
    lj('ctx', json.dumps({'block90': ctx['block90'], 'native': ctx['native'], 'moonwell_op': ctx['moonwell_op']}))
    out = []; th = []
    for ch in sorted({c[0] for c in cells}):
        t = threading.Thread(target=run_chain, args=(ch, [c for c in cells if c[0] == ch], ctx, out)); t.start(); th.append(t)
    for t in th: t.join()
    tag = ('_'.join(only) if only else 'all') + ('' if days == 90 else f'_d{days}') + ('_liqusers' if ADD_LIQ else '')
    rows = [o[0] for o in out]; pos = [p for o in out for p in o[1]]
    keys = ['chain', 'slug', 'family', 'state', 'status', 'tvl_now', 'tvl_max365', 'contracts', 'borrowers_90d', 'liquidatable', 'profitable_n', 'profit_sum', 'profit_median',
            'liq_events_90d', 'liquidators_90d', 'top1_share', 'frozen', 'gas_gwei', 'gas_usd_per_liq', 'from_block', 'to_block', 'base_src', 'cf', 'li', 'pause_fn', 'error']
    with open(os.path.join(RES, f'cells_{tag}.csv'), 'w', newline='') as f:
        wr = csv.DictWriter(f, keys, extrasaction='ignore'); wr.writeheader(); [wr.writerow(r) for r in sorted(rows, key=lambda r: (r['chain'], r['slug']))]
    pk = ['chain', 'slug', 'contract', 'user', 'hf', 'debt_usd', 'coll_usd', 'bonus', 'cf', 'net_usd', 'blocked', 'profitable', 'collateral', 'debt']
    with open(os.path.join(RES, f'positions_liquidatable_{tag}.csv'), 'w', newline='') as f:
        wr = csv.DictWriter(f, pk, extrasaction='ignore'); wr.writeheader(); [wr.writerow(p) for p in sorted(pos, key=lambda p: -p['net_usd'])]
    json.dump({'snapshot_utc': SNAP, 'elapsed_min': round((time.time() - T0) / 60, 1), 'days': days, 'ctx': {'block90': ctx['block90'], 'native': ctx['native']}},
              open(os.path.join(RES, f'run_meta_{tag}.json'), 'w'), ensure_ascii=False, indent=1)
    lj('done', len(rows), 'cells', len(pos), 'liquidatable positions', round((time.time() - T0) / 60, 1), 'min')

if __name__ == '__main__':
    main()
