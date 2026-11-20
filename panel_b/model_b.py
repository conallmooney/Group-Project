
"""Panel B: Interest-rate sensitivity analysis."""

import streamlit as st
import plotly.express as px

from market_data_b import (
    load_etf_prices,
    load_treasury_yields,
    prepare_regression_data,
)
from interest_rate_model_b import calculate_sensitivities


def render(scenario: dict) -> None:
    """Display Panel B using the selected economic scenario."""

    st.subheader("Interest Rate Sensitivity")

    frequency = st.selectbox(
        "Choose data frequency:",
        ["Monthly", "Weekly", "Daily"],
    )

    
    if st.button("Calculate Sensitivities"):
        with st.spinner("Loading market data and calculating sensitivities..."):
            prices = load_etf_prices()
            yields = load_treasury_yields()

            regression_data = prepare_regression_data(
                prices,
                yields,
                frequency=frequency,
            )

            sensitivities = calculate_sensitivities(regression_data)

            st.session_state["panel_b_sensitivities"] = sensitivities
            st.session_state["panel_b_frequency"] = frequency

    if (
        "panel_b_sensitivities" in st.session_state
        and st.session_state.get("panel_b_frequency") == frequency
    ):
        sensitivities = st.session_state["panel_b_sensitivities"]


        st.subheader("Regression Results")
        st.dataframe(sensitivities, use_container_width=True)

        chart_data = sensitivities.sort_values("Beta")

        fig = px.bar(
            chart_data,
            x="ETF",
            y="Beta",
            color="Beta",
            color_continuous_scale="RdYlGn",
            title="ETF Sensitivity to a 1 Percentage-Point Rise in Treasury Yields",
            labels={
                "ETF": "ETF",
                "Beta": "Estimated ETF Return (%)",
            },
        )

        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_zeroline=True,
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Source: Yahoo Finance ETF prices and FRED DGS10 Treasury yields. "
            "Sensitivities are historical regression estimates, not guaranteed forecasts."
        )
