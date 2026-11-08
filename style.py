"""Shared look for every chart in the dashboard. Import this before making a chart."""
import plotly.graph_objects as go
import plotly.io as pio

# Core colours
INK = "#13202C"       # main text
MUTED = "#5A6878"     # axis labels, captions
GRID = "#E8ECF0"      # gridlines
ACCENT = "#0E6E8C"    # the dashboard's main colour
POSITIVE = "#2E8F62"  # gains (Panel 2 bars)
NEGATIVE = "#C9473F"  # losses (Panel 2 bars)

# Panel 1: one fixed colour per region, so colours never shift when filtering
REGION_COLOURS = {
    "Europe & Central Asia": "#D99A1A",
    "North America": "#0E6E8C",
    "Latin America & Caribbean": "#2E9E6A",
    "East Asia & Pacific": "#D2504A",
    "South Asia": "#8E5AC8",
    "Sub-Saharan Africa": "#3BA7C9",
    "Middle East & North Africa": "#8C6D46",
}

# Panel 3: one fixed colour per asset
ASSET_COLOURS = {
    "SPY": ACCENT, "TLT": "#2E9E6A", "GLD": "#D99A1A",
    "XLE": "#C9473F", "XLU": "#3BA7C9",
}

# One Plotly template that every chart uses automatically
pio.templates["dashboard"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Source Sans Pro, sans-serif", size=13, color=INK),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[ACCENT, "#D99A1A", "#2E9E6A", "#D2504A", "#8E5AC8", "#3BA7C9"],
        xaxis=dict(gridcolor=GRID, zerolinecolor="#C9D1D9", linecolor=GRID,
                   title_font=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, zerolinecolor="#C9D1D9", linecolor=GRID,
                   title_font=dict(color=MUTED)),
        legend=dict(title_font=dict(color=MUTED)),
        margin=dict(l=40, r=20, t=30, b=40),
    )
)
pio.templates.default = "plotly_white+dashboard"