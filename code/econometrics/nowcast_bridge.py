#!/usr/bin/env python3
"""
Bridge nowcast of the quarterly saving rate — the transparent baseline
======================================================================

Aggregates the monthly leads to quarterly means and regresses the saving rate on
them (a "bridge" equation). Evaluated in expanding-window pseudo-out-of-sample
1-step-ahead forecasts and benchmarked against an AR(1) and a random walk. This is
the simple, interpretable benchmark the MFDFM must beat.

    python nowcast_bridge.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm

import _nowcast_data as D

PREDICTORS = ["sav_intent", "unemp_exp", "m1_growth", "m3_growth", "gpr", "epu", "rate"]
OOS_START = "2012-01-01"     # begin pseudo-real-time evaluation here
REPORT = []


def say(s=""):
    print(s); REPORT.append(str(s))


def build():
    """Quarterly design matrix: target + quarter-mean of each monthly lead."""
    mq = D.monthly_predictors().resample("QS").mean()
    y = D.quarterly_target()
    df = pd.concat([y, mq[PREDICTORS]], axis=1).dropna()
    return df


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def main():
    df = build()
    say("#" * 68)
    say("# Bridge nowcast of the euro-area quarterly saving rate")
    say("#" * 68)
    q0, q1 = pd.Period(df.index.min(), "Q"), pd.Period(df.index.max(), "Q")
    say(f"  sample {q0}…{q1}  ({len(df)} quarters); "
        f"predictors: {', '.join(PREDICTORS)}")

    # ---- full-sample fit (descriptive) ----
    X = sm.add_constant(df[PREDICTORS]); y = df["saving"]
    full = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    say(f"\nFull-sample bridge: R-squared = {full.rsquared:.3f}")
    say(f"{'predictor':<28}{'coef':>9}{'t':>8}{'p':>8}")
    for p in PREDICTORS:
        say(f"{D.PRED_LABELS[p]:<28}{full.params[p]:>9.3f}{full.tvalues[p]:>8.2f}"
            f"{full.pvalues[p]:>8.3f}")

    # ---- expanding-window pseudo-OOS, 1-step-ahead ----
    idx = df.index
    start = idx[idx >= OOS_START][0]
    preds, ar1s, rws, acts, dates = [], [], [], [], []
    for t in idx[idx >= start]:
        tr = df[df.index < t]
        if len(tr) < 20:
            continue
        Xtr = sm.add_constant(tr[PREDICTORS]); ytr = tr["saving"]
        b = sm.OLS(ytr, Xtr).fit()
        xt = np.r_[1.0, df.loc[t, PREDICTORS].values]
        preds.append(float(b.params.values @ xt))
        # AR(1)
        ar = sm.OLS(ytr.values[1:], sm.add_constant(ytr.values[:-1])).fit()
        ar1s.append(float(ar.params[0] + ar.params[1] * ytr.values[-1]))
        rws.append(float(ytr.values[-1]))           # random walk
        acts.append(float(df.loc[t, "saving"])); dates.append(t)

    acts = np.array(acts)
    r_bridge, r_ar1, r_rw = rmse(preds, acts), rmse(ar1s, acts), rmse(rws, acts)
    say("\nPseudo-out-of-sample (expanding window, 1-step-ahead), "
        f"{pd.Timestamp(dates[0]):%Y}Q{(dates[0].month-1)//3+1}–"
        f"{pd.Timestamp(dates[-1]):%Y}Q{(dates[-1].month-1)//3+1}:")
    say(f"  RMSE  bridge = {r_bridge:.3f}   AR(1) = {r_ar1:.3f}   "
        f"random walk = {r_rw:.3f}  (pp of the saving rate)")
    say(f"  bridge vs RW: {100*(1-r_bridge/r_rw):+.0f}% RMSE;  "
        f"bridge vs AR(1): {100*(1-r_bridge/r_ar1):+.0f}%")
    # exclude the COVID 2020 outliers to show the non-pandemic skill too
    msk = np.array([not (pd.Timestamp(d).year == 2020) for d in dates])
    say(f"  ex-2020:  bridge = {rmse(np.array(preds)[msk], acts[msk]):.3f}   "
        f"AR(1) = {rmse(np.array(ar1s)[msk], acts[msk]):.3f}   "
        f"RW = {rmse(np.array(rws)[msk], acts[msk]):.3f}")

    plot(df, dates, preds, acts)
    pd.DataFrame({"date": dates, "actual": acts, "bridge": preds,
                  "ar1": ar1s, "rw": rws}).to_csv(
        os.path.join(D.DATA, "P_nowcast_bridge.csv"), index=False)
    with open(os.path.join(D.DATA, "P_nowcast_bridge.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("Wrote data/P_nowcast_bridge.csv")


def plot(df, dates, preds, acts):
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(df.index, df["saving"], color="#1f4e79", lw=2.4, label="actual saving rate")
    ax.plot(dates, preds, color="#c0392b", lw=1.8, ls="--", marker="o", ms=3,
            label="bridge nowcast (pseudo-real-time, 1-step)")
    ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31"),
               color="#5d6d7e", alpha=0.12, lw=0)
    ax.set_ylabel("household saving rate (% of disposable income)")
    ax.set_xlabel("year")
    ax.set_title("Bridge nowcast vs the realised euro-area saving rate\n"
                 "quarterly, monthly leads aggregated to the quarter", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(D.FIG, "P_nowcast_bridge.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/P_nowcast_bridge.png")


if __name__ == "__main__":
    main()
