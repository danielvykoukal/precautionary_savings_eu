#!/usr/bin/env python3
"""
Follow the money — where did the extra saving actually go?
=========================================================

The cleanest way to separate "saving out of fear" from "saving because it now
pays" is to follow the money. Fear keeps cash you can grab instantly. Chasing a
return moves money into things that pay more but tie it up — time deposits and,
above all, bonds.

So we split households' yearly financial saving (Eurostat nasa_10_f_tr, the
net acquisition of financial assets by households, euro-area aggregate) into:

  instant-access  (fear-consistent)  = currency (F21) + overnight deposits (F22)
  locked for yield (payoff-consistent) = time deposits (F29) + bonds (F3)

and watch how the split moved around 2022. A jump into bonds and time deposits
(and away from instant-access cash) after rates rose is the yield-chasing
fingerprint that precaution cannot produce.

Reads nothing from ../data (self-contained pull). Writes figures + a results md.
    python follow_the_money.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as cm

REPORT = []

# instrument -> plain-language label
INSTR = {
    "F21": "currency (cash)",
    "F22": "overnight deposits",
    "F29": "time / savings deposits",
    "F3":  "bonds (debt securities)",
}
TOPLEVEL = [f"F{i}" for i in range(1, 9)]   # F1..F8 for the denominator


def say(line=""):
    print(line)
    REPORT.append(str(line))


def get_household_flows():
    """tidy [year, na_item, value(EUR mn)] for euro-area household net
    acquisition of financial assets (shared helper in _common)."""
    long, geo = cm.household_flows()
    say(f"  using euro-area geo = {geo}")
    return long, geo


def build(long):
    """Return a per-year frame with EUR-bn flows for each instrument and the two
    buckets, plus each bucket's share of total financial saving."""
    piv = long.groupby(["year", "na_item"])["value"].sum().unstack("na_item")
    missing = [k for k in INSTR if k not in piv.columns]
    if missing:
        say(f"  note: instruments not found and skipped: {missing}")
    # total net acquisition of financial assets
    if "F" in piv.columns:
        total = piv["F"]
    elif "FA" in piv.columns:
        total = piv["FA"]
    else:
        total = piv[[c for c in TOPLEVEL if c in piv.columns]].sum(axis=1)

    out = pd.DataFrame(index=piv.index)
    for code in INSTR:
        out[code] = piv[code] if code in piv.columns else np.nan
    out["instant_access"] = out[[c for c in ("F21", "F22") if c in out]].sum(axis=1)
    out["locked_yield"] = out[[c for c in ("F29", "F3") if c in out]].sum(axis=1)
    out["total"] = total
    # shares of total saving flow (%)
    out["instant_share"] = 100 * out["instant_access"] / out["total"]
    out["yield_share"] = 100 * out["locked_yield"] / out["total"]
    out["bonds_share"] = 100 * out["F3"] / out["total"] if "F3" in out else np.nan
    out = out.reset_index()
    out["year"] = out["year"].astype(int)
    return out.sort_values("year")


def bn(x):
    return x / 1000.0   # EUR million -> EUR billion


def main():
    say("#" * 70)
    say("# Follow the money — where the extra household saving went")
    say("#" * 70)
    try:
        long, geo = get_household_flows()
        df = build(long)
    except Exception as e:
        say(f"\nFAILED: {e}")
        with open(os.path.join(cm.DATA, "follow_the_money.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    def avg(col, lo, hi):
        m = df[(df["year"] >= lo) & (df["year"] <= hi)][col]
        return float(m.mean()) if len(m) else float("nan")

    say("\nShare of households' yearly financial saving, by destination:")
    say(f"{'':<22}{'2015-19':>10}{'2022-25':>10}{'change':>9}")
    for label, col in (("instant-access (cash)", "instant_share"),
                       ("locked for yield", "yield_share"),
                       ("  of which bonds", "bonds_share")):
        pre, post = avg(col, 2015, 2019), avg(col, 2022, 2025)
        say(f"{label:<22}{pre:>9.1f}%{post:>9.1f}%{post-pre:>+8.1f}")

    say("\nMoney into bonds (EUR bn, net purchases per year):")
    for _, r in df[df["year"] >= 2019].iterrows():
        say(f"  {int(r['year'])}: {bn(r['F3']):>7.1f}")
    say("\nReading: a shift toward time deposits and especially BONDS after 2022,"
        " away from instant-access cash, is the yield-chasing fingerprint —"
        " precaution would do the opposite (pile into instant-access cash).")

    # ---------------- figure: two panels ----------------
    fig, (axT, axB) = plt.subplots(2, 1, figsize=(9.5, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1], "hspace": 0.18})
    # top: EUR-bn flows into the key destinations
    axT.axhline(0, color="black", lw=0.8)
    axT.plot(df["year"], bn(df["instant_access"]), color=cm.C_BLUE, lw=2.2,
             marker="o", ms=3, label="instant-access (cash + overnight)")
    if "F29" in df:
        axT.plot(df["year"], bn(df["F29"]), color=cm.C_ORANGE, lw=2.2,
                 marker="o", ms=3, label="time / savings deposits")
    if "F3" in df:
        axT.plot(df["year"], bn(df["F3"]), color=cm.C_RED, lw=2.6,
                 marker="o", ms=4, label="bonds")
    axT.axvline(2021.5, color="grey", ls="--", lw=1)
    axT.set_ylabel("net flow per year (EUR bn)")
    axT.set_title("Where euro-area households put their saving", fontweight="bold")
    axT.legend(frameon=False, fontsize=9, loc="upper left")

    # bottom: the two buckets as a share of total saving
    axB.plot(df["year"], df["instant_share"], color=cm.C_BLUE, lw=2.4, marker="o",
             ms=3, label="instant-access (fear-consistent)")
    axB.plot(df["year"], df["yield_share"], color=cm.C_RED, lw=2.4, marker="o",
             ms=3, label="locked for yield (payoff-consistent)")
    axB.axvline(2021.5, color="grey", ls="--", lw=1)
    axB.annotate("rates start rising\n(mid-2022)", xy=(2021.5, axB.get_ylim()[1]),
                 xytext=(2, -2), textcoords="offset points", ha="left", va="top",
                 fontsize=8, color="grey")
    axB.axhline(0, color="black", lw=0.8)
    axB.set_ylabel("share of yearly saving (%)")
    axB.set_xlabel("year")
    axB.legend(frameon=False, fontsize=9, loc="upper left")
    cm.savefig(fig, "follow_the_money.png")

    df.to_csv(os.path.join(cm.DATA, "follow_the_money.csv"), index=False)
    with open(os.path.join(cm.DATA, "follow_the_money.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extension_follow_money/data/follow_the_money.md")


if __name__ == "__main__":
    main()
