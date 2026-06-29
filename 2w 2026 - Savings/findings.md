# Findings — Precautionary Saving in Europe

*Companion to the scripts. Run `bash run_all.sh` first (or `01_collect_data.py` → `02_make_figures.py` → `03_econometrics.py`); they write `data/` and `figures/`.*

> **Note on numbers.** The exact values below come from published Eurostat news
> releases, ECB Economic Bulletin boxes, and the Caldara–Iacoviello GPR index —
> the same series the script pulls live. When you run the script, confirm the
> figures against the freshly downloaded data (vintages get revised).

---

## Our hypothesis

> Europe's elevated household saving rate is **substantially precautionary**:
> driven by geopolitical and economic uncertainty, it should (A) move *with*
> uncertainty over time, (B) have risen *more* where the Russia/energy shock bit
> hardest, and (C) be concentrated among households who can actually afford to
> save — while the fear itself weighs heaviest on those who can't.

The three charts test the three legs (A, B, C). Short version: the **time-series
leg is strong**, the **cross-country leg is suggestive but confounded**, and the
**distributional leg reframes who bears the cost**.

---

## Chart A — Saving rate vs. uncertainty over time *(the strongest evidence)*

**What it shows.** The euro-area household saving rate sat near 12–13% before the
pandemic, spiked mechanically to ~25% in 2020 (lockdowns = forced saving), fell
back, then — crucially — **climbed again from mid-2022 and stayed elevated near
15%** (15.7% in Q3 2024, 15.4% in Q2 2025, easing only to ~14.4% by Q4 2025).
That second climb lines up with the February 2022 invasion (marked on the chart)
and the energy-price/inflation shock, when the GPR and EU EPU indices jumped.

**Intuition.** The 2020 spike was *involuntary* — people couldn't spend. The
post-2022 rise is the interesting one: incomes and wealth had largely normalised,
yet households kept saving. Buffer-stock theory says that when the future looks
riskier, households rebuild precautionary buffers — they defer big purchases and
hold cash "just in case." The ECB's own work attributes the persistence to
exactly this, and a Nov-2025 ECB survey found precautionary motives relevant for
~half of savers.

**Bearing on the hypothesis.** Supports leg (A). The co-movement is real and
visible. **Caveat:** co-movement ≠ causation. Saving also rose because the ECB
hiked rates (saving became more rewarding) and because high inflation made
households cautious — these move alongside uncertainty, so the chart shows the
*correlation*, not a clean causal channel. For a blog that's fine; just don't
overclaim.

---

## Chart B — Energy shock vs. rise in saving, by country *(suggestive, confounded)*

**What it shows.** A scatter: x = each country's peak 2022 energy-price inflation
(the size of the shock), y = the change in its saving rate from 2019 to 2023/24.
Red = high Russia/energy exposure (Germany, Austria, Finland, CEE, Baltics),
blue = lower exposure (much of the South/West). The companion bar chart (`B2`)
ranks the 2024 saving-rate *level*: **Germany ~20% and France high at the top,
Spain (12.7%) and Italy (12.0%) below the EU average.**

**Intuition.** If precaution is driven by the war/energy shock, the countries
hit hardest should have *raised* saving the most. There is something to this —
high-exposure, energy-import-dependent economies did see both the biggest price
shocks and strong saving — but the relationship is noisy.

**Bearing on the hypothesis.** Partially supports leg (B), with an honest
confound: **Germany and the Nordics are structurally high savers** (they were
before the war, too), while the South structurally saves less. So a raw "who
saves most" map mostly reflects long-standing habits, not the shock. Using the
*change* since 2019 (the scatter's y-axis) nets out some of that structural level
— that's the more defensible test. Expect a **positive but modest slope**: the
shock added to saving where it landed hardest, but didn't overturn the North–South
pattern. Lead with the scatter, not the level bar, if you want to argue causation.

---

## Chart C — How much each quintile saves *(the structural inequality)*

**What it shows.** Median household saving rate by income quintile, from
Eurostat's experimental ICW statistics (`icw_sr_03`). The pattern is stark:
the **bottom quintile has a *negative* saving rate** — these households *dissave*,
spending more than they earn — while saving climbs steeply to the top quintile.
The bottom-quintile dissaving is severe in some members (Romania ≈ −62%,
Netherlands ≈ −29%, Greece ≈ −16%, Austria ≈ −15%).

**Intuition.** Saving is a luxury of having income to spare. A higher aggregate
saving rate is therefore mechanically a story about the **upper part of the
distribution**: when uncertainty rises, it is the households *with* slack —
higher-income, often older — who add to their buffers. The poorest can't save
more out of fear; if anything they cut consumption or borrow.

**Bearing on the hypothesis.** This is the structural backbone of leg (C): the
"precautionary buffer" the aggregate rate measures is built mostly by the top
quintiles. **Big caveat — timeliness:** ICW is *experimental* and compiled only
~every five years (latest reference ≈ 2020), so it shows the *structure*, not the
*post-2022 response*. Don't imply this chart captures the uncertainty shock.

## Chart C2 — Who fears most, right now *(the timely complement)*

**What it shows.** Expected unemployment 12 months ahead by income group (ECB
CES): the **lowest-income group expects ~13.2% vs ~9.4% for the highest**.
(Hardcoded in the script — refresh from the latest CES release before publishing.)

**Intuition + the twist.** Put C and C2 together: the lowest-income households
report the *most* fear (C2) yet have the *least* capacity to save (C). So the
same uncertainty produces a *bigger buffer at the top* and *forgone consumption
at the bottom* — the fear is widely shared, the cushioning is not. The CES also
confirms that more-uncertain households report higher realised saving, the
micro-level footprint of the precautionary motive.

**Bearing on the hypothesis.** C2 is the timely, behavioural evidence for leg (C)
that C (structural, ~2020) can't provide; together they make the equity angle
that lifts the piece above a pure macro chart.

---

## Charts D / E / F — How the distribution changes over time

There is **no single official, annual, EA-wide saving-rate-by-quintile series**, so
the script triangulates with three sources, each with a different trade-off:

- **Chart D — Eurostat ICW slope (`icw_sr_03`).** Official and EA-wide, but only
  three reference years (~2010/2015/2020). Read it as a *structural shift*, not an
  annual path: does the Q5–Q1 gap widen across snapshots? Watch whether the
  bottom quintile's dissaving deepens.
- **Chart E — OECD distributional accounts (annual, per country).** The only true
  *year-by-year* panel of saving by quintile, free via the OECD API. Per-country
  (DE/FR/IT/ES by default), aligned to national accounts, but it lags (~2021–22)
  and isn't a clean EA aggregate. This is the chart that can actually show the
  distribution moving each year and whether the top pulled away around 2022.
- **Chart F — ECB CES (2020→now).** Timely and by income group, but the saving
  variables are survey indicators, not a clean rate — and you must paste the exact
  series keys from the ECB Data Portal into `CES_KEYS` to enable it. Best for the
  *post-2022* window the other two miss.

**How to read change, beyond the raw lines.** Three summary measures make the
"distribution moved" claim precise, in rising order of punch:

1. **Q5 − Q1 gap (pp) over time** — one line; did saving inequality widen?
2. **Top-quintile share of total saving** — what fraction of *all* household
   saving the richest fifth does each year (combine quintile rates with income
   shares). The strongest "who actually saves" visual.
3. **Contribution decomposition** — split the change in the *aggregate* saving
   rate (Chart A) into how much each quintile added. This ties the distribution
   directly back to the headline rate.

**Bearing on the hypothesis.** If precaution is concentrated where there's slack,
the post-2022 rise in the aggregate rate should show up mostly in Q4–Q5 (visible
in E/F) and as a widening Q5–Q1 gap (D). That's the distributional fingerprint of
a precautionary, not broad-based, saving surge.

## Synthesis → the 400-word blog narrative

1. **Hook (Chart A):** Europe's saving rate is stuck near 15%, well above its
   pre-pandemic norm, and it climbed in lockstep with geopolitical uncertainty
   after 2022. Europe is saving out of fear.
2. **Where (Chart B):** the caution is uneven — heaviest where the energy/Russia
   shock bit hardest, though long-standing North–South saving habits still
   dominate the map.
3. **Who (Chart C):** the fear is most acute among lower-income households, but
   the *saving* is done by those who can afford it — so uncertainty quietly
   widens the gap between who worries and who can cushion themselves.
4. **So what:** high precautionary saving = weak consumption = a drag on the
   recovery and a complication for monetary policy. Rational for each household,
   costly in aggregate — a mild paradox of thrift.

## Caveats to keep honest
- **Correlation, not causation.** Interest rates and inflation co-move with
  uncertainty; the charts can't isolate the precautionary channel alone.
- **Gross vs net saving.** Eurostat's headline is the *gross* household saving
  rate; note this if you compare across sources.
- **Energy-exposure grouping is editorial.** The red/blue split is a
  simplification; the scatter's continuous x-axis (actual peak energy inflation)
  is the more rigorous version.
- **CES income figures are hardcoded** from a published release — verify against
  the latest CES before publishing.
- **Distributional data (ICW) is ~2020 and experimental.** It shows the structural
  saving inequality, not the post-2022 dynamics — pair it with the CES, don't
  conflate them.

## Sources
- Eurostat — household saving rate (`nasq_10_ki`, na_item SRG, from 1999Q1; `tec00131` annual by country); HICP (`prc_hicp_manr`); consumer survey (`ei_bsco_m`); saving rate by income quintile (`icw_sr_03`, experimental ICW).
- FRED — EU Economic Policy Uncertainty (`EUEPUINDXM`).
- Caldara & Iacoviello — Geopolitical Risk index (matteoiacoviello.com/gpr.htm).
- ECB — Economic Bulletin boxes on the household saving rate; Consumer Expectations Survey.
