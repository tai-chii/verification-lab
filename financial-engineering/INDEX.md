# financial-engineering 検証一覧

> このファイルは `python3 tools/gen_fe_index.py` で自動生成しています。手で編集しないでください。

全 248 件。判定の「—」は未実行または README に判定の記載がないもの。詳細は各ディレクトリの README を参照。

| ディレクトリ | 問い | 判定 |
| :--- | :--- | :--- |
| [52week-high-vs-momentum](./52week-high-vs-momentum) | Q214 52 週高値への近さは 15 銘柄の翌月リターンを 12 か月モメンタムより予測するか（George・Hwang 2004 の型） | 棄却側の確定 |
| [adx-filter-tsmom](./adx-filter-tsmom) | Q246 ADX(14) > 25 の局面に限ると、順張りの純損益は上がるか（15 銘柄・月ブロック並べ替え帰無） | 棄却: 局面フィルタでは変わらない（Q142・Q221 と同じ） |
| [alt-btc-relative-strength](./alt-btc-relative-strength) | Q263 アルトコインの対 BTC 相対強弱（4 週）は翌週の相対リターンを予測するか（10 通貨の横断・順位並べ替え帰無） | 棄却: 全期間 z<2 |
| [anti-equity-curve](./anti-equity-curve) | Q254 逆エクイティカーブ（直近20日損益が負なら規模1.5）は Q210 の負の自己相関を利益に変えるか（15銘柄） | 棄却: Q210 の負の自己相関は利益にできない |
| [asian-range-breakout](./asian-range-breakout) | Q220 アジア時間（0〜7 UTC）のレンジを欧州時間に抜けたら終値まで続くか（FX8 H1・ブレイクアウト） | 棄却 |
| [atr-stop-loss-tsmom](./atr-stop-loss-tsmom) | Q204 ATR 倍の損切りは 15 銘柄の日足順張りの純損益と最大下落を改善するか（Kaminski・Lo 2014 の型） | 未確定（純損益の改善なし）／最大下落は確実に改善（記述） |
| [bad-period-weighted-selection](./bad-period-weighted-selection) | Q141 悪い時期を重くする目的関数で選んだ順張りは、標本外の最大下落が小さいか（TradeGrad の CPRO の型） | 棄却（確定） |
| [bars-per-year-audit-wide48-q418](./bars-per-year-audit-wide48-q418) | Q418 48 銘柄 D1_fromH1 の銘柄×年の足の本数の一覧と、本数 126 未満の年を年単位 t から除くと TSMOM60 等金額の前後半 t がどれだけ動くか（by_year_stats の min_rows 既定の見直し） | 支持 |
| [bb-squeeze-vol-increment-wide48-q451](./bb-squeeze-vol-increment-wide48-q451) | Q451 BB幅収縮度のボラ予測への増分（wide48 D1） | 実質的に増分なし |
| [bbc-cv-optimism](./bbc-cv-optimism) | Q172 BBC-CV のブートストラップ補正は時系列の順張り選択の楽観を取り除くか（Tsamardinos 2018） | —（未実行） |
| [bbc-cv-tsmom-optimism](./bbc-cv-tsmom-optimism) | Q172 BBC-CV のブートストラップ補正は時系列の順張り選択の楽観を取り除くか（Tsamardinos 2018） | 確定 |
| [bid-ask-signal-fragility](./bid-ask-signal-fragility) | Q185 合図は bid か ask かで何割変わるか（XAUUSD 実測＋15銘柄の半スプレッドの擬似ずらし） | 未確定（機械判定）／解釈: 規則の型による |
| [bollinger-mean-reversion-d1](./bollinger-mean-reversion-d1) | Q293 15 銘柄 D1 のボリンジャー平均回帰（+2σ 売り・−2σ 買い、SMA20 戻りで決済）は all15 の年単位平均 bp（コスト後）が前後半とも正か（Coakley2016-2 の D1 移植） | 棄却 |
| [breakeven-cost-vs-spread](./breakeven-cost-vs-spread) | Q140 順張りの損益分岐コストは実測スプレッドの何倍か（XAUUSD の Ask データで容量・コスト曲線） | TSMOM20・ドンチャン55/20 とも未確定 |
| [close-location-next-day](./close-location-next-day) | Q237 終値位置 CLV が極端な日の翌日は、続くか反転するか（15 銘柄・Holm） | 棄却 |
| [cluster-t-h1-shrinkage](./cluster-t-h1-shrinkage) | Q295 15 銘柄 H1 のクラスター t（時刻束ね）は naive パネル t より 30% 以上縮むか | ノイズ |
| [cluster-t-shrinkage](./cluster-t-shrinkage) | Q175 15銘柄を束ねた t は日でクラスタさせると素朴な t から何割下がるか（GarciaArano 2026-3） | 支持（確定） |
| [commodity-currency-leadlag](./commodity-currency-leadlag) | Q241 原油→USDCAD・金→AUDUSD の日次リード・ラグは、両方向のどちらが強いか（Chen・Rogoff・Rossi 2010 の逆向き） | 棄却: どちらの組も一方向の先導なし |
| [common-perm-rejudge-q322](./common-perm-rejudge-q322) | Q322 銘柄ごとの年内並べ替えを束ねて「支持・確定」とした Q183・Q212・Q205 を、日付共通の並べ替えで再判定する（Q321 の次段階） | z は 3 件とも 0.4〜0.9 倍に縮んだ（帰無が広がった）。週末ラベルが全通貨で同じ Q212 は後半で 1/2… |
| [common-perm-size-q321](./common-perm-size-q321) | Q321 束ねた年内並べ替えを全銘柄共通の（日付の）並べ替えにすると、腕なしの合成でサイズが名目 5% に戻るか（Q320 の次段階） | 銘柄ごとの年内並べ替えは、現実型の帰無でも膨らむ（12.4%）。Q320 の 16% は合成の作りだけのせいではない。… |
| [correlation-regime-tsmom](./correlation-regime-tsmom) | Q258 15銘柄の直近60日平均ペア相関が高い月は順張り束のシャープが低いか（相関レジーム） | 棄却 |
| [cpro-exact-selection](./cpro-exact-selection) | Q168 CPRO 本式（Yang 2026 TradeGrad の正格な実装）で順張りの参照日数を選んでも、翌年の最大下落は A と区別がつかない | 棄却（確定） |
| [crisis-alpha-tsmom](./crisis-alpha-tsmom) | Q207・Q224 危機アルファ：US500 の下落局面で順張りは正の損益か（Hurst・Ooi・Pedersen 2017 の型） | 原典型 TSMOM（1/3/12か月合成・σ60値幅目標）は US500 の下落局面で合計 +189 bp・6 局面中… |
| [cross-market-leadlag-h1](./cross-market-leadlag-h1) | Q236 4 組（XAU→XAG・WTI→UKOIL・BTC→ETH・US500→USTECH）の H1 リード・ラグは、両方向のどちらが強いか | 棄却: 1 組以下 |
| [cross-sectional-vs-ts-momentum](./cross-sectional-vs-ts-momentum) | Q218 横断モメンタム（15 銘柄の上位 5 買い・下位 5 売り）は時系列モメンタムとコスト後にどれだけ違うか（Moskowitz ほか 2012 の型） | ノイズ（前後半で揃った差はない） |
| [cross-signal-tsmom](./cross-signal-tsmom) | Q256 クロス・シグナル（金→銀・WTI→UKOIL・US500→USTECH・BTC→ETH）の日足順張りは自身の合図より良いか | 棄却: 主はリードしない（4 組とも全期間 ／z／<2） |
| [crypto-basis-gate-s23-q569](./crypto-basis-gate-s23-q569) | Q569 暗号資産の四半期先物の年率ベーシスが高い日に S23 を休むと、S23 の損益は上がるか | — |
| [crypto-d1-tsmom](./crypto-d1-tsmom) | Q262 暗号資産11通貨の日足順張り（TSMOM 20/60/120）は 2022 年以降もコスト後に残るか | 最初から無い: 前半 t<2（別の確定） |
| [crypto-h1-reversal-vol](./crypto-h1-reversal-vol) | Q183 暗号資産の1時間足の逆張りの見返りは直前のボラで予測できるか（Farag 2024-1・11通貨） | ボラは1時間逆張りの粗利を予測する（Farag 2024-1 の H1 版）。ただし後半で係数が3〜4倍小さくなり、保… |
| [crypto-h1-rules-battery](./crypto-h1-rules-battery) | Q298 暗号資産 11 通貨 H1 の 3 ルール群（TSMOM24・SMA50・RSI14 の 50 水準順張り）はコスト後に全て前後半で正か（Neely2003-2 の暗号 H1 移植） | 棄却 |
| [crypto-h1-tsmom](./crypto-h1-tsmom) | Q290 暗号資産 11 通貨 H1 の 24 本 TSMOM（L=24）はコスト後に前後半とも正か（Neely2003-3 の暗号 H1 移植） | 棄却 |
| [crypto-hour-of-day](./crypto-hour-of-day) | Q242 暗号資産 11 通貨の UTC 時刻効果は、Holm 補正後に前後半で同符号で残るか | 棄却: 前後半で同符号に残る時刻は 0 |
| [crypto-ma200-drawdown](./crypto-ma200-drawdown) | Q302 暗号資産 11 通貨日足の 200 日線（終値>SMA200 で買い・下で現金）の最大下落は同じ露出の循環シフトより浅いか（Q097/Q098 の暗号資産への移植） | 棄却 |
| [crypto-rsi2-dip](./crypto-rsi2-dip) | Q304 暗号資産 11 通貨日足の RSI2 押し目買い（RSI2<10 かつ終値>SMA200 で買い・終値>SMA5 で手仕舞い）はコスト後に前後半とも正か | 棄却 |
| [crypto-variance-ratio-trend](./crypto-variance-ratio-trend) | Q264 暗号資産11通貨の H1 の分散比は 2022 年以降に 1 へ近づいたか（適応的市場仮説の移植） | 棄却 |
| [crypto-weekend-effect](./crypto-weekend-effect) | Q212 暗号資産の週末（土日）はリターン・ボラ・順張りの損益が平日と違うか（11 通貨 H1） | 棄却 |
| [currency-strength-cross-redundancy](./currency-strength-cross-redundancy) | Q299 通貨強度（対ドル 6 本の L 本リターン平均・7 通貨）は、クロス 2 本（EURJPY・GBPJPY）を足した最小二乗版と H1 の L=24/120/480 時間で相関 0.99 以上か（クロスは冗長か） | 確定（支持: クロスは冗長） |
| [currency-strength-session-entry](./currency-strength-session-entry) | Q301 強度スプレッドの合図のエントリーをロンドン・NY 重複帯（NY 8〜12 時・8:30 ET の足の確定後）に限ると、1 トレードのコスト後期待値は即時エントリーとランダム時間窓の帰無を上回るか（全体／前半 3 時間・H1 執行・24 時間保有） | 棄却 |
| [currency-strength-spread-quintile](./currency-strength-spread-quintile) | Q300 7 通貨の強度ランキングの最強−最弱スプレッド（4H・L=30 本・ボラ正規化）の上位五分位は、翌 6 本（1 日）の合成リターンがコスト後に継続か反転か | 棄却 |
| [d1-fromh1-gap-check](./d1-fromh1-gap-check) | Q288: D1_fromH1 の WTI・UKOIL・US500・USTECH にある 2011-09〜2012-01 の空白は取得失敗か提供元の欠落か | H1 データの取得失敗が原因。提供元（Dukascopy D1）は欠落していない |
| [daily-cutoff-hour-dependence](./daily-cutoff-hour-dependence) | Q211 日足の区切り時刻（0・8・13・17・21 UTC）で順張りの純損益はどれだけ変わるか（帰無: 区切りをランダムに選ぶ） | 棄却 |
| [data-source-signal-agreement](./data-source-signal-agreement) | Q137 データ提供元の違い（Dukascopy vs Yahoo）で順張りの合図は何割一致し、純損益はどれだけ変わるか | 「データ源は規則の定義の一部（Korzan と同じ）」→ 確定 |
| [day-of-week-15](./day-of-week-15) | Q206 曜日効果は 15 銘柄の日足で 2017 年以降も残るか（曜日ラベル並べ替え・Holm） | 棄却（Q206・2026-10-10・15銘柄 D1 2008-02〜2026-07・B=500・SPLIT_YEAR… |
| [deflated-sharpe-lookback](./deflated-sharpe-lookback) | Q260 参照日数60通りから選んだ最良は Deflated Sharpe Ratio で補正すると何銘柄で残るか（Bailey・López de Prado 2014） | 効果なし（支持＝最良の参照日数は DSR 補正で残らない） |
| [direction-accuracy-vs-base-rate](./direction-accuracy-vs-base-rate) | Q147 翌日の方向の的中率は「常に上」「前日の符号」の基準率を超えるか（HSAT の基準の置き方） | 確定 |
| [dollar-factor-momentum](./dollar-factor-momentum) | Q208 ドル因子（6 通貨の対ドル等加重）の順張りは個別ペアの順張りの平均より強いか（Verdelhan 2018 の型） | 棄却 |
| [dow-structure-direction-vs-time](./dow-structure-direction-vs-time) | Q104 ダウ型の構造確定の後の24時間: 向きの情報か、時刻と地合いか | 棄却（向きの情報なし） |
| [dual-lookback-rotation](./dual-lookback-rotation) | Q292 15 銘柄 D1 の二周期ローテーション規則（L=20 と L=120 の TSMOM が同符号時のみ ±1）は、単独 TSMOM60 より all15 の年単位平均 bp（コスト後）が高いか（Korzan2026-1 の規則の移植） | 15 銘柄平均で見ると支持だが、群で分かれる |
| [ecb-fix-vshape](./ecb-fix-vshape) | Q268 ECB 参照レート（14:15 CET）の前後にドルの V 字はあるか（Krohn 2024 のロンドン fix の移植・FX6 H1） | 未確定 |
| [eia-release-followthrough](./eia-release-followthrough) | Q269 EIA 原油在庫発表（水曜 10:30 ET）直後 1 時間の向きは次の 2〜4 時間に続くか（WTI・UKOIL H1） | 要確認 |
| [eia-release-pool-q280](./eia-release-pool-q280) | Q280 EIA 原油在庫発表の実発表日に揃えた WTI・UKOIL の継続性再検証（2 銘柄プール） | WTIで継続側・時代効果と銘柄間の揃いが条件を欠く |
| [embargo-length-effect](./embargo-length-effect) | Q155 検証とテストの間のエンバーゴ日数で順張りの標本外成績はどれだけ変わるか | e=0 に楽観の方向はあるが、事前登録の第一指標が有意に届かなかった |
| [equities-free-data-q562](./equities-free-data-q562) | Q562 日本株・米国株の無料データ層（基盤・2026-10-28） | 価格層は基盤として通過、需給層は未達（毎日蓄積中） |
| [equity-curve-trading](./equity-curve-trading) | Q210 エクイティカーブ・トレーディング（戦略の直近損益で規模を変える）は 15 銘柄の順張りの標本外成績を上げるか | 棄却 |
| [execution-delay-effect](./execution-delay-effect) | Q156 約定を1〜2営業日遅らせると順張りの成績はどう変わるか（Korzan 2026 表5 では遅れで改善した） | 遅れで改善するのは Korzan のユニバース（二周期の株式ローテーション）に固有の性質。FX／商品／指数／BTC の… |
| [execution-hour-spread](./execution-hour-spread) | Q245 XAUUSD 順張りの約定時刻を、実測スプレッドの狭い時間に移すと純損益は上がるか | 棄却: 前後半のどちらかで t<2 または z<2 |
| [friday-last-hour-reversal](./friday-last-hour-reversal) | Q267 金曜の最終1時間（NY 16時前）のリターンは週の向きと逆か（週末前の手仕舞い・FX8＋トレンド7 H1） | 未確定 |
| [fundagent](./fundagent) | fundagent：ニュースから売買仮説を出し、その的中率を実測するシステム | — |
| [fx-roundnumber-bounce](./fx-roundnumber-bounce) | 為替のキリ番は「跳ね返る場所」ではなく「抜けやすい場所」 | 支持 |
| [fx-shortterm-meanreversion](./fx-shortterm-meanreversion) | 為替の超短期平均回帰は2015年以降の1時間足では消えたか | 消えた（支持） |
| [fx8-h1-triple-indicator](./fx8-h1-triple-indicator) | Q291 FX8 H1 の 3 指標（TSMOM24・SMA50・RSI14 符号）が同符号のときだけ売買すると、束ねた t はコスト後に単独 TSMOM24 を上回るか（Loubaris2026-2 の H1 移植） | 棄却 |
| [gate-candidates-c1-c2-pass-probability-q428](./gate-candidates-c1-c2-pass-probability-q428) | Q428 関門の候補 C1（σ 目標 0.25%／0.35%/日・最大下落 −6%）と C2（最大下落 ≥ −0.75×年率 σ）は年率シャープ S の戦略を何割通し、1 年以内の −6%／−10% 到達率はいくらか（Q416 の S07 ブロック・ブートストラップを規程の変種に当てる・★ C の判断材料） | ★ C の実質の選択肢は C1 の σ の値。σ0.25% なら関門が S≈1.4 で半数を通す（現行は S≈2.7）… |
| [gate-pass-probability-vs-sharpe-q416](./gate-pass-probability-vs-sharpe-q416) | Q416 関門（σ0.5%/日・14 年の最大下落 −6% 以内＋前後半 t≥2）は年率シャープ S がいくら以上の戦略を何割通すか（S07 規程モード損益の 20 日ブロック・ブートストラップで S を 0〜3 に合わせて測る） | 棄却（関門が律速） |
| [gotobi-cross-jpy](./gotobi-cross-jpy) | Q179 五十日の仲値前の円安はクロス円でも出て2021年以降に消えたか（Bessho 2023） | 対立を支持: ドル固有 |
| [h4-tsmom-trend7](./h4-tsmom-trend7) | Q261 トレンド7 の H4 順張り（TSMOM 30/60/120 本）はコスト後に残るか（為替で消えた H4 の条件の穴） | 支持: trend7 全期間 純損益 t<2 または z<2（H4 には無い） |
| [halloween-effect](./halloween-effect) | Q238 「5 月に売れ」（ハロウィン効果）は 2008〜2026 の指数・商品 6 銘柄で残るか（6 か月ブロックの循環シフト帰無） | 棄却: 全期間の z < 2（手元の 18 年では見えない） |
| [har-horizon-advantage](./har-horizon-advantage) | Q275 HAR の持続基準に対する優位は予測期間（1・5・22 日）で広がるか縮むか（15銘柄・QLIKE） | 逆向きで確定: 前後半とも t≤−2（短いほど効く） |
| [har-rolling-vs-expanding](./har-rolling-vs-expanding) | Q276 HAR の係数を 2 年の rolling で推定し直すと拡大窓より QLIKE は下がるか（15銘柄） | 棄却: 差は見えない（支持にも逆向きにも届かない） |
| [har-vol-targeting](./har-vol-targeting) | Q259 HAR 予測の分散でのボラ・ターゲティングは σ60 版よりシャープが高いか（Q222×Q205 の連鎖） | 棄却: 差は見えない |
| [hysteresis-band-tsmom](./hysteresis-band-tsmom) | Q250 ヒステリシス帯（±θσ の不感帯）は順張りの合図反転を減らし純損益を上げるか（15銘柄） | 棄却: 差は見えない |
| [ic-vs-decision-loss](./ic-vs-decision-loss) | Q138 予測の当たりやすさ（IC）と決定の損失（コスト後の純損益）はどれだけ食い違うか | 未確定 |
| [indicator-confirmation](./indicator-confirmation) | Q182 複数の順張り指標が一致したときだけ売買すると的中率と純損益は上がるか（Loubaris 2026-2） | 棄却（Loubaris と同じ非有意） |
| [instrument-selection-bias](./instrument-selection-bias) | Q150 15銘柄から成績の良い 8 銘柄を事後に選ぶと順張りの成績はどれだけ膨らむか（Korzan 2026 §6 の銘柄選択バイアス） | 支持（確定）。選んだ銘柄は後半でむしろ劣る（反転）。膨らみが帰無の95%点をわずかに超えるのはその反転の裏返し（帰無は… |
| [intraday-momentum-first-last](./intraday-momentum-first-last) | Q176 最初の1時間→最後の1時間の日中モメンタムは為替・株価指数・金で公表後に残るか（GarciaArano 2026） | 最初の1時間 → 最後の1時間 の日中モメンタムは、FX8・金・US株価指数2 の H1 で公表後にコスト前・コスト後… |
| [intraday-momentum-indices-decay](./intraday-momentum-indices-decay) | Q297 US500 / USTECH H1 の日中モメンタム（初動 1 時間 → 終盤 1 時間）は 2016 以降に減衰したか | ノイズ |
| [jp-industry-reversal-q566](./jp-industry-reversal-q566) | Q566 業種内の短期反転（日本株・月次・上下 10%） | 棄却 |
| [jp-low-vol-q545](./jp-low-vol-q545) | Q545 日本株の低ボラティリティ効果（月次・市場の動きを差し引いたアルファ） | — |
| [jp-us-residual-momentum-q564](./jp-us-residual-momentum-q564) | Q564 残差モメンタム（市場 1 因子の残差・12-1 か月・残差 σ で割る・月次・上下 10%）：日本株・米国株 | 棄却 |
| [jp-us-xs-momentum-q563](./jp-us-xs-momentum-q563) | Q563 日本株・米国株の横断モメンタム（12-1 か月・月次・上下 10%・等金額 L/S） | 棄却 |
| [jp-weekly-reversal-q544](./jp-weekly-reversal-q544) | Q544 日本株の週次の短期反転（J-Quants・日本株の検証の 1 本目） | — |
| [jump-day-followthrough](./jump-day-followthrough) | Q273 ジャンプ日（／ret／>2.5σ）の翌日・翌5日は継続か反転か（15銘柄・年内並べ替え帰無） | 未確定・ただし 2017 を境に y1 が「継続→反転」へ、y5 が「中立→継続」へ振れている可能性 |
| [kensho-anomaly-decay](./kensho-anomaly-decay) | 決算発表後のアノマリー減衰 | README の「主な検証」表を参照 |
| [leaderboard-width-tsmom-q326](./leaderboard-width-tsmom-q326) | Q326 順張りの参照日数60本の順位表 L(j) は上位ほど悪いか・格子を広げるほど選択の翌年は悪くなるか（Wang 2026 BT-2 を手元へ・Q325-C1） | ノイズ（幅は選択を良くも悪くもしない、と区別できない） |
| [leadlag-surface-q549](./leadlag-surface-q549) | Q549 「他市場の先行（リードラグ）」は面で尽きているか | — |
| [ledger-fdr-q338](./ledger-fdr-q338) | Q338 手元の検証の全体に偽発見率の補正を当てると「効果あり」のうち何本残るか（Chang ら 2026 を自分の台帳へ・Q336-C3） | 確定 |
| [long-short-decomposition](./long-short-decomposition) | Q152 順張りの利益は買い側だけか: 売り側はコスト後に0と区別できるか | 未確定（売り側に利益なしは確定。買い側の順張りは機械判定では支持だが、BTC・後半・ドンチャンに依存） |
| [lookback-ensemble-tsmom](./lookback-ensemble-tsmom) | Q223 参照日数の集合（20・60・120・250 の合図平均）は最良単一の参照日数より標本外で良いか（Baltas・Kosowski の型） | ノイズ: 合図平均と最良単一の差は前後半で揃わず事前固定の t≥2 または t≤−2 のどちらも通らない |
| [ltr-lambdamart-vs-jt-wide48-monthly-q448](./ltr-lambdamart-vs-jt-wide48-monthly-q448) | Q448 ランキング学習（LambdaMART）対 過去リターン並べ（JT）：wide48 月次・上下10・コスト後 | 棄却 |
| [m15-autocorr-by-hour](./m15-autocorr-by-hour) | Q153 15分足の1次自己相関は時刻で符号が変わるか（USDJPY・EURUSD 2021〜・Holm 補正） | 確定（棄却） |
| [ma-cross-eurusd](./ma-cross-eurusd) | MAクロス 全パターン検証（EURUSD 4時間足） | — |
| [ma200-timing-vs-exposure](./ma200-timing-vs-exposure) | 200日移動平均線ルールの下落防御は、タイミングの効果か市場露出が減るだけか（約100年・米株） | README の「主な検証」表を参照 |
| [ml-core-eurusd-h1](./ml-core-eurusd-h1) | Q191 ML 自動売買の「核」（Model 0）は EURUSD の1時間足からコスト後に 0 と区別できる信号を取り出せるか | 棄却（段階1: 粗利でも t<2・コスト以前に信号なし） |
| [month-end-fix-dollar](./month-end-fix-dollar) | Q229 月末のロンドン16時フィキシング前のドルの向きは、その月の US500 リターンと逆か（Melvin・Prins 2015 の型） | 棄却: 全期間の z > −2 |
| [month-of-year-15](./month-of-year-15) | Q265 15銘柄の月別季節性（month-of-year）は Holm 後に前後半で同符号で残るか | 効果なし（支持＝月別の季節性は残らない） |
| [nfp-m15-followthrough](./nfp-m15-followthrough) | Q219 米雇用統計（NFP）の直後 15 分の向きは次の 1〜4 時間に続くか反転するか（EURUSD・USDJPY M15・2021 年以降） | 棄却: 継続とも反転とも区別できない |
| [nr7-breakout-continuation](./nr7-breakout-continuation) | Q217 NR7（直前 7 日で最小レンジ）の翌日は最初の 2 時間の向きに続くか（FX8＋金・H1 から日足） | 棄却 |
| [null-center-bias-runner-results-q417](./null-center-bias-runner-results-q417) | Q417 Runner 型の既存結果 JSON を横断し、循環シフト帰無の中心（q025 と q975 の中点）が 0 から 0.5σ 以上ずれる割合と、そのずれが z と年単位 t の食い違いを説明するか | 支持（仕組みの変更が要る） |
| [null-model-choice](./null-model-choice) | Q178 帰無モデルの選び方（並べ替え・AR(1)・GARCH型）で移動平均ルールの判定は変わるか（Brock 1992） | 確定（H1 支持: 帰無の選び方で判定はほぼ割れない） |
| [null-zoo-size-q320](./null-zoo-size-q320) | Q320 手元の標準の判定は、15 銘柄の順張り損益の実際の ϕ1・歪度に合わせた腕なしの合成探索で名目 5% を守るか（Canli 2026 Null Zoo の移植・Q319-C1） | 歪みは確定。ただし原因は ϕ1・歪度（Null Zoo の筋）ではなく、銘柄間の相関を、銘柄ごとに別々の並べ替えで壊す… |
| [one-month-reversal](./one-month-reversal) | Q215 1 か月の短期反転（直前 21 日の逆）は 15 銘柄の日足でコスト後に残るか（Jegadeesh 1990 の型・12-1 モメンタムと対比） | 棄却（粗利でも負・事前固定 z≥2 を通らず） |
| [oshime-d1-yahoo-close-recheck](./oshime-d1-yahoo-close-recheck) | Q158 押し目・逆張りの D1 系14本を Dukascopy 日足に差し替えて再確認（2026-10-09 Opus） | — |
| [overnight-intraday-reversal-fx](./overnight-intraday-reversal-fx) | Q173 為替の夜間→日中の逆張りは2015年以降の主要8通貨でコスト後に残るか（DellaCorte 2015） | 棄却 |
| [overnight-intraday-reversal-indices](./overnight-intraday-reversal-indices) | Q270 株価指数・金の夜間→日中の逆張りはコスト後に残るか（DellaCorte 2015 の指数・金への移植・H1） | 棄却: 全期間の粗利の z<2（信号がない） |
| [overnight-premium-indices](./overnight-premium-indices) | Q209 株価指数・金の夜間（現物取引時間外）リターンは日中より高いか（夜間プレミアム・H1・2017 年以降） | 棄却。夜間が日中より稼ぐように見える差は「夜間が 18 時間・日中が 6 時間」という長さの差で説明でき、14〜20 … |
| [pair-trading](./pair-trading) | ペアトレード（IEF/TLT, NVDA/AMD） | README の「主な検証」表を参照 |
| [parameter-plateau-selection](./parameter-plateau-selection) | Q188 周辺パラメータの平均で選ぶ（台地選択）と最良1点で選ぶより標本外が良いか（ブログZenn2026e-2） | H0: 選び方では変わらない |
| [parkinson-vol-forecast](./parkinson-vol-forecast) | Q222 Parkinson のレンジボラは終値ボラより翌日の実現ボラをよく予測するか（15 銘柄・QLIKE・HAR 型） | 支持: Parkinson のレンジは終値より翌日の実現ボラをよく予測する |
| [parkinson-vol-targeting](./parkinson-vol-targeting) | Q232 Parkinson レンジボラでのボラ・ターゲティングは終値 σ60 版よりシャープが高いか（Q222 × Q205 の連鎖） | 棄却 |
| [path-smoothness-tsmom-q346](./path-smoothness-tsmom-q346) | Q346 直前の経路が滑らか（R² 高・FIP 連続的）なほど翌月の時系列モメンタム純損益は大きいか（15 銘柄・Clenow／Da ほか 2014 の移植） | 棄却で機械判定と同じ |
| [pbo-cscv-tsmom](./pbo-cscv-tsmom) | Q171 順張りの参照日数 60 通りの CSCV で測った過剰適合の確率 PBO は約 0.88（Bailey 2017） | 支持（過剰適合） |
| [pbo-tsmom-grid](./pbo-tsmom-grid) | Q171 順張りの参照日数60通りの CSCV で過剰適合の確率 PBO はいくつか（Bailey 2017） | —（未実行） |
| [permutation-null-stability](./permutation-null-stability) | Q146 並べ替え帰無の z は何回で安定するか（B と seed のぶれ。検証基盤の既定 B を決めるため） | — |
| [pooled-har-vs-individual](./pooled-har-vs-individual) | Q274 15銘柄をプールしたパネル HAR は銘柄別 HAR より翌日の QLIKE を下げるか | 棄却: 差は見えない（支持にも逆向きにも届かない） |
| [post-fix-conditional-sell](./post-fix-conditional-sell) | Q190 仲値後のドル円の売りは仲値前に上がった五十日だけ効くか（Bessho 2023-2・2008〜2026） | 棄却 |
| [pre-fomc-drift](./pre-fomc-drift) | Q243 FOMC 前日ドリフトは US500 H1 で 2015 年以降も残るか（Lucca・Moench 2015／Kurov ほか 2021 の追試） | ノイズ（規則どおり）、ただし Kurov 2021 の「2015 以降は消えた」の文脈とは一致しない形 |
| [pre-holiday-effect](./pre-holiday-effect) | Q239 休日前効果は SPX・NDX（2008〜2026）で残るか（祝日は欠損営業日から復元・Lakonishok・Smidt 1988 の型） | 棄却 |
| [predictability-to-profit-conversion](./predictability-to-profit-conversion) | Q149 分散比で「予測できる」と出た組は、次の期間にコスト後で儲かるか（Alahmadi 2026 §3.4.1 の変換率） | 前後半とも (b) の t<2 で事前の規則どおり「変換されない」。点推定も前後半とも負で、予測できる組は予測できない… |
| [profit-target-tsmom](./profit-target-tsmom) | Q252 利食い目標（k·ATR）は順張りの純損益を上げるか下げるか（15銘柄・Q204 の損切りの対） | Q204 と同じ「保険」型 |
| [q160-endpoint-sensitivity](./q160-endpoint-sensitivity) | Q354 Q160 の確定は評価期間の端点を ±1 年ずらした 9 通りで何通り保たれるか（方法論・確定判定の端点感度） | 確定（Q160 の確定は端点依存。商品4 の買い側の上乗せは 9/9 で頑健だが、BTC 除外トレンド6 は最新の半年… |
| [random-vs-chrono-split](./random-vs-chrono-split) | Q189 ランダム分割の交差検証は時系列分割より順張り選択の楽観をどれだけ膨らませるか（Roelofs 2019-2） | 符号は仮説と逆（ランダム分割の方が時系列分割より楽観が小さい）だが、有意ではない |
| [ratio-pairs-mean-reversion](./ratio-pairs-mean-reversion) | Q233 金銀比・Brent−WTI の z スコア逆張り（ペアトレード）は 2015 年以降コスト後に残るか | 棄却: どの組も残らない |
| [realized-skew-next-month](./realized-skew-next-month) | Q231 H1 から作る月次の実現歪度は翌月リターンを負に予測するか（Amaya ほか 2015 の型・15 銘柄） | 棄却 |
| [rebalance-frequency](./rebalance-frequency) | リバランス頻度とリスク尺度のどちらが成績差を支配するか（米国セクター ETF） | README の「主な検証」表を参照 |
| [report-scoring](./report-scoring) | 検証ログの採点基準の事後検証 | README の「主な検証」表を参照 |
| [reselection-frequency](./reselection-frequency) | Q177 順張りの参照日数を選び直す頻度（月・四半期・半年・年）で標本外成績は変わるか（Zarrabi 2017） | ノイズ |
| [residual-momentum-fx](./residual-momentum-fx) | Q255 ドル因子を除いた残差の順張りは生の順張りより強いか（FX6・Blitz 2011 の残差モメンタムの移植） | 棄却: 差は見えない |
| [riskoff-gate-window-surface-q542](./riskoff-gate-window-surface-q542) | Q542 リスクオフ・ゲートの失敗の確認（窓の面） | — |
| [rsi-rules-fx](./rsi-rules-fx) | Q180 RSI の族は先進国通貨の日足で2016年以降も補正後に残るか（Coakley 2016-2） | 棄却（確定） |
| [rsi2-dip-highvol-indices](./rsi2-dip-highvol-indices) | Q271 US500・USTECH の RSI2 押し目買いは高ボラのときだけコスト後に残るか（QuanterLab 2026-3 の追試・CFD 日足） | 棄却: 2 指数とも全期間 z<1 |
| [s02-tsmom60-sma200-timestop-wide48-q382](./s02-tsmom60-sma200-timestop-wide48-q382) | Q382 48 銘柄 D1 の TSMOM60 × SMA200 同符号ゲート × 時間ストップ 20 日の合成（部品は既存値で固定・掃引なし）は規程モードの封印前の前後半で t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s04-target-horizon-q383](./s04-target-horizon-q383) | Q383 翌 k 日（k∈{1,5,20}）リターンのリッジ予測は地平線で IC・コスト後損益が変わるか（embargo=k・3 試行・S04a/c の k=5 の妥当性） | — |
| [s04-train-window-length-q381](./s04-train-window-length-q381) | Q381 学習窓（4／6／10 年の固定長と拡張）で 48 銘柄プールのリッジ方向予測の年次 IC とコスト後損益は変わるか（6 試行・事前固定 4 年固定長の妥当性） | 支持（窓の長さは共通年の IC・コスト後損益に効かない。事前固定の 4 年固定長で可）。ただし 6 本とも損益は負で、… |
| [s04a-meta-label-predictability-q375](./s04a-meta-label-predictability-q375) | Q375 48 銘柄 D1 の TSMOM60 メタラベル（k∈{5,10,20}）は族の切除（mom／vol／range／dow／全部）のリッジで AUC・IC がラベル並べ替え帰無より高いか（メタラベルはそもそも当てられるか） | 支持 |
| [s04a-meta-label-tsmom60-wide48](./s04a-meta-label-tsmom60-wide48) | Q374 48 銘柄 D1 の TSMOM60 合図にメタラベリング（k=5・族 mom/vol/range/dow・リッジ→GBM・予測→規模 3 通り・格子 27）を重ねると、規程モードの封印前の前後半で S07 本体とゼロをコスト後に上回り年単位 t≥2 か | 棄却 |
| [s04b-asymmetric-vol-sizing-q377](./s04b-asymmetric-vol-sizing-q377) | Q377 予測ボラを上振れだけ使う非対称サイジング（σ_used=max(σ̂_HAR, σ60)）は対称版・σ60 版より S07 TSMOM60 の規程モードで最大下落が浅く、シャープを落とさないか | — |
| [s04b-vol-forecast-calibrated-q387](./s04b-vol-forecast-calibrated-q387) | Q387 48 銘柄 D1 の翌 5 日実現分散の予測を水準で学習する HAR-RV（銘柄別・Corsi 原型）・プール水準 HAR・EWMA λ0.94・log-HAR スミアリング補正は、較正（実現/予測の平均 0.8〜1.25）を満たした上で QLIKE で σ60 に勝つか（Q376 の中央値偏りの再設計） | 2015 年 1 年への依存が強く、残り 12 年では σ60 と差がない。平均 QLIKE の半減は 2015 の外… |
| [s04b-vol-forecast-sizing-q376](./s04b-vol-forecast-sizing-q376) | Q376 48 銘柄 D1 の翌 5 日実現ボラ予測（σ20・σ60・HAR・リッジ全特徴・GBM 全特徴）は QLIKE で σ60 に勝ち、σ̂ を size_weights に渡すと S07 TSMOM60 の規程モードで最大下落が浅くシャープが上がるか | 棄却 |
| [s04b-vol-sizing-calibrated-q388](./s04b-vol-sizing-calibrated-q388) | Q388 水準 HAR-RV（銘柄別 OLS）の σ̂ を size_weights の σ に渡した S07 TSMOM60 の規程モードは、σ60 版より最大下落が浅く Sharpe が高いか（較正を前提条件とし σ̂ 並べ替え帰無で判定。Q376 の偏りを除いた再判定・Q377 の前提） | 棄却 |
| [s04c-pooled-direction-wide48-q378](./s04c-pooled-direction-wide48-q378) | Q378 48 銘柄プールの翌 5 日リターン予測（リッジ→GBM・特徴量 3 組・変換 3 通り・格子 36・PBO）は規程モードの封印前の前後半で S07 本体とゼロをコスト後に上回り年単位 t≥2 か | ノイズ |
| [s04c-pooled-vs-persym-q379](./s04c-pooled-vs-persym-q379) | Q379 翌 5 日リターン予測で 48 銘柄プール学習は銘柄別学習より IC・コスト後損益が高いか（リッジ・GBM × プール／銘柄別の 4 試行） | 未確定 |
| [s04c-regression-vs-classification-q380](./s04c-regression-vs-classification-q380) | Q380 翌 5 日リターン予測で回帰目的（ret）と符号分類目的（sign）はどちらが IC・コスト後損益が高いか（リッジ回帰・GBM 回帰・GBM 分類・リッジ符号回帰の 4 試行） | 未確定（差は無い） |
| [s08-crypto11-d1-tsmom-q386](./s08-crypto11-d1-tsmom-q386) | Q386 暗号資産 11 通貨の D1（H1→D1・UTC 0 時区切り・週末込み）TSMOM L∈{60,120} は規程モード（暗号版）で封印前の前半（〜2020）・後半（2021〜2024-06）とも年単位 t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s08-crypto2-d1-tsmom-q385](./s08-crypto2-d1-tsmom-q385) | Q385 BTC＋ETH の D1（H1→D1・UTC 0 時区切り・週末込み）TSMOM L∈{60,120} は規程モード（暗号版）で封印前の前半（〜2020）・後半（2021〜2024-06）とも年単位 t≥2 かつ最大下落 −6% 以内か | 未確定 |
| [s09-fx22-carry-cross-sectional-q392](./s09-fx22-carry-cross-sectional-q392) | Q392 FX22 D1 の横断キャリー（政策金利差で 22 ペアを順位付け・上位 1/3 買い・下位 1/3 売り・スワップ込み）は時系列版（符号）より規程モードの封印前の前後半 t≥2 かつ最大下落 −6% 以内を通りやすいか | 未確定 |
| [s09-fx22-carry-sign-q389](./s09-fx22-carry-sign-q389) | Q389 FX22 D1 のキャリー単独（政策金利差の符号で高金利通貨を買う・スワップ＝金利差 − 年 0.75% マークアップを損益に含む）は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 未確定 |
| [s09-fx22-carry-tsmom-composite-q391](./s09-fx22-carry-tsmom-composite-q391) | Q391 FX22 D1 でキャリー符号と TSMOM60 符号が一致したときだけ持つ合成（副: スワップ込み総収益指数の TSMOM60）は、キャリー単独・TSMOM 単独より規程モードの封印前の前後半 t≥2 かつ最大下落 −6% 以内を通りやすいか | 未確定 |
| [s09-fx22-tsmom60-with-swap-q390](./s09-fx22-tsmom60-with-swap-q390) | Q390 FX22 D1 の TSMOM60 にスワップ（政策金利差 − 年 0.75% マークアップ）を損益に含めると、S07 のスワップなし（棄却）より規程モードの封印前の前後半 t・最大下落が改善し関門を通るか | 棄却 |
| [s10-equity-trend-safe-haven-fx-q395](./s10-equity-trend-safe-haven-fx-q395) | Q395 US500 の TSMOM60 符号が負の日は円・フランを買い（USDJPY/USDCHF/AUDJPY/NZDJPY/CADJPY 売り）正の日は逆、のリスクオフ・レジーム戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 未確定 |
| [s10-xasset-bond-equity-tsmom-q394](./s10-xasset-bond-equity-tsmom-q394) | Q394 株価指数 13＋債券 3 の D1 で、債券の 250 日リターン符号で株を持ち・株の 250 日リターンの逆符号で債券を持つクロスアセット TSMOM は規程モードで封印前の前後半（境 2021）とも年単位 t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s11-spread-predicts-relative-vol-q397](./s11-spread-predicts-relative-vol-q397) | Q397 48 銘柄 D1 で実測スプレッドの 5 日平均 z は翌 5 日の実現ボラ／σ60 の比を予測するか（σ60 に無い情報・年単位 IC の t） | 未確定 |
| [s11-spread-stress-gate-tsmom-q396](./s11-spread-stress-gate-tsmom-q396) | Q396 48 銘柄 D1 の TSMOM60 に実測スプレッドの z（250 日）>2 の日は休む流動性ゲートを足すと、ゲートなし（S07 本体と同じ合図）より規程モードの最大下落が浅く前後半の t が高いか | 棄却 |
| [s12-fx22-rate-momentum-sign-q398](./s12-fx22-rate-momentum-sign-q398) | Q398 FX22 D1 で政策金利差（base − quote）の 90 暦日変化の符号で持つ（金利モメンタム・スワップ込み）戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s12-fx22-rate-momentum-xsec-q399](./s12-fx22-rate-momentum-xsec-q399) | Q399 FX22 D1 を政策金利差の 90 暦日変化で順位付けし上位 1/3 買い・下位 1/3 売り（横断金利モメンタム・スワップ込み）は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s13-gap-excluded-rerun-q409](./s13-gap-excluded-rerun-q409) | Q409 S13 見直し: Q400（月替わり）・Q402（FOMC 偶数週）を穴跨ぎ足を除いて再計算 | 棄却 |
| [s13-idx13-fomc-cycle-even-weeks-q402](./s13-idx13-fomc-cycle-even-weeks-q402) | Q402 株価指数 13 の FOMC サイクル偶数週（定例発表日を 0 として −1〜+3・+9〜+13・+19〜+23・+29〜+33 営業日）だけ買い持ちする戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s13-idx13-pre-fomc-drift-q401](./s13-idx13-pre-fomc-drift-q401) | Q401 株価指数 13 の FOMC 前ドリフト（定例発表日の前日の足と当日の足の 2 本を買い持ち・年 8 回）は 2015 年以後も残り、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 未確定 |
| [s13-idx13-turn-of-month-q400](./s13-idx13-turn-of-month-q400) | Q400 株価指数 13 の D1 月替わり効果（各銘柄の足で数えた月の最終営業日と翌月の最初の 3 営業日の 4 本だけ買い持ち）は 2010 年以後も残り、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 棄却 |
| [s13-usd7-fomc-day-dollar-sell-q403](./s13-usd7-fomc-day-dollar-sell-q403) | Q403 対ドル 7 ペア（EURUSD・GBPUSD・AUDUSD・NZDUSD・USDJPY・USDCHF・USDCAD）で FOMC 定例発表日にドルを売る（当日の足 1 本・年 8 回）戦略は規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か | 2010〜2016 の標本外では Mueller ほか 2017 の発表日ドル安は出ず、2017 以後（とくに 202… |
| [s14-tick-volume-information-q413](./s14-tick-volume-information-q413) | Q413 15 銘柄の日次 tick 出来高 z は高値安値レンジ z と冗長か（Spearman）、σ20 とレンジを条件づけても翌 5 日の ／ret／ を予測するか（出来高に OHLC 以外の情報があるか） | — |
| [s14-volume-gate-tsmom60-all15-q411](./s14-volume-gate-tsmom60-all15-q411) | Q411 15 銘柄 H1→D1 の TSMOM60 を tick 出来高の増加（V20/V250 ≥ 1）の日だけ持つゲートは、ゲートなしより規程モードの前後半 t と最大下落を改善するか | 棄却 |
| [s14-volume-weighted-tsmom60-all15-q412](./s14-volume-weighted-tsmom60-all15-q412) | Q412 15 銘柄 H1→D1 の出来高加重 TSMOM60（直近 60 日の Σ ret_i × v_i/v̄_250 の符号）は素の TSMOM60 より規程モードの前後半 t≥2・最大下落 −6% 以内に近づくか | 未確定 |
| [s15-fomc-dollar-sell-hiking-regime-q414](./s15-fomc-dollar-sell-hiking-regime-q414) | Q414 対ドル 7 ペア（EURUSD・GBPUSD・AUDUSD・NZDUSD・USDJPY・USDCHF・USDCAD）の FOMC 定例発表日ドル売り（当日の足 1 本）を「米政策金利が直近 365 暦日に 1 回以上上がった」局面だけに限ると、Q403 で見えた後半（2022〜24）とは独立な第 1 サイクル（2015-12〜2019-07）でも規程モードの年単位 t≥2 か（前後半の境は 2020） | 未確定 |
| [s15-wide48-tsmom60-global-hiking-q415](./s15-wide48-tsmom60-global-hiking-q415) | Q415 48 銘柄 D1 の TSMOM60 を「8 中銀（USD EUR JPY GBP AUD CAD CHF NZD）のうち直近 180 暦日に利上げした数が 4 以上」の局面だけ持つと、常時持つ S07 本体より規程モードの前後半 t と最大下落が改善するか | 棄却 |
| [s16-three-family-equal-risk-composite-q425](./s16-three-family-equal-risk-composite-q425) | Q425 弱い正の 3 族（キャリー符号 FX22・BTC/ETH TSMOM60・FX22 TSMOM60）を事前固定の等リスク 1/3 合成にした 1 本は、規程モードで封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か（S16 本体・合成 1 本のみ・掃引しない） | 未確定 |
| [s17-long-only-risk-premia-idx-bond-gold-q468](./s17-long-only-risk-premia-idx-bond-gold-q468) | Q468 S17 多資産ロングオンリー（株価指数 10＋債券 2＋金）の等リスク買い持ちは、保有コスト年 4% 込みで C1 関門（規程モード σ0.25%/日・封印前の前後半 t≥2・max_dd −6% 以内）を通るか | 株価指数＋債券＋金の買い持ちプレミアムは等金額ならコスト後も正（1.5 bp/日・年率 約 3.8%・Sharpe 0… |
| [s17b-long-only-index-holdout-q543](./s17b-long-only-index-holdout-q543) | Q543 S17b: 指数・債券・金の買い持ち（等金額・建玉一定）：ホールドアウトで 1 回だけ確認 | — |
| [s18-four-family-equal-risk-composite-c1-q469](./s18-four-family-equal-risk-composite-c1-q469) | Q469 S18 低相関 4 族（キャリー符号 FX22・BTC/ETH TSMOM60・FX22 TSMOM60・株価指数 10 の買い持ち β）の事前固定 1/4 等リスク合成は、規程モード C1（σ0.25%/日）で封印前の前後半とも年単位 t≥2 かつ最大下落 −6% 以内か（合成 1 本のみ） | 初めて max_dd の関門（−6%）を通り、等金額の z も 2 を超えたが、年単位 t が前半 0.97・後半 1… |
| [s19-vix-riskoff-gate-index-beta-c1-q473](./s19-vix-riskoff-gate-index-beta-c1-q473) | Q473 S19 VIX リスクオフ・ゲート: 株価指数 10 の買い持ち β を VIX（t−1）が直近 250 観測の 80 分位以下の日だけ持つと、常時買い持ち（Q468 params 1）より規程 C1 で t_all・max_dd が良くなり、C1 関門（前後半 t≥2・max_dd −6%）を通るか | VIX の水準ゲートは株価指数の買い持ちを改善しない。むしろ高 VIX 日を外すことで平均リターンの高い日を捨て、t … |
| [s20-credit-riskoff-gate-composite-c1-q513](./s20-credit-riskoff-gate-composite-c1-q513) | Q513 S20 信用スプレッド（HY OAS）のリスクオフ・ゲート付き 4 族合成（C1） | 実行不能（データ源）・判定なし |
| [s20b-baa10y-riskoff-gate-composite-c1-q514](./s20b-baa10y-riskoff-gate-composite-c1-q514) | Q514 S20 再登録: 信用スプレッド（BAA10Y）のリスクオフ・ゲート付き 4 族合成（C1） | 棄却 |
| [s21-h1-ml-rr-weekcap-q515](./s21-h1-ml-rr-weekcap-q515) | Q515 S21：H1・15銘柄・ML が「入るか・方向・RR」を選ぶ bot（RR 1.0〜2.0・週10回/銘柄） | 未確定（仮判断不合格・最終 1 年は未開封） |
| [s22-crypto-ml-fintokei-q528](./s22-crypto-ml-fintokei-q528) | （README なし） | — |
| [s23-crypto-uptrend-long-q529](./s23-crypto-uptrend-long-q529) | （README なし） | — |
| [s24-multiasset-value-reversal-q536](./s24-multiasset-value-reversal-q536) | Q536 S24: 多資産の長期反転（バリューの代理） | 棄却 |
| [s25-t10y2y-steepening-gate-composite-c1-q535](./s25-t10y2y-steepening-gate-composite-c1-q535) | Q535 S25: 米国債 2s10s（T10Y2Y）のスティープ化ゲート付き 4 族合成（C1） | 棄却 |
| [s26-crypto-funding-gate-q551](./s26-crypto-funding-gate-q551) | Q551 S26：資金調達率で「買いが混みすぎた日」の S23 を休む | — |
| [s27-realyield-gold-q552](./s27-realyield-gold-q552) | Q552 S27：米国の実質金利の変化で金（XAUUSD）の向きを決める | — |
| [s28-onchain-liquidation-observe-q557](./s28-onchain-liquidation-observe-q557) | Q557 S28：マイナーチェーンの旧版レンディングに、清算できるのに放置された貸付けはあるか（読み取りのみの観測） | 棄却（S28 の「静的に放置された貸付けを拾う」形は閉じる。RealT の件だけ、許可型の担保の清算の決まりを文書で確… |
| [safe-haven-beta-stability](./safe-haven-beta-stability) | Q277 リスクオフ日（US500 下位 5%）の金・円・フラン・豪ドルのベータは前後半で安定か（安全資産の役割） | 棄却: 符号が逆または Holm 後 ／z／≥2 の銘柄あり（USDJPY: pre=0.6641 post=0.09… |
| [same-day-label-leak](./same-day-label-leak) | Q307 同じ特徴量の分類器で、ラベルを同日にすると上げ下げの精度は跳ね、翌日では基準率に落ちるか（HSAT の精度 0.69 はリークで再現できるか・Q306-C1） | 翌日の予測力なし（確定）・論文の0.69の由来は未確定 |
| [santa-rally](./santa-rally) | Q266 年末年始効果（12月最終5営業日＋1月最初2営業日）は SPX・NDX（2008〜2026）で残るか（年内ブロック並べ替え） | 棄却: 全期間 z<1（SPX・NDX とも） |
| [seasonality](./seasonality) | 季節性（暖房株・気温相関など） | README の「主な検証」表を参照 |
| [selection-optimism-vs-J](./selection-optimism-vs-J) | Q139 候補数 J を増やすと選択の楽観はどれだけ増え、Alonso の下側限界はそれを覆うか | 単調性「支持」・限界「使える」 |
| [selection-window-length](./selection-window-length) | Q244 参照日数の選択窓の長さ（1・2・3・5・8 年）で、順張りの標本外純損益は変わるか（15 銘柄） | 棄却: 窓の長さでは変わらない（Q177・Q188 と同じ） |
| [signal-confirmation-filter](./signal-confirmation-filter) | Q221 合図の確認フィルタ（k 日連続同符号で入る）は 15 銘柄の順張りのホイップソーを減らし純損益を上げるか | 未確定 |
| [signal-direction-compression](./signal-direction-compression) | Q145 戦略の日次ポジションを平均の向きに圧縮したとき、向きが離れたペアは履歴の相関も低いか（Nunes 2026 を 12 戦略 × 15銘柄で） | 向きの選別は履歴の違いを保証しないが、基準率より改善する（Nunes と同じ） |
| [signal-strength-terciles](./signal-strength-terciles) | Q249 順張りの合図強度（／ret_L／/σ）の3分位で翌日の純損益は単調に増えるか（15銘柄・sign と強度の対比） | 棄却 |
| [sma-cross-grid-spec-pass-q567](./sma-cross-grid-spec-pass-q567) | Q567 2 本 SMA クロスの総当たり（190 組×15 銘柄×D1/H4）: スペック §1 の再現合格数は偶然の範囲か・前半 TOP5 の等ウェイトは後半で勝つか | 確定（(C) で「前半 TOP5 の bot は後半で等ウェイトに勝たない」。(A) は帰無が 0 点に潰れた退化で、… |
| [split-year-sensitivity](./split-year-sensitivity) | Q278 前後半の分割年を 2014〜2020 で動かすと「前後半とも同符号 t≥2」の判定は何割割れるか（基盤・簡単な規則群） | 未確定寄りのトリビアル支持 |
| [spread-change-vol-forecast](./spread-change-vol-forecast) | Q234 XAUUSD の実測スプレッドの変化は、HAR に足すと翌時間の実現ボラの QLIKE を下げるか | 棄却: 前後半のどちらかで t > −2 または z > −2 |
| [streak-reversal](./streak-reversal) | Q240 k 日連続同符号（k=3・5）の翌日は反転するか（15 銘柄・年内並べ替え帰無） | 棄却 |
| [survivors-correlation-composite](./survivors-correlation-composite) | 生き残り 3 本（S17b・S21 候補形・S23）の相関と合成（記述・2026-10-29） | — |
| [time-stop-tsmom](./time-stop-tsmom) | Q251 時間ストップ（N 日で強制手仕舞い・再合図まで待つ）は順張りの純損益と最大下落を改善するか（15銘柄） | 支持: 時間ストップは最大下落を浅くするが純損益は上げない（Q204 と同じ型） |
| [trade-profit-concentration](./trade-profit-concentration) | Q314 順張りの利益は少数の取引に集中するか: 最良 1 取引の総利益比を、同じ取引数・保有期間で入る時期だけランダムにした帰無と比べる（Q313-C1・ブログの 91% は普通か異常か） | 未確定 |
| [trend-age-pnl](./trend-age-pnl) | Q253 トレンドの年齢（合図反転からの経過日数）が短いほど翌日の順張り損益は高いか（15銘柄） | 未確定 |
| [trend-persistence-vs-tf-pnl](./trend-persistence-vs-tf-pnl) | Q136 トレンドの持続時間が長い期間ほど、順張りはコスト後に儲かるか | H1・H2 とも棄却 |
| [trend-pnl-half-life](./trend-pnl-half-life) | Q143 順張りの純損益の減衰は指数か、それとも最初から0か（Feng 2026 の半減期を FX8・トレンド7 で） | 主 TSMOM20: FX8 は「未確定（Q063 と同じ）」／トレンド7 は「一定（減衰ではない）」（副 ドンチャン… |
| [trend7-d1-long-vs-short-q361](./trend7-d1-long-vs-short-q361) | Q361 TREND7 D1 TSMOM(L=60) を long-only と short-only に分けると、どちらが bp>0 を担うか（long-only で足りるか） | 未確定 |
| [trend7-d1-moskowitz-skip1m-q358](./trend7-d1-moskowitz-skip1m-q358) | Q358 Moskowitz 原著の 12m-1m（L=252、skip=21）TSMOM は、TREND7 D1 で封印前の前後半とも年単位 t≥2 で正か | 未確定 |
| [trend7-d1-sma200-vs-tsmom60-q364](./trend7-d1-sma200-vs-tsmom60-q364) | Q364 TREND7 D1 で TSMOM(L=60) と SMA200 の上下による順張りは、封印前の前後半で年単位 t≥2 を取る合図形式がどちらか | TSMOM(L=60) が前後半とも年単位 t<1（pre t=0.61, post t=0.66）。SMA200 は… |
| [trend7-d1-tsmom-breakeven-q362](./trend7-d1-tsmom-breakeven-q362) | Q362 TREND7 D1 TSMOM(L=60) は段階1コストの何倍までコスト後に正か（本番で許されるコストの余裕） | 支持（余裕大）: 3× 段階1コストでも全期間 bp_net>0（+1.39 bp）。ただし全期間 p_perm=0.… |
| [trend7-d1-tsmom-core-q355](./trend7-d1-tsmom-core-q355) | Q355 TREND7 の D1 TSMOM 本体（L=60）は、封印前の前後半とも年単位 t≥2 で純損益がコスト後に正か（S01 の中央関門） | 未確定: pre t=0.61、post t=1.12 — 両方 t<2 のため S01 ゲート未通過 |
| [trend7-d1-tsmom-ensemble-q363](./trend7-d1-tsmom-ensemble-q363) | Q363 TREND7 D1 で TSMOM 符号の等重みアンサンブル（L=20/60/120/250 の平均）は、単発 L=60 と比べて封印前の前後半で年単位 t≥2 を取りやすいか | 未確定 |
| [trend7-d1-tsmom-lookback-sensitivity-q356](./trend7-d1-tsmom-lookback-sensitivity-q356) | Q356 TREND7 D1 TSMOM の L ∈ {20,60,120,250} の掃引で、main（L=60）は Holm m=4 補正後も封印前の前後半で t≥2 を保つか（S01 の lookback 頑健性） | 未確定 |
| [trend7-d1-weekly-rebalance-q360](./trend7-d1-weekly-rebalance-q360) | Q360 TREND7 D1 TSMOM(L=60) を週次（月曜のみ）でリバランスしても、封印前の前後半で年単位 t≥2 を保つか（コスト低減の効果） | 未確定 |
| [trend7-h4-tsmom-wide-l-q359](./trend7-h4-tsmom-wide-l-q359) | Q359 TREND7 の H4 TSMOM で L を広げる（120/240/480 本 ≒ 20/40/80 日）と、Q261 の L=60（≒10 日）不支持は改善するか | 棄却: 広い L でも全期間 t<1 かつ前後半ともに t<2（H4 自体の問題。lookback 不足ではない） |
| [trend7-subgroup-carrier-q357](./trend7-subgroup-carrier-q357) | Q357 TREND7 D1 TSMOM(L=60) の収益は商品 4（XAU/XAG/WTI/UKOIL）と株＋BTC 3（US500/USTECH/BTC）のどちらが担うか | 棄却 |
| [tsmom-pnl-concentration](./tsmom-pnl-concentration) | Q230 順張りの純損益は上位 1% の日に集中しているか: 最大の k 日を除くと年単位の t が 2 を切るか（15 銘柄 D1） | 未確定: all15 の t_full が 2 未満の期間があり集中を問えない |
| [tsmom-smile-quadratic](./tsmom-smile-quadratic) | Q257 順張り束の月次損益は US500 月次リターンの 2 次関数（スマイル）か（Fung・Hsieh 2001／Moskowitz 2012 の型） | 棄却: 全期間 z<1 |
| [tsmom12m-ma200-cash-rule](./tsmom12m-ma200-cash-rule) | Q151 12か月リターン>0 かつ 200日線上で保有・外れたら現金の規則は、循環シフトの帰無より下落が浅いか（Korzan の規則を15銘柄で） | 確定 |
| [turn-of-month-shift](./turn-of-month-shift) | Q181 月替わり効果の窓は2017年以降に前倒しされたか（QuanterLab 2026・US500/USTECH/SPX） | 棄却: 古典窓と前倒し窓の差は見えない |
| [turn-of-month-shift-fx8-q284](./turn-of-month-shift-fx8-q284) | Q284 月末前4日の前倒し山は FX8 の日足に残っているか（Girgin 2026 ブログの FX 移植・Q283-C1） | 棄却: 前後半で上位5%オフセットが一致しない |
| [turn-of-month-shift-nikkei-topix-q285](./turn-of-month-shift-nikkei-topix-q285) | Q285 日本株（Nikkei 225・TOPIX）の pre-TOM 4日効果は T+2 市場でも 2017 年以降に残るか（Q283-C2・Girgin 2026 の pre-TOM 前倒しを日本株に移植） | 棄却: 日本株の後半で S−C の z<2（前倒し窓は古典窓を上回らない） |
| [turn-of-month-shift-xasset-q286](./turn-of-month-shift-xasset-q286) | Q286 商品・BTC・FX の pre-TOM 4日効果は残るか（15銘柄パネルの非米国株13本・Q283-C3） | 棄却（K=0 ≤ 1）: Girgin の pre-TOM は株固有の現象で、商品・BTC・FX には及ばない |
| [two-month-live-vs-random](./two-month-live-vs-random) | Q144 2か月の成績はランダム売買の分布のどこに入るか、順位は次の2か月で入れ替わるか（15銘柄・TSMOM20） | 支持（2か月では実力と運を分けられず順位も入れ替わる） |
| [usdjpy-donchian-side-window-stability](./usdjpy-donchian-side-window-stability) | USDJPY 日足ドンチャンの「優位な売買方向」は5年窓をずらしても符号が保たれるか（Q353） | ノイズ（確定） |
| [usdjpy-london-open-vs-naive-momentum](./usdjpy-london-open-vs-naive-momentum) | USDJPY の日中順張りは、ロンドン開始30分の時刻条件つきシグナルでのみ効くか | README の「主な検証」表を参照 |
| [ustech-btc-leadlag](./ustech-btc-leadlag) | Q213 USTECH の直前 1 時間のリターンは BTC の次の 1 時間を予測するか（リード・ラグ・2020 年以降・H1） | 棄却 |
| [variance-ratio-setting-dependence](./variance-ratio-setting-dependence) | Q148 弱い形の効率性の検定（分散比）の結論は、設定（q・期間）でどれだけ動くか（Alahmadi・Basingab 2026 §3.5） | 1年の日足では分散比検定そのものがほとんど棄却しない（名目 5% 以下）。「1つの q で非効率と出ても他の q では… |
| [vix-term-inversion-index-q568](./vix-term-inversion-index-q568) | Q568 VIX の期間構造の逆転（VIX/VIX3M ≥ 1）の後 20 営業日は、株価指数 10 本の平均リターンが高いか | 確定（逆転後 20 日の指数の平均リターンは高い）。ただしシャープの上乗せは後半で消え、S17b と相関 0.79 で… |
| [vol-asymmetry-by-group](./vol-asymmetry-by-group) | Q247 ボラの非対称性の向きは群で違うか（株価指数は負・金は正・FX は無し。HAR に符号項・15 銘柄） | 未確定 |
| [vol-change-reversal](./vol-change-reversal) | Q174 ボラの変化は1日逆張りの翌日リターンを予測するか（DellaCorte 2015-3・15銘柄） | 棄却 |
| [vol-forecast-loss-vs-model](./vol-forecast-loss-vs-model) | Q187 為替のボラ予測で損失関数の差はモデルの差の何倍に見えるか（Tokajuk 2026-1 の為替移植） | 棄却（H0 支持: 為替では損失関数の差はモデルの差より小さい・Tokajuk の構図は為替で再現しない） |
| [vol-managed-buyhold-trend7](./vol-managed-buyhold-trend7) | Q305 TREND7 日足の買い持ちを直前 20 日実現ボラの逆数で規模調整するとシャープは同じ重み分布の循環シフトより高いか（Moreira–Muir の CFD 移植） | 未確定 |
| [vol-regime-autocorr](./vol-regime-autocorr) | Q294 15 銘柄 D1 の 1 次自己相関は高ボラ月で低ボラ月より高いか | 棄却 |
| [vol-regime-trend-following](./vol-regime-trend-following) | Q142 高ボラ局面では順張りの的中率と純損益が下がるか（15銘柄・GARCH なしの実現ボラ） | 未確定（事後発見の向きは4通り一致、大きさは半期では届かず・全期間は2/4 で ／z／≥2・主に XAUUSD と v… |
| [vol-targeting-tsmom](./vol-targeting-tsmom) | Q205 ボラ・ターゲティング（σ60 で規模調整）は 15 銘柄の日足順張りの年ごとのシャープを上げるか（Harvey ほか 2018 の追試） | 支持（確定・事前登録どおり） |
| [volume-confirmed-breakout](./volume-confirmed-breakout) | Q235 ティック出来高の急増つきドンチャン・ブレイクアウトは、継続率と純損益を上げるか（15 銘柄・H1 出来高から日足） | 棄却 |
| [volume-return-interaction](./volume-return-interaction) | Q216 出来高（ティック数）が多い日のリターンは翌日に続きやすく、少ない日は反転しやすいか（Campbell・Grossman・Wang 1993 の型・15 銘柄） | 棄却（CGW の型の反転は FX+コモディティ+指数の日足では前後半揃って再現しない） |
| [weekend-gap-fill-trend7](./weekend-gap-fill-trend7) | Q248 トレンド群（金・銀・原油 2・株価指数 2）の週末の窓は週内に埋まるか（Dao 2016 の FX 以外への条件の穴） | 棄却: 全期間の z < 2 |
| [weekend-gap-reversal-15](./weekend-gap-reversal-15) | Q296 15 銘柄 D1 の月曜ギャップ逆張り（金曜終値→月曜始値のギャップと逆方向に月曜のみ ±1、火曜以降 0）は all15 の年単位平均 bp（コスト後）が前後半とも正か（Dao2016-2 の 15 銘柄移植） | 棄却 |
| [weekend-variance-ratio](./weekend-variance-ratio) | Q272 月曜（週末跨ぎ）のリターン分散は他の曜日の何倍か（取引時間 vs 暦時間・French・Roll 1986・15銘柄） | 支持: all15 の log R の年単位平均が log1.3 未満かつ log3 に対し t≤−2（取引時間仮説） |
| [weekly-vs-daily-tsmom](./weekly-vs-daily-tsmom) | Q186 週足の順張りは日足より強いか（Neely 2003-3・15銘柄・2008〜2026） | 棄却（前後半のどちらかで ／t／<2） |
| [wfo-rest-if-all-negative-q461](./wfo-rest-if-all-negative-q461) | Q461 選び直す WFO で直前窓の全候補が負なら休むと、常に最良を選ぶより標本外は良くなるか | 全候補が負なら休む規則は、15 銘柄の日足 TSMOM の選び直し WFO では純損益も最大下落もほとんど変えない（B… |
| [wfo-window-gate-q333](./wfo-window-gate-q333) | Q333 WFO の「プラスの窓が60%以上」の関門は、腕のない順張りを何%通し、本物の優位を何%落とすか（Q331-C1） | 確定（使えない）。主因は検出力 |
| [wide48-cross-sectional-mom60](./wide48-cross-sectional-mom60) | Q371 48 銘柄 wide48 の D1 横断モメンタム L=60（上位1/3買い・下位1/3売り）は封印前の前後半とも年単位 t≥2 か | 未確定 |
| [wide48-regime-hitrate-baserate](./wide48-regime-hitrate-baserate) | Q449 wide48 D1 の高ボラ局面の方向的中率の上乗せは基準率と MRS 平滑化ラベルの先読みで説明されるか | ノイズ |
| [wide48-tsmom-l120-plain](./wide48-tsmom-l120-plain) | Q369 48 銘柄 wide48 の D1 プレーン TSMOM L=120（約6ヶ月・ボラ正規化なし）は封印前の前後半とも年単位 t≥2 か | 未確定 |
| [wide48-tsmom-l250-plain](./wide48-tsmom-l250-plain) | Q370 48 銘柄 wide48 の D1 プレーン TSMOM L=250（約12ヶ月・ボラ正規化なし）は封印前の前後半とも年単位 t≥2 か | 棄却 |
| [wide48-tsmom-l60-plain](./wide48-tsmom-l60-plain) | Q368 48 銘柄 wide48 の D1 プレーン TSMOM L=60（ボラ正規化なし・等重み）は封印前の前後半とも年単位 t≥2 か | 棄却 |
| [wide48-tsmom60-vol-target](./wide48-tsmom60-vol-target) | Q367 48 銘柄 wide48 の D1 TSMOM60（σ60 ボラ正規化・等リスク束）は封印前（〜2024-06）の前後半とも年単位 t≥2 か | 棄却 |
| [window-pnl-vs-vol](./window-pnl-vs-vol) | Q184 2か月窓の順張り成績はその窓の実現ボラとドリフトで説明できるか（Rashid 2026-1・Q144 の続き） | Rashid の「ボラに左右される」は向きが違う |
| [wrc-spa-disagreement](./wrc-spa-disagreement) | Q154 WRC・SPA(consistent)・SPA(conservative) の判定は同じルール群でどれだけ割れるか | 確定（棄却） |
| [wrc-spa-monthly-size](./wrc-spa-monthly-size) | Q310 月次（約 220 か月）に束ねた 15 銘柄の順張りルール群で、並べ替え帰無の下の WRC・SPA の棄却率は名目 5% を超えるか（Q154 の月次版・Q309-C1） | 支持 |
| [xauusd-london-fix-vshape](./xauusd-london-fix-vshape) | Q289 XAUUSD の WM/Reuters ロンドン fix（16:00 UTC）の前後に V 字はあるか | 未確定 |
| [xauusd-vol-regime-single](./xauusd-vol-regime-single) | Q161 XAUUSD 単銘柄・直前20〜60日の実現ボラが高い日に翌日の順張り損益が下がるか（ドリフト除去・前後半） | 未確定（6/6 で向き一致・／z／≥2 達成は 3/6 で窓40・60日に偏る・ドリフト除去は結論を変えない） |
| [year-concentration-top2-q455](./year-concentration-top2-q455) | Q455 日足戦略の封印前の純損益は特定の年に集中しているか（年別寄与の上位 1・2 年を除いた年単位 t） | 規則の上では 9 本すべて「集中あり」だが、9 本中 8 本は元の年単位 t が 2 未満で「除くと t<2」の枝が自… |
| [yen-vs-dollar-tsmom-d1](./yen-vs-dollar-tsmom-d1) | Q303 FX8 日足の TSMOM60 で円の組 3 本の純損益はドルの組 5 本を上回るか（円の組の 4 時間足の知見の日足版・組ラベルの全 56 通り帰無） | 未確定 |
