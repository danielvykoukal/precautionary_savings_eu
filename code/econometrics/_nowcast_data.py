#!/usr/bin/env python3
"""Shared data loader for the saving-rate nowcast (bridge + MFDFM).

Target  : quarterly euro-area household saving rate.
Monthly leads (EA-aggregate): saving intentions, unemployment expectations,
M1 & M3 year-on-year growth, GPR, EPU, ECB rate.
"""

import os
import re
import pandas as pd

try:
    import eurostat
except ImportError:
    eurostat = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")

PRED_LABELS = {
    "sav_intent": "Saving intentions",
    "unemp_exp": "Unemployment expectations",
    "m1_growth": "M1 growth (YoY)",
    "m3_growth": "M3 growth (YoY)",
    "gpr": "Geopolitical risk (GPR)",
    "epu": "Economic policy uncertainty",
    "rate": "ECB / short rate",
    "retail_growth": "Retail sales volume (YoY)",
}


def _read(name):
    return pd.read_csv(os.path.join(DATA, name))


def _monthly(df, datecol="date"):
    df = df.copy()
    df[datecol] = pd.to_datetime(df[datecol]).dt.to_period("M").dt.to_timestamp()
    return df.set_index(datecol)


def monthly_predictors(include_retail=False):
    """Monthly DataFrame of standardisable leads, indexed by month-start.

    include_retail: add Eurostat retail-sales volume YoY as a hard consumption lead.
    Tested and left OFF by default — it is goods-only, redundant with the saving-
    intentions survey, and silent on the income side, so it adds no skill (and
    overfits the bridge). See `retail_growth()`.
    """
    si = _monthly(_read("E_saving_intentions.csv"))
    si = si.rename(columns={"savings": "sav_intent", "unemployment": "unemp_exp"})

    ms = _monthly(_read("H_money_supply_levels.csv")).sort_index()
    ms = ms.resample("MS").mean()
    m1g = (ms["M1"].pct_change(12) * 100).rename("m1_growth")
    m3g = (ms["M3"].pct_change(12) * 100).rename("m3_growth")

    gpr = _monthly(_read("A_gpr.csv"))["gpr"]
    epu = _monthly(_read("A_fred_eu_epu.csv"))["epu"]

    rate = _read("A_ecb_rate.csv")
    rate["date"] = pd.to_datetime(rate["date"])
    rate = rate.set_index("date")["rate"].resample("MS").mean().rename("rate")

    cols = [si["sav_intent"], si["unemp_exp"], m1g, m3g, gpr, epu, rate]
    if include_retail:
        rg = retail_growth()              # high-frequency hard consumption indicator
        if rg is not None:
            cols.append(rg)
    out = pd.concat(cols, axis=1)
    out = out.loc["1999-01-01":]
    return out


def retail_growth():
    """Euro-area retail-trade volume (Eurostat sts_trtu_m, deflated sales of G47),
    YoY % — the high-frequency hard read on goods consumption. None if unreachable."""
    if eurostat is None:
        return None
    try:
        df = eurostat.get_data_df("sts_trtu_m")
    except Exception:
        return None
    geocol = [c for c in df.columns if "geo" in c.lower()][0]
    tcols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    idc = [c for c in df.columns if c not in tcols]
    long = df.melt(id_vars=idc, value_vars=tcols, var_name="time", value_name="v")
    long["v"] = pd.to_numeric(long["v"], errors="coerce")
    ea = next((g for g in ("EA20", "EA19", "EA") if g in set(long[geocol])), None)
    unit = next((u for u in ("I21", "I15", "I10") if u in set(long["unit"])), "I21")
    f = long[(long[geocol] == ea) & (long["indic_bt"] == "VOL_SLS")
             & (long["nace_r2"] == "G47") & (long["s_adj"] == "SCA")
             & (long["unit"] == unit)].dropna(subset=["v"])
    f = f.copy()
    f["date"] = pd.to_datetime(f["time"] + "-01", errors="coerce")
    s = f.dropna(subset=["date"]).set_index("date")["v"].sort_index().resample("MS").mean()
    return (s.pct_change(12) * 100).rename("retail_growth")


def quarterly_target():
    """Quarterly saving rate, indexed by quarter-start Timestamp."""
    s = _read("A_ea_saving_rate_quarterly.csv")
    s["date"] = pd.to_datetime(s["date"]).dt.to_period("Q").dt.to_timestamp()
    return s.set_index("date")["value"].rename("saving").sort_index()
