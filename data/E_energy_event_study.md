```
######################################################################
# Energy-shock event study / DiD — exposed vs less-exposed countries
######################################################################
panel: 21 countries x 12 years (2014-2025); 11 high-exposure

--- Difference-in-differences (Exposed x Post>=2022) ---
  editorial high-exposure dummy                 : d = -0.40 pp (se 1.29, p 0.755)
  standardised peak-2022 energy inflation       : d = -0.77 pp (se 0.59, p 0.194)
  (d>0 => more-exposed countries raised saving more after 2022.)

--- Event-study coefficients (high-exposure x year; base 2021) ---
year       coef (pp)      se       p
2014           +0.39    1.50   0.797
2015           +0.03    1.47   0.986
2016           +0.28    1.48   0.849
2017           +0.12    1.66   0.944
2018           +1.70    1.85   0.357
2019           +1.18    1.37   0.388
2020           +0.72    1.20   0.550
2021           +0.00    0.00   0.000
2022           -0.06    1.36   0.965
2023           +0.17    1.84   0.924
2024           +0.48    1.71   0.780
2025           -0.41    2.00   0.837

parallel-trends check: largest |pre-2022 coef| = 1.70 pp (sizeable — qualifies the design)
```
