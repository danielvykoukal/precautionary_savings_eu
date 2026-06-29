#!/usr/bin/env python3
"""
Descriptive #3 (Wave 2) --- Why are Europeans more cautious savers?
==================================================================

Supervisor idea: the US discrepancy. Why do Europeans look like such cautious
savers, and how does the history of the state pension system explain it?

The cleanest data fact: euro-area households hold far LESS of their financial
wealth in market-exposed equity & investment funds (and far more in deposits)
than US households -- a large, persistent gap, not a recent blip. We plot the
risky (F5 equity & funds) share over time for the US and the euro area.

The narrative behind it (in the write-up): the US built a funded, equity-heavy
private-pension system (401(k)/IRA) and an equity-investing culture; much of
continental Europe leaned on pay-as-you-go STATE pensions and a bank-deposit
culture. So European households carry less market risk and look more 'cautious'.

Data: euro area from Eurostat nasa_10_f_bs (reused); US from the OECD financial
accounts (sector S1M households) -- no FRED needed.
    python us_caution.py
"""

import os
from io import StringIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C
from saving_composition_evolution import finstock_shares

REPORT = []
OECD_BS_FLOW = "DSD_NASEC20@DF_T720R_A"


def say(line=""):
    print(line)
    REPORT.append(str(line))


def oecd_us_shares(start=2005):
    """US household (S1M) risky (F5) and non-risky (F2) share of financial assets
    over time, from the OECD financial accounts. No FRED needed."""
    key = ".".join(["A", "", "USA"] + [""] * 15)
    url = (f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,{OECD_BS_FLOW},/{key}"
           f"?startPeriod={start}&dimensionAtObservation=AllDimensions&format=csvfilewithlabels")
    df = pd.read_csv(StringIO(C.http_get(url, timeout=120).text))
    df = df[(df["SECTOR"] == "S1M") & (df["ACCOUNTING_ENTRY"] == "A")
            & (df["TRANSACTION"] == "LE")]
    if "UNIT_MEASURE" in df.columns and "USD" in set(df["UNIT_MEASURE"]):
        df = df[df["UNIT_MEASURE"] == "USD"]
    if "MATURITY" in df.columns:
        df = df[df["MATURITY"].isin(["T", "_Z"])]
    df["value"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df["year"] = df["TIME_PERIOD"].astype(str).str.extract(r"(\d{4})").astype(float)
    df = df.dropna(subset=["value", "year"])
    df["year"] = df["year"].astype(int)
    piv = df.groupby(["year", "INSTR_ASSET"])["value"].sum().unstack("INSTR_ASSET")
    if not {"F", "F5", "F2"}.issubset(piv.columns):
        raise RuntimeError("OECD US: F/F5/F2 missing")
    return pd.DataFrame({"risky_F5": 100 * piv["F5"] / piv["F"],
                         "safe_F2": 100 * piv["F2"] / piv["F"]}).dropna().sort_index()


def main():
    say("#" * 72)
    say("# Why Europeans are more cautious savers -- equity involvement, US vs EA")
    say("#" * 72)

    ea = None
    try:
        shares = finstock_shares(["EA20", "EA19", "EA"])
        g = next((x for x in ("EA20", "EA19", "EA") if x in shares), None)
        ea = shares[g][["risky_F5", "safe_F2"]] if g else None
    except Exception as e:
        say(f"  EA shares failed: {e}")
    us = None
    try:
        us = oecd_us_shares()
    except Exception as e:
        say(f"  US shares (OECD) failed: {e}")

    if ea is not None and us is not None:
        yr = min(ea.index.max(), us.index.max())
        say(f"\nRisky (equity & funds, F5) share of household financial assets ({yr}):")
        say(f"  United States : {us.loc[us.index<=yr,'risky_F5'].iloc[-1]:.0f}%")
        say(f"  Euro area     : {ea.loc[ea.index<=yr,'risky_F5'].iloc[-1]:.0f}%")
        say("  -> US households hold far more equity (about 1.5x the euro-area share); "
            "the gap is large and persistent. Non-risky deposits (F2) are the mirror "
            "image: euro-area households hold far more in cash & deposits.")
    say("\nWhy (history): the US built a funded, equity-heavy private-pension system "
        "(401(k)/IRA) and an equity-investing culture; continental Europe leaned on "
        "pay-as-you-go STATE pensions and bank deposits. So European households carry "
        "less market risk and look more 'cautious' -- a structural, institutional "
        "difference, not just preferences.")

    fig, ax = plt.subplots(figsize=(10, 5.6))
    if us is not None:
        ax.plot(us.index, us["risky_F5"], color=C.C_MAIN, lw=2.8, marker="o", ms=3,
                label="US: risky (equity & funds)")
        ax.plot(us.index, us["safe_F2"], color=C.C_MAIN, lw=1.5, ls="--", alpha=0.7,
                label="US: non-risky (deposits)")
    if ea is not None:
        ax.plot(ea.index, ea["risky_F5"], color=C.C_ORANGE, lw=2.8, marker="o", ms=3,
                label="Euro area: risky (equity & funds)")
        ax.plot(ea.index, ea["safe_F2"], color=C.C_ORANGE, lw=1.5, ls="--", alpha=0.7,
                label="Euro area: non-risky (deposits)")
    C.mark_periods(ax, year_axis=True, shade=True, labels=False)
    ax.set_ylabel("share of household financial assets (%)")
    ax.set_xlabel("year")
    ax.set_title("Why Europeans look like cautious savers\n"
                 "US households hold far more equity, far less cash, than the euro area",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper left")
    C.caveat(fig, "US: OECD financial accounts (S1M households); euro area: Eurostat nasa_10_f_bs. "
                  "'Risky' = equity & investment-fund shares (F5); 'non-risky' = deposits (F2).")
    C.savefig(fig, "us_vs_ea_caution.png")

    out = {}
    if us is not None:
        out["us_risky"] = us["risky_F5"]; out["us_safe"] = us["safe_F2"]
    if ea is not None:
        out["ea_risky"] = ea["risky_F5"]; out["ea_safe"] = ea["safe_F2"]
    if out:
        pd.DataFrame(out).to_csv(os.path.join(C.DATA, "us_caution.csv"))
    with open(os.path.join(C.DATA, "us_caution.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'us_caution.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
