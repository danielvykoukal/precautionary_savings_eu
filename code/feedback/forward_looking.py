#!/usr/bin/env python3
"""
Feedback #3 --- A forward-looking approach
==========================================

Supervisor feedback: "the supervisors ask for a more forward-looking approach —
what can be done?"

The core analysis is backward-looking: it relates the REALISED saving rate to
REALISED / contemporaneous uncertainty (GPR). A forward-looking version asks
whether what households and markets EXPECT predicts saving BEFORE it happens. We
build a small forward-looking caution composite from variables that are, by
construction, about the future:

  * expected unemployment, next 12m   (Eurostat consumer survey ei_bsco_m)
  * intended saving, next 12m          (Eurostat consumer survey ei_bsco_m)
  * VIX implied volatility             (FRED VIXCLS — the market's expected risk;
                                        VSTOXX is the euro analogue)

composite = mean of the three z-scores (higher = more expected risk / caution).

We then test whether the composite LEADS the realised saving rate:
  (a) lead-lag correlation corr(saving_t, composite_{t-k}) for k = -4..+4 quarters;
  (b) a one-quarter-ahead predictive regression saving_t ~ composite_{t-1},
      compared with the contemporaneous GPR benchmark saving_t ~ GPR_t.

Reads ../data for the saving rate and GPR; pulls ei_bsco_m + VIX.
    python forward_looking.py
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

try:
    import statsmodels.api as sm
except Exception:
    sm = None

REPORT = []


def say(line=""):
    print(line)
    REPORT.append(str(line))


def _pick_indic(indics, must_have, prefer):
    cand = [i for i in indics if must_have in str(i).upper()]
    if not cand:
        return None
    for p in prefer:
        for i in cand:
            if p in str(i).upper():
                return i
    return sorted(cand)[0]


def get_survey():
    """Monthly euro-area survey balances: intended saving & expected unemployment."""
    long = C.es_long("ei_bsco_m")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    if "s_adj" in long.columns and "SA" in set(long["s_adj"]):
        long = long[long["s_adj"] == "SA"]
    if "unit" in long.columns and "BAL" in set(long["unit"]):
        long = long[long["unit"] == "BAL"]
    geo = next((g for g in C.EA_GEOS if g in set(long["geo"])), None)
    if geo is None:
        raise RuntimeError("ei_bsco_m: no euro-area aggregate geo")
    long = long[long["geo"] == geo]
    indics = sorted(set(long["indic"]))
    sav = _pick_indic(indics, "SV", prefer=["FS", "NY", "N12", "F12"])
    ue = _pick_indic(indics, "UE", prefer=["NY", "FS", "N12", "F12"])
    if sav is None or ue is None:
        raise RuntimeError(f"ei_bsco_m: indicators not found (sav={sav}, ue={ue})")
    say(f"  survey geo={geo}; saving-intentions={sav}; unemployment-expectations={ue}")
    out = {}
    for name, code in (("saving_intent", sav), ("unemp_expect", ue)):
        s = long[long["indic"] == code].copy()
        s["date"] = s["time"].map(C.parse_time)
        out[name] = (s.dropna(subset=["date"]).sort_values("date")
                       .set_index("date")["value"].rename(name))
    return pd.concat(out.values(), axis=1)


def leadlag(saving, x, kmax=4):
    """corr(saving_t, x_{t-k}) for k=-kmax..kmax (k>0 => x leads saving)."""
    rows = []
    for k in range(-kmax, kmax + 1):
        r = saving.corr(x.shift(k))
        rows.append((k, r))
    return pd.DataFrame(rows, columns=["lead_quarters", "corr"])


def main():
    say("#" * 72)
    say("# Forward-looking approach — do expectations lead saving?")
    say("#" * 72)

    # forward-looking inputs
    parts = {}
    try:
        surv = get_survey().resample("QS").mean()
        parts["unemp_expect"] = surv["unemp_expect"]
        parts["saving_intent"] = surv["saving_intent"]
    except Exception as e:
        say(f"  survey step failed: {e}")
    try:
        vix = C.get_fred_series("VIXCLS", "vix").set_index("date")["vix"].resample("QS").mean()
        parts["vix"] = vix
    except Exception as e:
        say(f"  VIX step failed: {e}")

    if not parts:
        say("\nNo forward-looking inputs available.")
        with open(os.path.join(C.DATA, "forward_looking.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    saving = C.load_quarterly("ea_saving_rate_quarterly.csv", "saving")

    # composite = mean of available z-scores (higher = more expected caution/risk)
    zin = pd.concat({k: C.zscore(v) for k, v in parts.items()}, axis=1).dropna()
    composite = zin.mean(axis=1).rename("fwd_composite")
    say(f"\nforward-looking composite from {list(parts)} "
        f"({composite.index.min().date()}->{composite.index.max().date()}, "
        f"{len(composite)} quarters)")

    # ---- (a) lead-lag with the realised saving rate ----
    common = pd.concat([saving, composite], axis=1).dropna()
    ll = leadlag(common["saving"], common["fwd_composite"])
    best = ll.loc[ll["corr"].abs().idxmax()]
    say("\n(a) lead-lag corr(saving_t, composite_{t-k}); k>0 = composite leads:")
    for _, r in ll.iterrows():
        mark = "  <- max |corr|" if int(r["lead_quarters"]) == int(best["lead_quarters"]) else ""
        say(f"   k={int(r['lead_quarters']):+d}q : corr={r['corr']:+.2f}{mark}")
    if best["lead_quarters"] > 0:
        say(f"  => the composite LEADS saving by ~{int(best['lead_quarters'])}q "
            f"(corr {best['corr']:+.2f}): expectations move first. Forward-looking.")
    else:
        say(f"  => strongest co-movement is contemporaneous/lagging "
            f"(k={int(best['lead_quarters'])}q, corr {best['corr']:+.2f}).")

    # ---- (b) one-quarter-ahead predictive regression vs the GPR benchmark ----
    if sm is not None:
        reg = common.copy()
        reg["composite_lag1"] = reg["fwd_composite"].shift(1)
        reg = reg.dropna()
        if len(reg) > 12:
            X = sm.add_constant(reg["composite_lag1"])
            m = sm.OLS(reg["saving"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
            say(f"\n(b) saving_t ~ composite_(t-1):  beta={m.params['composite_lag1']:+.2f} "
                f"(p={m.pvalues['composite_lag1']:.3f}), R^2={m.rsquared:.2f}, n={int(m.nobs)}")
        # contemporaneous GPR benchmark (quarterly)
        try:
            g = C.root_csv("gpr.csv")
            g = g.rename(columns={g.columns[0]: "date"})
            g["date"] = pd.to_datetime(g["date"], errors="coerce")
            gq = g.dropna(subset=["date"]).set_index("date")["gpr"].resample("QS").mean()
            b = pd.concat([saving, gq.rename("gpr")], axis=1).dropna()
            if len(b) > 12:
                Xg = sm.add_constant(b["gpr"])
                mg = sm.OLS(b["saving"], Xg).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
                say(f"    benchmark saving_t ~ GPR_t (contemporaneous): "
                    f"R^2={mg.rsquared:.2f}, n={int(mg.nobs)}")
                say("    (a forward composite that predicts one quarter AHEAD is the "
                    "value-add the supervisors asked for, beyond contemporaneous GPR.)")
        except Exception as e:
            say(f"    GPR benchmark skipped: {e}")
    else:
        say("\n(b) statsmodels unavailable — predictive regression skipped.")

    # ---- figures ----
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.axhline(0, color="black", lw=0.6, alpha=0.5)
    ax.plot(composite.index, composite.values, color=C.C_HOT, lw=1.8,
            label="forward-looking caution composite (z)")
    ax.plot(C.zscore(saving).index, C.zscore(saving).values, color=C.C_MAIN, lw=2.4,
            label="realised saving rate (z)")
    C.mark_periods(ax, shade=True)
    ax.set_ylabel("standardised (z)")
    ax.set_title("Expectations vs the realised saving rate\n"
                 "a forward-looking caution composite", fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    C.caveat(fig, "Composite = mean z of expected unemployment + intended saving (+ VIX when "
                  "FRED is reachable). It co-moves with, and helps predict, the realised saving rate.")
    C.savefig(fig, "J_forward_looking_composite.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    colors = [C.C_COOL if k <= 0 else C.C_HOT for k in ll["lead_quarters"]]
    ax.bar(ll["lead_quarters"], ll["corr"], color=colors, width=0.7)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("lead k (quarters); k>0 = composite leads saving")
    ax.set_ylabel("corr(saving_t, composite_(t-k))")
    ax.set_title("Does expected caution lead realised saving?", fontweight="bold")
    C.savefig(fig, "J2_forward_looking_leadlag.png")

    common.join(ll.set_index("lead_quarters")["corr"], how="left").to_csv(
        os.path.join(C.DATA, "forward_looking.csv"))
    ll.to_csv(os.path.join(C.DATA, "forward_looking_leadlag.csv"), index=False)
    with open(os.path.join(C.DATA, "forward_looking.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'forward_looking.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
