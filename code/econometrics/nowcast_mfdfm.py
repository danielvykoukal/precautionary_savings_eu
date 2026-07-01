#!/usr/bin/env python3
"""
1-quarter-ahead MFDFM nowcast of the saving rate (differenced, real-time)
=========================================================================

Two fixes over the first cut:
  * the saving rate is modelled in FIRST DIFFERENCES, so the nowcast anchors on the
    last observed level and adds a predicted change — no reversion to the historical
    mean (which biased the levels version ~1.4pp low on the recent plateau);
  * it is evaluated as a genuine 1-QUARTER-AHEAD real-time nowcast: for each test
    quarter we keep only the data a forecaster would actually have — the saving rate
    observed through the PREVIOUS quarter, and the monthly leads through the end of
    the CURRENT quarter — then nowcast that quarter's change. No future data, and the
    target value being nowcast is withheld.

DynamicFactorMQ (1 factor, AR(2), idiosyncratic AR(1)) on the standardised monthly
leads + the differenced quarterly target. Parameters are estimated once; each test
quarter re-runs only the Kalman smoother on its own (masked) data vintage.
Benchmarked against the random walk and the bridge.
    python nowcast_mfdfm.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ

import _nowcast_data as D

TEST_START = pd.Timestamp("2015-01-01")
REPORT = []


def say(s=""):
    print(s); REPORT.append(str(s))


def rmse(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def build(zm, zq):
    return DynamicFactorMQ(zm, endog_quarterly=zq.to_frame(), factors=1,
                           factor_orders=2, idiosyncratic_ar1=True, standardize=False)


def dy_at(res, t):
    """Extract the model's estimate of the differenced target at quarter t."""
    pr = res.predict()["d_saving"]
    idx = pr.index
    ts = idx.to_timestamp() if isinstance(idx, pd.PeriodIndex) else pd.to_datetime(idx)
    pr.index = pd.PeriodIndex(ts, freq="Q")
    return pr.groupby(level=0).last().get(pd.Period(t, "Q"), np.nan)


def main():
    monthly = D.monthly_predictors().asfreq("MS").loc["2000-01-01":]
    level = D.quarterly_target().asfreq("QS").loc["2000-01-01":]
    dy = level.diff().rename("d_saving")

    # fixed (full-sample) standardisation so the estimated parameters stay valid
    # across the per-quarter re-smoothing on masked vintages
    m_mu, m_sd = monthly.mean(), monthly.std()
    Zm = (monthly - m_mu) / m_sd
    dy_mu, dy_sd = dy.mean(), dy.std()
    Zdy = (dy - dy_mu) / dy_sd

    say("#" * 70)
    say("# 1-quarter-ahead nowcast of the saving rate — differenced DFM (real-time)")
    say("#" * 70)
    say(f"  leads: {', '.join(monthly.columns)}")
    say("  estimating parameters (EM) on the full standardised sample ...")
    params = build(Zm, Zdy).fit(disp=False, maxiter=200).params

    levP = level.copy(); levP.index = levP.index.to_period("Q")
    test_q = [t for t in dy.dropna().index if t >= TEST_START]

    dates, act, nc, rw = [], [], [], []
    for t in test_q:
        qend = pd.Period(t, "Q").end_time          # last day of the current quarter
        zm = Zm.copy(); zm[zm.index > qend] = np.nan   # leads only through this quarter
        zq = Zdy.copy(); zq[zq.index >= t] = np.nan     # saving withheld from t on
        res = build(zm, zq).smooth(params)
        dy_hat = dy_at(res, t) * dy_sd + dy_mu
        prev = levP.get(pd.Period(t, "Q") - 1, np.nan)  # last OBSERVED level (t-1)
        dates.append(t); act.append(float(level.loc[t]))
        nc.append(prev + dy_hat); rw.append(prev)

    act = np.array(act); nc = np.array(nc); rw = np.array(rw)
    yrs = np.array([pd.Timestamp(d).year for d in dates])
    say(f"\n1-quarter-ahead, {pd.Period(dates[0],'Q')}–{pd.Period(dates[-1],'Q')} "
        f"({len(dates)} quarters):")
    say(f"  RMSE  MFDFM(diff) = {rmse(nc, act):.3f}   random walk = {rmse(rw, act):.3f}   "
        f"(pp of the saving rate)")
    m = yrs != 2020
    say(f"  ex-2020:  MFDFM(diff) = {rmse(nc[m], act[m]):.3f}   "
        f"random walk = {rmse(rw[m], act[m]):.3f}")
    say(f"  skill vs RW: {100*(1-rmse(nc,act)/rmse(rw,act)):+.0f}% RMSE "
        f"(full), {100*(1-rmse(nc[m],act[m])/rmse(rw[m],act[m])):+.0f}% ex-2020")

    # compare on the shared recent window the levels version failed on
    recent = yrs >= 2024
    say(f"\n  2024-25 plateau (where the levels DFM was ~1.4pp low):")
    say(f"    MFDFM(diff) RMSE = {rmse(nc[recent], act[recent]):.3f}   "
        f"random walk = {rmse(rw[recent], act[recent]):.3f}")

    plot(dates, act, nc, rw)
    pd.DataFrame({"date": dates, "actual": act, "mfdfm_diff": nc, "rw": rw}).to_csv(
        os.path.join(D.DATA, "P_nowcast_mfdfm.csv"), index=False)
    with open(os.path.join(D.DATA, "P_nowcast_mfdfm.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("Wrote data/P_nowcast_mfdfm.csv")


def plot(dates, act, nc, rw):
    x = [pd.Timestamp(d) for d in dates]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(x, act, color="#1f4e79", lw=2.6, marker="o", ms=3, label="actual saving rate")
    ax.plot(x, nc, color="#117a65", lw=2.0, ls="--", marker="o", ms=3,
            label="MFDFM 1-quarter-ahead nowcast (differenced, real-time)")
    ax.plot(x, rw, color="#7f8c8d", lw=1.2, ls=":", label="random-walk benchmark")
    ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31"),
               color="#5d6d7e", alpha=0.12, lw=0)
    ax.set_ylabel("household saving rate (% of disposable income)")
    ax.set_xlabel("year")
    ax.set_title("1-quarter-ahead nowcast of the euro-area saving rate\n"
                 "differenced MFDFM, genuine real-time vintages (target withheld)",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.setp(ax.get_xticklabels(), rotation=45, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(D.FIG, "P_nowcast_mfdfm.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/P_nowcast_mfdfm.png")


if __name__ == "__main__":
    main()
