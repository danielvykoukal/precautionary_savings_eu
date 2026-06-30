```
##########################################################################
# Saving-rate -> financial-assets bridge: housing & borrowing close the gap
##########################################################################
  non-financial geo = EA20, financial geo = EA20

identity max abs error across years: 1 EUR mn (should be ~0)
uses-side build vs gross saving B8G: max gap 19,038 EUR mn = 0.22 pp of the rate (capital-account residual) -> the saving rate IS, up to that residual, the sum of asset types + housing − borrowing

VALIDATION — can the component data reproduce the REPORTED saving rate?
  reported = Eurostat nasq_10_ki (annual mean of quarters); ours = the uses-side build (asset types + housing − borrowing + transfers) / (B6G + D8net)
 year  reported  computed  diff(pp)
 2015    12.52%    12.51%     -0.01
 2016    12.54%    12.40%     -0.14
 2017    12.45%    12.23%     -0.22
 2018    12.49%    12.64%     +0.15
 2019    13.02%    12.99%     -0.02
 2020    19.45%    19.21%     -0.24
 2021    17.32%    17.22%     -0.10
 2022    13.45%    13.57%     +0.11
 2023    14.17%    13.97%     -0.20
 2024    15.05%    15.03%     -0.03
 2025    14.85%    14.86%     +0.01
  mean abs error 0.083 pp, max 0.245 pp over 2002-2025 -> the bottom-up build reproduces the headline rate.

================================================================
WHY the saving rate moved — income side + where the saving flowed
================================================================
period                      rate%  disp.inc bn   cons. bn
2015-19 (pre-COVID)         12.6        7,062      6,172
2020-21 (COVID)             18.2        7,685      6,277
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
 2018      908      645      214      530    12.6%
 2019      976      670      280      654    13.0%
 2020    1,458      665      263    1,116    19.2%
 2021    1,358      785      329    1,027    17.2%
 2022    1,138      883      294      733    13.6%
 2023    1,289      906       80      619    14.0%
 2024    1,434      845      104      821    15.0%
 2025    1,458      873      222      907    14.9%

Household BORROWING — net incurrence of liabilities (EUR bn/yr):
  2019: total  280.1   of which loans/mortgages (F4)  244.2
  2020: total  262.5   of which loans/mortgages (F4)  213.0
  2021: total  328.8   of which loans/mortgages (F4)  308.5
  2022: total  294.2   of which loans/mortgages (F4)  279.9
  2023: total   80.1   of which loans/mortgages (F4)   39.1
  2024: total  103.6   of which loans/mortgages (F4)   94.6
  2025: total  221.6   of which loans/mortgages (F4)  204.3

Saving rate built from its components, % of GDI, pooled 2023-2025:
  Deposits & cash (F2)                 +2.8
  Debt securities (F3)                 +1.4
  Equity & funds (F5)                  +1.9
  Insurance & pensions (F6)            +1.5
  Other financial                      +0.5
  + Housing & non-fin. inv.            +9.2
  − Borrowing (liabilities)            -1.4
  + Transfers & residual               -1.3
  = Saving rate                       +14.6
```
