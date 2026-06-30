#!/usr/bin/env python3
"""
Descriptive #4 --- Household saving rates across Europe (a map)
==============================================================

Supervisor idea: a zoomed-in map of Europe with the saving-rate numbers ---
Germany vs Southern Europe. One of the key deliverables, so it is built to stand
out and to be readable: a choropleth shaded high (dark) to low (light), every
country's number printed with a white halo so it reads on any fill, and a ranked
side list so no value is ever lost on a small country.

Renders with geopandas when available; otherwise it draws the same choropleth
directly from the GISCO GeoJSON with matplotlib (so it always generates).

Data: ../data/country_saving_annual.csv (Eurostat tec00131); GISCO boundaries.
Greece is 'EL' in Eurostat but 'GR' in GISCO (mapped).
    python europe_map.py
"""

import os
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe

import _common as C

REPORT = []
GISCO_URL = ("https://gisco-services.ec.europa.eu/distribution/v2/countries/"
             "geojson/CNTR_RG_20M_2020_4326.geojson")
EXTENT = (-12, 34, 34.5, 71.5)          # Europe bbox (lon_min, lon_max, lat_min, lat_max)
GISCO_TO_ESTAT = {"GR": "EL", "GB": "UK"}
CMAP = plt.cm.YlGnBu
OCEAN = "#eaf2fa"
NODATA = "#dfe3e6"
MIN_LABEL_AREA = 3.0                     # deg^2; below this, label only in the side list


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


# ---- geometry helpers ------------------------------------------------------
def _rings(geom):
    t = geom.get("type")
    if t == "Polygon":
        return [geom["coordinates"][0]]
    if t == "MultiPolygon":
        return [poly[0] for poly in geom["coordinates"]]
    return []


def _shoelace_area(ring):
    x = [p[0] for p in ring]; y = [p[1] for p in ring]
    return abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i]
                   for i in range(-1, len(ring) - 1))) / 2.0


def _centroid(ring):
    return float(np.mean([p[0] for p in ring])), float(np.mean([p[1] for p in ring]))


def _halo_label(ax, x, y, text, fill_rgba, fontsize=10):
    """Bold value with a contrasting halo so it reads on any fill colour."""
    r, g, b = mcolors.to_rgb(fill_rgba)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    txt, halo = ("white", "#202020") if lum < 0.5 else ("#202020", "white")
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, fontweight="bold",
            color=txt, zorder=6,
            path_effects=[pe.withStroke(linewidth=2.6, foreground=halo)])


# ---- the two renderers (both build {geo: (cx, cy, area, color)}) ------------
def draw_matplotlib(features, saving, norm):
    fig, axm, axl = _new_fig()
    cents = {}
    for feat in features:
        cid = str(feat["properties"].get("CNTR_ID"))
        geo = GISCO_TO_ESTAT.get(cid, cid)
        val = saving.get(geo)
        color = CMAP(norm(val)) if val is not None else NODATA
        rings = _rings(feat["geometry"])
        for ring in rings:
            axm.fill([p[0] for p in ring], [p[1] for p in ring],
                     facecolor=color, edgecolor="white", linewidth=0.7, zorder=1)
        if val is not None and rings:
            big = max(rings, key=_shoelace_area)
            cx, cy = _centroid(big)
            cents[geo] = (cx, cy, _shoelace_area(big), color)
    return fig, axm, axl, cents


def draw_geopandas(gj, saving, norm):
    import geopandas as gpd
    gdf = gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")
    gdf["geo"] = gdf["CNTR_ID"].replace(GISCO_TO_ESTAT)
    gdf["val"] = gdf["geo"].map(saving)
    fig, axm, axl = _new_fig()
    gdf.plot(ax=axm, color=[CMAP(norm(v)) if pd.notna(v) else NODATA for v in gdf["val"]],
             edgecolor="white", linewidth=0.7, zorder=1)
    cents = {}
    for _, row in gdf.dropna(subset=["val"]).iterrows():
        rp = row.geometry.representative_point()
        cents[row["geo"]] = (rp.x, rp.y, row.geometry.area, CMAP(norm(row["val"])))
    return fig, axm, axl, cents


def _new_fig():
    fig = plt.figure(figsize=(12.5, 11))
    gs = fig.add_gridspec(1, 2, width_ratios=[3.5, 1.0], wspace=0.0)
    axm = fig.add_subplot(gs[0]); axl = fig.add_subplot(gs[1])
    axm.set_facecolor(OCEAN)
    return fig, axm, axl


def finish(fig, axm, axl, saving, cents, norm, year):
    # value labels on the map (skip the tiniest countries -> the side list covers them)
    for geo, (cx, cy, area, color) in cents.items():
        if area >= MIN_LABEL_AREA and EXTENT[0] < cx < EXTENT[1] and EXTENT[2] < cy < EXTENT[3]:
            _halo_label(axm, cx, cy, f"{saving[geo]:.0f}", color)
    axm.set_xlim(EXTENT[0], EXTENT[1]); axm.set_ylim(EXTENT[2], EXTENT[3])
    axm.set_aspect(1.55); axm.axis("off")
    axm.set_title("Household saving rates across Europe", fontsize=17,
                  fontweight="bold", pad=24)
    axm.text(0.5, 1.012, f"gross saving, % of disposable income · {year}  —  "
             "Germany & the North save most; the South least",
             transform=axm.transAxes, ha="center", va="bottom", fontsize=9.5, color="#555")

    # ranked side list -> every value readable, doubles as the legend
    axl.axis("off"); axl.set_xlim(0, 1); axl.set_ylim(0, 1)
    items = sorted(saving.items(), key=lambda kv: kv[1], reverse=True)
    axl.text(0.0, 0.99, "Saving rate", fontsize=11, fontweight="bold", va="top")
    axl.text(0.0, 0.957, f"% of disp. income · {year}", fontsize=8.3, va="top", color="#555")
    n = len(items); topy = 0.905; row = 0.88 / n
    for i, (geo, val) in enumerate(items):
        y = topy - i * row
        axl.add_patch(plt.Rectangle((0.0, y - row * 0.42), 0.17, row * 0.84,
                                     facecolor=CMAP(norm(val)), edgecolor="white", lw=0.6))
        axl.text(0.23, y, f"{geo}", fontsize=9.5, va="center", fontweight="bold")
        axl.text(0.99, y, f"{val:+.0f}%", fontsize=9.5, va="center", ha="right")

    C.caveat(fig, f"Eurostat gross household saving rate (tec00131). {year} is the latest year with "
                  "full country coverage -- 2025 annual data is still incomplete (only ~7 of 21 "
                  "countries). GISCO boundaries; the North-South gap is structural, predating the shock.")
    C.savefig(fig, "europe_saving_map.png")


def main():
    say("#" * 72)
    say("# Household saving rates across Europe -- choropleth")
    say("#" * 72)
    saving, year = load_saving()
    norm = mcolors.Normalize(vmin=min(saving.values()), vmax=max(saving.values()))
    top = sorted(saving.items(), key=lambda kv: kv[1], reverse=True)
    say(f"\nSaving rate by country, {year}: highest {top[0][0]} {top[0][1]:.1f}%, "
        f"lowest {top[-1][0]} {top[-1][1]:.1f}%. North-South spread is the story.")

    try:
        gj = json.loads(C.http_get(GISCO_URL).text)
    except Exception as e:
        say(f"  GISCO boundaries failed: {e}")
        with open(os.path.join(C.DATA, "europe_map.md"), "w") as f:
            f.write("```\n" + "\n".join(REPORT) + "\n```\n")
        return

    try:
        import geopandas  # noqa: F401
        fig, axm, axl, cents = draw_geopandas(gj, saving, norm)
        say("  rendered with geopandas")
    except Exception as e:
        say(f"  geopandas unavailable/failed ({type(e).__name__}); matplotlib renderer")
        fig, axm, axl, cents = draw_matplotlib(gj["features"], saving, norm)
    finish(fig, axm, axl, saving, cents, norm, year)

    pd.Series(saving, name="saving_rate").rename_axis("geo").to_csv(
        os.path.join(C.DATA, "europe_saving_map.csv"))
    with open(os.path.join(C.DATA, "europe_map.md"), "w") as f:
        f.write("```\n" + "\n".join(REPORT) + "\n```\n")
    print(f"\nWrote {os.path.relpath(os.path.join(C.DATA, 'europe_map.md'), C.ROOT)}")


if __name__ == "__main__":
    main()
