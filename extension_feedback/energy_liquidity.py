#!/usr/bin/env python3
"""
Feedback #4 --- The risk of too little CASH against rising energy prices
========================================================================

Supervisor feedback: "talk about the potential risk of not holding enough cash
to fight rising energy prices."

A precautionary buffer is only useful if it can cover a NON-DEFERRABLE shock. The
energy bill is the cleanest example: you cannot postpone heating. The catch from
the rest of this analysis:

  * Households moved OUT of instant-access cash after 2022 (follow_the_money) and
    most household wealth is not instant cash anyway (liquidity_ladder) ...
  * ... exactly as the energy price level jumped ~50-60% and stayed high.

Selling marketable assets (ladder T3) to pay an energy bill is possible but
crystallises losses precisely in a stressed, high-tension state when those asset
prices are themselves depressed (risk_premia) — so "sellable fast" is not the
same as "safe to spend now." And the squeeze is regressive: the lowest-income
households spend the largest budget share on energy yet have the thinnest (often
negative) saving buffer.

This script makes the two points:
  (1) aggregate: the instant-cash share of household wealth vs the energy-price
      level over time;
  (2) distribution: energy budget share vs saving capacity, by income quintile.

Reuses build_tiers() from liquidity_ladder.py; reads ../data; pulls energy HICP.
    python energy_liquidity.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C
from liquidity_ladder import build_tiers

REPORT = []

# Energy share of household consumption by income quintile (electricity, gas &
# other fuels, COICOP CP045). ILLUSTRATIVE / stylised from Eurostat HBS + ECB
# distributional work — VERIFY against the latest HBS before publishing. The
# robust point is the regressive GRADIENT (poorest spend the largest share).
ENERGY_BUDGET_SHARE = {1: 11.0, 2: 9.5, 3: 8.0, 4: 7.0, 5: 5.5}


def say(line=""):
    print(line)
    REPORT.append(str(line))


def energy_price_index():
    """Euro-area energy HICP. Prefer the index level (prc_hicp_midx, NRG),
    fall back to compounding the YoY series (prc_hicp_manr, NRG). Rebased 2019=100."""
    # try the index level
    try:
        long = C.es_long("prc_hicp_midx")
        if "coicop" in long.columns and "NRG" in set(long["coicop"]):
            long = long[long["coicop"] == "NRG"]
        geo = next((g for g in C.EA_GEOS if g in set(long["geo"])), None)
        long = long[long["geo"] == geo]
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["date"] = long["time"].map(C.parse_time)
        s = (long.dropna(subset=["value", "date"]).sort_values("date")
                 .set_index("date")["value"].resample("MS").mean())
        if len(s) > 24:
            base = s[s.index.year == 2019].mean()
            return (100 * s / base).rename("energy_index"), "prc_hicp_midx NRG"
    except Exception as e:
        say(f"  energy index (midx) failed: {e}; trying YoY compounding")
    # fallback: compound YoY
    long = C.es_long("prc_hicp_manr")
    if "coicop" in long.columns and "NRG" in set(long["coicop"]):
        long = long[long["coicop"] == "NRG"]
    geo = next((g for g in C.EA_GEOS if g in set(long["geo"])), None)
    long = long[long["geo"] == geo]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["date"] = long["time"].map(C.parse_time)
    yoy = (long.dropna(subset=["value", "date"]).sort_values("date")
              .set_index("date")["value"].resample("MS").mean())
    idx = (1 + yoy / 100).cumprod()
    base = idx[idx.index.year == 2019].mean()
    return (100 * idx / base).rename("energy_index"), "prc_hicp_manr NRG (compounded)"


def main():
    say("#" * 72)
    say("# Energy prices vs the cash buffer — is there enough liquidity?")
    say("#" * 72)

    # ---- (1) aggregate: instant-cash share of wealth vs energy price level ----
    cash_share = None
    try:
        long_s, geo = C.household_instruments("nasa_10_f_bs")
        stocks, _ = build_tiers(long_s)
        cash_share = stocks.set_index("year")["narrow_cash_share"]
        say(f"\ninstant-cash (T1) share of household wealth, {geo}:")
        for y, v in cash_share[cash_share.index >= 2018].items():
            say(f"  {y}: {v:4.1f}%")
    except Exception as e:
        say(f"  stocks/cash-share step failed: {e}")

    energy = src = None
    try:
        energy, src = energy_price_index()
        peak = energy[energy.index >= "2021-01-01"].max()
        say(f"\nenergy price level ({src}, 2019=100): peak {peak:.0f} "
            f"(+{peak-100:.0f}% vs 2019). Non-deferrable, and it stays elevated.")
    except Exception as e:
        say(f"  energy price step failed: {e}")

    if energy is not None:
        fig, ax1 = plt.subplots(figsize=(10, 5.4))
        ax2 = ax1.twinx()
        ax2.grid(False)
        ax1.plot(energy.index, energy.values, color=C.C_HOT, lw=2.2,
                 label="euro-area energy price level (2019=100)")
        ax1.axhline(100, color=C.C_HOT, ls=":", lw=1, alpha=0.6)
        ax1.set_ylabel("energy price index (2019=100)", color=C.C_HOT)
        ax1.tick_params(axis="y", colors=C.C_HOT)
        if cash_share is not None:
            cy = cash_share.copy()
            cy.index = pd.to_datetime(cy.index.astype(str) + "-07-01")
            ax2.plot(cy.index, cy.values, color=C.C_COOL, lw=2.6, marker="o", ms=4,
                     label="instant-cash share of household wealth (right)")
            ax2.set_ylabel("instant-cash share of wealth (%)", color=C.C_COOL)
            ax2.tick_params(axis="y", colors=C.C_COOL)
        ax1.axvline(pd.Timestamp("2022-02-24"), color="grey", ls="--", lw=1)
        ax1.set_title("Energy bills surged; the instant-cash cushion did not\n"
                      "euro-area households", fontweight="bold")
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")
        C.savefig(fig, "energy_vs_cash_buffer.png")

    # ---- (2) distribution: energy budget share vs saving capacity by quintile ----
    try:
        q = C.root_csv("saving_rate_by_quintile.csv")
        q = q[["q", "value"]].dropna().sort_values("q")
        q["energy_share"] = q["q"].map(ENERGY_BUDGET_SHARE)
        say("\nBy income quintile (Q1=poorest): energy budget share vs saving rate")
        say("  (energy share is illustrative/stylised — VERIFY against latest HBS)")
        for _, r in q.iterrows():
            say(f"  Q{int(r['q'])}: energy {r['energy_share']:4.1f}% of spending | "
                f"saving rate {r['value']:+5.1f}%")
        say("  => the poorest face the LARGEST non-deferrable energy share and the "
            "SMALLEST (often negative) buffer: most exposed to an energy shock, "
            "least able to self-insure with cash.")

        fig, ax1 = plt.subplots(figsize=(8.6, 5.0))
        ax2 = ax1.twinx()
        ax2.grid(False)
        x = q["q"].values
        ax1.bar(x - 0.18, q["energy_share"], width=0.36, color=C.C_HOT,
                label="energy share of spending (%)")
        ax2.bar(x + 0.18, q["value"], width=0.36, color=C.C_COOL,
                label="saving rate (%)")
        ax1.axhline(0, color="black", lw=0.8)
        ax2.axhline(0, color=C.C_COOL, ls=":", lw=1)
        ax1.set_xticks(x)
        ax1.set_xticklabels([f"Q{int(v)}" for v in x])
        ax1.set_xlabel("income quintile (Q1 = lowest)")
        ax1.set_ylabel("energy share of spending (%)", color=C.C_HOT)
        ax2.set_ylabel("household saving rate (%)", color=C.C_COOL)
        ax1.tick_params(axis="y", colors=C.C_HOT)
        ax2.tick_params(axis="y", colors=C.C_COOL)
        ax1.set_title("The energy squeeze is regressive\n"
                      "highest energy burden meets the thinnest buffer",
                      fontweight="bold")
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8.5, loc="upper center")
        C.savefig(fig, "energy_squeeze_by_income.png")
        q.to_csv(os.path.join(C.DATA, "energy_squeeze_by_income.csv"), index=False)
    except Exception as e:
        say(f"  distribution step failed: {e}")

    if cash_share is not None and energy is not None:
        merged = pd.concat(
            [energy.resample("YS").mean().rename(lambda d: d.year),
             cash_share.rename("cash_share")], axis=1)
        merged.to_csv(os.path.join(C.DATA, "energy_vs_cash_buffer.csv"))

    with open(os.path.join(C.DATA, "energy_liquidity.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'energy_liquidity.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
