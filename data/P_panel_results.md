```
######################################################################
# Country panel: household saving rate on its drivers (two-way FE)
######################################################################
  1648 obs, 16 countries, 2000Q1–2025Q4
  countries: ['AT', 'BE', 'CZ', 'DE', 'DK', 'EL', 'ES', 'FI', 'FR', 'HU', 'IE', 'IT', 'NL', 'PL', 'PT', 'SE']

=== Two-way FE (country + quarter), SE clustered by country ===
  within R-squared = 0.154;  overall = 0.085
driver                                       coef      se      t       p
Sovereign spread (10y − Bund, pp)          -0.338   0.117  -2.89   0.004
Saving intentions (survey balance)          0.063   0.061   1.03   0.305
Unemployment expectations (balance)         0.030   0.020   1.51   0.131
Headline inflation (%)                      0.012   0.286   0.04   0.965
Energy inflation (%)                        0.016   0.030   0.52   0.600

=== robustness: coefficient on each driver across specifications ===
driver                                    2-way FE  country FE   pooled
Sovereign spread (10y − Bund, pp)           -0.338      -0.267   -0.696
Saving intentions (survey balance)           0.063       0.101    0.041
Unemployment expectations (balance)          0.030       0.046    0.055
Headline inflation (%)                       0.012       0.018    0.266
Energy inflation (%)                         0.016       0.013   -0.013

=== standardized betas (SD of saving per 1 SD of driver) ===
  Sovereign spread (10y − Bund, pp)        -0.135  [-0.227, -0.043]
  Saving intentions (survey balance)       +0.392  [-0.358, +1.142]
  Unemployment expectations (balance)      +0.131  [-0.039, +0.300]
  Headline inflation (%)                   +0.006  [-0.279, +0.292]
  Energy inflation (%)                     +0.035  [-0.096, +0.167]
```
