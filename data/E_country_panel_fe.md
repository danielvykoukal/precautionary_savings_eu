```
######################################################################
# Country panel, two-way fixed effects — within-country saving response
######################################################################

[1] Eurostat HICP by country (energy + headline) ...
  merged panel: 21 countries x 12 years, 238 obs (2014-2025)

--- Saving on the energy shock: pooled vs two-way FE ---

[pooled OLS (no FE)]  n=238
    energy inflation                  : -0.021 (se 0.040, p 0.604)
    headline inflation                : +0.057 (se 0.243, p 0.816)

[two-way FE (country + year)]  n=238
    energy inflation (within)         : +0.011 (se 0.025, p 0.675)
    headline inflation (within)       : -0.128 (se 0.231, p 0.581)
  (Identifying coefficient: energy inflation under two-way FE. A positive, significant value supports heterogeneity-driven precaution.)

[2] Country-level GPR (best-effort) ...
  GPRC panel: 12 countries, 139 obs

[two-way FE with country GPR]  n=139
    country GPR (z, within)           : -0.719 (se 0.659, p 0.275)
```
