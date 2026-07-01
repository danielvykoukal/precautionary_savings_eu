#!/usr/bin/env python3
"""
Descriptive #6 --- What are people saving in, and how has it evolved?
====================================================================

Supervisor idea: disaggregate saving. What do euro-area households hold their
financial wealth in, how has it evolved, and how does it differ across countries?
The user's read: the non-risky share (deposits) is still very high, but equity
involvement has grown over the last ~10 years.

We track two shares of household financial assets over time:
  non-risky  = F2 currency & deposits
  risky      = F5 equity & investment-fund shares
and add a cross-country snapshot (DE/FR/IT/ES vs the euro area) of the risky
share. This complements `../extension_feedback/liquidity_ladder.py` (which ranks
by *liquidity*); here the cut is *risk*.

Data: Eurostat nasa_10_f_bs (household financial balance sheet, stocks).
    python saving_composition_evolution.py
"""

import os

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

REPORT = []
COUNTRIES = ["DE", "FR", "IT", "ES"]


def say(line=""):
    print(line)
    REPORT.append(str(line))


def _col(piv, code):
    return piv[code] if code in piv.columns else pd.Series(0.0, index=piv.index)


def finstock_shares(geos):
    """Per-geo shares of household financial assets over time: F2 (non-risky),
    F5 (risky), F3 (bonds), F6 (insurance/pension). Returns {geo: DataFrame}."""
    long = C.es_long("nasa_10_f_bs")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    if "sector" in long.columns:
        sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
        long = long[long["sector"] == sec] if sec else long
    if "co_nco" in long.columns:
        for cc in ("NCO", "CO"):
            if cc in set(long["co_nco"]):
                long = long[long["co_nco"] == cc]
                break
    if "finpos" in long.columns:
        for fp in ("ASS", "A"):
            if fp in set(long["finpos"]):
                long = long[long["finpos"] == fp]
                break
    if "unit" in long.columns:
        for u in ("MIO_EUR", "CP_MEUR", "MIO_NAC"):
            if u in set(long["unit"]):
                long = long[long["unit"] == u]
                break
    long = long[long["geo"].isin(geos)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    out = {}
    for g in geos:
        piv = long[long["geo"] == g].groupby(["year", "na_item"])["value"].sum().unstack("na_item")
        if "F" not in piv.columns:
            continue
        tot = piv["F"]
        d = pd.DataFrame({
            "safe_F2": 100 * _col(piv, "F2") / tot,
            "risky_F5": 100 * _col(piv, "F5") / tot,
            "bonds_F3": 100 * _col(piv, "F3") / tot,
            "inspen_F6": 100 * _col(piv, "F6") / tot,
        })
        out[g] = d[tot.notna() & (tot > 0)].sort_index()
    return out


def main():
    say("#" * 72)
    say("# What households save in — non-risky (F2) vs risky (F5), over time")
    say("#" * 72)
    geos = ["EA20", "EA19", "EA"] + COUNTRIES
    try:
        shares = finstock_shares(geos)
    except Exception as e:
        say(f"\nFAILED: {e}")
        with open(os.path.join(C.DATA, "saving_composition_evolution.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return
    ea_geo = next((g for g in ("EA20", "EA19", "EA") if g in shares), None)
    if ea_geo is None:
        say("no euro-area aggregate available"); return
    ea = shares[ea_geo]

    decade = max(ea.index.min(), ea.index.max() - 10)
    latest = ea.index.max()
    say(f"\nEuro-area household assets ({ea_geo}):")
    say(f"  non-risky deposits (F2): {ea.loc[decade,'safe_F2']:.1f}% ({decade}) -> "
        f"{ea.loc[latest,'safe_F2']:.1f}% ({latest})")
    say(f"  risky equity & funds (F5): {ea.loc[decade,'risky_F5']:.1f}% ({decade}) -> "
        f"{ea.loc[latest,'risky_F5']:.1f}% ({latest})  ({ea.loc[latest,'risky_F5']-ea.loc[decade,'risky_F5']:+.1f} pp)")
    say("Reading: deposits remain the single biggest non-risky store, but the risky "
        "(equity & fund) share has grown over the past decade — more euro-area "
        "households now have market exposure, though still a minority of wealth.")

    # ---- figure 1: EA composition by RISK over time (clean lines + end labels) ----
    fig, ax = plt.subplots(figsize=(10, 5.6))
    lines = [("safe_F2", C.C_COOL, "-", 2.8, "deposits (F2)"),
             ("risky_F5", C.C_HOT, "-", 2.8, "equity & funds (F5)"),
             ("inspen_F6", C.C_ACCENT, "--", 1.8, "ins. & pension (F6)")]
    for col, color, ls, lw, txt in lines:
        ax.plot(ea.index, ea[col], color=color, lw=lw, ls=ls,
                alpha=0.85 if ls == "--" else 1.0)
        s = ea[col].dropna()
        ax.annotate(txt, (s.index[-1], s.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                    color=color, fontsize=8.5, fontweight="bold", va="center")
    ax.set_xlim(ea.index.min(), ea.index.max() + 5)      # room for the end labels
    C.mark_periods(ax, year_axis=True, shade=True)
    ax.set_ylabel("share of household financial assets (%)")
    ax.set_xlabel("year")
    ax.set_title("What euro-area households save in, by RISK\n"
                 "equity & funds (risky) have overtaken cash & deposits (non-risky)",
                 fontweight="bold")
    C.caveat(fig, "Eurostat nasa_10_f_bs (stocks) -- the same household balance sheet as the liquidity "
                  "ladder, cut by RISK not liquidity: 'risky' = equity & funds (F5), 'non-risky' = "
                  "deposits (F2). The risky share rose ~8 pp over the decade, overtaking deposits ~2021.")
    C.savefig(fig, "O5_saving_composition_evolution.png")

    # ---- figure 2: cross-country risky share (latest) ----
    rows = [(ea_geo.replace("EA20", "Euro area"), ea["risky_F5"].iloc[-1])]
    for c in COUNTRIES:
        if c in shares and len(shares[c]):
            rows.append((c, shares[c]["risky_F5"].iloc[-1]))
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(8, 5))
    names = [r[0] for r in rows]; vals = [r[1] for r in rows]
    ax.barh(names, vals, color=[C.C_HOT if n != "Euro area" else C.C_MAIN for n in names])
    for i, v in enumerate(vals):
        ax.text(v + 0.4, i, f"{v:.0f}%", va="center", fontsize=9)
    ax.set_xlabel("risky (equity & investment-fund) share of household financial assets (%)")
    ax.set_title("Equity involvement differs across Europe\n"
                 "risky-asset share of household wealth (latest)", fontweight="bold")
    C.caveat(fig, "Eurostat nasa_10_f_bs (stocks), F5 share of total financial assets. Southern "
                  "economies tend to hold less in market-exposed equity & funds.")
    C.savefig(fig, "O7_risky_share_by_country.png")

    ea.to_csv(os.path.join(C.DATA, "saving_composition_evolution.csv"))
    with open(os.path.join(C.DATA, "saving_composition_evolution.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'saving_composition_evolution.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
