# User Manual
## 1. Getting started
TODO: how to open the dashboard
## 2. Choosing a scenario

The macroeconomic scenario selector at the top of the dashboard allows you to explore how different economic conditions could affect investments, portfolio decisions and future savings.

Choose from three predefined scenarios or create your own using the Custom option.

| Scenario | Yield shock (pp) | Inflation (%) | Risk-free rate (%) |
|---|---:|---:|---:|
| Higher for longer | +1.50 | 3.50 | 4.75 |
| Rate cuts | −1.50 | 2.00 | 3.00 |
| Stagflation | +2.00 | 6.00 | 5.25 |
| Custom (default values) | 0.00 | 2.50 | 4.00 |

**What the scenarios represent**
- **Higher for longer:** interest rates remain elevated as inflation stays above target.
- **Rate cuts:** interest rates fall as inflation moderates.
- **Stagflation:** high inflation combined with weak economic growth and elevated interest rates.
- **Custom:** set your own assumptions for interest rates, inflation and the risk-free rate.

**How the assumptions are used**
- **Yield shock:** determines the estimated impact of interest-rate changes on ETFs in Panel 2 and informs portfolio analysis in Panel 3.
- **Inflation:** affects the purchasing power of future savings in Panel 4.
- **Risk-free rate:** provides a benchmark for evaluating risk-adjusted portfolio returns in Panel 3.

**How the panels work together**
- Panel 1 provides historical economic context.
- Panel 2 estimates how different investments respond to the selected yield shock.
- Panel 3 uses asset sensitivities and scenario assumptions to inform portfolio construction.
- Panel 4 explores how savings and investments could grow over time, including the option to use the portfolio from Panel 3.

Selecting a new scenario resets Panel 2's yield slider to the corresponding preset. Select Custom to enter your own assumptions.

**Try it yourself:** switch from Higher for longer to Rate cuts and compare the changes in estimated ETF returns, portfolio allocations and future savings outcomes.

The scenarios are hypothetical economic assumptions designed for comparison and exploration, not predictions of future economic conditions.
## 3. Panel 1: The global shock
TODO
## 4. Panel 2: Who wins when rates move?

Shows how eight different ETFs have historically responded to changes in the US 10-year Treasury yield. A linear regression estimates each ETF's interest-rate sensitivity using historical market data from Yahoo Finance and FRED.

**Controls**
- **Frequency:** choose daily, weekly or monthly observations to compare interest-rate sensitivity across different time intervals.
- **Estimated from:** choose 2015, 2017, 2019 or 2021 as the starting year for the regression. All estimation periods end in 2024.
- **Yield change (pp):** simulate a rise or fall in the 10-year Treasury yield, from −3 to +3 percentage points. For example, a move from 4% to 5% is a +1 percentage-point change.
- **Shared scenario:** the yield slider starts at the selected economic scenario's rate shock. Moving the slider allows you to explore a custom scenario.

**How to read the chart**
- **Green bars:** ETFs with a positive estimated return impact.
- **Red bars:** ETFs with a negative estimated return impact.
- **Faded bars:** regressions with an R² below 0.10, meaning yield changes explain less than 10% of historical return variation.
- **Bar labels:** the estimated percentage return impact associated with the selected yield change.
- Hover over any bar to see its estimated impact, beta and R².
- The headline and summary identify the best- and worst-performing ETFs under the selected rate shock.

**Regression details:** expand this section to examine the statistics behind each ETF's estimated sensitivity.

- **Alpha:** the estimated return when the yield change is zero.
- **Beta:** the estimated percentage return change associated with a one-percentage-point rise in yields.
- **R²:** the proportion of historical return variation explained by yield changes.
- **Observations:** the number of historical data points used in the regression.
- **Scenario impact:** beta multiplied by the selected yield shock.

**Try it yourself:** move the yield slider from +1 to −1 percentage points and compare how long-term Treasury bonds (TLT) respond relative to equities, gold and energy stocks. Change the frequency or starting year to see whether the estimated relationships remain consistent.

**Connection to Panel 3:** the estimated ETF sensitivities are shared with the portfolio optimisation panel, allowing the selected interest-rate scenario to inform portfolio analysis.

**Data availability:** no API keys are required. If live market data cannot be downloaded, the dashboard uses saved historical ETF prices and Treasury yields from 2015–2024.

All results are historical estimates based on a linear model, not forecasts or evidence of causation. Other economic factors can also influence investment returns.
## 5. Panel 3: Build the best portfolio
TODO
## 6. Panel 4: What could it become?
Shows what someone saving every month could end up with, across 1,000 simulated futures, in today's euros.

![Panel 4](img/p4_results.png)

**Controls**
- **Monthly (€), Years, Starting amount:** how much you save, for how long, and what you start with.
- **Inflation:** starts at the chosen scenario's rate, or Ireland's latest rate from the World Bank. Drag it to try your own.
- **Savings goal:** a target in today's euros. Set it to 0 to switch it off.
- **Risk quiz:** three questions that pick a mix of shares (SPY) and bonds (TLT): Cautious 30/70, Balanced 60/40 or Adventurous 90/10.
- **Use returns from:** your quiz mix, or the optimal portfolio from Panel 3 (if Panel 3 has built one).
- **Simulation method:** *Real past months (bootstrap)* re-uses real months since 2015 in a random order; *Bell curve* draws returns from a normal distribution with the same average and volatility.

**How to read the chart**
- **Dark band:** the middle half of the 1,000 futures. **Light band:** 90% of them.
- **Solid line:** the middle outcome. **Dashed line:** the money you paid in, in today's euros. **Dotted line:** your goal.
- Hover over any year to see all the values.
- **The four numbers underneath:** bad case (only 1 in 20 futures did worse), middle outcome, good case (only 1 in 20 did better), and the chance of reaching your goal.

**Download my projection (CSV):** saves a year-by-year table of the money paid in and the bad, middle and good outcomes.

All values are a range of possible outcomes, not a forecast.
## 7. When something goes wrong
TODO: messages users might see and what they mean