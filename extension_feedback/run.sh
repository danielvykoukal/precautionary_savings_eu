#!/usr/bin/env bash
# Feedback extension — run every script, continuing even if one source is down.
#
# Each script pulls live data (Eurostat / FRED / ECB) and is self-contained: it
# reads the project's ../data (copied in alongside this folder) and writes its own
# outputs to ./data and ./figures. If ../data is stale, refresh it first:
#     cd .. && python3 01_collect_data.py && cd extension_feedback
#
#     bash run.sh
cd "$(dirname "$0")" || exit 1

for s in liquidity_ladder.py money_supply.py risk_premia.py forward_looking.py energy_liquidity.py us_comparison.py; do
  echo ""
  echo "============================================================"
  echo "  $s"
  echo "============================================================"
  python3 "$s" || echo "  ($s exited with an error — continuing)"
done

echo ""
echo "Done. Figures in ./figures, per-script reports (*.md) and CSVs in ./data."
