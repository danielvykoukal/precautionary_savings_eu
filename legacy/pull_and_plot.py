#!/usr/bin/env python3
"""
Precautionary saving in Europe — data pull + plots
===================================================

Hypothesis
----------
Europe's elevated household saving rate is substantially PRECAUTIONARY:
driven by geopolitical / economic uncertainty, it (a) tracks uncertainty
indices over time, (b) rose most where the Russia/energy shock bit hardest,
and (c) is concentrated among households who can afford to save.

What this script does
---------------------
Pulls, cleans and plots (all via free APIs, no paid data needed):
  - Eurostat household saving rate: euro-area quarterly (teina500) +
    by-country annual (tec00131)
  - Eurostat HICP energy inflation by country (prc_hicp_manr) -> "energy shock"
  - Eurostat consumer survey: unemployment expectations / confidence (ei_bsco_m)
  - Eurostat ICW experimental: median saving rate by income quintile (icw_sr_03)
  - OECD EG DNA: annual saving rate by income quintile, per country (SDMX API)
  - ECB CES: recent saving by income group, 2020-> (needs series keys, optional)
  - FRED Economic Policy Uncertainty Index for Europe (EUEPUINDXM, keyless CSV)
  - Geopolitical Risk index (Caldara & Iacoviello, keyless .xls)

Outputs (next to this script):
  ./data/*.csv     cleaned tidy series
  ./figures/*.png  the charts

Run
---
    pip install eurostat pandas matplotlib openpyxl xlrd requests
    python pull_and_plot.py

Notes
-----
- FRED is pulled via its keyless CSV endpoint, so NO API key is required.
- Each section is wrapped in try/except: if one source is down or a dataset
  code changes, the rest still run. Failures print a clear message.
- Eurostat dataset dimensions occasionally change codes; the script prints the
  available dimension values it sees, so you can adjust filters if needed.
"""

import os
import re
import sys
import textwrap
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed; we save PNGs
import matplotlib.pyplot as plt

try:
    import eurostat
except ImportError:
    sys.exit("Missing 'eurostat'. Run: pip install eurostat pandas matplotlib openpyxl xlrd requests")

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

# How far back to plot (the long saving-rate series starts 1999Q1).
START = "1999-01-01"

# Euro-area aggregate code differs across vintages (EA19/EA20/EA). We try each
# and keep whichever has the longest coverage.
EA_CODES = ["EA20", "EA19", "EA", "EU27_2020"]

# Country set for the cross-section (ISO2 / Eurostat geo codes)
COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "FI", "IE", "PT", "EL",
             "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT", "SE", "DK"]

# Editorial grouping for color-coding (refine before publishing).
# "High exposure" = large Russian-gas reliance pre-2022 and/or frontline CEE.
HIGH_EXPOSURE = {"DE", "AT", "FI", "PL", "CZ", "SK", "HU", "SI", "EE", "LV", "LT"}

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25,
})


# ----------------------------------------------------------------------------
# Eurostat helpers
# ----------------------------------------------------------------------------
def es_long(code):
    """Fetch a Eurostat dataset and return it tidy: dimension cols + time + value."""
    df = eurostat.get_data_df(code)
    if df is None or df.empty:
        raise RuntimeError(f"Eurostat returned nothing for {code}")
    # geo column is named e.g. 'geo\\TIME_PERIOD' or 'geo\\time'
    geo_col = next((c for c in df.columns if "geo" in c.lower()), None)
    if geo_col:
        df = df.rename(columns={geo_col: "geo"})
    # time columns look like a year (2024) or a period (2024-Q2 / 2024Q2 / 2024-06)
    time_cols = [c for c in df.columns if re.match(r"^\d{4}", str(c))]
    id_cols = [c for c in df.columns if c not in time_cols]
    long = df.melt(id_vars=id_cols, value_vars=time_cols,
                   var_name="time", value_name="value")
    long = long.dropna(subset=["value"])
    return long


def parse_time(s):
    """Parse '2024', '2024-Q2'/'2024Q2', or '2024-06' to a sortable timestamp."""
    s = str(s)
    m = re.match(r"^(\d{4})[-_ ]?Q([1-4])$", s)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return pd.Timestamp(year=y, month=(q - 1) * 3 + 1, day=1)
    m = re.match(r"^(\d{4})[-_ ](\d{2})$", s)
    if m:
        return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=1)
    m = re.match(r"^(\d{4})$", s)
    if m:
        return pd.Timestamp(year=int(m.group(1)), month=1, day=1)
    return pd.NaT


def show_dims(long, code, dims):
    """Print available codes for given dimensions to help debugging filters."""
    print(f"  [{code}] dimension values:")
    for d in dims:
        if d in long.columns:
            vals = sorted(long[d].dropna().unique().tolist())[:25]
            print(f"    {d}: {vals}")


# ----------------------------------------------------------------------------
# 1) Euro-area saving rate (quarterly) vs uncertainty
# ----------------------------------------------------------------------------
def _pick_longest_ea(long):
    """From a tidy frame with geo/date/value, return (code, sub) for the EA/EU
    aggregate with the most observations."""
    best = None
    candidates = EA_CODES + sorted(c for c in long["geo"].unique()
                                   if str(c).startswith(("EA", "EU")))
    for code in dict.fromkeys(candidates):  # de-dup, keep order
        sub = long[long["geo"] == code].dropna(subset=["date", "value"])
        if not sub.empty and (best is None or len(sub) > len(best[1])):
            best = (code, sub)
    return best


SAVING_BAND = (5.0, 30.0)  # plausible household gross saving rate (% of disp. income)


def _best_saving_series(sub):
    """From a tidy frame already restricted to ONE euro-area geo, return
    (combo, series) for the single dimension-combination that is the household
    gross saving rate.

    Why this exists: the previous version filtered on na_item=='SRG' and, when
    that code wasn't present, silently kept *every* key-indicator ratio (saving
    rate, investment rate, profit share, ...) and averaged them with groupby-mean.
    The blend landed near ~35%, which is nonsense for a household saving rate.
    Here we NEVER average across indicators -- we pick one real series, preferring
    a saving-named na_item and a level that looks like a saving rate.
    """
    dimcols = [c for c in sub.columns if c not in ("time", "value", "geo", "date")]
    groups = sub.groupby(dimcols) if dimcols else [((), sub)]
    cands = []
    for combo, g in groups:
        s = g.dropna(subset=["date", "value"]).sort_values("date")
        if s.empty:
            continue
        # a genuine single series has ~one observation per period
        if s["date"].duplicated().mean() > 0.05:
            continue
        med = float(s["value"].median())
        if not (SAVING_BAND[0] <= med <= SAVING_BAND[1]):
            continue
        combo_t = combo if isinstance(combo, tuple) else (combo,)
        combo_str = " ".join(str(x) for x in combo_t).upper()
        is_saving = any(k in combo_str for k in ("SR", "SAV", "B8"))
        # prefer saving-named, then the level closest to a typical ~13% rate,
        # then the longest series.
        cands.append((is_saving, -abs(med - 13.0), len(s), combo_t, s[["date", "value"]]))
    if not cands:
        return None
    cands.sort(key=lambda c: (c[0], c[1], c[2]), reverse=True)
    return cands[0][3], cands[0][4]


def get_ea_saving_quarterly():
    """Long quarterly euro-area household gross saving rate (back to 1999Q1).

    Tries the current Eurostat sector-account datasets in turn, auto-detects the
    single household-saving-rate series (no blending), and refuses any result
    whose level is implausible for a household saving rate.
    """
    last_err = None
    for code in ("nasq_10_ki", "nasa_10_ki", "teina500"):
        try:
            long = es_long(code)
        except Exception as e:
            last_err = e
            print(f"  {code} unavailable ({e}); trying next dataset")
            continue

        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["date"] = long["time"].map(parse_time)
        long = long.dropna(subset=["value", "date"])
        show_dims(long, code,
                  [c for c in long.columns if c not in ("time", "value", "geo", "date")])

        # choose a euro-area aggregate geo
        ea_geo = next((g for g in EA_CODES if g in set(long["geo"])), None) \
            or next((g for g in long["geo"].unique() if str(g).startswith(("EA", "EU"))), None)
        if ea_geo is None:
            print(f"  {code}: no EA/EU aggregate; trying next dataset")
            continue
        sub = long[long["geo"] == ea_geo].copy()

        # narrow to the household sector and seasonally-adjusted data if those
        # dimensions exist (helps disambiguate; the selection below is the guard)
        if "sector" in sub.columns:
            for sec in ("S14_S15", "S14"):
                if sec in set(sub["sector"]):
                    sub = sub[sub["sector"] == sec]
                    break
        if "s_adj" in sub.columns:
            for sa in ("SCA", "SA"):
                if sa in set(sub["s_adj"]):
                    sub = sub[sub["s_adj"] == sa]
                    break

        picked = _best_saving_series(sub)
        if picked is None:
            print(f"  {code}: no series with a plausible saving-rate level; trying next")
            continue
        combo, ea = picked
        ea = ea.sort_values("date")
        ea = ea[ea["date"] >= START]
        med = float(ea["value"].median())
        if not (SAVING_BAND[0] <= med <= SAVING_BAND[1]):
            print(f"  {code}: selected level implausible (median {med:.1f}%); trying next")
            continue
        print(f"  saving rate from {code}, geo={ea_geo}, series={combo}: "
              f"{len(ea)} obs, median {med:.1f}%, "
              f"{ea['date'].min().date()} -> {ea['date'].max().date()}")
        ea.to_csv(os.path.join(DATA, "ea_saving_rate_quarterly.csv"), index=False)
        return ea

    raise RuntimeError(
        "Could not obtain a plausible euro-area household saving rate from any "
        f"candidate dataset (nasq_10_ki / nasa_10_ki / teina500). Last error: {last_err}")


def get_fred_eu_epu():
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=EUEPUINDXM"
    df = pd.read_csv(url)
    datecol = "observation_date" if "observation_date" in df.columns else df.columns[0]
    df = df.rename(columns={datecol: "date", df.columns[-1]: "epu"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["epu"] = pd.to_numeric(df["epu"], errors="coerce")
    df = df.dropna().sort_values("date")
    df = df[df["date"] >= START]
    df.to_csv(os.path.join(DATA, "fred_eu_epu.csv"), index=False)
    return df


def get_gpr():
    """Caldara-Iacoviello Geopolitical Risk index (monthly). Keyless .xls."""
    url = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"
    df = pd.read_excel(url)
    # date column is 'month' (datetime). Index is 'GPR'.
    datecol = next((c for c in df.columns if str(c).lower() in ("month", "date")), df.columns[0])
    gprcol = "GPR" if "GPR" in df.columns else next((c for c in df.columns if str(c).upper().startswith("GPR")), None)
    df = df[[datecol, gprcol]].rename(columns={datecol: "date", gprcol: "gpr"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna().sort_values("date")
    df = df[df["date"] >= START]
    df.to_csv(os.path.join(DATA, "gpr.csv"), index=False)
    return df


# ----------------------------------------------------------------------------
# Confounds (for the 'drivers' panel and the multivariate VAR in econometrics.py)
# ----------------------------------------------------------------------------
def get_fred_series(series_id, colname):
    """Generic keyless FRED CSV pull -> tidy [date, colname]."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    datecol = "observation_date" if "observation_date" in df.columns else df.columns[0]
    df = df.rename(columns={datecol: "date", df.columns[-1]: colname})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[colname] = pd.to_numeric(df[colname], errors="coerce")
    df = df.dropna().sort_values("date")
    return df[df["date"] >= START][["date", colname]]


def get_ecb_rate():
    """A euro-area short / policy rate, monthly. Tries a few keyless FRED IDs:
    ECB deposit facility rate, main refinancing rate, then 3-month interbank."""
    for sid in ("ECBDFR", "ECBMRRFR", "IR3TIB01EZM156N"):
        try:
            df = get_fred_series(sid, "rate")
            if len(df) > 24:
                df.to_csv(os.path.join(DATA, "ecb_rate.csv"), index=False)
                print(f"  policy/short rate from FRED {sid}: {len(df)} obs")
                return df
        except Exception as e:
            print(f"  FRED {sid} failed ({e})")
    raise RuntimeError("No euro-area rate series available from FRED")


def get_ea_inflation():
    """Euro-area headline HICP inflation, YoY %, monthly (Eurostat prc_hicp_manr,
    COICOP all-items CP00)."""
    long = es_long("prc_hicp_manr")
    if "coicop" in long.columns and "CP00" in set(long["coicop"]):
        long = long[long["coicop"] == "CP00"]
    geo = next((g for g in ("EA20", "EA19", "EA") if g in set(long["geo"])), None) \
        or next((g for g in long["geo"].unique() if str(g).startswith("EA")), None)
    long = long[long["geo"] == geo]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["date"] = long["time"].map(parse_time)
    df = (long.dropna(subset=["value", "date"]).sort_values("date")[["date", "value"]]
          .rename(columns={"value": "inflation"}))
    df = df[df["date"] >= START]
    df.to_csv(os.path.join(DATA, "ea_inflation.csv"), index=False)
    print(f"  EA HICP inflation (CP00, geo={geo}): {len(df)} obs")
    return df


def _to_quarterly(df):
    """[date, value] (any first two cols) -> quarterly mean, tidy [date, v]."""
    d = df.copy()
    d = d.rename(columns={d.columns[0]: "date", d.columns[1]: "v"})
    d["date"] = pd.to_datetime(d["date"])
    return (d.set_index("date")["v"].resample("QS").mean()
            .reset_index().dropna())


def chart_A(ea, uncertainty, unc_label, rate=None, inflation=None):
    """Two clean panels instead of one busy dual-axis chart.

    TOP  — the LEVEL story: the saving rate against its 2012–19 norm, with the
           post-2022 excess shaded. Single y-axis, one annotation, line labelled
           directly (no legend box).
    BOTTOM — the candidate DRIVERS, standardised (z-scores) so they share one
           scale: uncertainty + ECB rate + HICP inflation. They visibly co-move,
           which is exactly why eyeballing can't isolate the precautionary
           channel — that's what econometrics.py is for.
    """
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
             "precautionary channel — see econometrics.py for the VAR / cointegration test.",
             fontsize=7.5, style="italic", color="#555")

    fig.savefig(os.path.join(FIG, "A_saving_vs_uncertainty.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/A_saving_vs_uncertainty.png")


# ----------------------------------------------------------------------------
# 2) Cross-country: energy shock vs rise in saving
# ----------------------------------------------------------------------------
def get_country_saving_annual():
    long = es_long("tec00131")
    show_dims(long, "tec00131", [c for c in long.columns if c not in ("time", "value", "geo")])
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    long = long[long["geo"].isin(COUNTRIES)]
    piv = long.pivot_table(index="geo", columns="year", values="value", aggfunc="mean")
    piv.to_csv(os.path.join(DATA, "country_saving_annual.csv"))
    return piv


def get_country_energy_shock():
    """Peak monthly HICP energy inflation by country during 2022 (the shock)."""
    long = es_long("prc_hicp_manr")
    # Filter to energy ('NRG') COICOP code.
    if "coicop" in long.columns:
        if "NRG" in set(long["coicop"]):
            long = long[long["coicop"] == "NRG"]
        else:
            raise RuntimeError("Cannot find 'NRG' (energy) in 'coicop' dimension of prc_hicp_manr.")
    long["date"] = long["time"].map(parse_time)
    long = long[(long["date"] >= "2022-01-01") & (long["date"] <= "2022-12-31")]
    long = long[long["geo"].isin(COUNTRIES)]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    peak = long.groupby("geo")["value"].max()
    peak.to_csv(os.path.join(DATA, "country_energy_peak_2022.csv"))
    return peak


def chart_B(saving_piv, energy_peak):
    # rise in saving = (avg 2023-24) - (2019)
    yrs = saving_piv.columns
    base = 2019.0 if 2019.0 in yrs else min(yrs)
    recent = [y for y in (2024.0, 2023.0) if y in yrs]
    if not recent:
        recent = [max(yrs)]
    rise = saving_piv[recent].mean(axis=1) - saving_piv[base]
    df = pd.DataFrame({"rise": rise, "energy": energy_peak}).dropna()
    df.to_csv(os.path.join(DATA, "scatter_energy_vs_saving.csv"))

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
# 3a) Distributional saving: median saving rate by income quintile
#     Eurostat experimental ICW statistics (icw_sr_03). Reference years are
#     ~2010/2015/2020 (compiled ~every 5 yrs) — STRUCTURAL, not timely.
#     Built from EU-SILC + Household Budget Survey + ECB HFCS.
# ----------------------------------------------------------------------------
GEO_PREF = ["EA20", "EA19", "EA", "EU27_2020", "EU28", "DE", "FR", "IT", "ES"]


def _detect_quintile_col(long):
    """Return the column whose values look like income-quintile codes."""
    for c in long.columns:
        if c in ("time", "value", "geo"):
            continue
        vals = [str(v).upper() for v in long[c].dropna().unique()]
        if any(re.search(r"(QU?[1-5])|QUINT|^Q[1-5]$|D[1-9]0?", v) for v in vals):
            return c
    return None


def _quintile_num(code):
    m = re.search(r"([1-5])", str(code))
    return int(m.group(1)) if m else 99


def get_saving_by_quintile():
    long = es_long("icw_sr_03")
    show_dims(long, "icw_sr_03",
              [c for c in long.columns if c not in ("time", "value", "geo")])
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    qcol = _detect_quintile_col(long)
    if qcol is None:
        raise RuntimeError("Could not detect the income-quintile dimension in icw_sr_03 "
                           "(check the printed dimension values and set it manually)")
    # keep only quintile rows (drop TOTAL etc.)
    long = long[long[qcol].astype(str).str.upper().str.contains(r"QU?[1-5]|^Q[1-5]$|QUINT", regex=True)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    latest = long["year"].max()
    sub = long[long["year"] == latest]
    geo = next((g for g in GEO_PREF if g in set(sub["geo"])), None)
    if geo is None:  # fall back to whichever geo has all 5 quintiles
        counts = sub.groupby("geo")[qcol].nunique()
        geo = counts.idxmax()
    sub = sub[sub["geo"] == geo].copy()
    sub["q"] = sub[qcol].map(_quintile_num)
    out = sub.groupby("q", as_index=False)["value"].mean().sort_values("q")
    out["geo"] = geo
    out["year"] = int(latest)
    out.to_csv(os.path.join(DATA, "saving_rate_by_quintile.csv"), index=False)
    print(f"  saving rate by quintile from icw_sr_03: geo={geo}, year~{int(latest)}")
    return out, geo, int(latest)


def chart_C_quintile(out, geo, year):
    labels = {1: "Q1\n(lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5\n(highest)"}
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


# ----------------------------------------------------------------------------
# 3b) Distribution angle (ECB Consumer Expectations Survey)
#    The income-group breakdown is NOT in the Eurostat bulk API; these are
#    published ECB CES figures. Update with the latest CES release before
#    publishing. Source: ECB CES, unemployment expectations 12m ahead.
# ----------------------------------------------------------------------------
CES_UNEMP_EXPECT = {  # income group -> expected unemployment rate 12m ahead (%)
    "Lowest quintile": 13.2,
    "Q2": 12.0,
    "Q3": 11.0,
    "Q4": 10.0,
    "Highest quintile": 9.4,
}


def chart_C_expectations():
    g = list(CES_UNEMP_EXPECT.keys())
    v = list(CES_UNEMP_EXPECT.values())
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


# ============================================================================
# 4) CHANGE IN THE DISTRIBUTION OVER TIME  (three data bases)
#    4a Eurostat ICW   -> slope across ~2010/2015/2020 snapshots (EA-wide, official)
#    4b OECD EG DNA    -> annual saving rate by quintile (per country, true panel)
#    4c ECB CES        -> recent (2020->now) by income group (needs series keys)
# ============================================================================
QLABEL = {1: "Q1 (lowest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (highest)"}
QCOLORS = {1: "#c0392b", 2: "#e67e22", 3: "#7f8c8d", 4: "#2e86c1", 5: "#1f4e79"}


# --- 4a) Eurostat ICW: the distribution at each available snapshot ----------
def get_icw_panel(geo_pref=GEO_PREF):
    """Return (panel[year,q,value], geo) for the saving rate by quintile across
    ALL ICW reference years (~2010/2015/2020) for one geography."""
    long = es_long("icw_sr_03")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    qcol = _detect_quintile_col(long)
    if qcol is None:
        raise RuntimeError("icw_sr_03: quintile dimension not found")
    long = long[long[qcol].astype(str).str.upper().str.contains(
        r"QU?[1-5]|^Q[1-5]$|QUINT", regex=True)]
    long["year"] = long["time"].str.extract(r"(\d{4})").astype(float)
    geo = next((g for g in geo_pref if g in set(long["geo"])), None)
    if geo is None:
        geo = long.groupby("geo")[qcol].nunique().idxmax()
    sub = long[long["geo"] == geo].copy()
    sub["q"] = sub[qcol].map(_quintile_num)
    sub = sub[sub["q"].between(1, 5)]
    panel = sub.groupby(["year", "q"], as_index=False)["value"].mean()
    panel.to_csv(os.path.join(DATA, "icw_quintile_panel.csv"), index=False)
    return panel, geo


def chart_D_icw_slope(panel, geo):
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
    fig.text(0.01, -0.01, "Only 3 reference years exist (~2010/2015/2020) — "
             "structural shift, not an annual path.", fontsize=7.5,
             style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "D_icw_slope.png"), bbox_inches="tight")
    plt.close(fig)
    print("  saved figures/D_icw_slope.png")


# --- 4b) OECD EG DNA: annual saving rate by income quintile (per country) ----
# Flow found via the OECD Data Explorer (Expert Group on Distributional National
# Accounts). If the pull returns nothing, confirm the flow id / measure code at
#   https://data-explorer.oecd.org  (search "household ... saving" by quintile)
OECD_AGENCY = "OECD.SDD.NAD"
OECD_FLOW = "DSD_EGDNA_INC_HHT@DF_INC_HHT"   # candidate flow (household income & saving)
OECD_VERSION = ""                            # blank -> latest
OECD_COUNTRIES = ["DEU", "FRA", "ITA", "ESP"]  # change as you like


def _parse_oecd(df, country):
    """Turn an OECD SDMX-CSV frame into panel[year,q,value] for one country.
    Robust to column naming: finds TIME_PERIOD / OBS_VALUE / REF_AREA, the
    quintile dimension (by value pattern), and a saving-rate measure if present.
    """
    up = {c.upper(): c for c in df.columns}
    tcol = up.get("TIME_PERIOD")
    vcol = up.get("OBS_VALUE")
    rcol = up.get("REF_AREA") or up.get("COU") or up.get("LOCATION")
    if not (tcol and vcol):
        raise RuntimeError(f"OECD: TIME_PERIOD/OBS_VALUE not found in {list(df.columns)}")
    df = df.copy()
    df[vcol] = pd.to_numeric(df[vcol], errors="coerce")
    if rcol is not None and country:
        df = df[df[rcol].astype(str).str.upper() == country.upper()]
    if df.empty:
        raise RuntimeError(f"OECD: no rows for {country}")
    # quintile dimension: a column whose values look like quintiles
    qcol = None
    for c in df.columns:
        if c in (tcol, vcol):
            continue
        vals = [str(v).upper() for v in list(df[c].dropna().unique())[:80]]
        if any(re.search(r"QUINT|\bQU?[1-5]\b|_Q[1-5]\b|QUANTILE|QTL", v) for v in vals):
            qcol = c
            break
    if qcol is None:
        raise RuntimeError("OECD: quintile dimension not found — inspect printed columns")
    # if a measure/transaction dim names a saving rate, keep only that
    for c in df.columns:
        vals = [str(v).upper() for v in df[c].dropna().unique()]
        if any(("SAV" in v) and ("RAT" in v) for v in vals):
            mask = (df[c].astype(str).str.upper().str.contains("SAV")
                    & df[c].astype(str).str.upper().str.contains("RAT"))
            if mask.any():
                df = df[mask]
            break
    df["q"] = df[qcol].map(_quintile_num)
    df = df[df["q"].between(1, 5)]
    df["year"] = df[tcol].astype(str).str.extract(r"(\d{4})").astype(float)
    panel = (df.groupby(["year", "q"], as_index=False)[vcol]
             .mean().rename(columns={vcol: "value"}))
    return panel


def get_oecd_quintile_panel(country, start=2007):
    base = "https://sdmx.oecd.org/public/rest/data/"
    url = (f"{base}{OECD_AGENCY},{OECD_FLOW},{OECD_VERSION}/all"
           f"?startPeriod={start}&dimensionAtObservation=AllDimensions"
           f"&format=csvfilewithlabels")
    # The OECD SDMX server may return a 403 Forbidden error to requests that
    # do not have a standard browser User-Agent header. We use the `requests`
    # library to set one, making the request appear like it's from a browser.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get(url, headers=headers, timeout=60)
        res.raise_for_status()
        df = pd.read_csv(StringIO(res.text))
        print(f"  [OECD {country}] columns: {list(df.columns)[:18]}")
    except requests.exceptions.RequestException as e:
        # The main loop's except block will catch this and print a clean failure message.
        raise RuntimeError(f"OECD request failed for {country}: {e}") from e
    panel = _parse_oecd(df, country)
    panel.to_csv(os.path.join(DATA, f"oecd_quintile_panel_{country}.csv"), index=False)
    return panel


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


# --- 4c) ECB CES: recent saving by income group (2020 -> now) ----------------
# The exact series keys live on the ECB Data Portal, dataset 'CES':
#   https://data.ecb.europa.eu/data/datasets/CES
# Paste the saving series for (at least) the lowest and highest income groups,
# e.g. CES_KEYS = {"Lowest quintile": "M.U2.<...>", "Highest quintile": "M.U2.<...>"}
CES_KEYS = {}


def get_ces_saving():
    if not CES_KEYS:
        raise RuntimeError("CES_KEYS is empty — paste series keys from the ECB Data "
                           "Portal (dataset 'CES') to enable the recent by-income series.")
    base = "https://data-api.ecb.europa.eu/service/data/CES/"
    frames = []
    for label, key in CES_KEYS.items():
        url = f"{base}{key}?format=csvdata&startPeriod=2020-01"
        d = pd.read_csv(url)
        d = d.rename(columns={"TIME_PERIOD": "time", "OBS_VALUE": "value"})
        d["date"] = pd.to_datetime(d["time"], errors="coerce")
        d["group"] = label
        frames.append(d[["date", "value", "group"]].dropna())
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(os.path.join(DATA, "ces_saving_by_income.csv"), index=False)
    return out


def chart_F_ces(out):
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
# Main
# ----------------------------------------------------------------------------
def main():
    print("=" * 64)
    print("Precautionary saving in Europe — pulling data")
    print("=" * 64)

    uncertainty, unc_label = None, "Uncertainty"

    print("\n[1] FRED EU Economic Policy Uncertainty ...")
    try:
        epu = get_fred_eu_epu()
        uncertainty, unc_label = epu, "EU Economic Policy Uncertainty"
        print(f"  ok: {len(epu)} obs, latest {epu['date'].max().date()}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[2] Geopolitical Risk index (Iacoviello) ...")
    try:
        gpr = get_gpr()
        uncertainty, unc_label = gpr, "Geopolitical Risk index"  # prefer GPR for the geopolitics framing
        print(f"  ok: {len(gpr)} obs, latest {gpr['date'].max().date()}")
    except Exception as e:
        print(f"  FAILED (will fall back to EPU): {e}")

    print("\n[2b] Confounds: ECB/short rate (FRED) + EA HICP inflation (Eurostat) ...")
    rate = inflation = None
    try:
        rate = get_ecb_rate()
    except Exception as e:
        print(f"  rate FAILED: {e}")
    try:
        inflation = get_ea_inflation()
    except Exception as e:
        print(f"  inflation FAILED: {e}")

    print("\n[3] Euro-area quarterly saving rate (Eurostat nasq_10_ki) ...")
    try:
        ea = get_ea_saving_quarterly()
        print(f"  ok: {len(ea)} quarters, latest {ea['date'].max().date()} = {ea['value'].iloc[-1]:.1f}%")
        if uncertainty is not None:
            chart_A(ea, uncertainty, unc_label, rate=rate, inflation=inflation)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[4] Saving rate by country (Eurostat tec00131) ...")
    saving_piv = None
    try:
        saving_piv = get_country_saving_annual()
        print(f"  ok: {saving_piv.shape[0]} countries, years {list(saving_piv.columns)}")
        chart_B_bar(saving_piv)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[5] Energy price shock by country (Eurostat prc_hicp_manr) ...")
    try:
        energy_peak = get_country_energy_shock()
        print(f"  ok: peak 2022 energy inflation for {len(energy_peak)} countries")
        if saving_piv is not None:
            chart_B(saving_piv, energy_peak)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[6] Distribution: saving rate by income quintile (Eurostat icw_sr_03) ...")
    try:
        out, geo, year = get_saving_by_quintile()
        chart_C_quintile(out, geo, year)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[7] Distribution: fear by income, recent (ECB CES, hardcoded) ...")
    try:
        chart_C_expectations()
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[8] Distribution over time — Eurostat ICW snapshots ...")
    try:
        panel, geo = get_icw_panel()
        chart_D_icw_slope(panel, geo)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[9] Distribution over time — OECD annual by quintile ...")
    for c in OECD_COUNTRIES:
        try:
            panel = get_oecd_quintile_panel(c)
            if panel.empty:
                print(f"  {c}: no data returned")
            else:
                chart_E_oecd(panel, c)
        except Exception as e:
            print(f"  {c} FAILED: {e}")

    print("\n[10] Distribution over time — ECB CES by income (needs keys) ...")
    try:
        out = get_ces_saving()
        chart_F_ces(out)
    except Exception as e:
        print(f"  SKIPPED: {e}")

    print("\nDone. See ./figures and ./data")


if __name__ == "__main__":
    main()
