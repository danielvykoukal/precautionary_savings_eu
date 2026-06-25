#!/usr/bin/env bash
#
# Run the identification extensions (classic Python, no virtualenv).
# The main pipeline must have run first, so ../data exists:
#     cd .. && python3 01_collect_data.py && cd extensions
# Then:
#     bash run_extensions.sh
#
# Override the interpreter with PYTHON=python3.13.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
cd "$HERE"

for s in local_projections.py energy_event_study.py country_panel_fe.py \
         saving_composition.py saving_intentions.py; do
    echo ">> $s"
    "$PYTHON" "$s"
    echo
done

echo ">> done. See extensions/figures and extensions/data"
