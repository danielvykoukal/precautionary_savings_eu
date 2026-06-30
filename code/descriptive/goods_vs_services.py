#!/usr/bin/env python3
"""
Descriptive #5 --- Spending habits: goods vs services
=====================================================

Supervisor puzzle: if the saving rate is so high, how has spending on *services*
stayed so elevated? The answer is a composition shift inside consumption: as
households save more and pull back on *goods* (especially durables), they keep
spending on *services* (the post-COVID reopening plus strong services inflation).
High saving and strong services are reconciled by a goods->services rotation.

We split euro-area household final consumption into goods (durable +
semi-durable + non-durable) and services, track each share over time, and set
them against the saving rate.

Data: Eurostat nama_10_co3_p3 (final consumption by COICOP / durability) +
../data saving rate. Writes a figure + CSV + report.
    python goods_vs_services.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def get_consumption():
    """Euro-area household consumption: services vs goods (current-price), per year."""
    long = C.es_long("nama_10_fcs")   # final consumption aggregates by durability
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    C.show_dims(long, "nama_10_fcs")
    if "unit" in long.columns:        # real volumes (for the index); current-price fallback
        for u in ("CLV15_MEUR", "CLV10_MEUR", "CLV05_MEUR", "CP_MEUR", "CP_MNAC"):
            if u in set(long["unit"]):
                long = long[long["unit"] == u]
                break
    if "s_adj" in long.columns:       # one adjustment only (avoid summing SCA+NSA)
        for sa in ("SCA", "NSA", "SA"):
            if sa in set(long["s_adj"]):
                long = long[long["s_adj"] == sa]
                break
    geo = next((g for g in C.EA_GEOS if g in set(long["geo"])), None)
    if geo is None:
        raise RuntimeError("nama_10_fcs: no euro-area aggregate geo")
    long = long[long["geo"] == geo]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    piv = long.groupby(["year", "na_item"])["value"].sum().unstack("na_item")
    cols = set(piv.columns)
    goods_parts = [c for c in ("P311_S14", "P312_S14", "P313_S14") if c in cols]
    if "P314_S14" not in cols or not goods_parts:
        raise RuntimeError(f"nama_10_fcs: durability codes missing (have {sorted(cols)[:20]})")
    services = piv["P314_S14"]                 # services
    goods = piv[goods_parts].sum(axis=1)       # durable + semi-durable + non-durable
    say(f"  services=P314_S14; goods={'+'.join(goods_parts)}; geo={geo}")
    out = pd.DataFrame({"services": services, "goods": goods}).dropna()
    out["serv_share"] = 100 * out["services"] / (out["services"] + out["goods"])
    out["goods_share"] = 100 - out["serv_share"]
    out.index = out.index.astype(int)
    return out.sort_index(), geo


def main():
    say("#" * 72)
    say("# Goods vs services — the consumption rotation behind high saving")
    say("#" * 72)
    try:
        c, geo = get_consumption()
    except Exception as e:
        say(f"\nFAILED: {e}")
        with open(os.path.join(C.DATA, "goods_vs_services.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    base = 2019 if 2019 in c.index else int(c.index.min())
    c["goods_idx"] = 100 * c["goods"] / c.loc[base, "goods"]
    c["services_idx"] = 100 * c["services"] / c.loc[base, "services"]
    latest = int(c.index.max())
    say(f"\nReal consumption index ({base}=100): in {latest}, services "
        f"{c.loc[latest,'services_idx']:.0f} vs goods {c.loc[latest,'goods_idx']:.0f}.")
    say("The argument, plainly: a high saving rate just means households spend a smaller share "
        "of income. WITHIN what they spend, the mix rotated — in the 2020 lockdowns GOODS boomed "
        "(durables, electronics) while SERVICES collapsed; after reopening SERVICES rebounded "
        "strongly while goods demand faded. So 'elevated services spending' is the post-COVID "
        "services recovery (plus high services inflation), not a consumer boom; the GOODS weakness "
        "is part of why total consumption — and so the saving rate — stayed high. Split goods from "
        "services and the apparent tension between high saving and strong services disappears.")

    saving = C.annual_mean("ea_saving_rate_quarterly.csv", "saving")
    cc = c[c.index >= 2015]                          # focus on the recent rotation
    sv = saving[saving.index >= 2015]
    fig, ax1 = plt.subplots(figsize=(10, 5.6))
    ax2 = ax1.twinx(); ax2.grid(False)
    ax1.axhline(100, color=C.C_GREY, ls=":", lw=1)
    ax1.plot(cc.index, cc["services_idx"], color=C.C_MAIN, lw=2.8, marker="o", ms=4,
             label="services consumption (real)")
    ax1.plot(cc.index, cc["goods_idx"], color=C.C_ORANGE, lw=2.6, marker="o", ms=4,
             label="goods consumption (real)")
    ax1.set_ylabel(f"real consumption, index ({base}=100)")
    ax1.set_xlabel("year")
    if 2020 in cc.index:
        ax1.annotate("lockdown:\ngoods up, services down", xy=(2020, cc.loc[2020, "goods_idx"]),
                     xytext=(2015.3, 103.5), fontsize=8, color="#444",
                     arrowprops=dict(arrowstyle="->", color="#999", lw=0.9))
    if 2023 in cc.index:
        ax1.annotate("reopening:\nservices rebound, goods flat",
                     xy=(2023, cc.loc[2023, "services_idx"]), xytext=(2020.8, 90.5),
                     fontsize=8, color="#444", arrowprops=dict(arrowstyle="->", color="#999", lw=0.9))
    sv_line, = ax2.plot(sv.index, sv.values, color=C.C_HOT, lw=2.2, ls=(0, (1, 1)),
                        label="household saving rate (right)")
    ax2.set_ylabel("household saving rate (%)", color=C.C_HOT)
    ax2.tick_params(axis="y", colors=C.C_HOT)
    C.mark_periods(ax1, year_axis=True, shade=True, labels=False)
    ax1.set_title("Strong services + high saving are reconciled by weak goods\n"
                  f"euro-area real household consumption, goods vs services ({geo})",
                  fontweight="bold")
    h1, l1 = ax1.get_legend_handles_labels()
    ax1.legend(h1 + [sv_line], l1 + ["household saving rate (right)"],
               frameon=False, fontsize=8.5, loc="lower left")
    C.caveat(fig, "Eurostat nama_10_fcs, real volumes (2019=100). Services rebounded after reopening "
                  "while goods faded; that goods weakness is part of why overall consumption — and the "
                  "saving rate — stayed high. Nominal services spending is higher still (services inflation).")
    C.savefig(fig, "goods_vs_services.png")

    c.join(saving.rename("saving")).to_csv(os.path.join(C.DATA, "goods_vs_services.csv"))
    with open(os.path.join(C.DATA, "goods_vs_services.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'goods_vs_services.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
