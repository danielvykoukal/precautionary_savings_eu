```
##########################################################################
# Saving-rate -> financial-assets bridge: housing & borrowing close the gap
##########################################################################
  non-financial geo = EA20, financial geo = EA20

identity max abs error across years: 1 EUR mn (should be ~0)

VALIDATION — can the component data reproduce the REPORTED saving rate?
  reported = Eurostat nasq_10_ki (annual mean of quarters); ours = B8G / (B6G + D8net)
 year  reported  computed  diff(pp)
 2015    12.52%    12.51%     -0.00
 2016    12.54%    12.54%     +0.00
 2017    12.45%    12.45%     -0.00
 2018    12.49%    12.50%     +0.00
 2019    13.02%    13.01%     -0.00
 2020    19.45%    19.42%     -0.04
 2021    17.32%    17.28%     -0.04
 2022    13.45%    13.45%     -0.00
 2023    14.17%    14.18%     +0.01
 2024    15.05%    15.05%     -0.00
 2025    14.85%    14.85%     -0.00
  mean abs error 0.005 pp, max 0.042 pp over 2002-2025 -> the bottom-up build reproduces the headline rate.

================================================================
WHY the saving rate moved — income side + where the saving flowed
================================================================
period                      rate%  disp.inc bn   cons. bn
2015-19 (pre-COVID)         12.6        7,062      6,172
2020-21 (COVID)             18.3        7,685      6,277
2022-25 (post-rate-shock)   14.4        9,224      7,894

Income side — cumulative growth across the key transitions:
  2019 -> 2020 (COVID onset): disposable income +0.1%, consumption -7.2%  -> a CONSUMPTION collapse, not an income boom
  2019 -> 2023 (durable):     disposable income +21.2%, consumption +19.6%  -> nominal income outran consumption

Uses side — where the saving flowed (% of disposable income, period sum):
                              2015-19  2020-21  2022-25
financial assets                  7.5     13.9      8.3
housing / non-fin. inv.           8.6      9.4      9.5
borrowing (liabilities)           2.8      3.8      1.9

Reading: the COVID spike was forced saving (consumption fell ~7%) parked in FINANCIAL ASSETS (7.5%->13.9% of income). The durable post-2022 step is income outrunning consumption WHILE borrowing fell (2.8%->1.9%): households saved a little more and levered up less, so the NET rate stayed high. Housing was steady throughout — it did not drive the increase.

Household capital + financial bridge (EUR bn, euro area):
 year   saving  housing   borrow  fin.ass sav.rate
 2018      908      645      214      530    12.5%
 2019      976      670      280      654    13.0%
 2020    1,458      665      263    1,116    19.4%
 2021    1,358      785      329    1,027    17.3%
 2022    1,138      883      294      733    13.5%
 2023    1,289      906       80      619    14.2%
 2024    1,434      845      104      821    15.1%
 2025    1,458      873      222      907    14.8%

Household BORROWING — net incurrence of liabilities (EUR bn/yr):
  2019: total  280.1   of which loans/mortgages (F4)  244.2
  2020: total  262.5   of which loans/mortgages (F4)  213.0
  2021: total  328.8   of which loans/mortgages (F4)  308.5
  2022: total  294.2   of which loans/mortgages (F4)  279.9
  2023: total   80.1   of which loans/mortgages (F4)   39.1
  2024: total  103.6   of which loans/mortgages (F4)   94.6
  2025: total  221.6   of which loans/mortgages (F4)  204.3

Bridge as % of gross disposable income, pooled 2023-2025:
  Gross saving (saving rate)          +14.7
  − Housing & non-fin. investment      -9.2
  + Capital transfers (net)            +0.2
  + Borrowing (liabilities)            +1.4
  − Stat. discrepancy                  +1.0
  = Financial assets acquired          +8.3
```
