# -*- coding: utf-8 -*-
"""Runner — ポジション型の検証の固定された流れ（2026-10-13）。

    事前登録（spec を先に保存） → 読み込み＋health → strategy（合図） → 損益 2 本（コスト 0／段階1） → 期間分割（all/pre/post）
    → 統計（年単位 t・束ねた t・Sharpe・DD・露出） → 帰無（既定: 合図の循環シフト） → 判定（既定: 3 分岐） → 保存（JSON＋CSV）

検証スクリプトが書くのは Spec と strategy（必要なら judge・null）だけ。流れの中身は変えない。
イベント研究（Q268 型: 時刻ラベルごとの平均）はこの型に入らないので、従来どおり土台の関数を直接使って書く。
"""
import dataclasses
import datetime as _dt
import json
import os
import time as _time
import warnings

import numpy as np
import pandas as pd

from . import _paths as P
from .costs import cost_bp_oneway, pnl_bp, COST_RT, CRYPTO_COST_RT_REL
from .data import load_d1, load_h1, h1_to_d1, syms_available, health
from .metrics import tstat, nw_t, sharpe_ann, max_drawdown, by_year_stats, cluster_t, fmt
from .multiple import z_of, perm_p, null_summary, holm, circ_shift, block_perm
from .io import parse_args, write_result, sanitize

PERIODS = {"all": (0, 9999), "pre": None, "post": None}  # pre/post は spec.split_year で決まる


@dataclasses.dataclass
class Spec:
    """事前登録の中身。測る前に埋めて固定する（Runner が最初に results/<qid>_spec_<ts>.json へ書く）。
    使う場面: ポジション型の検証スクリプトの冒頭。アイデア候補の行の内容をそのまま写す
    入力: qid、question、hypothesis、reject_if（判定規則の文。3 分岐）、syms、kind（"D1_fromH1"|"H1_dukascopy"|"H1→D1"）、params（掃引する設定の list。1 件なら [{}]）、main_param（判定に使う設定の添字）、n_tests（判定に使う検定の本数＝holm の m）、warmup、per_year、B、split_year、start、null_kind（"circ_shift"|"block_perm"|"none"）、null_block、null_min_shift、cost_rel、discarded、knowledge_cutoff、delegation、README 用の source・data・measure・null_desc・prior_art・batch・designer・coder、settings
    返り値: dataclass
    禁止: 結果を見てから hypothesis・reject_if・n_tests・main_param・B を変えない
    段階: 共通
    """
    qid: str
    question: str
    hypothesis: str
    reject_if: str
    syms: list = dataclasses.field(default_factory=lambda: list(P.SYMS))
    kind: str = "D1_fromH1"
    params: list = dataclasses.field(default_factory=lambda: [{}])
    main_param: int = 0
    n_tests: int = 2
    warmup: int = 0
    per_year: int = 252
    B: int = 500
    split_year: int = P.SPLIT_YEAR
    start: str = None
    cutoff_hour: int = 0
    null_kind: str = "circ_shift"
    null_block: int = 20
    null_min_shift: int = 60
    cost_rel: dict = dataclasses.field(default_factory=dict)
    discarded: str = ""
    knowledge_cutoff: str = "Claude の知識の締め切りはおよそ 2026-06。規則は固定で相場観は使わない"
    delegation: str = ""
    # README 用（/lab-plan が埋める）
    source: str = ""          # 出典（主張カード [[...]]・知見 Qxxx・原論文）
    data: str = ""            # データの説明（省略で「N 銘柄 kind」）
    measure: str = ""         # 測るもの
    null_desc: str = ""       # 帰無の説明（省略で null_kind から）
    prior_art: str = ""       # 先行研究チェック（WebSearch の日付・検索語・結果）
    batch: str = ""           # 「20案一括生成 第X弾」など
    designer: str = "Fable"
    coder: str = "Claude"
    settings: dict = dataclasses.field(default_factory=dict)

    def as_dict(self):
        return sanitize(dataclasses.asdict(self))


def default_judge(res, spec):
    """既定の 3 分岐。main_param のコスト後 bp（all15・年単位）が前後半とも >0 かつ holm 補正後 p<0.05 → 支持。全期間の z<1 → 棄却。ほか → 未確定。
    使う場面: Runner(judge=None) のとき。独自の規則にするなら同じ署名の関数を渡し、規則の文を Spec.reject_if に書く
    入力: res: Runner が組んだ結果 dict、spec
    返り値: str（"支持: …"／"棄却: …"／"未確定: …"）
    禁止: 判定に使う数を結果を見てから変えない
    段階: 判定
    """
    m = res["main"]
    pre, post, allp = m.get("pre", {}), m.get("post", {}), m.get("all", {})
    vals = [pre.get("bp_net"), post.get("bp_net"), pre.get("p_holm"), post.get("p_holm"), allp.get("z")]
    if any(v is None for v in vals):
        return "未確定: 計算できない（期間・銘柄の不足か帰無の退化）"
    if pre["bp_net"] > 0 and post["bp_net"] > 0 and pre["p_holm"] < 0.05 and post["p_holm"] < 0.05:
        return "支持: 前後半ともコスト後 bp>0 かつ Holm 補正後 p<0.05"
    if allp["z"] < 1:
        return "棄却: 全期間の z<1"
    return "未確定"


class Runner:
    """ポジション型の検証の固定された流れ。strategy(df, p, sym) -> pos（長さ len(df) の ±1/0。shift しない）だけを外から受ける。
    使う場面: 日足・時間足で合図→損益→統計→帰無→判定を行う検証。params に設定を並べると掃引し、n_tests を数える
    入力: spec: Spec、strategy: 関数、judge: (res, spec)->str（省略で default_judge）、null: (rng, pos, df, p, sym)->pos（省略で spec.null_kind）、summarize_extra: (cells, spec)->dict（結果に足す記述統計）
    返り値: Runner。run(args, rng) -> (res, csvs)、execute(argv=None) で parse_args から保存まで
    禁止: Runner の中の流れを検証ごとに書き換えない。合図側で shift しない。gap 行・years_dropped・data_health の failed を見ずに「確定」と書かない
    段階: 共通
    """

    def __init__(self, spec, strategy, judge=None, null=None, summarize_extra=None, here=None):
        self.spec, self.strategy = spec, strategy
        self.judge = judge or default_judge
        self.null_fn = null
        self.summarize_extra = summarize_extra
        self.here = here

    # ------------------------------------------------------------------ 読み込み
    def _load(self, sym, smoke, rng):
        k = self.spec.kind
        if k == "D1_fromH1":
            df = load_d1(sym, smoke, rng)
        elif k == "H1_dukascopy":
            df = load_h1(sym, smoke, rng)
        elif k == "H1→D1":
            df = h1_to_d1(load_h1(sym, smoke, rng), self.spec.cutoff_hour)
        else:
            raise ValueError(f"kind が不明: {k}")
        if self.spec.start:
            df = df[df["time"] >= pd.Timestamp(self.spec.start)].reset_index(drop=True)
        return df

    def _cost(self, sym, close):
        rel = self.spec.cost_rel.get(sym)
        if rel is None and sym not in COST_RT:
            rel = CRYPTO_COST_RT_REL
        return cost_bp_oneway(sym, close, rel=rel)

    # ------------------------------------------------------------------ 合図 → 損益
    def _cells(self, dfs, rng, null=False):
        """銘柄 × 設定の損益表（行＝足）。null=True なら合図を帰無化してから損益にする。"""
        frames = []
        for sym, df in dfs.items():
            c = df["close"].values; cb = self._cost(sym, c); zero = np.zeros(len(c))
            for i, p in enumerate(self.spec.params):
                pos = np.asarray(self.strategy(df, p, sym), float)
                if len(pos) != len(c):
                    raise ValueError(f"strategy の返り値の長さが違う: {sym} {len(pos)} != {len(c)}")
                if null:
                    pos = self._null_pos(rng, pos, df, p, sym)
                g, n = pnl_bp(pos, c, zero), pnl_bp(pos, c, cb)
                if self.spec.warmup:
                    g[: self.spec.warmup + 1] = np.nan; n[: self.spec.warmup + 1] = np.nan
                frames.append(pd.DataFrame({"time": df["time"].values, "year": df["year"].values, "sym": sym, "param": i,
                                            "gap": df["gap"].values if "gap" in df else False,
                                            "pnl_gross": g, "pnl_net": n, "exp": np.abs(np.r_[0.0, pos[:-1]])}))
        return pd.concat(frames, ignore_index=True)

    def _null_pos(self, rng, pos, df, p, sym):
        if self.null_fn is not None:
            return self.null_fn(rng, pos, df, p, sym)
        k = self.spec.null_kind
        if k == "circ_shift":
            return circ_shift(rng, pos, min_shift=self.spec.null_min_shift)
        if k == "block_perm":
            return block_perm(rng, pos, self.spec.null_block)
        if k == "none":
            return pos
        raise ValueError(f"null_kind が不明: {k}")

    # ------------------------------------------------------------------ 統計
    def _periods(self):
        sy = self.spec.split_year
        return {"all": (0, 9999), "pre": (0, sy), "post": (sy, 9999)}

    def _stat_block(self, cells, y0, y1):
        d = cells[(cells["year"] >= y0) & (cells["year"] < y1)]
        if d.empty:
            return None
        bys_n = by_year_stats(d, "pnl_net", y0=y0, y1=y1)
        bys_g = by_year_stats(d, "pnl_gross", y0=y0, y1=y1)
        pool = d.groupby("time")[["pnl_net", "pnl_gross"]].mean()
        cl = cluster_t(d, "pnl_net", by="time")
        return {"n_years": bys_n["n_years"], "years_dropped": bys_n["years_dropped"], "n_bars": int(d["pnl_net"].notna().sum()),
                "bp_gross": fmt(bys_g["mean"]), "t_gross": fmt(bys_g["t"]),
                "bp_net": fmt(bys_n["mean"]), "t_year": fmt(bys_n["t"]), "t_cluster": fmt(cl["t"]),
                "sharpe_net": fmt(sharpe_ann(pool["pnl_net"].values, self.spec.per_year)),
                "sharpe_gross": fmt(sharpe_ann(pool["pnl_gross"].values, self.spec.per_year)),
                "max_dd_net_bp": fmt(max_drawdown(pool["pnl_net"].values)),
                "exposure": fmt(d["exp"].mean()), "gap_bars": int(d["gap"].sum()), "_bp_net_raw": bys_n["mean"]}

    def _summarize(self, cells):
        out = {}
        groups = {g: m for g, m in P.GROUPS.items()} if set(self.spec.syms) == set(P.SYMS) else {"all": list(self.spec.syms)}
        for i, _ in enumerate(self.spec.params):
            ci = cells[cells["param"] == i]
            for g, members in groups.items():
                cg = ci[ci["sym"].isin(members)]
                for pn, (y0, y1) in self._periods().items():
                    b = self._stat_block(cg, y0, y1)
                    if b is not None:
                        out[(i, g, pn)] = b
        return out

    # ------------------------------------------------------------------ 実行
    def run(self, args, rng):
        """計算して (res, csvs) を返す。write はしない（execute が行う）。"""
        spec = self.spec; t0 = _time.time()
        syms, missing = syms_available(spec.syms, kind=spec.kind.replace("H1→D1", "H1_dukascopy"), smoke=args.smoke)
        dh = None if args.smoke else health(syms, kind=spec.kind.replace("H1→D1", "H1_dukascopy"))
        dfs = {s: self._load(s, args.smoke, rng) for s in syms}
        cells = self._cells(dfs, rng)
        obs = self._summarize(cells)
        main_group = "all15" if set(spec.syms) == set(P.SYMS) else "all"
        # 帰無: main_param の main_group の bp_net（年単位）を B 回
        keys = [(spec.main_param, main_group, pn) for pn in self._periods()]
        null = {k: [] for k in keys}
        if spec.null_kind != "none" and args.B > 0:
            for b in range(args.B):
                nc = self._cells(dfs, rng, null=True)
                nc = nc[(nc["param"] == spec.main_param) & (nc["sym"].isin(P.GROUPS.get(main_group, spec.syms)))]
                for k in keys:
                    y0, y1 = self._periods()[k[2]]
                    st = by_year_stats(nc, "pnl_net", y0=y0, y1=y1)
                    null[k].append(st["mean"])
        # 判定に使う本数 = n_tests（pre/post の 2 本が既定）。holm は pre/post の perm_p に掛ける
        main = {}
        pvals = {}
        for k in keys:
            b = obs.get(k)
            if b is None:
                continue
            ns = null_summary(b["_bp_net_raw"], null[k]) if null[k] else {"z": None, "pct": None, "p_perm": None, "degenerate": None, "B": 0}
            main[k[2]] = {kk: v for kk, v in b.items() if not kk.startswith("_")}
            main[k[2]].update({"z": fmt(ns["z"]), "pct": fmt(ns["pct"]), "p_perm": fmt(ns["p_perm"]), "null_degenerate": ns["degenerate"],
                               "null_q025": fmt(ns.get("q025")), "null_q975": fmt(ns.get("q975"))})
            if k[2] in ("pre", "post"):
                pvals[k[2]] = ns["p_perm"] if ns["p_perm"] is not None else np.nan
        if pvals:
            # n_tests が宣言より多い本数なら、宣言の方に合わせず警告する
            m = max(spec.n_tests, len(pvals))
            padded = list(pvals.values()) + [np.nan] * (m - len(pvals))  # 宣言した本数ぶん補正（NaN は m に数える）
            adj = holm(padded)
            for (pn, _), a in zip(pvals.items(), adj):
                main[pn]["p_holm"] = fmt(a)
        summary = {f"p{i}_{g}_{pn}": {kk: v for kk, v in b.items() if not kk.startswith("_")} for (i, g, pn), b in obs.items()}
        res = {"question": spec.question, "spec": spec.as_dict(), "missing": missing, "data_health": dh,
               "main": main, "summary": summary,
               "multiple_comparisons": f"判定は main_param={spec.main_param}・{main_group} の前後半 {len(pvals)} 本（宣言 n_tests={spec.n_tests}、Holm で補正）。ほかの設定・群は記述。",
               "elapsed_s": round(_time.time() - t0, 1)}
        if self.summarize_extra is not None:
            res["extra"] = sanitize(self.summarize_extra(cells, spec))
        res["machine_verdict"] = self.judge(res, spec)
        if dh and (dh["failed"] or dh["gaps"]):
            res["machine_verdict"] += "（data_health に failed/gaps あり: 確定にする前に点検）"
        yr = cells.groupby(["param", "sym", "year"])[["pnl_gross", "pnl_net", "exp"]].mean().reset_index()
        return res, {"year_sym": yr}

    def execute(self, argv=None, extra_args=None, script=None):
        """parse_args → spec を先に保存 → run → write_result。スクリプトの main() から呼ぶ。`--readme` なら README.md を生成して終わる（実行しない）。"""
        import sys as _sys
        from .readme import render_readme
        spec = self.spec
        here = self.here or P.script_dir()
        script = script or os.path.basename(_sys.argv[0] if _sys.argv and _sys.argv[0] else "kensho.py")
        av = list(argv) if argv is not None else _sys.argv[1:]
        if "--readme" in av:
            path = os.path.join(here, "README.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(render_readme(spec, script))
            print("wrote", path); return path, None

        def _extra(ap):
            ap.add_argument("--readme", action="store_true", help="README.md を SPEC から生成して終わる")
            if extra_args:
                extra_args(ap)
        args = parse_args(default_B=spec.B, extra=_extra, argv=argv)
        rng = np.random.default_rng(args.seed)
        out = os.path.join(here, "results"); os.makedirs(out, exist_ok=True)
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        pre = f"smoke_{spec.qid}" if args.smoke else spec.qid
        with open(os.path.join(out, f"{pre}_spec_{ts}.json"), "w", encoding="utf-8") as fh:  # 事前登録を先に書く
            json.dump({"qid": spec.qid, "registered": ts, "B": args.B, "seed": args.seed, **spec.as_dict()}, fh, ensure_ascii=False, indent=1)
        res, csvs = self.run(args, rng)
        res["spec"]["B_used"] = args.B; res["spec"]["seed"] = args.seed
        path = write_result(spec.qid, res, args.smoke, csvs, here=here)
        print("machine_verdict:", res["machine_verdict"])
        return path, res
