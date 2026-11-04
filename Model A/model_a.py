import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

# Lets this file find data.py in the main folder
sys.path.append(str(Path(__file__).resolve().parents[1]))
from data import load_world_bank

df = load_world_bank()
plot_df = df.dropna(subset=["inflation", "gdp_growth", "gdp_usd"])

fig = px.scatter(plot_df, x="inflation", y="gdp_growth", size="gdp_usd",
                 color="region", hover_name="name",
                 animation_frame="year", animation_group="name",
                 size_max=55, range_x=[-5, 20], range_y=[-15, 15])
st.plotly_chart(fig)