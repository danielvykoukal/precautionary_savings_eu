#!/usr/bin/env python3
"""
Shared helpers for the "follow the money" extension
===================================================

These two scripts ask whether the post-2022 rise in euro-area saving looks more
like *yield-chasing* (money moving into higher-paying, less-liquid assets as the
ECB raised rates) than *precaution* (money parked in instant-access cash). They
reuse the main pipeline's ../data and pull one extra Eurostat dataset, writing
outputs into this folder's data/ and figures/.

Run the main pipeline first so ../data exists.
"""

import os
import re
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import eurostat
except ImportError:
    eurostat = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROOT_DATA = os.path.join(ROOT, "data")
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

START = "1999-01-01"

# palette
C_NAVY = "#1f4e79"
C_RED = "#c0392b"
C_BLUE = "#2e86c1"
C_ORANGE = "#e67e22"
C_PURPLE = "#6c3483"
C_GREY = "#7f8c8d"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})


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


def show_dims(long, code, skip=("time", "value", "geo")):
    print(f"  [{code}] dimension values:")
    for d in [c for c in long.columns if c not in skip]:
        vals = sorted(str(v) for v in long[d].dropna().unique())[:25]
        print(f"    {d}: {vals}")


def root_csv(name, required=True):
    """Read ../data/<name>; raise (or None) if missing."""
    path = os.path.join(ROOT_DATA, name)
    if not os.path.exists(path):
        if required:
            raise SystemExit(
                f"Missing {os.path.relpath(path, HERE)} — run the main pipeline "
                f"first (python ../01_collect_data.py).")
        return None
    return pd.read_csv(path)


def load_quarterly(name, valcol):
    """Read a [date, value] CSV from ../data -> quarterly-mean Series."""
    d = root_csv(name)
    d = d.rename(columns={d.columns[0]: "date"})
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    vc = valcol if valcol in d.columns else d.columns[1]
    d[vc] = pd.to_numeric(d[vc], errors="coerce")
    s = d.dropna(subset=["date", vc]).set_index("date")[vc].rename(valcol)
    return s.resample("QS").mean()


def household_flows():
    """Euro-area household net acquisition of financial assets, tidy
    [year, na_item, value(EUR mn)] + geo. Source: Eurostat nasa_10_f_tr, sector
    S14(_S15), assets side, non-consolidated, current-price millions."""
    long = es_long("nasa_10_f_tr")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    if "sector" in long.columns:
        sec = next((s for s in ("S14_S15", "S14") if s in set(long["sector"])), None)
        if sec is None:
            raise RuntimeError("nasa_10_f_tr: household sector S14/S14_S15 not found")
        long = long[long["sector"] == sec]
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
    geo = next((g for g in ("EA20", "EA19", "EA", "EU27_2020")
                if g in set(long["geo"])), None)
    if geo is None:
        raise RuntimeError("nasa_10_f_tr: no euro-area aggregate geo")
    long = long[long["geo"] == geo]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long.dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    return long[["year", "na_item", "value"]], geo


def annual_mean(name, valcol):
    """Read a [date, value] CSV from ../data -> Series indexed by year (annual mean)."""
    s = load_quarterly(name, valcol)
    out = s.groupby(s.index.year).mean()
    out.index.name = "year"
    return out.rename(valcol)


def savefig(fig, name):
    out = os.path.join(FIG, name)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {os.path.relpath(out, ROOT)}")
