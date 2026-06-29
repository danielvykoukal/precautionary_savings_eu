#!/usr/bin/env python3
"""
The before-and-after test — did saving fall when rates were cut?
===============================================================

A simple, intuitive check. If people saved more because saving suddenly paid
(yield-chasing), then when the ECB reversed course and CUT rates in 2024-25,
saving should ease back. If they saved out of fear (precaution), saving should
stay high until people feel safe again, regardless of rates.

We line up the euro-area household saving rate against the ECB policy rate and
measure what saving did during the hiking phase vs the cutting phase.

Reads ../data (saving rate + ECB rate). Writes a figure + a results md.
    python saving_vs_rates_reversal.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as cm

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def main():
    say("#" * 70)
    say("# Before-and-after — saving rate vs the ECB rate (hiking vs cutting)")
    say("#" * 70)

    saving = cm.load_quarterly("ea_saving_rate_quarterly.csv", "saving")
    rate = cm.load_quarterly("ecb_rate.csv", "rate")
    df = pd.concat([saving, rate], axis=1).dropna()
    df.index = pd.PeriodIndex(df.index, freq="Q").to_timestamp()
    df = df[df.index >= "2018-01-01"]   # focus on the modern episode

    # locate the rate trough before the hikes and the rate peak
    rate_peak_date = df["rate"].idxmax()
    rate_peak = df.loc[rate_peak_date, "rate"]
    pre = df[df.index < "2022-01-01"]
    trough_rate = pre["rate"].min() if len(pre) else df["rate"].min()
    latest = df.index.max()

    sav_at = lambda d: float(df.loc[d, "saving"])
    say(f"\nECB rate: trough ~{trough_rate:.2f}% (pre-2022) -> peak "
        f"{rate_peak:.2f}% ({rate_peak_date.date()}) -> {df['rate'].iloc[-1]:.2f}% "
        f"({latest.date()})")

    # saving change over the hiking phase (2022Q1 -> rate peak) and the cutting
    # phase (rate peak -> latest)
    hike = df[(df.index >= "2022-01-01") & (df.index <= rate_peak_date)]
    cut = df[df.index >= rate_peak_date]
    if len(hike) >= 2:
        say(f"\nHIKING phase {hike.index.min().date()}->{hike.index.max().date()}: "
            f"rate {hike['rate'].iloc[0]:.2f}->{hike['rate'].iloc[-1]:.2f}%, "
            f"saving {hike['saving'].iloc[0]:.1f}->{hike['saving'].iloc[-1]:.1f}% "
            f"({hike['saving'].iloc[-1]-hike['saving'].iloc[0]:+.1f} pp)")
    if len(cut) >= 2:
        d_rate = cut["rate"].iloc[-1] - cut["rate"].iloc[0]
        d_sav = cut["saving"].iloc[-1] - cut["saving"].iloc[0]
        say(f"CUTTING phase {cut.index.min().date()}->{cut.index.max().date()}: "
            f"rate {cut['rate'].iloc[0]:.2f}->{cut['rate'].iloc[-1]:.2f}% "
            f"({d_rate:+.2f} pp), saving {cut['saving'].iloc[0]:.1f}->"
            f"{cut['saving'].iloc[-1]:.1f}% ({d_sav:+.1f} pp)")
        if d_rate < -0.25:
            verdict = ("saving eased as rates were cut — consistent with yield-chasing"
                       if d_sav < -0.2 else
                       "saving did NOT ease despite rate cuts — more consistent with "
                       "precaution / stickiness")
            say(f"  => {verdict}.")

    corr = df[df.index >= "2021-01-01"][["saving", "rate"]].corr().iloc[0, 1]
    say(f"\ncorrelation(saving, ECB rate), 2021+ : {corr:+.2f}")
    say("Reading: be cautious. The phase moves are small (~0.5 pp each way), and the "
        "raw 2021+ correlation is confounded by the post-COVID unwind — saving was "
        "drifting down from its 2020-21 highs while rates rose, which can flip the "
        "sign. So this before/after check is weak and suggestive at best, not decisive "
        "on its own; the composition test (follow_the_money.py) is the stronger one.")

    # ---------------- figure: twin-axis, ALIGNED on the post-2022 window ----------------
    # Pick the right-axis (rate) scale so the rate line overlays the saving line as
    # closely as possible after 2022: best affine fit saving ~ a + b*rate there, then
    # map the left limits [s_lo,s_hi] to right limits via that fit.
    post = df[df.index >= "2022-01-01"]
    if len(post) >= 3 and post["rate"].std() > 0:
        b, a = np.polyfit(post["rate"].values, post["saving"].values, 1)
        r_post = post[["saving", "rate"]].corr().iloc[0, 1]
        say(f"\npost-2022 alignment: saving ≈ {a:.2f} + {b:.2f}·rate "
            f"(corr {r_post:+.2f}); right axis scaled so the lines overlay after 2022.")
    else:
        b, a = 1.0, float(df["saving"].mean())

    fig, ax1 = plt.subplots(figsize=(10, 5.4))
    ax2 = ax1.twinx()
    ax2.grid(False)
    if len(hike):
        ax1.axvspan(hike.index.min(), rate_peak_date, color=cm.C_RED, alpha=0.06)
    if len(cut) >= 2:
        ax1.axvspan(rate_peak_date, latest, color=cm.C_BLUE, alpha=0.06)
    l1, = ax1.plot(df.index, df["saving"], color=cm.C_NAVY, lw=2.6,
                   label="household saving rate (left)")
    l2, = ax2.plot(df.index, df["rate"], color=cm.C_RED, lw=2.0, ls="--",
                   label="ECB policy rate (right)")
    ax1.axvline(pd.Timestamp("2022-02-24"), color="grey", ls=":", lw=1)

    s_lo, s_hi = float(df["saving"].min()) - 0.7, float(df["saving"].max()) + 0.7
    ax1.set_ylim(s_lo, s_hi)
    if b > 0:                                   # map left (saving) limits -> right (rate)
        ax2.set_ylim((s_lo - a) / b, (s_hi - a) / b)

    ax1.set_ylabel("household saving rate (% of disposable income)", color=cm.C_NAVY)
    ax2.set_ylabel("ECB policy rate (%)", color=cm.C_RED)
    ax1.set_xlabel("")
    ax1.set_title("Saving tracks the ECB rate after 2022 (axes aligned on 2022+)\n"
                  "red = hiking phase, blue = cutting phase", fontweight="bold")
    ax1.legend(handles=[l1, l2], frameon=False, loc="upper left", fontsize=9)
    cm.savefig(fig, "saving_vs_rates_reversal.png")

    df.to_csv(os.path.join(cm.DATA, "saving_vs_rates.csv"))
    with open(os.path.join(cm.DATA, "saving_vs_rates_reversal.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extension_follow_money/data/saving_vs_rates_reversal.md")


if __name__ == "__main__":
    main()
