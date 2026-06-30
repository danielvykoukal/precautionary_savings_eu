#!/usr/bin/env python3
"""
Composition tilt vs the ECB rate (+ correlation)
================================================

If the post-2022 reallocation toward yield is rate-driven, the composition tilt
(locked-for-yield minus instant-access, EUR bn/yr) should rise and fall WITH the
ECB rate. This plots the tilt (bars) against the ECB policy rate (line) and
reports their correlation.

Needs follow_the_money.csv (run follow_the_money.py first) + ../data/ecb_rate.csv.
    python tilt_vs_rates.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as cm


def main():
    fm_path = os.path.join(cm.DATA, "follow_the_money.csv")
    if not os.path.exists(fm_path):
        raise SystemExit("Missing data/follow_the_money.csv — run follow_the_money.py first.")
    fm = pd.read_csv(fm_path)
    fm["tilt_bn"] = (fm["locked_yield"] - fm["instant_access"]) / 1000.0

    rate = cm.annual_mean("ecb_rate.csv", "rate")          # ECB rate, annual mean
    df = fm.merge(rate.reset_index(), on="year", how="inner").sort_values("year")

    r_all = df["tilt_bn"].corr(df["rate"])
    recent = df[df["year"] >= 2010]
    r_recent = recent["tilt_bn"].corr(recent["rate"])
    print("Correlation between the composition tilt and the ECB rate (annual):")
    print(f"  full sample ({int(df['year'].min())}-{int(df['year'].max())}): "
          f"r = {r_all:+.2f}")
    print(f"  2010+:                          r = {r_recent:+.2f}")

    fig, ax1 = plt.subplots(figsize=(10.5, 5.8))
    ax2 = ax1.twinx()
    ax1.set_axisbelow(True)
    ax2.grid(False)

    colors = [cm.C_RED if v >= 0 else cm.C_BLUE for v in df["tilt_bn"]]
    ax1.bar(df["year"], df["tilt_bn"], color=colors, width=0.78,
            edgecolor="white", linewidth=0.4, alpha=0.95, zorder=2)
    ax1.axhline(0, color="black", lw=1.0)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax1.set_ylabel("composition tilt: locked-for-yield − instant-access (EUR bn/yr)")
    ax1.set_xlabel("year")

    l_rate, = ax2.plot(df["year"], df["rate"], color="#117a65", lw=2.8, marker="o",
                       ms=4, zorder=4, label="ECB policy rate (right)")
    ax2.set_ylabel("ECB policy rate (%, annual mean)", color="#117a65")
    ax2.tick_params(axis="y", colors="#117a65")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

    # correlation callout
    ax1.text(0.015, 0.97, f"corr(tilt, ECB rate) = {r_all:+.2f}",
             transform=ax1.transAxes, va="top", ha="left", fontsize=10,
             fontweight="bold", bbox=dict(boxstyle="round,pad=0.35", fc="white",
                                          ec="#117a65", alpha=0.9))

    from matplotlib.patches import Patch
    yield_p = Patch(color=cm.C_RED, label="tilt toward yield")
    cash_p = Patch(color=cm.C_BLUE, label="tilt toward instant-access cash")
    ax1.legend(handles=[yield_p, cash_p, l_rate], loc="lower left",
               frameon=True, framealpha=0.9, edgecolor="none", fontsize=9)

    ax1.set_title("The saving-composition tilt moves with the ECB rate\n"
                  "Euro-area households: tilt (bars) vs policy rate (line)",
                  fontweight="bold")
    fig.tight_layout()
    cm.savefig(fig, "tilt_vs_rates.png")

    df[["year", "tilt_bn", "rate"]].to_csv(
        os.path.join(cm.DATA, "tilt_vs_rates.csv"), index=False)
    print("\nWrote extension_follow_money/data/tilt_vs_rates.csv")


if __name__ == "__main__":
    main()
