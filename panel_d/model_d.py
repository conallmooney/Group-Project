"""Panel 4 - What could it become?

Simulates 1,000 possible futures for a monthly saver and shows the range of
outcomes as a fan chart, in today's euros.

Author: Hannah McElligott (Person D, Panel 4 owner)
Data: daily SPY and TLT prices from Yahoo Finance and Irish inflation from the
World Bank, both loaded through data.py (with saved CSV backups)."""

import numpy as np
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from style import ACCENT, INK, MUTED, FAN_OUTER, FAN_INNER
from data import load_prices, load_world_bank


# Each risk profile is a real mix of shares (SPY) and bonds (TLT).
# The return and volatility are measured from real prices since 2015.
PROFILES = {"Cautious": {"shares": 0.3},
    "Balanced": {"shares": 0.6},
    "Adventurous": {"shares": 0.9},   
}

# The three risk-quiz questions. Answers are in order of score: 0, 1, 2.
QUIZ = [
    {"question": "When will you need most of this money?",
     "answers": ["In less than 5 years", "In 5 to 15 years", "In more than 15 years"]},
    {"question": "Your savings drop 20% in one bad year. What do you do?",
     "answers": ["Sell, so I don't lose any more", "Hold on and wait for them to recover",
                 "Invest more while prices are low"]},
    {"question": "Which matters most to you?",
     "answers": ["Keep it safe", "Grow it steadily",
                 "Aim for the most growth. I don't mind short-term losses"]},
]

def monthly_rate(annual_return: float) -> float:
    """Turn an annual return into the equivalent monthly return.

    Args:
        annual_return (float): The annual return as a decimal, e.g., 0.05 for 5%.  
    
    Returns:
        float: The monthly return as a decimal.
    """
    return (1 + annual_return) ** (1 / 12) - 1


def monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Turn daily prices into monthly returns.

    Args:
        prices (pd.DataFrame): Daily prices, one column per fund, dates as the index.

    Returns:
        pd.DataFrame: One row per month, the % change as a decimal (0.02 = +2%).
    """
    month_end = prices.resample("ME").last()
    return month_end.pct_change().dropna()


def portfolio_returns(history: pd.DataFrame, weights: dict) -> pd.Series:
    """Monthly returns of a mix of funds.

    Args:
        history (pd.DataFrame): Monthly returns, one column per fund.
        weights (dict): Share of the money in each fund, e.g. {"SPY": 0.6, "TLT": 0.4}.

    Returns:
        pd.Series: The mix's return for every month.
    """
    mix = pd.Series(0.0, index=history.index)
    for ticker, weight in weights.items():
        mix = mix + weight * history[ticker]
    return mix


def mix_stats(monthly: pd.DataFrame, share_weight: float) -> tuple[float, float]:
    """Real yearly return and volatility of a share/bond mix.

    Each month the mix earns share_weight of SPY's return plus the rest
    from TLT's return.

    Args:
        monthly (pd.DataFrame): Monthly returns with "SPY" and "TLT" columns.
        share_weight (float): Share of the money in SPY, e.g. 0.6 for 60%.

    Returns:
        tuple[float, float]: (yearly return, yearly volatility) as decimals.
    """
    mix = share_weight * monthly["SPY"] + (1 - share_weight) * monthly["TLT"]
    yearly_return = (1 + mix.mean()) ** 12 - 1
    yearly_volatility = mix.std() * np.sqrt(12)
    return float(yearly_return), float(yearly_volatility)


def latest_inflation(world_bank: pd.DataFrame, country: str = "IRL") -> tuple[float, int]:
    """Find a country's most recent inflation rate in the World Bank data.

    Args:
        world_bank (pd.DataFrame): Ciara's World Bank table, with "economy",
            "year" and "inflation" (in %) columns.
        country (str): Country code, e.g. "IRL" for Ireland.

    Returns:
        tuple[float, int]: (inflation as a decimal, the year it's from).
    """
    rows = world_bank[world_bank["economy"] == country].dropna(subset=["inflation"])
    latest = rows.sort_values("year").iloc[-1]
    return float(latest["inflation"]) / 100, int(latest["year"])


def scenario_inflation(scenario: dict) -> float | None:
    """The scenario's inflation as a decimal, or None if it has none.

    Person B's scenarios store inflation in percent (3.5 means 3.5%),
    so it is divided by 100 here.

    Args:
        scenario (dict): The chosen scenario from app.py.

    Returns:
        float | None: Inflation as a decimal (e.g. 0.035), or None.
    """
    value = scenario.get("inflation")
    if value is None:
        return None
    return value / 100


def compound_annual_return(arithmetic_annual: float) -> float:
    """Turn an annualised arithmetic mean return into a compound annual return.

    Panel 3 reports an annualised arithmetic mean (mean daily return x 252).
    Dividing by 12 gives the arithmetic monthly mean; compounding that over
    12 months gives the yearly rate this panel's simulation expects, so both
    panels mean the same monthly return.

    Args:
        arithmetic_annual (float): Annualised arithmetic mean return, e.g. 0.12.

    Returns:
        float: The equivalent compound annual return, e.g. 0.1268.
    """
    return (1 + arithmetic_annual / 12) ** 12 - 1


def grow_savings(start: float, monthly: float, annual_return: float, years: int) -> float:
    """Grow savings month by month at a fixed return.

    Args:
        start (float): The initial money invested, in euros.
        monthly (float): The amount of money added each month, in euros.
        annual_return (float): The annual return as a decimal, e.g., 0.065.
        years (int): The number of years of saving.

    Returns:
        float: The total amount of money after the specified number of years.
    """
    rate = monthly_rate(annual_return)
    balance = start
    for month in range(years * 12):
        balance = balance * (1 + rate)
        balance = balance + monthly
    return balance


def random_monthly_returns(annual_return: float, volatility: float, months: int, seed: int = 42) -> np.ndarray:
    """Make a random sequence of monthly returns that average to the given annual return, with the given volatility.
    
    Args:
        annual_return (float): The average annual return as a decimal, e.g., 0.065.
        volatility (float): The standard deviation of the returns as a decimal, e.g., 0.15.
        months (int): How many monthly returns to generate.
        seed (int): Starting point for the random number generator, for reproducibility.
        
    Returns: 
        np.ndarray: An array of random monthly returns.
    """
    rng = np.random.default_rng(seed)
    monthly_vol = volatility/np.sqrt(12)
    return rng.normal(monthly_rate(annual_return), monthly_vol, months)


def simulate_one_future(start: float, monthly: float, annual_return: float, volatility: float, years: int, seed: int = 42) -> float:
    """Grow savings month by month using a different random return each month.
    
    Args:
        start (float): The initial money invested, in euros.
        monthly (float): The amount of money added at the end of each month, in euros.
        annual_return (float): The average annual return as a decimal, e.g., 0.065.
        volatility (float): The annual standard deviation of the returns as a decimal, e.g., 0.15.
        years (int): The number of years of saving.
        seed (int): Starting point for the random number generator, for reproducibility.
    
    Returns:
        float: The value of the savings at the end of this one possible future.
        """
    returns = random_monthly_returns(annual_return, volatility, years * 12, seed)
    balance = start
    for r in returns:
        balance = balance * (1 + r)
        balance = balance + monthly
    return balance


def simulate_many_futures(start: float, monthly: float, annual_return: float, volatility: float, years: int, n_futures: int = 1000) -> np.ndarray:
    """Run many random futures and collect the end value of each one.
    
    Args:
        start (float): The initial money invested, in euros.
        monthly (float): The amount of money added at the end of each month, in euros.
        annual_return (float): The average annual return as a decimal, e.g., 0.065.
        volatility (float): The annual standard deviation of the returns as a decimal, e.g., 0.15.
        years (int): The number of years of saving.
        n_futures (int): How many random futures to simulate.
    
    Returns:
        np.ndarray: The end value of every simulated future.
        """
    results = []
    for i in range(n_futures):
        end_value = simulate_one_future(start, monthly, annual_return, volatility, years, seed=i)
        results.append(end_value)
    return np.array(results)


def simulate_paths(start: float, monthly: float, annual_return: float, volatility: float, years: int, n_futures: int = 1000, seed: int = 42) -> np.ndarray:
    """Simulate many random futures and return the full path of each one.

    Args: 
        start (float): The initial money invested, in euros.
        monthly (float): The amount of money added at the end of each month, in euros.
        annual_return (float): The average annual return as a decimal, e.g. 0.065.
        volatility (float): The annual standard deviation of the returns as a decimal, e.g. 0.15.
        years (int): The number of years of saving.
        n_futures (int): How many random futures to simulate.
        seed (int): Starting point for the random number generator, for reproducibility.

    Returns:
        np.ndarray: A grid with one row per future and one column per month.
        """
    months = years * 12
    rng = np.random.default_rng(seed)
    monthly_vol = volatility / np.sqrt(12)
    returns = rng.normal(monthly_rate(annual_return), monthly_vol, size = (n_futures, months))
    
    paths = np.zeros((n_futures, months +1))
    paths[:, 0] = start

    for m in range(months):
        paths[:, m + 1] = paths[:, m] * (1 + returns[:, m]) + monthly
    return paths


def bootstrap_paths(start: float, monthly: float, mix: pd.Series,
                    years: int, n_futures: int = 1000, seed: int = 42) -> np.ndarray:
    """Simulate many futures by re-using a portfolio's real months in a random order.

    Args:
        start (float): Money invested at the beginning, in euros.
        monthly (float): Money added at the end of each month, in euros.
        mix (pd.Series): The portfolio's real monthly returns, from portfolio_returns.
        years (int): Number of years of saving.
        n_futures (int): How many futures to simulate.
        seed (int): Starting point for the random numbers, so results repeat.

    Returns:
        np.ndarray: A grid with one row per future and one column per month.
    """
    months = years * 12
    rng = np.random.default_rng(seed)
    returns = rng.choice(mix.to_numpy(), size=(n_futures, months), replace=True)

    paths = np.zeros((n_futures, months + 1))
    paths[:, 0] = start
    for m in range(months):
        paths[:, m + 1] = paths[:, m] * (1 + returns[:, m]) + monthly
    return paths


def to_todays_euros(paths: np.ndarray, inflation: float) -> np.ndarray:
    """Convert future values into today's euros by removing inflation.

    Args:
        paths (np.ndarray): Grid of values, one row per future and one column per month.
        inflation (float): Yearly inflation rate as a decimal, e.g. 0.025.

    Returns:
        np.ndarray: The same grid, in today's euros.
    """
    months = np.arange(paths.shape[1])
    price_growth = (1 + inflation) ** (months / 12)
    return paths / price_growth


def paid_in_todays_euros(start: float, monthly: float, inflation: float, years: int) -> np.ndarray:
    """Total money paid in by each month, in today's euros.

    Each monthly payment is converted by when it is made, then they are added up.

    Args:
        start (float): Money invested at the beginning, in euros.
        monthly (float): Money added at the end of each month, in euros.
        inflation (float): Yearly inflation rate as a decimal, e.g. 0.025.
        years (int): Number of years of saving.

    Returns:
        np.ndarray: Total paid in by each month (month 0 to the final month).
    """
    months = np.arange(years * 12 + 1)
    each_payment = monthly / (1 + inflation) ** (months / 12)
    each_payment[0] = 0
    return start + np.cumsum(each_payment)

def fan_percentiles(paths: np.ndarray) -> dict:
    """Work out the bad, middle and good values at every month.

    Args:
        paths (np.ndarray): Grid of values, one row per future and one column per month.
    
    Returns:
        dict: Keys 5, 25, 50, 75 and 95, each holding one value per month.
    """
    fan = {}
    for p in [5, 25, 50, 75, 95]:
        fan[p] = np.percentile(paths, p, axis=0)
    return fan


def chance_of_reaching(finals: np.ndarray, goal: float) -> float:
    """Work out the share of futures that end at or above a savings goal.

    Args:
        finals (np.ndarray): The final value of each simulated future.
        goal (float): The savings goal, in the same units as finals.

    Returns:
        float: A probability between 0 and 1, e.g. 0.43 for 43%.
    """
    if goal <= 0:
        return 1.0
    return float(np.mean(finals >= goal))


def quiz_to_profile(scores: list) -> str:
    """Turn the three quiz answers into a risk profile.

    Each answer scores 0, 1 or 2, so the total runs from 0 to 6.
    0-2 is Cautious, 3-4 is Balanced and 5-6 is Adventurous.

    Args:
        scores (list): One score (0, 1 or 2) for each of the three questions.

    Returns:
        str: "Cautious", "Balanced" or "Adventurous".
    """
    total = sum(scores)
    if total <= 2:
        return "Cautious"
    elif total <= 4:
        return "Balanced"
    else:
        return "Adventurous"


def render(scenario: dict) -> None: 
    """Draw Panel 4 on the dashboard.

    Args:
        scenario (dict): The chosen scenario, with keys "name", "shock_pp",
            "inflation" and "rf".
    """
    st.subheader("What could it become?")
    headline_slot = st.empty()

    # --- Default inflation: the scenario's if it has one, else Ireland's latest real rate ---
    scenario_infl = scenario_inflation(scenario)
    if scenario_infl is not None:
        default_inflation = scenario_infl
        inflation_source = f"the {scenario['name']} scenario"
    else:
        world_bank, wb_note = load_world_bank()
        default_inflation, wb_year = latest_inflation(world_bank)
        inflation_source = f"Ireland's latest real rate, {wb_year}, World Bank. {wb_note}"

    default_pct = round(default_inflation * 100, 1)
    if st.session_state.get("p4_inflation_default") != default_pct:
        st.session_state["p4_inflation"] = default_pct
        st.session_state["p4_inflation_default"] = default_pct

    # --- Controls ---
    # Row 1: the three sliders
    c1, c2, c3 = st.columns(3)
    monthly = c1.slider("Monthly (€)", 0, 1000, 150, step=25, key="p4_monthly")
    years = c2.slider("Years", 5, 40, 30, key="p4_years")
    inflation = c3.slider("Inflation (% a year)", 0.0, 8.0,
                           step=0.1, key="p4_inflation") / 100

    # Row 2: the two amounts
    c4, c5 = st.columns(2)
    start = c4.number_input("Starting amount (€)", min_value=0, max_value=100000,
                            value=1000, step=500, key="p4_start")
    goal = c5.number_input("Savings goal, today's € (0 = none)", min_value=0,
                           max_value=10000000, value=50000, step=5000, key="p4_goal")
    
    with st.expander("Risk quiz: answer 3 questions to set your risk profile"):
        scores = []
        for i, q in enumerate(QUIZ):
            answer = st.radio(q["question"], q["answers"], index=1, key=f"p4_quiz_{i}")
            scores.append(q["answers"].index(answer))

    profile = quiz_to_profile(scores)
    prices = load_prices(("SPY", "TLT"))
    real_monthly = monthly_returns(prices)
    share_weight = PROFILES[profile]["shares"]
    annual_return, volatility = mix_stats(real_monthly, share_weight)
    real_mix = portfolio_returns(real_monthly, {"SPY": share_weight, "TLT": 1 - share_weight})
    st.caption(f"Your answers suggest a **{profile}** profile: {share_weight:.0%} shares (SPY), "
               f"{1 - share_weight:.0%} bonds (TLT). Real history since 2015: "
               f"{annual_return:.1%} average return and {volatility:.0%} volatility a year.")

    # --- Panel 3 link: use C's optimal portfolio if it exists ---
    source = st.radio("Use returns from", ["My risk quiz", "My Panel 3 portfolio"], horizontal=True, key="p4_source")
    p3 = st.session_state.get("p3_result")
    use_p3 = source == "My Panel 3 portfolio" and p3 is not None

    if source == "My Panel 3 portfolio" and p3 is None:
        st.info("Panel 3 hasn't built a portfolio yet, so your risk quiz is used for now.")

    if use_p3:
        p3_return = p3["expected_return"]
        annual_return = compound_annual_return(p3_return)
        volatility = p3["volatility"]
        p3_weights = dict(zip(p3["tickers"], p3["weights"]))
        p3_prices = load_prices(tuple(p3["tickers"]), start=p3["estimation_start"])
        p3_prices = p3_prices.loc[:p3["estimation_end"]]
        p3_monthly = monthly_returns(p3_prices)
        real_mix = portfolio_returns(p3_monthly, p3_weights)
        mix_text = ", ".join(f"{t} {w:.0%}" for t, w in p3_weights.items())
        st.caption(f"Using your Panel 3 portfolio ({mix_text}): {p3_return:.1%} expected "
                   f"return and {volatility:.0%} volatility a year.")
        st.caption(f"Bootstrap re-uses Panel 3's historical months "
                   f"({p3['estimation_start']} to {p3['estimation_end']}), so it doesn't "
                   f"reflect any scenario adjustment Panel 3 makes to expected returns.")

    method = st.radio("Simulation method",
                      ["Real past months (bootstrap)", "Bell curve"], horizontal=True, key="p4_method")

    # --- Simulation ---
    if method == "Real past months (bootstrap)":
        paths = bootstrap_paths(start, monthly, real_mix, years)
    else:
        paths = simulate_paths(start, monthly, annual_return, volatility, years)
    real_paths = to_todays_euros(paths, inflation)
    finals = real_paths[:, -1]
    fan = fan_percentiles(real_paths)
    x = np.arange(years + 1)

    # --- Headline: the finding, updated by the controls ---
    headline = f"After {years} years, the middle outcome is **€{np.median(finals):,.0f}** in today's money"
    if goal > 0:
        headline += f", with a **{chance_of_reaching(finals, goal):.0%} chance** of reaching €{goal:,.0f}"
    headline_slot.markdown(headline + ".")

    # --- Fan chart ---
    fig = go.Figure()
    # Light band: 90% of futures land between the 5th and 95th percentiles
    fig.add_trace(go.Scatter(x=x, y=fan[5][::12], mode="lines", line=dict(width=0),
                             showlegend=False, name="Bad case"))
    fig.add_trace(go.Scatter(x=x, y=fan[95][::12], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor=FAN_OUTER,
                             name="Good case"))

    # Darker band: the middle half of futures, between the 25th and 75th percentiles
    fig.add_trace(go.Scatter(x=x, y=fan[25][::12], mode="lines", line=dict(width=0),
                             showlegend=False, name="Lower middle"))
    fig.add_trace(go.Scatter(x=x, y=fan[75][::12], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor=FAN_INNER,
                             name="Upper middle"))
    
    fig.add_trace(go.Scatter(x=x, y=fan[50][::12], mode="lines", name="Middle outcome", line=dict(color=ACCENT, width=3)))
    paid = paid_in_todays_euros(start, monthly, inflation, years)
    fig.add_trace(go.Scatter(x=x, y=paid[::12], mode="lines", name="Paid in",
                             line=dict(color=MUTED, width=2, dash="dash")))
    if goal > 0:
        fig.add_hline(y=goal, line_dash="dot", line_color=INK,
                      annotation_text=f"Goal €{goal:,.0f}", annotation_position="top left")
        
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10),xaxis_title="Years from now", yaxis_title="Value in today's €", yaxis=dict(tickprefix="€",tickformat=",.0f", rangemode="tozero"),hovermode="x unified", legend=dict(orientation="h", y=1.1, x=0),height=420, showlegend=False)
    st.plotly_chart(fig, theme=None) 

    # --- Results ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bad case (1 in 20)", f"€{np.percentile(finals, 5):,.0f}")
    c2.metric("Middle outcome", f"€{np.median(finals):,.0f}")
    c3.metric("Good case (1 in 20)", f"€{np.percentile(finals, 95):,.0f}")
    if goal > 0:
        c4.metric("Chance of goal", f"{chance_of_reaching(finals, goal):.0%}")
    st.caption("Dark band: the middle half of the 1,000 simulated futures. Light band: 90% of them. "
               "Dashed line: the money you paid in. This shows a range of possible outcomes, not a forecast.")
    st.caption(f"Adjusted for {inflation:.1%} inflation a year (default from {inflation_source}), "
               f"so values show what the money would buy today.")
    fund_names = ", ".join(p3["tickers"]) if use_p3 else "SPY and TLT"
    st.caption(f"Source: daily {fund_names} prices from Yahoo Finance and inflation from the World Bank "
               f"(both via data.py, with saved CSV backups). Returns are historical estimates, not "
               f"forecasts, and ETF prices are in US dollars, so exchange-rate effects are ignored. "
               f"1,000 simulated futures using {method.lower()}.")

    # --- Share the result with the dashboard's Overview tab and headline numbers ---
    st.session_state["p4_result"] = {
        "years": years,
        "fan": {str(p): fan[p][::12].tolist() for p in (5, 25, 50, 75, 95)},
        "paid": paid[::12].tolist(),
        "median": float(np.median(finals)),
        "goal": float(goal),
        "chance": chance_of_reaching(finals, goal) if goal > 0 else None,
        "inflation": float(inflation),
    }
    # --- Download ---
    years_list = np.arange(years + 1)
    table = pd.DataFrame({
        "year": years_list,
        "paid_in_eur_nominal": start + monthly * 12 * years_list,
        "paid_in_todays_eur": paid_in_todays_euros(start, monthly, inflation, years)[::12].round(0).astype(int), 
        "bad_case_todays_eur": fan[5][::12].round(0).astype(int),
        "middle_todays_eur": fan[50][::12].round(0).astype(int),
        "good_case_todays_eur": fan[95][::12].round(0).astype(int),
    })
    st.download_button("Download my projection (CSV)", table.to_csv(index=False),
                       file_name="my_projection.csv", mime="text/csv", key="p4_download")

if __name__ == "__main__":
    render({"name": "Placeholder", "shock_pp": 0.0, "inflation": None, "rf": 0.04})