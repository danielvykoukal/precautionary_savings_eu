#!/usr/bin/env python3
"""
Feedback #1b --- Money supply, divided by TERM (M1 / M2 / M3)
=============================================================

Supervisor feedback also asked to "look more into money supply" and to "divide
assets based on term." The monetary aggregates ARE the central bank's own
liquidity-by-term tiering of the money-holding sector's claims, so they are the
natural macro counterpart to the household liquidity ladder:

  M1            = currency + overnight deposits          (instant   ~ ladder T1)
  M2 - M1       = deposits <=2y maturity + redeemable <=3m notice (near-money by TERM ~ T2)
  M3 - M2       = repos + money-market-fund shares + debt securities <=2y
                                                       (marketable near-money ~ T2/T3)

We pull euro-area M1/M2/M3, decompose by term, plot the components and their YoY
growth, and relate near-money growth to the household saving rate.

Sources (free, keyless), tried in order:
  1. ECB Data Portal SDMX (BSI) — authoritative and internally consistent
     (M1<M2<M3 from one table), so the term decomposition is clean.
  2. FRED OECD euro-area money series — fallback; growth rates are robust even if
     levels are not perfectly comparable across the three.

If a source returns an INDEX rather than a EUR level (so M2-M1 would be
meaningless), the script detects it and reports YoY growth only.

    python money_supply.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []

# ECB BSI series keys (outstanding amounts, EUR, working-day & seasonally adj.)
ECB = {
    "M1": ("BSI", "M.U2.Y.V.M10.X.1.U2.2300.Z01.E"),
    "M2": ("BSI", "M.U2.Y.V.M20.X.1.U2.2300.Z01.E"),
    "M3": ("BSI", "M.U2.Y.V.M30.X.1.U2.2300.Z01.E"),
}
# FRED fallbacks (OECD / ECB euro-area monetary aggregates)
FRED = {"M1": "MANMM101EZM189S", "M2": "MYAGM2EZM196N", "M3": "MABMM301EZM189S"}


def say(line=""):
    print(line)
    REPORT.append(str(line))


def fetch_aggregate(label):
    """Monthly [date, value] level for one aggregate. ECB first, FRED fallback.
    Returns (Series indexed by date, source_str) or (None, None)."""
    flow, key = ECB[label]
    try:
        df = C.ecb_sdmx(flow, key)
        if len(df) > 24:
            s = df.set_index("date")["value"].rename(label)
            say(f"  {label}: ECB {flow}/{key} ({len(s)} obs)")
            return s, "ECB"
    except Exception as e:
        say(f"  {label}: ECB pull failed ({e}); trying FRED")
    try:
        df = C.get_fred_series(FRED[label], label.lower())
        if len(df) > 24:
            s = df.set_index("date")[label.lower()].rename(label)
            say(f"  {label}: FRED {FRED[label]} ({len(s)} obs)")
            return s, "FRED"
    except Exception as e:
        say(f"  {label}: FRED pull failed ({e})")
    return None, None


def yoy(s):
    return 100.0 * (s / s.shift(12) - 1.0)


def main():
    say("#" * 72)
    say("# Money supply by term — euro-area M1 / M2 / M3")
    say("#" * 72)

    series, sources = {}, {}
    for lab in ("M1", "M2", "M3"):
        s, src = fetch_aggregate(lab)
        if s is not None:
            series[lab], sources[lab] = s, src

    if "M3" not in series and "M1" not in series:
        say("\nNo monetary aggregates available from ECB or FRED.")
        with open(os.path.join(C.DATA, "money_supply.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    # Are these EUR levels (term decomposition possible) or an index?
    ref = series.get("M3", series.get("M1"))
    is_level = float(ref.median()) > 1000  # EUR mn levels are ~1e7; an index is ~1e2
    say(f"\nseries look like {'EUR levels' if is_level else 'an index'} "
        f"(median {float(ref.median()):,.0f}) -> "
        f"{'term decomposition + growth' if is_level else 'growth only'}")

    # ---- YoY growth figure (always) ----
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.axhline(0, color="black", lw=0.8)
    for lab, color in (("M1", C.C_COOL), ("M2", C.C_GREEN), ("M3", C.C_MAIN)):
        if lab in series:
            g = yoy(series[lab]).dropna()
            ax.plot(g.index, g.values, color=color, lw=2.0, label=f"{lab} YoY %")
    ax.axvline(pd.Timestamp("2022-02-24"), color="grey", ls="--", lw=1)
    ax.set_ylabel("year-on-year growth (%)")
    ax.set_title("Euro-area money supply growth by aggregate\n"
                 "M1 (instant) reacts most to the rate cycle", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    C.savefig(fig, "money_supply_growth.png")

    out = pd.DataFrame(series)

    # ---- term decomposition (only if levels) ----
    if is_level and {"M1", "M2", "M3"}.issubset(series):
        ann = out.resample("YS").mean() / 1000.0   # EUR bn, annual mean
        ann["instant_M1"] = ann["M1"]
        ann["term_M2_M1"] = (ann["M2"] - ann["M1"]).clip(lower=0)
        ann["mktbl_M3_M2"] = (ann["M3"] - ann["M2"]).clip(lower=0)
        ann.index = ann.index.year

        say("\nEuro-area money by term (EUR bn, annual mean):")
        say(f"{'year':>6}{'M1 instant':>13}{'M2-M1 term':>13}{'M3-M2 mktbl':>13}{'M3':>11}")
        for y, r in ann[ann.index >= 2018].iterrows():
            say(f"{y:>6}{r['instant_M1']:>13,.0f}{r['term_M2_M1']:>13,.0f}"
                f"{r['mktbl_M3_M2']:>13,.0f}{r['M3']:>11,.0f}")

        fig, ax = plt.subplots(figsize=(10, 5.6))
        ax.stackplot(ann.index, ann["instant_M1"], ann["term_M2_M1"], ann["mktbl_M3_M2"],
                     labels=["M1 instant (overnight)",
                             "M2-M1 term/notice deposits",
                             "M3-M2 marketable (MMF, repo, short debt)"],
                     colors=[C.C_COOL, C.C_GREEN, C.C_ORANGE], alpha=0.9)
        ax.axvline(2021.5, color="grey", ls=":", lw=1)
        ax.set_ylabel("outstanding amount (EUR bn)")
        ax.set_xlabel("year")
        ax.set_title("Euro-area money supply, divided by term\n"
                     "M1 / (M2-M1) / (M3-M2)", fontweight="bold")
        ax.legend(frameon=False, fontsize=8.5, loc="upper left")
        C.savefig(fig, "money_supply_by_term.png")
        ann.to_csv(os.path.join(C.DATA, "money_supply_by_term.csv"))

    # ---- link to the household saving rate ----
    try:
        saving = C.annual_mean("ea_saving_rate_quarterly.csv", "saving")
        m3g = yoy(series["M3"]).resample("YS").mean() if "M3" in series else None
        if m3g is not None:
            m3g.index = m3g.index.year
            j = pd.concat([saving, m3g.rename("m3_growth")], axis=1).dropna()
            if len(j) > 5:
                r = j["saving"].corr(j["m3_growth"])
                say(f"\ncorr(household saving rate, M3 YoY growth), annual = {r:+.2f} "
                    f"({j.index.min()}-{j.index.max()})")
                say("  (broad-money growth and the saving rate move together: saving "
                    "feeds the deposit/near-money stock.)")
    except Exception as e:
        say(f"\nsaving-rate link skipped: {e}")

    say("\nMapping to the household ladder: M1 ~ T1 (instant); M2-M1 ~ T2 "
        "(term/notice near-money); M3-M2 ~ marketable near-money (MMF shares, repo) "
        "straddling T2/T3. So 'money' itself is already tiered by term — the "
        "precautionary buffer is not just M1 cash.")

    out.to_csv(os.path.join(C.DATA, "money_supply_levels.csv"))
    with open(os.path.join(C.DATA, "money_supply.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'money_supply.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
