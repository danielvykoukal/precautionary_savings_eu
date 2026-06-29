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
and a **cycle**. Result: the trend **stepped up ~1.7 pp**, from **12.9% (2012–19)
to 14.6%** today, while the latest **cycle is ~0** (the rate ≈ its trend). The
2020 lockdown spike was almost entirely cyclical and has unwound. So the
persistence is now **mostly structural** — a higher norm — consistent with the
"saving more for old age as pensions weaken" story, not a transient bump that
should revert. (Caveat: the 2020 spike distorts the HP trend around 2020; read
the pre-2020 vs latest step as the structural signal.)

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
