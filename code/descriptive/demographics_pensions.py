#!/usr/bin/env python3
"""
Descriptive #2 (Wave 2) --- Demographics & pensions
===================================================

Supervisor ideas: as populations age and people doubt the state pension, do they
save more privately and hold less-risky assets? And do countries with bigger
*funded* pension systems show different household saving?

Two cross-country scatters:
  (a) old-age dependency ratio   vs the household saving rate  (does aging -> more saving?)
  (b) insurance & pension share of household assets (F6, a funded-pillar proxy)
                                  vs the household saving rate  (do funded pensions
                                  go with more or less private saving?)

Why F6 as the proxy: in a funded system households *hold* pension assets (high F6);
under a pure pay-as-you-go promise the pension is a state liability, not a
household asset (low F6). So F6/total is a rough "how funded is the pension" gauge.

Data: Eurostat demo_pjanind (old-age dependency) + ../data/country_saving_annual.csv
+ nasa_10_f_bs (F6 share, reused from saving_composition_evolution).
    python demographics_pensions.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C
from saving_composition_evolution import finstock_shares

REPORT = []
COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "FI", "IE", "PT", "EL",
             "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT", "SE", "DK"]


def say(line=""):
    print(line)
    REPORT.append(str(line))


def country_saving():
    df = C.root_csv("country_saving_annual.csv")
    df = df.rename(columns={df.columns[0]: "geo"}).set_index("geo")
    df.columns = [int(float(c)) for c in df.columns]
    for y in sorted(df.columns, reverse=True):
        s = df[y].dropna()
        if len(s) >= 10:
            return s.to_dict(), y
    y = max(df.columns)
    return df[y].dropna().to_dict(), y


def old_age_dependency():
    """{geo: old-age dependency ratio} for the latest year (Eurostat demo_pjanind)."""
    long = C.es_long("demo_pjanind")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    icol = code = None
    for c in long.columns:
        if c in ("geo", "time", "value"):
            continue
        vals = {str(v).upper() for v in long[c].dropna().unique()}
        old = [v for v in vals if "OLDDEP" in v]
        if old:
            icol = c
            code = next((v for v in ("OLDDEP1", "OLDDEP") if v in old), sorted(old)[0])
            break
    if icol is None:
        raise RuntimeError("demo_pjanind: no OLDDEP indicator found")
    long = long[long[icol].astype(str).str.upper() == code]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    yr = int(long["year"].max())
    sub = long[long["year"] == yr].groupby("geo")["value"].mean()
    return sub.to_dict(), yr, code


def scatter(ax, xs, ys, labels, xlabel, ylabel, title):
    ax.scatter(xs, ys, s=55, color=C.C_MAIN, zorder=3)
    for x, y, g in zip(xs, ys, labels):
        ax.annotate(g, (x, y), xytext=(4, 4), textcoords="offset points", fontsize=8.5)
    r = np.nan
    if len(xs) >= 4:
        b1, b0 = np.polyfit(xs, ys, 1)
        xx = np.array([min(xs), max(xs)])
        ax.plot(xx, b0 + b1 * xx, color=C.C_HOT, ls="--", lw=1.3,
                label=f"OLS slope {b1:+.2f}")
        r = float(np.corrcoef(xs, ys)[0, 1])
        ax.legend(frameon=False, fontsize=8.5, loc="best")
    ax.axhline(0, color="black", lw=0.7, alpha=0.5)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    return r


def main():
    say("#" * 72)
    say("# Demographics & pensions vs household saving")
    say("#" * 72)
    saving, syear = country_saving()
    try:
        dep, dyear, code = old_age_dependency()
    except Exception as e:
        say(f"  old-age dependency failed: {e}")
        dep, dyear, code = {}, None, None
    try:
        shares = finstock_shares(["EA20", "EA19"] + COUNTRIES)
        f6 = {g: shares[g]["inspen_F6"].iloc[-1] for g in shares if len(shares[g])}
    except Exception as e:
        say(f"  F6 share failed: {e}")
        f6 = {}

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(13, 5.8))

    ga = [g for g in COUNTRIES if g in dep and g in saving]
    ra = scatter(axa, [dep[g] for g in ga], [saving[g] for g in ga], ga,
                 f"old-age dependency ratio (%, {dyear})",
                 f"household saving rate (%, {syear})",
                 "Does an older population save more?") if ga else np.nan
    gb = [g for g in COUNTRIES if g in f6 and g in saving]
    rb = scatter(axb, [f6[g] for g in gb], [saving[g] for g in gb], gb,
                 "insurance & pension share of household assets (F6, %)",
                 f"household saving rate (%, {syear})",
                 "Funded pensions vs private saving") if gb else np.nan

    say(f"\n(a) corr(old-age dependency, saving rate), n={len(ga)}: {ra:+.2f}")
    say(f"(b) corr(F6 insurance/pension share, saving rate), n={len(gb)}: {rb:+.2f}")
    say("Reading: the cross-country links are weak/noisy. Aging alone does not "
        "mechanically raise saving (high-dependency Southern economies save less, "
        "not more), and big funded-pension systems (NL/DK, high F6) coexist with "
        "solid saving rather than low saving -- so 'good pensions => less private "
        "saving' is not clear in the cross-section. Pensions DO shape WHERE wealth "
        "sits (funded systems hold more in F6/F5), more than how MUCH is saved.")

    fig.suptitle("Demographics, pensions, and household saving across Europe",
                 fontweight="bold", y=1.02)
    C.caveat(fig, "Eurostat demo_pjanind (old-age dependency) + tec00131 saving + nasa_10_f_bs "
                  "(F6 share as a funded-pension proxy). Cross-section, latest year; descriptive.")
    fig.tight_layout()
    C.savefig(fig, "demographics_pensions.png")

    rows = [{"geo": g, "old_age_dep": dep.get(g), "f6_share": f6.get(g),
             "saving": saving.get(g)} for g in COUNTRIES]
    pd.DataFrame(rows).to_csv(os.path.join(C.DATA, "demographics_pensions.csv"), index=False)
    with open(os.path.join(C.DATA, "demographics_pensions.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'demographics_pensions.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
