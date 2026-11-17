"""Panel 3: Build the best portfolio. Portfolio optimiser and historical backtest."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))  # find data.py and style.py
from style import ASSET_COLOURS

# Default assets used to build the portfolio
DEFAULT_TICKERS = ["SPY", "TLT", "GLD", "XLE", "XLU"]

# Ticker -> description shown to the user
ASSET_NAMES = {
    "SPY": "US shares",
    "TLT": "Long-term US government bonds",
    "GLD": "Gold",
    "XLE": "US energy shares",
    "XLU": "US utilities shares",
}


def render(scenario: dict | None = None) -> None:
    """Draw Panel 3. Start with asset selection before adding calculations."""
    st.subheader("Build a portfolio across shares, bonds and gold")

    # --- Controls ---
    tickers = st.multiselect(
        "Choose your assets",
        options=DEFAULT_TICKERS,
        default=DEFAULT_TICKERS,
        format_func=lambda ticker: f"{ticker} — {ASSET_NAMES[ticker]}",
        key="p3_tickers",
    )

    if len(tickers) < 3:
        st.info("Choose at least three assets to build a portfolio.")
        return

    # --- Portfolio overview ---
    st.write(f"You have selected {len(tickers)} assets.")

    st.caption(
        "The portfolio optimiser will compare historical returns and risk "
        "to find a mix of these assets."
    )


# Only runs when you test this file on its own, not when app.py imports it
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
