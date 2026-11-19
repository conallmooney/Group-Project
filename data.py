"""Shared data loaders for the Rates, Risk & Returns dashboard.

Author: Ciara Feeney (Person A, data lead): World Bank loader, caching and backup CSV.
Teammates adding their own loaders here: add your name next to your function.
"""
from pathlib import Path
from datetime import datetime
import time 
import threading 
import pandas as pd
import streamlit as st
import wbgapi as wb

FALLBACK_DIR = Path(__file__).parent / "data" / "fallback"
WB_FALLBACK = FALLBACK_DIR / "world_bank.csv"

WB_SERIES = {
    "FP.CPI.TOTL.ZG": "inflation",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",
    "SL.UEM.TOTL.ZS": "unemployment",
    "NY.GDP.MKTP.CD": "gdp_usd",
}

REGION_NAMES = {
    "EAS": "East Asia & Pacific", "ECS": "Europe & Central Asia",
    "LCN": "Latin America & Caribbean", "MEA": "Middle East & North Africa",
    "NAC": "North America", "SAS": "South Asia", "SSF": "Sub-Saharan Africa",
}


def _fetch_series(code: str, start: int, end: int, tries: int = 3) -> pd.DataFrame:
    """Download one World Bank indicator, retrying if the API has a hiccup.

    Asking for one indicator at a time keeps each request small, which the
    World Bank API handles far more reliably than one large request.
    """
    for attempt in range(1, tries + 1):
        try:
            return wb.data.DataFrame(code, time=range(start, end + 1), skipAggs=True)
        except Exception:
            if attempt == tries:
                raise
            time.sleep(2)  # short pause, then try again


def _download_world_bank(start: int, end: int) -> pd.DataFrame:
    """Download the indicators one by one and reshape to one row per country per year."""
    frames = []
    for code, name in WB_SERIES.items():
        raw = _fetch_series(code, start, end)  # rows = countries, columns = YR2000 ...
        long = raw.reset_index().melt(id_vars="economy", var_name="year", value_name=name)
        long["year"] = long["year"].str.replace("YR", "").astype(int)
        frames.append(long.set_index(["economy", "year"]))
    tidy = pd.concat(frames, axis=1).reset_index()  # line the indicators up side by side

    # An indicator that came back completely empty counts as a failed download
    empty = [name for name in WB_SERIES.values() if tidy[name].isna().all()]
    if empty:
        raise ValueError(f"World Bank data is missing: {empty}")

    info = wb.economy.DataFrame(skipAggs=True)[["name", "region"]]
    info["region"] = info["region"].map(REGION_NAMES)
    tidy = tidy.merge(info, left_on="economy", right_index=True)
    return tidy.sort_values(["year", "name"]).reset_index(drop=True)


WB_TIMEOUT = 30  # seconds to wait for the World Bank before using the backup


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Downloading World Bank data...")
def _download_with_timeout(start: int, end: int) -> tuple[pd.DataFrame, str]:
    """Download in a background thread and give up after WB_TIMEOUT seconds.

    The thread is a daemon, so a stuck download can't stop the app from closing.
    Only successful downloads are cached: if this raises an error,
    Streamlit caches nothing and the backup is used instead.
    """
    result = {}

    def worker() -> None:
        try:
            result["df"] = _download_world_bank(start, end)
        except Exception as error:
            result["error"] = error

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(WB_TIMEOUT)  # wait at most WB_TIMEOUT seconds
    if thread.is_alive():
        raise TimeoutError(f"no reply within {WB_TIMEOUT} seconds")
    if "error" in result:
        raise result["error"]
    fetched = datetime.now().strftime("%d %b %Y, %H:%M")
    return result["df"], f"Live from the World Bank API, fetched {fetched}."


def load_world_bank(start: int = 2000, end: int = 2024) -> tuple[pd.DataFrame, str]:
    """Return tidy World Bank data plus a note saying where it came from.

    Tries the live API for up to WB_TIMEOUT seconds. If it fails, is too slow,
    or returns partial data, falls back to the saved CSV snapshot and says so.
    After one failure, the rest of the session uses the backup straight away.
    """
    if "wb_offline" not in st.session_state:
        try:
            return _download_with_timeout(start, end)
        except Exception as error:
            st.session_state["wb_offline"] = (
                str(error) or f"no reply within {WB_TIMEOUT} seconds")
    saved = datetime.fromtimestamp(WB_FALLBACK.stat().st_mtime).strftime("%d %b %Y")
    note = (f"World Bank API unavailable ({st.session_state['wb_offline']}). "
            f"Showing the saved snapshot from {saved}.")
    return pd.read_csv(WB_FALLBACK), note

def save_snapshot() -> None:
    """Download fresh data and save it as the backup CSV."""
    FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    _download_world_bank(2000, 2024).to_csv(WB_FALLBACK, index=False)
    print(f"Saved {WB_FALLBACK}")


if __name__ == "__main__":
    save_snapshot()