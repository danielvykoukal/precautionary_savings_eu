#!/usr/bin/env python3
"""
Build the quarterly country panel for the saving regression
===========================================================

Assembles a balanced-ish quarterly panel (country x quarter) of the household
saving rate and its candidate drivers, so the precautionary channels can be
identified from CROSS-COUNTRY variation with two-way fixed effects (country +
quarter) — far better identified than the euro-area single time series.

Columns built (all per country-quarter):
  saving       household gross saving rate, % of (B6G + D8net), trailing 4 quarters
               (deseasonalised), from Eurostat nasq_10_nf_tr (sector S14_S15)
  spread       10y govt bond yield minus the German Bund (pp), Eurostat irt_lt_mcby_m
  sav_intent   consumer survey: intention to save, next 12m (balance), ei_bsco_m BS-SV-NY
  unemp_exp    consumer survey: expected unemployment, next 12m (balance), BS-UE-NY
  headline_infl HICP all-items annual rate (%), prc_hicp_manr CP00
  energy_infl  HICP energy annual rate (%), prc_hicp_manr NRG

Writes data/P_country_panel_quarterly.csv.
    python build_country_panel.py
"""

import os
import re
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import eurostat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

# euro-area-ish country set with good coverage (saving-rate ratio is unit-free, so
# non-euro members are fine too)
COUNTRIES = ["AT", "BE", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HU",
             "IE", "IT", "LT", "LV", "NL", "PL", "PT", "SE", "SI", "SK"]


def es_long(code):
    df = eurostat.get_data_df(code)
    geo = [c for c in df.columns if "geo" in c.lower()][0]
    df = df.rename(columns={geo: "geo"})
    tcols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    idc = [c for c in df.columns if c not in tcols]
    long = df.melt(id_vars=idc, value_vars=tcols, var_name="time", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long.dropna(subset=["value"])


def to_q(time):
    """'2024-Q1'/'2024Q1' or '2024-06' -> quarterly Period."""
    s = str(time)
    m = re.match(r"^(\d{4})[-]?Q([1-4])$", s)
    if m:
        return pd.Period(f"{m.group(1)}Q{m.group(2)}", freq="Q")
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        return pd.Period(pd.Timestamp(int(m.group(1)), int(m.group(2)), 1), freq="Q")
    return pd.NaT


def pick(series_vals, prefs):
    for p in prefs:
        if p in series_vals:
            return p
    return None


# ---------------------------------------------------------------- saving rate
def saving_rate_panel():
    long = es_long("nasq_10_nf_tr")
    sec = "S14_S15" if "S14_S15" in set(long["sector"]) else "S14"
    long = long[long["sector"] == sec]
    unit = pick(set(long["unit"]), ["CP_MEUR", "CP_MNAC"])
    long = long[long["unit"] == unit]
    long["q"] = long["time"].map(to_q)
    long = long.dropna(subset=["q"])
    long = long[long["geo"].isin(COUNTRIES)]

    def item(na, direct):
        s = long[(long["na_item"] == na) & (long["direct"] == direct)]
        return s.groupby(["geo", "q"])["value"].sum()

    B8G = item("B8G", "RECV")
    B6G = item("B6G", "RECV")
    D8r = item("D8", "RECV"); D8p = item("D8", "PAID")
    D8net = D8r.subtract(D8p, fill_value=0.0)
    df = pd.concat([B8G.rename("B8G"), B6G.rename("B6G"), D8net.rename("D8net")], axis=1)
    df = df.reset_index().sort_values(["geo", "q"])
    df["denom"] = df["B6G"] + df["D8net"].fillna(0.0)
    # trailing 4-quarter sums -> deseasonalised saving rate
    g = df.groupby("geo")
    df["B8G_4"] = g["B8G"].transform(lambda s: s.rolling(4).sum())
    df["den_4"] = g["denom"].transform(lambda s: s.rolling(4).sum())
    df["saving"] = 100.0 * df["B8G_4"] / df["den_4"]
    return df.dropna(subset=["saving"])[["geo", "q", "saving"]]


# ---------------------------------------------------------------- spread
def spread_panel():
    long = es_long("irt_lt_mcby_m")
    long["q"] = long["time"].map(to_q)
    long = long.dropna(subset=["q"])
    yq = long.groupby(["geo", "q"])["value"].mean().reset_index()
    de = yq[yq["geo"] == "DE"][["q", "value"]].rename(columns={"value": "de"})
    out = yq.merge(de, on="q", how="inner")
    out["spread"] = out["value"] - out["de"]
    out = out[out["geo"].isin(COUNTRIES)]
    return out[["geo", "q", "spread"]]


# ---------------------------------------------------------------- survey expectations
def survey_panel():
    long = es_long("ei_bsco_m")
    if "s_adj" in long.columns and "SA" in set(long["s_adj"]):
        long = long[long["s_adj"] == "SA"]
    long["q"] = long["time"].map(to_q)
    long = long.dropna(subset=["q"])
    long = long[long["geo"].isin(COUNTRIES)]

    def ind(code, name):
        s = long[long["indic"] == code]
        return (s.groupby(["geo", "q"])["value"].mean().rename(name))
    sav = ind("BS-SV-NY", "sav_intent")
    une = ind("BS-UE-NY", "unemp_exp")
    return pd.concat([sav, une], axis=1).reset_index()


# ---------------------------------------------------------------- inflation
def inflation_panel():
    long = es_long("prc_hicp_manr")
    long["q"] = long["time"].map(to_q)
    long = long.dropna(subset=["q"])
    long = long[long["geo"].isin(COUNTRIES)]

    def cp(code, name):
        s = long[long["coicop"] == code]
        return (s.groupby(["geo", "q"])["value"].mean().rename(name))
    head = cp("CP00", "headline_infl")
    nrg = cp("NRG", "energy_infl")
    return pd.concat([head, nrg], axis=1).reset_index()


def main():
    print("Building quarterly country panel ...")
    sav = saving_rate_panel();  print(f"  saving:     {len(sav):5d} rows, {sav['geo'].nunique()} geos")
    spr = spread_panel();       print(f"  spread:     {len(spr):5d} rows, {spr['geo'].nunique()} geos")
    sur = survey_panel();       print(f"  survey:     {len(sur):5d} rows, {sur['geo'].nunique()} geos")
    inf = inflation_panel();    print(f"  inflation:  {len(inf):5d} rows, {inf['geo'].nunique()} geos")

    panel = (sav.merge(spr, on=["geo", "q"], how="left")
                .merge(sur, on=["geo", "q"], how="left")
                .merge(inf, on=["geo", "q"], how="left"))
    panel = panel[panel["q"] >= pd.Period("2000Q1", freq="Q")].copy()
    panel["quarter"] = panel["q"].astype(str)
    panel = panel.sort_values(["geo", "q"])

    full = panel.dropna(subset=["saving", "spread", "sav_intent", "unemp_exp",
                                "headline_infl", "energy_infl"])
    print(f"\nPanel: {len(panel)} rows; complete-case {len(full)} rows, "
          f"{full['geo'].nunique()} countries, "
          f"{full['q'].min()}–{full['q'].max()}")
    out = panel[["geo", "quarter", "saving", "spread", "sav_intent", "unemp_exp",
                 "headline_infl", "energy_infl"]]
    path = os.path.join(DATA, "P_country_panel_quarterly.csv")
    out.to_csv(path, index=False)
    print(f"Wrote {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
