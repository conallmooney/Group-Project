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

Needs Python 3.11 or newer. From the main project folder:

    pip install -r requirements.txt
    streamlit run app.py

No internet? Every data loader falls back to the saved CSVs in `data/fallback/`.

## How to run the tests

From the main project folder:

    python3 -m pytest -v

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
| [Yahoo Finance](https://finance.yahoo.com) via `yfinance` | Daily adjusted prices for SPY, TLT, GLD, XLE, XLU | Public, no key | Daily, from Jan 2015 | Yahoo Finance terms of use |

**Reliability:** downloads are cached for a day. If the World Bank doesn't reply within 20 seconds,
or returns incomplete data, the panel uses the saved snapshot in `data/fallback/world_bank.csv`
and says so on screen. Refresh the snapshot with `python data.py`.

## Panel 2: Who wins when rates move? (Eoin Cunningham)

**Question:** how do changes in interest rates affect different types of investments, and which ETFs are most sensitive?

A bar chart comparing the historical interest-rate sensitivity of eight ETFs (SPY, TLT, GLD, XLE, XLU, QQQ, IWM, EFA). Each sensitivity is estimated using a linear regression of ETF percentage returns against changes in the US 10-year Treasury yield, with the regression coefficient showing the estimated ETF return for a one-percentage-point rise in yields. A rate-shock slider applies these sensitivities to different interest-rate scenarios, showing which investments are expected to gain or lose. Regression results also include R² values to indicate how much of each ETF's historical return variation is explained by yield changes.

**Controls:** data frequency (daily / weekly / monthly), regression start year (2015 / 2017 / 2019 / 2021), interest-rate shock slider (−3 to +3 percentage points), and shared economic scenario selector.


**Files:** `panel_b/model_b.py` (interest-rate regression, scenario calculations and dashboard), `data.py` (shared ETF and Treasury data loaders, regression data preparation and offline fallbacks), `scenarios.py` (shared economic scenarios), `style.py` (shared chart style).

### Data source

| Provider | Indicators | Access | Frequency | Licence |
| --- | --- | --- | --- | --- |
| [Yahoo Finance](https://finance.yahoo.com) via `yfinance` | Historical adjusted prices for SPY, TLT, GLD, XLE, XLU, QQQ, IWM, EFA | Public, no key needed | Daily prices, aggregated to weekly or monthly | Yahoo Finance terms of use |
| [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/series/DGS10) | US 10-year Treasury constant-maturity yield (`DGS10`) | Public CSV endpoint, no API key required | Daily observations, aggregated to weekly or monthly | See FRED series terms |

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

**Question:** how much could someone saving every month end up with, in today's euros?

A Monte Carlo fan chart of 1,000 simulated futures, showing the bad, middle and good outcomes and the chance of reaching a savings goal. Each future either re-uses real historical months of the chosen portfolio in a random order (bootstrap) or draws from a normal distribution with the same mean and volatility, and everything is converted to today's euros using the scenario's inflation (or Ireland's latest World Bank rate by default).

**Controls:** monthly amount, years, inflation, starting amount, savings goal, a 3-question risk quiz (Cautious 30/70, Balanced 60/40, Adventurous 90/10 shares/bonds), use Panel 3's optimal portfolio instead, simulation method (bootstrap or bell curve), and "Download my projection" (CSV).

**Files:** `panel_d/model_d.py` (panel), `tests/test_p4_future.py` (tests), `data.py` (shared loaders), `style.py` (shared chart style).

## Authors

| Name | Panel | Shared job |
|------|-------|------------|
| Ciara Feeney | 1: The global shock | Data and robustness |
| Eoin Cunningham | 2: Who wins when rates move? | Scenario and integration |
| Conall Mooney | 3: Build the best portfolio | GitHub and deployment |
| Hannah McElligott | 4: What could it become? | Docs and testing |
