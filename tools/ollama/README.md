# tools/ollama — ローカル LLM（Ollama）に下ろす作業（2026-10-13・Mac だけで回す版）

目的: Claude（Sonnet）のトークンを、**判断を含まない・Python で検品できる**作業から外す。壁打ち（2026-10-13）の「Local LLM → 自動テスト → 合格したものだけ Claude」の実装。
いまの検証キューの大半（c: 読む・主張カード化）が対象。

## 仕組み

```
Claude（device_bash）: make_job.py quotes --inv 95   → 検証/自動実行/llm/pending/<id>.json
        ↓
Mac のターミナル: ollama_loop.py --once | --watch 120
        pending → running → 本文を抜く（pypdf / pdftotext / md）→ Ollama にページ 3 枚ずつ投げる
        → 返った引用を原文と照合（正規化後の完全一致、または先頭 60 字＋末尾 60 字が同じページ）
        → 実在するものだけ 文献/_ローカルLLM/<label>_quotes.{json,md} に書く → done（失敗は failed に理由）
        ↓
Claude: _ローカルLLM/<label>_quotes.md を読む（本文全体ではなく、照合済みの引用だけ）→ 主張カードにするかを判断
```

**device_bash の Linux VM から Mac の Ollama（localhost:11434）には届かない。** だからループは Mac 本体で動かす（`自動実行/lab_loop.sh` と同じ置き方）。

## Mac の準備（1 回）

1. Ollama を入れる: https://ollama.com からインストール（または `brew install ollama`）。`ollama serve` が動いていること（アプリ起動で自動）。
2. モデル: `ollama pull qwen3:8b`（M2 16GB の既定・約 5GB。思考モードはループが切る）。訳の質が足りなければ `ollama pull gemma3:12b`（約 8GB。他のアプリを閉じる）、コード生成（後日）は `qwen2.5-coder:7b`。30B 級は 16GB に入らない。**モデル名は ollama.com/library か `ollama list` で確認**（この README の名前は 2026-06 時点の知識）。
3. PDF 用: `pip3 install --user pypdf`（無ければ `pdftotext` を探す。どちらも無いと failed になる）。

## 使い方

Mac のターミナル:
```
cd ~/ワークスペース/検証/verification-lab/tools/ollama
python3 ollama_loop.py --once                 # 溜まった pending を処理して終わる
python3 ollama_loop.py --watch 120            # 2 分ごとに見に行く（Claude が置いたジョブを順に処理）
python3 ollama_loop.py --once --model qwen2.5:14b
python3 ollama_loop.py --once --mock          # Ollama 無しで経路と検品だけ試す（出力は _ローカルLLM/_mock/）
```
Claude 側（device_bash）:
```
python3 make_job.py quotes --inv 95 --focus "取引コスト後の収益・公表後の減衰"
python3 make_job.py quotes --src 検証/学問/金融工学/知識/文献/Web保存/xxx.md --label QuanterLab2026
python3 make_job.py translate --from-quotes 検証/学問/金融工学/知識/文献/_ローカルLLM/ID95_quotes.json
python3 make_job.py list
```

## 種類

| kind | 入力 | 出力 | 検品 |
|---|---|---|---|
| `quotes` | 入荷台帳の ID（PDF／Web保存を自動で探す）か `--src` | 引用（ページ・種別・1 文の要点）の json と md | **引用が原文に実在するか**。実在しないものは `rejected` に理由つきで残す（黙って捨てない） |
| `translate` | quotes の json | 各引用の訳（`ローカル訳（未確認）`） | 訳語表（`_基盤/知識/概念/` のノート名）を prompt に渡す。訳の正しさは検品できないので、主張カードに使うときは Claude が原文と照合（委託ルールの抜き取り 2 件） |

## 守ること

- **判断を下ろさない**: 主張カードにするか、接続、Spec の設計、確定／ノイズ／未確定、先行研究チェックは Claude。
- 出力は材料。`_ローカルLLM/` のファイルを論文ノート・主張カードにそのまま昇格させない。
- `failed` は Claude が見て、その 1 件だけ自分でやる（空の結果を成功に見せない）。
- 効果の記録: `_基盤/知識/定期タスク.md` の「委託の記録」に、1 件あたりの Sonnet 消費（下ろす前／後）と、抜き出しの採用率（照合済み引用のうち主張カードに使った割合）を残す。4 週間後に見直す。

## 次の候補

- `strategy` kind: `Spec` から `strategy(df, p, sym)` を書かせ、`py_compile`＋`--smoke --B 3` を通ったものだけ Claude に渡す（fe_core の Runner 型が前提）。
- `summary` kind: 入荷台帳の新着の 1 行要約・分野タグ（事前点数の機械的な部分）。
- windesk（RTX 3060）に広げるときは lab-ops の `resource: llm` にする（Mac で型が固まってから）。
