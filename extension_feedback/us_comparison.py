#!/usr/bin/env python3
"""
US comparison --- the same liquidity ladder, United States vs euro area
=======================================================================

Supervisor feedback: look at the same thing in the US for comparison.

We rebuild the household liquidity ladder for the United States from the Federal
Reserve Financial Accounts (Z.1), households & nonprofit organisations (HNO),
and set it against the euro-area ladder from `liquidity_ladder.py`. We also
contrast the saving rate (US personal saving rate vs the euro-area household
saving rate). The story to test: US households hold far less in cash/deposits and
far more in marketable equities & funds than euro-area households, so their
"buffer" is even more sellable-fast (but more exposed to market price risk).

Data: FRED (Z.1 HNO levels, $bn; US personal saving rate PSAVERT). This is
FRED-sourced, so run it where FRED is reachable. **US Z.1 series ids are
best-effort**: each component lists candidate ids and the script uses the first
that resolves, printing a resolved/unresolved table — replace any unresolved id
from fred.stlouisfed.org (search "Households; <concept>; Asset, Level"). Shares
are computed against TOTAL financial assets, so a component that fails to resolve
shows up as an unclassified residual rather than inflating the liquid share.

    python us_comparison.py        # needs FRED
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []

# Total financial assets of households & nonprofits (the denominator).
US_TOTAL = ["TFAABSHNO", "BOGZ1FL152000005Q"]

# (tier, concept label, [candidate FRED ids]); first id that resolves is used.
US_COMPONENTS = [
    ("T1", "checkable deposits & currency", ["CDCABSHNO", "BOGZ1FL153020005Q"]),
    ("T2", "time & savings deposits",        ["TSDABSHNO", "BOGZ1FL153030005Q"]),
    ("T2", "money-market fund shares",       ["MMFSABSHNO", "BOGZ1FL153034005Q"]),
    ("T3", "debt securities",                ["BOGZ1FL154022005Q", "CMABSHNO"]),
    ("T3", "corporate equities",             ["BOGZ1FL153064105Q"]),
    ("T3", "mutual fund shares",             ["BOGZ1FL153064205Q", "MFSABSHNO"]),
    ("T4", "equity in noncorporate business",["BOGZ1FL152090205Q"]),
    ("T4", "pension entitlements",           ["BOGZ1FL574090005Q", "BOGZ1FL153050005Q"]),
    ("T4", "life insurance reserves",        ["BOGZ1FL543040005Q", "BOGZ1FL153040005Q"]),
]
TIERS = ["T1", "T2", "T3", "T4"]
TIER_LABELS = {"T1": "T1 instant", "T2": "T2 near-money",
               "T3": "T3 marketable", "T4": "T4 illiquid"}
TIER_COLORS = {"T1": C.C_COOL, "T2": C.C_GREEN, "T3": C.C_ORANGE, "T4": C.C_HOT}


def say(line=""):
    print(line)
    REPORT.append(str(line))


def _first_resolving(ids, name):
    """Return the quarterly Series for the first FRED id that resolves, else None."""
    for sid in ids:
        try:
            df = C.get_fred_series(sid, "v")
            s = df.set_index("date")["v"].resample("QS").mean()
            if len(s) > 8:
                return s, sid
        except Exception:
            continue
    say(f"  UNRESOLVED: {name} (tried {ids}) — replace from fred.stlouisfed.org")
    return None, None


def us_tier_shares():
    """Build US household tier shares of total financial assets (latest year)."""
    total, tid = None, None
    for sid in US_TOTAL:
        try:
            d = C.get_fred_series(sid, "v")
            total = d.set_index("date")["v"].resample("QS").mean()
            tid = sid
            break
        except Exception:
            continue
    if total is None:
        raise RuntimeError("US total financial assets (TFAABSHNO) did not resolve")
    say(f"  US total financial assets from {tid}")

    tier_sum = {t: pd.Series(0.0, index=total.index) for t in TIERS}
    resolved = []
    for tier, name, ids in US_COMPONENTS:
        s, sid = _first_resolving(ids, name)
        if s is not None:
            tier_sum[tier] = tier_sum[tier].add(s.reindex(total.index), fill_value=0.0)
            resolved.append((tier, name, sid))
    say(f"  resolved {len(resolved)}/{len(US_COMPONENTS)} components")

    df = pd.DataFrame({t: tier_sum[t] for t in TIERS})
    df["total"] = total
    df = df.dropna(subset=["total"])
    df = df[df["total"] > 0]
    for t in TIERS:
        df[f"{t}_share"] = 100 * df[t] / df["total"]
    df["broad_liquid_share"] = df[["T1_share", "T2_share", "T3_share"]].sum(axis=1)
    df["year"] = df.index.year
    return df.groupby("year").last()


def ea_latest_shares():
    """Latest EA tier shares from liquidity_ladder.py output (run it first)."""
    p = os.path.join(C.DATA, "liquidity_ladder_stocks.csv")
    if not os.path.exists(p):
        return None
    ea = pd.read_csv(p).sort_values("year").iloc[-1]
    return {t: float(ea[f"{t}_share"]) for t in TIERS} | \
           {"broad_liquid_share": float(ea["broad_liquid_share"]), "year": int(ea["year"])}


def plot_ladder_compare(us_latest, ea):
    """Grouped bars: US vs EA tier shares + broad sellable-fast share."""
    cats = TIERS + ["broad_liquid_share"]
    labels = [TIER_LABELS[t] for t in TIERS] + ["broad\nsellable-fast"]
    us_vals = [us_latest[f"{t}_share"] for t in TIERS] + [us_latest["broad_liquid_share"]]
    ea_vals = [ea[f"{t}_share"] for t in TIERS] + [ea["broad_liquid_share"]]
    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    ax.bar(x - 0.2, us_vals, width=0.4, color=C.C_MAIN, label="United States")
    ax.bar(x + 0.2, ea_vals, width=0.4, color=C.C_ORANGE, label="Euro area")
    for i, (u, e) in enumerate(zip(us_vals, ea_vals)):
        ax.text(i - 0.2, u + 0.6, f"{u:.0f}", ha="center", fontsize=8, color=C.C_MAIN)
        ax.text(i + 0.2, e + 0.6, f"{e:.0f}", ha="center", fontsize=8, color="#a04000")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("share of household financial assets (%)")
    ax.set_title("Households hold liquidity differently: US vs euro area\n"
                 "financial wealth by liquidity tier (stocks, latest)",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    C.caveat(fig, "US: Fed Z.1 (HNO), shares of total financial assets. EA: Eurostat "
                  "nasa_10_f_bs. US tilts to T3 (equities/funds); EA holds more in deposits.")
    C.savefig(fig, "us_vs_ea_ladder.png")


def plot_saving_compare():
    """US personal saving rate (PSAVERT) vs EA household saving rate over time."""
    try:
        us = C.get_fred_series("PSAVERT", "psr").set_index("date")["psr"].resample("QS").mean()
    except Exception as e:
        say(f"  US saving rate (PSAVERT) failed: {e}")
        return
    ea = C.load_quarterly("ea_saving_rate_quarterly.csv", "saving")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.plot(us.index, us.values, color=C.C_MAIN, lw=2.0, label="US personal saving rate")
    ax.plot(ea.index, ea.values, color=C.C_ORANGE, lw=2.4, label="Euro-area household saving rate")
    C.mark_periods(ax, shade=True)
    ax.set_ylabel("saving rate (% of disposable income)")
    ax.set_xlabel("date")
    ax.set_title("Saving rates: US vs euro area", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    C.caveat(fig, "Note: US PSAVERT is a NET personal saving rate, the EA figure is GROSS — "
                  "compare the dynamics (both rose post-2022), not the levels.")
    C.savefig(fig, "us_vs_ea_saving.png")
    pd.concat([us.rename("us"), ea.rename("ea")], axis=1).to_csv(
        os.path.join(C.DATA, "us_vs_ea_saving.csv"))


def main():
    say("#" * 72)
    say("# US vs euro area — the same liquidity ladder")
    say("#" * 72)

    try:
        us = us_tier_shares()
        latest = us.iloc[-1]
        say(f"\nUS household tier shares of financial assets ({int(latest['year'])}):")
        for t in TIERS:
            say(f"  {TIER_LABELS[t]:<16}: {latest[f'{t}_share']:5.1f}%")
        say(f"  broad sellable-fast (T1+T2+T3): {latest['broad_liquid_share']:.1f}%")
        us.to_csv(os.path.join(C.DATA, "us_ladder_stocks.csv"))
    except Exception as e:
        say(f"  US ladder failed: {e}")
        latest = None

    ea = ea_latest_shares()
    if ea is None:
        say("\n  EA shares not found — run liquidity_ladder.py first for the comparison.")
    elif latest is not None:
        say(f"\nUS vs EA broad sellable-fast share: "
            f"US {latest['broad_liquid_share']:.0f}% vs EA {ea['broad_liquid_share']:.0f}% "
            f"(EA {ea['year']}). US tilts more to marketable (T3) equities & funds; "
            f"EA holds more in deposits (T1/T2) — a more market-price-exposed US buffer.")
        plot_ladder_compare(latest, ea)

    plot_saving_compare()

    with open(os.path.join(C.DATA, "us_comparison.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'us_comparison.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
