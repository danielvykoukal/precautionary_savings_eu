```
####################################################################
# Bridge nowcast of the euro-area quarterly saving rate
####################################################################
  sample 2000Q1…2025Q4  (104 quarters); predictors: sav_intent, unemp_exp, m1_growth, m3_growth, gpr, epu, rate

Full-sample bridge: R-squared = 0.710
predictor                        coef       t       p
Saving intentions               0.252    9.42   0.000
Unemployment expectations       0.090    6.07   0.000
M1 growth (YoY)                -0.062   -2.46   0.014
M3 growth (YoY)                 0.212    4.21   0.000
Geopolitical risk (GPR)        -0.004   -1.21   0.225
Economic policy uncertainty    -0.004   -3.29   0.001
ECB / short rate               -0.180   -2.16   0.030

Pseudo-out-of-sample (expanding window, 1-step-ahead), 2012Q1–2025Q4:
  RMSE  bridge = 1.629   AR(1) = 2.499   random walk = 1.841  (pp of the saving rate)
  bridge vs RW: +12% RMSE;  bridge vs AR(1): +35%
  ex-2020:  bridge = 0.704   AR(1) = 0.676   RW = 0.701
```
