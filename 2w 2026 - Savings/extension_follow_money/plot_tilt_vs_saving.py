#!/usr/bin/env python3
"""
Saving tilt (locked-for-yield minus instant-access) vs the saving rate
======================================================================

One chart, two stories on shared years:
  * bars  = net flow into "locked for yield" (time deposits + bonds) MINUS net
            flow into "instant-access" (cash + overnight deposits), EUR bn/yr.
            Positive = households tilted that year's saving toward yield;
            negative = toward instant-access cash.
  * line  = the household saving rate (annual mean, %), on the right axis.

It makes the "how vs why" point visible: the saving rate stays elevated while the
COMPOSITION tilt flips from cash (negative, the low-rate/COVID years) to yield
(positive, once rates rose in 2023-24).

Needs follow_the_money.csv (run follow_the_money.py first) and ../data saving.
    python plot_tilt_vs_saving.py
"""

import os

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter

import _common as cm

START_YEAR = 2002


def main():
    path = os.path.join(cm.DATA, "follow_the_money.csv")
    if not os.path.exists(path):
        raise SystemExit("Missing data/follow_the_money.csv — run follow_the_money.py first.")
    fm = pd.read_csv(path)
    fm["tilt_bn"] = (fm["locked_yield"] - fm["instant_access"]) / 1000.0  # EUR bn

    sav_q = cm.load_quarterly("ea_saving_rate_quarterly.csv", "saving")
    sav_a = sav_q.groupby(sav_q.index.year).mean().rename("saving")
    sav_a.index.name = "year"

    df = fm.merge(sav_a.reset_index(), on="year", how="inner")
    df = df[df["year"] >= START_YEAR].sort_values("year")

    print("year   tilt(EUR bn)   saving(%)")
    for _, r in df.iterrows():
        print(f"{int(r['year'])}   {r['tilt_bn']:>+11.0f}   {r['saving']:>8.1f}")

    fig, ax1 = plt.subplots(figsize=(11, 6))
    ax2 = ax1.twinx()
    ax1.set_axisbelow(True)
    ax2.grid(False)

    # --- left axis: the composition tilt (bars, EUR bn) ---
    colors = [cm.C_RED if v >= 0 else cm.C_BLUE for v in df["tilt_bn"]]
    ax1.bar(df["year"], df["tilt_bn"], color=colors, width=0.78,
            edgecolor="white", linewidth=0.4, alpha=0.95, zorder=2)
    ax1.axhline(0, color="black", lw=1.0)
    ax1.set_ylim(-850, 1500)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax1.set_ylabel("net flow: locked-for-yield − instant-access  (EUR bn / yr)")
    ax1.set_xlabel("year")

    # --- right axis: the saving rate (line, %) — forced to a positive range ---
    l_sav, = ax2.plot(df["year"], df["saving"], color=cm.C_NAVY, lw=2.8,
                      marker="o", ms=4, zorder=4, label="household saving rate (right)")
    ax2.set_ylim(0, 22)
    ax2.set_yticks([0, 5, 10, 15, 20])
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.set_ylabel("household saving rate (% of disposable income)", color=cm.C_NAVY)
    ax2.tick_params(axis="y", colors=cm.C_NAVY)

    # --- regime backdrops (inspired by chart A): ZLB, COVID, period of interest ---
    # ZLB span = the years the ECB deposit rate was at or below zero (data-driven).
    try:
        r = cm.root_csv("ecb_rate.csv")
        r = r.rename(columns={r.columns[0]: "date"})
        r["date"] = pd.to_datetime(r["date"], errors="coerce")
        rv = r.columns[1]
        zl = r[pd.to_numeric(r[rv], errors="coerce") <= 0]["date"].dropna()
        fy = lambda d: d.year + (d.dayofyear - 1) / 365.25
        zlb_start, zlb_end = fy(zl.min()), fy(zl.max())
    except Exception:
        zlb_start, zlb_end = 2012.5, 2022.6
    xmax = df["year"].max() + 0.6

    ax1.axvspan(zlb_start, zlb_end, color="#5d6d7e", alpha=0.07, zorder=0)
    ax1.axvspan(2019.7, 2021.4, color="#5d6d7e", alpha=0.17, zorder=0)
    ax1.axvspan(zlb_end, xmax, color="#e0a800", alpha=0.11, zorder=0)
    ax1.axvline(zlb_end, color="grey", ls="--", lw=1, zorder=1)

    top = 1455
    ax1.text((zlb_start + 2019.7) / 2, top, "ZLB era\n(zero / neg. rates)",
             ha="center", va="top", fontsize=8.5, color="#4a5a6a")
    ax1.text(2020.55, top, "COVID\nforced saving", ha="center", va="top",
             fontsize=8.5, color="#34495e")
    ax1.text((zlb_end + xmax) / 2, top, "period of\ninterest", ha="center",
             va="top", fontsize=8.5, color="#8a6d00")

    # compact value tag on the smoking-gun 2023 bar
    ax1.text(2023, 1285, "+€1.26 tn", ha="center", va="bottom",
             fontsize=9, fontweight="bold", color=cm.C_RED)

    # --- legend ---
    yield_p = mpatches.Patch(color=cm.C_RED, label="tilt toward yield (bonds, time deposits)")
    cash_p = mpatches.Patch(color=cm.C_BLUE, label="tilt toward instant-access cash")
    ax1.legend(handles=[yield_p, cash_p, l_sav], loc="lower left",
               frameon=True, framealpha=0.9, edgecolor="none", fontsize=9)

    ax1.set_title("Saving stayed high — but WHERE it went flipped from cash to yield\n"
                  "Euro-area households: composition tilt (bars) vs the saving rate (line)",
                  fontweight="bold")
    fig.tight_layout()
    cm.savefig(fig, "tilt_vs_saving.png")

    df[["year", "tilt_bn", "saving"]].to_csv(
        os.path.join(cm.DATA, "tilt_vs_saving.csv"), index=False)
    print("\nWrote extension_follow_money/data/tilt_vs_saving.csv")


if __name__ == "__main__":
    main()
