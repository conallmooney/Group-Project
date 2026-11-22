
"""Panel B: Interest-rate sensitivity analysis."""

import streamlit as st
import plotly.express as px
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


    
    if (
        "panel_b_sensitivities" in st.session_state
        and st.session_state.get("panel_b_frequency") == frequency
        and st.session_state.get("panel_b_start_year") == start_year
    ):

        sensitivities = st.session_state["panel_b_sensitivities"]


        st.subheader("Regression Results")
        st.dataframe(sensitivities, use_container_width=True)

        chart_data = sensitivities.sort_values("Beta")
        
        chart_data = chart_data.copy()

        chart_data["Direction"] = chart_data["Beta"].apply(
            lambda beta: "Positive" if beta >= 0 else "Negative"
        )
        most_negative = chart_data.iloc[0]
        most_positive = chart_data.iloc[-1]

        st.markdown(
            f"**{most_negative['ETF']} has the strongest negative "
            f"interest-rate sensitivity ({most_negative['Beta']:.2f}).**"
        )

        fig = px.bar(
            chart_data,
            x="ETF",
            y="Beta",
            color="Direction",
            color_discrete_map={
                "Positive": style.POSITIVE,
                "Negative": style.NEGATIVE,
            },
            hover_data={
                "Beta": ":.2f",
                "R_squared": ":.3f",
                "Observations": True,
            },
            title="ETF Sensitivity to a 1 Percentage-Point Rise in Treasury Yields",
            labels={
                "ETF": "ETF",
                "Beta": "Estimated ETF Return (%)",
            },
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Source: Yahoo Finance ETF prices and FRED DGS10 Treasury yields. "
            "Sensitivities are historical regression estimates, not guaranteed forecasts."
        )

        st.caption(
            f"Analysis period: {start_year}–2024 | "
            f"Frequency: {frequency} | "
            f"Most positive sensitivity: {most_positive['ETF']} "
            f"({most_positive['Beta']:+.2f})"
        )

        st.caption(
            "R² measures how much of an ETF's historical return variation "
            "is explained by Treasury yield changes. A low R² suggests "
            "that other factors are important."
        )

        st.subheader("Interest-Rate Shock Simulator")

        
        def on_shock_change():
            """Keep the Custom scenario and slider in sync."""
            shock_value = float(st.session_state["panel_b_shock"])

            st.session_state["scenario_selector"] = "Custom"
            st.session_state["custom_shock"] = shock_value

        # Initialise the slider if no value exists yet.
        if "panel_b_shock" not in st.session_state:
            st.session_state["panel_b_shock"] = float(
                scenario["shock_pp"]
            )

        shock = st.slider(
            "Change in Treasury yields (percentage points)",
            min_value=-3.0,
            max_value=3.0,
            step=0.25,
            key="panel_b_shock",
            on_change=on_shock_change,
        )



        impacts = calculate_scenario_impacts(
            sensitivities,
            shock,
        )

        st.dataframe(
            impacts[["ETF", "Beta", "Scenario_Impact"]],
            use_container_width=True,
        )
        
        impacts = impacts.copy()

        impacts["Direction"] = impacts["Scenario_Impact"].apply(
            lambda impact: "Positive" if impact >= 0 else "Negative"
        )

        impact_chart = px.bar(
            impacts.sort_values("Scenario_Impact"),
            x="ETF",
            y="Scenario_Impact",
            color="Direction",
            color_discrete_map={
                "Positive": style.POSITIVE,
                "Negative": style.NEGATIVE,
            },
            title=f"Estimated ETF Impact of a {shock:+.2f} pp Yield Change",
            labels={
                "ETF": "ETF",
                "Scenario_Impact": "Estimated ETF Return (%)",
            },
        )

        impact_chart.update_layout(showlegend=False)

        st.plotly_chart(
            impact_chart,
            use_container_width=True,
        )

        st.caption(
            "Scenario impacts are linear extrapolations of historical "
            "regression sensitivities, not guaranteed forecasts."
        )

