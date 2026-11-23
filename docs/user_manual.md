# User Manual
## 1. Getting started
TODO: how to open the dashboard
## 2. Choosing a scenario
TODO: what the scenario switch does
## 3. Panel 1: The global shock

Shows where inflation struck around the world from 2000 to 2024, and how it related to growth, for around 190 countries. This panel shows history, so it does not change with the scenario.

![Panel 1 in Bubbles view, 2022](img/p1_bubbles.png)

![Panel 1 in Globe view, 2022](img/p1_globe.png)

**Controls**

- **View:** switch between **Bubbles** (compare countries) and **Globe** (see where inflation was).
- **Y-axis (bubbles view):** compare inflation with **GDP growth** or with **unemployment**. It is greyed out on the globe, which shows inflation only.
- **Regions:** untick regions to focus on the others.
- **Highlight:** the country named on the chart as it plays (Ireland by default).
- **▶ and the year slider** (under the chart): play the years 2000–2024, or drag to any year.
- **Explain a year:** pick a year to see what happened and its numbers. The play button runs in your browser, so use this slider to update the numbers underneath.

**How to read the bubble chart**

- **Each bubble is a country.** Across: inflation (%). Up: GDP growth (%) or unemployment (%).
- **Bubble size:** the size of the economy (GDP in US dollars). Hover over a bubble to see its GDP.
- **Colour:** the country's region, shown in the legend.
- Countries outside the chart's axes are listed underneath ("Off the chart in 2022: …"), so none are hidden.

**How to read the globe**

- Each country is coloured by its inflation rate, from **blue (low)** to **red (high)**. The scale is fixed at 0–15%, so a colour means the same in every year; anything above 15% shows as the darkest red.
- **Drag the globe** to spin it. Press **▶** to watch inflation spread in 2021–22.

**Explain a year**

- **What happened:** one line on the key event, e.g. "2022: Russia invades Ukraine, energy prices spike, the Fed and ECB start raising rates."
- **The three numbers:** median inflation, the share of countries above 5% inflation, and the number of economies shrinking. The small figure underneath is the change from the year before. **Red means worse** (more inflation, more economies shrinking) and green means better.
- **Correlation:** a sentence giving the Spearman rank correlation (ρ) between inflation and growth (or unemployment) that year. Below 0 means countries with higher inflation tended to grow more slowly. "Statistically significant" means p is below 0.05.
- **Largest bubble:** the biggest economy that year, as a guide to bubble sizes.
- **"Why does Ireland's GDP jump around?"** (shown when Ireland is highlighted): explains why multinationals make Irish GDP swing, and why the CSO's GNI\* gives a truer picture.

**Good to know**

- A year is only shown if at least 80% of countries reported data, so the bubbles don't flicker as countries drop in and out.
- Under the chart, a grey line says when the data was fetched live from the World Bank. If the World Bank is slow or unavailable, the panel uses a saved copy and shows a **yellow notice** with its date.

All values are historical World Bank data, not forecasts.
## 4. Panel 2: Who wins when rates move?
TODO
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
