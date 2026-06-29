#!/usr/bin/env python3
"""
Descriptive #4 --- Household saving rates across Europe (a map)
==============================================================

Supervisor idea: a zoomed-in map of Europe with the saving-rate numbers ---
Germany vs Southern Europe.

A choropleth of the gross household saving rate by country (latest year),
shaded high (dark) to low (light), with each country's number annotated. It
uses geopandas when available (the clean path) and otherwise renders the same
choropleth directly from the GISCO GeoJSON with matplotlib, so the figure always
generates.

Data: ../data/country_saving_annual.csv (Eurostat tec00131); country boundaries
from Eurostat GISCO. Greece is 'EL' in Eurostat but 'GR' in GISCO (mapped).
    python europe_map.py
"""

import os
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C

REPORT = []
GISCO_URL = ("https://gisco-services.ec.europa.eu/distribution/v2/countries/"
             "geojson/CNTR_RG_20M_2020_4326.geojson")
EXTENT = (-25, 45, 34, 72)   # Europe bbox (lon_min, lon_max, lat_min, lat_max)
GISCO_TO_ESTAT = {"GR": "EL", "GB": "UK"}


def say(line=""):
    print(line)
    REPORT.append(str(line))


def load_saving():
    """Latest-year gross household saving rate per Eurostat geo -> ({geo: rate}, year)."""
    df = C.root_csv("country_saving_annual.csv")
    df = df.rename(columns={df.columns[0]: "geo"}).set_index("geo")
    df.columns = [int(float(c)) for c in df.columns]
    for y in sorted(df.columns, reverse=True):
        s = df[y].dropna()
        if len(s) >= 10:
            return s.to_dict(), y
    y = max(df.columns)
    return df[y].dropna().to_dict(), y


# ---- geometry helpers (matplotlib fallback path) ---------------------------
def _rings(geom):
    t = geom.get("type")
    if t == "Polygon":
        return [geom["coordinates"][0]]
    if t == "MultiPolygon":
        return [poly[0] for poly in geom["coordinates"]]
    return []


def _bbox_area(ring):
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def draw_matplotlib(features, saving, year):
    import matplotlib.colors as mcolors
    from matplotlib.cm import ScalarMappable
    vals = list(saving.values())
    norm = mcolors.Normalize(vmin=min(vals), vmax=max(vals))
    cmap = plt.cm.YlGnBu
    fig, ax = plt.subplots(figsize=(9.2, 9))
    for feat in features:
        cid = str(feat["properties"].get("CNTR_ID"))
        geo = GISCO_TO_ESTAT.get(cid, cid)
        val = saving.get(geo)
        color = cmap(norm(val)) if val is not None else "#e9e9e9"
        rings = _rings(feat["geometry"])
        for ring in rings:
            ax.fill([p[0] for p in ring], [p[1] for p in ring],
                    facecolor=color, edgecolor="white", linewidth=0.4, zorder=1)
        if val is not None and rings:
            big = max(rings, key=_bbox_area)
            cx = np.mean([p[0] for p in big]); cy = np.mean([p[1] for p in big])
            if EXTENT[0] < cx < EXTENT[1] and EXTENT[2] < cy < EXTENT[3]:
                ax.text(cx, cy, f"{val:.0f}", ha="center", va="center",
                        fontsize=7.5, fontweight="bold", color="black", zorder=3)
    ax.set_xlim(EXTENT[0], EXTENT[1]); ax.set_ylim(EXTENT[2], EXTENT[3])
    ax.set_aspect(1.5); ax.axis("off")
    sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.01, label="gross household saving rate (%)")
    _finish(fig, ax, year)


def draw_geopandas(gj, saving, year):
    import geopandas as gpd
    gdf = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")
    gdf["geo"] = gdf["CNTR_ID"].replace(GISCO_TO_ESTAT)
    sav = pd.Series(saving, name="saving").rename_axis("geo").reset_index()
    gdf = gdf.merge(sav, on="geo", how="left")
    fig, ax = plt.subplots(figsize=(9.2, 9))
    gdf.plot(ax=ax, column="saving", cmap="YlGnBu", edgecolor="white", linewidth=0.4,
             missing_kwds={"color": "#e9e9e9"}, legend=True,
             legend_kwds={"shrink": 0.5, "pad": 0.01,
                          "label": "gross household saving rate (%)"})
    for _, row in gdf.dropna(subset=["saving"]).iterrows():
        c = row.geometry.representative_point()
        if EXTENT[0] < c.x < EXTENT[1] and EXTENT[2] < c.y < EXTENT[3]:
            ax.annotate(f"{row['saving']:.0f}", (c.x, c.y), ha="center", va="center",
                        fontsize=7.5, fontweight="bold")
    ax.set_xlim(EXTENT[0], EXTENT[1]); ax.set_ylim(EXTENT[2], EXTENT[3]); ax.axis("off")
    _finish(fig, ax, year)


def _finish(fig, ax, year):
    ax.set_title(f"Household saving rates across Europe ({year})\n"
                 "Germany and the North save most; the South least", fontweight="bold")
    C.caveat(fig, "Eurostat gross household saving rate (tec00131); GISCO boundaries. "
                  "The North-South gap is structural, not new — it predates the energy shock.")
    C.savefig(fig, "europe_saving_map.png")


def main():
    say("#" * 72)
    say("# Household saving rates across Europe — choropleth")
    say("#" * 72)
    saving, year = load_saving()
    top = sorted(saving.items(), key=lambda kv: kv[1], reverse=True)
    say(f"\nSaving rate by country, {year} (top & bottom):")
    for g, v in top[:4] + [("...", float("nan"))] + top[-4:]:
        say(f"  {g}: {v:.1f}%" if g != "..." else "  ...")
    say("North-South spread is the story: Germany and the Nordics high, the South low.")

    try:
        gj = json.loads(C.http_get(GISCO_URL).text)
    except Exception as e:
        say(f"  GISCO boundaries failed: {e}")
        with open(os.path.join(C.DATA, "europe_map.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    try:
        import geopandas  # noqa: F401
        draw_geopandas(gj, saving, year)
        say("  rendered with geopandas")
    except Exception as e:
        say(f"  geopandas unavailable/failed ({type(e).__name__}); matplotlib renderer")
        draw_matplotlib(gj["features"], saving, year)

    pd.Series(saving, name="saving_rate").rename_axis("geo").to_csv(
        os.path.join(C.DATA, "europe_saving_map.csv"))
    with open(os.path.join(C.DATA, "europe_map.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'europe_map.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
