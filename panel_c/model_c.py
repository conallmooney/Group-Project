"""Panel 3: Build the best portfolio. Portfolio optimiser and historical backtest."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import minimize

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


def optimise_portfolio(
    annual_returns: pd.Series,
    annual_covariance: pd.DataFrame,
    risk_free_rate: float,
    max_weight: float,
) -> np.ndarray:
    """Find long-only portfolio weights that maximise the estimated Sharpe ratio."""
    n_assets = len(annual_returns)

    if n_assets * max_weight < 1 - 1e-9:
        raise ValueError("The maximum allocation is too low for these assets.")

    # Start with an equal allocation
    initial_weights = np.full(n_assets, 1 / n_assets)

    def negative_sharpe(weights: np.ndarray) -> float:
        """Minimise negative Sharpe to maximise Sharpe."""
        _, volatility, sharpe = portfolio_stats(
            weights,
            annual_returns,
            annual_covariance,
            risk_free_rate,
        )

        if volatility <= 0 or not np.isfinite(sharpe):
            return 1e10

        return -sharpe

    # No short selling; allocations must add up to 100%
    bounds = [(0.0, max_weight)] * n_assets
    constraints = {
        "type": "eq",
        "fun": lambda weights: weights.sum() - 1,
    }

    result = minimize(
        negative_sharpe,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if not result.success:
        raise ValueError(f"Optimisation failed: {result.message}")

    weights = result.x

    if (
        not np.isfinite(weights).all()
        or abs(weights.sum() - 1) > 1e-6
        or (weights < -1e-6).any()
        or (weights > max_weight + 1e-6).any()
    ):
        raise ValueError("The optimiser returned invalid allocations.")

    return weights


def efficient_frontier(
    annual_returns: pd.Series,
    annual_covariance: pd.DataFrame,
    max_weight: float,
    n_points: int = 30,
) -> pd.DataFrame:
    """Calculate minimum-risk portfolios across feasible return targets."""
    n_assets = len(annual_returns)

    if n_assets * max_weight < 1 - 1e-9:
        raise ValueError("The allocation limit is too low.")

    means = annual_returns.to_numpy()
    covariance = annual_covariance.to_numpy()
    initial_weights = np.full(n_assets, 1 / n_assets)
    bounds = [(0.0, max_weight)] * n_assets
    total_weight = {
        "type": "eq",
        "fun": lambda weights: weights.sum() - 1,
    }

    def portfolio_variance(weights: np.ndarray) -> float:
        """Return annual portfolio variance."""
        return float(weights @ covariance @ weights)

    # Find the lowest-risk feasible portfolio
    minimum = minimize(
        portfolio_variance,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=total_weight,
        options={"maxiter": 1000, "ftol": 1e-10},
    )

    if not minimum.success:
        raise ValueError("Could not calculate the minimum-risk portfolio.")

    # Find the highest achievable return under the allocation limit
    highest = minimize(
        lambda weights: -float(weights @ means),
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=total_weight,
        options={"maxiter": 1000, "ftol": 1e-10},
    )

    if not highest.success:
        raise ValueError("Could not calculate the highest feasible return.")

    start_return = float(minimum.x @ means)
    end_return = float(highest.x @ means)
    targets = np.linspace(start_return, end_return, n_points)

    # A binding allocation limit can leave only one feasible portfolio
    if np.isclose(start_return, end_return, atol=1e-9, rtol=0):
        targets = np.array([start_return])

    rows = []
    starting_weights = minimum.x

    for target in targets:
        constraints = [
            total_weight,
            {
                "type": "ineq",
                "fun": lambda weights, target=target: (
                    float(weights @ means) - target
                ),
            },
        ]

        result = minimize(
            portfolio_variance,
            starting_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-10},
        )

        if not result.success:
            raise ValueError("Could not calculate every frontier point.")

        weights = result.x
        actual_return = float(weights @ means)

        if (
            not np.isfinite(weights).all()
            or abs(weights.sum() - 1) > 1e-6
            or (weights < -1e-6).any()
            or (weights > max_weight + 1e-6).any()
            or actual_return < target - 1e-6
        ):
            raise ValueError("The frontier returned an invalid portfolio.")

        rows.append({
            "Return": actual_return,
            "Volatility": float(
                np.sqrt(max(portfolio_variance(weights), 0.0))
            ),
        })
        starting_weights = weights

    return pd.DataFrame(rows)


def allocation_chart(allocation: pd.DataFrame) -> go.Figure:
    """Show the optimised portfolio allocation using the shared asset colours."""
    # Exclude allocations too small to display meaningfully
    chart_df = allocation[allocation["Allocation"] > 1e-6].copy()

    fig = px.pie(
        chart_df,
        names="Asset",
        values="Allocation",
        color="Asset",
        color_discrete_map=ASSET_COLOURS,
        hole=0.65,
    )

    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        hovertemplate="%{label}: %{percent}<extra></extra>",
        sort=False,
    )

    fig.update_layout(
        height=380,
        margin=dict(l=40, r=40, t=30, b=30),
        showlegend=False,
        annotations=[
            dict(
                text="Portfolio<br>allocation",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=18),
            )
        ],
    )

    return fig


def render(scenario: dict | None = None) -> None:
    """Draw Panel 3 with equal-weight and optimised portfolio comparisons."""

    # Clear previous results so invalid selections cannot leave stale data
    st.session_state.pop("p3_result", None)

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

    max_weight_pct = st.slider(
        "Maximum allocation to one asset (%)",
        min_value=10,
        max_value=100,
        value=60,
        step=5,
        key="p3_max_weight",
        help="A lower limit prevents the portfolio concentrating in one asset.",
    )
    max_weight = max_weight_pct / 100

    if len(tickers) * max_weight < 1 - 1e-9:
        st.info(
            f"With {len(tickers)} assets, the maximum allocation must be "
            f"at least {100 / len(tickers):.1f}% per asset. "
            "Increase the slider to the next available value."
        )
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

    # --- Optimised portfolio ---
    try:
        optimal_weights = optimise_portfolio(
            annual_returns,
            annual_covariance,
            risk_free_rate,
            max_weight,
        )

        optimal_return, optimal_volatility, optimal_sharpe = portfolio_stats(
            optimal_weights,
            annual_returns,
            annual_covariance,
            risk_free_rate,
        )
    except ValueError as error:
        st.error(f"Unable to optimise the portfolio: {error}")
        return

    # --- Share portfolio results with Panel D ---
    st.session_state["p3_result"] = {
        "tickers": list(tickers),
        "weights": optimal_weights.tolist(),
        "annual_return": float(optimal_return),
        "annual_volatility": float(optimal_volatility),
        "sharpe": float(optimal_sharpe),
        "risk_free_rate": float(risk_free_rate),
        "estimation_start": prices.index.min().strftime("%Y-%m-%d"),
        "estimation_end": prices.index.max().strftime("%Y-%m-%d"),
        "basis": "Historical estimates; assumed 3% risk-free rate",
    }

    st.write("Maximum-Sharpe portfolio")

    col1, col2, col3 = st.columns(3)
    col1.metric("Estimated annual return", f"{optimal_return:.2%}")
    col2.metric("Annual volatility", f"{optimal_volatility:.2%}")
    col3.metric("Sharpe ratio", f"{optimal_sharpe:.2f}")

    allocation = pd.DataFrame({
        "Asset": tickers,
        "Allocation": optimal_weights,
    })

    fig = allocation_chart(allocation)
    st.plotly_chart(fig, width="stretch", theme=None)

    st.dataframe(
        allocation.style.format({"Allocation": "{:.1%}"}),
        hide_index=True,
    )

    st.caption(
        f"Allocations total 100%, with no short selling and a maximum "
        f"of {max_weight:.0%} in any asset. "
        "Optimisation uses historical estimates and an assumed 3% annual "
        "risk-free rate. Historical performance does not guarantee future results."
    )

    # --- Efficient frontier ---
    st.write("The trade-off between estimated return and risk")

    try:
        frontier = efficient_frontier(
            annual_returns,
            annual_covariance,
            max_weight,
        )
    except ValueError as error:
        st.warning(f"Efficient frontier unavailable: {error}")
    else:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=frontier["Volatility"],
            y=frontier["Return"],
            mode="lines+markers",
            name="Efficient frontier",
            line=dict(color="#0E6E8C", width=3),
            marker=dict(size=5),
            hovertemplate=(
                "Annual volatility: %{x:.2%}<br>"
                "Estimated annual return: %{y:.2%}<extra></extra>"
            ),
        ))

        fig.add_trace(go.Scatter(
            x=[optimal_volatility],
            y=[optimal_return],
            mode="markers",
            name="Maximum-Sharpe portfolio",
            marker=dict(
                symbol="star",
                size=18,
                color="#D99A1A",
            ),
            hovertemplate=(
                "Maximum-Sharpe portfolio<br>"
                "Annual volatility: %{x:.2%}<br>"
                "Estimated annual return: %{y:.2%}<extra></extra>"
            ),
        ))

        fig.add_trace(go.Scatter(
            x=[volatility],
            y=[expected_return],
            mode="markers",
            name="Equal-weight portfolio",
            marker=dict(size=10, color="#5A6878"),
            hovertemplate=(
                "Equal-weight portfolio<br>"
                "Annual volatility: %{x:.2%}<br>"
                "Estimated annual return: %{y:.2%}<extra></extra>"
            ),
        ))

        fig.update_layout(
            height=440,
            xaxis_title="Annual volatility",
            yaxis_title="Estimated annual return",
            xaxis_tickformat=".0%",
            yaxis_tickformat=".0%",
            legend=dict(orientation="h", y=1.15, x=0),
        )

        st.plotly_chart(fig, width="stretch", theme=None)

        st.caption(
            "The curve shows the lowest estimated volatility available "
            "for each return target, using your selected assets and "
            "allocation limit. The star marks the maximum-Sharpe portfolio. "
            "All results use historical estimates."
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
        "The optimiser compares historical returns and risk "
        "to estimate the highest-Sharpe mix under your allocation limit."
    )


# Only runs when you test this file on its own, not when app.py imports it
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
