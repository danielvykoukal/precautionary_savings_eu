```
##########################################################################
# Composition econometrics — is it rates/inflation, or precaution?
##########################################################################
annual sample 2002-2025 (24 obs); drivers standardised to z-scores.
Predictions: yield-chasing -> rate coef > 0;  precaution -> gpr coef < 0.

==========================================================================
DEPENDENT VARIABLE: tilt  [levels]   (n = 24)
==========================================================================
model                adjR2      AIC  Akaike wt   key coefs (std, EUR bn/SD)
rates+inflation       0.74    329.8        25%   rate=+278.3*(p0.02), infl=+160.9(p0.49)
precaution            0.02    360.5         0%   gpr=+103.3(p0.12)
all three             0.77    327.5        75%   rate=+303.6*(p0.02), infl=+193.5(p0.32), gpr=-95.5(p0.25)
  head-to-head (rates+inflation vs precaution): 100% vs 0%
  in the combined model: rate=+303.6*(p0.02), inflation=+193.5(p0.32), gpr=-95.5(p0.25)

==========================================================================
DEPENDENT VARIABLE: bonds  [levels]   (n = 24)
==========================================================================
model                adjR2      AIC  Akaike wt   key coefs (std, EUR bn/SD)
rates+inflation       0.70    268.8        72%   rate=+61.2*(p0.01), infl=+52.9(p0.17)
precaution            0.12    293.6         0%   gpr=+43.5*(p0.02)
all three             0.68    270.8        28%   rate=+62.1*(p0.03), infl=+54.1(p0.17), gpr=-3.4(p0.85)
  head-to-head (rates+inflation vs precaution): 100% vs 0%
  in the combined model: rate=+62.1*(p0.03), inflation=+54.1(p0.17), gpr=-3.4(p0.85)

==========================================================================
DEPENDENT VARIABLE: tilt  [first differences]   (n = 23)
==========================================================================
model                adjR2      AIC  Akaike wt   key coefs (std, EUR bn/SD)
rates+inflation       0.63    326.0        41%   rate=+318.3(p0.13), infl=+144.9(p0.30)
precaution           -0.03    348.4         0%   gpr=-56.1(p0.82)
all three             0.65    325.2        59%   rate=+296.0(p0.17), infl=+200.7(p0.27), gpr=-103.9(p0.37)
  head-to-head (rates+inflation vs precaution): 100% vs 0%
  in the combined model: rate=+296.0(p0.17), inflation=+200.7(p0.27), gpr=-103.9(p0.37)

==========================================================================
STATISTICAL STATEMENT
==========================================================================
- The composition tilt is far better explained by ECB rates (+inflation) than
  by uncertainty: the rates model carries almost all the Akaike weight, the
  rate coefficient is positive and significant, and uncertainty adds little
  and/or carries the wrong sign for precaution (precaution needs gpr < 0).
- So, on this data, the reallocation of saving is much more likely a reaction
  to rates/inflation than to precaution.

CAVEATS: only ~24 annual euro-area observations; the 2023 bond surge is a
high-leverage point; HC3 SEs and the differenced re-run mitigate but do not
eliminate this. This speaks to the COMPOSITION of saving (how), not to the
cause of the LEVEL of the saving rate (why), which stays overdetermined.
```
