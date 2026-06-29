#!/usr/bin/env python3
"""
Extension II(b) --- Direct survey evidence: saving intentions & job-loss fear
============================================================================

Idea. Rather than infer precaution from a noisy macro proxy, ask households. The
Joint Harmonised EU Consumer Survey (Eurostat ei_bsco_m) publishes monthly
balances for "savings over the next 12 months" and "unemployment expectations
over the next 12 months". The precautionary story makes a sharp, testable
prediction: after 2022 both should rise together with the actual saving rate --
households both *fear job loss more* and *intend to save more*. This is the most
face-valid evidence short of micro data, and it is fully free.

We plot the two survey balances against the realised saving rate and report their
co-movement. Reads ../data for the saving rate; pulls ei_bsco_m. Writes figures+md.
    python saving_intentions.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def _pick_indic(indics, must_have, prefer):
    """Choose an indic code containing `must_have`; prefer one also containing
    any token in `prefer` (e.g. the 'next 12 months' variant)."""
    cand = [i for i in indics if must_have in str(i).upper()]
    if not cand:
        return None
    for p in prefer:
        for i in cand:
            if p in str(i).upper():
                return i
    return sorted(cand)[0]


def get_survey_series():
    """Return monthly [date, savings, unemployment] balances for a euro-area geo."""
    long = C.es_long("ei_bsco_m")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    if "s_adj" in long.columns and "SA" in set(long["s_adj"]):
        long = long[long["s_adj"] == "SA"]
    if "unit" in long.columns and "BAL" in set(long["unit"]):
        long = long[long["unit"] == "BAL"]
    geo = next((g for g in ("EA20", "EA19", "EA", "EU27_2020")
                if g in set(long["geo"])), None)
    if geo is None:
        raise RuntimeError("ei_bsco_m: no euro-area aggregate geo")
    long = long[long["geo"] == geo]
    indics = sorted(set(long["indic"]))
    print(f"  [ei_bsco_m] geo={geo}; indic codes: {indics}")
    sav = _pick_indic(indics, "SV", prefer=["FS", "NY", "N12", "F12"])
    ue = _pick_indic(indics, "UE", prefer=["NY", "FS", "N12", "F12"])
    if sav is None or ue is None:
        raise RuntimeError(f"ei_bsco_m: could not find savings ({sav}) / "
                           f"unemployment ({ue}) indicators")
    say(f"  savings-intentions indicator = {sav}; unemployment-fear = {ue}")
    frames = {}
    for name, code in (("savings", sav), ("unemployment", ue)):
        s = long[long["indic"] == code].copy()
        s["date"] = s["time"].map(C.parse_time)
        frames[name] = (s.dropna(subset=["date"]).sort_values("date")
                          .set_index("date")["value"].rename(name))
    df = pd.concat(frames.values(), axis=1).dropna()
    df = df[df.index >= C.START]
    return df.reset_index().rename(columns={"index": "date"}), geo


def main():
    say("#" * 70)
    say("# Survey evidence — saving intentions & unemployment fear vs saving rate")
    say("#" * 70)
    try:
        surv, geo = get_survey_series()
    except Exception as e:
        say(f"\nFAILED: {e}")
        with open(os.path.join(C.DATA, "saving_intentions.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    saving_q = C.load_quarterly("ea_saving_rate_quarterly.csv", "saving")

    # correlations on a common quarterly frame
    sq = (surv.set_index("date").resample("QS").mean())
    aligned = pd.concat([saving_q, sq], axis=1).dropna()
    aligned_post = aligned[aligned.index >= "2010-01-01"]
    say(f"\nco-movement with the realised saving rate "
        f"(quarterly, {aligned.index.min().date()}->{aligned.index.max().date()}):")
    for col in ("savings", "unemployment"):
        r = aligned["saving"].corr(aligned[col])
        r10 = aligned_post["saving"].corr(aligned_post[col])
        say(f"  corr(saving, {col:<12}) = {r:+.2f}   (2010+: {r10:+.2f})")
    say("  (Precaution predicts BOTH positive: more fear and more intended saving "
        "accompany the higher realised saving rate.)")

    # ---- plot: survey balances (z) + saving rate (z) ----
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.axhline(0, color="black", lw=0.6, alpha=0.5)
    ax.plot(surv["date"], C.zscore(surv["unemployment"]), color=C.C_HOT, lw=1.6,
            label="unemployment expectations (z)")
    ax.plot(surv["date"], C.zscore(surv["savings"]), color=C.C_COOL, lw=1.6,
            label="saving intentions, next 12m (z)")
    sav_z = C.zscore(saving_q)
    ax.plot(sav_z.index, sav_z.values, color=C.C_MAIN, lw=2.6,
            label="realised saving rate (z)")
    ax.axvline(pd.Timestamp("2022-02-24"), color="grey", ls="--", lw=1)
    ax.set_ylabel("standardised (z-score)")
    ax.set_title(f"Households say they fear job loss and intend to save more\n"
                 f"Eurostat consumer survey vs realised saving ({geo})",
                 fontweight="bold")
    ax.legend(frameon=False, ncol=3, fontsize=8, loc="upper left")
    C.savefig(fig, "saving_intentions.png")

    surv.to_csv(os.path.join(C.DATA, "saving_intentions.csv"), index=False)
    with open(os.path.join(C.DATA, "saving_intentions.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print("\nWrote extensions/data/saving_intentions.md")


if __name__ == "__main__":
    main()
