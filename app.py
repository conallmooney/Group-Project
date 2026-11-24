"""Main application for the Rates, Risk & Returns dashboard.

Layout: a banner, the scenario buttons, four headline numbers, then tabs:
an Overview with one small chart per panel (they all update together when
the scenario changes), followed by one full-width tab per panel.

All four panels still run on every change, so the scenario flows through
them in order: Panel 2's betas feed Panel 3, and Panel 3's best portfolio
feeds Panel 4. The Overview and headline numbers are filled in last, from
what the panels have just calculated.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import style
from scenarios import get_scenario_names, get_scenario
from data import load_world_bank
from panel_a.model_a import render as render_panel_a
from panel_b.model_b import render as render_panel_b, get_sensitivities
from panel_c.model_c import render as render_panel_c
from panel_d.model_d import render as render_panel_d

st.set_page_config(
    page_title="Rates, Risk & Returns",
    page_icon="📈",
    layout="wide",
)

# One-line description of each scenario, shown under the buttons
SCENARIO_NOTES = {
    "Higher for longer": "Inflation stays sticky, so central banks keep rates high.",
    "Rate cuts": "Inflation settles near target and central banks cut rates.",
    "Stagflation": "An energy shock pushes inflation up while growth stalls.",
    "Custom": "Set your own rate shock, inflation and risk-free rate below.",
}

# Apply the shared appearance to the Overview and every panel tab.
style.apply_dashboard_style()

# --- Banner ---
st.markdown(
    f"""
    <div style="
        background: linear-gradient(
            110deg,
            {style.NAVY} 0%,
            #07536B 48%,
            #00889A 100%
        );
        border-radius: 14px;
        padding: 26px 30px;
        margin-bottom: 18px;
    ">
        <div style="
            color: #D6EBF2;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
        ">
            RATES, RISK &amp; RETURNS
        </div>
        <div style="
            color: #FFFFFF;
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 6px;
        ">
            How the 2021–23 inflation shock travelled
            from the world economy to your savings
        </div>
        <div style="
            color: #E3F3F8;
            font-size: 0.98rem;
            margin-top: 8px;
        ">
            Explore historical inflation, then see how
            rate scenarios affect investments and savings.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Scenario buttons ---
scenario_names = get_scenario_names()


def on_scenario_change():
    """Reset the shock slider when a scenario is selected."""
    selected = st.session_state["scenario_selector"]

    # Clicking the selected button again would clear it, so keep the last one
    if selected is None:
        st.session_state["scenario_selector"] = st.session_state.get(
            "last_scenario", scenario_names[0]
        )
        return

    selected_scenario = get_scenario(selected)
    st.session_state["panel_b_shock"] = float(selected_scenario["shock_pp"])
    st.session_state["custom_shock"] = float(selected_scenario["shock_pp"])


def on_custom_shock_change():
    """Update Panel B's slider when the Custom shock changes."""
    st.session_state["panel_b_shock"] = float(st.session_state["custom_shock"])


if "custom_shock" not in st.session_state:
    st.session_state["custom_shock"] = float(
        st.session_state.get("panel_b_shock", 0.0)
    )

with st.container(border=True, key="card_scenario"):
    scenario_name = st.segmented_control(
        "Economic scenario",
        scenario_names,
        default=scenario_names[0],
        key="scenario_selector",
        on_change=on_scenario_change,
        help="Sets the interest-rate shock, inflation and risk-free rate "
             "used by every panel.",
    )
    if scenario_name is None:
        scenario_name = st.session_state.get("last_scenario", scenario_names[0])
    st.session_state["last_scenario"] = scenario_name

    scenario = get_scenario(scenario_name)

    if scenario_name == "Custom":
        c1, c2, c3 = st.columns(3)
        scenario["shock_pp"] = c1.number_input(
            "Interest-rate shock (percentage points)",
            min_value=-3.0,
            max_value=3.0,
            step=0.25,
            key="custom_shock",
            on_change=on_custom_shock_change,
        )
        scenario["inflation"] = c2.number_input(
            "Inflation rate (%)",
            value=float(scenario["inflation"]),
            step=0.25,
        )
        scenario["rf"] = c3.number_input(
            "Risk-free rate (%)",
            value=float(scenario["rf"]),
            step=0.25,
        )

    st.caption(
        f"{SCENARIO_NOTES.get(scenario_name, '')} "
        f"10-year yield {float(scenario['shock_pp']):+.2f} pp · "
        f"inflation {float(scenario['inflation']):.2f}% · "
        f"risk-free rate {float(scenario['rf']):.2f}%. "
        "Applies to all four panels."
    )

st.session_state["scenario"] = scenario

# --- Headline numbers: filled in once the panels have run ---
headline_slots = [column.empty() for column in st.columns(4)]

# --- Tabs: an overview, then each panel full width ---
tab_overview, tab_a, tab_b, tab_c, tab_d = st.tabs([
    "Overview",
    "1 · The global shock",
    "2 · Who wins when rates move?",
    "3 · Build the best portfolio",
    "4 · What could it become?",
])

# Reserve the overview's four cards now; they are filled at the end
with tab_overview:
    st.markdown("#### All four panels at a glance")
    st.caption(
        "Switch the scenario above and watch them all change. "
        "Open a tab for each panel's full detail and controls."
    )
    top_left, top_right = st.columns(2, gap="medium")
    bottom_left, bottom_right = st.columns(2, gap="medium")
    cards = [
        column.container(
            border=True,
            key=f"card_overview_{index}",
        )
        for index, column in enumerate(
            (top_left, top_right, bottom_left, bottom_right),
            start=1,
        )
    ]


def safe_render(render, panel_name: str) -> None:
    """Run one panel; if it fails, show the error there and keep the others working."""
    try:
        render(scenario)
    except Exception as error:
        st.error(f"{panel_name} could not load: {error}")
        with st.expander("Technical details"):
            st.exception(error)


# Clear last run's shared results, so a panel that fails this time shows
# "not available" in the overview instead of an old, stale result.
# (Panel 3 already clears its own p3_result.)
for shared_key in ("asset_betas", "p4_result"):
    st.session_state.pop(shared_key, None)

with tab_a:
    safe_render(render_panel_a, "Panel 1")
with tab_b:
    safe_render(render_panel_b, "Panel 2")
with tab_c:
    safe_render(render_panel_c, "Panel 3")
with tab_d:
    safe_render(render_panel_d, "Panel 4")


# --- Overview cards ---
MINI_HEIGHT = 300


def mini_layout(fig: go.Figure) -> go.Figure:
    """Apply the shared appearance to the overview charts."""
    fig.update_layout(
        template="plotly_white+dashboard",
        height=MINI_HEIGHT,
        paper_bgcolor=style.SURFACE,
        plot_bgcolor=style.SURFACE,
        font=dict(size=14, color=style.INK),
        margin=dict(l=35, r=35, t=15, b=35),
        showlegend=False,
    )

    fig.update_xaxes(
        gridcolor=style.GRID,
        zerolinecolor=style.BORDER,
        tickfont=dict(size=13, color=style.MUTED),
        title_font=dict(size=13, color=style.MUTED),
        automargin=True,
    )

    fig.update_yaxes(
        gridcolor=style.GRID,
        zerolinecolor=style.BORDER,
        tickfont=dict(size=13, color=style.MUTED),
        title_font=dict(size=13, color=style.MUTED),
        automargin=True,
    )

    return fig


def card_header(card, number: str, title: str, headline: str) -> None:
    """Small label, panel name and the finding, at the top of a card."""
    card.caption(f"{number} · {title.upper()}")
    card.markdown(f"**{headline}**")


def card_footer(card, tab_name: str) -> None:
    """Show a subtle link-style instruction to the detailed panel."""
    panel_number = tab_name.split()[0]

    card.markdown(
        f'<p class="overview-footer">'
        f"Open Panel {panel_number} for the full detail →"
        f"</p>",
        unsafe_allow_html=True,
    )


def overview_panel_1(card) -> None:
    """The 2022 bubble chart, small and without controls."""
    world, _ = load_world_bank()
    year = 2022
    d = world[world["year"] == year].dropna(
        subset=["inflation", "gdp_growth", "gdp_usd"]
    )
    fig = px.scatter(
        d, x="inflation", y="gdp_growth", size="gdp_usd", color="region",
        hover_name="name", size_max=35,
        color_discrete_map=style.REGION_COLOURS,
        range_x=[-5, 20], range_y=[-15, 15],
        labels={"inflation": "Inflation (%)", "gdp_growth": "GDP growth (%)"},
    )
    card_header(card, "1", "The global shock",
                f"Inflation hit almost every economy at once in {year}")
    card.plotly_chart(mini_layout(fig), width="stretch", theme=None,
                      config={"displayModeBar": False})
    card.caption(
        f"Median inflation in {year}: {d['inflation'].median():.1f}%. "
        "History, so it doesn't change with the scenario."
    )
    card_footer(card, "1 · The global shock")


def overview_panel_2(card, shock: float) -> None:
    """Each ETF's estimated move under the scenario's rate shock."""
    sensitivities = get_sensitivities(
        st.session_state.get("panel_b_frequency_selector", "Monthly"),
        st.session_state.get("panel_b_start_year_selector", 2015),
    )
    # With no rate change, show each ETF's sensitivity (its move per +1 pp)
    # and say so clearly, rather than a blank chart of zeros
    no_change = shock == 0
    shown_shock = 1.0 if no_change else shock
    d = sensitivities.assign(Impact=sensitivities["Beta"] * shown_shock)
    d = d.sort_values("Impact")
    worst, best = d.iloc[0], d.iloc[-1]

    fig = go.Figure(go.Bar(
        x=d["Impact"], y=d["ETF"], orientation="h",
        marker=dict(
            color=[style.POSITIVE if v >= 0 else style.NEGATIVE for v in d["Impact"]],
            opacity=[0.35 if r2 < 0.10 else 1.0 for r2 in d["R_squared"]],
        ),
        text=[f"{v:+.1f}%" for v in d["Impact"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b>: %{x:+.1f}%<extra></extra>",
    ))
    if no_change:
        fig.update_xaxes(title="Move for a +1 pp rise in yields (%), for reference")
        headline = ("No interest-rate change in this scenario. For reference, a +1 pp "
                    f"rise would hit {worst['ETF']} most")
    else:
        fig.update_xaxes(title="Estimated ETF return (%)")
        direction = "Rising" if shock > 0 else "Falling"
        headline = (f"{direction} yields ({shock:+.2f} pp): "
                    f"{worst['ETF']} falls most, {best['ETF']} gains most")
    card_header(card, "2", "Who wins when rates move?", headline)
    card.plotly_chart(mini_layout(fig), width="stretch", theme=None,
                      config={"displayModeBar": False})
    note = "Faded bars: yields explain little of that ETF's moves (R² below 0.10)."
    if no_change:
        note = ("Bars show sensitivity (the move per +1 pp), not a prediction: "
                "this scenario has no rate change. " + note)
    card.caption(note)
    card_footer(card, "2 · Who wins when rates move?")


def overview_panel_3(card) -> None:
    """The best portfolio's weights and key numbers."""
    best = st.session_state.get("p3_result")
    if not best:
        card_header(card, "3", "Build the best portfolio", "No portfolio yet")
        card.info("Panel 3 needs at least three assets to build a portfolio.")
        card_footer(card, "3 · Build the best portfolio")
        return

    weights = pd.DataFrame({"Asset": best["tickers"], "Weight": best["weights"]})
    # Group holdings under 0.5% into "Other", so the donut still adds to 100%
    small = weights["Weight"] < 0.005
    if small.any() and weights.loc[small, "Weight"].sum() > 0:
        weights = pd.concat([
            weights[~small],
            pd.DataFrame({"Asset": ["Other"], "Weight": [weights.loc[small, "Weight"].sum()]}),
        ], ignore_index=True)
    else:
        weights = weights[~small]
    fig = px.pie(
        weights, names="Asset", values="Weight", hole=0.6,
        color="Asset", color_discrete_map={**style.ASSET_COLOURS, "Other": "#B0B7C0"},
    )
    fig.update_traces(textposition="inside", texttemplate="%{label}<br>%{percent:.0%}",
                      hovertemplate="%{label}: %{percent:.1%}<extra></extra>", sort=False)

    card_header(card, "3", "Build the best portfolio",
                f"The best mix: {best['expected_return']:.1%} a year "
                f"for {best['volatility']:.1%} risk")
    chart_column, numbers_column = card.columns([3, 2])
    chart_column.plotly_chart(mini_layout(fig), width="stretch", theme=None,
                              config={"displayModeBar": False})
    numbers_column.metric("Expected return", f"{best['expected_return']:.1%}")
    numbers_column.metric("Sharpe ratio", f"{best['sharpe']:.2f}")
    numbers_column.caption(f"Risk-free rate {best['risk_free_rate']:.2%}")
    card_footer(card, "3 · Build the best portfolio")


def overview_panel_4(card) -> None:
    """The saver's fan chart, exactly as Panel 4 last drew it."""
    result = st.session_state.get("p4_result")
    if not result:
        card_header(card, "4", "What could it become?", "No projection yet")
        card.info("Panel 4's projection will appear here.")
        card_footer(card, "4 · What could it become?")
        return

    x = list(range(result["years"] + 1))
    fan = result["fan"]
    fig = go.Figure([
        go.Scatter(x=x, y=fan["5"], mode="lines", line=dict(width=0), hoverinfo="skip"),
        go.Scatter(x=x, y=fan["95"], mode="lines", line=dict(width=0), fill="tonexty",
                   fillcolor="rgba(14,110,140,0.15)", hoverinfo="skip"),
        go.Scatter(x=x, y=fan["25"], mode="lines", line=dict(width=0), hoverinfo="skip"),
        go.Scatter(x=x, y=fan["75"], mode="lines", line=dict(width=0), fill="tonexty",
                   fillcolor="rgba(14,110,140,0.35)", hoverinfo="skip"),
        go.Scatter(x=x, y=fan["50"], mode="lines", line=dict(color=style.ACCENT, width=3),
                   name="Middle outcome", hovertemplate="Year %{x}: €%{y:,.0f}<extra></extra>"),
        go.Scatter(x=x, y=result["paid"], mode="lines",
                   line=dict(color=style.MUTED, width=2, dash="dash"),
                   name="Paid in", hovertemplate="Paid in: €%{y:,.0f}<extra></extra>"),
    ])
    fig.update_xaxes(title="Years from now")
    fig.update_yaxes(tickprefix="€", tickformat=",.0f", rangemode="tozero")

    headline = (f"After {result['years']} years, the middle outcome is "
                f"€{result['median']:,.0f} in today's money")
    card_header(card, "4", "What could it become?", headline)
    card.plotly_chart(mini_layout(fig), width="stretch", theme=None,
                      config={"displayModeBar": False})
    note = f"Adjusted for {result['inflation']:.1%} inflation a year."
    if result.get("chance") is not None:
        note = (f"{result['chance']:.0%} chance of reaching "
                f"€{result['goal']:,.0f}. " + note)
    card.caption(note)
    card_footer(card, "4 · What could it become?")


def fill_card(card, draw, *args) -> None:
    """Draw one overview card; if it fails, say so and keep the others."""
    try:
        draw(card, *args)
    except Exception as error:
        card.warning(f"This preview could not load: {error}")


shock = float(st.session_state.get("panel_b_shock", scenario.get("shock_pp", 0.0)))
fill_card(cards[0], overview_panel_1)
fill_card(cards[1], overview_panel_2, shock)
fill_card(cards[2], overview_panel_3)
fill_card(cards[3], overview_panel_4)


# --- Headline numbers ---
def fill_headline_numbers() -> None:
    """One key number per panel, so the whole story is visible at a glance."""
    # Panel 1: median inflation across countries in 2022
    try:
        world, _ = load_world_bank()
        median = world.groupby("year")["inflation"].median()
        headline_slots[0].metric(
            "Median inflation, 2022",
            f"{median[2022]:.1f}%",
            f"{median[2022] - median[2021]:+.1f} pts on 2021",
            delta_color="inverse",
            border=True,
        )
    except Exception:
        headline_slots[0].metric("Median inflation, 2022", "–", border=True)

    # Panel 2: the asset hit hardest by the scenario's rate move
    betas = st.session_state.get("asset_betas") or {}
    if betas:
        shown_shock = shock if shock != 0 else 1.0
        moves = {ticker: beta * shown_shock for ticker, beta in betas.items()}
        worst = min(moves, key=moves.get)
        label = (f"Biggest fall if yields move {shock:+.2f} pp" if shock != 0
                 else "No rate change. Most rate-sensitive (per +1 pp)")
        headline_slots[1].metric(label, f"{worst} {moves[worst]:+.1f}%", border=True)
    else:
        headline_slots[1].metric("Biggest fall when yields move", "–", border=True)

    # Panel 3: the best portfolio's expected return and Sharpe ratio
    best = st.session_state.get("p3_result")
    if best:
        headline_slots[2].metric(
            f"Best portfolio (Sharpe {best['sharpe']:.2f})",
            f"{best['expected_return']:.1%} a year",
            border=True,
        )
    else:
        headline_slots[2].metric("Best portfolio", "–", border=True)

    # Panel 4: middle outcome, with a separate goal-probability badge.
    saver = st.session_state.get("p4_result")

    if saver:
        with headline_slots[3].container(
            border=True,
            key="card_saver",
        ):
            st.metric(
                f"Saver after {saver['years']} years (today's €)",
                f"€{saver['median']:,.0f}",
            )

            if saver.get("chance") is not None:
                st.markdown(
                    f'<span class="probability-badge">'
                    f"{saver['chance']:.0%} chance of reaching "
                    f"€{saver['goal']:,.0f}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
    else:
        headline_slots[3].metric(
            "Saver's middle outcome",
            "–",
            border=True,
        )


fill_headline_numbers()

st.caption(
    "Data: World Bank World Development Indicators; Yahoo Finance ETF prices; "
    "FRED 10-year Treasury yield (DGS10). Estimates based on historical data, "
    "not forecasts or investment advice. MIS20080 group project, UCD 2026."
)