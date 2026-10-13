# Q288: D1_fromH1 の WTI・UKOIL・US500・USTECH にある 2011-09〜2012-01 の空白は取得失敗か提供元の欠落か

事前登録: 検証キュー Q288（2026-10-13）。fe_core.health の初回実行で検出（REVIEW_20261013.md）。

- **データ**: D1_fromH1 および D1_dukascopy（WTI・UKOIL・US500・USTECH）、H1_dukascopy（WTI・US500）
- **測るもの**: ① gap の根本原因（H1 取得失敗 or 提供元欠落）、② 既存検証（tsmom12m-ma200-cash-rule Q151）の gap 行での position → 結論変化の有無
- **帰無**: なし（データ点検）
- **出典**: fe_core.health 初回実行結果（REVIEW_20261013.md 「固定後に実データで分かったこと」）

## 設計

**H1 根本原因の確認**

- D1_fromH1 の gap 期間に D1_dukascopy がデータを持つ → 提供元の欠落ではない
- 同 gap 期間の H1_dukascopy が high==low（flat 行）→ H1 取得失敗が原因

**既存検証への影響確認**

- gap 行の直前 t-1 での pos（tsmom12m-ma200-cash-rule の規則: 12m リターン>0 かつ SMA200 超え）を計算
- pos=0 なら gap 行の ret は PnL に入らない

## gap の詳細

| 銘柄 | gap 期間 | 時間数 | gap 行 ret |
|------|----------|--------|------------|
| WTI | 2011-09-23 → 2011-11-10 | 1152h (48日) | +23.7% |
| US500 | 2011-09-22 → 2012-01-16 | 2784h (116日) | +15.0% |
| USTECH | 2011-09-22 → 2012-01-19 | 2856h (119日) | +12.4% |
| UKOIL | 計5本（最大 672h=28日） | — | +1.0%〜+5.3% |

## 結果

**H1（根本原因）**: 支持

- D1_dukascopy は WTI 2011-09〜11 に 60 行以上のデータを持つ（WTI 約 $79〜$99 の価格帯）
- WTI の H1 ソースは同期間 1153 行中 1147 行（99.5%）が flat（high==low）、非 flat 6 行は gap 開始直後の 2011-09-23 のみ
- US500 も同様（同期間中 2785 行中 2777 行が flat）
- **結論: H1 データの取得失敗が原因。提供元（Dukascopy D1）は欠落していない。**

**H2（既存検証への影響）**: 支持

- tsmom12m-ma200-cash-rule (Q151) の gap 行前日 pos:
  - WTI 2011-11-10: pos=0（cash。mom12m < 0: 下落相場）
  - US500 2012-01-16: pos=0（cash）
  - USTECH 2012-01-19: pos=0（cash）
  - UKOIL 2011-11-15: pos=0（cash）
  - UKOIL 2013-02-26: **pos=1** (mom12m=+5.8%, close > SMA200)、ret=-4.9%、effect=-494bp
- **大きな gap（2011-2012）は全て cash 保持 → PnL ゼロ影響**
- UKOIL 2013-02-26 は pos=1 だが effect=-494bp（MDD -98,622bp の 0.5%）→ 棄却判定は変わらない

## 判定

判定: **確定: H1 取得失敗が根本原因。2011-2012 の大 gap 行は tsmom12m 既存検証の PnL に影響しない（cash 保持）。UKOIL の小 gap（2013-02-26）は -494bp だが棄却判定に変化なし。**

## 結果ファイル

- `results/Q288_result_20261014_010425.json`: gap 詳細・H1 flat 確認・tsmom12m 各 gap 行の pos
