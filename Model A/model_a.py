import wbgapi as wb
import pandas as pd
import plotly.express as px
import streamlit as st

# World Bank codes -> the column names we want
SERIES = {
    "FP.CPI.TOTL.ZG": "inflation",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",
    "SL.UEM.TOTL.ZS": "unemployment",
    "NY.GDP.MKTP.CD": "gdp_usd",
}

# Region codes from the World Bank -> readable names
REGION_NAMES = {
    "EAS": "East Asia & Pacific", "ECS": "Europe & Central Asia",
    "LCN": "Latin America & Caribbean", "MEA": "Middle East & North Africa",
    "NAC": "North America", "SAS": "South Asia", "SSF": "Sub-Saharan Africa",
}

# 1. Download: rows = (country, measure), columns = YR2000 ... YR2024
raw = wb.data.DataFrame(list(SERIES), time=range(2000, 2025), skipAggs=True)

# 2. Melt: turn the year columns into rows -> (country, measure, year, value)
long = raw.reset_index().melt(id_vars=["economy", "series"],
                              var_name="year", value_name="value")
long["year"] = long["year"].str.replace("YR", "").astype(int)

# 3. Pivot: turn the measures into columns -> one row per country per year
tidy = long.pivot_table(index=["economy", "year"], columns="series",
                        values="value").reset_index()
tidy = tidy.rename(columns=SERIES)

# 4. Add each country's name and region
info = wb.economy.DataFrame(skipAggs=True)[["name", "region"]]
info["region"] = info["region"].map(REGION_NAMES)
tidy = tidy.merge(info, left_on="economy", right_index=True)

# 5. Keep only rows the chart can draw
tidy = tidy.dropna(subset=["inflation", "gdp_growth", "gdp_usd"]).sort_values("year")

# Quick checks: how many countries have data in each year?
print(tidy.head())
print(tidy.groupby("year")["economy"].count())

# 6. First version of the bubble chart
fig = px.scatter(tidy, x="inflation", y="gdp_growth", size="gdp_usd",
                 color="region", hover_name="name",
                 animation_frame="year", animation_group="name",
                 size_max=55, range_x=[-5, 20], range_y=[-15, 15])
st.plotly_chart(fig)