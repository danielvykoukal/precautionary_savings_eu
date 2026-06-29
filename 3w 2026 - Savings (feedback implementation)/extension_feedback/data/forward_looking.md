```
########################################################################
# Forward-looking approach — do expectations lead saving?
########################################################################
  survey geo=EA20; saving-intentions=BS-SV-NY; unemployment-expectations=BS-UE-NY
  VIX step failed: HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=60)

forward-looking composite from ['unemp_expect', 'saving_intent'] (1985-01-01->2025-10-01, 164 quarters)

(a) lead-lag corr(saving_t, composite_{t-k}); k>0 = composite leads:
   k=-4q : corr=+0.39
   k=-3q : corr=+0.53
   k=-2q : corr=+0.63
   k=-1q : corr=+0.74
   k=+0q : corr=+0.76  <- max |corr|
   k=+1q : corr=+0.62
   k=+2q : corr=+0.57
   k=+3q : corr=+0.47
   k=+4q : corr=+0.31
  => strongest co-movement is contemporaneous/lagging (k=0q, corr +0.76).

(b) saving_t ~ composite_(t-1):  beta=+1.88 (p=0.000), R^2=0.38, n=107
    benchmark saving_t ~ GPR_t (contemporaneous): R^2=0.00, n=108
    (a forward composite that predicts one quarter AHEAD is the value-add the supervisors asked for, beyond contemporaneous GPR.)
```
