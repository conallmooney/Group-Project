
"""Panel B: Interest-rate sensitivity analysis."""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import style

from market_data_b import (
    load_etf_prices,
    load_treasury_yields,
    prepare_regression_data,
)
from interest_rate_model_b import (
    calculate_sensitivities,
    calculate_scenario_impacts,
)


@st.cache_data(ttl=60 * 60 * 24)
def get_sensitivities(frequency: str, start_year: int):
    """Estimate ETF sensitivities using historical market data."""

    start_date = f"{start_year}-01-01"
    end_date = "2025-01-01"

    prices = load_etf_prices(
        start=start_date,
        end=end_date,
    )

    yields = load_treasury_yields(
        start=start_date,
        end=end_date,
    )

    regression_data = prepare_regression_data(
        prices,
        yields,
        frequency=frequency,
    )

    return calculate_sensitivities(regression_data)


def render(scenario: dict) -> None:
    """Render the compact interest-rate sensitivity panel."""

    st.caption("02 · WHO WINS WHEN RATES MOVE?")

    # Synchronise the slider with the shared scenario.
    if "panel_b_shock" not in st.session_state:
        st.session_state["panel_b_shock"] = float(
            scenario.get("shock_pp", 0.0)
        )

    def on_shock_change():
        shock_value = float(st.session_state["panel_b_shock"])

        st.session_state["scenario_selector"] = "Custom"
        st.session_state["custom_shock"] = shock_value

    # All three controls on one row.
    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        frequency = st.selectbox(
            "Frequency",
            ["Monthly", "Weekly", "Daily"],
            key="panel_b_frequency_selector",
        )

    with col2:
        start_year = st.selectbox(
            "Estimated from",
            [2015, 2017, 2019, 2021],
            key="panel_b_start_year_selector",
        )

    with col3:
        shock = st.slider(
            "Yield change (pp)",
            min_value=-3.0,
            max_value=3.0,
            step=0.25,
            key="panel_b_shock",
            on_change=on_shock_change,
        )

    # Calculate automatically, with caching.
    try:
        with st.spinner("Estimating ETF sensitivities..."):
            sensitivities = get_sensitivities(
                frequency,
                start_year,
            )

    except Exception as exc:
        st.error("Unable to calculate ETF sensitivities.")
        st.caption(str(exc))
        return

    if sensitivities.empty:
        st.warning("No regression results available.")
        return

    # Share betas with Panel C.
    st.session_state["asset_betas"] = dict(
        zip(
            sensitivities["ETF"],
            sensitivities["Beta"],
        )
    )

    impacts = calculate_scenario_impacts(
        sensitivities,
        shock,
    ).copy()

    # Ensure R-squared is available for chart styling.
    if "R_squared" not in impacts.columns:
        impacts = impacts.merge(
            sensitivities[["ETF", "R_squared"]],
            on="ETF",
            how="left",
        )

    impacts = impacts.sort_values("Scenario_Impact")

    worst = impacts.iloc[0]
    best = impacts.iloc[-1]

    # Dynamic, sign-aware headline.
    if shock == 0:
        headline = "No interest-rate change selected"

    elif worst["Scenario_Impact"] < 0 and best["Scenario_Impact"] > 0:
        direction = "Rising" if shock > 0 else "Falling"

        headline = (
            f"{direction} yields: "
            f"{best['ETF']} gains most, "
            f"{worst['ETF']} falls most"
        )

    else:
        direction = "Rising" if shock > 0 else "Falling"

        headline = (
            f"{direction} yields: "
            f"{best['ETF']} performs best, "
            f"{worst['ETF']} performs worst"
        )

    st.markdown(f"**{headline}**")

    # Green = gain, red = loss.
    # Low R² bars use lighter colours to indicate weak explanatory power.

    colors = [
    style.POSITIVE if impact >= 0 else style.NEGATIVE
    for impact in impacts["Scenario_Impact"]
]

    opacities = [
    0.35 if pd.notna(r2) and r2 < 0.10 else 1.0
    for r2 in impacts["R_squared"]
]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=impacts["Scenario_Impact"],
            y=impacts["ETF"],
            orientation="h",
            marker=dict(
            color=colors,
            opacity=opacities,
            ),
            text=[
                f"{value:+.1f}%"
                for value in impacts["Scenario_Impact"]
            ],
            textposition="outside",
            cliponaxis=False,
            customdata=impacts[
                ["Beta", "R_squared"]
            ].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Estimated impact: %{x:+.2f}%<br>"
                "Beta: %{customdata[0]:+.2f}<br>"
                "R²: %{customdata[1]:.3f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=320,
        margin=dict(l=10, r=50, t=10, b=35),
        showlegend=False,
        bargap=0.20,
        xaxis_title="Estimated ETF return (%)",
        yaxis_title=None,
        font=dict(size=11),
    )

    fig.update_xaxes(
        zeroline=True,
        zerolinecolor=style.MUTED,
        showgrid=True,
        gridcolor=style.GRID,
    )

    fig.update_yaxes(
        autorange=True,
        showgrid=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # One concise scenario takeaway.
    if shock == 0:
        st.info(
            "Move the yield slider to estimate "
            "how each ETF responds."
        )
    else:
        st.info(
            f"For a {shock:+.2f} pp change in the "
            f"10-year Treasury yield, the model estimates "
            f"**{best['ETF']} at "
            f"{best['Scenario_Impact']:+.1f}%** "
            f"and **{worst['ETF']} at "
            f"{worst['Scenario_Impact']:+.1f}%**."
        )

    # One combined table, hidden by default.
    with st.expander("Regression details"):

        details = sensitivities.merge(
            impacts[["ETF", "Scenario_Impact"]],
            on="ETF",
            how="left",
        )

        details = details.rename(
            columns={
                "Alpha": "Alpha (%)",
                "Beta": "Move per +1 pp (%)",
                "R_squared": "R²",
                "Observations": "Observations",
                "Scenario_Impact": "Scenario impact (%)",
            }
        )

        st.dataframe(
            details,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Alpha (%)": st.column_config.NumberColumn(
                    format="%.2f"
                ),
                "Move per +1 pp (%)": st.column_config.NumberColumn(
                    format="%+.2f"
                ),
                "R²": st.column_config.NumberColumn(
                    format="%.3f"
                ),
                "Scenario impact (%)": st.column_config.NumberColumn(
                    format="%+.2f"
                ),
            },
        )

        st.caption(
            "Beta measures the estimated ETF return (%) "
            "associated with a +1 percentage-point yield "
            "change. R² measures the proportion of return "
            "variation explained by the regression."
        )

    st.caption(
        f"Source: Yahoo Finance ETF prices; FRED DGS10. "
        f"{frequency} data, {start_year}–2024. "
        "Faded bars: R² below 0.10, indicating weak "
        "explanatory power. Linear historical estimates, "
        "not forecasts."
    )
