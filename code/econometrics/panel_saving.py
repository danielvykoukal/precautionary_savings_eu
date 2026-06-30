#!/usr/bin/env python3
"""
Country-panel regression of the household saving rate on its drivers
====================================================================

Two-way fixed-effects panel (country + quarter) on the quarterly panel built by
build_country_panel.py:

    saving_it = a_i + g_t + b1 spread_it + b2 sav_intent_it + b3 unemp_exp_it
                + b4 headline_infl_it + b5 energy_infl_it + e_it

Country FE (a_i) absorb the structural North–South level differences; quarter FE
(g_t) absorb euro-area-wide shocks (the common ECB rate, common uncertainty,
seasonality). Identification is then from CROSS-COUNTRY variation — exactly what
the euro-area single time series cannot give. SEs clustered by country.

Outputs a coefficient table (data/P_panel_results.md) and a standardized-coefficient
forest plot (figures/P_panel_coefficients.png).
    python panel_saving.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from linearmodels.panel import PanelOLS, PooledOLS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")

DRIVERS = ["spread", "sav_intent", "unemp_exp", "headline_infl", "energy_infl"]
LABELS = {
    "spread": "Sovereign spread (10y − Bund, pp)",
    "sav_intent": "Saving intentions (survey balance)",
    "unemp_exp": "Unemployment expectations (balance)",
    "headline_infl": "Headline inflation (%)",
    "energy_infl": "Energy inflation (%)",
}
REPORT = []


def say(line=""):
    print(line); REPORT.append(str(line))


def load():
    df = pd.read_csv(os.path.join(DATA, "P_country_panel_quarterly.csv"))
    df = df.dropna(subset=["saving"] + DRIVERS).copy()
    # entity = country, time = quarter (Timestamp at quarter start, for ordering)
    df["time"] = pd.PeriodIndex(df["quarter"], freq="Q").to_timestamp()
    df = df.set_index(["geo", "time"]).sort_index()
    return df


def fit(df, X, entity=True, time=True):
    mod = PanelOLS(df["saving"], df[X], entity_effects=entity, time_effects=time,
                   drop_absorbed=True, check_rank=False)
    return mod.fit(cov_type="clustered", cluster_entity=True)


def main():
    df = load()
    say("#" * 70)
    say("# Country panel: household saving rate on its drivers (two-way FE)")
    say("#" * 70)
    tmin = pd.Period(df.index.get_level_values("time").min(), freq="Q")
    tmax = pd.Period(df.index.get_level_values("time").max(), freq="Q")
    say(f"  {df.shape[0]} obs, {df.index.get_level_values('geo').nunique()} countries, "
        f"{tmin}–{tmax}")
    say(f"  countries: {sorted(df.index.get_level_values('geo').unique())}")

    # --- main spec: two-way FE, raw units, clustered SE ---
    res = fit(df, DRIVERS)
    say("\n=== Two-way FE (country + quarter), SE clustered by country ===")
    say(f"  within R-squared = {res.rsquared_within:.3f};  overall = {res.rsquared:.3f}")
    say(f"{'driver':<40}{'coef':>9}{'se':>8}{'t':>7}{'p':>8}")
    for v in DRIVERS:
        say(f"{LABELS[v]:<40}{res.params[v]:>9.3f}{res.std_errors[v]:>8.3f}"
            f"{res.tstats[v]:>7.2f}{res.pvalues[v]:>8.3f}")

    # --- robustness: country-FE only, and pooled ---
    res_c = fit(df, DRIVERS, entity=True, time=False)
    pooled = PooledOLS(df["saving"], df[DRIVERS].assign(const=1.0)).fit(
        cov_type="clustered", cluster_entity=True)
    say("\n=== robustness: coefficient on each driver across specifications ===")
    say(f"{'driver':<40}{'2-way FE':>10}{'country FE':>12}{'pooled':>9}")
    for v in DRIVERS:
        say(f"{LABELS[v]:<40}{res.params[v]:>10.3f}{res_c.params[v]:>12.3f}"
            f"{pooled.params[v]:>9.3f}")

    # --- standardized betas for the forest plot (comparable magnitudes) ---
    z = df.copy()
    for v in DRIVERS + ["saving"]:
        z[v] = (z[v] - z[v].mean()) / z[v].std(ddof=0)
    res_z = fit(z, DRIVERS)
    say("\n=== standardized betas (SD of saving per 1 SD of driver) ===")
    for v in DRIVERS:
        say(f"  {LABELS[v]:<40}{res_z.params[v]:>+7.3f}  "
            f"[{res_z.conf_int().loc[v, 'lower']:+.3f}, {res_z.conf_int().loc[v, 'upper']:+.3f}]")

    plot_forest(res_z)

    with open(os.path.join(DATA, "P_panel_results.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(DATA, 'P_panel_results.md'), ROOT)}")


def plot_forest(res_z):
    ci = res_z.conf_int()
    vs = DRIVERS[::-1]
    y = np.arange(len(vs))
    coefs = [res_z.params[v] for v in vs]
    lo = [ci.loc[v, "lower"] for v in vs]
    hi = [ci.loc[v, "upper"] for v in vs]
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.axvline(0, color="black", lw=0.9)
    for i, v in enumerate(vs):
        sig = res_z.pvalues[v] < 0.05
        col = "#1f4e79" if coefs[i] >= 0 else "#c0392b"
        ax.plot([lo[i], hi[i]], [i, i], color=col, lw=2.4, alpha=0.9 if sig else 0.4)
        ax.scatter([coefs[i]], [i], color=col, s=70 if sig else 45,
                   zorder=5, edgecolor="white", alpha=0.95 if sig else 0.5)
    ax.set_yticks(y); ax.set_yticklabels([LABELS[v] for v in vs], fontsize=9.5)
    ax.set_xlabel("standardized effect on the saving rate (SD per 1 SD of driver, 95% CI)")
    ax.set_title("What moves household saving across euro-area countries?\n"
                 "two-way fixed-effects panel (country + quarter), 16 countries, 2000–2025",
                 fontweight="bold")
    ax.text(0.985, 0.04, "solid = significant at 5%, faded = not",
            transform=ax.transAxes, ha="right", fontsize=8, color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "P_panel_coefficients.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/P_panel_coefficients.png")


if __name__ == "__main__":
    main()
