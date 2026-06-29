#!/usr/bin/env python3
"""
Precautionary saving in Europe — STEP 2: figures
================================================

Reads the tidy CSVs written by 01_collect_data.py and draws every descriptive
chart into ./figures. It does NO downloading and NO econometrics: it only reads
./data and writes ./figures, so it is fully reproducible offline once step 1 has
run. Each chart is skipped (with a message) if its input CSV is missing.

Charts:
  A  Euro-area saving rate vs uncertainty (+ rate & inflation drivers)
  B  Energy shock vs rise in saving, by country (scatter)
  B2 Household saving rate by country (bar)
  C  Median saving rate by income quintile (latest ICW snapshot)
  C2 Expected unemployment by income group (ECB CES)
  D  Saving rate by quintile across ICW snapshots (slope)
  E  Saving rate by quintile, annual (OECD), per country  [if CSVs present]
  F  Saving by income group since 2020 (ECB CES)          [if CSV present]

Run
---
    python 02_make_figures.py
"""

import os
import glob
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed; we save PNGs
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

START = "1999-01-01"  # left edge for the time-series panels

# Editorial grouping for colour-coding (refine before publishing).
# "High exposure" = large Russian-gas reliance pre-2022 and/or frontline CEE.
HIGH_EXPOSURE = {"DE", "AT", "FI", "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT"}

QLABEL = {1: "Q1 (lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (highest)"}
QCOLORS = {1: "#c0392b", 2: "#e67e22", 3: "#7f8c8d", 4: "#2e86c1", 5: "#1f4e79"}

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})


def _path(name):
    return os.path.join(DATA, name)


def _read(name):
    """Read a CSV from ./data, or None if it does not exist."""
    p = _path(name)
    return pd.read_csv(p) if os.path.exists(p) else None


def _to_quarterly(df):
    """[date, value] (any first two cols) -> quarterly mean, tidy [date, v]."""
    d = df.copy()
    d = d.rename(columns={d.columns[0]: "date", d.columns[1]: "v"})
    d["date"] = pd.to_datetime(d["date"])
    return (d.set_index("date")["v"].resample("QS").mean()
            .reset_index().dropna())


# ----------------------------------------------------------------------------
# A) Saving rate vs uncertainty (two panels)
# ----------------------------------------------------------------------------
def chart_A(ea, uncertainty, unc_label, rate=None, inflation=None):
    """TOP — the LEVEL story: saving rate vs its 2012-19 norm, post-2022 excess
    shaded. BOTTOM — candidate DRIVERS standardised to z-scores (uncertainty,
    ECB rate, HICP inflation). They co-move, which is why eyeballing can't isolate
    the precautionary channel — that's what 03_econometrics.py is for."""
    ea = ea.dropna(subset=["date", "value"]).sort_values("date").copy()
    ea["date"] = pd.to_datetime(ea["date"])
    unc_q = _to_quarterly(uncertainty)

    pre = ea[(ea["date"] >= "2012-01-01") & (ea["date"] <= "2019-12-31")]["value"]
    base = float(pre.mean()) if len(pre) else float(ea["value"].median())
    post = ea[ea["date"] >= "2022-07-01"]["value"]
    excess = float(post.mean() - base) if len(post) else float("nan")

    fig = plt.figure(figsize=(10, 7.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.2], hspace=0.10)
    axT = fig.add_subplot(gs[0])
    axB = fig.add_subplot(gs[1], sharex=axT)

    # ---------------- TOP: level vs norm ----------------
    axT.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31"),
                color="#5d6d7e", alpha=0.10, zorder=0)
    axT.plot(ea["date"], ea["value"], color="#1f4e79", lw=2.6, zorder=5)
    axT.axhline(base, color="#7f8c8d", ls=":", lw=1.4, zorder=3)
    mask = ea["date"] >= pd.Timestamp("2022-01-01")
    axT.fill_between(ea["date"], base, ea["value"],
                     where=mask & (ea["value"] > base),
                     color="#1f4e79", alpha=0.15, zorder=2)
    axT.axvline(pd.Timestamp("2022-02-24"), color="grey", ls="--", lw=1, zorder=3)

    # direct label at the end of the line (replaces a legend)
    axT.annotate("household\nsaving rate", xy=(ea["date"].iloc[-1], ea["value"].iloc[-1]),
                 xytext=(6, 0), textcoords="offset points",
                 color="#1f4e79", fontsize=9, va="center", ha="left")
    axT.text(ea["date"].min(), base, f" pre-pandemic norm ’12–’19: {base:.1f}%",
             va="bottom", ha="left", fontsize=8.5, color="#7f8c8d")
    axT.text(pd.Timestamp("2020-07-01"), axT.get_ylim()[1], "COVID\n(forced saving)",
             ha="center", va="top", fontsize=8, color="#5d6d7e")
    if len(post):
        axT.annotate(f"≈ {excess:.0f} pp above norm\nsince 2022",
                     xy=(pd.Timestamp("2024-01-01"), float(post.mean())),
                     xytext=(pd.Timestamp("2014-06-01"),
                             base + 0.65 * (float(post.mean()) - base)),
                     fontsize=9, color="#1f4e79", ha="left",
                     arrowprops=dict(arrowstyle="->", color="#1f4e79", lw=1))

    axT.set_ylabel("Household saving rate\n(% of disposable income)")
    axT.set_title("Euro-area households still save above their pre-pandemic norm",
                  fontweight="bold")
    plt.setp(axT.get_xticklabels(), visible=False)

    # ---------------- BOTTOM: standardised drivers ----------------
    def z(s):
        s = s.astype(float)
        sd = s.std(ddof=0)
        return (s - s.mean()) / sd if sd else s * 0.0

    drivers = [("#c0392b", unc_label, unc_q)]
    if rate is not None:
        drivers.append(("#6c3483", "ECB / short rate", _to_quarterly(rate)))
    if inflation is not None:
        drivers.append(("#e67e22", "HICP inflation", _to_quarterly(inflation)))
    for color, lab, d in drivers:
        d = d[d["date"] >= START]
        axB.plot(d["date"], z(d["v"]), color=color, lw=1.5, alpha=0.9, label=lab)
    axB.axhline(0, color="black", lw=0.6, alpha=0.5)
    axB.axvline(pd.Timestamp("2022-02-24"), color="grey", ls="--", lw=1)
    axB.set_ylabel("drivers\n(z-score)")
    axB.legend(loc="upper left", ncol=3, fontsize=8, frameon=False)
    axB.text(0.0, 1.02, "…and the candidate drivers all rose together (standardised)",
             transform=axB.transAxes, fontsize=9, color="#333")

    fig.text(0.01, 0.005,
             "Top: saving level vs its 2012–19 norm. Bottom: drivers standardised to "
             "z-scores. They co-move, so co-movement alone can’t isolate the "
             "precautionary channel — see 03_econometrics.py for the VAR / bounds test.",
             fontsize=7.5, style="italic", color="#555")

    fig.savefig(os.path.join(FIG, "A_saving_vs_uncertainty.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/A_saving_vs_uncertainty.png")


# ----------------------------------------------------------------------------
# B) Cross-country: energy shock vs rise in saving
# ----------------------------------------------------------------------------
def chart_B(scatter):
    df = scatter.dropna()
    fig, ax = plt.subplots(figsize=(9, 6))
    for geo, row in df.iterrows():
        c = "#c0392b" if geo in HIGH_EXPOSURE else "#2e86c1"
        ax.scatter(row["energy"], row["rise"], color=c, s=60, zorder=3)
        ax.annotate(geo, (row["energy"], row["rise"]),
                    xytext=(4, 4), textcoords="offset points", fontsize=9)
    # dummy points so the colour coding shows up in the legend
    ax.scatter([], [], color="#c0392b", s=60, label="High Russia/energy exposure")
    ax.scatter([], [], color="#2e86c1", s=60, label="Lower exposure")
    # OLS trend line
    if len(df) >= 3:
        b1, b0 = np.polyfit(df["energy"].astype(float), df["rise"].astype(float), 1)
        xs = [df["energy"].min(), df["energy"].max()]
        ax.plot(xs, [b0 + b1 * x for x in xs], color="grey", ls="--", lw=1.2,
                label=f"OLS fit (slope = {b1:.2f})")
    ax.set_xlabel("Peak 2022 energy price inflation (%, HICP energy, YoY)")
    ax.set_ylabel("Change in saving rate, 2019 → 2023/24 (pp)")
    ax.set_title("Did the bigger energy shock mean more saving?", fontweight="bold")
    ax.legend(loc="best", frameon=True, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "B_energy_vs_saving_scatter.png"))
    plt.close(fig)
    print("  saved figures/B_energy_vs_saving_scatter.png")


def chart_B_bar(saving_piv):
    yrs = saving_piv.columns
    latest = max([y for y in (2024.0, 2023.0) if y in yrs], default=max(yrs))
    s = saving_piv[latest].dropna().sort_values(ascending=True)
    colors = ["#c0392b" if g in HIGH_EXPOSURE else "#2e86c1" for g in s.index]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.barh(s.index, s.values, color=colors)
    ax.set_xlabel(f"Household saving rate, {int(latest)} (% of disposable income)")
    ax.set_title(f"Who saves most? Household saving rate by country ({int(latest)})",
                 fontweight="bold")
    ax.scatter([], [], color="#c0392b", label="High Russia/energy exposure")
    ax.scatter([], [], color="#2e86c1", label="Lower exposure")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "B2_saving_by_country_bar.png"))
    plt.close(fig)
    print("  saved figures/B2_saving_by_country_bar.png")


# ----------------------------------------------------------------------------
# C) Distribution: median saving rate by income quintile (latest ICW snapshot)
# ----------------------------------------------------------------------------
def chart_C_quintile(out):
    geo = out["geo"].iloc[0]
    year = int(out["year"].iloc[0])
    labels = {1: "Q1\n(lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5\n(highest)"}
    out = out.sort_values("q")
    x = [labels.get(int(q), str(q)) for q in out["q"]]
    v = out["value"].tolist()
    colors = ["#c0392b" if val < 0 else "#1f4e79" for val in v]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x, v, color=colors)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Median saving rate (% of disposable income)")
    ax.set_xlabel("Income quintile")
    ax.set_title(f"The poorest dissave, the richest save\n"
                 f"Median household saving rate by income quintile "
                 f"({geo}, ~{year})", fontweight="bold")
    for i, val in enumerate(v):
        ax.text(i, val + (0.6 if val >= 0 else -0.6), f"{val:.0f}",
                ha="center", va="bottom" if val >= 0 else "top", fontsize=9)
    ax.scatter([], [], color="#c0392b", marker="s", label="Dissaving (negative)")
    ax.scatter([], [], color="#1f4e79", marker="s", label="Saving (positive)")
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "C_saving_by_quintile.png"))
    plt.close(fig)
    print("  saved figures/C_saving_by_quintile.png")


def chart_C_expectations(ces):
    g = ces["group"].tolist()
    v = ces["expected_unemployment"].tolist()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(g, v, color="#5b2c6f", label="Expected unemployment, 12m ahead")
    ax.set_ylabel("Expected unemployment rate, 12m ahead (%)")
    ax.set_xlabel("Household income group")
    ax.set_title("Lower-income households fear job loss most\n"
                 "(yet can least afford to save) — ECB CES", fontweight="bold")
    for i, val in enumerate(v):
        ax.text(i, val + 0.1, f"{val:.1f}", ha="center", fontsize=9)
    ax.legend(loc="upper right", frameon=True, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "C2_expectations_by_income.png"))
    plt.close(fig)
    print("  saved figures/C2_expectations_by_income.png  (hardcoded ECB CES figures — verify)")


# ----------------------------------------------------------------------------
# D) Distribution over time — Eurostat ICW snapshots
# ----------------------------------------------------------------------------
def chart_D_icw_slope(panel):
    geo = panel["geo"].iloc[0]
    years = sorted(panel["year"].unique())
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for q in sorted(panel["q"].unique()):
        d = panel[panel["q"] == q].sort_values("year")
        ax.plot(d["year"], d["value"], marker="o", lw=2,
                color=QCOLORS.get(int(q), "grey"), label=QLABEL.get(int(q), str(q)))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(years)
    ax.set_ylabel("Median saving rate (% of disposable income)")
    ax.set_xlabel("ICW reference year (compiled ~every 5 yrs)")
    ax.set_title(f"How the saving distribution shifted across snapshots\n"
                 f"Eurostat ICW ({geo})", fontweight="bold")
    ax.legend(title="Income quintile", fontsize=9)
    fig.text(0.01, -0.01, "Only a few reference years exist (~2010/2015/2020) — "
             "structural shift, not an annual path.", fontsize=7.5,
             style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "D_icw_slope.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/D_icw_slope.png")


# ----------------------------------------------------------------------------
# E) OECD annual saving rate by quintile (per country)
# ----------------------------------------------------------------------------
def chart_E_oecd(panel, country):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for q in sorted(panel["q"].unique()):
        d = panel[panel["q"] == q].sort_values("year")
        ax.plot(d["year"], d["value"], marker="o", ms=3, lw=1.8,
                color=QCOLORS.get(int(q), "grey"), label=QLABEL.get(int(q), str(q)))
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(2022, color="grey", ls="--", lw=1, label="2022 (war/energy shock)")
    ax.set_ylabel("Saving rate (% of disposable income)")
    ax.set_xlabel("Year")
    ax.set_title(f"Saving rate by income quintile, year by year\n"
                 f"OECD distributional accounts ({country})", fontweight="bold")
    ax.legend(title="Income quintile", fontsize=8.5, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, f"E_oecd_quintile_{country}.png"))
    plt.close(fig)
    print(f"  saved figures/E_oecd_quintile_{country}.png")


# ----------------------------------------------------------------------------
# F) ECB CES: saving by income group since 2020
# ----------------------------------------------------------------------------
def chart_F_ces(out):
    out = out.copy()
    out["date"] = pd.to_datetime(out["date"])
    fig, ax = plt.subplots(figsize=(9, 5))
    for g, d in out.groupby("group"):
        d = d.sort_values("date")
        ax.plot(d["date"], d["value"], marker=".", lw=1.6, label=g)
    ax.axvline(pd.Timestamp("2022-02-24"), color="grey", ls="--", lw=1)
    ax.set_ylabel("CES saving indicator")
    ax.set_title("Saving by income group since 2020 — ECB CES", fontweight="bold")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "F_ces_saving_by_income.png"))
    plt.close(fig)
    print("  saved figures/F_ces_saving_by_income.png")


# ----------------------------------------------------------------------------
# Loaders + main
# ----------------------------------------------------------------------------
def _load_pivot(name):
    """Read a country x year saving pivot back with float year columns."""
    df = _read(name)
    if df is None:
        return None
    df = df.set_index(df.columns[0])
    df.columns = [float(c) for c in df.columns]
    return df


def main():
    print("=" * 64)
    print("STEP 2 — drawing figures into ./figures (reads ./data)")
    print("=" * 64)

    print("\n[A] Saving rate vs uncertainty ...")
    try:
        ea = _read("ea_saving_rate_quarterly.csv")
        # prefer GPR for the geopolitics framing; fall back to EU EPU
        if os.path.exists(_path("gpr.csv")):
            unc, unc_label = _read("gpr.csv"), "Geopolitical Risk index"
        elif os.path.exists(_path("fred_eu_epu.csv")):
            unc, unc_label = _read("fred_eu_epu.csv"), "EU Economic Policy Uncertainty"
        else:
            unc = None
        if ea is None or unc is None:
            print("  SKIPPED: need ea_saving_rate_quarterly.csv and a proxy CSV.")
        else:
            chart_A(ea, unc, unc_label,
                    rate=_read("ecb_rate.csv"), inflation=_read("ea_inflation.csv"))
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[B] Energy shock vs rise in saving (scatter) ...")
    try:
        scatter = _read("scatter_energy_vs_saving.csv")
        if scatter is None:
            print("  SKIPPED: scatter_energy_vs_saving.csv missing.")
        else:
            chart_B(scatter.set_index(scatter.columns[0]))
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[B2] Saving rate by country (bar) ...")
    try:
        piv = _load_pivot("country_saving_annual.csv")
        if piv is None:
            print("  SKIPPED: country_saving_annual.csv missing.")
        else:
            chart_B_bar(piv)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[C] Saving rate by income quintile (latest snapshot) ...")
    try:
        out = _read("saving_rate_by_quintile.csv")
        if out is None:
            print("  SKIPPED: saving_rate_by_quintile.csv missing.")
        else:
            chart_C_quintile(out)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[C2] Unemployment expectations by income group ...")
    try:
        ces = _read("ces_unemp_expectations.csv")
        if ces is None:
            print("  SKIPPED: ces_unemp_expectations.csv missing.")
        else:
            chart_C_expectations(ces)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[D] Saving distribution across ICW snapshots ...")
    try:
        panel = _read("icw_quintile_panel.csv")
        if panel is None:
            print("  SKIPPED: icw_quintile_panel.csv missing.")
        else:
            chart_D_icw_slope(panel)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[E] OECD annual saving by quintile (per country) ...")
    oecd_files = sorted(glob.glob(_path("oecd_quintile_panel_*.csv")))
    if not oecd_files:
        print("  SKIPPED: no oecd_quintile_panel_*.csv (OECD pull returned nothing).")
    for f in oecd_files:
        country = os.path.basename(f).replace("oecd_quintile_panel_", "").replace(".csv", "")
        try:
            chart_E_oecd(pd.read_csv(f), country)
        except Exception as e:
            print(f"  {country} FAILED: {e}")

    print("\n[F] ECB CES saving by income group since 2020 ...")
    try:
        out = _read("ces_saving_by_income.csv")
        if out is None:
            print("  SKIPPED: ces_saving_by_income.csv missing (needs CES keys in step 1).")
        else:
            chart_F_ces(out)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\nDone. See ./figures — now run 03_econometrics.py")


if __name__ == "__main__":
    main()
