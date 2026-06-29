# extension_descriptive — the saving question, descriptively

Supervisors asked to approach the saving question **descriptively first**, before
the hypothesis testing. This folder is that descriptive overview: a small set of
charts that set the scene — is the high rate structural or cyclical, where in
Europe is it high, how spending has rotated, and what households actually hold.

Each script is standalone, mirrors the project house style (shaded COVID /
energy-hiking bands, annotations, an italic footnote), reuses the helpers in
`_common.py`, and writes a figure + a `*.md` report + CSVs. All data is free; no
FRED needed.

This now covers **all six descriptive ideas (1–6)** — Wave 1 (structural-vs-cyclical,
the map, goods-vs-services, the asset mix) and Wave 2 (demographics & pensions; the
US discrepancy / pension history).

## How to run

```bash
pip install -r ../requirements.txt   # adds geopandas (for the map; a fallback
                                     # renderer is used if it is unavailable)
bash run.sh                          # or run any script on its own
```

## Idea → script

| # | Idea | Script | What it shows | Data |
|---|---|---|---|---|
| 1 | **Structural vs cyclical** | `structural_vs_cyclical.py` | HP trend/cycle split of the saving rate: did the *trend* step up (a new norm) or is the level a *cycle* that reverts? Cyclical drivers (rate/inflation/GPR) overlaid. | `../data` saving + drivers |
| 4 | **Europe map** | `europe_map.py` | Choropleth of the household saving rate by country (Germany & the North dark, the South light), numbers annotated. geopandas, with a matplotlib-GeoJSON fallback. | `../data/country_saving_annual.csv` + GISCO |
| 5 | **Goods vs services** | `goods_vs_services.py` | Real consumption of goods vs services (2019=100) vs the saving rate — the goods→services rotation behind high saving. | Eurostat `nama_10_fcs` |
| 6 | **What households save in** | `saving_composition_evolution.py` | Non-risky (F2 deposits) vs risky (F5 equity & funds) share of household wealth over time, + a cross-country snapshot. | Eurostat `nasa_10_f_bs` |
| 2 | **Demographics & pensions** | `demographics_pensions.py` | Old-age dependency vs saving, and a funded-pension proxy (F6 share) vs saving — cross-country scatters. Do aging / good pensions move saving? | Eurostat `demo_pjanind` + `nasa_10_f_bs` |
| 3 | **US caution** | `us_caution.py` | US vs euro-area equity (F5) and deposit (F2) shares over time — the persistent gap, with a pension-history narrative for why Europeans look cautious. | OECD (US, no FRED) + Eurostat (EA) |

## Headline descriptive findings (live run)

- **Structural, mostly.** The saving-rate *trend* stepped up ~1.7 pp (12.9%→14.6%)
  and the current cycle is ~0 — the elevation has become a higher norm, not a
  transient bump (the 2020 spike was almost all cyclical).
- **A structural North–South map.** Germany ~20%, France ~18% vs Italy ~11%,
  Spain ~13%, Greece dissaving — a long-standing pattern, not new.
- **Goods→services rotation.** Real services consumption rebounded to ~107
  (2019=100) vs goods ~103; high saving coexists with strong services because
  households pulled back on goods.
- **Equity involvement grew.** The risky (F5) share rose ~+8 pp over the decade
  (29%→37%) and is now the largest single instrument, though deposits + pensions
  (non-risky) still dominate combined.
- **Aging & pensions move saving only weakly.** Old-age dependency↔saving ≈ −0.14;
  the funded-pension proxy (F6)↔saving ≈ +0.34 — pensions shape *where* wealth sits
  more than *how much* is saved.
- **Cautious holders, not low savers.** US households hold ~57% of financial wealth
  in equity & funds vs ~37% in the euro area (and far less cash) — a large,
  persistent, pension-rooted gap.

See `findings.md` for the full write-up and `documentation.pdf` for the figures.

## Notes
- The map uses geopandas if installed; otherwise it renders the same choropleth
  directly from the GISCO GeoJSON with matplotlib (so it always generates).
- Greece is `EL` in Eurostat but `GR` in GISCO (mapped).
- All series are pulled live and revised by the providers — regenerate before citing.
