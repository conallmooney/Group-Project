
"""Panel B: Interest-rate sensitivity analysis."""

import streamlit as st
import plotly.express as px

from market_data_b import (
    load_etf_prices,
    load_treasury_yields,
    prepare_regression_data,
)
from interest_rate_model_b import (
    calculate_sensitivities,
    calculate_scenario_impacts,
)


def render(scenario: dict) -> None:
    """Display Panel B using the selected economic scenario."""

    st.subheader("Interest Rate Sensitivity")

    frequency = st.selectbox(
        "Choose data frequency:",
        ["Monthly", "Weekly", "Daily"],
    )


    start_year = st.selectbox(
        "Regression start year:",
        [2015, 2017, 2019, 2021],
        index=0,
    )


    
    if st.button("Calculate Sensitivities"):
        with st.spinner("Loading market data and calculating sensitivities..."):
            
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

            sensitivities = calculate_sensitivities(regression_data)

            st.session_state["panel_b_sensitivities"] = sensitivities
            st.session_state["panel_b_frequency"] = frequency
            st.session_state["panel_b_start_year"] = start_year


            # Share ETF interest-rate betas with Panel C.
            st.session_state["asset_betas"] = dict(
                zip(sensitivities["ETF"], sensitivities["Beta"])
            )

            st.write("Shared asset betas:", st.session_state["asset_betas"])


    
    if (
        "panel_b_sensitivities" in st.session_state
        and st.session_state.get("panel_b_frequency") == frequency
        and st.session_state.get("panel_b_start_year") == start_year
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


        st.subheader("Interest-Rate Shock Simulator")

        
        # Reset the slider when the economic scenario changes.
        scenario_shock = float(scenario["shock_pp"])

        if st.session_state.get("panel_b_scenario") != scenario:
            st.session_state["panel_b_shock"] = scenario_shock
            st.session_state["panel_b_scenario"] = scenario.copy()

        shock = st.slider(
            "Change in Treasury yields (percentage points)",
            min_value=-3.0,
            max_value=3.0,
            step=0.25,
            key="panel_b_shock",
        )


        impacts = calculate_scenario_impacts(
            sensitivities,
            shock,
        )

        st.dataframe(
            impacts[["ETF", "Beta", "Scenario_Impact"]],
            use_container_width=True,
        )

        impact_chart = px.bar(
            impacts.sort_values("Scenario_Impact"),
            x="ETF",
            y="Scenario_Impact",
            color="Scenario_Impact",
            color_continuous_scale="RdYlGn",
            title=f"Estimated ETF Impact of a {shock:+.2f} pp Yield Change",
            labels={
                "ETF": "ETF",
                "Scenario_Impact": "Estimated ETF Return (%)",
            },
        )

        impact_chart.update_layout(
            coloraxis_showscale=False,
        )

        st.plotly_chart(
            impact_chart,
            use_container_width=True,
        )

        st.caption(
            "Scenario impacts are linear extrapolations of historical "
            "regression sensitivities, not guaranteed forecasts."
        )

