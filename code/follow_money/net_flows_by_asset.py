#!/usr/bin/env python3
"""
Net household saving flows by asset type, vs the saving rate
===========================================================

Instead of the single "tilt" summary, this shows the full picture: the net flow
households put into EACH type of financial asset, year by year, as separate
series — currency & overnight deposits, time/savings deposits, bonds, equity &
investment funds, and insurance & pensions — matched against the saving rate.

It makes the post-2022 reallocation legible: bonds and time deposits surge while
overnight deposits collapse, even as the saving rate itself moves little.

Pulls Eurostat nasa_10_f_tr (via _common) and reads ../data saving rate.
    python net_flows_by_asset.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import glob
import _common as cm

# --- run from the flattened repo layout: point at the top-level data/ & figures/
cm.ROOT = os.path.dirname(os.path.dirname(cm.HERE))   # code/follow_money -> repo root
cm.ROOT_DATA = os.path.join(cm.ROOT, "data")
cm.DATA = os.path.join(cm.ROOT, "data")
cm.FIG = os.path.join(cm.ROOT, "figures")
_orig_root_csv = cm.root_csv
def _tagged_root_csv(name, required=True):
    if not os.path.exists(os.path.join(cm.ROOT_DATA, name)):
        hits = glob.glob(os.path.join(cm.ROOT_DATA, "?_" + name))
        if hits:
            return pd.read_csv(hits[0])
    return _orig_root_csv(name, required)
cm.root_csv = _tagged_root_csv

# Asset types match the M2 decomposition (ESA top-level instrument codes), so this
# is the time-series companion to M2_savings_reconciliation_decomposition.
# (label, [ESA instrument codes], colour)
ASSETS = [
    ("Currency & deposits (F2)",              ["F2"],              cm.C_BLUE),
    ("Bonds / debt securities (F3)",          ["F3"],              "#117a65"),
    ("Listed shares & investment funds (F5)", ["F5"],              cm.C_ORANGE),
    ("Insurance & pension entitlements (F6)", ["F6"],              cm.C_PURPLE),
    ("Other financial (F1/F7/F8)",            ["F1", "F7", "F8"],  cm.C_GREY),
]


def main():
    print("Pulling Eurostat household financial flows ...")
    long, geo = cm.household_flows()
    piv = long.groupby(["year", "na_item"])["value"].sum().unstack("na_item")
    piv = piv.sort_index()

    # build each asset's net flow (EUR bn), keeping only those present
    series = {}
    for label, codes, color in ASSETS:
        present = [c for c in codes if c in piv.columns]
        if not present:
            print(f"  note: {label} ({codes}) not found — skipped")
            continue
        series[label] = (piv[present].sum(axis=1) / 1000.0, color)

    saving = cm.annual_mean("ea_saving_rate_quarterly.csv", "saving")

    years = piv.index
    print(f"\ngeo={geo}; net flows in EUR bn (latest years):")
    cols = list(series.keys())
    print("year  " + "  ".join(f"{c[:14]:>14}" for c in cols))
    for y in [yr for yr in years if yr >= 2019]:
        row = "  ".join(f"{series[c][0].get(y, np.nan):>14.0f}" for c in cols)
        print(f"{y}  {row}")

    # ---------------- figure ----------------
    fig, ax1 = plt.subplots(figsize=(11, 6))
    ax2 = ax1.twinx()
    ax1.set_axisbelow(True)
    ax2.grid(False)
    ax1.axhline(0, color="black", lw=0.9)
    ax1.axvline(2021.5, color="grey", ls="--", lw=1)

    for label, (s, color) in series.items():
        ax1.plot(s.index, s.values, color=color, lw=2.2, marker="o", ms=3, label=label)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax1.set_ylabel("net flow into the asset type (EUR bn / yr)")
    ax1.set_xlabel("year")

    sav_line, = ax2.plot(saving.index, saving.values, color=cm.C_NAVY, lw=3.0,
                         ls=(0, (1, 1)), zorder=5, label="household saving rate (right)")
    ax2.set_ylim(0, 22)
    ax2.set_yticks([0, 5, 10, 15, 20])
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.set_ylabel("household saving rate (% of disposable income)", color=cm.C_NAVY)
    ax2.tick_params(axis="y", colors=cm.C_NAVY)

    ax1.text(2021.4, ax1.get_ylim()[1] * 0.97, "ECB hiking\nbegins (2022)",
             fontsize=8, color="grey", va="top", ha="right")

    h1, l1 = ax1.get_legend_handles_labels()
    ax1.legend(h1 + [sav_line], l1 + ["household saving rate (right)"],
               loc="upper left", frameon=True, framealpha=0.9, edgecolor="none",
               fontsize=8.5, ncol=2)
    ax1.set_title(f"Where euro-area households put their saving, by asset type\n"
                  f"net flows by ESA instrument vs the saving rate ({geo}) "
                  f"— companion to the M2 decomposition",
                  fontweight="bold")
    fig.tight_layout()
    cm.savefig(fig, "F3_net_flows_by_asset.png")

    out = pd.DataFrame({lab: s for lab, (s, _) in series.items()})
    out.index.name = "year"
    out.join(saving).to_csv(os.path.join(cm.DATA, "F3_net_flows_by_asset.csv"))
    print("\nWrote data/F3_net_flows_by_asset.csv")


if __name__ == "__main__":
    main()
