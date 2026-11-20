# Rates, Risk & Returns
MIS20080 Introduction to Programming, group dashboard project

## Panel 1: The global shock (Ciara Feeney)

**Question:** where is each economy on inflation and growth, and how did that change year by year?

An animated Gapminder-style bubble chart (inflation vs GDP growth or unemployment, bubble size = GDP,
colour = region), with a spinning-globe view of inflation by country. Pick a year to see what happened,
summary metrics compared with the year before, and the rank correlation between inflation and
growth (or unemployment) with its p-value.

**Controls:** view (bubbles / globe), Y-axis, regions, highlighted country (Ireland by default),
play / year slider, "Explain a year".

**Files:** `panel_a/model_a.py` (panel), `data.py` (shared loaders), `style.py` (shared chart style).

### Data source

| Provider | Indicators | Access | Frequency | Licence |
| --- | --- | --- | --- | --- |
| [World Bank World Development Indicators](https://data.worldbank.org) | Inflation `FP.CPI.TOTL.ZG`, GDP growth `NY.GDP.MKTP.KD.ZG`, unemployment `SL.UEM.TOTL.ZS`, GDP `NY.GDP.MKTP.CD` | Public API via `wbgapi`, no key needed | Annual | CC BY 4.0 |

**Reliability:** downloads are cached for a day. If the World Bank doesn't reply within 20 seconds,
or returns incomplete data, the panel uses the saved snapshot in `data/fallback/world_bank.csv`
and says so on screen. Refresh the snapshot with `python data.py`.
