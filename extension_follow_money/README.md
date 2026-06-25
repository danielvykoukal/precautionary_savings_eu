# extension_follow_money

Does the post-2022 rise in euro-area saving look more like **yield-chasing**
(money moving into higher-paying, less-liquid assets as the ECB raised rates)
than **precaution** (money parked in instant-access cash "just in case")? The two
stories make *opposite* predictions about where the money goes and what happens
when rates fall — so we test those.

These scripts reuse the main pipeline's `../data` and pull one extra Eurostat
dataset. Run the main pipeline first so `../data` exists.

```bash
cd .. && python3 01_collect_data.py && cd extension_follow_money
bash run.sh                 # or run the two scripts individually
```

## Scripts

Run `follow_the_money.py` first (it writes `follow_the_money.csv`, which several
others read), or just `bash run.sh`.

| Script | Question | Data |
|---|---|---|
| `follow_the_money.py` | Where did the extra saving go — instant-access cash, or bonds & time deposits (reach for yield)? | Eurostat `nasa_10_f_tr` |
| `net_flows_by_asset.py` | Net flow into *each* asset type (currency/overnight, time deposits, bonds, equity/funds, insurance/pensions) vs the saving rate | Eurostat `nasa_10_f_tr` + `../data` saving |
| `total_vs_saving.py` | **Link to the headline:** does the *sum of all* asset flows behave like the saving rate? (reconciliation via disposable income) | Eurostat `nasa_10_f_tr` + `nasa_10_nf_tr` + `../data` saving |
| `plot_tilt_vs_saving.py` | The composition tilt vs the saving rate, with ZLB / COVID / period-of-interest regimes | `follow_the_money.csv` + `../data` saving |
| `tilt_vs_rates.py` | The tilt vs the ECB rate, and their correlation | `follow_the_money.csv` + `../data` ECB rate |
| `saving_vs_rates_reversal.py` | Did saving track the ECB rate (axes aligned on the post-2022 window)? | `../data` saving rate + ECB rate |
| `composition_econometrics.py` | **Is the tilt better explained by rates/inflation or by precaution?** (model comparison, Akaike weights) | `follow_the_money.csv` + `../data` rate/inflation/GPR |

## What we found (clean run — regenerate before citing)

**Follow the money — strong support for yield-chasing.** The destination of
household financial saving flipped completely after rates rose:

- Share going into **instant-access cash & overnight deposits**: **~66% (2015–19) → ~2% (2022–25)**.
- Share going into **bonds + time deposits**: **−29% → +52%**.
- **Net bond purchases** went from *negative* (households were net sellers:
  about −€40–50 bn/yr in 2019–21) to **+€96 bn (2022), +€311 bn (2023)**, easing
  to +€71 bn (2024) and +€31 bn (2025).

Households went from shunning bonds to buying them in record size exactly as bond
yields jumped, and abandoned instant-access cash. That is the reach-for-yield
fingerprint; precaution predicts the opposite (pile into instant-access cash, as
indeed happened in **2020**).

**Reversal — weak and mixed.** Saving rose only ~0.6 pp during the hiking phase
and eased only ~0.4 pp during the cutting phase — directionally consistent with
yield-chasing but tiny, and the raw 2021+ saving/rate correlation is negative,
confounded by the post-COVID unwind. Not decisive on its own. (With axes aligned
on the post-2022 window the saving rate and the ECB rate do overlay closely,
corr ≈ +0.71.)

**Tilt vs rates — strong.** The composition tilt (locked-for-yield minus
instant-access) correlates **+0.79** with the ECB policy rate (annual).

**Econometrics — rates/inflation vs precaution (model comparison).** We regress
the tilt (and net bond purchases) on the ECB rate, inflation, and a precaution
proxy (GPR), and compare a *rates+inflation* model against a *precaution* model
with Akaike weights (a probability that each is the best in the set):

- The tilt: rates+inflation model adj-R² ≈ 0.74 (rate coef **+, p≈0.02**) vs the
  precaution model adj-R² ≈ 0.02. **Akaike weight: ~100% rates/inflation vs ~0%
  precaution.** In the combined model uncertainty is insignificant.
- Net bond purchases: same verdict (rate coef +, p≈0.01; ~100% vs 0%).
- In first differences the rate coefficient is right-signed but no longer
  significant (p≈0.13 — small-sample power), yet precaution still gets ~0% weight.

So we *can* make the statistical statement: on this data the reallocation of
saving is far more likely a reaction to rates/inflation than to precaution.

**Link to the saving rate.** The tilt is a *composition* measure, so it doesn't
map to the saving rate directly. The bridge is that **summing all the asset flows
= households' net acquisition of financial assets**, the part of saving that goes
into financial wealth. That total tracks the saving rate: corr **+0.87** in levels
and **+0.73** as a share of disposable income, and the income/saving figures
reproduce the published saving rate exactly (B8G/B6G, corr +1.00). The combined
flow sits a few points *below* the saving rate — the wedge is mainly housing
investment, which saving funds but isn't a financial asset. So the decomposition
(and the tilt within it) is a genuine slice of household saving.

## Honest bottom line

The composition evidence is genuinely strong: *how* euro-area households saved
after 2022 was strongly yield-driven (into bonds and term deposits, out of cash).
But this is about the **allocation** of saving, not proof that the **level** rise
in the aggregate saving rate was *caused* by rates — that remains overdetermined
(the formal tests in `../extensions/` return nulls for both the precautionary and
the cross-country channels). The fair statement: **rates clearly reshaped where
people saved; the size of the overall increase is harder to attribute cleanly.**

## Caveats

- Flows are *net*, so the share denominator (total net financial-asset
  acquisition) can be small and make shares swing past 100% or go negative; the
  euro-bn bond flows are the robust, interpretable numbers.
- Euro-area aggregate (EA20); no country breakdown here.
- Series are pulled live and revised — regenerate before citing.
