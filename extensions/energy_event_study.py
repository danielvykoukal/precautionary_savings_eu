#!/usr/bin/env python3
"""
Extension III(a) --- Energy-shock event study / difference-in-differences
========================================================================

Idea. The 2022 Russia/energy shock is plausibly exogenous to a country's saving
*preferences*, and it hit some countries far harder than others. So we can run a
natural experiment: did countries more exposed to the energy shock raise saving
*more* after 2022, relative to less-exposed countries and to their own pre-2022
path? Country and year fixed effects net out structural North--South saving habits
and euro-area-wide shocks (the ECB rate, common inflation), so the estimate is
the differential, within-country, post-shock response.

Design (annual country panel, 2014--2025; base year 2021):
    saving_it = a_i + g_t + sum_k b_k ( Exposed_i x 1[t = 2022+k] ) + e_it
Pre-2022 b_k near zero is the parallel-trends check; post b_k > 0 is the
precautionary fingerprint. A compact diff-in-diff collapses the post years:
    saving_it = a_i + g_t + d ( Exposed_i x Post_t ) + e_it.
Exposure is taken two ways: the editorial high-exposure dummy, and (continuously)
each country's standardised peak-2022 energy inflation. SEs cluster by country.

Reads ../data only. Writes extensions/figures + a results md.
    python energy_event_study.py
"""

import os

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

import _common as cm

BASE_YEAR = 2021      # omitted reference (last full pre-shock year)
REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def load_panel():
    df = cm.load_country_saving_long()                    # geo, year, saving
    peak = cm.root_csv("country_energy_peak_2022.csv")    # geo, value
    peak = peak.rename(columns={peak.columns[0]: "geo", peak.columns[1]: "energy"})
    df = df.merge(peak[["geo", "energy"]], on="geo", how="left")
    df["exposed"] = df["geo"].isin(cm.HIGH_EXPOSURE).astype(int)
    df["energy_z"] = cm.zscore(df["energy"])
    df["post"] = (df["year"] >= 2022).astype(int)
    return df.dropna(subset=["saving"])


def did(df, treat):
    """Two-way FE diff-in-differences with the chosen treatment column."""
    df = df.copy()
    df["treatXpost"] = df[treat] * df["post"]
    res = smf.ols("saving ~ treatXpost + C(geo) + C(year)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["geo"]})
    return res.params["treatXpost"], res.bse["treatXpost"], res.pvalues["treatXpost"]


def event_study(df):
    """Two-way FE event study on the high-exposure dummy; base year omitted."""
    df = df.copy()
    years = sorted(y for y in df["year"].unique() if y != BASE_YEAR)
    terms = []
    for y in years:
        col = f"x{y}"
        df[col] = df["exposed"] * (df["year"] == y)
        terms.append(col)
    res = smf.ols("saving ~ " + " + ".join(terms) + " + C(geo) + C(year)",
                  data=df).fit(cov_type="cluster", cov_kwds={"groups": df["geo"]})
    rows = [(BASE_YEAR, 0.0, 0.0, 0.0)]
    for y in years:
        col = f"x{y}"
        rows.append((y, res.params[col], res.bse[col], res.pvalues[col]))
    return pd.DataFrame(rows, columns=["year", "coef", "se", "p"]).sort_values("year")


def main():
    say("#" * 70)
    say("# Energy-shock event study / DiD — exposed vs less-exposed countries")
    say("#" * 70)
    df = load_panel()
    say(f"panel: {df['geo'].nunique()} countries x {df['year'].nunique()} years "
        f"({df['year'].min()}-{df['year'].max()}); "
        f"{df['exposed'].groupby(df['geo']).first().sum()} high-exposure")

    say("\n--- Difference-in-differences (Exposed x Post>=2022) ---")
    for label, col in [("editorial high-exposure dummy", "exposed"),
                       ("standardised peak-2022 energy inflation", "energy_z")]:
        b, se, p = did(df, col)
        star = " *" if p < 0.05 else ""
        say(f"  {label:<46}: d = {b:+.2f} pp (se {se:.2f}, p {p:.3f}){star}")
    say("  (d>0 => more-exposed countries raised saving more after 2022.)")

    es = event_study(df)
    say("\n--- Event-study coefficients (high-exposure x year; base "
        f"{BASE_YEAR}) ---")
    say(f"{'year':<8}{'coef (pp)':>12}{'se':>8}{'p':>8}")
    for _, r in es.iterrows():
        say(f"{int(r['year']):<8}{r['coef']:>+12.2f}{r['se']:>8.2f}{r['p']:>8.3f}")
    pre = es[es["year"] < 2022]["coef"].abs().max()
    say(f"\nparallel-trends check: largest |pre-2022 coef| = {pre:.2f} pp "
        f"({'small — supports' if pre < 1.0 else 'sizeable — qualifies'} the design)")

    # ---- event-study plot ----
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(2021.5, color="grey", ls="--", lw=1)
    ax.errorbar(es["year"], es["coef"], yerr=1.96 * es["se"], fmt="o-",
                color=cm.C_HOT, ecolor=cm.C_HOT, capsize=3, lw=1.8, ms=4,
                label="exposed − less-exposed (vs 2021)")
    ax.annotate("2022 shock", xy=(2021.5, ax.get_ylim()[1]), xytext=(2, -2),
                textcoords="offset points", ha="left", va="top",
                fontsize=8, color="grey")
    ax.set_xlabel("year")
    ax.set_ylabel("differential saving rate (pp, vs 2021)")
    ax.set_title("Did more energy-exposed countries save more after 2022?\n"
                 "Event study, country & year fixed effects", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    cm.savefig(fig, "energy_event_study.png")

    es.to_csv(os.path.join(cm.DATA, "energy_event_study_coefs.csv"), index=False)
    with open(os.path.join(cm.DATA, "energy_event_study.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extensions/data/energy_event_study.md")


if __name__ == "__main__":
    main()
