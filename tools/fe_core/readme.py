# -*- coding: utf-8 -*-
"""検証フォルダの README を Spec から生成する（「Q204 の形」の正本。2026-10-13）。
人が手で書くときの写しは `検証/_基盤/知識/_テンプレ/検証README.md`。実行後の「結果」の節は人（/lab）が書く。"""
import datetime as _dt

TEMPLATE = """# {qid} {question}

事前登録: `検証/学問/金融工学/知識/文献/アイデア候補.md` の {qid} の行（{designer}・{batch}）。出典: {source}

- スクリプト: `{script}`（`fe_core` {script_kind}。事前登録の内容は `SPEC` に固定。`python3 {script} --readme` でこの README を再生成）
- データ: {data}（`検証/学問/金融工学/作業/FX/システムトレード/data_*.csv`。無い銘柄は除いて JSON の `missing` に。欠損の点検は JSON の `data_health`）
- 実行: `python3 {script}`（B={B}{elapsed}。pandas/numpy のみ）
- 試走: `--B 10`。経路の確認だけなら `--smoke`（合成データ・結果は `results/smoke_*`。**判定には使わない**）
- 結果: `results/{qid}_spec_<日時>.json`（実行前に書かれる事前登録）・`results/{qid}_result_<日時>.json`（設定・集計・`data_health`・機械判定 `machine_verdict`）・`results/{qid}_year_sym_<日時>.csv`

## 状態（{today}）

**{status}**
Sonnet／Opus が実行するときの手順:

1. 標準手順H の 3「出口で検証するときの決まり」どおり、`SPEC`（仮説・判定・捨てた案の数・知識の締め切り・委託の確かめ方）を読んでから走らせる（変更しない）。
2. `python3 {script}` を Mac で実行。
3. JSON の `machine_verdict` は事前固定の規則で機械的に付けたもの。**確定／ノイズ／未確定** の解釈は実行者が書く（下の「結果」の節に `判定: **…**` の形で）。`data_health` に failed／gaps があれば、該当銘柄・期間を除いた結果も見てから書く。`years_dropped`・`null_degenerate` も確かめる。
4. 記録先: 知見ノート（＋知見一覧.jsonl）、出典の主張カードの `自分の検証`、アイデア候補の状態、FX 改善ログ（FX のとき）、検証キュー {qid} を完了へ、`gen_fe_index.py` で一覧を更新。

## 方法（要点）

- 仮説: {hypothesis}
- 測るもの: {measure}
- 帰無: {null_desc}
- 多重比較: 判定は {n_tests} 本（Holm で補正）。ほかの設定・群は記述
- 先行研究チェック: {prior_art}
- 捨てた案の数: {discarded}
- 知識の締め切り: {knowledge_cutoff}
- 委託の確かめ方: {delegation}

## 判定（事前固定）

{reject_if}

## 結果

未実行。
"""


def render_readme(spec, script, status=None, script_kind="Runner 型", elapsed=None, today=None):
    """Spec から README.md の本文を作る。
    使う場面: /lab-plan のコーディング時（`python3 <script> --readme`）。実行後の結果の節は人が書く
    入力: spec: Spec、script: スクリプトのファイル名、status: 状態の 1 文（省略で「設計とコードまで。実行と解釈は未」）、script_kind: "Runner 型"|"土台を直接使う型"、elapsed: 実行時間のメモ、today: 日付
    返り値: str（Markdown）
    禁止: 結果の節をここで埋めない（解釈は人）
    段階: 保存
    """
    today = today or _dt.date.today().isoformat()
    st = status or f"設計（{spec.designer}）とコード（{spec.coder}）まで。実行と結果の解釈は未。** コードはクラウド側で `--smoke --B 5` の経路確認だけ済み（合成データ・判定には使わない）。**"
    return TEMPLATE.format(
        qid=spec.qid, question=spec.question, designer=spec.designer, batch=spec.batch or "単発", source=spec.source or "（未記入）",
        script=script, script_kind=script_kind, data=spec.data or f"{len(spec.syms)} 銘柄 {spec.kind}", B=spec.B,
        elapsed=f"・{elapsed}" if elapsed else "", today=today, status=st, hypothesis=spec.hypothesis,
        measure=spec.measure or "（未記入）", null_desc=spec.null_desc or f"{spec.null_kind}（min_shift={spec.null_min_shift}, block={spec.null_block}）",
        n_tests=spec.n_tests, prior_art=spec.prior_art or "（未記入。WebSearch の日付・検索語・見つかった研究と未確認の点を書く）",
        discarded=spec.discarded or "（未記入）", knowledge_cutoff=spec.knowledge_cutoff, delegation=spec.delegation or "（未記入）", reject_if=spec.reject_if)
