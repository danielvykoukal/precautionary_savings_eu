```
##########################################################################
# Precautionary saving — econometrics  (proxy = GPR)
##########################################################################
Aligned quarterly sample: 2000-10-01 -> 2025-10-01 (101 quarters); columns: ['saving', 'gpr', 'rate', 'inflation']

==========================================================================
1) INTEGRATION ORDER  (ADF H0: unit root;  KPSS H0: stationary)
==========================================================================
series        ADF p lvl  KPSS p lvl   ADF p Δ   order   agree?
saving            0.017       0.087     0.000    I(0)      yes
gpr               0.000       0.100     0.000    I(0)      yes
rate              0.061       0.083     0.001    I(1) CONFLICT
inflation         0.652       0.100     0.000    I(1) CONFLICT
  Note: where ADF and KPSS conflict the order is ambiguous — which is exactly why the long-run test below uses ARDL bounds (order-agnostic).

==========================================================================
2) LONG-RUN: ARDL BOUNDS TEST  (Pesaran-Shin-Smith; valid for mixed I(0)/I(1))
==========================================================================
    H0: no long-run level relationship between saving and the drivers.
  selected UECM (AIC): endog lags=3, exog order=1  (COVID-2020 dropped)
  bounds F-statistic = 0.94
  critical-value bounds (rows = sig. level; lower = I(0), upper = I(1)):
                   lower     upper
    percentile                    
    90.0        2.456553  3.516144
    95.0        2.877209  4.010500
    99.0        3.779853  5.050468
    99.9        4.985268  6.402243
  => F 0.94 vs 5% I(1) upper bound 4.01: cannot confirm a long-run relationship at 5%.

--------------------------------------------------------------------------
   (reference) Johansen trace — interpret ONLY if every series is I(1):
   trace-implied rank at 95% = 2  (treat with caution given mixed orders)

==========================================================================
3) GRANGER CAUSALITY [full sample]  (does past GPR help predict saving?)
==========================================================================
  representation: saving in levels, gpr in levels  (no over-differencing of I(0) series)
lag       p: unc->saving    p: saving->unc
1                  0.907             0.154
2                  0.439             0.315
3                  0.712             0.011
4                  0.724             0.010
  (p<0.05 in column 1 => uncertainty Granger-causes saving.)

==========================================================================
4) VAR + IMPULSE RESPONSE [full sample]  (saving's response to a +1 s.d. GPR shock)
==========================================================================
  estimating the VAR in LEVELS (saving & uncertainty are I(0)); IRF is the level response directly.
  lag length: AIC=6, BIC=2 -> using p=4 (capped at 4)
  peak response +0.108 pp at 0q; response at 12q = +0.040 pp
  peak is NOT significant at 95% (CI [-0.015, +0.230]).
  => a positive uncertainty shock raises saving — consistent with precaution (but NOT significant).
  saved figures/A2_irf_saving_to_uncertainty.png

##########################################################################
# SUBSAMPLE from 2010 (64 quarters) — robustness
##########################################################################

==========================================================================
1) INTEGRATION ORDER  (ADF H0: unit root;  KPSS H0: stationary)
==========================================================================
series        ADF p lvl  KPSS p lvl   ADF p Δ   order   agree?
saving            0.021       0.025     0.000    I(0) CONFLICT
gpr               0.001       0.011     0.000    I(0) CONFLICT
rate              0.498       0.055     0.008    I(1) CONFLICT
inflation         0.250       0.100     0.030    I(1) CONFLICT
  Note: where ADF and KPSS conflict the order is ambiguous — which is exactly why the long-run test below uses ARDL bounds (order-agnostic).

==========================================================================
3) GRANGER CAUSALITY [2010+]  (does past GPR help predict saving?)
==========================================================================
  representation: saving in levels, gpr in levels  (no over-differencing of I(0) series)
lag       p: unc->saving    p: saving->unc
1                  0.987             0.124
2                  0.343             0.250
3                  0.571             0.000
4                  0.738             0.000
  (p<0.05 in column 1 => uncertainty Granger-causes saving.)

==========================================================================
4) VAR + IMPULSE RESPONSE [2010+]  (saving's response to a +1 s.d. GPR shock)
==========================================================================
  estimating the VAR in LEVELS (saving & uncertainty are I(0)); IRF is the level response directly.
  lag length: AIC=6, BIC=2 -> using p=4 (capped at 4)
  peak response +0.161 pp at 6q; response at 12q = +0.089 pp
  peak is NOT significant at 95% (CI [-0.019, +0.340]).
  => a positive uncertainty shock raises saving — consistent with precaution (but NOT significant).

==========================================================================
5) PROXY & TIMING — lead/lag cross-correlation (which proxy, what lag)
==========================================================================
  k>0 = proxy LEADS saving by k quarters; COVID-2020 dropped
  == levels ==
    GPR   peak |corr| = +0.42 at k=-4 (4q lag)
    EPU   peak |corr| = +0.35 at k=-5 (5q lag)
  == changes (Δ) ==
    GPR   peak |corr| = -0.32 at k=-2 (2q lag)
    EPU   peak |corr| = -0.20 at k=-1 (1q lag)
  saved figures/A3_proxy_leadlag.png

==========================================================================
HOW TO READ THIS
==========================================================================
- ARDL bounds is the long-run verdict (order-agnostic). Johansen is only a reference and should be ignored unless every series is I(1).
- Granger & VAR now use levels for the I(0) core, so a null here is a real (if low-power) null, not an over-differencing artifact.
- Compare full sample vs subsample and GPR vs EPU (--proxy epu) before settling on the headline. Section 5 reports the best lead/lag per proxy.
```
