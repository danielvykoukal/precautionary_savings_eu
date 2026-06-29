# Identification extensions

Stronger tests of the precautionary-saving hypothesis than the aggregate
time-series core (`../03_econometrics.py`). The aggregate euro-area series is
underpowered (~101 quarters, a COVID break, four drivers that all moved together
after 2022), so these scripts change the *identification strategy*: exploit
heterogeneity, sharpen the dependent variable, use a more robust estimator, and
bring in direct survey evidence.

Each script is standalone. They **reuse the CSVs already produced by the main
pipeline** (read from `../data`) and pull only the few extra series they need,
writing their own outputs to `extensions/data` and `extensions/figures` so the
main project is untouched. Shared helpers live in `_common.py`.

## How to run

```bash
# 1) main pipeline first, so ../data exists
cd .. && python3 01_collect_data.py && cd extensions
# 2) all extensions (classic Python, no venv)
bash run_extensions.sh
# or individually
python3 local_projections.py
python3 country_panel_fe.py --help
```

No new dependencies beyond the main `../requirements.txt`.

## What each script does

| Script | Idea | Identifying assumption | Extra data (free) |
|---|---|---|---|
| `local_projections.py` | Jordà local-projection IRF as a robust cross-check on the VAR | uncertainty ordered most-exogenous (no contemporaneous rate/inflation control) | none (reuses `../data`) |
| `energy_event_study.py` | Event study / diff-in-diff: did more energy-exposed countries save more after 2022? | the 2022 energy shock is exogenous to saving *preferences*; country & year FE absorb structure and common shocks | none (reuses `../data`) |
| `country_panel_fe.py` | Two-way (country+year) FE panel of saving on country-specific shocks | within-country variation in the shock is conditionally exogenous given FE | Eurostat HICP by country; country GPR (best-effort) |
| `saving_composition.py` | Flight-to-safety: share of household financial saving going into currency & deposits (F2) | precaution favours liquid/safe assets, intertemporal substitution chases yield | Eurostat `nasa_10_f_tr` |
| `saving_intentions.py` | Direct survey evidence: intended saving and job-loss fear vs the realised rate | survey balances measure the precautionary motive | Eurostat consumer survey `ei_bsco_m` |

## What we found (from a clean run — regenerate before citing)

The evidence is **mixed and, on balance, cautious** — consistent with the core
result that the saving rise is *consistent with, but not proof of,* precaution.

- **Local projections** — response of saving to a GPR shock is positive but
  insignificant (CI excludes zero only on impact). Corroborates the VAR's null.
- **Energy event study / DiD** — null: more-exposed countries did **not** raise
  saving significantly more after 2022 (DiD coefficients ≈ 0, even slightly
  negative; pre-trends are non-trivial, which qualifies the design). The
  cross-country leg is confounded by structural North–South habits.
- **Country panel FE** — null: the within-country coefficients on energy
  inflation (+0.01, n.s.) and on country GPR (−0.72, n.s.) are insignificant.
  Pooled-vs-FE contrast shows the confound the FE remove.
- **Composition (flight-to-safety)** — the liquid-deposit (F2) share spiked to
  ~65% in **2020** (textbook precautionary cash-hoarding during lockdowns) but
  **fell** to ~36% after 2022. So the post-2022 saving did *not* take a
  flight-to-safety form — evidence *against* a simple precautionary reading of
  the post-2022 rise (more consistent with yield-chasing as rates rose).
- **Survey intentions** — the one clearly **supportive** leg: intended saving
  (corr ≈ +0.50; +0.59 since 2010) and unemployment fear (≈ +0.36; +0.40) both
  co-move positively with the realised saving rate.

**Bottom line.** Direct survey expectations and the 2020 episode support a
precautionary motive, but the harder identification designs (panel, event study,
local projections) and the post-2022 asset composition do **not** confirm a
robust precautionary surge *after 2022* specifically. The honest verdict remains
a measured one.

## Caveats

- Few clusters (21 countries) make clustered SEs approximate; treat panel/DiD
  p-values as indicative.
- The energy event study's pre-trends are not perfectly flat — the parallel-
  trends assumption is imperfect.
- `country_panel_fe.py` uses country-specific *energy inflation* as the
  within-country shock; country GPR is added where available (12 countries).
- All series are pulled live and revised by providers — regenerate before citing.
