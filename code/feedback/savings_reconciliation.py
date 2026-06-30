#!/usr/bin/env python3
"""
Feedback #6 --- Why financial assets don't add up to the saving rate
====================================================================

The earlier sections track where households put their *financial* saving (the
liquidity ladder, follow-the-money). But the net acquisition of financial assets
is much SMALLER than gross saving, so "the assets" never sum to the saving rate.
Two channels close the gap, and the supervisors asked to see them explicitly:

  1. NON-FINANCIAL INVESTMENT (mainly HOUSING).  A large part of household saving
     buys dwellings, not financial claims. In the sector accounts this is gross
     capital formation P5G (≈ P51G fixed investment), which absorbs saving before
     anything reaches the financial account.
  2. BORROWING.  Households also take on debt (net incurrence of liabilities,
     above all F4 loans / mortgages). Borrowed funds let them acquire MORE
     financial assets than saving alone would allow, so borrowing ADDS to the
     financial-asset flow. This liability never appears on the asset ladder.

The ESA-2010 capital + financial identity for the household sector (S14_S15):

    B8G (gross saving) + D9net (capital transfers)
        = P5G (capital formation) + NP (non-produced assets) + B9 (net lending)
    B9  = F.ASS (net acq. financial assets) − F.LIAB (net borrowing)   [+ B9–B9F gap]

We first VALIDATE the build: computing the rate bottom-up as B8G / (B6G + D8net)
— the official Eurostat denominator, gross disposable income plus the adjustment
for the change in pension entitlements — reproduces the published series
(nasq_10_ki) to ~0.005 pp. So the component data really does add up to the
reported saving rate. The bridge from that rate to the financial-asset flow, all
as a % of the same (B6G + D8net) denominator, is:

    saving rate (B8G)
      − housing / non-financial investment (P5G, NP)
      + capital transfers received (D9net)
      + borrowing (F.LIAB)
      − statistical discrepancy (B9 − B9F)
      = financial assets acquired (F.ASS)

We pull the euro-area household accounts (Eurostat nasa_10_nf_tr + nasa_10_f_tr),
build the bridge per year, and plot (a) the waterfall for the recent period and
(b) the two missing pieces — borrowing and housing — over time.

    python savings_reconciliation.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []
TOPLEVEL = [f"F{i}" for i in range(1, 9)]


def say(line=""):
    print(line)
    REPORT.append(str(line))


# ----------------------------------------------------------------------------
# Non-financial sector accounts (nasa_10_nf_tr): households, euro-area, EUR mn
# ----------------------------------------------------------------------------
def nf_table():
    long = C.es_long("nasa_10_nf_tr")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
    geo = next((g for g in C.EA_GEOS if g in set(long["geo"])), None)
    unit = next((u for u in ("CP_MEUR", "CP_MNAC") if u in set(long["unit"])), None)
    if not (sec and geo and unit):
        raise RuntimeError(f"nasa_10_nf_tr: sector/geo/unit not found ({sec},{geo},{unit})")
    long = long[(long["sector"] == sec) & (long["geo"] == geo) & (long["unit"] == unit)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    return long, geo


def nf_series(nf, item, direction):
    """Year-indexed Series for one na_item on a chosen flow direction."""
    s = nf[(nf["na_item"] == item) & (nf["direct"] == direction)]
    return s.groupby("year")["value"].sum().rename(item)


# ----------------------------------------------------------------------------
# Financial accounts (nasa_10_f_tr): household assets / liabilities, EUR mn
# ----------------------------------------------------------------------------
def fin_table():
    long = C.es_long("nasa_10_f_tr")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
    geo = next((g for g in C.EA_GEOS if g in set(long["geo"])), None)
    if "co_nco" in long.columns and "NCO" in set(long["co_nco"]):
        long = long[long["co_nco"] == "NCO"]
    unit = next((u for u in ("MIO_EUR", "MIO_NAC") if u in set(long["unit"])), None)
    long = long[(long["sector"] == sec) & (long["geo"] == geo) & (long["unit"] == unit)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    return long, geo


def fin_total(fin, finpos):
    """Net acquisition (ASS) or net incurrence (LIAB): sum of F1..F8 per year."""
    s = fin[(fin["finpos"] == finpos) & (fin["na_item"].isin(TOPLEVEL))]
    return s.groupby("year")["value"].sum()


def fin_item(fin, finpos, item):
    s = fin[(fin["finpos"] == finpos) & (fin["na_item"] == item)]
    return s.groupby("year")["value"].sum()


def bn(x):
    return x / 1000.0


def main():
    say("#" * 74)
    say("# Saving-rate -> financial-assets bridge: housing & borrowing close the gap")
    say("#" * 74)

    nf, geo_nf = nf_table()
    fin, geo_f = fin_table()
    say(f"  non-financial geo = {geo_nf}, financial geo = {geo_f}")

    # capital account pieces (balancing items are duplicated PAID==RECV -> take RECV)
    B8G = nf_series(nf, "B8G", "RECV")          # gross saving
    B6G = nf_series(nf, "B6G", "RECV")          # gross disposable income
    B9 = nf_series(nf, "B9", "RECV")            # net lending(+)/borrowing(-)
    P5G = nf_series(nf, "P5G", "PAID")          # gross capital formation (housing-heavy)
    P51G = nf_series(nf, "P51G", "PAID")        # of which gross fixed capital formation
    NP = nf_series(nf, "NP", "PAID")            # non-produced non-financial assets
    P3 = nf_series(nf, "P3", "PAID")            # final consumption expenditure
    D9net = (nf_series(nf, "D9", "RECV") - nf_series(nf, "D9", "PAID")).rename("D9net")
    # D8 = adjustment for the change in pension entitlements. The OFFICIAL Eurostat
    # household saving rate divides by (B6G + D8net), not B6G alone — so we use the
    # same denominator and our computed rate matches the reported series.
    D8net = (nf_series(nf, "D8", "RECV") - nf_series(nf, "D8", "PAID")).rename("D8net")

    # financial account pieces
    F_ASS = fin_total(fin, "ASS").rename("F_ASS")     # net acquisition of fin. assets
    F_LIAB = fin_total(fin, "LIAB").rename("F_LIAB")  # net incurrence of liabilities = borrowing
    F4_LIAB = fin_item(fin, "LIAB", "F4").rename("F4_loans")  # of which loans/mortgages

    df = pd.concat([B8G, B6G, B9, P5G, P51G, NP, P3.rename("P3"), D9net, D8net,
                    F_ASS, F_LIAB, F4_LIAB],
                   axis=1).dropna(subset=["B8G", "B6G", "P5G", "F_ASS"])
    df.index.name = "year"
    # statistical discrepancy between the two measures of net lending
    df["B9F"] = df["F_ASS"] - df["F_LIAB"]
    df["discrep"] = df["B9"] - df["B9F"]
    # official denominator: gross disposable income + pension-entitlement adjustment
    df["denom"] = df["B6G"] + df["D8net"].fillna(0)
    df["saving_rate"] = 100 * df["B8G"] / df["denom"]

    # ---- verify the identity holds, then report ----
    df["check"] = (df["B8G"] - df["P5G"] - df["NP"] + df["D9net"]
                   + df["F_LIAB"] - df["discrep"])
    max_err = (df["check"] - df["F_ASS"]).abs().max()
    say(f"\nidentity max abs error across years: {max_err:,.0f} EUR mn (should be ~0)")

    # ---- VALIDATION: does our bottom-up rate reproduce the REPORTED saving rate? ----
    validate_against_reported(df)

    # ---- WHY did the saving rate move? income vs consumption + where it flowed ----
    decompose_episodes(df)

    say("\nHousehold capital + financial bridge (EUR bn, euro area):")
    say(f"{'year':>5}{'saving':>9}{'housing':>9}{'borrow':>9}{'fin.ass':>9}{'sav.rate':>9}")
    for y, r in df[df.index >= 2018].iterrows():
        say(f"{y:>5}{bn(r['B8G']):>9,.0f}{bn(r['P5G']):>9,.0f}{bn(r['F_LIAB']):>9,.0f}"
            f"{bn(r['F_ASS']):>9,.0f}{r['saving_rate']:>8.1f}%")

    say("\nHousehold BORROWING — net incurrence of liabilities (EUR bn/yr):")
    for y, r in df[df.index >= 2019].iterrows():
        say(f"  {y}: total {bn(r['F_LIAB']):>6.1f}   of which loans/mortgages (F4) "
            f"{bn(r['F4_loans']):>6.1f}")

    # ---- the bridge as a share of gross disposable income, recent period ----
    recent = df[df.index >= df.index.max() - 2]   # last 3 available years
    lo, hi = int(recent.index.min()), int(recent.index.max())
    g = lambda c: 100 * recent[c].sum() / recent["denom"].sum()   # % of denom, pooled
    bridge = {
        "Gross saving\n(saving rate)": g("B8G"),
        "− Housing &\nnon-fin. investment": -g("P5G") - g("NP"),
        "+ Capital\ntransfers (net)": g("D9net"),
        "+ Borrowing\n(liabilities)": g("F_LIAB"),
        "− Stat.\ndiscrepancy": -g("discrep"),
        "= Financial\nassets acquired": g("F_ASS"),
    }
    say(f"\nBridge as % of gross disposable income, pooled {lo}-{hi}:")
    for k, v in bridge.items():
        say(f"  {k.replace(chr(10),' '):<34}{v:>+7.1f}")

    plot_waterfall(bridge, lo, hi, geo_nf)
    plot_pieces_over_time(df, geo_nf)
    plot_decomposition_vs_saving(df, geo_nf)

    out = df.reset_index()
    keep = ["year", "saving_rate", "reported_rate", "B8G", "B6G", "D8net", "denom",
            "P3", "P5G", "P51G", "NP", "D9net", "B9", "F_ASS", "F_LIAB", "F4_loans",
            "B9F", "discrep"]
    out[keep].to_csv(os.path.join(C.DATA, "savings_reconciliation.csv"), index=False)
    with open(os.path.join(C.DATA, "savings_reconciliation.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'savings_reconciliation.csv'), C.ROOT)}")


EPISODES = [(2015, 2019, "2015-19 (pre-COVID)"),
            (2020, 2021, "2020-21 (COVID)"),
            (2022, 2025, "2022-25 (post-rate-shock)")]


def decompose_episodes(df):
    """Why did the saving rate move? Split each episode into (a) the income side —
    growth of disposable income vs consumption (the rate rises when consumption
    grows slower than income) — and (b) the uses side — where the extra saving
    flowed (financial assets / housing / borrowing, % of income)."""
    Y = df["denom"]                  # disposable income incl. pension adj.
    C = df["P3"]                     # consumption

    def avg(x, lo, hi):
        return x.loc[lo:hi].mean()

    def grw(x, lo, hi):
        return 100 * (x.loc[hi] / x.loc[lo] - 1) if lo in x.index and hi in x.index else float("nan")

    def share(col, lo, hi):
        return 100 * df.loc[lo:hi, col].sum() / Y.loc[lo:hi].sum()

    say("\n" + "=" * 64)
    say("WHY the saving rate moved — income side + where the saving flowed")
    say("=" * 64)
    say(f"{'period':<26}{'rate%':>7}{'disp.inc bn':>13}{'cons. bn':>11}")
    for lo, hi, nm in EPISODES:
        say(f"{nm:<26}{avg(df['saving_rate'], lo, hi):>6.1f} "
            f"{avg(Y, lo, hi)/1000:>12,.0f}{avg(C, lo, hi)/1000:>11,.0f}")

    say("\nIncome side — cumulative growth across the key transitions:")
    say(f"  2019 -> 2020 (COVID onset): disposable income {grw(Y,2019,2020):+.1f}%, "
        f"consumption {grw(C,2019,2020):+.1f}%  -> a CONSUMPTION collapse, not an income boom")
    say(f"  2019 -> 2023 (durable):     disposable income {grw(Y,2019,2023):+.1f}%, "
        f"consumption {grw(C,2019,2023):+.1f}%  -> nominal income outran consumption")

    say("\nUses side — where the saving flowed (% of disposable income, period sum):")
    say(f"{'':<28}{'2015-19':>9}{'2020-21':>9}{'2022-25':>9}")
    for col, lab in (("F_ASS", "financial assets"),
                     ("P5G", "housing / non-fin. inv."),
                     ("F_LIAB", "borrowing (liabilities)")):
        say(f"{lab:<28}{share(col,2015,2019):>9.1f}{share(col,2020,2021):>9.1f}"
            f"{share(col,2022,2025):>9.1f}")
    say("\nReading: the COVID spike was forced saving (consumption fell ~7%) parked in "
        "FINANCIAL ASSETS (7.5%->13.9% of income). The durable post-2022 step is "
        "income outrunning consumption WHILE borrowing fell (2.8%->1.9%): households "
        "saved a little more and levered up less, so the NET rate stayed high. Housing "
        "was steady throughout — it did not drive the increase.")
    plot_why(df)


def plot_why(df):
    """Two-panel: (top) saving rate with episode bands; (bottom) the three uses of
    saving as % of income, so the rise in the rate maps to where the money went."""
    Y = df["denom"]
    d = df[df.index >= 2002]
    fig, (axT, axB) = plt.subplots(2, 1, figsize=(10, 7.6), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1.15], "hspace": 0.12})
    axT.plot(d.index, d["saving_rate"], color="black", lw=2.6, marker="o", ms=3.5)
    axT.axhspan(0, 0, color="none")
    base = df.loc[2015:2019, "saving_rate"].mean()
    axT.axhline(base, color=C.C_GREY, ls=":", lw=1.4)
    axT.text(2002.2, base + 0.15, f"2015-19 avg {base:.1f}%", fontsize=8, color=C.C_GREY)
    for lo, hi, nm in EPISODES[1:]:
        axT.axvspan(lo - 0.5, hi + 0.5, color=C.C_ORANGE, alpha=0.08)
    axT.set_ylabel("household saving rate (%)")
    axT.set_title("Why the saving rate rose: a COVID consumption shock, then a\n"
                  "durable step as income outran spending and borrowing fell",
                  fontweight="bold")

    fa = 100 * d["F_ASS"] / Y.loc[d.index]
    house = 100 * d["P5G"] / Y.loc[d.index]
    borrow = 100 * d["F_LIAB"] / Y.loc[d.index]
    axB.plot(d.index, fa, color=C.C_COOL, lw=2.3, marker="o", ms=3, label="financial assets acquired")
    axB.plot(d.index, house, color=C.C_ORANGE, lw=2.3, marker="o", ms=3, label="housing / non-financial investment")
    axB.plot(d.index, borrow, color=C.C_HOT, lw=2.3, marker="o", ms=3, label="borrowing (net incurrence of liabilities)")
    for lo, hi, nm in EPISODES[1:]:
        axB.axvspan(lo - 0.5, hi + 0.5, color=C.C_ORANGE, alpha=0.08)
    axB.set_ylabel("% of disposable income")
    axB.set_xlabel("year")
    axB.legend(frameon=False, fontsize=9, loc="upper left")
    C.savefig(fig, "savings_reconciliation_why.png")


def validate_against_reported(df):
    """Compare our bottom-up saving rate to the REPORTED Eurostat series
    (../data/ea_saving_rate_quarterly.csv, nasq_10_ki), annual mean. Attaches a
    'reported_rate' column to df and prints the year-by-year match + error."""
    try:
        rep = C.annual_mean("ea_saving_rate_quarterly.csv", "reported")
    except Exception as e:
        say(f"\nvalidation skipped (reported series unavailable): {e}")
        df["reported_rate"] = np.nan
        return
    df["reported_rate"] = df.index.map(rep)
    cmp = df.dropna(subset=["reported_rate"])
    err = (cmp["saving_rate"] - cmp["reported_rate"]).abs()
    say("\nVALIDATION — can the component data reproduce the REPORTED saving rate?")
    say("  reported = Eurostat nasq_10_ki (annual mean of quarters); "
        "ours = B8G / (B6G + D8net)")
    say(f"{'year':>5}{'reported':>10}{'computed':>10}{'diff(pp)':>10}")
    for y, r in cmp[cmp.index >= 2015].iterrows():
        say(f"{y:>5}{r['reported_rate']:>9.2f}%{r['saving_rate']:>9.2f}%"
            f"{r['saving_rate']-r['reported_rate']:>+10.2f}")
    say(f"  mean abs error {err.mean():.3f} pp, max {err.max():.3f} pp "
        f"over {int(cmp.index.min())}-{int(cmp.index.max())} -> the bottom-up "
        f"build reproduces the headline rate.")
    plot_validation(cmp)


def plot_validation(cmp):
    """Reported vs computed saving rate over time — they should sit on top of each other."""
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(cmp.index, cmp["reported_rate"], color=C.C_GREY, lw=5.0, alpha=0.55,
            solid_capstyle="round", label="reported (Eurostat nasq_10_ki)")
    ax.plot(cmp.index, cmp["saving_rate"], color=C.C_MAIN, lw=1.8, marker="o", ms=3.5,
            label="computed from components: B8G / (B6G + D8)")
    ax.set_ylabel("household gross saving rate (%)")
    ax.set_xlabel("year")
    err = (cmp["saving_rate"] - cmp["reported_rate"]).abs().mean()
    ax.text(0.015, 0.04, f"mean abs error = {err:.3f} pp", transform=ax.transAxes,
            va="bottom", ha="left", fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=C.C_MAIN, alpha=0.9))
    ax.set_title("Our component data reproduces the reported saving rate\n"
                 "euro-area households: reported vs bottom-up reconstruction",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    C.savefig(fig, "savings_reconciliation_validation.png")


def plot_waterfall(bridge, lo, hi, geo):
    """Waterfall from the saving rate down to financial assets acquired (% of GDI)."""
    labels = list(bridge.keys())
    vals = list(bridge.values())
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axhline(0, color="black", lw=0.9)

    running = 0.0
    for i, (lab, v) in enumerate(zip(labels, vals)):
        is_total = lab.startswith("Gross") or lab.startswith("= ")
        if is_total:
            ax.bar(i, v, bottom=0, width=0.68, color=C.C_MAIN, alpha=0.95,
                   edgecolor="white", zorder=2)
            top = v
            running = v
        else:
            color = C.C_GREEN if v >= 0 else C.C_HOT
            ax.bar(i, v, bottom=running, width=0.68, color=color, alpha=0.9,
                   edgecolor="white", zorder=2)
            # connector
            ax.plot([i - 0.34, i - 0.66], [running, running], color="grey",
                    lw=0.8, ls="--", zorder=1)
            top = running + v
            running = top
        ax.text(i, top + (0.25 if v >= 0 else -0.25), f"{v:+.1f}", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=9, fontweight="bold")

    ax.set_ylim(0, max(vals) + 2.2)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("% of gross disposable income")
    ax.set_title("Why financial assets don't add up to the saving rate\n"
                 f"euro-area households, pooled {lo}-{hi} ({geo}): housing absorbs "
                 "saving, borrowing adds back", fontweight="bold")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C.C_MAIN, label="level (saving rate / financial assets)"),
                       Patch(color=C.C_HOT, label="absorbs saving (−)"),
                       Patch(color=C.C_GREEN, label="adds to financial assets (+)")],
              loc="upper right", frameon=False, fontsize=9)
    C.savefig(fig, "savings_reconciliation_waterfall.png")


def plot_decomposition_vs_saving(df, geo):
    """Decompose the saving rate over time (% of GDI) into where it goes, with the
    saving rate itself as a line. Stacks sum to the line by the ESA identity:
        saving rate = financial assets + housing/non-fin. inv. + other − borrowing
    Borrowing is a SOURCE of funds, so it sits below zero (it lets households hold
    more financial assets than own saving alone)."""
    d = df[df.index >= 2002].copy()
    den = d["denom"]                            # B6G + D8net (official denominator)
    fa = 100 * d["F_ASS"] / den
    house = 100 * (d["P5G"] + d["NP"]) / den
    other = 100 * (-d["D9net"] + d["discrep"]) / den
    borrow = -100 * d["F_LIAB"] / den          # negative: a source, not a use
    yrs = d.index.values

    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.axhline(0, color="black", lw=0.9)

    # positive stack (uses of funds)
    ax.bar(yrs, fa, width=0.8, color=C.C_COOL, label="financial assets acquired (the ladder)",
           edgecolor="white", linewidth=0.3, zorder=2)
    ax.bar(yrs, house, bottom=fa, width=0.8, color=C.C_ORANGE,
           label="housing & non-financial investment", edgecolor="white",
           linewidth=0.3, zorder=2)
    pos_top = fa + house
    ax.bar(yrs, other, bottom=pos_top, width=0.8, color=C.C_GREY,
           label="other (capital transfers, discrepancy)", edgecolor="white",
           linewidth=0.3, alpha=0.8, zorder=2)

    # borrowing below zero (a source of funds)
    ax.bar(yrs, borrow, width=0.8, color=C.C_HOT,
           label="− borrowing (net incurrence of liabilities)", edgecolor="white",
           linewidth=0.3, zorder=2)

    # the saving rate = algebraic sum of the stack; overlay the REPORTED series to
    # show the bottom-up bars net to the published rate
    if "reported_rate" in d and d["reported_rate"].notna().any():
        ax.plot(yrs, d["reported_rate"], color=C.C_GREY, lw=5.0, alpha=0.5,
                solid_capstyle="round", zorder=4, label="reported saving rate (Eurostat)")
    ax.plot(yrs, d["saving_rate"], color="black", lw=2.4, marker="o", ms=4,
            zorder=5, label="saving rate = net of the stack (computed)")

    ax.axvline(2021.5, color="grey", ls="--", lw=1, zorder=1)
    ax.set_ylabel("% of gross disposable income")
    ax.set_xlabel("year")
    ax.set_title("The saving rate, decomposed: housing absorbs it, borrowing funds it\n"
                 f"euro-area households ({geo}) — bars net to the saving-rate line",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncol=2)
    C.savefig(fig, "savings_reconciliation_decomposition.png")


def plot_pieces_over_time(df, geo):
    """The two missing pieces over time: housing investment and borrowing (EUR bn)."""
    d = df[df.index >= 1999]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.axhline(0, color="black", lw=0.8)
    ax.plot(d.index, bn(d["P5G"]), color=C.C_ORANGE, lw=2.4, marker="o", ms=3,
            label="non-financial investment (P5G, housing-heavy)")
    ax.plot(d.index, bn(d["F_LIAB"]), color=C.C_HOT, lw=2.4, marker="o", ms=3,
            label="borrowing — net incurrence of liabilities")
    ax.plot(d.index, bn(d["F4_loans"]), color=C.C_ACCENT, lw=1.8, ls="--",
            marker="o", ms=2.5, label="   of which loans / mortgages (F4)")
    ax.plot(d.index, bn(d["F_ASS"]), color=C.C_COOL, lw=2.4, marker="o", ms=3,
            label="net acquisition of financial assets")
    ax.axvline(2021.5, color="grey", ls="--", lw=1)
    ax.set_ylabel("EUR bn / yr")
    ax.set_xlabel("year")
    ax.set_title("The two pieces missing from the asset ladder\n"
                 f"euro-area households ({geo}): housing absorbs saving, borrowing "
                 "is a liability, not an asset", fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    C.savefig(fig, "savings_reconciliation_pieces.png")


if __name__ == "__main__":
    main()
