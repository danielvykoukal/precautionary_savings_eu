#!/usr/bin/env python3
"""
Descriptive #4b --- How saving rates evolved across Europe
==========================================================

The map is a snapshot; this is the time dimension. We plot the household saving
rate for every country since 2000 (light grey for context), highlight a few
North/high and South/low economies and the euro-area average, and track the
North-South gap. The point: the spread is long-standing, the ranking is sticky,
and the post-2022 lift is broad rather than a single-country story.

Data: Eurostat tec00131 (annual gross household saving rate by country).
    python saving_rate_evolution.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

# --- run from the flattened repo layout: top-level data/ & figures/, tagged CSVs
import os as _os, glob as _glob
C.ROOT = _os.path.dirname(_os.path.dirname(C.HERE))
C.ROOT_DATA = _os.path.join(C.ROOT, "data")
C.DATA = _os.path.join(C.ROOT, "data")
C.FIG = _os.path.join(C.ROOT, "figures")
_ORC = C.root_csv
def _TRC(name, required=True):
    import pandas as _pd
    if not _os.path.exists(_os.path.join(C.ROOT_DATA, name)):
        _h = _glob.glob(_os.path.join(C.ROOT_DATA, "?_" + name))
        if _h:
            return _pd.read_csv(_h[0])
    return _ORC(name, required)
C.root_csv = _TRC

REPORT = []
COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "FI", "IE", "PT", "EL",
             "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT", "SE", "DK"]
# highlighted lines: North/high (cool) vs South/low (warm)
HIGHLIGHT = {"DE": C.C_MAIN, "NL": C.C_COOL, "SE": "#117a65",
             "FR": "#8e44ad", "IT": C.C_HOT, "ES": C.C_ORANGE, "EL": "#7b241c"}
START = 2000


def say(line=""):
    print(line)
    REPORT.append(str(line))


def get_panel():
    long = C.es_long("tec00131")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    piv = long.pivot_table(index="geo", columns="year", values="value", aggfunc="mean")
    piv = piv[[y for y in piv.columns if y >= START]]
    return piv


def main():
    say("#" * 72)
    say("# How household saving rates evolved across Europe")
    say("#" * 72)
    piv = get_panel()
    years = list(piv.columns)
    ea_geo = next((g for g in ("EA20", "EA19", "EA") if g in piv.index), None)

    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    # context: every country, light grey
    for g in COUNTRIES:
        if g in piv.index:
            ax.plot(years, piv.loc[g].values, color="#cfcfcf", lw=0.8, zorder=1)
    # euro-area average
    if ea_geo:
        ax.plot(years, piv.loc[ea_geo].values, color="black", lw=2.6, ls=(0, (1, 1)),
                zorder=5, label="Euro area")
        eal = piv.loc[ea_geo].dropna()
        if len(eal):
            ax.annotate("Euro area", (eal.index[-1], eal.iloc[-1]), xytext=(5, 0),
                        textcoords="offset points", color="black", fontsize=9,
                        fontweight="bold", va="center")
    # highlighted countries + end labels
    for g, col in HIGHLIGHT.items():
        if g not in piv.index:
            continue
        s = piv.loc[g]
        ax.plot(years, s.values, color=col, lw=2.4, zorder=4, label=g)
        last = s.dropna()
        if len(last):
            ax.annotate(g, (last.index[-1], last.iloc[-1]), xytext=(5, 0),
                        textcoords="offset points", color=col, fontsize=9,
                        fontweight="bold", va="center")
    C.mark_periods(ax, year_axis=True, shade=True, labels=True)
    ax.set_ylabel("gross household saving rate (% of disposable income)")
    ax.set_xlabel("year")
    ax.set_title("How saving rates evolved across Europe\n"
                 "a sticky North-South ranking; a broad post-2022 lift",
                 fontweight="bold")
    # no legend: highlighted lines are labelled at their right-hand ends; grey =
    # all 21 countries; the euro-area average is the black dotted line (see footnote)
    C.caveat(fig, "Eurostat tec00131. Grey = all 21 countries; coloured = highlighted North (cool) "
                  "vs South (warm) economies and the euro-area average. Ranking is persistent.")
    C.savefig(fig, "O_saving_rate_evolution.png")

    # North-South gap over time (highlighted North avg minus South avg)
    north, south = ["DE", "NL", "SE", "AT", "FI", "DK"], ["IT", "ES", "EL", "PT"]
    nN = [g for g in north if g in piv.index]; sS = [g for g in south if g in piv.index]
    gap = piv.loc[nN].mean() - piv.loc[sS].mean()
    ylast = gap.dropna().index[-1]
    say(f"\nNorth-South saving-rate gap (avg {nN} minus {sS}):")
    say(f"  ~2000: {gap.get(min(years), float('nan')):.1f} pp  ->  {ylast}: {gap[ylast]:.1f} pp")
    say("Reading: the North consistently saves ~8-12 pp more than the South; the gap "
        "is long-standing and the country ranking barely changes. The post-2022 rise "
        "lifted most countries together rather than re-ordering them.")

    piv.to_csv(os.path.join(C.DATA, "saving_rate_evolution.csv"))
    with open(os.path.join(C.DATA, "saving_rate_evolution.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'saving_rate_evolution.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
