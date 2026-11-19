"""Panel 3: Build the best portfolio. Portfolio optimiser and historical backtest."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))  # find data.py and style.py
from data import load_prices
from style import ASSET_COLOURS

# Default assets used to build the portfolio
DEFAULT_TICKERS = ["SPY", "TLT", "GLD", "XLE", "XLU"]
TRADING_DAYS = 252

# Ticker -> description shown to the user
ASSET_NAMES = {
    "SPY": "US shares",
    "TLT": "Long-term US government bonds",
    "GLD": "Gold",
    "XLE": "US energy shares",
    "XLU": "US utilities shares",
}


def portfolio_stats(
    weights: np.ndarray,
    annual_returns: pd.Series,
    annual_covariance: pd.DataFrame,
    risk_free_rate: float,
) -> tuple[float, float, float]:
    """Calculate estimated annual return, volatility and Sharpe ratio."""
    expected_return = float(weights @ annual_returns.to_numpy())

    variance = float(
        weights @ annual_covariance.to_numpy() @ weights
    )
    volatility = float(np.sqrt(max(variance, 0.0)))

    sharpe = (
        (expected_return - risk_free_rate) / volatility
        if volatility > 0
        else float("nan")
    )

    return expected_return, volatility, sharpe


def render(scenario: dict | None = None) -> None:
    """Draw Panel 3 with asset selection and equal-weight portfolio metrics."""
    st.subheader("Build a portfolio across shares, bonds and gold")

    # --- Controls ---
    tickers = st.multiselect(
        "Choose your assets",
        options=DEFAULT_TICKERS,
        default=DEFAULT_TICKERS,
        format_func=lambda ticker: f"{ticker} — {ASSET_NAMES[ticker]}",
        key="p3_tickers",
    )

    if len(tickers) < 3:
        st.info("Choose at least three assets to build a portfolio.")
        return

    # --- Load the data ---
    try:
        prices = load_prices(tuple(tickers))
    except Exception as error:
        st.error(f"ETF prices are unavailable: {error}")
        return

    # Keep dates where every selected asset has a price
    prices = prices.dropna()

    if len(prices) < 3:
        st.info("Not enough shared price history.")
        return
    
    # --- Calculate historical returns and risk ---
    daily_returns = prices.pct_change(fill_method=None).dropna()
    annual_returns = daily_returns.mean() * TRADING_DAYS
    annual_covariance = daily_returns.cov() * TRADING_DAYS

    # Equal allocation across the selected assets
    weights = np.full(len(tickers), 1 / len(tickers))

    # Temporary assumption until Person B's scenario is connected
    risk_free_rate = 0.03

    expected_return, volatility, sharpe = portfolio_stats(
        weights,
        annual_returns,
        annual_covariance,
        risk_free_rate,
    )

    # --- Equal-weight portfolio ---
    st.write("Equal-weight portfolio")

    col1, col2, col3 = st.columns(3)
    col1.metric("Estimated annual return", f"{expected_return:.2%}")
    col2.metric("Annual volatility", f"{volatility:.2%}")
    col3.metric("Sharpe ratio", f"{sharpe:.2f}")

    st.caption(
        f"Each selected asset receives {1 / len(tickers):.1%} of the portfolio. "
        "Historical arithmetic estimates using 252 trading days per year "
        "and an assumed 3% annual risk-free rate. "
        "These estimates are not forecasts."
    )

    # --- Check the downloaded prices ---
    st.write("Latest adjusted closing prices")
    st.dataframe(prices.tail())

    start_date = prices.index.min().strftime("%d %b %Y")
    end_date = prices.index.max().strftime("%d %b %Y")

    st.caption(
        f"Price history available from {start_date} to {end_date}."
    )
    st.caption("Source: Yahoo Finance via yfinance. Adjusted closing prices.")

    # --- Portfolio overview ---
    st.write(f"You have selected {len(tickers)} assets.")

    st.caption(
        "The portfolio optimiser will compare historical returns and risk "
        "to find a mix of these assets."
    )


# Only runs when you test this file on its own, not when app.py imports it
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
