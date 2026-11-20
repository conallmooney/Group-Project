
"""Main application for the Rates, Risk & Returns dashboard."""

import streamlit as st

from scenarios import get_scenario_names, get_scenario
from panel_b.model_b import render as render_panel_b

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


def on_scenario_change():
    """Reset the shock slider when a scenario is selected."""
    selected = st.session_state["scenario_selector"]
    selected_scenario = get_scenario(selected)

    st.session_state["panel_b_shock"] = float(
        selected_scenario["shock_pp"]
    )


scenario_name = st.selectbox(
    "Choose an economic scenario:",
    get_scenario_names(),
    key="scenario_selector",
    on_change=on_scenario_change,
)

scenario = get_scenario(scenario_name)

if scenario_name == "Custom":
    scenario["shock_pp"] = st.number_input(
        "Interest-rate shock (percentage points)",
        value=float(
            st.session_state.get(
                "panel_b_shock",
                scenario["shock_pp"],
            )
        ),
        step=0.25,
    )

    scenario["inflation"] = st.number_input(
        "Inflation rate (%)",
        value=float(scenario["inflation"]),
        step=0.25,
    )

    scenario["rf"] = st.number_input(
        "Risk-free rate (%)",
        value=float(scenario["rf"]),
        step=0.25,
    )

st.session_state["scenario"] = scenario


st.write("Selected scenario data:", scenario)

# Display Panel B.
render_panel_b(scenario)
