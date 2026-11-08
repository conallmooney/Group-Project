"""Panel 1: The global shock. Animated bubble chart with a spinning-globe view of the same data."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))  # find data.py and style.py
from data import load_world_bank
from style import REGION_COLOURS

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

# Axis ranges (kept here so the off-chart check uses the same numbers)
X_RANGE = [-5, 20]
Y_RANGES = {"gdp_growth": [-15, 15], "unemployment": [0, 30]}

IRELAND_NOTE = (
    "Ireland's GDP swings wildly because multinationals book large profits and "
    "intellectual property here, which inflates GDP without changing much for people "
    "living in Ireland. The CSO's modified GNI* strips these effects out and gives a "
    "truer picture of the Irish economy."
)


def complete_years(df: pd.DataFrame, share: float = 0.8) -> pd.DataFrame:
    """Keep only years where at least `share` of the usual number of countries reported."""
    counts = df.groupby("year")["name"].count()
    good_years = counts[counts >= share * counts.max()].index
    return df[df["year"].isin(good_years)]


def bubble_chart(plot_df: pd.DataFrame, y_col: str, y_label: str) -> go.Figure :
    """Gapminder-style animated bubble chart: inflation vs growth or unemployment.
    Bubble size = GDP in US dollars."""
    fig = px.scatter(
        plot_df, x="inflation", y=y_col, size="gdp_usd", color="region",
        hover_name="name", text="label",
        hover_data={"gdp_tn": ":.2f", "gdp_usd": False, "label": False},
        animation_frame="year", animation_group="name",
        size_max=55, range_x=X_RANGE, range_y=Y_RANGES[y_col],
        color_discrete_map=REGION_COLOURS,
        category_orders={"region": list(REGION_COLOURS)},
        labels={"inflation": "Inflation (%)", y_col: y_label, "region": "Region",
                "gdp_tn": "GDP (US$ trillion)"},
    )
    fig.update_traces(textposition="top center")
    return fig


def globe_chart(plot_df: pd.DataFrame) -> go.Figure :
    """Spinning 3D globe with each country coloured by its inflation rate."""
    fig = px.choropleth(
        plot_df, locations="economy", color="inflation", hover_name="name",
        animation_frame="year", projection="orthographic",
        color_continuous_scale="RdYlBu_r", range_color=[0, 15],
        labels={"inflation": "Inflation (%)"},
    )
    fig.update_geos(
        showocean=True, oceancolor="#E1EFF4",
        showcountries=True, countrycolor="white",
        showframe=False, projection_rotation=dict(lon=-10, lat=35),  # starts over Europe
    )
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0))
    return fig


def render(scenario: dict | None = None) -> None:
    """Draw Panel 1. It shows history, so it doesn't use the scenario."""
    st.subheader("Inflation hit almost every economy at once in 2022")
    df = load_world_bank()

    # --- Controls ---
    view = st.radio("View", ["Bubbles", "Globe"], horizontal=True)
    col1, col2, col3 = st.columns(3)
    y_label = col1.selectbox("Y-axis (bubbles view)", list(Y_OPTIONS),
                             disabled=view != "Bubbles")
    all_regions = sorted(df["region"].dropna().unique())
    regions = col2.multiselect("Regions", all_regions, default=all_regions)
    names = sorted(df["name"].unique())
    highlight = col3.selectbox("Highlight", names, index=names.index("Ireland"))

    # --- Filter the data for the chosen view ---
    y_col = Y_OPTIONS[y_label]
    if view == "Bubbles":
        needed = ["inflation", y_col, "gdp_usd"]
    else:
        needed = ["inflation"]
    plot_df = df[df["region"].isin(regions)].dropna(subset=needed).copy()
    if plot_df.empty:
        st.info("Pick at least one region to see the chart.")
        return
    plot_df = complete_years(plot_df)
    plot_df["label"] = plot_df["name"].where(plot_df["name"] == highlight, "")
    plot_df["gdp_tn"] = plot_df["gdp_usd"] / 1e12  # GDP in trillions, for the hover

    # --- Chart ---
    if view == "Bubbles":
        fig = bubble_chart(plot_df, y_col, y_label)
        st.caption("Bubble size = GDP in US dollars, so bigger bubbles are bigger economies. "
                   "Hover over a bubble to see its GDP.")
    else:
        fig = globe_chart(plot_df)
        st.caption("Drag the globe to spin it. Press ▶ to watch inflation spread in 2021–22.")
    st.plotly_chart(fig, width="stretch", theme=None)

    # --- Explain a year ---
    years = sorted(plot_df["year"].unique())
    year = st.select_slider("Explain a year", options=years,
                            value=2022 if 2022 in years else years[-1])
    that_year = plot_df[plot_df["year"] == year]
    high = (that_year["inflation"] > 5).sum()
    event = EVENTS.get(year, "No major event noted")
    st.markdown(f"**{year}: {event}.** {high} of {len(that_year)} "
                f"countries shown had inflation above 5%.")

    if view == "Bubbles":
        # A reference point for bubble size: the largest economy that year
        biggest = that_year.loc[that_year["gdp_usd"].idxmax()]
        st.caption(f"Largest bubble in {year}: {biggest['name']} "
                   f"(about US${biggest['gdp_tn']:.1f} trillion).")

        # Countries outside the bubble chart's axes, named so nothing is hidden
        y_lo, y_hi = Y_RANGES[y_col]
        off = that_year[
            (that_year["inflation"] < X_RANGE[0]) | (that_year["inflation"] > X_RANGE[1])
            | (that_year[y_col] < y_lo) | (that_year[y_col] > y_hi)
        ]
        if len(off) > 0:
            shown = ", ".join(off["name"].head(5))
            more = f" and {len(off) - 5} more" if len(off) > 5 else ""
            st.caption(f"Off the chart in {year}: {shown}{more}.")

    if highlight == "Ireland":
        with st.expander("Why does Ireland's GDP jump around?"):
            st.write(IRELAND_NOTE)

    st.caption("Source: World Bank World Development Indicators "
               "(FP.CPI.TOTL.ZG, NY.GDP.MKTP.KD.ZG, SL.UEM.TOTL.ZS, NY.GDP.MKTP.CD).")


# Only runs when you test this file on its own, not when app.py imports it
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()