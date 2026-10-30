#!/bin/bash
# 2026-10-30 深夜・第 3 便: Q581（グリッドの設定地図・1,170 セル × 2 種の帰無）を持ち時間いっぱい計算
#   → キューの Q581 を 保留→待ち に戻す → /lab 1 件で Opus が判定・記録
# 使い方（Mac のターミナル・1 行）:
#   caffeinate -i bash ~/ワークスペース/検証/verification-lab/tools/run_night_20261030c.sh 7.5
#   引数 = 計算の持ち時間（時間）。既定 7.5。帰無を 50 本ずつのパスで積み増し、時間が来たら区切りの良いところで止める（上限 B=2000）。
#   計算の後に Opus の記録が 5〜15 分つく。
#   途中で止まったら同じコマンドをもう一度（results/partial の途中結果から続く）。止めたいときは Ctrl-C。
set -u
HOURS="${1:-7.5}"
cd "$(dirname "$0")/.." || exit 1   # verification-lab
LOG="../自動実行/ログ/night_20261030c_$(date +%H%M%S).log"; mkdir -p "$(dirname "$LOG")"
Q="financial-engineering/grid-map-q581"
echo "=== Q581 計算 開始 $(date '+%F %T') 持ち時間=${HOURS}h  cpu=$(sysctl -n hw.ncpu 2>/dev/null || nproc)" | tee -a "$LOG"
( cd "$Q" && Q581_HOURS="$HOURS" python3 kensho_grid_map_q581.py 2>&1 ) | tee -a "$LOG"
echo "=== Q581 計算 終了 $(date '+%F %T')" | tee -a "$LOG"
if ls "$Q"/results/Q581_result_*.json >/dev/null 2>&1; then
  python3 - <<'PY' 2>&1 | tee -a "$LOG"
import os, unicodedata as U
home = os.path.expanduser("~")
def find(base, rel):
    cur = base
    for p in rel.split("/"):
        hit = [x for x in os.listdir(cur) if U.normalize("NFC", x) == U.normalize("NFC", p)]
        if not hit: raise SystemExit("見つからない: " + rel)
        cur = os.path.join(cur, hit[0])
    return cur
qp = find(home, "ワークスペース/検証/_基盤/知識/検証キュー.md")
lines = open(qp, encoding="utf-8").read().split("\n"); n = 0
for i, l in enumerate(lines):
    if l.startswith("|") and "| Q581 |" in l:
        c = l.split("|")
        if len(c) > 7 and c[7].strip().startswith("保留"):
            c[6] = " 計算済み（run_night_20261030c.sh）。再計算せず results の最新 JSON を読む（無ければ --analyze だけ） "; c[7] = " 待ち "; lines[i] = "|".join(c); n += 1
open(qp, "w", encoding="utf-8").write("\n".join(lines)); print(f"検証キュー: Q581 を待ちに戻した（{n} 行）")
PY
  echo "=== /lab 1 件（Opus が Q581 を判定・記録） $(date '+%F %T')" | tee -a "$LOG"
  LAB_SKIP_OLLAMA=1 bash ../自動実行/lab_run.sh 1 2>&1 | tail -25 | tee -a "$LOG"
else
  echo "結果 JSON が無い（計算が途中で止まった）。同じコマンドをもう一度打てば続きから" | tee -a "$LOG"
fi
echo "=== 全部終わり $(date '+%F %T')" | tee -a "$LOG"
echo "見るもの: $Q/README.md の結果節、自動実行/レポート/事後の判断_*.md、自動実行/要対応.md"
