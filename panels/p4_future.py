"""Panel 4 - What could it become?

Shows how a monthly saver's money could grow over time, 
using 1,000 simulated futures and adjusted for inflation."""

import numpy as np
import streamlit as st
import plotly.graph_objects as go

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


def render(scenario: dict) -> None:
    """Draw Panel 4 on the dashboard.
    Args:
        scenario (dict): The chosen scenario, with keys "name", "shock_pp",
            "inflation" and "rf". Not used yet.
    """
    st.subheader("Panel 4 -  What could it become?")
    monthly = st.slider("Monthly contribution (€)", 0, 1000, 150, step=25)
    years = st.slider("Years", 5, 40, 30)
    paths = simulate_paths(1000, monthly, 0.065, 0.15, years)
    real_paths = to_todays_euros(paths, scenario["inflation"])
    finals = real_paths[:, -1]
    fan = fan_percentiles(real_paths)
    x = np.arange(years + 1)
    fig = go.Figure()
    # Light band: 90% of futures land between the 5th and 95th percentiles
    fig.add_trace(go.Scatter(x=x, y=fan[5][::12], mode="lines", line=dict(width=0),
                             showlegend=False, name = "Bad case"))
    fig.add_trace(go.Scatter(x=x, y=fan[95][::12], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(14,110,140,0.15)",
                             name="Good case"))

    # Darker band: the middle half of futures, between the 25th and 75th percentiles
    fig.add_trace(go.Scatter(x=x, y=fan[25][::12], mode="lines", line=dict(width=0),
                             showlegend=False, name = "Lower middle"))
    fig.add_trace(go.Scatter(x=x, y=fan[75][::12], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(14,110,140,0.35)",
                             name="Upper middle"))
    fig.add_trace(go.Scatter(x=x, y=fan[50][::12], mode="lines", name="Middle outcome", line=dict(color="#0E6E8C", width=3)))
    fig.update_layout(title="How your savings could grow (today's €)", xaxis_title="Years from now", yaxis_title="Value in today's €", yaxis=dict(tickprefix="€",tickformat=",.0f", rangemode="tozero"),hovermode="x unified", legend=dict(orientation="h", y=1.1, x=0), template="plotly_white",height=420, showlegend=False)
    st.plotly_chart(fig)
    st.metric("Bad case (1 in 20), today's €", f"€{np.percentile(finals, 5):,.0f}")
    st.metric("Middle outcome, today's €", f"€{np.median(finals):,.0f}")
    st.metric("Good case (1 in 20), today's €", f"€{np.percentile(finals, 95):,.0f}")
    st.caption(f"Adjusted for {scenario['inflation']:.1%} inflation a year, so values show what the money would buy today.")


if __name__ == "__main__":
    render({"name": "Placeholder", "shock_pp": 0.0, "inflation": 0.025, "rf": 0.04})