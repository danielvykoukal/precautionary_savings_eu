#!/usr/bin/env python3
"""
Mixed-frequency dynamic factor model (MFDFM) nowcast of the saving rate
=======================================================================

A small dynamic factor model (statsmodels DynamicFactorMQ) in which one latent
factor drives the monthly leads (saving intentions, unemployment expectations,
M1/M3 growth, GPR, EPU, rate) AND the quarterly saving rate. The Kalman smoother
produces a nowcast of the quarterly saving rate that updates as monthly data
arrive — and fills any quarter whose saving observation is missing.

Pseudo-out-of-sample test: the last 8 quarters of the SAVING series are blanked
(set NaN) while the monthly leads are kept, so the model must nowcast them from
the factor; we then score those nowcasts against the realised values and against
the bridge baseline.

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

HOLDOUT = 8       # quarters blanked for the pseudo-OOS test
REPORT = []


def say(s=""):
    print(s); REPORT.append(str(s))


def rmse(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def fit_mfdfm(monthly, quarterly):
    mod = DynamicFactorMQ(monthly, endog_quarterly=quarterly.to_frame(),
                          factors=1, factor_orders=2, idiosyncratic_ar1=True,
                          standardize=True)
    return mod.fit(disp=False, maxiter=150)


def saving_nowcast(res):
    """Smoothed estimate of the quarterly saving rate, one value per quarter."""
    pred = res.predict()
    s = pred["saving"].dropna()
    idx = s.index
    ts = idx.to_timestamp() if isinstance(idx, pd.PeriodIndex) else pd.to_datetime(idx)
    s.index = pd.PeriodIndex(ts, freq="Q")
    # keep one value per quarter (the model carries it at quarter-end months)
    return s.groupby(level=0).last()


def main():
    monthly = D.monthly_predictors().asfreq("MS")
    monthly = monthly.loc["2000-01-01":]
    target = D.quarterly_target().asfreq("QS")
    target = target.loc["2000-01-01":]

    say("#" * 66)
    say("# MFDFM nowcast of the euro-area quarterly saving rate")
    say("#" * 66)
    say(f"  monthly leads: {', '.join(monthly.columns)}")
    say(f"  {len(target.dropna())} quarterly saving obs, "
        f"{pd.Period(target.dropna().index.min(),'Q')}–"
        f"{pd.Period(target.dropna().index.max(),'Q')}; 1 factor, AR(2)")

    # ---- full-sample fit (for the in-sample nowcast plot) ----
    res = fit_mfdfm(monthly, target)
    nc_full = saving_nowcast(res)
    act = target.copy(); act.index = act.index.to_period("Q")
    common = nc_full.index.intersection(act.dropna().index)
    say(f"\nin-sample fit: corr(nowcast, actual) = "
        f"{np.corrcoef(nc_full[common], act[common])[0,1]:.3f}, "
        f"RMSE = {rmse(nc_full[common], act[common]):.3f} pp")

    # ---- pseudo-OOS: blank the last HOLDOUT quarters of saving, keep the leads ----
    t_oos = target.copy()
    obs = t_oos.dropna().index
    blanked = obs[-HOLDOUT:]
    t_oos.loc[blanked] = np.nan
    res_oos = fit_mfdfm(monthly, t_oos)
    nc_oos = saving_nowcast(res_oos)
    bp = blanked.to_period("Q")
    a = act.loc[bp]; f = nc_oos.loc[bp]
    rb = pd.read_csv(os.path.join(D.DATA, "P_nowcast_bridge.csv")) \
        if os.path.exists(os.path.join(D.DATA, "P_nowcast_bridge.csv")) else None
    say(f"\nPseudo-OOS (last {HOLDOUT} quarters blanked, nowcast from the leads):")
    say(f"{'quarter':<9}{'actual':>8}{'MFDFM':>8}{'error':>8}")
    for q in bp:
        say(f"{str(q):<9}{a[q]:>8.2f}{f[q]:>8.2f}{f[q]-a[q]:>+8.2f}")
    say(f"  MFDFM OOS RMSE = {rmse(f.values, a.values):.3f} pp")
    if rb is not None:
        rb["q"] = pd.PeriodIndex(pd.to_datetime(rb["date"]), freq="Q")
        sub = rb[rb["q"].isin(bp)]
        if len(sub):
            say(f"  bridge OOS RMSE (same quarters) = "
                f"{rmse(sub['bridge'].values, sub['actual'].values):.3f};  "
                f"random walk = {rmse(sub['rw'].values, sub['actual'].values):.3f}")

    plot(act, nc_full, bp, f)
    with open(os.path.join(D.DATA, "P_nowcast_mfdfm.md"), "w") as fp:
        fp.write("```\n" + "\n".join(REPORT) + "\n```\n")
    nc_full.rename("mfdfm_nowcast").to_frame().assign(
        actual=act.reindex(nc_full.index)).to_csv(
        os.path.join(D.DATA, "P_nowcast_mfdfm.csv"))
    print("Wrote data/P_nowcast_mfdfm.csv")


def plot(act, nc_full, bp, f):
    x = act.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(x, act.values, color="#1f4e79", lw=2.4, label="actual saving rate")
    ax.plot(nc_full.index.to_timestamp(), nc_full.values, color="#117a65", lw=1.8,
            ls="--", label="MFDFM nowcast (smoothed)")
    ax.plot(bp.to_timestamp(), f.values, color="#c0392b", lw=0, marker="o", ms=6,
            label=f"pseudo-OOS nowcast (last {len(bp)}q, leads only)")
    ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31"),
               color="#5d6d7e", alpha=0.12, lw=0)
    ax.set_ylabel("household saving rate (% of disposable income)")
    ax.set_xlabel("year")
    ax.set_title("MFDFM nowcast of the euro-area saving rate\n"
                 "one latent factor from monthly leads + the quarterly target",
                 fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(D.FIG, "P_nowcast_mfdfm.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/P_nowcast_mfdfm.png")


if __name__ == "__main__":
    main()
