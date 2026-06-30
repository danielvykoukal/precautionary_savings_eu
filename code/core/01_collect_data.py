#!/usr/bin/env python3
"""
Precautionary saving in Europe — STEP 1: data collection
========================================================

Pulls and cleans every series the project needs and writes tidy CSVs to ./data.
It produces NO plots and runs NO econometrics — that is 02_make_figures.py and
03_econometrics.py respectively. Run this first.

Sources (all free, no API key):
  - Eurostat household saving rate: euro-area quarterly (nasq_10_ki) +
    by-country annual (tec00131)
  - Eurostat HICP inflation (prc_hicp_manr): headline (confound) + energy (shock)
  - Eurostat ICW experimental: median saving rate by income quintile (icw_sr_03)
  - OECD EG DNA: annual saving rate by income quintile, per country (SDMX API)
  - FRED Economic Policy Uncertainty for Europe (EUEPUINDXM) + an ECB/short rate
  - Geopolitical Risk index (Caldara & Iacoviello, keyless .xls)

Outputs (./data/*.csv):
  ea_saving_rate_quarterly.csv   country_saving_annual.csv
  fred_eu_epu.csv  gpr.csv       country_energy_peak_2022.csv
  ecb_rate.csv  ea_inflation.csv scatter_energy_vs_saving.csv
  saving_rate_by_quintile.csv    icw_quintile_panel.csv
  ces_unemp_expectations.csv     oecd_quintile_panel_<CC>.csv (if OECD responds)

Run
---
    pip install -r requirements.txt
    python 01_collect_data.py

Notes
-----
- Network downloads go through `requests` (which bundles CA certs via certifi).
  pandas' own URL reader uses urllib, which fails with SSL CERTIFICATE_VERIFY
  errors on a stock macOS Python — hence the explicit `requests` calls here.
- Each section is wrapped in try/except: if one source is down or a dataset code
  changes, the rest still run. Failures print a clear message, and any existing
  CSV from a previous run is left untouched.
"""

import os
import re
import sys
import warnings
from io import StringIO, BytesIO

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import requests

try:
    import eurostat
except ImportError:
    sys.exit("Missing 'eurostat'. Run: pip install -r requirements.txt")

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

# How far back to keep (the long saving-rate series starts 1999Q1).
START = "1999-01-01"

# Euro-area aggregate code differs across vintages (EA19/EA20/EA). We try each
# and keep whichever has the longest coverage.
EA_CODES = ["EA20", "EA19", "EA", "EU27_2020"]

# Country set for the cross-section (ISO2 / Eurostat geo codes)
COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "FI", "IE", "PT", "EL",
             "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT", "SE", "DK"]

# Browser-like header; some endpoints (notably OECD SDMX) reject default agents.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}


def _http_get(url, timeout=60):
    """GET via requests (certifi CA bundle) -> Response, raising on HTTP error."""
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r


# ----------------------------------------------------------------------------
# Eurostat helpers
# ----------------------------------------------------------------------------
def es_long(code):
    """Fetch a Eurostat dataset and return it tidy: dimension cols + time + value."""
    df = eurostat.get_data_df(code)
    if df is None or df.empty:
        raise RuntimeError(f"Eurostat returned nothing for {code}")
    # geo column is named e.g. 'geo\\TIME_PERIOD' or 'geo\\time'
    geo_col = next((c for c in df.columns if "geo" in c.lower()), None)
    if geo_col:
        df = df.rename(columns={geo_col: "geo"})
    # time columns look like a year (2024) or a period (2024-Q2 / 2024Q2 / 2024-06)
    time_cols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    id_cols = [c for c in df.columns if c not in time_cols]
    long = df.melt(id_vars=id_cols, value_vars=time_cols,
                   var_name="time", value_name="value")
    long = long.dropna(subset=["value"])
    return long


def parse_time(s):
    """Parse '2024', '2024-Q2'/'2024Q2', or '2024-06' to a sortable timestamp."""
    s = str(s)
    m = re.match(r"^(\d{4})[-_ ]?Q([1-4])$", s)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return pd.Timestamp(year=y, month=(q - 1) * 3 + 1, day=1)
    m = re.match(r"^(\d{4})[-_ ](\d{2})$", s)
    if m:
        return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=1)
    m = re.match(r"^(\d{4})$", s)
    if m:
        return pd.Timestamp(year=int(m.group(1)), month=1, day=1)
    return pd.NaT


def show_dims(long, code, dims):
    """Print available codes for given dimensions to help debugging filters."""
    print(f"  [{code}] dimension values:")
    for d in dims:
        if d in long.columns:
            vals = sorted(long[d].dropna().unique().tolist())[:25]
            print(f"    {d}: {vals}")


# ----------------------------------------------------------------------------
# 1) Euro-area saving rate (quarterly)
# ----------------------------------------------------------------------------
SAVING_BAND = (5.0, 30.0)  # plausible household gross saving rate (% of disp. income)


def _best_saving_series(sub):
    """From a tidy frame already restricted to ONE euro-area geo, return
    (combo, series) for the single dimension-combination that is the household
    gross saving rate.

    Why this exists: an earlier version filtered on na_item=='SRG' and, when that
    code wasn't present, silently kept *every* key-indicator ratio (saving rate,
    investment rate, profit share, ...) and averaged them. The blend landed near
    ~35%, nonsense for a household saving rate. Here we NEVER average across
    indicators -- we pick one real series, preferring a saving-named na_item and a
    level that looks like a saving rate.
    """
    dimcols = [c for c in sub.columns if c not in ("time", "value", "geo", "date")]
    groups = sub.groupby(dimcols) if dimcols else [((), sub)]
    cands = []
    for combo, g in groups:
        s = g.dropna(subset=["date", "value"]).sort_values("date")
        if s.empty:
            continue
        # a genuine single series has ~one observation per period
        if s["date"].duplicated().mean() > 0.05:
            continue
        med = float(s["value"].median())
        if not (SAVING_BAND[0] <= med <= SAVING_BAND[1]):
            continue
        combo_t = combo if isinstance(combo, tuple) else (combo,)
        combo_str = " ".join(str(x) for x in combo_t).upper()
        is_saving = any(k in combo_str for k in ("SR", "SAV", "B8"))
        # prefer saving-named, then the level closest to a typical ~13% rate,
        # then the longest series.
        cands.append((is_saving, -abs(med - 13.0), len(s), combo_t, s[["date", "value"]]))
    if not cands:
        return None
    cands.sort(key=lambda c: (c[0], c[1], c[2]), reverse=True)
    return cands[0][3], cands[0][4]


def get_ea_saving_quarterly():
    """Long quarterly euro-area household gross saving rate (back to 1999Q1).

    Tries the current Eurostat sector-account datasets in turn, auto-detects the
    single household-saving-rate series (no blending), and refuses any result
    whose level is implausible for a household saving rate.
    """
    last_err = None
    for code in ("nasq_10_ki", "nasa_10_ki", "teina500"):
        try:
            long = es_long(code)
        except Exception as e:
            last_err = e
            print(f"  {code} unavailable ({e}); trying next dataset")
            continue

        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["date"] = long["time"].map(parse_time)
        long = long.dropna(subset=["value", "date"])
        show_dims(long, code,
                  [c for c in long.columns if c not in ("time", "value", "geo", "date")])

        # choose a euro-area aggregate geo
        ea_geo = next((g for g in EA_CODES if g in set(long["geo"])), None) \
            or next((g for g in long["geo"].unique() if str(g).startswith(("EA", "EU"))), None)
        if ea_geo is None:
            print(f"  {code}: no EA/EU aggregate; trying next dataset")
            continue
        sub = long[long["geo"] == ea_geo].copy()

        # narrow to the household sector and seasonally-adjusted data if those
        # dimensions exist (helps disambiguate; the selection below is the guard)
        if "sector" in sub.columns:
            for sec in ("S14_S15", "S14"):
                if sec in set(sub["sector"]):
                    sub = sub[sub["sector"] == sec]
                    break
        if "s_adj" in sub.columns:
            for sa in ("SCA", "SA"):
                if sa in set(sub["s_adj"]):
                    sub = sub[sub["s_adj"] == sa]
                    break

        picked = _best_saving_series(sub)
        if picked is None:
            print(f"  {code}: no series with a plausible saving-rate level; trying next")
            continue
        combo, ea = picked
        ea = ea.sort_values("date")
        ea = ea[ea["date"] >= START]
        med = float(ea["value"].median())
        if not (SAVING_BAND[0] <= med <= SAVING_BAND[1]):
            print(f"  {code}: selected level implausible (median {med:.1f}%); trying next")
            continue
        print(f"  saving rate from {code}, geo={ea_geo}, series={combo}: "
              f"{len(ea)} obs, median {med:.1f}%, "
              f"{ea['date'].min().date()} -> {ea['date'].max().date()}")
        ea.to_csv(os.path.join(DATA, "ea_saving_rate_quarterly.csv"), index=False)
        return ea

    raise RuntimeError(
        "Could not obtain a plausible euro-area household saving rate from any "
        f"candidate dataset (nasq_10_ki / nasa_10_ki / teina500). Last error: {last_err}")


# ----------------------------------------------------------------------------
# 2) Uncertainty proxies + confounds (rate, inflation)
# ----------------------------------------------------------------------------
def get_fred_series(series_id, colname):
    """Generic keyless FRED CSV pull -> tidy [date, colname]."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(StringIO(_http_get(url).text))
    datecol = "observation_date" if "observation_date" in df.columns else df.columns[0]
    df = df.rename(columns={datecol: "date", df.columns[-1]: colname})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[colname] = pd.to_numeric(df[colname], errors="coerce")
    df = df.dropna().sort_values("date")
    return df[df["date"] >= START][["date", colname]]


def get_fred_eu_epu():
    df = get_fred_series("EUEPUINDXM", "epu")
    df.to_csv(os.path.join(DATA, "fred_eu_epu.csv"), index=False)
    return df


def get_gpr():
    """Caldara-Iacoviello Geopolitical Risk index (monthly). Keyless .xls."""
    url = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
    df = pd.read_excel(BytesIO(_http_get(url).content))
    # date column is 'month' (datetime). Index is 'GPR'.
    datecol = next((c for c in df.columns if str(c).lower() in ("month", "date")), df.columns[0])
    gprcol = "GPR" if "GPR" in df.columns else next((c for c in df.columns if str(c).upper().startswith("GPR")), None)
    df = df[[datecol, gprcol]].rename(columns={datecol: "date", gprcol: "gpr"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna().sort_values("date")
    df = df[df["date"] >= START]
    df.to_csv(os.path.join(DATA, "gpr.csv"), index=False)
    return df


def get_ecb_rate():
    """A euro-area short / policy rate, monthly. Tries a few keyless FRED IDs:
    ECB deposit facility rate, main refinancing rate, then 3-month interbank."""
    for sid in ("ECBDFR", "ECBMRRFR", "IR3TIB01EZM156N"):
        try:
            df = get_fred_series(sid, "rate")
            if len(df) > 24:
                df.to_csv(os.path.join(DATA, "ecb_rate.csv"), index=False)
                print(f"  policy/short rate from FRED {sid}: {len(df)} obs")
                return df
        except Exception as e:
            print(f"  FRED {sid} failed ({e})")
    raise RuntimeError("No euro-area rate series available from FRED")


def get_ea_inflation():
    """Euro-area headline HICP inflation, YoY %, monthly (Eurostat prc_hicp_manr,
    COICOP all-items CP00)."""
    long = es_long("prc_hicp_manr")
    if "coicop" in long.columns and "CP00" in set(long["coicop"]):
        long = long[long["coicop"] == "CP00"]
    geo = next((g for g in ("EA20", "EA19", "EA") if g in set(long["geo"])), None) \
        or next((g for g in long["geo"].unique() if str(g).startswith("EA")), None)
    long = long[long["geo"] == geo]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["date"] = long["time"].map(parse_time)
    df = (long.dropna(subset=["value", "date"]).sort_values("date")[["date", "value"]]
          .rename(columns={"value": "inflation"}))
    df = df[df["date"] >= START]
    df.to_csv(os.path.join(DATA, "ea_inflation.csv"), index=False)
    print(f"  EA HICP inflation (CP00, geo={geo}): {len(df)} obs")
    return df


# ----------------------------------------------------------------------------
# 3) Cross-country: saving level + energy shock + their join (scatter)
# ----------------------------------------------------------------------------
def get_country_saving_annual():
    long = es_long("tec00131")
    show_dims(long, "tec00131", [c for c in long.columns if c not in ("time", "value", "geo")])
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long[long["geo"].isin(COUNTRIES)]
    piv = long.pivot_table(index="geo", columns="year", values="value", aggfunc="mean")
    piv.to_csv(os.path.join(DATA, "country_saving_annual.csv"))
    return piv


def get_country_energy_shock():
    """Peak monthly HICP energy inflation by country during 2022 (the shock)."""
    long = es_long("prc_hicp_manr")
    # Filter to energy ('NRG') COICOP code.
    if "coicop" in long.columns:
        if "NRG" in set(long["coicop"]):
            long = long[long["coicop"] == "NRG"]
        else:
            raise RuntimeError("Cannot find 'NRG' (energy) in 'coicop' dimension of prc_hicp_manr.")
    long["date"] = long["time"].map(parse_time)
    long = long[(long["date"] >= "2022-01-01") & (long["date"] <= "2022-12-31")]
    long = long[long["geo"].isin(COUNTRIES)]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    peak = long.groupby("geo")["value"].max()
    peak.to_csv(os.path.join(DATA, "country_energy_peak_2022.csv"))
    return peak


def build_energy_saving_scatter(saving_piv, energy_peak):
    """Join: per country, rise in saving (2019 -> avg 2023/24) vs peak 2022 energy
    inflation. This is the data behind chart B; computing it here keeps 02 a pure
    renderer."""
    yrs = saving_piv.columns
    base = 2019.0 if 2019.0 in yrs else min(yrs)
    recent = [y for y in (2024.0, 2023.0) if y in yrs]
    if not recent:
        recent = [max(yrs)]
    rise = saving_piv[recent].mean(axis=1) - saving_piv[base]
    df = pd.DataFrame({"rise": rise, "energy": energy_peak}).dropna()
    df.to_csv(os.path.join(DATA, "scatter_energy_vs_saving.csv"))
    return df


# ----------------------------------------------------------------------------
# 4) Distribution: saving rate by income quintile (Eurostat ICW, experimental)
#    Reference years ~2010/2015/2020 (compiled ~every 5 yrs) — STRUCTURAL.
# ----------------------------------------------------------------------------
GEO_PREF = ["EA20", "EA19", "EA", "EU27_2020", "EU28", "DE", "FR", "IT", "ES"]


def _detect_quintile_col(long):
    """Return the column whose values look like income-quintile codes."""
    for c in long.columns:
        if c in ("time", "value", "geo"):
            continue
        vals = [str(v).upper() for v in long[c].dropna().unique()]
        if any(re.search(r"(QU?[1-5])|QUINT|^Q[1-5]$|D[1-9]0?", v) for v in vals):
            return c
    return None


def _quintile_num(code):
    m = re.search(r"([1-5])", str(code))
    return int(m.group(1)) if m else 99


def get_saving_by_quintile():
    """Latest ICW snapshot: median saving rate by quintile for one geography."""
    long = es_long("icw_sr_03")
    show_dims(long, "icw_sr_03",
              [c for c in long.columns if c not in ("time", "value", "geo")])
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    qcol = _detect_quintile_col(long)
    if qcol is None:
        raise RuntimeError("Could not detect the income-quintile dimension in icw_sr_03 "
                           "(check the printed dimension values and set it manually)")
    # keep only quintile rows (drop TOTAL etc.)
    long = long[long[qcol].astype(str).str.upper().str.contains(r"QU?[1-5]|^Q[1-5]$|QUINT", regex=True)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    latest = long["year"].max()
    sub = long[long["year"] == latest]
    geo = next((g for g in GEO_PREF if g in set(sub["geo"])), None)
    if geo is None:  # fall back to whichever geo has all 5 quintiles
        counts = sub.groupby("geo")[qcol].nunique()
        geo = counts.idxmax()
    sub = sub[sub["geo"] == geo].copy()
    sub["q"] = sub[qcol].map(_quintile_num)
    out = sub.groupby("q", as_index=False)["value"].mean().sort_values("q")
    out["geo"] = geo
    out["year"] = int(latest)
    out.to_csv(os.path.join(DATA, "saving_rate_by_quintile.csv"), index=False)
    print(f"  saving rate by quintile from icw_sr_03: geo={geo}, year~{int(latest)}")
    return out


def get_icw_panel(geo_pref=GEO_PREF):
    """Saving rate by quintile across ALL ICW reference years (~2010/2015/2020)
    for one geography. The geo is stored in the CSV so 02 can label the chart."""
    long = es_long("icw_sr_03")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    qcol = _detect_quintile_col(long)
    if qcol is None:
        raise RuntimeError("icw_sr_03: quintile dimension not found")
    long = long[long[qcol].astype(str).str.upper().str.contains(
        r"QU?[1-5]|^Q[1-5]$|QUINT", regex=True)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    geo = next((g for g in geo_pref if g in set(long["geo"])), None)
    if geo is None:
        geo = long.groupby("geo")[qcol].nunique().idxmax()
    sub = long[long["geo"] == geo].copy()
    sub["q"] = sub[qcol].map(_quintile_num)
    sub = sub[sub["q"].between(1, 5)]
    panel = sub.groupby(["year", "q"], as_index=False)["value"].mean()
    panel["geo"] = geo
    panel.to_csv(os.path.join(DATA, "icw_quintile_panel.csv"), index=False)
    return panel


# --- ECB CES unemployment expectations by income group (published figures) ----
# These are NOT in the Eurostat bulk API; they are published ECB Consumer
# Expectations Survey aggregates. Refresh from the latest CES release before
# publishing. Source: ECB CES, expected unemployment rate 12 months ahead.
CES_UNEMP_EXPECT = {  # income group -> expected unemployment rate 12m ahead (%)
    "Lowest quintile": 13.2,
    "Q2": 12.0,
    "Q3": 11.0,
    "Q4": 10.0,
    "Highest quintile": 9.4,
}


def write_ces_expectations():
    df = pd.DataFrame({"group": list(CES_UNEMP_EXPECT.keys()),
                       "expected_unemployment": list(CES_UNEMP_EXPECT.values())})
    df.to_csv(os.path.join(DATA, "ces_unemp_expectations.csv"), index=False)
    print("  wrote ces_unemp_expectations.csv (hardcoded ECB CES figures — verify)")
    return df


# ----------------------------------------------------------------------------
# 5) OECD EG DNA: annual saving rate by income quintile (per country)
#    Flow id from the OECD Data Explorer (Expert Group on Distributional NA).
#    If a pull returns nothing, confirm the flow id at https://data-explorer.oecd.org
# ----------------------------------------------------------------------------
OECD_AGENCY = "OECD.SDD.NAD"
OECD_FLOW = "DSD_EGDNA_INC_HHT@DF_INC_HHT"   # candidate flow (household income & saving)
OECD_VERSION = ""                            # blank -> latest
OECD_COUNTRIES = ["DEU", "FRA", "ITA", "ESP"]


def _parse_oecd(df, country):
    """Turn an OECD SDMX-CSV frame into panel[year,q,value] for one country.
    Robust to column naming: finds TIME_PERIOD / OBS_VALUE / REF_AREA, the
    quintile dimension (by value pattern), and a saving-rate measure if present.
    """
    up = {c.upper(): c for c in df.columns}
    tcol = up.get("TIME_PERIOD")
    vcol = up.get("OBS_VALUE")
    rcol = up.get("REF_AREA") or up.get("COU") or up.get("LOCATION")
    if not (tcol and vcol):
        raise RuntimeError(f"OECD: TIME_PERIOD/OBS_VALUE not found in {list(df.columns)}")
    df = df.copy()
    df[vcol] = pd.to_numeric(df[vcol], errors="coerce")
    if rcol is not None and country:
        df = df[df[rcol].astype(str).str.upper() == country.upper()]
    if df.empty:
        raise RuntimeError(f"OECD: no rows for {country}")
    # quintile dimension: a column whose values look like quintiles
    qcol = None
    for c in df.columns:
        if c in (tcol, vcol):
            continue
        vals = [str(v).upper() for v in list(df[c].dropna().unique())[:80]]
        if any(re.search(r"QUINT|\bQU?[1-5]\b|_Q[1-5]\b|QUANTILE|QTL", v) for v in vals):
            qcol = c
            break
    if qcol is None:
        raise RuntimeError("OECD: quintile dimension not found — inspect printed columns")
    # if a measure/transaction dim names a saving rate, keep only that
    for c in df.columns:
        vals = [str(v).upper() for v in df[c].dropna().unique()]
        if any(("SAV" in v) and ("RAT" in v) for v in vals):
            mask = (df[c].astype(str).str.upper().str.contains("SAV")
                    & df[c].astype(str).str.upper().str.contains("RAT"))
            if mask.any():
                df = df[mask]
            break
    df["q"] = df[qcol].map(_quintile_num)
    df = df[df["q"].between(1, 5)]
    df["year"] = df[tcol].astype(str).str.extract(r"(\d{4})").astype(float)
    panel = (df.groupby(["year", "q"], as_index=False)[vcol]
             .mean().rename(columns={vcol: "value"}))
    return panel


def get_oecd_quintile_panel(country, start=2007):
    base = "https://sdmx.oecd.org/public/rest/data/"
    url = (f"{base}{OECD_AGENCY},{OECD_FLOW},{OECD_VERSION}/all"
           f"?startPeriod={start}&dimensionAtObservation=AllDimensions"
           f"&format=csvfilewithlabels")
    try:
        res = _http_get(url)
        df = pd.read_csv(StringIO(res.text))
        print(f"  [OECD {country}] columns: {list(df.columns)[:18]}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"OECD request failed for {country}: {e}") from e
    panel = _parse_oecd(df, country)
    panel.to_csv(os.path.join(DATA, f"oecd_quintile_panel_{country}.csv"), index=False)
    return panel


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    print("=" * 64)
    print("STEP 1 — collecting data into ./data")
    print("=" * 64)

    print("\n[1] FRED EU Economic Policy Uncertainty ...")
    try:
        epu = get_fred_eu_epu()
        print(f"  ok: {len(epu)} obs, latest {epu['date'].max().date()}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[2] Geopolitical Risk index (Iacoviello) ...")
    try:
        gpr = get_gpr()
        print(f"  ok: {len(gpr)} obs, latest {gpr['date'].max().date()}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[3] Confounds: ECB/short rate (FRED) + EA HICP inflation (Eurostat) ...")
    try:
        get_ecb_rate()
    except Exception as e:
        print(f"  rate FAILED: {e}")
    try:
        get_ea_inflation()
    except Exception as e:
        print(f"  inflation FAILED: {e}")

    print("\n[4] Euro-area quarterly saving rate (Eurostat nasq_10_ki) ...")
    try:
        ea = get_ea_saving_quarterly()
        print(f"  ok: {len(ea)} quarters, latest {ea['date'].max().date()} = {ea['value'].iloc[-1]:.1f}%")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[5] Saving rate by country (Eurostat tec00131) ...")
    saving_piv = None
    try:
        saving_piv = get_country_saving_annual()
        print(f"  ok: {saving_piv.shape[0]} countries, years {list(saving_piv.columns)}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[6] Energy price shock by country (Eurostat prc_hicp_manr) ...")
    energy_peak = None
    try:
        energy_peak = get_country_energy_shock()
        print(f"  ok: peak 2022 energy inflation for {len(energy_peak)} countries")
    except Exception as e:
        print(f"  FAILED: {e}")

    if saving_piv is not None and energy_peak is not None:
        print("\n[6b] Building energy-vs-saving scatter dataset ...")
        try:
            df = build_energy_saving_scatter(saving_piv, energy_peak)
            print(f"  ok: {len(df)} countries in scatter_energy_vs_saving.csv")
        except Exception as e:
            print(f"  FAILED: {e}")

    print("\n[7] Distribution: saving rate by income quintile (Eurostat icw_sr_03) ...")
    try:
        get_saving_by_quintile()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[8] Distribution over time — Eurostat ICW snapshots ...")
    try:
        panel = get_icw_panel()
        print(f"  ok: {panel['year'].nunique()} reference years, geo={panel['geo'].iloc[0]}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[9] ECB CES unemployment expectations by income (published figures) ...")
    try:
        write_ces_expectations()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[10] Distribution over time — OECD annual by quintile ...")
    for c in OECD_COUNTRIES:
        try:
            panel = get_oecd_quintile_panel(c)
            print(f"  {c}: {'no data returned' if panel.empty else str(len(panel)) + ' rows'}")
        except Exception as e:
            print(f"  {c} FAILED: {e}")

    print("\nDone. CSVs written to ./data — now run 02_make_figures.py")


if __name__ == "__main__":
    main()
