
"""Main application for the Rates, Risk & Returns dashboard."""

import streamlit as st

from scenarios import get_scenario_names, get_scenario

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