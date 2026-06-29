#!/usr/bin/env bash
# Descriptive extension --- run every script, continuing even if one source is down.
# Reads the project's ../data (copied in alongside this folder) and pulls a few extra
# Eurostat series + the GISCO boundaries. No FRED needed.
#     bash run.sh
cd "$(dirname "$0")" || exit 1

for s in structural_vs_cyclical.py europe_map.py goods_vs_services.py saving_composition_evolution.py; do
  echo ""
  echo "============================================================"
  echo "  $s"
  echo "============================================================"
  python3 "$s" || echo "  ($s exited with an error — continuing)"
done

echo ""
echo "Done. Figures in ./figures, per-script reports (*.md) and CSVs in ./data."
