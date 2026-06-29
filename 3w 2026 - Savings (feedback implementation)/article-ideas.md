# Blog Article Ideas — Working Notes

**Format target:** ~400 words, a few charts. Basically a blog post → pick ONE sharp, visual story per idea. No econometrics; the charts carry the argument, the text interprets.

**Preferred data:** Eurostat + FRED (both free, no Moody's needed). Note on access below.

---

## Idea 1 — Precautionary saving in Europe (RECOMMENDED)

### The hook
The euro-area household saving rate is stuck near 15% — well above the ~12–13% pre-pandemic norm — even though pandemic forced-saving and the income/wealth shocks have unwound. The ECB itself links the persistence to **precautionary motives under elevated uncertainty**. A January 2026 ECB box finds that "uncertain households report lower realised consumption and higher realised savings, in line with precautionary saving theory." That's the spine: *Europe is saving out of fear.*

### Recent numbers (for the text + charts)
- Euro-area saving rate: 15.7% (Q3 2024) → 15.4% (Q2 2025) → ~14.4% (Q4 2025). Elevated and only slowly easing.
- EU-27 ~13.7% (Q4 2024).
- Cross-country spread, 2024 gross household saving rate: **Germany ~20%** (highest major economy), France high (~18–20%), vs **Spain 12.7%**, **Italy 12.0%** — both below EU average but well above their own pre-pandemic levels.

### The two angles you liked, combined into one narrative
1. **Cross-country heterogeneity (headline chart).** Did countries more exposed to Russia/energy (Germany, Baltics, CEE) save more than insulated ones? The German ~20% rate vs. southern ~12% is the visual anchor. Frame as: caution rose most where the war/energy shock bit hardest.
2. **Distribution / equity twist.** Precautionary saving concentrates among those who *can* save — higher-income, older households. The CES shows lower-income households expect far higher unemployment (≈13.2% vs ≈9.4% for the top group), yet save least because budgets are tight. So "fear" shows up as forgone consumption at the bottom and a savings buffer at the top.

### Suggested charts (2–3)
- **Chart A (hook):** Euro-area saving rate vs. Geopolitical Risk index (or EU EPU), 2019–2025 — fear tracks saving.
- **Chart B (headline):** Saving-rate change since 2021 by country, ordered/colored by Russia–energy exposure.
- **Chart C (kicker, optional):** Saving behaviour or unemployment expectations by income group (ECB CES).

### Data — exactly where
- **Eurostat household saving rate:** `teina500` (euro-area/EU quarterly, seasonally adj.) and `tec00131` / `nasa_10_ki` (annual, by country). Databrowser: ec.europa.eu/eurostat/databrowser/view/teina500
- **Eurostat consumer confidence / unemployment expectations:** `ei_bsco_m` (Business & Consumer Survey).
- **FRED Europe EPU:** series `EUEPUINDXM` (monthly, from 1987). US comparison: `PSAVERT`.
- **Geopolitical Risk (GPR) index:** Caldara & Iacoviello, free download at matteoiacoviello.com/gpr.htm — spikes cleanly at the Feb-2022 invasion and Middle-East escalations.
- **Distribution:** ECB Consumer Expectations Survey (CES) — published aggregates by income group; **no raw microdata needed** for a blog.

### So what (the closing line)
High precautionary saving = weak consumption = a drag on the recovery and a headwind for monetary transmission. Caution is rational for households but costly in aggregate (a mild paradox-of-thrift).

### Why this is the safer pick
Clean question, fully observable target variable, all regressors/series free in Eurostat + FRED, and a live ECB literature to anchor and extend. Perfect fit for a short, chart-led post.

---

## Idea 2 — AI investment, EU vs US

### Your data concern, resolved
What's hidden is **individual private-company financials** (you can't get Anthropic's or OpenAI's actual books). But you don't need those for a region comparison — **aggregate AI investment by country/region is public and citable**:
- **Stanford AI Index** — private/VC AI investment by country, generative-AI breakouts.
- **OECD.AI** — VC into AI by country (live dashboards).
- **Dealroom / Atomico "State of European Tech"** — European VC detail.

So the country-level investment story is fully doable; per-company secrecy doesn't block it.

### The numbers that make the story
- **US private AI investment: $109.1B (2024)** — ~12× China, ~24× the UK.
- **AI VC, 2023:** ~$68B (US) vs ~$8B (EU). Gap widening with generative AI.
- **Notable AI models, 2024:** US 40, China 15, **Europe 3.**
- **Adoption (Eurostat `isoc_eb_ai`):** EU enterprises using AI 8.0% (2023) → 13.5% (2024) → ~20% (2025). Leaders: **Denmark 27.6%, Sweden 25.1%, Belgium 24.7%.** Laggards: **Romania 3.1%, Poland 5.9%, Bulgaria 6.5%.**
- **Intangible investment gap:** EU spends <1% of gross fixed capital formation on "other IP products" vs ~5% in the US.

### The original angle: adopt vs. fund
Everyone quotes the VC gap. Fewer make the sharper point: **Europe consumes US-made AI without funding it.** Is the EU becoming an AI *consumer*, not *producer*? Pair the investment gap with the adoption gap to show the split — and the within-EU divide (Nordics vs. South/East; large firms vs. SMEs).

### Suggested charts (2)
- **Chart A:** US vs EU vs UK private AI investment, 2019–2024 (Stanford/OECD).
- **Chart B:** AI adoption by EU country, 2024 (Eurostat `isoc_eb_ai`) — Nordics on top, CEE bottom.

### Data — where
- Stanford HAI AI Index (hai.stanford.edu/ai-index), OECD.AI (oecd.ai), Dealroom.
- Eurostat `isoc_eb_ai` (AI by enterprise size class). Intangibles: Eurostat `nama_10_an6` / national accounts GFCF by asset; FRED for US BEA software & IP investment.

### Feasibility note
Strong IF framed as **"adoption + investment gap."** The Eurostat adoption survey is the cleanest free, official, cross-country dataset. The headline VC figures require Stanford/OECD/Dealroom (free to cite, just not Eurostat/FRED).

---

## A bridging idea (if you want something more novel)
One post linking both: **uncertainty → precautionary saving / low risk appetite → under-investment in frontier (digital/AI) capital.** European caution helps explain why the EU under-funds risky tech vs. the US. Unifies both topics; more original than either alone — but harder to nail in 400 words.

---

## Data-access status (what I tried)
- **Confirmed public + free:** all series above exist at the listed Eurostat datasets, FRED series IDs, and the GPR download.
- **Could not auto-pull raw series in this environment:** the sandbox can't reach `fred.stlouisfed.org` or `ec.europa.eu` (not on its network allowlist), and the fetch tool won't render their JSON/CSV payloads. Pulling the actual time series needs either a quick manual download or running a small script on your own machine (Eurostat API needs no key; FRED CSV: `fred.stlouisfed.org/graph/fredgraph.csv?id=EUEPUINDXM`).
- **Figures above** come from Eurostat news releases, ECB bulletin boxes, and the Stanford AI Index (sources listed in chat).

## Recommendation
Lead with **Idea 1**. It's the cleanest 400-word, chart-led story, the data is immediately at hand and free, and the "who saves out of fear" framing (cross-country + distribution) is both timely and underexplored at blog length.
