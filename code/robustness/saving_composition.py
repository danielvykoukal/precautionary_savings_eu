#!/usr/bin/env python3
"""
Extension I --- Composition of saving: the flight-to-safety test
================================================================

Idea. The single cleanest way to separate *precautionary* saving from ordinary
*intertemporal substitution* is where the saving goes. If households save more
because the ECB raised the reward to saving, they should chase yield (debt
securities, equity, funds). If they save more out of fear, they should pile into
*liquid, safe* assets -- currency and deposits -- even when those pay least. So we
track the share of households' net acquisition of financial assets that goes into
currency & deposits (instrument F2) over time, and ask whether it rose after 2022.

    F2 share_t = 100 * F2(assets)_t / total financial-asset acquisition_t.

A rising F2 share post-2022 is a precautionary fingerprint that intertemporal
substitution cannot produce. Data: Eurostat sector financial accounts
(nasa_10_f), households (S14/S14_S15), euro-area aggregate, annual.

Reads nothing from ../data (self-contained pull). Writes extensions/figures + md.
    python saving_composition.py
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


def get_household_finflows():
    """Return tidy [year, na_item, value] for household net acquisition of
    financial assets, one euro-area aggregate, in a millions unit."""
    long = C.es_long("nasa_10_f_tr")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    C.show_dims(long, "nasa_10_f_tr")

    # household sector (required, else we would blend sectors)
    if "sector" in long.columns:
        sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
        if sec is None:
            raise RuntimeError("nasa_10_f_tr: household sector S14/S14_S15 not found")
        long = long[long["sector"] == sec]
    # non-consolidated transactions if that dimension exists
    if "co_nco" in long.columns:
        for cc in ("NCO", "CO"):
            if cc in set(long["co_nco"]):
                long = long[long["co_nco"] == cc]
                break
    # assets side (net acquisition of financial assets)
    if "finpos" in long.columns:
        for fp in ("ASS", "A"):
            if fp in set(long["finpos"]):
                long = long[long["finpos"] == fp]
                break
    # a millions unit (current prices)
    if "unit" in long.columns:
        for u in ("MIO_EUR", "CP_MEUR", "MIO_NAC"):
            if u in set(long["unit"]):
                long = long[long["unit"] == u]
                break
    # euro-area aggregate geo
    geo = next((g for g in ("EA20", "EA19", "EA", "EU27_2020")
                if g in set(long["geo"])), None)
    if geo is None:
        raise RuntimeError("nasa_10_f: no euro-area aggregate geo found")
    long = long[long["geo"] == geo]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    say(f"  using geo={geo}; instruments seen: "
        f"{sorted(set(long['na_item']))[:12]}")
    return long[["year", "na_item", "value"]], geo


def compute_f2_share(long):
    """F2 share of total net financial-asset acquisition, per year."""
    piv = long.groupby(["year", "na_item"])["value"].sum().unstack("na_item")
    if "F2" not in piv.columns:
        raise RuntimeError("nasa_10_f: no F2 (currency & deposits) instrument")
    # denominator: total net acquisition of financial assets. Use 'F'/'FA' if
    # published, else sum the eight TOP-LEVEL instruments only (never the
    # F11/F21... subcomponents, which would double-count).
    toplevel = [f"F{i}" for i in range(1, 9)]
    if "F" in piv.columns:
        total = piv["F"]
    elif "FA" in piv.columns:
        total = piv["FA"]
    else:
        comp = [c for c in toplevel if c in piv.columns]
        total = piv[comp].sum(axis=1)
    share = (100 * piv["F2"] / total).rename("f2_share")
    out = pd.concat([piv["F2"].rename("f2_flow"), total.rename("total_flow"),
                     share], axis=1).dropna().reset_index()
    out["year"] = out["year"].astype(int)
    return out


def main():
    say("#" * 70)
    say("# Composition of saving — currency & deposits (F2) share over time")
    say("#" * 70)
    try:
        long, geo = get_household_finflows()
        out = compute_f2_share(long)
    except Exception as e:
        say(f"\nFAILED to build the composition series: {e}")
        say("Inspect the printed nasa_10_f dimensions and adjust the filters.")
        with open(os.path.join(C.DATA, "saving_composition.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    pre = out[(out["year"] >= 2015) & (out["year"] <= 2019)]["f2_share"].mean()
    post = out[out["year"] >= 2022]["f2_share"].mean()
    say(f"\nF2 (currency & deposits) share of household financial-asset acquisition:")
    say(f"  2015-19 average : {pre:5.1f}%")
    say(f"  2022+   average : {post:5.1f}%")
    say(f"  change          : {post - pre:+5.1f} pp")
    say("  (A rise after 2022 = flight to liquidity/safety, the precautionary "
        "fingerprint that intertemporal substitution cannot produce.)")
    say("\nLatest years:")
    for _, r in out[out["year"] >= 2019].iterrows():
        say(f"  {int(r['year'])}: F2 share {r['f2_share']:5.1f}%")

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(out["year"], out["f2_share"], color=C.C_MAIN, lw=2.4, marker="o", ms=4)
    if not np.isnan(pre):
        ax.axhline(pre, color="#7f8c8d", ls=":", lw=1.3)
        ax.text(out["year"].min(), pre, f" 2015-19 avg {pre:.0f}%",
                va="bottom", ha="left", fontsize=8.5, color="#7f8c8d")
    ax.axvline(2021.5, color="grey", ls="--", lw=1)
    ax.annotate("2022 shock", xy=(2021.5, ax.get_ylim()[1]), xytext=(2, -2),
                textcoords="offset points", ha="left", va="top",
                fontsize=8, color="grey")
    ax.set_xlabel("year")
    ax.set_ylabel("F2 share of financial-asset acquisition (%)")
    ax.set_title(f"Flight to safety? Currency & deposits as a share of household\n"
                 f"financial saving, euro area ({geo})", fontweight="bold")
    C.savefig(fig, "saving_composition_f2_share.png")

    out.to_csv(os.path.join(C.DATA, "saving_composition.csv"), index=False)
    with open(os.path.join(C.DATA, "saving_composition.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extensions/data/saving_composition.md")


if __name__ == "__main__":
    main()
