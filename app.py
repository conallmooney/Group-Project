
"""Main application for the Rates, Risk & Returns dashboard."""

import streamlit as st

from scenarios import get_scenario_names, get_scenario
from panel_a.model_a import render as render_panel_a
from panel_b.model_b import render as render_panel_b
from panel_c.model_c import render as render_panel_c
from panel_d.model_d import render as render_panel_d

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

    st.session_state["custom_shock"] = float(
        selected_scenario["shock_pp"]
    )


if "custom_shock" not in st.session_state:
    st.session_state["custom_shock"] = float(
        st.session_state.get("panel_b_shock", 0.0)
    )

scenario_name = st.selectbox(
    "Choose an economic scenario:",
    get_scenario_names(),
    key="scenario_selector",
    on_change=on_scenario_change,
)

scenario = get_scenario(scenario_name)

if scenario_name == "Custom":
    
    def on_custom_shock_change():
        """Update Panel B's slider when the Custom shock changes."""
        st.session_state["panel_b_shock"] = float(
            st.session_state["custom_shock"]
        )

    scenario["shock_pp"] = st.number_input(
        "Interest-rate shock (percentage points)",
        min_value=-3.0,
        max_value=3.0,
        step=0.25,
        key="custom_shock",
        on_change=on_custom_shock_change,
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


# Four-panel dashboard layout

st.divider()

top_left, top_right = st.columns(2, gap="large")

with top_left:
    with st.container(border=True):
        st.subheader("01 · Global Economy")
        render_panel_a(scenario)

with top_right:
    with st.container(border=True):
        st.subheader("02 · Interest Rate Sensitivity")
        render_panel_b(scenario)

bottom_left, bottom_right = st.columns(2, gap="large")

with bottom_left:
    with st.container(border=True):
        st.subheader("03 · Portfolio Optimiser")
        render_panel_c(scenario)

with bottom_right:
    with st.container(border=True):
        st.subheader("04 · Savings Simulation")
        render_panel_d(scenario)