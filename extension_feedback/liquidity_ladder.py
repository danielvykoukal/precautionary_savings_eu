#!/usr/bin/env python3
"""
Feedback #1 --- Asset types by TERM & LIQUIDITY: the liquidity ladder
=====================================================================

Supervisor feedback: "look more into each asset type; divide assets by term;
many assets can be sold fast, so we can't treat only cash & deposits as the only
precautionary savings."

The existing extension_follow_money/ used a BINARY split — instant-access cash
(F21+F22) vs "locked for yield" (F29+F3) — and read the post-2022 move into bonds
& term deposits as yield-chasing, NOT precaution. That binary is exactly what the
feedback targets: bonds, listed shares and fund shares are *sellable in days*, so
calling them "locked / not precautionary" is too strong.

So we replace the binary with a four-rung LIQUIDITY / MATURITY ladder (ESA 2010
instrument codes), and we compute it on BOTH:
  - STOCKS  (nasa_10_f_bs)  -> the standing liquidity composition of household
    financial wealth: how much of what households *hold* is actually liquid;
  - FLOWS   (nasa_10_f_tr)  -> where the marginal saving went, re-read on the
    ladder rather than the old binary.

Ladder
------
  T1 instant / settlement (~ M1)        : F21 currency + F22 overnight deposits
  T2 near-money, short term/notice (~M2/M3): F29 other deposits + F521 MMF shares
  T3 marketable, sellable-fast (price risk): F3 bonds + F511 listed shares
                                             + F522 non-MMF investment-fund shares
  T4 illiquid / contractual / long-term : F512/F519 unlisted & other equity
                                             + F6 insurance, pension & guarantees

The headline the feedback asks for: the NARROW "cash" share (T1) vs the BROAD
"sellable-fast" share (T1+T2+T3). If a large slice of household wealth is liquid
beyond cash, then "out of cash = not precautionary" no longer follows.

Eurostat does not always publish the F5 children (F511/F512/F519/F521/F522). The
classifier auto-detects what is present and falls back conservatively (an
un-splittable equity/funds block is treated as ILLIQUID, making the broad-liquid
share a LOWER bound — we never overstate liquidity). The chosen mapping + any
fallback is printed and written to the report.

    python liquidity_ladder.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []

TIER_LABELS = ["T1 instant (cash, overnight)",
               "T2 near-money (term/notice, MMF)",
               "T3 marketable (bonds, listed shares, funds)",
               "T4 illiquid (unlisted equity, insurance/pension)"]
TIER_COLORS = [C.C_COOL, C.C_GREEN, C.C_ORANGE, C.C_HOT]


def say(line=""):
    print(line)
    REPORT.append(str(line))


def _col(piv, code):
    """piv[code] if present, else a zero Series aligned to the index."""
    if code in piv.columns:
        return piv[code].fillna(0.0)
    return pd.Series(0.0, index=piv.index)


def build_tiers(long):
    """long [year, na_item, value] -> per-year frame with T1..T4 (EUR mn), the
    total, and each tier's share of total. Returns (frame, notes)."""
    piv = long.groupby(["year", "na_item"])["value"].sum().unstack("na_item").sort_index()
    cols = set(piv.columns)
    notes = []

    # denominator: total financial assets / total net acquisition
    toplevel = [f"F{i}" for i in range(1, 9)]
    if "F" in cols:
        total = piv["F"]
    elif "FA" in cols:
        total = piv["FA"]
    else:
        total = piv[[c for c in toplevel if c in cols]].sum(axis=1)

    # MMF shares (near-money) if separable
    mmf = _col(piv, "F521") if "F521" in cols else pd.Series(0.0, index=piv.index)
    if "F521" not in cols:
        notes.append("F521 (MMF shares) not separately published -> not split out of funds")

    # marketable fund shares (non-MMF)
    if "F522" in cols:
        nonmmf_funds = _col(piv, "F522")
    elif "F52" in cols:
        nonmmf_funds = _col(piv, "F52") - mmf       # F52 minus MMF (mmf may be 0)
        if "F521" not in cols:
            notes.append("F52 used whole as marketable funds (MMF not separable)")
    else:
        nonmmf_funds = pd.Series(0.0, index=piv.index)

    listed = _col(piv, "F511")

    # illiquid equity: prefer the unlisted/other children; else back out of F51;
    # else treat the whole equity/funds block as illiquid (a conservative LOWER
    # bound on the liquid share).
    if ("F512" in cols) or ("F519" in cols):
        illiquid_eq = _col(piv, "F512") + _col(piv, "F519")
    elif ("F51" in cols) and ("F511" in cols):
        illiquid_eq = _col(piv, "F51") - listed
    elif "F51" in cols:
        illiquid_eq = _col(piv, "F51")
        notes.append("F51 (all equity) treated illiquid: bundles listed shares -> broad-liquid share is a LOWER bound")
    elif ("F5" in cols) and ("F52" not in cols):
        illiquid_eq = _col(piv, "F5")
        notes.append("only combined F5 available: equity & funds treated illiquid -> broad-liquid share is a LOWER bound")
    else:
        illiquid_eq = pd.Series(0.0, index=piv.index)

    out = pd.DataFrame(index=piv.index)
    out["T1"] = _col(piv, "F21") + _col(piv, "F22")
    out["T2"] = _col(piv, "F29") + mmf
    out["T3"] = _col(piv, "F3") + listed + nonmmf_funds
    out["T4"] = illiquid_eq + _col(piv, "F6")
    out["total"] = total
    # drop years without a usable denominator: deposits (F2x) run back to the
    # 1990s but the total financial assets (F) and the bond/equity detail only
    # start ~2001, so the earlier shares are NaN (and a NaN-skipping sum would
    # plot a spurious zero-then-jump in the liquid-share line).
    out = out[out["total"].notna() & (out["total"] > 0)]
    for t in ("T1", "T2", "T3", "T4"):
        out[f"{t}_share"] = 100 * out[t] / out["total"]
    out["narrow_cash_share"] = out["T1_share"]
    out["broad_liquid_share"] = out[["T1_share", "T2_share", "T3_share"]].sum(axis=1)
    out = out.reset_index()
    out["year"] = out["year"].astype(int)
    return out.sort_values("year"), notes


def _avg(df, col, lo, hi):
    m = df[(df["year"] >= lo) & (df["year"] <= hi)][col]
    return float(m.mean()) if len(m) else float("nan")


def report_block(tag, df, notes):
    say(f"\n### {tag}")
    for n in notes:
        say(f"  note: {n}")
    say(f"{'':<26}{'2015-19':>10}{'2022+':>10}{'change':>9}")
    rows = [("T1 instant (cash)", "T1_share"),
            ("T2 near-money", "T2_share"),
            ("T3 marketable", "T3_share"),
            ("T4 illiquid", "T4_share"),
            ("-> narrow cash (T1)", "narrow_cash_share"),
            ("-> broad sellable-fast", "broad_liquid_share")]
    for label, col in rows:
        pre, post = _avg(df, col, 2015, 2019), _avg(df, col, 2022, 2099)
        say(f"{label:<26}{pre:>9.1f}%{post:>9.1f}%{post-pre:>+8.1f}")


def plot_stocks(df, geo):
    """Stacked tier shares of household financial wealth, with the broad-liquid line."""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    shares = [df[f"T{i}_share"].values for i in range(1, 5)]
    ax.stackplot(df["year"], *shares, labels=TIER_LABELS, colors=TIER_COLORS, alpha=0.88)
    ax.plot(df["year"], df["broad_liquid_share"], color="black", lw=2.2, ls="--",
            label="broad sellable-fast (T1+T2+T3)")
    ax.axvline(2021.5, color="grey", ls=":", lw=1)
    ax.set_ylim(0, 100)
    ax.set_ylabel("share of household financial assets (%)")
    ax.set_xlabel("year")
    ax.set_title(f"What households actually hold, ranked by liquidity\n"
                 f"euro-area household financial wealth by tier ({geo}, stocks)",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
    C.savefig(fig, "liquidity_ladder_stocks.png")


def plot_flows(df, geo):
    """Net flow into each tier (EUR bn) over time — the post-2022 reframe."""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.axhline(0, color="black", lw=0.9)
    for i, (lab, color) in enumerate(zip(TIER_LABELS, TIER_COLORS), start=1):
        ax.plot(df["year"], df[f"T{i}"] / 1000.0, color=color, lw=2.3, marker="o",
                ms=3, label=lab)
    ax.axvline(2021.5, color="grey", ls="--", lw=1)
    ax.text(2021.4, ax.get_ylim()[1] * 0.96, "ECB hiking\nbegins (2022)",
            fontsize=8, color="grey", va="top", ha="right")
    ax.set_ylabel("net flow into the tier (EUR bn / yr)")
    ax.set_xlabel("year")
    ax.set_title(f"Where the marginal saving went, re-read on the ladder\n"
                 f"euro-area household net financial flows by liquidity tier ({geo})",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    C.savefig(fig, "liquidity_ladder_flows.png")


def main():
    say("#" * 72)
    say("# Liquidity ladder — household assets by term & liquidity")
    say("#" * 72)
    say("Tiers: T1 instant (F21,F22) | T2 near-money (F29,F521) | "
        "T3 marketable (F3,F511,F522) | T4 illiquid (F512/F519,F6)")

    results = {}

    # ---- STOCKS: the standing liquidity composition of household wealth ----
    say("\n## STOCKS — household financial balance sheet (nasa_10_f_bs)")
    try:
        long_s, geo_s = C.household_instruments("nasa_10_f_bs")
        stocks, notes_s = build_tiers(long_s)
        report_block("Stock shares of household financial wealth", stocks, notes_s)
        latest = stocks.iloc[-1]
        say(f"\nLatest ({int(latest['year'])}): of household financial wealth, only "
            f"{latest['narrow_cash_share']:.0f}% is instant cash, but "
            f"{latest['broad_liquid_share']:.0f}% is sellable within days "
            f"(T1+T2+T3). The 'precautionary buffer' is far bigger than cash.")
        plot_stocks(stocks, geo_s)
        stocks.to_csv(os.path.join(C.DATA, "liquidity_ladder_stocks.csv"), index=False)
        results["stocks"] = True
    except Exception as e:
        say(f"  STOCKS step failed: {e}")

    # ---- FLOWS: re-read the post-2022 reallocation on the ladder ----
    say("\n## FLOWS — household net acquisition of financial assets (nasa_10_f_tr)")
    try:
        long_f, geo_f = C.household_instruments("nasa_10_f_tr")
        flows, notes_f = build_tiers(long_f)
        report_block("Flow shares of yearly financial saving", flows, notes_f)
        say("\nReframe: the post-2022 shift into T3 (bonds, listed shares, funds) is a "
            "move into assets that are still SELLABLE FAST. On the ladder it is not "
            "'leaving the precautionary buffer' — it is moving up the risk/return "
            "scale while staying liquid. The old cash-only binary missed this.")
        plot_flows(flows, geo_f)
        flows.to_csv(os.path.join(C.DATA, "liquidity_ladder_flows.csv"), index=False)
        results["flows"] = True
    except Exception as e:
        say(f"  FLOWS step failed: {e}")

    with open(os.path.join(C.DATA, "liquidity_ladder.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'liquidity_ladder.md'), C.ROOT)}")
    if not results:
        print("Both steps failed — inspect the printed dataset dimensions above.")


if __name__ == "__main__":
    main()
