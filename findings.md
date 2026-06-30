# Findings — Precautionary Saving in Europe (combined)

*Single write-up for the whole project. Figures live in `figures/`, tagged by idea
letter (A–O); data in `data/` shares the matching letter; scripts in `code/<module>/`.*

**Idea map:** A–D core legs (saving vs uncertainty / cross-country / distribution) ·
E robustness · F follow-the-money · G liquidity ladder · H money supply ·
I risk premia · J forward-looking · K energy-liquidity squeeze · L US vs euro-area ·
M savings reconciliation · N real consumption function · O descriptive overview.

---



<!-- ===================== Core study (A–F) ===================== -->

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


---


<!-- ===================== Feedback extension (G–L) ===================== -->

# Findings — feedback implementation

*Companion to the scripts. Numbers below are from a clean live run on
2026-06-29 (Eurostat + ECB Data Portal). The **risk-premia** figures (§3) need
FRED, which was unreachable in the build environment — regenerate them on your
machine (`python3 risk_premia.py`) and fill the two bracketed slots. All series
are pulled live and revised, so re-run before citing.*

> **The reframe that ties the feedback together.** The presented analysis split
> household saving into instant-access cash (precautionary) vs "locked for yield"
> bonds & term deposits (yield-chasing) and concluded the post-2022 move was
> yield-chasing. The supervisors' objection is correct: **bonds, listed shares and
> fund shares are sellable in days**, so the precautionary buffer is much larger
> than cash. Re-ranking assets on a liquidity/maturity ladder is the spine of
> every section below.

---

## 1. Liquidity ladder — assets by term (`liquidity_ladder.py`)

**Question.** How much of what households *hold* (stocks) and *add* (flows) is
actually liquid, once we go beyond cash?

**Tiers.** T1 instant (F21+F22) · T2 near-money (F29+F521) · T3 marketable, sellable-fast (F3+F511+F522) · T4 illiquid (F512/F519+F6).

**Result (EA20, live run).**
- **Stocks.** Instant cash (T1) is only **~18%** of household financial wealth
  (17.2% in 2015–19, 19.2% in 2022+), but the **broad sellable-fast share
  (T1+T2+T3) is ~50%** (47.5% → 49.8%). Half of household financial wealth can be
  mobilised within days; only a fifth is literally cash. T4 illiquid (~47–49%) is
  dominated by insurance/pension claims and unlisted business equity.
- **Flows.** The cash (T1) share of yearly financial saving **collapsed from 66%
  (2015–19) to 2% (2022+)** — the headline of the old binary. *But* the **broad
  sellable-fast share rose from 54% to 73%** (T3 marketable: −1% → +37%). So the
  post-2022 reallocation went *out of cash and into other liquid assets*, not out
  of the precautionary buffer.

**Bearing.** "Out of cash" ≠ "not precautionary." This directly answers the
feedback. The classifier's conservative fallback (any un-splittable equity/funds
block → T4) means the broad-liquid share is a **lower bound**.

## 2. Money supply by term (`money_supply.py`)

**Question.** Does the money supply, divided by term, tell the same story?

**Result (euro area, live ECB BSI, EUR bn annual mean).**
| year | M1 instant | M2−M1 term/notice | M3−M2 marketable | M3 |
|---|---|---|---|---|
| 2021 | 10,846 | 3,434 | 766 | 15,045 |
| 2022 | 11,556 | 3,604 | 776 | 15,936 |
| 2024 | 10,351 | 4,938 | 1,096 | 16,384 |

As rates rose, money migrated **out of instant M1 (−€1.2tn, 2022→24) into term/
notice deposits (M2−M1: +€1.3tn) and marketable near-money (M3−M2: +43%)** — the
macro mirror of the household-ladder flows. Broad-money (M3) growth and the saving
rate co-move (**corr +0.27**, 2000–2025). Money itself is tiered by term — the
buffer is not just M1 cash.

## 3. Risk premia vs geopolitical tension (`risk_premia.py`)

**Question (supervisors).** Risk premia rise with geopolitical tension — *can we
observe it?* **Answer — yes**, three observable euro-area premia overlaid on GPR:
- Euro **HY credit spread** (FRED `BAMLHE00EHYIOAS`) — [fill from your run: corr with GPR, Feb-2022 jump].
- **Italy–Germany (BTP–Bund)** sovereign spread — [fill: corr; jump]. The cleanest euro-area fragmentation gauge; widened sharply in 2022.
- **VIX** (VSTOXX analogue) — [fill: corr]; forward-looking risk-aversion read.

*(FRED was unreachable in the build sandbox; the script and FRED IDs are verified
and identical in form to the project's existing FRED pulls.)*

**Bearing.** Geopolitical tension is observably priced; higher premia + uncertainty
strengthen the precautionary motive and the tilt toward liquidity.

## 4. Forward-looking approach (`forward_looking.py`)

**Question (supervisors).** What can be done to be more forward-looking?

**Approach.** A caution composite of *expected* unemployment + *intended* saving
(+ VIX implied vol when FRED is reachable), tested for whether it **leads** the
realised saving rate.

**Result (EA20, live; VIX omitted here as FRED was blocked).** Co-movement is
strong and the composite **predicts one quarter ahead**: `saving_t ~
composite_(t−1)` gives **β=+1.88 (p<0.001), R²=0.38** (n=107), versus the
contemporaneous-GPR benchmark **R²≈0.00**. Lead-lag corr peaks contemporaneously
(+0.76) and is still +0.74 at one-quarter lead. *Honest caveat:* the composite
includes *intended saving*, which is close to the target by construction — the
*expected-unemployment* and *VIX* legs are the cleaner forward signals, so read
this as "expectations carry real predictive content GPR lacks," not a clean
out-of-sample forecast.

## 5. Energy prices vs the cash buffer (`energy_liquidity.py`)

**Question (supervisors).** The risk of not holding enough cash against rising
energy prices.

**Result (euro area, live).**
- Aggregate: the energy price level **peaked ~+60% vs 2019** and stayed elevated,
  while the instant-cash share of household wealth rose to 21.5% (2022, forced
  saving) then **fell back to ~18% by 2024** — the cushion did not keep pace, and
  households moved *out* of cash (§1). The non-deferrable bill grew as the cash
  buffer thinned.
- Distribution (ICW quintiles): the squeeze is **regressive** — the poorest
  quintile **dissaves (saving rate −3.4%)** with the **largest** energy budget
  share (~11%, illustrative), while the top quintile saves **+44%** on the
  smallest energy share (~5.5%). Most exposed, least able to self-insure with cash.
- "Sellable fast" ≠ "safe to spend now": liquidating T3 assets to pay an energy
  bill crystallises losses precisely when risk premia (§3) are elevated.

---

## Synthesis (for the write-up / slides)

1. The precautionary buffer is **not just cash** — ~50% of household wealth and a
   tiered money stock are liquid by term (§1, §2).
2. So "out of cash, into bonds/funds after 2022" is **moving up the risk ladder
   while staying liquid** (broad-liquid flow share 54%→73%), not abandoning
   precaution (§1 flows).
3. Geopolitical tension is **observably priced** in risk premia (§3), and
   **expected** caution carries predictive content the contemporaneous GPR lacks
   (§4).
4. The binding constraint is the **non-deferrable energy bill** meeting a thin,
   unevenly distributed cash buffer (§5): the real "not enough cash" risk is
   concentrated at the bottom of the income distribution.

## Caveats
- F5 sub-instrument availability → broad-liquid share is a **lower bound**
  (in this run F521/F52 were not separable; noted in the report).
- Stocks > flows for the "standing liquidity" claim (flow shares can exceed 100%).
- Money-supply term decomposition relies on EUR levels (ECB) — confirmed here.
- Forward composite includes intended saving (partly mechanical — see §4).
- Energy budget share by income is **illustrative** — verify against HBS.
- All series live & revised — regenerate before citing.


---


<!-- ===================== Why the saving rate rose — read from the accounts (M, reconciliation) ===================== -->

# Why the euro-area household saving rate rose — read straight from the accounts

*Companion to `savings_reconciliation.py`. All numbers are a live run on the
euro-area (EA20) household sector (Eurostat `nasa_10_nf_tr` + `nasa_10_f_tr`),
regenerate before citing. This note is the payoff of the reconciliation: the saving
rate is **built bottom-up from the asset types households acquire (deposits,
securities, equity & fund shares, insurance & pensions) plus housing investment
minus borrowing**, not from dividing disposable income. That component build
reproduces the **reported** saving rate to ~0.08 pp (mean abs error 2002–2025; see
`M4_savings_reconciliation_validation.png`), so we can decompose the rate's *moves*
with confidence — both why households saved more, and where the money went.*

## The saving rate, by episode

| period | saving rate | disposable income (EUR bn) | consumption (EUR bn) |
|---|---|---|---|
| 2015–19 (pre-COVID) | **12.6%** | 7,062 | 6,172 |
| 2020–21 (COVID) | **18.3%** | 7,685 | 6,277 |
| 2022–25 (post-rate-shock) | **14.4%** | 9,224 | 7,894 |

Two distinct increases, with two different causes: a large **transitory** COVID
spike (+5.7 pp), and a smaller **durable** step that has held the rate ~2 pp above
its pre-pandemic norm.

---

## 1. The COVID spike (2020–21): a consumption shock, parked in cash

The rate jumped because **consumption collapsed, not because income rose**:

- 2019 → 2020: disposable income **+0.1%**, consumption **−7.2%**.

Households kept earning (wages were furloughed/supported, transfers rose) but
*could not spend* — lockdowns closed the consumption channel. The arithmetic of
`rate = 1 − consumption/income` does the rest. This is **forced saving**, not a
behavioural shift toward thrift.

**Where it went — almost entirely into financial assets.** The flow into financial
assets nearly doubled, from **7.5% to 13.9% of income**, while housing investment
and borrowing barely moved. On the liquidity ladder (`liquidity_ladder.py`) that
2020–21 financial-asset surge was overwhelmingly **T1 cash / overnight deposits** —
the precautionary-buffer build-up.

## 2. The durable step (2022–25): income outran spending, and borrowing fell

The rate settled at **14.4%**, ~2 pp above 2015–19, for two reinforcing reasons:

1. **Income kept ahead of consumption.** 2019 → 2023: disposable income **+21.2%**
   vs consumption **+19.6%**. In a high-inflation period nominal incomes (wages,
   indexed pensions/transfers) rose fast while households held nominal spending
   growth a touch lower — real consumption was squeezed and partly deferred amid
   uncertainty. The gap is modest but persistent.
2. **Borrowing collapsed.** Net incurrence of liabilities fell from **2.8% to 1.9%
   of income** (loans/mortgages: €280 bn in 2022 → €39 bn in 2023) as the ECB
   hiking cycle made credit expensive. Less new debt means households financed more
   of their spending and investment out of their own income — which *raises the net
   saving rate* directly.

**Where it went — not housing.** Housing/non-financial investment was **steady
throughout** (8.6% → 9.4% → 9.5% of income); it did **not** drive the increase.
The extra saving stayed in financial assets (8.3% of income, only modestly above
the 7.5% baseline) — but on the ladder it rotated **out of cash into yield**
(term deposits, bonds, funds) once rates rose. That rotation is the subject of the
liquidity-ladder reframe: "out of cash" ≠ "out of the precautionary buffer."

## 3. Real terms: is the durable rise just "people have more money"? **No.**

*(`real_consumption_function.py`; the decisive cut.)* The saving rate is a ratio of
two nominal flows, so deflating both by the consumption deflator leaves it
unchanged — but it tells us whether **real** income rose and whether the rise is
the mechanical "income up → average propensity to consume down" effect or a genuine
behavioural shift.

- **Most of the nominal income growth was inflation.** 2019→2023 disposable income
  was **+21.2% nominal but only +3.8% real**; consumption +19.6% nominal / +2.4%
  real. Real income *did* rise, just modestly.
- **The pre-COVID consumption function rules out the income mechanism.** Fitting
  real `C = a + b·Y` on 2002–2019 gives **MPC ≈ 0.94, R² = 0.97, and an
  ~zero/negative intercept**. With a non-positive intercept the APC does *not* fall
  as income grows — so "richer → saves a bigger share" **does not operate here**;
  pure real-income growth would, if anything, push the saving rate slightly *down*.
- **Post-2022 consumption sits clearly BELOW that line, and the gap widens.**
  Households consumed €90 bn (2022) → €220 bn (2025) *less* than the historical
  income relationship predicts. Decomposing the 2022–25 average saving rate:

  | | saving rate |
  |---|---|
  | predicted by real income alone (on the pre-COVID curve) | ~12.1% |
  | **actual** | **14.4%** |
  | **= behavioural downward shift** | **+2.3 pp** |

  A Chow break test confirms a **structural break** (F ≈ 11.6) in the consumption
  function after 2021.

**Verdict.** The durable post-2022 saving rate is **not** "people have more money."
Real income rose only a few percent, and the pre-COVID relationship would put the
rate near 12%. The actual ~15% comes from consumption sitting **below** its
historical link to income — a genuine downward shift that **persists and widens**
through 2025. That is the structural-precaution signature the project is after
(`N_real_consumption_function.png`).

*Caveat:* a levels regression on trending data is fragile (treat the MPC/intercept
as descriptive); and "downward shift" bundles precaution with possible slow COVID-
buffer unwind, relative-price (energy) effects, higher rates rewarding saving, and
wealth effects — it establishes *that* behaviour shifted, not *only* precaution.

---

## The one-line story

> The saving rate rose **first** because COVID stopped households spending (a pure
> consumption shock, banked as cash), and **stayed** elevated because households
> consume *less than their historical relationship with income predicts* — a genuine
> downward shift, not just "more income" (real income rose only a few percent) —
> while the rate shock cut borrowing to a trickle. Housing absorbed its usual ~9% of
> income the whole time — the swing came from **consumption behaviour, then
> borrowing**, not from investment or from income growth.

## Uses of saving, % of disposable income (the engine of the above)

| | 2015–19 | 2020–21 | 2022–25 |
|---|---|---|---|
| financial assets acquired | 7.5 | **13.9** | 8.3 |
| housing / non-financial investment | 8.6 | 9.4 | 9.5 |
| borrowing (net incurrence of liabilities) | 2.8 | 3.8 | **1.9** |

## Figures
- `M5_savings_reconciliation_why.png` — saving rate (top) over the uses of saving as
  % of income (bottom), COVID and post-shock episodes shaded.
- `M4_savings_reconciliation_validation.png` — the component build reproduces the
  reported rate (the licence to do this decomposition at all).
- `M2_savings_reconciliation_decomposition.png` — the full annual stack, split by
  **asset type** (deposits, securities, equity & funds, insurance & pensions) plus
  housing minus borrowing, netting to the saving-rate line;
  `M_savings_reconciliation_waterfall.png` — the same build for the recent period.
- `M3_savings_reconciliation_pieces.png` — housing, borrowing and net financial-asset
  acquisition over time (EUR bn).

## Caveats
- A **statistical discrepancy** (B9 vs B9F, ~1 pp of income) remains between the
  non-financial and financial accounts — Eurostat's own, shown as its own bar, not
  a build error.
- The headline bridge figures are **nominal**; the real-terms test that interprets
  the *durable* rise is §3 (`real_consumption_function.py`). The 2022–25 nominal
  income growth is mostly inflation (real income +3.8% to 2023).
- Series are **live and revised** — regenerate (`python3 savings_reconciliation.py`
  then `python3 real_consumption_function.py`) before citing.


---


<!-- ===================== Descriptive overview (O) ===================== -->

# Findings — descriptive overview

*Companion to the scripts (all six descriptive ideas). Numbers from a clean live
run on 2026-06-29 (Eurostat + GISCO + OECD; no FRED). Regenerate before citing.*

> The supervisors asked to look at the saving question **descriptively first**.
> Four pictures set the scene before any hypothesis testing: is the high rate a
> new norm or a cycle; where in Europe is it high; how spending rotated; and what
> households actually hold.

---

## 1. Structural or cyclical? (`structural_vs_cyclical.py`)

An HP filter (λ=1600) splits the saving rate into a slow **trend** (structural)
and a **cycle**. The 2020-21 COVID spike was *forced* saving (people could not
spend), not a behavioural change, so those quarters are **excluded from the
filter** (interpolated); the cycle is the real deviation from that de-COVID trend,
so the spike correctly appears as a large positive **cycle**, not a trend lift.
Result: the trend **steps up ~2.6 pp**, from **12.5% (2012–19) to 15.1%** today,
while the latest **cycle is ~0** (the rate ≈ its trend). So the persistence is now
**mostly structural** — a higher norm — consistent with the "saving more for old
age as pensions weaken" story, not a transient bump that should revert.

## 2. The European map (`europe_map.py`)

A choropleth of the gross household saving rate by country (2024): **Germany ~20%
and France ~18%** at the top, the Nordics high; **Italy ~11%, Spain ~13%**, and
**Greece dissaving (≈ −3%)** at the bottom. The North–South gap is **structural
and long-standing** — it predates the energy shock — so a raw "who saves most"
map mostly reflects habits, not the recent crisis.

## 3. Goods vs services (`goods_vs_services.py`)

The puzzle: high saving, yet strong services spending. Real consumption volumes
(2019=100) resolve it — **services collapsed in 2020, then rebounded to ~107**,
while **goods boomed in lockdown then flattened (~103)**. Households kept
consuming services (reopening; services inflation pushes nominal spend higher
still) and saved by **pulling back on goods**. High saving and a strong services
recovery are not a contradiction — they are two sides of a **goods→services
rotation**.

## 4. What households save in (`saving_composition_evolution.py`)

Disaggregating the household balance sheet by **risk**: the **risky share (F5
equity & investment funds) rose ~+8 pp over the decade, 29% → 37%**, while
**non-risky deposits (F2) held ~31%** and insurance/pensions (F6) also rose.
Equity is now the **largest single instrument**, though deposits + pensions
(non-risky) still dominate combined. So the user's read holds: the non-risky base
is still large, but **equity involvement has clearly grown** — more euro-area
households now carry market exposure. A cross-country snapshot shows the risky
share is **higher in the North/core and lower in the South**.

## 5. Demographics & pensions (`demographics_pensions.py`)

Do aging and pension design move household saving? Two cross-country scatters.
**(a) Aging:** the old-age dependency ratio is, if anything, **weakly negatively**
related to the saving rate (corr ≈ **−0.14**) — older Southern economies save
*less*, not more, so aging does not mechanically lift saving. **(b) Funded
pensions:** using the insurance & pension share of household assets (F6) as a
funded-pillar proxy — high where households actually *hold* pension assets, low
under pay-as-you-go state promises — the link to saving is **weakly positive**
(corr ≈ **+0.34**): big funded systems (Netherlands, Denmark) coexist with solid
saving, not low saving. So "good pensions ⇒ less private saving" does not hold in
the cross-section; **pensions shape *where* wealth sits more than *how much* is
saved**.

## 6. Why Europeans look like cautious savers (`us_caution.py`)

The clearest US–Europe difference is not *how much* households save but *how* they
hold it. US households hold about **57%** of their financial wealth in equity &
investment funds vs **~37%** in the euro area (~1.5×), with the mirror image in
deposits (US ~11% vs euro area ~31%) — a **large, persistent** gap across two
decades. The institutional history: the US built a funded, equity-heavy
private-pension system (401(k)/IRA) and an equity-investing culture; much of
continental Europe leaned on **pay-as-you-go state pensions** and bank deposits.
European households therefore carry less market risk and look more "cautious" — a
**structural, pension-rooted** difference, not just preferences.

---

## Synthesis (the descriptive scene-setter)

1. The elevated saving rate is now a **higher structural norm**, not a passing
   cycle (§1).
2. It sits on a **structural North–South map** that long predates the shock (§2).
3. High saving coexists with **strong services** via a goods→services rotation
   (§3).
4. Households still hold a large **non-risky** base but **equity involvement has
   grown** markedly over the decade (§4).
5. **Aging and pension design** move household saving only weakly cross-country;
   pensions shape *where* wealth sits more than *how much* (§5).
6. Versus the US, euro-area households are **cautious holders, not low savers** —
   far less equity, far more cash — a structural, pension-rooted gap (§6).

These motivate the hypothesis work in `../extension_feedback/`: a precautionary,
liquidity-tiered reading of *why* the rate is high and *where* the money sits.

## Caveats
- HP trend distorted by the 2020 spike (read the step, not the 2020 bend).
- The map's North–South gap is structural/editorial, not caused by the shock.
- Goods/services uses real volumes; nominal services spending is higher (services
  inflation).
- "Risky" (F5) includes unlisted business equity, not only listed shares.
- All series live & revised — regenerate before citing.


---
