"""Panel 1: The global shock, an animated bubble chart of inflation vs growth."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))  # find data.py
from data import load_world_bank

# What happened in key years (shown under the chart)
EVENTS = {
    2008: "Global financial crisis",
    2009: "Great Recession: many economies shrink",
    2012: "Euro-area debt crisis",
    2020: "COVID-19 lockdowns",
    2021: "Economies reopen and supply chains snarl",
    2022: "Russia invades Ukraine, energy prices spike, the Fed and ECB start raising rates",
    2023: "Interest rates at their peak",
    2024: "Inflation cools and the first rate cuts arrive",
}

# Dropdown label -> column in the data
Y_OPTIONS = {"GDP growth (%)": "gdp_growth", "Unemployment (%)": "unemployment"}


def render(scenario: dict | None = None) -> None:
    """Draw Panel 1. It shows history, so it doesn't use the scenario."""
    st.subheader("Inflation hit almost every economy at once in 2022")
    df = load_world_bank()

    # --- Controls ---
    col1, col2, col3 = st.columns(3)
    y_label = col1.selectbox("Y-axis", list(Y_OPTIONS))
    all_regions = sorted(df["region"].dropna().unique())
    regions = col2.multiselect("Regions", all_regions, default=all_regions)
    names = sorted(df["name"].unique())
    highlight = col3.selectbox("Highlight", names, index=names.index("Ireland"))

    # --- Filter the data for the chart ---
    y_col = Y_OPTIONS[y_label]
    plot_df = df[df["region"].isin(regions)]
    plot_df = plot_df.dropna(subset=["inflation", y_col, "gdp_usd"]).copy()
    if plot_df.empty:
        st.info("Pick at least one region to see the chart.")
        return
    # Only the highlighted country gets a name label on the chart
    plot_df["label"] = plot_df["name"].where(plot_df["name"] == highlight, "")

    # --- Chart ---
    fig = px.scatter(
        plot_df, x="inflation", y=y_col, size="gdp_usd", color="region",
        hover_name="name", text="label",
        animation_frame="year", animation_group="name",
        size_max=55, range_x=[-5, 20],
        range_y=[-15, 15] if y_col == "gdp_growth" else [0, 30],
        labels={"inflation": "Inflation (%)", y_col: y_label, "region": "Region"},
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

    # --- Explain a year ---
    years = sorted(plot_df["year"].unique())
    year = st.select_slider("Explain a year", options=years,
                            value=2022 if 2022 in years else years[-1])
    that_year = plot_df[plot_df["year"] == year]
    high = (that_year["inflation"] > 5).sum()
    event = EVENTS.get(year, "No major event noted")
    st.markdown(f"**{year}: {event}.** {high} of {len(that_year)} "
                f"countries shown had inflation above 5%.")
    st.caption("Source: World Bank World Development Indicators "
               "(FP.CPI.TOTL.ZG, NY.GDP.MKTP.KD.ZG, SL.UEM.TOTL.ZS, NY.GDP.MKTP.CD).")


# Only runs when you test this file on its own, not when app.py imports it
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()