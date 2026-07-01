#!/usr/bin/env python3
"""
Feedback #2 --- Risk premia and geopolitical tension: can we observe it?
========================================================================

Supervisor feedback: "look into risk premia, which increase with geopolitical
tension — can we observe it somewhere?"

Yes. Three euro-area risk premia are free, keyless, and observable, and we can
line them up against the Geopolitical Risk (GPR) index the project already pulls:

  * Credit risk premium       : ICE BofA Euro High-Yield OAS   (FRED BAMLHE00EHYIOAS)
  * Sovereign / fragmentation : Italy 10y - Germany 10y (BTP-Bund)
                                (FRED IRLTLT01ITM156N - IRLTLT01DEM156N)
  * Risk aversion / implied vol: VIX                            (FRED VIXCLS)
    (VSTOXX is the euro-area analogue — Eurex/STOXX, not cleanly keyless; VIX is
     the free global proxy and tracks VSTOXX closely.)

We overlay each premium on GPR, report their co-movement (levels and monthly
changes), and event-window the Feb-2022 invasion. The economic link back to the
project: when geopolitical tension lifts risk premia and uncertainty, households'
precautionary motive strengthens and portfolios tilt toward liquidity.

    python risk_premia.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

# --- run from the flattened repo layout: top-level data/ & figures/, tagged CSVs
import os as _os, glob as _glob
C.ROOT = _os.path.dirname(_os.path.dirname(C.HERE))
C.ROOT_DATA = _os.path.join(C.ROOT, "data")
C.DATA = _os.path.join(C.ROOT, "data")
C.FIG = _os.path.join(C.ROOT, "figures")
_ORC = C.root_csv
def _TRC(name, required=True):
    import pandas as _pd
    if not _os.path.exists(_os.path.join(C.ROOT_DATA, name)):
        _h = _glob.glob(_os.path.join(C.ROOT_DATA, "?_" + name))
        if _h:
            return _pd.read_csv(_h[0])
    return _ORC(name, required)
C.root_csv = _TRC

REPORT = []
INVASION = pd.Timestamp("2022-02-24")


def say(line=""):
    print(line)
    REPORT.append(str(line))


def monthly(s):
    """Series indexed by date -> month-start mean."""
    return s.resample("MS").mean()


def load_gpr():
    d = C.root_csv("gpr.csv")
    d = d.rename(columns={d.columns[0]: "date"})
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    col = "gpr" if "gpr" in d.columns else d.columns[1]
    d[col] = pd.to_numeric(d[col], errors="coerce")
    return monthly(d.dropna(subset=["date", col]).set_index("date")[col].rename("gpr"))


def event_window(s, anchor=INVASION, pre_m=1, post_m=6):
    """Level just before `anchor`, peak in the `post_m` months after, and the jump."""
    s = s.dropna()
    pre = s[s.index <= anchor]
    base = float(pre.iloc[-1]) if len(pre) else np.nan
    after = s[(s.index > anchor) & (s.index <= anchor + pd.DateOffset(months=post_m))]
    peak = float(after.max()) if len(after) else np.nan
    return base, peak, peak - base


def main():
    say("#" * 72)
    say("# Risk premia vs geopolitical tension (GPR)")
    say("#" * 72)

    prem = {}   # label -> monthly Series
    sources = {}

    # credit premium
    try:
        hy = C.get_fred_series("BAMLHE00EHYIOAS", "hy")
        prem["Euro HY credit spread (OAS, %)"] = monthly(hy.set_index("date")["hy"])
        sources["credit"] = "FRED BAMLHE00EHYIOAS"
    except Exception as e:
        say(f"  credit spread failed: {e}")

    # sovereign / fragmentation premium: IT 10y - DE 10y. FRED first; if FRED is
    # unreachable, fall back to the ECB Data Portal (Maastricht 10y gov-bond yields)
    # so this spread (the cleanest euro-area gauge) still renders.
    btp = None
    try:
        it = C.get_fred_series("IRLTLT01ITM156N", "it").set_index("date")["it"]
        de = C.get_fred_series("IRLTLT01DEM156N", "de").set_index("date")["de"]
        btp = (monthly(it) - monthly(de)).dropna().rename("btp_bund")
        sources["sovereign"] = "FRED IRLTLT01ITM156N - IRLTLT01DEM156N"
    except Exception as e:
        say(f"  sovereign spread via FRED failed ({e}); trying ECB")
        try:
            it = C.ecb_sdmx("IRS", "M.IT.L.L40.CI.0000.EUR.N.Z").set_index("date")["value"]
            de = C.ecb_sdmx("IRS", "M.DE.L.L40.CI.0000.EUR.N.Z").set_index("date")["value"]
            btp = (it.resample("MS").mean() - de.resample("MS").mean()).dropna().rename("btp_bund")
            sources["sovereign"] = "ECB IRS Maastricht 10y (IT - DE)"
        except Exception as e2:
            say(f"  sovereign spread via ECB failed: {e2}")
    if btp is not None:
        prem["Italy-Germany 10y spread (pp)"] = btp

    # implied volatility / risk aversion
    try:
        vix = C.get_fred_series("VIXCLS", "vix")
        prem["VIX (implied equity vol)"] = monthly(vix.set_index("date")["vix"])
        sources["vol"] = "FRED VIXCLS (VSTOXX analogue)"
    except Exception as e:
        say(f"  VIX failed: {e}")

    if not prem:
        say("\nNo risk-premium series available.")
        with open(os.path.join(C.DATA, "risk_premia.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    try:
        gpr = load_gpr()
    except Exception as e:
        say(f"  GPR load failed ({e}); correlations skipped")
        gpr = None

    # ---- co-movement with GPR + the invasion event window ----
    say("\nObservable? Co-movement with the GPR index and the Feb-2022 jump:")
    say(f"{'premium':<34}{'corr lvl':>9}{'corr Δ':>8}{'Jan-22':>9}{'2022 peak':>11}{'jump':>8}")
    rows = []
    for label, s in prem.items():
        rl = rd = np.nan
        if gpr is not None:
            j = pd.concat([s.rename("x"), gpr], axis=1).dropna()
            if len(j) > 24:
                rl = j["x"].corr(j["gpr"])
                rd = j["x"].diff().corr(j["gpr"].diff())
        base, peak, jump = event_window(s)
        say(f"{label:<34}{rl:>+9.2f}{rd:>+8.2f}{base:>9.2f}{peak:>11.2f}{jump:>+8.2f}")
        rows.append({"premium": label, "corr_level": rl, "corr_change": rd,
                     "jan_2022": base, "peak_2022": peak, "jump": jump})

    say("\nReading: positive correlations and a clear upward jump after Feb-2022 = "
        "yes, risk premia are observable and they rise with geopolitical tension. "
        "The sovereign (BTP-Bund) and credit spreads are the cleanest euro-area "
        "fragmentation/risk gauges; VIX/VSTOXX is the forward-looking risk-aversion read.")

    # ---- figure: premia vs GPR ----
    fig, axes = plt.subplots(2, 1, figsize=(10, 8.4), sharex=True,
                             gridspec_kw={"hspace": 0.16})
    # top: credit + sovereign spreads (left) vs GPR (right)
    axT, axTg = axes[0], axes[0].twinx()
    axTg.grid(False)
    colors = [C.C_HOT, C.C_MAIN, C.C_ORANGE]
    spread_labels = [l for l in prem if "VIX" not in l]
    for label, color in zip(spread_labels, colors):
        axT.plot(prem[label].index, prem[label].values, color=color, lw=1.8, label=label)
    if gpr is not None:
        axTg.fill_between(gpr.index, gpr.values, color=C.C_GREY, alpha=0.18)
        axTg.plot(gpr.index, gpr.values, color=C.C_GREY, lw=1.0, label="GPR (right)")
        axTg.set_ylabel("GPR index", color=C.C_GREY)
    C.mark_periods(axT, shade=True)
    axT.set_ylabel("spread (% / pp)")
    axT.set_title("Risk premia rise with geopolitical tension\n"
                  "euro-area credit & sovereign spreads vs the GPR index",
                  fontweight="bold")
    h1, l1 = axT.get_legend_handles_labels()
    h2, l2 = axTg.get_legend_handles_labels()
    axT.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")

    # bottom: VIX (z) and GPR (z)
    axB = axes[1]
    if "VIX (implied equity vol)" in prem:
        axB.plot(prem["VIX (implied equity vol)"].index,
                 C.zscore(prem["VIX (implied equity vol)"]),
                 color=C.C_COOL, lw=1.6, label="VIX (z)")
    if gpr is not None:
        axB.plot(gpr.index, C.zscore(gpr), color=C.C_GREY, lw=1.6, label="GPR (z)")
    C.mark_periods(axB, shade=True, labels=False)
    axB.axhline(0, color="black", lw=0.6, alpha=0.5)
    axB.set_ylabel("standardised (z)")
    axB.set_xlabel("date")
    axB.legend(frameon=False, fontsize=8, loc="upper left")
    C.caveat(fig, "Euro-area risk premia vs the GPR index. Spreads/implied vol jump with "
                  "geopolitical tension (Feb-2022 line); shaded = COVID and the energy/hiking window.")
    C.savefig(fig, "I_risk_premia_vs_gpr.png")

    pd.DataFrame(rows).to_csv(os.path.join(C.DATA, "risk_premia_summary.csv"), index=False)
    out = pd.concat(list(prem.values()) + ([gpr] if gpr is not None else []), axis=1)
    out.to_csv(os.path.join(C.DATA, "risk_premia_series.csv"))
    say("\nsources: " + "; ".join(f"{k}={v}" for k, v in sources.items()))
    with open(os.path.join(C.DATA, "risk_premia.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'risk_premia.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
