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

Data (no FRED needed for the ladder): the US household balance sheet comes from
the **OECD** financial accounts (sector S1M households, SDMX, the same ESA F-codes
as the euro area), so the ladder renders anywhere OECD is reachable and reuses the
same `build_tiers()`. The US personal saving rate uses FRED (PSAVERT) when
reachable; the saving figure ALWAYS renders (euro area always shown, US line added
when FRED is available). A FRED Z.1 component path is kept as a ladder fallback.
Shares are taken against TOTAL financial assets.

    python us_comparison.py
"""

import os
from io import StringIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

# --- run from the flattened repo layout: top-level data/ & figures/, tagged CSVs
import os as _os, glob as _glob
C.ROOT = _os.path.dirname(_os.path.dirname(C.HERE))
C.ROOT_DATA = _os.path.join(C.ROOT, "data")
C.DATA = _os.path.join(C.ROOT, "data")
C.FIG = _os.path.join(C.ROOT, "figures")
_ORC = C.root_csv
def _TRC(name, required=True):
    import pandas as _pd
    if not _os.path.exists(_os.path.join(C.ROOT_DATA, name)):
        _h = _glob.glob(_os.path.join(C.ROOT_DATA, "?_" + name))
        if _h:
            return _pd.read_csv(_h[0])
    return _ORC(name, required)
C.root_csv = _TRC
from liquidity_ladder import build_tiers

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


OECD_BS_FLOW = "DSD_NASEC20@DF_T720R_A"   # OECD financial balance sheets (stocks)


def oecd_us_household_stocks(start=2005):
    """US household (S1M) financial assets by instrument from the OECD financial
    accounts -> tidy [year, na_item(F-code), value]. No FRED needed; the same ESA
    instrument codes as the euro-area ladder, so build_tiers() applies directly."""
    key = ".".join(["A", "", "USA"] + [""] * 15)   # 18-dim key: FREQ=A, REF_AREA=USA
    url = (f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,{OECD_BS_FLOW},/{key}"
           f"?startPeriod={start}&dimensionAtObservation=AllDimensions&format=csvfilewithlabels")
    df = pd.read_csv(StringIO(C.http_get(url, timeout=120).text))
    df = df[(df["SECTOR"] == "S1M") & (df["ACCOUNTING_ENTRY"] == "A")
            & (df["TRANSACTION"] == "LE")]
    if "UNIT_MEASURE" in df.columns and "USD" in set(df["UNIT_MEASURE"]):
        df = df[df["UNIT_MEASURE"] == "USD"]
    if "MATURITY" in df.columns:        # one row per instrument (total / not-applicable)
        df = df[df["MATURITY"].isin(["T", "_Z"])]
    df["value"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df["year"] = df["TIME_PERIOD"].astype(str).str.extract(r"(\d{4})").astype(float)
    df = df.dropna(subset=["value", "year"])
    df["year"] = df["year"].astype(int)
    long = (df.rename(columns={"INSTR_ASSET": "na_item"})
              .groupby(["year", "na_item"])["value"].sum().reset_index())
    if long.empty or "F" not in set(long["na_item"]):
        raise RuntimeError("OECD US balance sheet: no usable rows after filtering")
    return long[["year", "na_item", "value"]], f"OECD {OECD_BS_FLOW} (USA, S1M)"


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
    return {f"{t}_share": float(ea[f"{t}_share"]) for t in TIERS} | \
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
    C.caveat(fig, "US: OECD financial accounts (S1M households, Fed Z.1 basis), shares of total "
                  "financial assets. EA: Eurostat nasa_10_f_bs. US tilts to T3 (equities/funds); "
                  "EA holds more in deposits.")
    C.savefig(fig, "L2_us_vs_ea_ladder.png")


def plot_saving_compare():
    """US personal saving rate (PSAVERT) vs EA household saving rate over time."""
    ea = C.load_quarterly("ea_saving_rate_quarterly.csv", "saving")
    us = None
    try:
        us = C.get_fred_series("PSAVERT", "psr").set_index("date")["psr"].resample("QS").mean()
    except Exception as e:
        say(f"  US saving rate (PSAVERT, FRED) unavailable: {e}; EA shown alone "
            f"(run where FRED is reachable for the US line)")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.plot(ea.index, ea.values, color=C.C_ORANGE, lw=2.4,
            label="Euro-area household saving rate (gross)")
    if us is not None:
        ax.plot(us.index, us.values, color=C.C_MAIN, lw=2.0,
                label="US personal saving rate (net)")
    else:
        ax.text(0.5, 0.5, "US line pending FRED\n(run us_comparison.py where FRED is reachable)",
                transform=ax.transAxes, ha="center", va="center", fontsize=9,
                color=C.C_GREY, style="italic")
    C.mark_periods(ax, shade=True)
    ax.set_ylabel("saving rate (% of disposable income)")
    ax.set_xlabel("date")
    ax.set_title("Saving rates: US vs euro area", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    C.caveat(fig, "US PSAVERT is a NET personal saving rate; the EA figure is GROSS — "
                  "compare the dynamics, not the levels.")
    C.savefig(fig, "L_us_vs_ea_saving.png")
    if us is not None:
        pd.concat([us.rename("us"), ea.rename("ea")], axis=1).to_csv(
            os.path.join(C.DATA, "us_vs_ea_saving.csv"))


def main():
    say("#" * 72)
    say("# US vs euro area — the same liquidity ladder")
    say("#" * 72)

    us = None
    try:
        long_us, src = oecd_us_household_stocks()
        us, notes = build_tiers(long_us)
        say(f"\nUS ladder from {src}")
        for n in notes:
            say(f"  note: {n}")
    except Exception as e:
        say(f"  US via OECD failed ({e}); trying FRED Z.1 fallback")
        try:
            us = us_tier_shares()
        except Exception as e2:
            say(f"  US via FRED also failed: {e2}")

    latest = None
    if us is not None and len(us):
        latest = us.iloc[-1]
        say(f"\nUS household tier shares of financial assets ({int(latest['year'])}):")
        for t in TIERS:
            say(f"  {TIER_LABELS[t]:<16}: {latest[f'{t}_share']:5.1f}%")
        say(f"  broad sellable-fast (T1+T2+T3): {latest['broad_liquid_share']:.1f}%")
        us.to_csv(os.path.join(C.DATA, "us_ladder_stocks.csv"))

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
