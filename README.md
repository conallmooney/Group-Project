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

## Panel 3: Build the best portfolio (Conall Mooney)

**Question:** how can shares, bonds and gold be combined to balance estimated return and risk, and how would a portfolio fitted before 2022 have performed afterwards?

The panel compares an equal-weight portfolio with a portfolio optimised for the highest estimated Sharpe ratio, subject to an allocation limit and no short selling. An interactive efficient frontier shows the available return–risk trade-offs, individual assets, the optimised mix and an optional user-defined portfolio. A dashed line illustrates combinations of risk-free cash and the optimised mix without borrowing. A doughnut chart shows the optimised allocations.

A separate historical backtest fits portfolio weights using 2015–2021 data only, then evaluates buy-and-hold performance during 2022–2024 against SPY and a portfolio initially allocated 60% to SPY and 40% to TLT. It reports total return, annualised compound return, annual volatility and maximum drawdown.

**Controls:** asset selection (SPY, TLT, GLD, XLE, XLU, QQQ, IWM and EFA), maximum allocation per asset, historical estimation window, and custom portfolio weights.

**Files:** `panel_c/model_c.py` (panel), `data.py` (shared price loader and CSV fallback), `style.py` (shared chart style), `data/fallback/etf_prices.csv` (saved prices).

### Data source

| **Provider** | **Data** | **Access** | **Frequency** | **Terms** |
| ------------ | -------- | ---------- | ------------- | --------- |
| [Yahoo Finance](https://finance.yahoo.com/) via `yfinance` | Adjusted closing prices for SPY, TLT, GLD, XLE, XLU, QQQ, IWM and EFA | Downloaded without an API key | Daily, from Jan 2015 | Yahoo Finance terms of use |

**Reliability:** downloads are cached for a day. If downloading fails or a requested asset has no data, the loader attempts to use `data/fallback/etf_prices.csv` and displays a warning. The panel uses dates with prices for every selected asset and requires at least 252 shared price observations.

### Methods and assumptions

Estimated annual returns are mean daily percentage changes multiplied by 252. Annual covariance is daily covariance multiplied by 252. Portfolio volatility uses the asset weights and covariance matrix; the Sharpe ratio is estimated annual excess return divided by annual volatility.

The optimiser uses SciPy's SLSQP method. Allocations must total 100%, remain non-negative and respect the selected maximum allocation. Optimisation uses historical estimates and does not guarantee future performance.

**Scenario connection:** Panel 3 uses Person B's scenario risk-free rate when available, otherwise an assumed 3% annual rate. When all selected assets have Panel B sensitivities, an illustrative annual return adjustment is applied: sensitivity × rate shock ÷ 5, converted from percentage units to decimals. Historical covariance remains unchanged. If sensitivities are missing, all selected assets retain their historical return estimates and the panel explains why.

**Panel 4 connection:** the optimised weights, estimated annual return, annual volatility, Sharpe ratio, estimation dates and scenario information are published through `st.session_state["p3_result"]`. Returns and volatility are supplied as annual decimals. Panel 4 continues to receive the optimised portfolio when a user explores a custom allocation.

**Backtest assumptions:** weights are fitted using only the training period and a fixed 3% risk-free rate. The portfolios start at US$100 at the final available close of 2021 and are held without rebalancing through 2022–2024. This test is independent of the current estimation-window selector and scenario adjustments.

**Limitations:** results use USD prices and exclude trading costs, taxes and currency conversion. Historical estimates and backtest results are not forecasts.

### Run Panel 3 separately

From the main project folder:

```bash
python -m streamlit run panel_c/model_c.py
```

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
