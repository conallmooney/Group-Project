# Rates, Risk & Returns
MIS20080 Introduction to Programming, group dashboard project.

An interactive dashboard showing how the 2021–23 inflation shock and the rise in interest rates that followed affected economies, investments and what a saver's money could grow to.

## The four panels

| # | Panel | Chart | Owner |
|---|-------|-------|-------|
| 1 | The global shock | Animated bubble chart and globe | Ciara Feeney |
| 2 | Who wins when rates move? | Bar chart with a rate-shock slider | Eoin Cunningham |
| 3 | Build the best portfolio | Efficient frontier | Conall Mooney |
| 4 | What could it become? | Monte Carlo fan chart | Hannah McElligott |

## How to install and run

Install Python and Git before starting. Python 3.14 has been used during development; compatibility with other Python versions has not been fully verified.

An internet connection is needed to install the dependencies. Once installed, the dashboard can use the supplied data snapshots when live downloads are unavailable.

### 1. Get the project

Clone the repository and enter its main folder:

```bash
git clone https://github.com/conallmooney/Group-Project.git
cd Group-Project
```

If you already have the project, open its main folder in VS Code instead.

### 2. Create a virtual environment

This keeps the project's packages separate from other Python projects.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows Command Prompt:**

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Install the dependencies

With the virtual environment activated:

```bash
python -m pip install -r requirements.txt
```

The package versions are specified in `requirements.txt`.

### 4. Start the dashboard

Run this from the main project folder, which contains `app.py`:

```bash
python -m streamlit run app.py
```

Open the Local URL printed in the terminal, usually `http://localhost:8501`.

Leave the terminal running while using the dashboard. To stop the app, click inside that terminal and press **Control + C**.

## Using the dashboard

The **Overview** tab summarises the four panels. Open an individual panel's tab for its full charts, controls and explanations.

The shared economic scenario supplies the rate shock, inflation and risk-free rate used by the relevant models. Panel 1 shows historical observations and does not change with the scenario.

Panel 2 supplies asset sensitivities to Panel 3. Panel 3 publishes its optimised portfolio for use in Panel 4. In Panel 4, select **My Panel 3 portfolio** to use that result.

For detailed instructions, see the [user manual](docs/user_manual.md).

## Data access and offline use

The current data loaders do not require API keys:

- **World Bank:** public API access through `wbgapi`.
- **Yahoo Finance:** adjusted ETF prices through `yfinance`.
- **FRED:** public CSV download of the US 10-year Treasury yield (`DGS10`).

If a live download fails, the loaders attempt to use the supplied snapshots:

| Saved file | Contents |
|---|---|
| `data/fallback/world_bank.csv` | Country-level economic indicators |
| `data/fallback/etf_prices.csv` | Adjusted ETF closing prices |
| `data/fallback/treasury_yields.csv` | US 10-year Treasury yields |

The dashboard displays a notice when saved data is used. Offline results reflect the dates covered by those snapshots.

Keep these files in the project folder structure when copying or submitting the project.

## How to run the tests

From the main project folder, with the virtual environment activated:

```bash
python -m pytest -v
```

The tests check selected data-processing and financial calculations. They complement manual checks of the dashboard controls and panel connections.

See the [testing log](docs/testing_log.md) for recorded checks, problems and fixes.

## Panel 1: The global shock (Ciara Feeney)

**Question:** where is each economy on inflation and growth, and how did that change year by year?

An animated Gapminder-style bubble chart (inflation vs GDP growth or unemployment, bubble size = GDP, colour = region), with a rotatable globe view of inflation by country. Pick a year to see what happened, summary metrics compared with the year before (median inflation, share of countries above 5%, number of economies shrinking), and the rank correlation between inflation and growth (or unemployment) with its p-value.

**Controls:** view (bubbles / globe), Y-axis, regions, highlighted country (Ireland by default), play / year slider, "Explain a year".

**Files:** `panel_a/model_a.py` (panel), `data.py` (shared loaders), `style.py` (shared chart style), `tests/test_data.py` (tests).

**Design choices**

- **Spearman, not Pearson:** a few countries with extreme inflation would dominate a Pearson correlation; Spearman uses ranks, so they count as just the highest rank. In 2022 it finds a weak but significant negative link (ρ = −0.22, p = 0.003, 178 countries).
- **Bubble size is GDP**, not population, because the story is about economies. This is explained on the chart and shown on hover.
- **Honest charts:** a year is only shown if at least 80% of countries reported; countries outside the axes are named rather than hidden; a note explains why Ireland's GDP overstates its domestic economy (GNI\*).

**How the globe works**

The globe uses **Plotly Express** (`px.choropleth`), the same library as the bubble chart. No extra mapping library or map files are needed.

1. **Countries:** each country is matched by its ISO-3 code from the World Bank (e.g. `IRL`). Plotly has world country outlines built in, so it colours the right shape automatically.
2. **A globe, not a flat map:** setting `projection="orthographic"` draws the world as a sphere seen from space, which the user can **drag to rotate**. `update_geos` adds blue oceans and white borders, and starts the view over Europe.
3. **Animation:** `animation_frame="year"` adds the play button and year slider, so you can watch inflation spread in 2021–22.
4. **Fixed colour scale:** blue (low) to red (high), fixed at **0–15%** so a colour means the same thing in every year. Countries above 15% show as the darkest red, so one country with very high inflation can't stretch the scale and wash out the rest.

From `globe_chart()` in `panel_a/model_a.py`:

```python
fig = px.choropleth(
    plot_df, locations="economy", color="inflation", hover_name="name",
    animation_frame="year", projection="orthographic",   # a draggable globe
    color_continuous_scale="RdYlBu_r", range_color=[0, 15],  # same colours every year
    labels={"inflation": "Inflation (%)"},
)
fig.update_geos(
    showocean=True, oceancolor="#E1EFF4",
    showcountries=True, countrycolor="white",
    showframe=False, projection_rotation=dict(lon=-10, lat=35),  # starts over Europe
)
```

**Data source**

| Provider | Indicators | Access | Frequency | Licence |
|---|---|---|---|---|
| [World Bank World Development Indicators](https://data.worldbank.org/) | Inflation `FP.CPI.TOTL.ZG`, GDP growth `NY.GDP.MKTP.KD.ZG`, unemployment `SL.UEM.TOTL.ZS`, GDP `NY.GDP.MKTP.CD` | Public API via `wbgapi`, no key needed | Annual | CC BY 4.0 |
| [Yahoo Finance](https://finance.yahoo.com/) via `yfinance` | Daily adjusted prices for SPY, TLT, GLD, XLE, XLU, QQQ, IWM, EFA | Public, no key | Daily, from Jan 2015 | Yahoo Finance terms of use |

**Reliability:** downloads are cached for a day. `data.py` requests one indicator at a time, with retries. If the World Bank doesn't reply within 30 seconds, or returns incomplete data, the panel uses the saved snapshot in `data/fallback/world_bank.csv` and says so on screen. Refresh the snapshot with `python data.py`.

**Tests:** `tests/test_data.py` checks that an incomplete download raises an error (so the snapshot is used), that the download is reshaped into one row per country per year, and that the snapshot has every column the panel needs. Run with `python -m pytest -v`.

## Panel 2: Who wins when rates move? (Eoin Cunningham)

**Question:** how do changes in interest rates affect different types of investments, and which ETFs are most sensitive?

A bar chart comparing the historical interest-rate sensitivity of eight ETFs (SPY, TLT, GLD, XLE, XLU, QQQ, IWM, EFA). Each sensitivity is estimated using a linear regression of ETF percentage returns against changes in the US 10-year Treasury yield, with the regression coefficient showing the estimated ETF return for a one-percentage-point rise in yields. A rate-shock slider applies these sensitivities to different interest-rate scenarios, showing which investments are expected to gain or lose. Regression results also include R² values to indicate how much of each ETF's historical return variation is explained by yield changes.

**Controls:** data frequency (daily / weekly / monthly), regression start year (2015 / 2017 / 2019 / 2021), interest-rate shock slider (−3 to +3 percentage points), and shared economic scenario selector.


**Files:** `panel_b/model_b.py` (interest-rate regression, scenario calculations and dashboard), `data.py` (shared ETF and Treasury data loaders, regression data preparation and offline fallbacks), `scenarios.py` (shared economic scenarios), `style.py` (shared chart style).

### Data source

| Provider | Indicators | Access | Frequency | Licence |
| --- | --- | --- | --- | --- |
| [Yahoo Finance](https://finance.yahoo.com) via `yfinance` | Historical adjusted prices for SPY, TLT, GLD, XLE, XLU, QQQ, IWM, EFA | Public, no key needed | Daily prices, aggregated to weekly or monthly | Yahoo Finance terms of use |
| [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/series/DGS10) | US 10-year Treasury constant-maturity yield (`DGS10`) | Public CSV download; no API key required | Daily observations, aggregated to weekly or monthly | See FRED series terms |

**Reliability:** market data downloads are cached for 24 hours using Streamlit. No API keys or credentials are required. If live downloads fail, the application uses the saved datasets in `data/fallback/etf_prices.csv` and `data/fallback/treasury_yields.csv`, covering 2015–2024. ETF percentage returns and Treasury yield changes are matched by date, and missing observations are excluded from each regression. Results are recalculated when the selected frequency or start year changes. The estimated sensitivities are also shared with Panel 3 for portfolio analysis. Historical relationships represent statistical associations rather than causal effects or forecasts of future returns.

## Panel 3: Build the best portfolio (Conall Mooney)

**Question:** how can shares, bonds and gold be combined to balance estimated return and risk, and how would a portfolio fitted before 2022 have performed afterwards?

An interactive efficient frontier compares an equal-weight portfolio, individual assets, a user-defined allocation and a portfolio optimised for the highest estimated Sharpe ratio. A doughnut chart shows the optimised weights, while a dashed line illustrates combining risk-free cash with the optimised mix without borrowing.

A historical backtest fits weights using 2015–2021 data and evaluates buy-and-hold performance during 2022–2024 against SPY and a 60/40 SPY–TLT benchmark. It reports total return, annualised compound return, volatility and maximum drawdown.

**Controls:** eight ETFs (SPY, TLT, GLD, XLE, XLU, QQQ, IWM and EFA), maximum allocation per asset, estimation window and custom portfolio weights.

**Data and assumptions:** daily adjusted prices from Yahoo Finance via `yfinance`, cached for a day with a saved CSV fallback. Estimates use 252 trading days per year. Optimised weights total 100%, with no short selling. Results are in USD and exclude costs, taxes and currency conversion. Historical estimates are not forecasts.

**Connections:** uses Panel 2's scenario risk-free rate and available asset sensitivities; otherwise explains the historical assumptions used. Publishes the optimised portfolio through `st.session_state["p3_result"]` for Panel 4.

**Files:** `panel_c/model_c.py` (panel), `data.py` (shared loader), `style.py` (shared chart style), `data/fallback/etf_prices.csv` (saved prices).

## Panel 4: What could it become? (Hannah McElligott)

**Question:** how much could someone saving every month end up with, in today's euros, and how likely are they to reach their goal?

A Monte Carlo fan chart of 1,000 simulated futures, showing the bad (1 in 20), middle and good (1 in 20) outcomes and the chance of reaching a savings goal. Shaded bands show the middle 50% and 90% of outcomes, a dashed line shows the total paid in, and a dotted line marks the goal. Each future either re-uses real historical months of the chosen portfolio in a random order (bootstrap), so it includes real crashes such as 2020 and 2022, or draws from a normal distribution with the same mean and volatility (bell curve). Everything is converted to today's euros using the scenario's inflation, or Ireland's latest World Bank rate by default.

**Controls:** monthly amount, years, inflation, starting amount, savings goal, a 3-question risk quiz (Cautious 30/70, Balanced 60/40, Adventurous 90/10 shares/bonds), use Panel 3's optimal portfolio instead, simulation method (bootstrap or bell curve), and "Download my projection" (CSV).

**Data and assumptions:** daily adjusted SPY (shares) and TLT (bonds) prices from Yahoo Finance via `data.load_prices`, converted to monthly returns; Ireland's latest annual inflation rate from the World Bank (`FP.CPI.TOTL.ZG`) via `data.load_world_bank`. Both have saved CSV fallbacks, so the panel works offline. Prices are in USD, and exchange-rate effects, fees and taxes are ignored. Results show a range of possible outcomes based on history, not a forecast.

**Connections:** uses the inflation rate from Panel 2's scenario (converted from percent to a decimal). When Panel 3's portfolio is chosen, reads `st.session_state["p3_result"]` and uses its funds, weights, expected return (converted to a compound rate), volatility and estimation dates.

**Files:** `panel_d/model_d.py` (panel), `tests/test_p4_future.py` (tests), `docs/risk_quiz.md` (quiz scoring), `data.py` (shared loaders), `style.py` (shared chart style).


## Authors and contributions

Each member developed one principal panel and contributed to shared
project work. Responsibilities below summarise contributions evidenced
by the repository history; they do not represent measured hours or
percentage shares.

| Member | Individual panel | Shared project contributions | Selected evidence |
|---|---|---|---|
| **Ciara Feeney** | Developed the global economic panel, including animated bubbles, the rotatable globe and statistical comparisons. | Developed World Bank loading and robustness checks; established shared chart styling; implemented the overview/tab layout; pinned dependencies and contributed manual instructions and screenshots. | [Data-loader tests](https://github.com/conallmooney/Group-Project/commit/6035d07), [overview and tab layout](https://github.com/conallmooney/Group-Project/commit/26c0ed8), [dependency versions](https://github.com/conallmooney/Group-Project/commit/9d0b5a8) |
| **Eoin Cunningham** | Developed ETF interest-rate regressions, frequency controls, scenario-impact calculations and sensitivity charts. | Developed shared scenarios and synchronised controls; integrated panel execution; consolidated market-data functions into shared modules; contributed setup, troubleshooting and integration documentation. | [Four-panel integration](https://github.com/conallmooney/Group-Project/commit/e3c7496), [shared market-data modules](https://github.com/conallmooney/Group-Project/commit/e4edc95), [scenario documentation](https://github.com/conallmooney/Group-Project/commit/707eabe) |
| **Conall Mooney** | Developed portfolio optimisation, the efficient frontier, custom allocations, historical backtesting and the portfolio connections to Panels 2 and 4. | Established and managed the repository; reviewed and merged group changes; added portfolio price loading and fallback data; improved shared styling, card alignment, README instructions and Panel 3 documentation. | [Price loader and fallback](https://github.com/conallmooney/Group-Project/commit/5848c00), [README setup instructions](https://github.com/conallmooney/Group-Project/commit/5b6bac6), [shared theme refinements](https://github.com/conallmooney/Group-Project/commit/84f06e1) |
| **Hannah McElligott** | Developed savings simulations, historical bootstrapping, the risk quiz, inflation-adjusted outcomes and projection downloads. | Developed and maintained automated tests and testing records; identified integration issues; implemented Panel 4 compatibility fixes; established README/manual content and contributed final documentation updates. | [Panel 3 known-answer test](https://github.com/conallmooney/Group-Project/commit/9378108), [Panel 2 regression tests](https://github.com/conallmooney/Group-Project/commit/135bbe1), [integration testing records](https://github.com/conallmooney/Group-Project/commit/93b7e03) |

The linked commits are representative examples. The full Git history,
pull requests and testing log provide further evidence of development,
review and collaboration.

## AI assistance

Generative AI tools were used during development to explain programming
concepts, suggest and navigate code, troubleshoot errors, and explore
dashboard layouts and documentation. Team members reviewed and adapted
suggestions, with checks recorded in the testing log. AI output was
not treated as proof that the application was correct.

Each member describes their own use in their individual learning journal.

