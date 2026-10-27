# Q557 S28 — マイナーチェーンの旧版レンディングに、清算できるのに放置された貸付けはあるか（読み取りのみの観測）

- 事前登録: `事前登録_q557.md`（2026-10-27 18:55・データを見る前に固定）。コード: `q557_lib.py`（keccak・ABI・**許可した RPC メソッドだけ**）・`q557_run.py`（本体。冒頭に事前登録からの変更点 1〜8）。
- 実行: 2026-10-28 03:47〜04:40 JST（引き継いだ Opus セッション）。スナップショット 2026-10-27 19:33 UTC。ブロック範囲は `results/run_meta_all.json`。
- 安全: 送信・署名・秘密鍵なし。呼んだ RPC は `eth_chainId / eth_blockNumber / eth_getLogs / eth_call / eth_gasPrice` だけで、清算関数は呼び出しを組み立てる段階で拒否している。
- 生データ（ログのキャッシュ 56MB）は `作業層/大容量/onchain/q557/` にあり、git には入れていない。

## 判定（事前登録）: **棄却**
- 条件を満たすセル（10 チェーン × Aave V2/V3・Compound V2 系 × チェーン別 TVL 10万〜5,000万ドル）は **25** で、上限の 60 未満なので全部調べた。
- 除外は 5 セル: **Base 4 は時間切れ**（公開 RPC の getLogs が 500 ブロック幅しか通らず、3 時間に収まらない）、**Mantle Lendle 1 は住所不明**（LendingPool の view 関数がすべて revert）。
- **調べられたセル 20**（現役 8・旧版 4・凍結 8）。**利益の出る放置は、どのセルでも 0 件**だった → 事前の文「調べられたセル ≥20 のどれにも利益の出る放置が無ければ棄却」に当たる。
- 90 日の借り手の中で清算できる状態だったのは 2 件だけで、どちらも借入が 1 セント未満のくず（見込み純益はマイナス）。

| 状態 | セル | 90 日の借り手 | 清算可能 | 利益の出る放置 | 90 日の清算 | 清算者（中央値） |
|---|---|---|---|---|---|---|
| 現役 | 8 | 945 | 2 | 0 | 2,999 | 6 |
| 旧版 | 4 | 138 | 0 | 0 | 155 | 3.5 |
| 凍結 | 8 | 8 | 0 | 0 | 3,474 | 14.5 |

- 旧版 4 セル（Radiant v2 Arbitrum・Aave V3 Linea・Extra xLend OP・Moonwell OP）の清算者は 0・5・2・17。清算者が 0 の Radiant v2 は、90 日の清算も 0 件で、借り手は 3 人だけ。

## 副（記述・判定に使わない）
- **副A（借り手に「90 日以内に清算された人」も足す）**: 母集団は 1,091 → 5,731 人、清算可能は 2 → 787 件。凍結した市場にも、清算可能な貸付けが数百件残っていた（Polygon Aave V2 195・BSC Cream 110・Gnosis Spark 47 など）。ただしどれも、①資産が凍結・停止されている、②担保がほぼ 0 の不良債権（Cream は借入 55.9 万ドルに対し担保 0.1 万ドル）、③ 1 ドル未満のくず、のどれか。
- **例外: Gnosis の RealT RMM（現役）で 130 件・見込み純益の合計 40 万ドル。** 健全度の中央値は 0.96 で、担保は RealToken（`RTW-USD-01`、不動産トークン）。RealToken は KYC を済ませた住所しか持てない許可型のトークンで、清算者は上位 1 者が 83% を占める。**誰でも清算して担保を売れる状況ではない可能性が高い（未確認）。** 事前登録の見込み純益は換金性（スリッページ・受け取りの制限）を含まないので、この数字は上限にすぎない。
- 凍結した市場では、90 日の借入が 0 件のところが多かった（Scroll Aave V3・Polygon Aave V2・Avalanche Aave V2・Spark Gnosis など）。それでも清算は活発で（Scroll 866 件・清算者 13）、残った貸付けは他の清算者が拾っている。
- ガス代は 1 回の清算（70 万 gas）あたり最大 0.59 ドル（L1 データ手数料は含まない）で、どのチェーンでも障害にならない。

## 読み
- 元記事の「旧版・終了処理中の相手は歩留まりが高い」は、**このやり方（スナップショット 1 回・設計どおりの清算だけ）では再現しなかった**。放置に見える貸付けは、凍結・不良債権・くずに分かれ、残りの普通の貸付けは清算者が数人〜数十人いて、すぐに片付けられている。
- 元記事の稼ぎは、終了処理中の相手の**一回きりの出来事**（停止の直前・直後に大きな貸付けが動く瞬間）だった可能性がある。それは静止画の観測には写らない。
- 限界: 借り手を 90 日に絞った（事前登録どおり）。365 日に広げた版は走らせていない。Base の 4 セルは見ていない。

**解釈: 棄却（S28 の「静的に放置された貸付けを拾う」形は閉じる。RealT の件だけ、許可型の担保の清算の決まりを文書で確かめる価値がある）**

## 追記（Q558・2026-10-28・文書の確認。判定は変えない）
- **RealT RMM v3 の清算は、KYC を済ませたホワイトリストの住所だけができる。** LlamaRisk（Aave ガバナンスフォーラム、2025-07-03）は「This allows whitelisted addresses (which must have completed KYC with RealT) to acquire 50%」と書いている。https://governance.aave.com/t/temp-check-add-armmwxdai-realt-rmm-xdai-deposit-token-to-aave-v3-gnosis/22378
- 担保の `RTW` は RealToken をまとめた包み（「allows users to lock their various RealTokens in exchange for `RTW-1-usd`」）。RealToken は「available only to non-US KYC'd users」。価格は鑑定で更新され、鑑定は「discretionary and not guaranteed to occur at regular intervals」。（同じ出典）
- RealT 自身のガバナンス RIP00038（2026-02-21 提案・否決 434K 対 855K）は「Liquidatable unpaid loans (HF < 1) represent a debt of $2,358,051 (as of Sunday, February 15, 2026…)」「Daily liquidations are negligible: $114/day…」と書き、清算ボーナスを 10% から 30% に上げる案を出していた。つまり**清算の放置は運営も知っている既知の状態**で、原因は誘因の不足と、清算者の制限。https://www.tally.xyz/gov/realtoken-ecosystem-governance/proposal/19298587768033104745565651921982972376376322195387053377988034262742159470150
- 参考（報道・二次）: RealT は 2026-07 に任意清算を発表し、資産の売却を予定している（cryptoactu 2026-07-04・cryptobriefing 2026-07-28）。担保の出口がさらに細っている。
- 検索語（2026-10-28）: "RealT RMM v3 RTW-USD-01 token"・"RealT RMM liquidation whitelist KYC liquidators RealTokens"・"RealT RMM v3 migration docs liquidation"・"RealT gitbook RMM v3 oracle price RealToken liquidation docs"・"RealT RMM v3 RIP governance 2026 liquidation oracle RTW bad debt" ほか。GitHub・Discord・監査の PDF は見ていない。
- **結論: 副A の RealT 130 件は、誰でも動かせる bot では清算できない（許可制）。S28 は閉じる。**
