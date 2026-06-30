# Savings Series Catalog

Verified macro time series for the *Precautionary Saving in Europe* project, organised by the liquidity/maturity ladder (T1 instant → T4 illiquid).

For ECB series, the API CSV pull is:
`https://data-api.ecb.europa.eu/service/data/<DATASET>/<KEY-without-dataset-prefix>?format=csvdata`

---

## T1 — Instant / overnight

### Overnight (current-account) deposits — euro-area households
- **Source:** ECB, Balance Sheet Items (BSI)
- **Series key:** `BSI.M.U2.N.A.L21.A.1.U2.2250.Z01.E`
- **Link:** https://data.ecb.europa.eu/data/datasets/BSI/BSI.M.U2.N.A.L21.A.1.U2.2250.Z01.E
- **API (CSV):** `https://data-api.ecb.europa.eu/service/data/BSI/M.U2.N.A.L21.A.1.U2.2250.Z01.E?format=csvdata`
- **Description:** Overnight deposits placed by euro-area households (S.14+S.15) at MFIs excl. Eurosystem. Monthly stocks, all currencies, EUR millions, not seasonally adjusted. Maps to current/sight accounts (withdrawable on demand). Coverage: monthly from Sep 1997.
- **Verified:** 2026-06-29 — Apr 2026 = €5,531,171 M; May 2026 = €5,561,874 M (provisional).
- **Counterpart-sector variants** (swap the counterpart field): `2240` = non-financial corporations; `2300` = total money-holding sector (non-MFIs excl. central gov, "all customers" — see next entry).

### Sight & overnight deposits — all euro-area customers (total money-holding sector)
- **Source:** ECB, Balance Sheet Items (BSI)
- **Series key:** `BSI.M.U2.N.A.L21.A.1.U2.2300.Z01.E`
- **Link:** https://data.ecb.europa.eu/data/datasets/BSI/BSI.M.U2.N.A.L21.A.1.U2.2300.Z01.E
- **API (CSV):** `https://data-api.ecb.europa.eu/service/data/BSI/M.U2.N.A.L21.A.1.U2.2300.Z01.E?format=csvdata`
- **Description:** Overnight (sight) deposits placed by euro-area non-MFIs excl. central government — the M1 money-holding sector, i.e. all bank customers (households + NFCs + non-MFI financials + other general gov). Monthly stocks, all currencies, EUR millions, NSA. Same instrument (L21) as the household entry above; differs only by counterpart sector.
- **Verified:** 2026-06-29 — May 2026 = €9,473,417 M (households €5.56 tn + NFCs €2.61 tn + financials/other).
- **Counterpart-sector variants** (swap the counterpart field): `2250` households; `2240` NFCs; `2200` non-MFIs excl. general gov; `2210` non-MFI financials; `2120` other general gov.

---

*Add new entries under the matching ladder tier.*
