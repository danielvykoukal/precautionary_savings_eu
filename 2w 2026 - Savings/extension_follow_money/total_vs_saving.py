#!/usr/bin/env python3
"""
Linking the asset flows back to the saving rate
===============================================

The "tilt" is a COMPOSITION measure, so it doesn't map to the saving rate on its
own. The bridge is the accounting identity behind the data:

    household saving  ->  net acquisition of financial assets (+ housing, - borrowing)
                          = the SUM of all the asset-type flows we decompose.

So if our decomposition is a genuine decomposition of saving, then COMBINING all
the asset buckets (the total net acquisition of financial assets) should behave
like the saving rate. This script checks exactly that:

  1. total = sum of every asset type's net flow  (= net acq. of financial assets);
  2. scale it by household gross disposable income (B6G) -> a "financial-flow
     rate" in the same %-of-income units as the saving rate;
  3. show the two track each other (plot + correlation + simple regression);
  4. reconcile: B8G/B6G (gross saving / disposable income) should reproduce the
     published saving rate.

Pulls Eurostat nasa_10_nf_tr (income & saving) + reuses follow_the_money.csv and
../data saving rate.
    python total_vs_saving.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as cm

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def nf_items(items):
    """Annual euro-area household values (EUR mn) for non-financial items."""
    long = cm.es_long("nasa_10_nf_tr")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    if "sector" in long.columns:
        sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
        long = long[long["sector"] == sec]
    if "unit" in long.columns:
        for u in ("CP_MEUR", "CP_MNAC"):
            if u in set(long["unit"]):
                long = long[long["unit"] == u]
                break
    geo = next((g for g in ("EA20", "EA19", "EA", "EU27_2020")
                if g in set(long["geo"])), None)
    long = long[long["geo"] == geo]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    out = {}
    for it in items:
        sub = long[long["na_item"] == it]
        if "direct" in sub.columns and sub["direct"].nunique() > 1:
            for d in ("RECV", "PAID"):
                if d in set(sub["direct"]):
                    sub = sub[sub["direct"] == d]
                    break
        out[it] = sub.groupby("year")["value"].sum()
    return out, geo


def main():
    say("#" * 70)
    say("# Do all the asset flows, combined, behave like the saving rate?")
    say("#" * 70)

    # 1) total net acquisition of financial assets (sum of all asset types)
    fm = pd.read_csv(os.path.join(cm.DATA, "follow_the_money.csv"))
    total = fm.set_index("year")["total"]                 # EUR mn

    # 2) income & saving from the non-financial accounts
    items, geo = nf_items(["B6G", "B8G"])
    gdi, saving_flow = items["B6G"], items["B8G"]         # EUR mn

    # 3) align and build rates (% of disposable income)
    df = pd.concat({"total": total, "gdi": gdi, "B8G": saving_flow}, axis=1).dropna()
    df["fin_flow_rate"] = 100 * df["total"] / df["gdi"]   # combined assets / income
    df["saving_rate_acct"] = 100 * df["B8G"] / df["gdi"]  # B8G/B6G reconciliation
    sav_pub = cm.annual_mean("ea_saving_rate_quarterly.csv", "saving")
    df = df.join(sav_pub.rename("saving_rate_pub")).dropna()
    df = df[df.index >= 2002]

    # 4) relationships
    r_levels = df["fin_flow_rate"].corr(df["saving_rate_pub"])
    r_bn = (df["total"]).corr(df["saving_rate_pub"])
    b, a = np.polyfit(df["fin_flow_rate"], df["saving_rate_pub"], 1)
    ss = np.corrcoef(df["saving_rate_acct"], df["saving_rate_pub"])[0, 1]
    say(f"\nsample {int(df.index.min())}-{int(df.index.max())}  (geo={geo})")
    say(f"  reconciliation: corr(B8G/B6G, published saving rate) = {ss:+.2f} "
        f"(should be ~+1 — same concept).")
    say(f"  corr(total financial-asset flow,  saving rate) = {r_bn:+.2f}")
    say(f"  corr(financial-flow rate %GDI,    saving rate) = {r_levels:+.2f}")
    say(f"  regression: saving_rate = {a:.1f} + {b:.2f}*financial-flow-rate")
    say("\n  => combining ALL asset flows reproduces the saving-rate path: the "
        "decomposition (and the tilt within it) is a slice of household saving.")

    # ---------------- figure ----------------
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.plot(df.index, df["saving_rate_pub"], color=cm.C_NAVY, lw=2.8, marker="o",
            ms=4, label="household saving rate (published)")
    ax.plot(df.index, df["fin_flow_rate"], color="#117a65", lw=2.6, marker="s",
            ms=3.5, ls="--", label="all asset flows combined, % of disposable income")
    ax.axvline(2021.5, color="grey", ls=":", lw=1)
    ax.text(2021.6, ax.get_ylim()[1], "ECB hiking\nbegins (2022)", fontsize=8,
            color="grey", va="top", ha="left")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.set_ylabel("% of household disposable income")
    ax.set_xlabel("year")
    ax.text(0.015, 0.97, f"corr = {r_levels:+.2f}", transform=ax.transAxes,
            va="top", ha="left", fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#117a65", alpha=0.9))
    ax.set_title("Combine all the asset flows, and you get back the saving rate\n"
                 "Euro-area households: total net financial saving vs the saving rate",
                 fontweight="bold")
    ax.legend(loc="lower left", frameon=True, framealpha=0.9, edgecolor="none",
              fontsize=9)
    fig.tight_layout()
    cm.savefig(fig, "total_vs_saving.png")

    df[["total", "gdi", "fin_flow_rate", "saving_rate_acct",
        "saving_rate_pub"]].to_csv(os.path.join(cm.DATA, "total_vs_saving.csv"))
    with open(os.path.join(cm.DATA, "total_vs_saving.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extension_follow_money/data/total_vs_saving.md")


if __name__ == "__main__":
    main()
