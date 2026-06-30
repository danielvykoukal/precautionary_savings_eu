#!/usr/bin/env python3
"""
Descriptive #1 --- Structural or cyclical? Decomposing the saving rate
=====================================================================

Supervisor question: is the elevated euro-area household saving rate a new
*structural* norm (e.g. saving more for old age as pension promises weaken), or a
*cyclical* response to the unprecedented volatility of the last six years (COVID
forced saving, the energy shock, the ECB hiking cycle)?

We split the saving rate into a slow-moving TREND (structural) and a CYCLE
(cyclical deviation from trend) with a Hodrick-Prescott filter (lambda=1600,
the standard for quarterly data), then ask two things:
  (a) did the structural TREND step up after the pandemic, or is the elevation a
      cycle that should revert?
  (b) does the cyclical component co-move with cyclical drivers (the ECB rate,
      inflation, geopolitical risk)?

Reads ../data (saving rate + drivers). Writes a figure + CSV + report.
    python structural_vs_cyclical.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

try:
    from statsmodels.tsa.filters.hp_filter import hpfilter
except Exception:
    hpfilter = None

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def main():
    say("#" * 72)
    say("# Structural vs cyclical — HP decomposition of the saving rate")
    say("#" * 72)

    saving = C.load_quarterly("ea_saving_rate_quarterly.csv", "saving").dropna()
    if hpfilter is None:
        say("statsmodels unavailable — cannot run the HP filter.")
        with open(os.path.join(C.DATA, "structural_vs_cyclical.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    # The 2020-21 COVID spike was forced saving (people could not spend), not a
    # behavioural change, and it badly distorts an HP trend. So we EXCLUDE those
    # quarters from the filter (interpolate linearly across them) and compute the
    # cycle as the real deviation from that de-COVID trend -- the spike then shows
    # up (correctly) as a large positive cycle, not as a lift in the structural trend.
    covid = (saving.index >= "2020-01-01") & (saving.index <= "2021-12-31")
    hp_in = saving.where(~covid).interpolate(method="linear", limit_direction="both")
    _, trend = hpfilter(hp_in, lamb=1600)
    cycle = saving - trend

    pre = trend[(trend.index >= "2012-01-01") & (trend.index <= "2019-12-31")].mean()
    latest_t, latest_c = float(trend.iloc[-1]), float(cycle.iloc[-1])
    latest = float(saving.iloc[-1])
    say(f"\nStructural trend: pre-pandemic (2012-19 avg) {pre:4.1f}%  ->  latest {latest_t:4.1f}%"
        f"  (structural step {latest_t-pre:+.1f} pp)")
    say(f"Latest quarter {saving.index[-1].date()}: rate {latest:4.1f}% = trend {latest_t:4.1f}% "
        f"+ cycle {latest_c:+.1f} pp")
    say("Reading: a positive structural step = a higher NORM (consistent with saving "
        "more for old age as pensions weaken); a large positive cycle = a temporary "
        "bump that should revert. With 2020-21 excluded from the filter, the lockdown "
        "spike reads as a pure cycle (forced saving), not a change in the norm -- yet "
        "the trend still steps up, so the post-2022 level is genuinely structural.")

    # ---- cyclical drivers (z-scored), to show the cycle is cyclical ----
    drivers = {}
    for name, fn, col in (("ECB / short rate", "ecb_rate.csv", "rate"),
                          ("HICP inflation", "ea_inflation.csv", "inflation"),
                          ("Geopolitical Risk", "gpr.csv", "gpr")):
        try:
            drivers[name] = C.load_quarterly(fn, col)
        except Exception as e:
            say(f"  driver {name} skipped: {e}")

    # ---- figure: top level+trend, bottom cycle vs drivers ----
    fig, (axT, axB) = plt.subplots(2, 1, figsize=(10, 7.6), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1.5], "hspace": 0.1})
    axT.plot(saving.index, saving.values, color=C.C_MAIN, lw=2.6, label="household saving rate")
    axT.plot(trend.index, trend.values, color=C.C_HOT, lw=2.2, ls="--",
             label="structural trend (HP, 2020-21 excluded)")
    axT.axhline(pre, color=C.C_GREY, ls=":", lw=1.3)
    axT.text(saving.index[0], pre, f" 2012-19 trend {pre:.1f}%", va="bottom", ha="left",
             fontsize=8.5, color=C.C_GREY)
    C.mark_periods(axT, shade=True)
    axT.set_ylabel("saving rate (% of disp. income)")
    axT.set_title("Structural or cyclical? Trend vs cycle in the euro-area saving rate",
                  fontweight="bold")
    axT.legend(frameon=False, fontsize=9, loc="upper left")

    axB.axhline(0, color="black", lw=0.8)
    axB.plot(cycle.index, C.zscore(cycle), color=C.C_MAIN, lw=2.0, label="saving CYCLE (z)")
    for (name, s), color in zip(drivers.items(), [C.C_ACCENT, C.C_ORANGE, C.C_GREY]):
        s = s.reindex(cycle.index).interpolate()
        axB.plot(s.index, C.zscore(s), color=color, lw=1.3, alpha=0.9, label=name)
    C.mark_periods(axB, shade=True, labels=False)
    axB.set_ylabel("cycle & drivers (z)")
    axB.set_xlabel("date")
    axB.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")

    C.caveat(fig, "HP filter (λ=1600) with the 2020-21 COVID forced-saving quarters EXCLUDED "
                  "(interpolated), so the trend reflects behaviour, not the lockdown spike -- which "
                  "instead appears as the large positive cycle in the lower panel.")
    C.savefig(fig, "structural_vs_cyclical.png")

    out = pd.DataFrame({"saving": saving, "trend": trend, "cycle": cycle})
    out.to_csv(os.path.join(C.DATA, "structural_vs_cyclical.csv"))
    with open(os.path.join(C.DATA, "structural_vs_cyclical.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'structural_vs_cyclical.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
