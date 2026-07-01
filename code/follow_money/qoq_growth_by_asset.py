#!/usr/bin/env python3
"""
Quarter-on-quarter growth of the household balance sheet, by component
======================================================================

For each part of the euro-area household balance sheet, the q-o-q % growth of the
outstanding STOCK (so it reflects net flows AND valuation changes):

  financial assets, by instrument (Eurostat nasq_10_f_bs, households S14_S15):
    F2 currency & deposits · F3 debt securities · F5 equity & fund shares ·
    F6 insurance & pension entitlements
  borrowing:  F4 loans (liability side)
  housing:    euro-area house price index, q-o-q (Eurostat prc_hpi_q, RCH_Q)

Small multiples with a shared y-axis so the momentum is comparable across
components, with the Feb-2022 invasion and Jul-2022 first-hike lines marked.
    python qoq_growth_by_asset.py
"""

import os
import re
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import eurostat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")

INVASION = pd.Timestamp("2022-02-24")
HIKE = pd.Timestamp("2022-07-27")

# (label, na_item, finpos, colour)
COMPONENTS = [
    ("Currency & deposits (F2)",        "F2", "ASS", "#2e86c1"),
    ("Debt securities (F3)",            "F3", "ASS", "#117a65"),
    ("Equity & fund shares (F5)",       "F5", "ASS", "#e67e22"),
    ("Insurance & pensions (F6)",       "F6", "ASS", "#6c3483"),
    ("Borrowing — loans (F4)",          "F4", "LIAB", "#c0392b"),
    ("Housing — house prices",          "HPI", None, "#1f4e79"),
]


def es_long(code):
    df = eurostat.get_data_df(code)
    geo = [c for c in df.columns if "geo" in c.lower()][0]
    df = df.rename(columns={geo: "geo"})
    tcols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    idc = [c for c in df.columns if c not in tcols]
    long = df.melt(id_vars=idc, value_vars=tcols, var_name="time", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long.dropna(subset=["value"])


def q_index(s):
    s = s.copy()
    s["q"] = pd.PeriodIndex(s["time"].str.replace("-", ""), freq="Q").to_timestamp()
    return s


def balance_sheet():
    """Quarterly household stocks by instrument -> q-o-q % growth per series."""
    long = es_long("nasq_10_f_bs")
    sec = "S14_S15" if "S14_S15" in set(long["sector"]) else "S14"
    long = long[long["sector"] == sec]
    if "co_nco" in long.columns and "NCO" in set(long["co_nco"]):
        long = long[long["co_nco"] == "NCO"]
    geo = next((g for g in ("EA20", "EA19", "EA") if g in set(long["geo"])), None)
    unit = "MIO_EUR" if "MIO_EUR" in set(long["unit"]) else "MIO_NAC"
    long = long[(long["geo"] == geo) & (long["unit"] == unit)]
    long = q_index(long)
    out = {}
    for _lab, item, finpos, _c in COMPONENTS:
        if item == "HPI":
            continue
        s = long[(long["na_item"] == item) & (long["finpos"] == finpos)]
        s = s.groupby("q")["value"].sum().sort_index()
        out[item] = (s.pct_change() * 100).rename(item)
    return out, geo


def house_prices():
    long = es_long("prc_hpi_q")
    geo = next((g for g in ("EA20", "EA19", "EA") if g in set(long["geo"])), None)
    f = long[(long["geo"] == geo) & (long["purchase"] == "TOTAL") & (long["unit"] == "RCH_Q")]
    f = q_index(f)
    return f.groupby("q")["value"].mean().sort_index().rename("HPI")


def main():
    print("Pulling quarterly household balance sheet + house prices ...")
    bs, geo = balance_sheet()
    hpi = house_prices()
    series = dict(bs); series["HPI"] = hpi

    start = pd.Timestamp("2005-04-01")   # common window (house prices start 2005)
    fig, axes = plt.subplots(3, 2, figsize=(13, 9), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, (lab, item, _fp, col) in zip(axes, COMPONENTS):
        s = series[item]
        s = s[s.index >= start]
        ax.axhline(0, color="black", lw=0.7)
        ax.fill_between(s.index, 0, s.values, color=col, alpha=0.25, zorder=1)
        ax.plot(s.index, s.values, color=col, lw=1.6, zorder=2)
        ax.axvline(INVASION, color="grey", ls="--", lw=1, zorder=3)
        ax.axvline(HIKE, color="#7b241c", ls=":", lw=1, zorder=3)
        ax.set_title(lab, fontsize=10.5, fontweight="bold", color=col)
        ax.set_ylabel("q-o-q %", fontsize=8)
        ax.grid(True, alpha=0.25)
    # shared, robust y-limits (financial-asset revaluations can spike)
    allv = np.concatenate([series[i][series[i].index >= start].dropna().values
                           for _l, i, _f, _c in COMPONENTS])
    lim = np.nanpercentile(np.abs(allv), 98)
    axes[0].set_ylim(-lim, lim)
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.setp(ax.get_xticklabels(), rotation=45, fontsize=8)
    # one shared legend for the two event lines
    axes[1].plot([], [], color="grey", ls="--", lw=1, label="Russia invades (Feb 2022)")
    axes[1].plot([], [], color="#7b241c", ls=":", lw=1, label="ECB 1st hike (Jul 2022)")
    axes[1].legend(loc="upper right", frameon=False, fontsize=8)
    fig.suptitle("Quarter-on-quarter growth of the household balance sheet, by component\n"
                 f"euro area ({geo}): financial assets by type, borrowing, and housing "
                 "— stock growth (flows + valuation)", fontweight="bold", fontsize=13)
    fig.supxlabel("quarter", fontsize=9)
    fig.tight_layout(rect=(0, 0.01, 1, 0.95))
    fig.savefig(os.path.join(FIG, "F7_qoq_growth_by_component.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/F7_qoq_growth_by_component.png")

    out = pd.DataFrame({i: series[i] for _l, i, _f, _c in COMPONENTS})
    out.index.name = "quarter"
    out[out.index >= start].to_csv(os.path.join(DATA, "F_qoq_growth_by_component.csv"))
    print("Wrote data/F_qoq_growth_by_component.csv")

    # brief recent readout
    print("\nrecent q-o-q % growth (last 6 quarters):")
    print(out[out.index >= "2024-01-01"].round(2).to_string())


if __name__ == "__main__":
    main()
