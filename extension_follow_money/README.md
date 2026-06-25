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

| Script | Question | Data |
|---|---|---|
| `follow_the_money.py` | Where did the extra saving go — instant-access cash, or bonds & time deposits (reach for yield)? | Eurostat `nasa_10_f_tr` (household financial transactions) |
| `saving_vs_rates_reversal.py` | Did saving ease when the ECB *cut* rates in 2024–25? | `../data` saving rate + ECB rate |

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
confounded by the post-COVID unwind. Not decisive on its own.

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
