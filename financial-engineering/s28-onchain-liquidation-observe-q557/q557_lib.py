"""Q557 共通部品（標準ライブラリだけ）。読み取り専用: 許可した RPC メソッドだけを呼び、送信・署名・清算関数は一切扱わない。"""
import json, time, threading, urllib.request, urllib.error, gzip, os, hashlib

# ---------- keccak-256（自前実装・標準ライブラリに無いため） ----------
_RC = [0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,
       0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
       0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,
       0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
_ROT = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
_M = (1 << 64) - 1
def _f(A):
    for rc in _RC:
        C = [A[x][0]^A[x][1]^A[x][2]^A[x][3]^A[x][4] for x in range(5)]
        D = [C[(x-1) % 5] ^ (((C[(x+1) % 5] << 1) | (C[(x+1) % 5] >> 63)) & _M) for x in range(5)]
        A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0]*5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                r = _ROT[x][y]; v = A[x][y]
                B[y][(2*x+3*y) % 5] = (((v << r) | (v >> (64-r))) & _M) if r else v
        A = [[B[x][y] ^ ((~B[(x+1) % 5][y]) & B[(x+2) % 5][y]) for y in range(5)] for x in range(5)]
        A[0][0] ^= rc
    return A
def keccak256(data: bytes) -> bytes:
    rate = 136; p = bytearray(data); p.append(0x01)
    while len(p) % rate: p.append(0)
    p[-1] |= 0x80
    A = [[0]*5 for _ in range(5)]
    for off in range(0, len(p), rate):
        for i in range(rate // 8):
            A[i % 5][i // 5] ^= int.from_bytes(p[off+8*i:off+8*i+8], 'little')
        A = _f(A)
    return b''.join(A[i % 5][i // 5].to_bytes(8, 'little') for i in range(4))
def sel(sig): return keccak256(sig.encode())[:4]
def topic(sig): return '0x' + keccak256(sig.encode()).hex()
assert keccak256(b'').hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
assert sel('transfer(address,uint256)').hex() == 'a9059cbb'

# 清算・送信につながる関数は呼び出しを組み立てる段階で拒否する（安全規則 4）
_DENY = {sel(s) for s in ['liquidationCall(address,address,address,uint256,bool)', 'liquidateBorrow(address,uint256,address)',
         'liquidateBorrow(address,address,uint256,address)', 'flashLoan(address,address[],uint256[],uint256[],address,bytes,uint16)',
         'flashLoanSimple(address,address,uint256,bytes,uint16)', 'transfer(address,uint256)', 'approve(address,uint256)']}

# ---------- ABI ----------
def w(n): return int(n).to_bytes(32, 'big')
def wa(a): return bytes(12) + bytes.fromhex(a[2:].lower())
def call_data(sig, *args):
    s = sel(sig); assert s not in _DENY, sig
    b = s
    for a in args: b += wa(a) if isinstance(a, str) else w(a)
    return b
def word(b, i): return int.from_bytes(b[32*i:32*i+32], 'big')
def addr_at(b, i): return '0x' + b[32*i+12:32*i+32].hex()
def dec_addr_array(b):
    if len(b) < 64: return None
    off = word(b, 0); n = int.from_bytes(b[off:off+32], 'big')
    if n > 5000 or len(b) < off + 32 + 32*n: return None
    return ['0x' + b[off+32+32*i+12:off+64+32*i].hex() for i in range(n)]
def dec_string(b):
    if len(b) == 32: return b.rstrip(b'\0').decode('utf-8', 'ignore')
    if len(b) < 64: return ''
    off = word(b, 0); n = int.from_bytes(b[off:off+32], 'big')
    return b[off+32:off+32+n].decode('utf-8', 'ignore')

MC3 = '0xca11bde05977b3631167028862be2a173976ca11'
def enc_aggregate3(calls):
    n = len(calls); elems = []
    for t, d in calls:
        pad = d + bytes((32 - len(d) % 32) % 32)
        elems.append(wa(t) + w(1) + w(0x60) + w(len(d)) + pad)
    offs = []; cur = 32*n
    for e in elems: offs.append(cur); cur += len(e)
    return sel('aggregate3((address,bool,bytes)[])') + w(0x20) + w(n) + b''.join(w(o) for o in offs) + b''.join(elems)
def dec_aggregate3(b):
    off = word(b, 0); n = int.from_bytes(b[off:off+32], 'big'); base = off + 32; out = []
    for i in range(n):
        eo = base + int.from_bytes(b[base+32*i:base+32*i+32], 'big')
        ok = int.from_bytes(b[eo:eo+32], 'big'); do = eo + int.from_bytes(b[eo+32:eo+64], 'big')
        ln = int.from_bytes(b[do:do+32], 'big'); out.append((bool(ok), b[do+32:do+32+ln]))
    return out

# ---------- HTTP / RPC ----------
UA = {'Content-Type': 'application/json', 'User-Agent': 'q557-readonly-observer'}
ALLOWED = {'eth_chainId', 'eth_blockNumber', 'eth_getLogs', 'eth_call', 'eth_gasPrice'}  # 安全規則 2
class RpcError(Exception): pass
_locks = {}; _last = {}; _glock = threading.Lock()
def _throttle(u, min_iv=0.25):  # 1 口あたり 4 件/秒以下（安全規則 3）
    with _glock: lk = _locks.setdefault(u, threading.Lock())
    with lk:
        dt = time.time() - _last.get(u, 0)
        if dt < min_iv: time.sleep(min_iv - dt)
        _last[u] = time.time()
def http_json(url, body=None, timeout=60, tries=6):
    for k in range(tries):
        _throttle(url.split('/')[2], 0.25)
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=timeout))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504, 520, 521, 522, 524) and k < tries - 1: time.sleep(min(60, 2 ** k * 2)); continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            if k < tries - 1: time.sleep(min(60, 2 ** k * 2)); continue
            raise
class Rpc:
    def __init__(self, urls): self.urls = list(urls); self.i = 0; self.n = 0
    def call(self, method, params):
        assert method in ALLOWED, method
        last = None
        for j in range(len(self.urls)):
            u = self.urls[(self.i + j) % len(self.urls)]
            try:
                r = http_json(u, {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}); self.n += 1
            except Exception as e:
                last = e; continue
            if 'error' in r:  # 口ごとに上限や保持期間が違うので、次の口でも試してから諦める（2026-10-28 追加）
                last = RpcError(str(r['error'])[:300])
                if j < len(self.urls) - 1: continue
                raise last
            self.i = (self.i + j) % len(self.urls)
            return r['result']
        raise RpcError('all endpoints failed: ' + str(last)[:200])
    def block(self): return int(self.call('eth_blockNumber', []), 16)
    def gas_price(self): return int(self.call('eth_gasPrice', []), 16)
    def eth_call(self, to, data, blk='latest'):
        return bytes.fromhex(self.call('eth_call', [{'to': to, 'data': '0x' + data.hex()}, blk])[2:])
    def multicall(self, calls, chunk=150):
        """calls: [(target, calldata)] -> [(ok, bytes)]。allowFailure=true。"""
        out = []
        for s in range(0, len(calls), chunk):
            part = calls[s:s+chunk]
            try:
                out += dec_aggregate3(self.eth_call(MC3, enc_aggregate3(part)))
            except RpcError:
                if len(part) == 1: out.append((False, b'')); continue
                out += self.multicall(part, max(1, len(part) // 3))
        return out
    def logs(self, addrs, topics0, frm, to, span, deadline):
        """getLogs を口の上限に合わせて分割（失敗で半分、成功で倍）。"""
        res = []; cur = frm; s = span; maxs = span
        while cur <= to:
            if time.time() > deadline: raise TimeoutError('cell time limit')
            hi = min(to, cur + s - 1)
            try:
                r = self.call('eth_getLogs', [{'fromBlock': hex(cur), 'toBlock': hex(hi), 'address': addrs, 'topics': [topics0]}])
            except RpcError as e:
                if s <= 100: raise
                s = max(100, s // 2); continue
            res += r; cur = hi + 1
            if len(r) < 2000 and s < maxs: s = min(maxs, s * 2)
        return res

def cache_json(path, fn):
    if os.path.exists(path):
        with gzip.open(path, 'rt') as f: return json.load(f)
    v = fn()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path + '.tmp', 'wt') as f: json.dump(v, f)
    os.replace(path + '.tmp', path)
    return v
def short(a): return a[:8] + '…' + a[-4:]
