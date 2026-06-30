```
##################################################################
# MFDFM nowcast of the euro-area quarterly saving rate
##################################################################
  monthly leads: sav_intent, unemp_exp, m1_growth, m3_growth, gpr, epu, rate
  104 quarterly saving obs, 2000Q1–2025Q4; 1 factor, AR(2)

in-sample fit: corr(nowcast, actual) = 0.680, RMSE = 1.344 pp

Pseudo-OOS (last 8 quarters blanked, nowcast from the leads):
quarter    actual   MFDFM   error
2024Q1      15.15   14.31   -0.84
2024Q2      15.23   13.70   -1.53
2024Q3      15.02   13.47   -1.55
2024Q4      14.81   13.40   -1.41
2025Q1      15.06   13.39   -1.67
2025Q2      15.14   13.40   -1.74
2025Q3      14.78   13.41   -1.37
2025Q4      14.42   13.41   -1.01
  MFDFM OOS RMSE = 1.420 pp
  bridge OOS RMSE (same quarters) = 0.720;  random walk = 0.255
```
