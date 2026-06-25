#!/usr/bin/env bash
#
# Run the "follow the money" extension (classic Python, no virtualenv).
# The main pipeline must have run first, so ../data exists:
#     cd .. && python3 01_collect_data.py && cd extension_follow_money
# Then:
#     bash run.sh
#
# Override the interpreter with PYTHON=python3.13.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
cd "$HERE"

for s in follow_the_money.py saving_vs_rates_reversal.py; do
    echo ">> $s"
    "$PYTHON" "$s"
    echo
done

echo ">> done. See extension_follow_money/figures and extension_follow_money/data"
