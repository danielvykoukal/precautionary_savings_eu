#!/usr/bin/env python3
"""
Shared helpers for the feedback extension
=========================================

This folder implements the supervisor feedback on the savings analysis. The
unifying move is to stop treating "cash + deposits" as the only precautionary
buffer and instead rank household assets on a LIQUIDITY / MATURITY ladder, then
layer risk-premia, forward-looking and energy-liquidity angles on top.

The helpers below are lifted from the proven main-project modules so the new
scripts reuse code rather than reinvent it:
  - es_long / parse_time / show_dims / get_fred_series / http_get / zscore /
    root_csv / load_quarterly / savefig / palette  -> ../extensions/_common.py
  - household_flows (Eurostat sector financial accounts)  -> ../extension_follow_money/_common.py

NEW here (needed for the feedback themes):
  - household_instruments(code, ...) : generalises household_flows to ANY sector
    financial-accounts dataset, so the SAME tier classification runs on flows
    (nasa_10_f_tr) and on stocks / balance sheets (nasa_10_f_bs).
  - ecb_sdmx(flow, key)              : keyless pull from the ECB Data Portal
    (data-api.ecb.europa.eu) for the monetary aggregates M1/M2/M3.

Each script reads the project's ../data (copied in alongside this folder) and
pulls only the few extra series it needs, writing outputs to ./data and
./figures so the rest of the project is untouched.
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
    eurostat = None  # only the Eurostat-based scripts need it

# ----------------------------------------------------------------------------
# Paths: read the main project's ../data, write into ./{data,figures}
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROOT_DATA = os.path.join(ROOT, "data")
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

START = "1999-01-01"

COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "FI", "IE", "PT", "EL",
             "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT", "SE", "DK"]
HIGH_EXPOSURE = {"DE", "AT", "FI", "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}

EA_GEOS = ("EA20", "EA19", "EA", "EU27_2020")

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})

# A small consistent palette (matches ../extensions/_common.py).
C_MAIN = "#1f4e79"
C_HOT = "#c0392b"
C_COOL = "#2e86c1"
C_ACCENT = "#6c3483"
C_GREEN = "#117a65"
C_ORANGE = "#e67e22"
C_GREY = "#7f8c8d"

# Tier colours for the liquidity ladder (T1 most liquid -> T4 least).
TIER_COLORS = {
    "T1 instant (cash, overnight)": C_COOL,
    "T2 near-money (term/notice, MMF)": C_GREEN,
    "T3 marketable (bonds, listed shares, funds)": C_ORANGE,
    "T4 illiquid (unlisted equity, insurance/pension)": C_HOT,
}


# ----------------------------------------------------------------------------
# Regime shading / annotation -- the project "house style". Three regimes:
#   ZLB / negative ECB rates : 2012-07 (deposit rate hits 0%) -> 27 Jul 2022 (1st hike)
#   COVID forced saving      : 2020
#   war + energy + ECB hikes : begins at the Feb-2022 invasion (so the dashed
#                              invasion line == the LEFT EDGE of the orange band)
# ----------------------------------------------------------------------------
ZLB_SPAN = ("2012-07-01", "2022-07-27")
COVID_SPAN = ("2020-02-01", "2020-12-31")
INVASION = "2022-02-24"
ENERGY_SPAN = (INVASION, "2023-12-31")


def _xpos(ts, year_axis):
    """Map a date to the x-axis: a Timestamp, or a fractional year if year_axis."""
    t = pd.Timestamp(ts)
    return (t.year + (t.dayofyear - 1) / 365.25) if year_axis else t


def mark_periods(ax, year_axis=False, shade=True, invasion=True, labels=True, zlb=True):
    """Shade the three regimes and mark the Feb-2022 invasion. The invasion dashed
    line coincides with the left edge of the war/energy band by construction, so
    the line and the orange shading line up. Works on a datetime or integer-year
    (year_axis=True) axis; call AFTER plotting (it reads the y-limits for labels).
    For stacked-area charts pass shade=False (the stack hides the fills); the
    invasion line + labels still draw."""
    if shade:
        if zlb:
            ax.axvspan(_xpos(ZLB_SPAN[0], year_axis), _xpos(ZLB_SPAN[1], year_axis),
                       color="#6c5ce7", alpha=0.06, zorder=0)
        ax.axvspan(_xpos(COVID_SPAN[0], year_axis), _xpos(COVID_SPAN[1], year_axis),
                   color="#5d6d7e", alpha=0.14, zorder=0)
        ax.axvspan(_xpos(ENERGY_SPAN[0], year_axis), _xpos(ENERGY_SPAN[1], year_axis),
                   color=C_ORANGE, alpha=0.10, zorder=0)
    if invasion:
        ax.axvline(_xpos(INVASION, year_axis), color="#7b241c", ls="--", lw=1.1, zorder=3)
    if labels:
        top = ax.get_ylim()[1]
        if zlb:
            ax.text(_xpos("2016-09-01", year_axis), top, "ZLB / negative ECB rates",
                    ha="center", va="top", fontsize=7.5, color="#5b4bbf")
        ax.text(_xpos("2020-07-01", year_axis), top, "COVID\n(forced saving)",
                ha="center", va="top", fontsize=7.5, color="#5d6d7e")
        ax.text(_xpos("2022-11-15", year_axis), top, "war + energy\n+ ECB hikes",
                ha="center", va="top", fontsize=7.5, color="#a04000")
    # every year on the x-axis (rotated), so no years are hidden
    import matplotlib.ticker as _mtick
    import matplotlib.dates as _mdates
    if year_axis:
        ax.xaxis.set_major_locator(_mtick.MultipleLocator(1))
    else:
        ax.xaxis.set_major_locator(_mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(_mdates.DateFormatter("%Y"))
    for _lb in ax.get_xticklabels():
        _lb.set_rotation(45)
        _lb.set_fontsize(8)
    return ax


def caveat(fig, text):
    """Small italic footnote, bottom-left (2w report style)."""
    fig.text(0.01, 0.005, text, fontsize=7.5, style="italic", color="#555")


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
    """Keyless FRED CSV pull -> tidy [date, colname] (requests/certifi)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(StringIO(http_get(url).text))
    datecol = "observation_date" if "observation_date" in df.columns else df.columns[0]
    df = df.rename(columns={datecol: "date", df.columns[-1]: colname})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[colname] = pd.to_numeric(df[colname], errors="coerce")
    return df.dropna().sort_values("date")[["date", colname]]


def ecb_sdmx(flow, key, start="1999-01"):
    """Keyless pull from the ECB Data Portal SDMX API -> tidy [date, value].

    flow : dataflow id, e.g. 'BSI' (balance-sheet items / monetary aggregates).
    key  : the series key WITHOUT the flow prefix, e.g.
           'M.U2.Y.V.M30.X.1.U2.2300.Z01.E' (M3, index of notional stock).
    The API returns SDMX-CSV with TIME_PERIOD / OBS_VALUE columns.
    """
    base = "https://data-api.ecb.europa.eu/service/data"
    url = f"{base}/{flow}/{key}?format=csvdata&startPeriod={start}"
    df = pd.read_csv(StringIO(http_get(url).text))
    up = {c.upper(): c for c in df.columns}
    tcol, vcol = up.get("TIME_PERIOD"), up.get("OBS_VALUE")
    if not (tcol and vcol):
        raise RuntimeError(f"ECB SDMX {flow}/{key}: TIME_PERIOD/OBS_VALUE not in "
                           f"{list(df.columns)}")
    out = df[[tcol, vcol]].rename(columns={tcol: "time", vcol: "value"})
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out["date"] = out["time"].map(parse_time)
    return out.dropna(subset=["date", "value"]).sort_values("date")[["date", "value"]]


# ----------------------------------------------------------------------------
# Sector financial accounts: works for flows (nasa_10_f_tr) AND stocks (nasa_10_f_bs)
# ----------------------------------------------------------------------------
def household_instruments(code, finpos=("ASS", "A", "LE")):
    """Euro-area HOUSEHOLD financial position by instrument, tidy
    [year, na_item, value(EUR mn)] + geo.

    code   : 'nasa_10_f_tr' (transactions / net flows) or 'nasa_10_f_bs'
             (balance sheet / outstanding stocks). Same dimension structure.
    finpos : preferred codes for the assets side (ESA: ASS = financial assets).

    Mirrors the selection logic of the original household_flows(): household
    sector S14(_S15), non-consolidated, assets side, current-price millions, one
    euro-area aggregate geo. Prints the dataset dimensions so a changed code is
    visible.
    """
    long = es_long(code)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    show_dims(long, code)
    if "sector" in long.columns:
        sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
        if sec is None:
            raise RuntimeError(f"{code}: household sector S14/S14_S15 not found")
        long = long[long["sector"] == sec]
    if "co_nco" in long.columns:
        for cc in ("NCO", "CO"):
            if cc in set(long["co_nco"]):
                long = long[long["co_nco"] == cc]
                break
    if "finpos" in long.columns:
        for fp in finpos:
            if fp in set(long["finpos"]):
                long = long[long["finpos"] == fp]
                break
    if "unit" in long.columns:
        for u in ("MIO_EUR", "CP_MEUR", "MIO_NAC"):
            if u in set(long["unit"]):
                long = long[long["unit"] == u]
                break
    geo = next((g for g in EA_GEOS if g in set(long["geo"])), None)
    if geo is None:
        raise RuntimeError(f"{code}: no euro-area aggregate geo found")
    long = long[long["geo"] == geo]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    return long[["year", "na_item", "value"]], geo


def household_flows():
    """Back-compatible alias: household net acquisition of financial assets
    (Eurostat nasa_10_f_tr), tidy [year, na_item, value] + geo."""
    return household_instruments("nasa_10_f_tr")


# ----------------------------------------------------------------------------
# Loaders for the project's ../data
# ----------------------------------------------------------------------------
def root_csv(name, required=True):
    """Read ../data/<name>. If required and missing, raise with guidance."""
    path = os.path.join(ROOT_DATA, name)
    if not os.path.exists(path):
        if required:
            raise SystemExit(
                f"Missing {os.path.relpath(path, HERE)} — run the main pipeline "
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


def annual_mean(name, valcol):
    """Read a [date, value] CSV from ../data -> Series indexed by year (annual mean)."""
    s = load_quarterly(name, valcol)
    out = s.groupby(s.index.year).mean()
    out.index.name = "year"
    return out.rename(valcol)


def zscore(s):
    s = s.astype(float)
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd else s * 0.0


def savefig(fig, name):
    out = os.path.join(FIG, name)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {os.path.relpath(out, ROOT)}")
