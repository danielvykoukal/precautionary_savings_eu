#!/usr/bin/env python3
"""
Proxy & timing test  (standalone — NOT wired into pull_and_plot.py)
==================================================================

Two quick questions before committing to the headline:
  (a) WHICH uncertainty proxy co-moves with saving most — Geopolitical Risk
      (GPR) or EU Economic Policy Uncertainty (EPU)?
  (b) WHAT is the timing — does saving respond contemporaneously, or with a
      lead/lag? Precautionary buffers may build a quarter or two AFTER an
      uncertainty spike.

Method: standardise everything to z-scores, then compute the cross-correlation
between the saving rate and each proxy at quarterly leads/lags k = -8..+8, where
k>0 means "uncertainty k quarters EARLIER correlates with saving now" (i.e.
uncertainty leads saving). Reported on the change (Δ) as well as the level,
because levels of trending series inflate correlations. COVID 2020 is dropped.

Run pull_and_plot.py first (needs ./data CSVs), then:
    pip install pandas numpy matplotlib
    python proxy_timing_test.py
"""

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
MAXK = 8  # quarters of lead/lag to scan


def _read_q(name, col):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    d = d.rename(columns={d.columns[0]: "date"})
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    vc = col if col in d.columns else d.columns[1]
    d[vc] = pd.to_numeric(d[vc], errors="coerce")
    s = d.dropna(subset=["date", vc]).set_index("date")[vc]
    return s.resample("QS").mean()


def z(s):
    return (s - s.mean()) / s.std(ddof=0)


def lead_lag(saving, proxy, drop_covid=True, diff=False):
    """Return dict k -> corr(saving_t, proxy_{t-k}); k>0 = proxy leads saving."""
    a, b = saving.align(proxy, join="inner")
    if diff:
        a, b = a.diff(), b.diff()
    if drop_covid:
        mask = ~a.index.year.isin([2020])
        a, b = a[mask], b[mask]
    out = {}
    for k in range(-MAXK, MAXK + 1):
        bb = b.shift(k)
        pair = pd.concat([a, bb], axis=1).dropna()
        out[k] = pair.iloc[:, 0].corr(pair.iloc[:, 1]) if len(pair) > 6 else np.nan
    return out


def best(d):
    dd = {k: v for k, v in d.items() if not np.isnan(v)}
    k = max(dd, key=lambda k: abs(dd[k]))
    return k, dd[k]


def main():
    saving = _read_q("ea_saving_rate_quarterly.csv", "saving")
    if saving is None:
        raise SystemExit("Missing data/ea_saving_rate_quarterly.csv — run pull_and_plot.py first.")
    proxies = {}
    g = _read_q("gpr.csv", "gpr")
    e = _read_q("fred_eu_epu.csv", "epu")
    if g is not None:
        proxies["GPR"] = g
    if e is not None:
        proxies["EPU"] = e
    if not proxies:
        raise SystemExit("No proxy CSVs found (gpr.csv / fred_eu_epu.csv).")

    print("Lead/lag cross-correlation with the saving rate")
    print("k>0 = proxy LEADS saving by k quarters; COVID-2020 dropped\n")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, mode, dif in zip(axes, ("levels", "changes (Δ)"), (False, True)):
        print(f"== {mode} ==")
        for name, p in proxies.items():
            d = lead_lag(z(saving), z(p), diff=dif)
            k, r = best(d)
            lead = "lead" if k > 0 else ("lag" if k < 0 else "contemp.")
            print(f"  {name:<5} peak |corr| = {r:+.2f} at k={k:+d} ({abs(k)}q {lead})")
            ks = sorted(d)
            ax.plot(ks, [d[i] for i in ks], marker="o", ms=3, label=name)
        ax.axvline(0, color="grey", lw=0.8, ls="--")
        ax.axhline(0, color="black", lw=0.6)
        ax.set_title(f"Cross-correlation — {mode}")
        ax.set_xlabel("k (quarters proxy leads saving →)")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False)
        print()
    axes[0].set_ylabel("correlation (z-scored)")
    fig.suptitle("Which uncertainty proxy, and at what lag, best tracks saving?",
                 fontweight="bold")
    fig.tight_layout()
    out = os.path.join(FIG, "A3_proxy_leadlag.png")
    os.makedirs(FIG, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"saved {os.path.relpath(out, HERE)}")
    print("\nUse the winning proxy/lag as the headline; feed the same proxy to "
          "econometrics.py via --proxy gpr|epu.")


if __name__ == "__main__":
    main()
