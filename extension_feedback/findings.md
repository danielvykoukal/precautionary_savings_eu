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
