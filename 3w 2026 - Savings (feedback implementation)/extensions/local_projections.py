#!/usr/bin/env python3
"""
Extension II --- Local projections (Jordà) for the saving response
==================================================================

Idea. The core VAR/IRF is fragile on ~100 quarters with a COVID break. Jordà
(2005) local projections estimate the impulse response horizon-by-horizon with a
separate regression, which is more robust to misspecification and small samples
and does not impose the VAR's dynamics. We re-estimate the response of the saving
rate to an uncertainty shock this way, as a cross-check on the VAR.

Specification (per horizon h = 0..H):
    saving_{t+h} = a_h + b_h * shock_t
                   + sum_l ( controls_{t-l} ) + COVID dummies + u_{t+h}
where shock_t is the uncertainty proxy (ordered most-exogenous, so contemporaneous
rate/inflation are excluded), and controls are p lags of saving, proxy, rate and
inflation. b_h (scaled to a +1 s.d. shock) is the impulse response at horizon h;
Newey--West (HAC) standard errors account for the MA(h) residuals LP induces.

Reads ../data (saving + proxy + controls). Writes extensions/figures + a results md.

    python local_projections.py                 # GPR
    python local_projections.py --proxy epu
"""

import argparse
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

import _common as C

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def build_frame(proxy):
    saving = C.load_quarterly("ea_saving_rate_quarterly.csv", "saving")
    unc = C.load_quarterly(
        "gpr.csv" if proxy == "gpr" else "fred_eu_epu.csv", proxy)
    rate = C.load_quarterly("ecb_rate.csv", "rate")
    infl = C.load_quarterly("ea_inflation.csv", "inflation")
    df = pd.concat([saving, unc, rate, infl], axis=1).dropna()
    df.index = pd.PeriodIndex(df.index, freq="Q").to_timestamp()
    return df


def covid_dummies(index):
    d = pd.DataFrame(index=index)
    for q in ("2020-04-01", "2020-07-01", "2020-10-01", "2021-01-01"):
        d[f"d{q[:7]}"] = (index == pd.Timestamp(q)).astype(float)
    return d


def local_projection(df, proxy, horizon=12, lags=2):
    """Return (h, irf, lo95, hi95) per +1 s.d. proxy shock."""
    shock_sd = df[proxy].std(ddof=0)
    # regressors: contemporaneous shock + p lags of every variable + COVID dummies
    base = pd.DataFrame(index=df.index)
    base["shock"] = df[proxy]
    for v in ["saving", proxy, "rate", "inflation"]:
        for l in range(1, lags + 1):
            base[f"{v}_l{l}"] = df[v].shift(l)
    base = pd.concat([base, covid_dummies(df.index)], axis=1)

    irf, lo, hi = [], [], []
    for h in range(horizon + 1):
        y = df["saving"].shift(-h)
        d = pd.concat([y.rename("y"), base], axis=1).dropna()
        X = sm.add_constant(d.drop(columns="y"))
        res = sm.OLS(d["y"], X).fit(
            cov_type="HAC", cov_kwds={"maxlags": max(1, h), "use_correction": True})
        b = res.params["shock"] * shock_sd
        se = res.bse["shock"] * shock_sd
        irf.append(b); lo.append(b - 1.96 * se); hi.append(b + 1.96 * se)
    return (np.arange(horizon + 1), np.array(irf), np.array(lo), np.array(hi))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", choices=["gpr", "epu"], default="gpr")
    ap.add_argument("--horizon", type=int, default=12)
    ap.add_argument("--lags", type=int, default=2)
    args = ap.parse_args()

    say("#" * 70)
    say(f"# Local projections — saving response to a {args.proxy.upper()} shock")
    say("#" * 70)
    df = build_frame(args.proxy)
    say(f"sample {df.index.min().date()} -> {df.index.max().date()} "
        f"({len(df)} quarters); p={args.lags} control lags")

    h, irf, lo, hi = local_projection(df, args.proxy, args.horizon, args.lags)

    peak = int(np.nanargmax(np.abs(irf)))
    sig = "significant" if (lo[peak] > 0 or hi[peak] < 0) else "NOT significant"
    say(f"\npeak response {irf[peak]:+.3f} pp at {peak}q (95% CI "
        f"[{lo[peak]:+.3f}, {hi[peak]:+.3f}], {sig}); "
        f"response at {args.horizon}q = {irf[-1]:+.3f} pp")
    say(f"horizons with 95% CI excluding zero: "
        f"{[int(x) for x in h[(lo > 0) | (hi < 0)]] or 'none'}")
    say("\nReading: compare with the VAR IRF in ../figures/A2. A positive but "
        "insignificant LP response corroborates the VAR's measured null.")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhline(0, color="black", lw=0.8)
    ax.fill_between(h, lo, hi, color=C.C_MAIN, alpha=0.15, label="95% CI")
    ax.plot(h, irf, color=C.C_MAIN, lw=2.2, marker="o", ms=3,
            label="LP response of saving")
    ax.set_xlabel("quarters after the shock")
    ax.set_ylabel("response of saving rate (pp)")
    ax.set_title(f"Local-projection response of saving to a +1 s.d. "
                 f"{args.proxy.upper()} shock\n(controls: lags of saving, "
                 f"{args.proxy}, rate, inflation; COVID dummies)", fontweight="bold")
    ax.legend(frameon=False)
    C.savefig(fig, f"LP_irf_{args.proxy}.png")

    with open(os.path.join(C.DATA, f"local_projections_{args.proxy}.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote extensions/data/local_projections_{args.proxy}.md")


if __name__ == "__main__":
    main()
