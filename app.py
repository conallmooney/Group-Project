
"""Main application for the Rates, Risk & Returns dashboard."""

import streamlit as st

from scenarios import get_scenario_names, get_scenario

from market_data_b import (
    load_etf_prices,
    load_treasury_yields,
    prepare_regression_data,
)
from interest_rate_model_b import calculate_sensitivities

st.set_page_config(
    page_title="Rates, Risk & Returns",
    page_icon="📈",
    layout="wide",
)

st.title("Rates, Risk & Returns")

st.write(
    "Explore how interest rate changes affect "
    "financial markets, investment portfolios, "
    "and future savings."
)


st.subheader("Macroeconomic Scenario")

scenario_name = st.selectbox(
    "Choose an economic scenario:",
    get_scenario_names()
)

scenario = get_scenario(scenario_name)

if scenario_name == "Custom":
        scenario["shock_pp"] = st.number_input(
        "Interest-rate shock (percentage points)",
        value=float(scenario["shock_pp"]),
        step=0.25
    )    
        
        scenario["inflation"] = st.number_input(
        "Inflation rate (%)",
        value=float(scenario["inflation"]),
        step=0.25
    )
        
        scenario["rf"] = st.number_input(
        "Risk-free rate (%)",
        value=float(scenario["rf"]),
        step=0.25
    )

st.write("Selected scenario data:", scenario)


st.subheader("Interest Rate Sensitivity")

frequency = st.selectbox(
    "Choose data frequency:",
    ["Monthly", "Weekly", "Daily"],
)

st.write("Selected frequency:", frequency)


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

    st.subheader("Regression Results")
    st.dataframe(sensitivities, use_container_width=True)
