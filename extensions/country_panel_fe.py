#!/usr/bin/env python3
"""
Extension III(b) --- Country panel with two-way fixed effects
============================================================

Idea. The euro-area aggregate time series is underpowered. A country panel has an
order of magnitude more variation, and two-way (country + year) fixed effects do
the identification work the aggregate cannot: country FE absorb the structural
North--South differences in saving habits, year FE absorb every euro-area-wide
shock (the ECB rate, common inflation, the common uncertainty wave). What is left
is the *within-country* co-movement of saving with country-specific shocks:

    saving_it = a_i + g_t + b1 * energy_infl_it + b2 * headline_infl_it + e_it.

A positive b1 means that, beyond common time effects and its own structural
level, a country saving more in years it is hit harder by the energy/cost shock
-- the heterogeneity fingerprint of precaution. We contrast pooled OLS (no FE,
contaminated by the North--South confound) with the two-way FE estimator to show
how much the confound matters, and -- where the series is available -- add a
country-level Geopolitical Risk index (GPRC) as a cleaner uncertainty regressor.
SEs cluster by country.

Pulls Eurostat HICP by country (energy + headline) and, best-effort, GPRcm.
Reads ../data for country saving. Writes extensions/figures + a results md.
    python country_panel_fe.py
"""

import os
from io import BytesIO

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

import _common as cm

REPORT = []

ISO2_TO_ISO3 = {
    "DE": "DEU", "FR": "FRA", "IT": "ITA", "ES": "ESP", "NL": "NLD", "BE": "BEL",
    "AT": "AUT", "FI": "FIN", "IE": "IRL", "PT": "PRT", "EL": "GRC", "PL": "POL",
    "CZ": "CZE", "SK": "SVK", "HU": "HUN", "SI": "SVN", "EE": "EST", "LV": "LVA",
    "LT": "LTU", "SE": "SWE", "DK": "DNK",
}


def say(line=""):
    print(line)
    REPORT.append(str(line))


def get_country_year_inflation():
    """Eurostat prc_hicp_manr -> country x year mean YoY for energy + headline."""
    long = cm.es_long("prc_hicp_manr")
    long = long[long["coicop"].isin(["NRG", "CP00"]) & long["geo"].isin(cm.COUNTRIES)]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["value", "year"])
    g = (long.groupby(["geo", "year", "coicop"])["value"].mean()
              .unstack("coicop").reset_index()
              .rename(columns={"NRG": "energy_infl", "CP00": "headline_infl"}))
    g["year"] = g["year"].astype(int)
    return g


def get_country_gpr():
    """Best-effort country GPR (GPRC_<ISO3>) from Caldara--Iacoviello. Returns
    long [geo, year, gprc] or None if the file lacks country columns."""
    url = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
    try:
        df = pd.read_excel(BytesIO(cm.http_get(url).content))
    except Exception as e:
        print(f"  GPRC: download/read failed ({e}); skipping.")
        return None
    datecol = next((c for c in df.columns if str(c).lower() in ("month", "date")),
                   df.columns[0])
    iso3_cols = {}
    for iso2, iso3 in ISO2_TO_ISO3.items():
        col = next((c for c in df.columns
                    if str(c).upper() in (f"GPRC_{iso3}", f"GPRC{iso3}", iso3)), None)
        if col is not None:
            iso3_cols[iso2] = col
    if len(iso3_cols) < 3:
        print(f"  GPRC: file has no usable country columns "
              f"({len(iso3_cols)} matched); skipping.")
        return None
    df["year"] = pd.to_datetime(df[datecol], errors="coerce").dt.year
    frames = []
    for iso2, col in iso3_cols.items():
        s = (df[["year", col]].dropna()
               .groupby("year")[col].mean().reset_index()
               .rename(columns={col: "gprc"}))
        s["geo"] = iso2
        frames.append(s)
    out = pd.concat(frames, ignore_index=True)
    out["year"] = out["year"].astype(int)
    print(f"  GPRC: {len(iso3_cols)} countries matched.")
    return out


def fe_fit(df, formula, label):
    res = smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["geo"]})
    say(f"\n[{label}]  n={int(res.nobs)}")
    return res


def report_coef(res, name, pretty):
    if name not in res.params:
        return
    b, se, p = res.params[name], res.bse[name], res.pvalues[name]
    star = " *" if p < 0.05 else ""
    say(f"    {pretty:<34}: {b:+.3f} (se {se:.3f}, p {p:.3f}){star}")


def main():
    say("#" * 70)
    say("# Country panel, two-way fixed effects — within-country saving response")
    say("#" * 70)

    saving = cm.load_country_saving_long()                 # geo, year, saving
    say("\n[1] Eurostat HICP by country (energy + headline) ...")
    infl = get_country_year_inflation()
    df = saving.merge(infl, on=["geo", "year"], how="inner").dropna(
        subset=["saving", "energy_infl", "headline_infl"])
    say(f"  merged panel: {df['geo'].nunique()} countries x "
        f"{df['year'].nunique()} years, {len(df)} obs "
        f"({df['year'].min()}-{df['year'].max()})")

    # Pooled OLS (no FE) vs two-way FE: shows how the North-South confound biases
    # the naive estimate.
    say("\n--- Saving on the energy shock: pooled vs two-way FE ---")
    pooled = fe_fit(df, "saving ~ energy_infl + headline_infl", "pooled OLS (no FE)")
    report_coef(pooled, "energy_infl", "energy inflation")
    report_coef(pooled, "headline_infl", "headline inflation")

    twfe = fe_fit(df, "saving ~ energy_infl + headline_infl + C(geo) + C(year)",
                  "two-way FE (country + year)")
    report_coef(twfe, "energy_infl", "energy inflation (within)")
    report_coef(twfe, "headline_infl", "headline inflation (within)")
    say("  (Identifying coefficient: energy inflation under two-way FE. A positive,"
        " significant value supports heterogeneity-driven precaution.)")

    # Optional GPRC robustness.
    say("\n[2] Country-level GPR (best-effort) ...")
    gprc = get_country_gpr()
    coefs_for_plot = [("energy infl.\n(pooled)", pooled, "energy_infl"),
                      ("energy infl.\n(two-way FE)", twfe, "energy_infl")]
    if gprc is not None:
        dfg = df.merge(gprc, on=["geo", "year"], how="inner").dropna(subset=["gprc"])
        dfg["gprc_z"] = cm.zscore(dfg["gprc"])
        if dfg["geo"].nunique() >= 5 and len(dfg) >= 40:
            say(f"  GPRC panel: {dfg['geo'].nunique()} countries, {len(dfg)} obs")
            gfe = fe_fit(dfg, "saving ~ gprc_z + headline_infl + C(geo) + C(year)",
                         "two-way FE with country GPR")
            report_coef(gfe, "gprc_z", "country GPR (z, within)")
            coefs_for_plot.append(("country GPR (z)\n(two-way FE)", gfe, "gprc_z"))
        else:
            say("  GPRC panel too small after merge; skipping GPRC regression.")

    # ---- coefficient comparison plot ----
    labels = [l for l, _, _ in coefs_for_plot]
    vals = [r.params[n] for _, r, n in coefs_for_plot]
    errs = [1.96 * r.bse[n] for _, r, n in coefs_for_plot]
    colors = [cm.C_COOL if "pooled" in l else cm.C_MAIN for l in labels]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhline(0, color="black", lw=0.8)
    ax.bar(range(len(vals)), vals, yerr=errs, color=colors, capsize=4, width=0.6)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("coefficient on the shock (pp per unit)")
    ax.set_title("Within-country, saving responds to country-specific shocks\n"
                 "Pooled OLS vs two-way fixed effects (95% CI)", fontweight="bold")
    cm.savefig(fig, "country_panel_fe.png")

    df.to_csv(os.path.join(cm.DATA, "country_panel.csv"), index=False)
    with open(os.path.join(cm.DATA, "country_panel_fe.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extensions/data/country_panel_fe.md")


if __name__ == "__main__":
    main()
