#!/usr/bin/env python3
"""Shared data loader for the saving-rate nowcast (bridge + MFDFM).

Target  : quarterly euro-area household saving rate.
Monthly leads (EA-aggregate): saving intentions, unemployment expectations,
M1 & M3 year-on-year growth, GPR, EPU, ECB rate.
"""

import os
import pandas as pd

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
}


def _read(name):
    return pd.read_csv(os.path.join(DATA, name))


def _monthly(df, datecol="date"):
    df = df.copy()
    df[datecol] = pd.to_datetime(df[datecol]).dt.to_period("M").dt.to_timestamp()
    return df.set_index(datecol)


def monthly_predictors():
    """Monthly DataFrame of standardisable leads, indexed by month-start."""
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

    out = pd.concat([si["sav_intent"], si["unemp_exp"], m1g, m3g, gpr, epu, rate],
                    axis=1)
    out = out.loc["1999-01-01":]
    return out


def quarterly_target():
    """Quarterly saving rate, indexed by quarter-start Timestamp."""
    s = _read("A_ea_saving_rate_quarterly.csv")
    s["date"] = pd.to_datetime(s["date"]).dt.to_period("Q").dt.to_timestamp()
    return s.set_index("date")["value"].rename("saving").sort_index()
