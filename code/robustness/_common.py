#!/usr/bin/env python3
"""
Shared helpers for the identification extensions
================================================

These scripts test the precautionary-saving hypothesis with stronger
identification than the aggregate time-series core (see ../03_econometrics.py).
They REUSE the CSVs already produced by ../01_collect_data.py (read from
../data) and pull only the few extra series each design needs, writing their own
outputs to extensions/data and extensions/figures so the main pipeline is left
untouched.

Run the main pipeline first (so ../data exists), then any extension script.
"""

import os
import re
import warnings
from io import StringIO, BytesIO

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import eurostat
except ImportError:
    eurostat = None  # only the Eurostat-based extensions need it

# ----------------------------------------------------------------------------
# Paths: read from the main project's ./data, write into extensions/{data,figures}
# ----------------------------------------------------------------------------
EXT_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(EXT_HERE)
ROOT_DATA = os.path.join(ROOT, "data")
DATA = os.path.join(EXT_HERE, "data")
FIG = os.path.join(EXT_HERE, "figures")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

START = "1999-01-01"

# Country set + editorial Russia/energy exposure (mirrors the main pipeline).
COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "FI", "IE", "PT", "EL",
             "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT", "SE", "DK"]
HIGH_EXPOSURE = {"DE", "AT", "FI", "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})

# A small consistent palette.
C_MAIN = "#1f4e79"
C_HOT = "#c0392b"
C_COOL = "#2e86c1"
C_ACCENT = "#6c3483"


# ----------------------------------------------------------------------------
# Network + Eurostat helpers
# ----------------------------------------------------------------------------
def http_get(url, timeout=60):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r


def es_long(code):
    """Fetch a Eurostat dataset tidy: dimension cols + 'time' + 'value'."""
    if eurostat is None:
        raise RuntimeError("eurostat package not installed (pip install eurostat)")
    df = eurostat.get_data_df(code)
    if df is None or df.empty:
        raise RuntimeError(f"Eurostat returned nothing for {code}")
    geo_col = next((c for c in df.columns if "geo" in c.lower()), None)
    if geo_col:
        df = df.rename(columns={geo_col: "geo"})
    time_cols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    id_cols = [c for c in df.columns if c not in time_cols]
    long = df.melt(id_vars=id_cols, value_vars=time_cols,
                   var_name="time", value_name="value")
    return long.dropna(subset=["value"])


def parse_time(s):
    """'2024', '2024-Q2'/'2024Q2', or '2024-06' -> sortable Timestamp."""
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


def show_dims(long, code, skip=("time", "value", "geo")):
    print(f"  [{code}] dimension values:")
    for d in [c for c in long.columns if c not in skip]:
        vals = sorted(str(v) for v in long[d].dropna().unique())[:25]
        print(f"    {d}: {vals}")


def get_fred_series(series_id, colname):
    """Keyless FRED CSV pull -> tidy [date, colname] (via requests/certifi)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(StringIO(http_get(url).text))
    datecol = "observation_date" if "observation_date" in df.columns else df.columns[0]
    df = df.rename(columns={datecol: "date", df.columns[-1]: colname})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[colname] = pd.to_numeric(df[colname], errors="coerce")
    return df.dropna().sort_values("date")[["date", colname]]


# ----------------------------------------------------------------------------
# Loaders for the main pipeline's ./data
# ----------------------------------------------------------------------------
def root_csv(name, required=True):
    """Read ../data/<name>. If required and missing, raise with guidance."""
    path = os.path.join(ROOT_DATA, name)
    if not os.path.exists(path):
        if required:
            raise SystemExit(
                f"Missing {os.path.relpath(path, EXT_HERE)} — run the main pipeline "
                f"first (python ../01_collect_data.py).")
        return None
    return pd.read_csv(path)


def load_quarterly(name, valcol):
    """Read a [date, value] CSV from ../data and return a quarterly-mean Series."""
    d = root_csv(name)
    d = d.rename(columns={d.columns[0]: "date"})
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    vc = valcol if valcol in d.columns else d.columns[1]
    d[vc] = pd.to_numeric(d[vc], errors="coerce")
    s = d.dropna(subset=["date", vc]).set_index("date")[vc].rename(valcol)
    return s.resample("QS").mean()


def load_country_saving_long():
    """../data/country_saving_annual.csv (geo x year pivot) -> long [geo, year, saving]."""
    piv = root_csv("country_saving_annual.csv")
    piv = piv.rename(columns={piv.columns[0]: "geo"}).set_index("geo")
    piv.columns = [int(float(c)) for c in piv.columns]
    long = (piv.reset_index()
               .melt(id_vars="geo", var_name="year", value_name="saving")
               .dropna(subset=["saving"]))
    long["year"] = long["year"].astype(int)
    return long


def zscore(s):
    s = s.astype(float)
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd else s * 0.0


def savefig(fig, name):
    out = os.path.join(FIG, name)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {os.path.relpath(out, ROOT)}")
