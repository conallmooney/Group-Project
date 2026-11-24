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
from style import ACCENT, ASSET_COLOURS, GOLD, INK, MUTED

# Default assets used to build the portfolio
DEFAULT_TICKERS = [
    "SPY", "TLT", "GLD", "XLE", "XLU", "QQQ", "IWM", "EFA",
]
AVAILABLE_TICKERS = DEFAULT_TICKERS.copy()
TRADING_DAYS = 252

# Ticker -> description shown to the user
ASSET_NAMES = {
    "SPY": "US shares",
    "TLT": "Long-term US government bonds",
    "GLD": "Gold",
    "XLE": "US energy shares",
    "XLU": "US utilities shares",
    "QQQ": "Nasdaq-100 shares",
    "IWM": "US small-company shares",
    "EFA": "Developed-market shares outside US and Canada",
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
    """Show all allocations, grouping small holdings without discarding them."""
    chart_df = allocation[allocation["Allocation"] > 0].copy()
    small = chart_df["Allocation"] < 0.005
    other_weight = float(chart_df.loc[small, "Allocation"].sum())
    chart_df = chart_df.loc[~small].copy()

    if other_weight > 0:
        chart_df = pd.concat([
            chart_df,
            pd.DataFrame({"Asset": ["Other"], "Allocation": [other_weight]}),
        ], ignore_index=True)

    chart_df = chart_df.sort_values("Allocation", ascending=False)
    chart_df["Label"] = [
        f"{asset}  {weight:.1%}"
        for asset, weight in zip(chart_df["Asset"], chart_df["Allocation"])
    ]
    chart_df["Text"] = [
        f"{weight:.0%}" if weight >= 0.03 else ""
        for weight in chart_df["Allocation"]
    ]

    fig = px.pie(
        chart_df,
        names="Label",
        values="Allocation",
        color="Asset",
        color_discrete_map={**ASSET_COLOURS, "Other": "#B8C2CC"},
        hole=0.6,
    )
    fig.update_traces(
        text=chart_df["Text"].tolist(),
        textposition="inside",
        texttemplate="%{text}",
        insidetextfont=dict(color="white", size=13),
        hovertemplate="%{label}<extra></extra>",
        sort=False,
        direction="clockwise",
    )
    fig.update_layout(
        height=480,
        margin=dict(l=10, r=10, t=30, b=30),
        showlegend=True,
        legend=dict(
            orientation="v", x=1.0, y=0.5,
            xanchor="left", yanchor="middle",
            font=dict(size=13),
        ),
        annotations=[dict(
            text="Portfolio<br>allocation",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=MUTED),
        )],
    )
    return fig


def frontier_chart(
    frontier: pd.DataFrame,
    annual_returns: pd.Series,
    annual_covariance: pd.DataFrame,
    points: dict,
    risk_free_rate: float,
) -> go.Figure:
    """Compare the frontier, individual assets and highlighted portfolios."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=frontier["Volatility"],
        y=frontier["Return"],
        mode="lines+markers",
        name="Efficient frontier",
        line=dict(color=ACCENT, width=3),
        marker=dict(size=4),
    ))

    # Cash combined with the optimised portfolio, without borrowing
    best_volatility, best_return = points["Maximum-Sharpe portfolio"]

    if best_volatility > 0:
        fig.add_trace(go.Scatter(
            x=[0.0, best_volatility],
            y=[risk_free_rate, best_return],
            mode="lines",
            name="Capital Market Line",
            line=dict(color=MUTED, width=2, dash="dash"),
        ))

    # A standalone asset's volatility is the square root of its variance
    asset_volatility = np.sqrt(
        np.maximum(np.diag(annual_covariance.to_numpy()), 0.0)
    )

    fig.add_trace(go.Scatter(
        x=asset_volatility,
        y=annual_returns.to_numpy(),
        mode="markers+text",
        name="Single assets",
        text=list(annual_returns.index),
        textposition="top center",
        textfont=dict(size=13, color=MUTED),
        marker=dict(
            size=10,
            color="white",
            line=dict(color=MUTED, width=2),
        ),
        hovertemplate=(
            "%{text}<br>Annual volatility: %{x:.2%}<br>"
            "Estimated annual return: %{y:.2%}<extra></extra>"
        ),
    ))

    styles = {
        "Equal-weight portfolio": dict(size=10, color=MUTED),
        "Your allocation": dict(
            symbol="diamond", size=12, color="#8E5AC8",
        ),
        "Maximum-Sharpe portfolio": dict(
            symbol="star", size=18, color=GOLD,
        ),
    }

    for name, (volatility, expected_return) in points.items():
        fig.add_trace(go.Scatter(
            x=[volatility],
            y=[expected_return],
            mode="markers",
            name=name,
            marker=styles[name],
        ))

    for trace in fig.data:
        if trace.hovertemplate is None:
            trace.hovertemplate = (
                "Annual volatility: %{x:.2%}<br>"
                "Estimated annual return: %{y:.2%}"
                "<extra>%{fullData.name}</extra>"
            )

    fig.update_layout(
        height=480,
        font=dict(size=13, color=INK),
        xaxis=dict(
            title=dict(
                text="Annual volatility (risk)",
                font=dict(size=13),
            ),
            tickformat=".0%",
            rangemode="tozero",
            tickfont=dict(size=12),
            automargin=True,
        ),
        yaxis=dict(
            title=dict(
                text="Estimated annual return",
                font=dict(size=13),
            ),
            tickformat=".0%",
            tickfont=dict(size=12),
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            yanchor="bottom",
            x=0,
            font=dict(size=12),
        ),
        margin=dict(l=55, r=20, t=55, b=55),
    )

    return fig


def historical_backtest(
    full_prices: pd.DataFrame,
    tickers: list[str],
    max_weight: float,
) -> tuple[pd.DataFrame, pd.Series]:
    """Fit weights in 2015–2021 and evaluate buy-and-hold results in 2022–2024."""
    columns = list(dict.fromkeys(tickers + ["SPY", "TLT"]))
    history = full_prices.loc[:, columns].sort_index().dropna()
    training = history.loc["2015-01-01":"2021-12-31"]
    testing = history.loc["2022-01-01":"2024-12-31"]

    if len(training) < TRADING_DAYS or len(testing) < TRADING_DAYS:
        raise ValueError(
            "Insufficient shared history for the training or test period."
        )

    if (
        training.index.min().year != 2015
        or training.index.max().year != 2021
        or testing.index.min().year != 2022
        or testing.index.max().year != 2024
    ):
        raise ValueError(
            "Shared prices must cover 2015–2021 and 2022–2024."
        )

    training_returns = training[tickers].pct_change(
        fill_method=None
    ).dropna()

    fitted_weights = optimise_portfolio(
        training_returns.mean() * TRADING_DAYS,
        training_returns.cov() * TRADING_DAYS,
        risk_free_rate=0.03,
        max_weight=max_weight,
    )

    # Include the first test-day return using the final training close
    evaluation = pd.concat([training.tail(1), testing])
    relative_prices = evaluation / evaluation.iloc[0]

    growth = pd.DataFrame({
        "Optimised portfolio": relative_prices[tickers] @ fitted_weights,
        "60/40 shares–bonds": (
            0.6 * relative_prices["SPY"]
            + 0.4 * relative_prices["TLT"]
        ),
        "SPY": relative_prices["SPY"],
    })

    allocation = pd.Series(
        fitted_weights,
        index=tickers,
        name="Allocation",
    )

    return growth, allocation


def backtest_summary(growth: pd.DataFrame) -> pd.DataFrame:
    """Summarise realised performance over the historical test period."""
    daily_returns = growth.pct_change(fill_method=None).dropna()
    years = (growth.index[-1] - growth.index[0]).days / 365.25
    drawdowns = growth / growth.cummax() - 1
    total_growth = growth.iloc[-1] / growth.iloc[0]

    return pd.DataFrame({
        "Total return": total_growth - 1,
        "Annualised compound return": total_growth ** (1 / years) - 1,
        "Annual volatility": daily_returns.std() * np.sqrt(TRADING_DAYS),
        "Maximum drawdown": drawdowns.min(),
    })


def render(scenario: dict | None = None) -> None:
    """Draw Panel 3 with equal-weight and optimised portfolio comparisons."""

    # Clear previous results so invalid selections cannot leave stale data
    st.session_state.pop("p3_result", None)

    st.caption("03 · BUILD THE BEST PORTFOLIO")
    headline = st.empty()
    headline.subheader("Build a portfolio across shares, bonds and gold")

    # --- Controls ---
    assets_col, limit_col, window_col = st.columns([2.2, 1, 1])

    tickers = assets_col.multiselect(
        "Assets",
        options=AVAILABLE_TICKERS,
        default=DEFAULT_TICKERS,
        format_func=lambda ticker: f"{ticker} — {ASSET_NAMES[ticker]}",
        key="p3_tickers",
    )

    max_weight_pct = limit_col.slider(
        "Maximum allocation per asset (%)",
        min_value=10,
        max_value=100,
        value=60,
        step=5,
        key="p3_max_weight",
        help="Limits concentration in the optimised portfolio.",
    )

    lookback = window_col.selectbox(
        "Estimation window",
        options=["All available", "Last 3 years", "Last 5 years", "Last 10 years"],
        key="p3_lookback",
    )

    max_weight = max_weight_pct / 100

    if len(tickers) < 3:
        st.info("Choose at least three assets to build a portfolio.")
        return

    if len(tickers) * max_weight < 1 - 1e-9:
        st.info(
            f"With {len(tickers)} assets, the maximum allocation must be "
            f"at least {100 / len(tickers):.1f}% per asset. "
            "Increase the slider to the next available value."
        )
        return

    # --- Load the data ---
    # Always include both benchmark assets for the historical backtest
    download_tickers = tuple(dict.fromkeys(tickers + ["SPY", "TLT"]))

    try:
        full_prices = load_prices(download_tickers).sort_index()
    except Exception as error:
        st.error(f"ETF prices are unavailable: {error}")
        return

    prices = full_prices.loc[:, tickers].copy()

    # Keep dates where every selected asset has a price
    prices = prices.dropna().sort_index()

    if prices.empty:
        st.info("No shared price history is available for these assets.")
        return

    # Measure the window backwards from the latest available observation
    if lookback != "All available":
        years_back = int(lookback.split()[1])
        cutoff = prices.index.max() - pd.DateOffset(years=years_back)
        prices = prices.loc[prices.index >= cutoff].copy()

    if len(prices) < TRADING_DAYS:
        st.info("At least 252 shared price observations are required.")
        return

    # --- Calculate historical returns and risk ---
    daily_returns = prices.pct_change(fill_method=None).dropna()
    annual_returns = daily_returns.mean() * TRADING_DAYS
    annual_covariance = daily_returns.cov() * TRADING_DAYS

    # Equal allocation across the selected assets
    weights = np.full(len(tickers), 1 / len(tickers))

    # --- Scenario risk-free rate ---
    active_scenario = (
        scenario
        if scenario is not None
        else st.session_state.get("scenario")
    )

    if active_scenario is None:
        risk_free_rate = 0.03
        risk_free_note = "an assumed 3% annual risk-free rate"
    else:
        try:
            # Person B supplies percentages: 4.75 means 4.75%
            risk_free_rate = float(active_scenario["rf"]) / 100

            if not np.isfinite(risk_free_rate):
                raise ValueError(
                    "The scenario risk-free rate must be a finite number."
                )
        except (KeyError, TypeError, ValueError) as error:
            st.error(f"Invalid scenario risk-free rate: {error}")
            return

        scenario_name = str(active_scenario.get("name", "Custom"))
        risk_free_note = (
            f"a {risk_free_rate:.2%} annual risk-free rate "
            f"from the '{scenario_name}' scenario"
        )

    # --- Scenario adjustments to estimated asset returns ---
    scenario_adjusted = False
    scenario_note = "Asset returns use historical estimates."
    shock_pp = 0.0

    if active_scenario is not None:
        try:
            shock_pp = float(active_scenario["shock_pp"])

            if not np.isfinite(shock_pp):
                raise ValueError(
                    "The rate shock must be a finite number."
                )
        except (KeyError, TypeError, ValueError) as error:
            st.error(f"Invalid scenario rate shock: {error}")
            return

        if shock_pp == 0:
            scenario_note = (
                "The selected rate shock is zero; asset returns use "
                "historical estimates."
            )
        else:
            asset_betas = st.session_state.get("asset_betas", {})

            try:
                betas = pd.Series(
                    {
                        ticker: float(asset_betas.get(ticker, np.nan))
                        for ticker in tickers
                    },
                    dtype=float,
                )
            except (TypeError, ValueError, AttributeError):
                betas = pd.Series(
                    np.nan,
                    index=tickers,
                    dtype=float,
                )

            missing = betas.index[~np.isfinite(betas)].tolist()

            if missing:
                st.warning(
                    "Rate-shock adjustment not applied: Panel B "
                    "sensitivities are unavailable for "
                    f"{', '.join(missing)}. "
                    "Calculate sensitivities in Panel B. All selected "
                    "assets currently retain their historical "
                    "return estimates."
                )

                scenario_note = (
                    "Asset returns remain historical because some "
                    "Panel B sensitivities are unavailable."
                )
            else:
                # Convert percentage units and spread over five years
                adjustments = betas * shock_pp / 5 / 100
                annual_returns = annual_returns.add(adjustments)

                scenario_adjusted = True
                scenario_note = (
                    f"Asset returns include an illustrative "
                    f"{shock_pp:+.2f} pp rate shock, using Panel B "
                    "sensitivities divided by five and added to "
                    "annual historical estimates. "
                    "Historical covariance is unchanged."
                )

    expected_return, volatility, sharpe = portfolio_stats(
        weights,
        annual_returns,
        annual_covariance,
        risk_free_rate,
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
        "expected_return": float(optimal_return),
        "volatility": float(optimal_volatility),
        "sharpe": float(optimal_sharpe),
        "risk_free_rate": float(risk_free_rate),
        "estimation_start": prices.index.min().strftime("%Y-%m-%d"),
        "estimation_end": prices.index.max().strftime("%Y-%m-%d"),
        "scenario_adjusted": scenario_adjusted,
        "shock_pp": shock_pp,
        "basis": (
            f"{scenario_note} Calculations use {risk_free_note}."
        ),
    }

    allocation = pd.DataFrame({
        "Asset": tickers,
        "Allocation": optimal_weights,
    })
    top = allocation.loc[allocation["Allocation"].idxmax()]

    # --- Headline based on the current result ---
    headline.subheader(
        f"Best mix: {optimal_return:.1%} estimated annual return "
        f"at {optimal_volatility:.1%} volatility"
    )

    # --- Compact portfolio comparison ---
    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Estimated annual return",
        f"{optimal_return:.1%}",
        f"{(optimal_return - expected_return) * 100:+.1f} pp vs equal weights",
        border=True,
    )
    m2.metric(
        "Annual volatility",
        f"{optimal_volatility:.1%}",
        f"{(optimal_volatility - volatility) * 100:+.1f} pp vs equal weights",
        delta_color="inverse",
        border=True,
    )
    m3.metric(
        "Sharpe ratio",
        f"{optimal_sharpe:.2f}",
        f"{optimal_sharpe - sharpe:+.2f} vs equal weights",
        border=True,
    )
    m4.metric(
        "Largest holding",
        str(top["Asset"]),
        f"{top['Allocation']:.1%} of the portfolio",
        delta_color="off",
        border=True,
    )

    with st.expander("Compare portfolio metrics"):
        comparison = pd.DataFrame({
            "Portfolio": ["Equal weight", "Maximum Sharpe"],
            "Estimated annual return": [expected_return, optimal_return],
            "Annual volatility": [volatility, optimal_volatility],
            "Sharpe ratio": [sharpe, optimal_sharpe],
        })
        st.dataframe(
            comparison.style.format({
                "Estimated annual return": "{:.2%}",
                "Annual volatility": "{:.2%}",
                "Sharpe ratio": "{:.2f}",
            }),
            hide_index=True,
        )
        st.caption(
            "pp means percentage points. Both portfolios use the same "
            "estimation window, scenario assumptions and risk-free rate."
        )

    # --- Main charts ---
    frontier_column, allocation_column = st.columns([1.35, 1])
    frontier_box = frontier_column.container(border=True, key="card_p3_frontier",)
    allocation_box = allocation_column.container(border=True,  key="card_p3_allocation",)

    frontier_box.markdown("**Risk vs Return (No Borrowing)**")
    allocation_box.markdown("**Optimised allocation**")

    fig = allocation_chart(allocation)
    allocation_box.plotly_chart(fig, width="stretch", theme=None)

    with allocation_column.expander("View allocation table"):
        st.dataframe(
            allocation.style.format({"Allocation": "{:.1%}"}),
            hide_index=True,
        )
        st.caption(
            "Holdings below 0.5% are grouped as Other in the chart. "
            "This table lists every selected asset."
        )

    takeaway = st.empty()

    # --- Custom portfolio comparison ---
    custom_stats = None

    with st.expander("Try your own mix"):
        st.caption(
            "Enter percentages totalling 100%. Your mix appears as a purple "
            "diamond on the chart. The allocation limit applies to the "
            "optimiser only; Panel D continues to receive the optimised mix."
        )

        custom_percentages = []

        # Up to four inputs per row keeps eight-asset selections readable
        for start in range(0, len(tickers), 4):
            row_tickers = tickers[start:start + 4]
            input_columns = st.columns(len(row_tickers))

            for column, ticker in zip(input_columns, row_tickers):
                percentage = column.number_input(
                    f"{ticker} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=1.0,
                    key=f"p3_custom_{ticker}",
                )
                custom_percentages.append(percentage)

        total = float(sum(custom_percentages))

        if not np.isclose(total, 100.0, atol=1e-6, rtol=0):
            st.info(
                f"Your allocations currently total {total:.1f}%. "
                "Adjust them to total 100%."
            )
        else:
            custom_weights = np.array(custom_percentages) / 100

            custom_stats = portfolio_stats(
                custom_weights,
                annual_returns,
                annual_covariance,
                risk_free_rate,
            )

            custom_return, custom_volatility, custom_sharpe = custom_stats

            col1, col2, col3 = st.columns(3)
            col1.metric("Your estimated annual return", f"{custom_return:.2%}")
            col2.metric("Your annual volatility", f"{custom_volatility:.2%}")
            col3.metric("Your Sharpe ratio", f"{custom_sharpe:.2f}")

            st.caption(
                "Uses the same estimation window and risk-free rate "
                "as the other portfolios. Panel D continues to receive "
                "the optimised portfolio."
            )

    # --- Efficient frontier ---
    flat_note = ""

    try:
        frontier = efficient_frontier(
            annual_returns,
            annual_covariance,
            max_weight,
        )
    except ValueError as error:
        frontier_box.warning(
            f"Efficient frontier unavailable: {error}"
        )
    else:
        points = {
            "Equal-weight portfolio": (volatility, expected_return),
        }

        if custom_stats is not None:
            points["Your allocation"] = (
                custom_stats[1],
                custom_stats[0],
            )

        points["Maximum-Sharpe portfolio"] = (
            optimal_volatility,
            optimal_return,
        )

        fig = frontier_chart(
            frontier,
            annual_returns,
            annual_covariance,
            points,
            risk_free_rate,
        )

        frontier_box.plotly_chart(
            fig,
            width="stretch",
            theme=None,
        )

        # Add a numerical explanation only when the curve clearly flattens
        last = frontier.iloc[-1]
        extra_return = float(last["Return"] - optimal_return)
        extra_risk = float(last["Volatility"] - optimal_volatility)

        if extra_risk > 0.02 and 0 <= extra_return < 0.01:
            flat_note = (
                f" At the frontier's highest-return point, volatility is "
                f"{extra_risk * 100:.1f} percentage points higher for only "
                f"{extra_return * 100:.1f} percentage points more "
                "estimated annual return."
            )

    # --- Explain the current allocation without implying a forecast ---
    with takeaway.container(border=True):
        st.markdown(
            f"**Largest holding:** {top['Asset']} "
            f"({ASSET_NAMES[top['Asset']]}) — "
            f"**{top['Allocation']:.1%}** of the optimised portfolio.\n\n"
            f"**Estimated Sharpe ratio:** {optimal_sharpe:.2f} "
            f"for the optimised mix versus {sharpe:.2f} "
            "for equal weights."
        )

        if flat_note:
            st.caption(flat_note.strip())

    # --- Historical backtest ---
    with st.expander("Historical backtest: fitted on 2015–21, tested on 2022–24"):
        st.caption(
            "Weights are fitted using 2015–2021 data only, with your "
            "selected assets, allocation limit and a fixed 3% risk-free rate. "
            "The portfolios are then held through 2022–2024."
        )

        try:
            growth, backtest_allocation = historical_backtest(
                full_prices,
                tickers,
                max_weight,
            )
        except ValueError as error:
            st.warning(f"Historical backtest unavailable: {error}")
        else:
            fig = px.line(
                growth * 100,
                labels={
                    "index": "Date",
                    "value": "Value of initial US$100",
                    "variable": "Portfolio",
                },
                color_discrete_map={
                    "Optimised portfolio":ACCENT,
                    "60/40 shares–bonds": GOLD,
                    "SPY": MUTED,
                },
            )

            fig.update_traces(
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "Value: US$%{y:.2f}<extra>%{fullData.name}</extra>"
                )
            )

            fig.update_layout(
                height=340,
                margin=dict(l=20, r=20, t=55, b=30),
                xaxis_title=None,
                yaxis_title="Value of initial US$100",
                legend=dict(
                    title_text="",
                    orientation="h",
                    y=1.15,
                    x=0,
                ),
            )

            st.plotly_chart(fig, width="stretch", theme=None)

            summary = backtest_summary(growth)
            fitted_return = float(summary.loc["Optimised portfolio", "Total return"])
            benchmark_return = float(summary.loc["60/40 shares–bonds", "Total return"])

            if np.isclose(fitted_return, benchmark_return, atol=1e-6, rtol=0):
                verdict = "approximately matched"
            elif fitted_return > benchmark_return:
                verdict = "outperformed"
            else:
                verdict = "trailed"

            st.markdown(
                f"**The mix fitted on 2015–21 returned {fitted_return:+.1%} "
                f"over 2022–24 and {verdict} the 60/40 benchmark "
                f"({benchmark_return:+.1%}).**"
            )

            summary_column, weights_column = st.columns([2.2, 1])
            summary_column.markdown("**Realised test-period performance**")
            summary_column.dataframe(
                summary.style.format("{:.2%}"),
                width="stretch",
            )
            weights_column.markdown("**Weights fitted on 2015–21**")
            weights_column.dataframe(
                backtest_allocation.to_frame().style.format({
                    "Allocation": "{:.1%}",
                }),
                width="stretch",
            )

            st.caption(
                "All three portfolios start at US$100 at the final "
                "available close of 2021. The benchmark starts with "
                "60% SPY and 40% TLT. These are buy-and-hold comparisons: "
                "weights drift and there is no periodic rebalancing. "
                "Results use adjusted prices in USD and exclude trading "
                "costs, taxes and currency conversion. This backtest uses "
                "a fixed historical period, independently of the "
                "estimation-window selector and scenario adjustments."
            )

    # --- Supporting information, kept out of the main chart area ---
    with st.expander("Data, assumptions and latest prices"):
        st.write("Latest adjusted closing prices (USD)")
        st.dataframe(prices.tail(), width="stretch")

        st.markdown("**Estimation basis**")
        st.write(
            f"Using {len(prices):,} shared daily price observations from "
            f"{prices.index.min():%d %b %Y} to {prices.index.max():%d %b %Y}. "
            "Estimated annual returns are mean daily returns × 252. "
            "Annual covariance is daily covariance × 252; annual "
            "volatility is the square root of portfolio variance. "
            "Sharpe is estimated annual excess return divided by "
            "annual volatility."
        )
        st.write(f"Calculations use {risk_free_note}. {scenario_note}")

        st.markdown("**Portfolio constraints and chart**")
        st.write(
            f"Optimised weights sum to 100%, with no short selling and "
            f"a maximum of {max_weight:.0%} in one asset. The frontier "
            "shows minimum estimated risk for each return target under "
            "that limit. Single-asset points represent 100% in one ETF "
            "and may exceed the limit."
        )
        st.write(
            "The dashed line labelled Capital Market Line illustrates "
            "risk-free cash combined with this constrained maximum-Sharpe "
            "mix. It stops at the star: borrowing is not included. It is "
            "a cash-and-portfolio illustration rather than an estimate "
            "of the economy-wide market portfolio."
        )
        st.write(
            "Chart returns include any scenario adjustment described "
            "above. The historical backtest uses its separate fixed "
            "training and test periods and a fixed 3% risk-free rate. "
            "Results are in USD and exclude transaction costs, taxes "
            "and currency conversion. Historical estimates are not forecasts."
        )

    # --- Compact source line ---
    st.caption(
        f"Source: Yahoo Finance via yfinance, adjusted prices in USD. "
        f"{prices.index.min():%b %Y}–{prices.index.max():%b %Y}; "
        f"{len(prices):,} shared daily observations. "
        f"Calculations use {risk_free_note}. {scenario_note} "
        "Estimates, not forecasts."
    )


# Only runs when you test this file on its own, not when app.py imports it
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
