"""Panel 4 - What could it become?

Shows how a monthly saver's money could grow over time, 
using 1,000 simulated futures and adjusted for inflation."""

import numpy as np
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from style import ACCENT, INK, MUTED

# Return and volatility for each risk profile (yearly, as decimals).
# Long-run assumptions, matching docs/risk_quiz.md.
PROFILES = {
    "Cautious": {"return": 0.045, "volatility": 0.07},
    "Balanced": {"return": 0.065, "volatility": 0.11},
    "Adventurous": {"return": 0.085, "volatility": 0.16},
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
    st.subheader("Panel 4 -  What could it become?")
    headline_slot = st.empty()

    # --- Controls ---
    # Row 1: the three sliders
    c1, c2, c3 = st.columns(3)
    monthly = c1.slider("Monthly (€)", 0, 1000, 150, step=25)
    years = c2.slider("Years", 5, 40, 30)
    inflation = c3.slider("Inflation (% a year)", 0.0, 8.0,
                          scenario["inflation"] * 100, step=0.5) / 100

    # Row 2: the two amounts
    c4, c5 = st.columns(2)
    start = c4.number_input("Starting amount (€)", min_value=0, max_value=100000,
                            value=1000, step=500)
    goal = c5.number_input("Savings goal, today's € (0 = none)", min_value=0,
                           max_value=10000000, value=50000, step=5000)
    
    with st.expander("Risk quiz: answer 3 questions to set your risk profile"):
        scores = []
        for i, q in enumerate(QUIZ):
            answer = st.radio(q["question"], q["answers"], index=1, key=f"quiz_{i}")
            scores.append(q["answers"].index(answer))

    profile = quiz_to_profile(scores)
    annual_return = PROFILES[profile]["return"]
    volatility = PROFILES[profile]["volatility"]
    st.caption(f"Your answers suggest a **{profile}** profile: "
               f"{annual_return:.1%} expected return and {volatility:.0%} volatility a year.")

    # --- Simulation ---
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
                             fill="tonexty", fillcolor="rgba(14,110,140,0.15)",
                             name="Good case"))

    # Darker band: the middle half of futures, between the 25th and 75th percentiles
    fig.add_trace(go.Scatter(x=x, y=fan[25][::12], mode="lines", line=dict(width=0),
                             showlegend=False, name="Lower middle"))
    fig.add_trace(go.Scatter(x=x, y=fan[75][::12], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(14,110,140,0.35)",
                             name="Upper middle"))
    
    fig.add_trace(go.Scatter(x=x, y=fan[50][::12], mode="lines", name="Middle outcome", line=dict(color=ACCENT, width=3)))
    paid = paid_in_todays_euros(start, monthly, inflation, years)
    fig.add_trace(go.Scatter(x=x, y=paid[::12], mode="lines", name="Paid in",
                             line=dict(color=MUTED, width=2, dash="dash")))
    if goal > 0:
        fig.add_hline(y=goal, line_dash="dot", line_color=INK,
                      annotation_text=f"Goal €{goal:,.0f}", annotation_position="top left")
        
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10),xaxis_title="Years from now", yaxis_title="Value in today's €", yaxis=dict(tickprefix="€",tickformat=",.0f", rangemode="tozero"),hovermode="x unified", legend=dict(orientation="h", y=1.1, x=0),height=420, showlegend=False)
    st.plotly_chart(fig, theme = None) 

    # --- Results ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bad case (1 in 20)", f"€{np.percentile(finals, 5):,.0f}")
    c2.metric("Middle outcome", f"€{np.median(finals):,.0f}")
    c3.metric("Good case (1 in 20)", f"€{np.percentile(finals, 95):,.0f}")
    if goal > 0:
        c4.metric("Chance of goal", f"{chance_of_reaching(finals, goal):.0%}")
    st.caption("Dark band: the middle half of the 1,000 simulated futures. Light band: 90% of them. "
               "Dashed line: the money you paid in. This shows a range of possible outcomes, not a forecast.")
    st.caption(f"Adjusted for {inflation:.1%} inflation a year, so values show what the money would buy today.")
    st.caption("Source: Monte Carlo simulation with random monthly returns. Returns and volatility "
               "are long-run assumptions for each risk profile.")

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
                       file_name="my_projection.csv", mime="text/csv")

if __name__ == "__main__":
    render({"name": "Placeholder", "shock_pp": 0.0, "inflation": 0.025, "rf": 0.04})