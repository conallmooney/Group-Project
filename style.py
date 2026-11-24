"""Shared colours and chart styling for the dashboard.

Author: Ciara Feeney (Person A): original colours, colour maps and Plotly template.
Theme: navy, teal and gold, with white cards on a pale blue page.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Core colours
NAVY = "#102D50"       # banner and headings
INK = NAVY            # main text
MUTED = "#435B74"      # secondary text and axis labels
ACCENT = "#008C9E"     # teal controls and chart lines
GOLD = "#DDA51A"       # portfolio highlights
POSITIVE = "#238457"   # gains and favourable comparisons
NEGATIVE = "#D43B36"   # losses and unfavourable comparisons

# Backgrounds and borders
PAGE = "#E4EEF6"       # slightly stronger blue-grey page background
PAGE_END = "#D5E7F1"   # more visible blue at the gradient's end
SURFACE = "#FFFFFF"    # keep cards and charts white
BORDER = "#B8CEDF"     # clearer separation between cards and page
GRID = "#E8EFF5"       # chart gridlines

# Savings chart: shaded ranges containing 90% and 50% of simulated outcomes
FAN_OUTER = "rgba(0,140,158,0.17)"
FAN_INNER = "rgba(0,140,158,0.38)"

# Panel 1: fixed region colours prevent changes when filtering
REGION_COLOURS = {
    "Europe & Central Asia": GOLD,
    "North America": ACCENT,
    "Latin America & Caribbean": "#2E9E6A",
    "East Asia & Pacific": "#D2504A",
    "South Asia": "#8E5AC8",
    "Sub-Saharan Africa": "#3BA7C9",
    "Middle East & North Africa": "#8C6D46",
}

# Fixed asset colours identify holdings consistently across panels
ASSET_COLOURS = {
    "SPY": ACCENT, "TLT": "#2E9E6A", "GLD": GOLD,
    "XLE": NEGATIVE, "XLU": "#3BA7C9", "QQQ": "#9254D8",
    "IWM": "#D2504A", "EFA": "#8C6D46",
}


def apply_dashboard_style() -> None:
    """Apply page and card styling once, after app.py sets page configuration."""
    st.markdown(
        f"""
        <style>
        /* Pale page gradient behind the white cards. */
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(
                135deg, {PAGE} 0%, #ECF4F9 48%, {PAGE_END} 100%
            );
        }}
        [data-testid="stHeader"] {{ background: transparent; }}

        /* Named containers use keys beginning with card_. */
        [class*="st-key-card_"] {{
            background-color: {SURFACE};
            border-radius: 12px;
        }}
        [data-testid="stMetric"] {{
            background-color: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 14px 16px;
        }}
        [data-testid="stPlotlyChart"] {{
            background-color: {SURFACE};
            border-radius: 10px;
        }}

        /* Slightly stronger colour for Streamlit's comparison badges. */
        [data-testid="stMetricDelta"] {{
            filter: saturate(1.25);
        }}

        /* Stronger findings and metric labels improve readability. */
        [class*="st-key-card_overview_"]
        [data-testid="stMarkdownContainer"] strong {{
            color: {INK};
            font-size: 1.05rem;
            font-weight: 700;
        }}

        [data-testid="stMetricValue"] {{
            font-weight: 700;
        }}

        [data-testid="stMetricLabel"] p {{
            font-size: 0.95rem;
            font-weight: 600;
        }}

        /* Avoid extra boxes inside the portfolio overview card. */
        .st-key-card_overview_3 [data-testid="stMetric"] {{
            background: transparent;
            border: none;
            padding: 0;
        }}

        /* Readable navigation and navy overview footers. */
        .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
        .stTabs [data-baseweb="tab"] {{ padding: 10px 18px; }}
        .stTabs [data-baseweb="tab"] p {{
            font-size: 1rem;
            font-weight: 600;
        }}
        .overview-footer {{
            color: {NAVY};
            font-size: 0.8rem;
            font-weight: 500;
            line-height: 1.4;
            margin: 0;
        }}
        /* Keep the savings value and probability inside one white card. */
        .st-key-card_saver [data-testid="stMetric"] {{
            background: transparent;
            border: none;
            padding: 0;
        }}

        .probability-badge {{
            display: inline-block;
            background-color: #DDF1E4;
            color: #19643F;
            border: 1px solid #C1E2CC;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 0.8rem;
            font-weight: 600;
            line-height: 1.3;
            margin-top: 6px;
        }}
        /* Give metric change badges the same outline and rounded shape. */
        [data-testid="stMetricDelta"] {{
            border: 1px solid currentColor;
            border-radius: 6px;
            padding: 4px 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# One Plotly template gives every chart matching backgrounds and labels.
pio.templates["dashboard"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Source Sans Pro, sans-serif", size=13, color=INK),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=[ACCENT, GOLD, "#2E9E6A", "#D2504A", "#8E5AC8", "#3BA7C9"],
        xaxis=dict(
            gridcolor=GRID, zerolinecolor=BORDER, linecolor=BORDER,
            title_font=dict(color=MUTED), tickfont=dict(color=MUTED),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor=GRID, zerolinecolor=BORDER, linecolor=BORDER,
            title_font=dict(color=MUTED), tickfont=dict(color=MUTED),
            automargin=True,
        ),
        geo=dict(bgcolor=SURFACE),  # white space around the globe
        legend=dict(font=dict(color=INK), title_font=dict(color=MUTED)),
        margin=dict(l=40, r=20, t=30, b=40),
    )
)
pio.templates.default = "plotly_white+dashboard"