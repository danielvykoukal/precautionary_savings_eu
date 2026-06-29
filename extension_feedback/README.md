# extension_feedback — implementing the supervisor feedback

This folder answers the feedback on the savings analysis. The single unifying
idea: **stop treating "cash + deposits" as the only precautionary buffer.** Most
of the feedback follows from ranking household assets on a **liquidity / maturity
ladder** instead of the old cash-vs-rest binary, then layering risk-premia,
forward-looking and energy angles on top.

Each script is standalone, mirrors the style of `../extensions/` and
`../extension_follow_money/` (reuses shared helpers in `_common.py`, prints a
report, writes a `*.md` + CSVs to `./data` and PNGs to `./figures`), and pulls
only free / keyless data (Eurostat, FRED, ECB Data Portal).

**Write-up:** `documentation.tex` (→ `documentation.pdf`) is the full narrative —
the question, each result with its figure, and the synthesis of what it says about
the precautionary hypothesis. Compile with `pdflatex documentation.tex` (run twice
for the table of contents and references); regenerate after running
`risk_premia.py` so its figure fills in.

## How to run

```bash
# optional: refresh the project's ../data first (the folder ships with a copy)
cd .. && python3 01_collect_data.py && cd extension_feedback

pip install -r ../requirements.txt   # no new dependencies
bash run.sh                          # or run any script on its own
```

## Feedback → script

| Feedback point | Script | What it does | Extra data |
|---|---|---|---|
| each asset type; **divide by term**; "sold fast"; where/liquidity | `liquidity_ladder.py` | Reclassifies household assets into 4 liquidity/maturity tiers (T1 instant → T4 illiquid), on **stocks** (`nasa_10_f_bs`) and **flows** (`nasa_10_f_tr`). Headline: narrow **cash** share vs broad **sellable-fast** share. | Eurostat `nasa_10_f_bs` |
| **money supply**; divide by term | `money_supply.py` | Euro-area **M1 / M2−M1 / M3−M2** decomposed by term; growth vs the saving rate. The central-bank counterpart to the household ladder. | ECB Data Portal (BSI); FRED fallback |
| **risk premia** rise with geopolitical tension — *observable?* | `risk_premia.py` | Euro **HY credit spread**, **Italy–Germany (BTP–Bund)** sovereign spread, **VIX**, overlaid on the **GPR** index; co-movement + Feb-2022 event window. | FRED `BAMLHE00EHYIOAS`, `IRLTLT01ITM156N`, `IRLTLT01DEM156N`, `VIXCLS` |
| more **forward-looking** approach | `forward_looking.py` | A forward-looking caution composite (expected unemployment + saving intentions + VIX) tested for whether it **leads** the saving rate (lead-lag + 1-quarter-ahead regression vs a contemporaneous-GPR benchmark). | Eurostat `ei_bsco_m`, FRED `VIXCLS` |
| risk of **too little cash** vs rising **energy** prices | `energy_liquidity.py` | Instant-cash share of wealth vs the energy-price level; the regressive squeeze by income quintile (energy budget share vs saving capacity). | Eurostat energy HICP; reuses `build_tiers` |

## The argument in one paragraph

The presented analysis used a binary (cash+overnight = precautionary; bonds+term
deposits = yield-chasing) and concluded the post-2022 move was yield-chasing.
But bonds, listed shares and fund shares are **sellable in days**, so that binary
understates the precautionary buffer. On a proper liquidity ladder, a large share
of household wealth — well beyond cash — is liquid (`liquidity_ladder`), and the
money supply is itself tiered by term (`money_supply`). Geopolitical tension
**raises observable risk premia** (`risk_premia`), and **expected** caution can
**lead** realised saving (`forward_looking`). Yet "sellable fast" is not "safe to
spend now": selling into a stressed market crystallises losses, and the one truly
non-deferrable shock — the **energy bill** — hits hardest where the cash buffer is
thinnest, i.e. the lowest-income households (`energy_liquidity`).

## Caveats

- **Eurostat F5 sub-instruments** (F511/F512/F519/F521/F522) are not always
  published. The classifier auto-detects what exists and falls back
  conservatively (an un-splittable equity/funds block is treated as illiquid), so
  the broad-liquid share is a **lower bound** — we never overstate liquidity. The
  chosen mapping is printed and saved.
- **Net flows** can push shares past 100% / negative; the **stocks** view is the
  robust basis for the "standing liquidity" claim.
- **VSTOXX** and 5y5y inflation swaps are not cleanly keyless — VIX is the free
  proxy (and tracks VSTOXX closely).
- **Money-supply keys**: the script tries the ECB Data Portal first; if a key does
  not resolve it falls back to FRED and (if it only gets an index) reports growth
  rather than the term decomposition.
- The **energy budget share by income** in `energy_liquidity.py` is *illustrative*
  (stylised from HBS/ECB) — verify against the latest HBS before publishing, as
  with the project's hardcoded CES figures.
- All series are pulled **live and revised** by providers — regenerate before
  citing.
