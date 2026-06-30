```
######################################################################
# Do all the asset flows, combined, behave like the saving rate?
######################################################################

sample 2002-2025  (geo=EA20)
  reconciliation: corr(B8G/B6G, published saving rate) = +1.00 (should be ~+1 — same concept).
  corr(total financial-asset flow,  saving rate) = +0.87
  corr(financial-flow rate %GDI,    saving rate) = +0.73
  regression: saving_rate = 9.5 + 0.47*financial-flow-rate

  => combining ALL asset flows reproduces the saving-rate path: the decomposition (and the tilt within it) is a slice of household saving.
```
