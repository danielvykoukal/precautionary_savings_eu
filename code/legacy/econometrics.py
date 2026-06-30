#!/usr/bin/env python3
"""
Econometrics — does uncertainty actually drive euro-area precautionary saving?
=============================================================================

Companion to `pull_and_plot.py`. Run that FIRST so the CSVs exist in ./data:
    ea_saving_rate_quarterly.csv   (household gross saving rate, %)
    gpr.csv / fred_eu_epu.csv      (uncertainty proxies, monthly)
    ecb_rate.csv                   (ECB / short rate, monthly)        [confound]
    ea_inflation.csv               (EA HICP inflation YoY, monthly)   [confound]

Why this version is different
-----------------------------
The first cut differenced every series and leaned on a VECM. But on the real
data saving and GPR are I(0) (stationary in levels), so:
  * differencing them was OVER-differencing -> it threw away the level signal
    and biased the impulse response toward zero;
  * Johansen/VECM is only meaningful for I(1) series, so its "long-run" reading
    was an artifact of feeding it stationary variables.

This version therefore:
  1. Classifies each series' integration order from ADF + KPSS TOGETHER.
  2. Runs Granger causality and the VAR/IRF in the form each series needs —
     LEVELS for the stationary core (saving, uncertainty) — no over-differencing.
  3. Replaces the VECM with an ARDL bounds test (Pesaran-Shin-Smith), which is
     valid for a mix of I(0) and I(1) regressors — the correct long-run test here.
  4. Re-runs the key tests on a post-2010 subsample (the period that matters).

ARMA is still not used: it models one series' own memory, not a driver relation.

Outputs:
    ./data/econometrics_results.md
    ./figures/A2_irf_saving_to_uncertainty.png

    pip install statsmodels pandas numpy matplotlib
    python econometrics.py                 # GPR
    python econometrics.py --proxy epu     # EU EPU
    python econometrics.py --substart 2010 # change subsample start
"""

import os
import sys
import argparse
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from statsmodels.tsa.stattools import adfuller, kpss, grangercausalitytests
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


# ----------------------------------------------------------------------------
# Load + align to a quarterly frame
# ----------------------------------------------------------------------------
def _read(name, valcol):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    d = d.rename(columns={d.columns[0]: "date"})
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    vc = valcol if valcol in d.columns else d.columns[1]
    d[vc] = pd.to_numeric(d[vc], errors="coerce")
    return d.dropna(subset=["date", vc])[["date", vc]].rename(columns={vc: valcol})


def _to_q(d):
    return d.set_index("date").iloc[:, 0].resample("QS").mean()


def load_data(proxy="gpr"):
    sav = _read("ea_saving_rate_quarterly.csv", "saving")
    if sav is None:
        sys.exit("Missing data/ea_saving_rate_quarterly.csv — run pull_and_plot.py first.")
    unc_file = {"gpr": ("gpr.csv", "gpr"), "epu": ("fred_eu_epu.csv", "epu")}[proxy]
    unc = _read(*unc_file)
    if unc is None:
        sys.exit(f"Missing data/{unc_file[0]} — run pull_and_plot.py first.")
    rate = _read("ecb_rate.csv", "rate")
    infl = _read("ea_inflation.csv", "inflation")

    cols = {"saving": _to_q(sav), proxy: _to_q(unc)}
    if rate is not None:
        cols["rate"] = _to_q(rate)
    if infl is not None:
        cols["inflation"] = _to_q(infl)
    df = pd.DataFrame(cols).dropna()
    df.index = pd.PeriodIndex(df.index, freq="Q").to_timestamp()
    say(f"Aligned quarterly sample: {df.index.min().date()} -> {df.index.max().date()} "
        f"({len(df)} quarters); columns: {list(df.columns)}")
    return df, proxy


# ----------------------------------------------------------------------------
# 1) Integration order from ADF + KPSS together
# ----------------------------------------------------------------------------
def integration_order(df):
    say("\n" + "=" * 74)
    say("1) INTEGRATION ORDER  (ADF H0: unit root;  KPSS H0: stationary)")
    say("=" * 74)
    say(f"{'series':<12}{'ADF p lvl':>11}{'KPSS p lvl':>12}{'ADF p Δ':>10}{'order':>8}{'agree?':>9}")
    order, reliable = {}, {}
    for c in df.columns:
        x = df[c].dropna()
        try:
            adf_l = adfuller(x, autolag="AIC")[1]
        except Exception:
            adf_l = np.nan
        try:
            adf_d = adfuller(x.diff().dropna(), autolag="AIC")[1]
        except Exception:
            adf_d = np.nan
        try:
            kp_l = kpss(x, regression="c", nlags="auto")[1]
        except Exception:
            kp_l = np.nan
        adf_says_0 = adf_l < 0.05
        kpss_says_0 = kp_l > 0.05
        o = 0 if adf_says_0 else 1
        agree = (adf_says_0 == kpss_says_0)
        order[c], reliable[c] = o, agree
        say(f"{c:<12}{adf_l:>11.3f}{kp_l:>12.3f}{adf_d:>10.3f}"
            f"{('I('+str(o)+')'):>8}{('yes' if agree else 'CONFLICT'):>9}")
    say("  Note: where ADF and KPSS conflict the order is ambiguous — which is "
        "exactly why the long-run test below uses ARDL bounds (order-agnostic).")
    return order, reliable


def _stationary(series, o):
    """Return the series in stationary form: level if I(0), else first difference."""
    return series if o == 0 else series.diff()


# ----------------------------------------------------------------------------
# 2) Long-run relationship — ARDL bounds test (handles mixed I(0)/I(1))
# ----------------------------------------------------------------------------
def ardl_bounds(df, proxy):
    say("\n" + "=" * 74)
    say("2) LONG-RUN: ARDL BOUNDS TEST  (Pesaran-Shin-Smith; valid for mixed I(0)/I(1))")
    say("=" * 74)
    say("    H0: no long-run level relationship between saving and the drivers.")
    try:
        from statsmodels.tsa.ardl import ardl_select_order, UECM
    except Exception as e:
        say(f"  ARDL unavailable in this statsmodels ({e}). Upgrade: pip install -U statsmodels")
        return
    y = df["saving"]
    xcols = [c for c in [proxy, "rate", "inflation"] if c in df.columns]
    X = df[xcols]
    try:
        # Drop the forced-saving COVID quarters, then pick the UECM by AIC over a
        # small grid. UECM requires every exog order >= 1, so we search O>=1
        # directly (this avoids the from_ardl/fixed-regressor error).
        samp = pd.concat([y, X], axis=1).dropna()
        samp = samp[~samp.index.year.isin([2020])]
        yy, XX = samp["saving"], samp[xcols]
        best = None
        for L in range(1, 5):
            for O in range(1, 5):
                try:
                    r = UECM(yy, lags=L, exog=XX, order=O, trend="c").fit()
                    if best is None or r.aic < best[0]:
                        best = (r.aic, L, O, r)
                except Exception:
                    continue
        if best is None:
            say("  ARDL/UECM could not be estimated on this sample.")
            return
        _, L, O, res = best
        say(f"  selected UECM (AIC): endog lags={L}, exog order={O}  (COVID-2020 dropped)")
        bt = res.bounds_test(case=3)  # case 3: unrestricted constant, no trend
        stat = float(getattr(bt, "stat", np.nan))
        say(f"  bounds F-statistic = {stat:.2f}")

        crit = getattr(bt, "crit_vals", None)
        if crit is not None:
            try:
                say("  critical-value bounds (rows = sig. level; lower = I(0), upper = I(1)):")
                say("    " + crit.to_string().replace("\n", "\n    "))
            except Exception:
                pass

        decided = False
        pv = getattr(bt, "pvalues", None)
        if pv is not None:
            try:
                lo_p, hi_p = float(pv["lower"]), float(pv["upper"])
                say(f"  bounds p-values: lower(I0) = {lo_p:.3f}, upper(I1) = {hi_p:.3f}")
                if hi_p < 0.05:
                    say("  => upper-bound p < 0.05: REJECT H0 — a long-run level relationship "
                        "between saving and the drivers IS supported.")
                elif lo_p > 0.05:
                    say("  => lower-bound p > 0.05: cannot reject H0 — no long-run relationship.")
                else:
                    say("  => inconclusive (F falls between the bounds).")
                decided = True
            except Exception:
                pass
        if not decided and crit is not None:
            try:
                upper95 = float(crit.iloc[1, 1])  # 5% row, upper (I(1)) column
                verdict = ("REJECT H0 — long-run relationship supported"
                           if stat > upper95 else
                           "cannot confirm a long-run relationship at 5%")
                say(f"  => F {stat:.2f} vs 5% I(1) upper bound {upper95:.2f}: {verdict}.")
            except Exception as e:
                say(f"  (could not auto-decide from critical values: {e})")
    except Exception as e:
        say(f"  ARDL bounds test failed ({e}).")


def johansen_reference(df, proxy):
    """Kept only for reference; valid ONLY if all series are I(1)."""
    say("\n" + "-" * 74)
    say("   (reference) Johansen trace — interpret ONLY if every series is I(1):")
    sysdf = df[[c for c in ["saving", proxy, "inflation", "rate"] if c in df.columns]].dropna()
    try:
        j = coint_johansen(sysdf, det_order=0, k_ar_diff=2)
        rank = int(sum(j.lr1 > j.cvt[:, 1]))
        say(f"   trace-implied rank at 95% = {rank}  (treat with caution given mixed orders)")
    except Exception as e:
        say(f"   Johansen failed ({e}).")


# ----------------------------------------------------------------------------
# 3) Granger causality — in the correct (stationary) representation
# ----------------------------------------------------------------------------
def granger(df, proxy, order, maxlag=4, drop_covid=True, tag="full sample"):
    say("\n" + "=" * 74)
    say(f"3) GRANGER CAUSALITY [{tag}]  (does past {proxy.upper()} help predict saving?)")
    say("=" * 74)
    s = _stationary(df["saving"], order["saving"])
    u = _stationary(df[proxy], order[proxy])
    rep = (f"saving in {'levels' if order['saving']==0 else 'Δ'}, "
           f"{proxy} in {'levels' if order[proxy]==0 else 'Δ'}")
    say(f"  representation: {rep}  (no over-differencing of I(0) series)")
    d = pd.concat([s, u], axis=1).dropna()
    d.columns = ["saving", proxy]
    if drop_covid:
        d = d[~d.index.year.isin([2020])]
    if len(d) < maxlag + 8:
        say(f"  too few obs ({len(d)}) for lag {maxlag}; skipping.")
        return
    say(f"{'lag':<6}{'p: unc->saving':>18}{'p: saving->unc':>18}")
    for lag in range(1, maxlag + 1):
        try:
            p1 = grangercausalitytests(d[["saving", proxy]], maxlag=[lag], verbose=False)[lag][0]["ssr_ftest"][1]
            p2 = grangercausalitytests(d[[proxy, "saving"]], maxlag=[lag], verbose=False)[lag][0]["ssr_ftest"][1]
            star = "  *" if p1 < 0.05 else ""
            say(f"{lag:<6}{p1:>18.3f}{p2:>18.3f}{star}")
        except Exception as e:
            say(f"{lag:<6}  failed: {e}")
    say("  (p<0.05 in column 1 => uncertainty Granger-causes saving.)")


# ----------------------------------------------------------------------------
# 4) VAR + impulse response — in LEVELS (avoids over-differencing the I(0) core)
# ----------------------------------------------------------------------------
def covid_dummies(index):
    dums = pd.DataFrame(index=index)
    for q in ("2020-04-01", "2020-07-01", "2020-10-01", "2021-01-01"):
        dums[f"d{q[:7]}"] = (index == pd.Timestamp(q)).astype(float)
    return dums


def var_irf(df, proxy, order, horizon=12, tag="full sample", save_plot=True):
    say("\n" + "=" * 74)
    say(f"4) VAR + IMPULSE RESPONSE [{tag}]  (saving's response to a +1 s.d. {proxy.upper()} shock)")
    say("=" * 74)
    core = ["saving", proxy]
    use_levels = (order["saving"] == 0 and order[proxy] == 0)
    ordering = [c for c in [proxy, "rate", "inflation", "saving"] if c in df.columns]
    sub = df[ordering].dropna()

    if use_levels:
        endog = sub.copy()
        say("  estimating the VAR in LEVELS (saving & uncertainty are I(0)); "
            "IRF is the level response directly.")
    else:
        endog = sub.diff().dropna()
        say("  core series not both I(0): estimating in first differences; "
            "IRF cumulated to levels.")
    dums = covid_dummies(endog.index)

    model = VAR(endog, exog=dums)
    try:
        sel = model.select_order(maxlags=min(6, len(endog) // 8))
        p = max(1, min(int(sel.aic), 4))  # cap to keep IRFs stable on a short sample
        say(f"  lag length: AIC={int(sel.aic)}, BIC={int(sel.bic)} -> using p={p} (capped at 4)")
    except Exception:
        p = 2
        say(f"  lag selection failed; using p={p}")
    res = model.fit(p)
    irf = res.irf(horizon)

    imp, rsp = ordering.index(proxy), ordering.index("saving")
    if use_levels:
        resp = irf.orth_irfs[:, rsp, imp]
    else:
        resp = irf.orth_cum_effects[:, rsp, imp]
    try:
        se = (irf.stderr(orth=True)[:, rsp, imp] if use_levels
              else irf.cum_effect_stderr(orth=True)[:, rsp, imp])
        lo, hi = resp - 1.96 * se, resp + 1.96 * se
    except Exception:
        lo = hi = None

    peak_i = int(np.nanargmax(np.abs(resp)))
    say(f"  peak response {resp[peak_i]:+.3f} pp at {peak_i}q; "
        f"response at {horizon}q = {resp[-1]:+.3f} pp")
    sig = ""
    if lo is not None:
        sig = ("significant" if (lo[peak_i] > 0 or hi[peak_i] < 0) else "NOT significant")
        say(f"  peak is {sig} at 95% (CI [{lo[peak_i]:+.3f}, {hi[peak_i]:+.3f}]).")
    direction = "raises" if resp[peak_i] > 0 else "lowers"
    say(f"  => a positive uncertainty shock {direction} saving — "
        f"{'consistent with' if resp[peak_i] > 0 else 'not consistent with'} precaution"
        f"{' (but ' + sig + ')' if sig else ''}.")

    if save_plot:
        fig, ax = plt.subplots(figsize=(8, 5))
        h = np.arange(horizon + 1)
        ax.axhline(0, color="black", lw=0.8)
        if lo is not None:
            ax.fill_between(h, lo, hi, color="#1f4e79", alpha=0.15, label="95% CI")
        ax.plot(h, resp, color="#1f4e79", lw=2.2, marker="o", ms=3,
                label="response of saving rate")
        ax.set_xlabel("quarters after the shock")
        ax.set_ylabel("response of saving rate (pp)")
        ax.set_title(f"Saving response to a +1 s.d. {proxy.upper()} shock\n"
                     f"({'levels' if use_levels else 'differenced'} VAR, "
                     f"controls: rate & inflation, COVID dummies)", fontweight="bold")
        ax.legend(frameon=False)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        out = os.path.join(FIG, "A2_irf_saving_to_uncertainty.png")
        fig.savefig(out, dpi=150)
        plt.close(fig)
        say(f"  saved {os.path.relpath(out, HERE)}")
    return float(resp[peak_i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", choices=["gpr", "epu"], default="gpr")
    ap.add_argument("--horizon", type=int, default=12)
    ap.add_argument("--substart", type=int, default=2010,
                    help="start year for the subsample re-run")
    args = ap.parse_args()

    say("#" * 74)
    say(f"# Precautionary saving — econometrics  (proxy = {args.proxy.upper()})")
    say("#" * 74)

    df, proxy = load_data(args.proxy)
    order, _ = integration_order(df)
    ardl_bounds(df, proxy)
    johansen_reference(df, proxy)

    # full sample (correct representation)
    granger(df, proxy, order, tag="full sample")
    var_irf(df, proxy, order, horizon=args.horizon, tag="full sample", save_plot=True)

    # subsample — the period that actually matters
    sub = df[df.index.year >= args.substart]
    if len(sub) >= 28:
        say("\n" + "#" * 74)
        say(f"# SUBSAMPLE from {args.substart} ({len(sub)} quarters) — robustness")
        say("#" * 74)
        sorder, _ = integration_order(sub)
        granger(sub, proxy, sorder, tag=f"{args.substart}+")
        var_irf(sub, proxy, sorder, horizon=args.horizon,
                tag=f"{args.substart}+", save_plot=False)
    else:
        say(f"\nSubsample from {args.substart} too short ({len(sub)}q) — skipped.")

    say("\n" + "=" * 74)
    say("HOW TO READ THIS")
    say("=" * 74)
    say("- ARDL bounds is the long-run verdict (order-agnostic). Johansen is only a "
        "reference and should be ignored unless every series is I(1).")
    say("- Granger & VAR now use levels for the I(0) core, so a null here is a real "
        "(if low-power) null, not an over-differencing artifact.")
    say("- Compare full sample vs subsample and GPR vs EPU (--proxy epu) before "
        "settling on the headline. Use proxy_timing_test.py for the best lead/lag.")

    with open(os.path.join(DATA, "econometrics_results.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.join('data', 'econometrics_results.md')}")


if __name__ == "__main__":
    main()
