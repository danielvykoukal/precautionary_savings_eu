```
##########################################################################
# Composition econometrics --- is it rates/inflation, or precaution?
##########################################################################
annual sample 2002-2025 (24 obs); drivers standardised to z-scores.
Predictions: yield-chasing -> rate coef > 0;  precaution -> gpr coef < 0.

==========================================================================
DEPENDENT VARIABLE: composition tilt (EUR bn/yr), levels
==========================================================================

===============================================
          (1) rates+infl (2) precaution (3) all
-----------------------------------------------
rate      278.3**                       303.6**
          (123.3)                       (125.6)
inflation 160.9                         193.5  
          (231.0)                       (194.9)
gpr                      103.3          -95.5  
                         (65.6)         (83.9) 
Intercept -123.5*        -123.5         -123.5*
          (70.9)         (88.6)         (66.7) 
Adj. R2   0.74           0.02           0.77   
N         24             24             24     
R2        0.76           0.06           0.80   
===============================================
Standard errors in parentheses.
* p<.1, ** p<.05, ***p<.01
  horse race (all drivers together): ECB rate b=+304 (p=0.02, significant); uncertainty b=-95 (p=0.25, n.s.).
  explained variation (adj. R2): rates+inflation 0.74  vs  precaution 0.02.

==========================================================================
DEPENDENT VARIABLE: net bond purchases (EUR bn/yr), levels
==========================================================================

===============================================
          (1) rates+infl (2) precaution (3) all
-----------------------------------------------
rate      61.2***                       62.1** 
          (23.2)                        (28.2) 
inflation 52.9                          54.1   
          (38.7)                        (39.6) 
gpr                      43.5**         -3.4   
                         (18.6)         (18.5) 
Intercept -3.6           -3.6           -3.6   
          (15.9)         (22.1)         (16.8) 
Adj. R2   0.70           0.12           0.68   
N         24             24             24     
R2        0.72           0.16           0.72   
===============================================
Standard errors in parentheses.
* p<.1, ** p<.05, ***p<.01
  horse race (all drivers together): ECB rate b=+62 (p=0.03, significant); uncertainty b=-3 (p=0.85, n.s.).
  explained variation (adj. R2): rates+inflation 0.70  vs  precaution 0.12.

==========================================================================
ROBUSTNESS: composition tilt, FIRST DIFFERENCES
==========================================================================

===============================================
          (1) rates+infl (2) precaution (3) all
-----------------------------------------------
rate      318.3                         296.0  
          (212.4)                       (218.1)
inflation 144.9                         200.7  
          (140.7)                       (183.1)
gpr                      -56.1          -103.9 
                         (242.3)        (116.6)
Intercept -13.3          -13.3          -13.3  
          (85.4)         (114.2)        (87.9) 
Adj. R2   0.63           -0.03          0.65   
N         23             23             23     
R2        0.66           0.02           0.70   
===============================================
Standard errors in parentheses.
* p<.1, ** p<.05, ***p<.01
  horse race (all drivers together): ECB rate b=+296 (p=0.17, n.s.); uncertainty b=-104 (p=0.37, n.s.).
  explained variation (adj. R2): rates+inflation 0.63  vs  precaution -0.03.

==========================================================================
STATISTICAL STATEMENT
==========================================================================
- Let the drivers compete: only the ECB rate is significant (p~0.02) and
  positive; inflation and uncertainty are not, and uncertainty has the
  wrong sign for precaution.
- Explained variation is lopsided: the rates+inflation model accounts for
  ~74% of the tilt's variation; the precaution model ~2%.
- Verdict: on this data the reallocation of saving is a reaction to
  rates/inflation, not to precaution.

CAVEATS: ~24 annual euro-area observations; the 2023 bond surge is a
high-leverage point (HC3 SEs and the differenced re-run mitigate, not
eliminate). This speaks to the COMPOSITION of saving (how), not the LEVEL
of the saving rate (why), which stays overdetermined.
```
