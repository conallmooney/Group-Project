"""Shared data loaders for the Rates, Risk & Returns dashboard."""
from pathlib import Path

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


def _download_world_bank(start: int, end: int) -> pd.DataFrame:
    """Download the indicators and reshape to one row per country per year."""
    raw = wb.data.DataFrame(list(WB_SERIES), time=range(start, end + 1), skipAggs=True)
    long = raw.reset_index().melt(id_vars=["economy", "series"],
                                  var_name="year", value_name="value")
    long["year"] = long["year"].str.replace("YR", "").astype(int)
    tidy = long.pivot_table(index=["economy", "year"], columns="series",
                            values="value").reset_index()
    tidy = tidy.rename(columns=WB_SERIES)
    missing = [col for col in WB_SERIES.values() if col not in tidy.columns]
    if missing or tidy.empty:
        raise ValueError(f"World Bank data is missing: {missing}")
    info = wb.economy.DataFrame(skipAggs=True)[["name", "region"]]
    info["region"] = info["region"].map(REGION_NAMES)
    tidy = tidy.merge(info, left_on="economy", right_index=True)
    return tidy.sort_values(["year", "name"]).reset_index(drop=True)


@st.cache_data(ttl=60 * 60 * 24)  # re-download at most once a day
def load_world_bank(start: int = 2000, end: int = 2024) -> pd.DataFrame:
    """Return tidy World Bank data, or the saved CSV if the API is down."""
    try:
        return _download_world_bank(start, end)
    except Exception as error:
        st.warning(f"World Bank API unavailable ({error}). Showing saved data.")
        return pd.read_csv(WB_FALLBACK)


def save_snapshot() -> None:
    """Download fresh data and save it as the backup CSV."""
    FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    _download_world_bank(2000, 2024).to_csv(WB_FALLBACK, index=False)
    print(f"Saved {WB_FALLBACK}")


if __name__ == "__main__":
    save_snapshot()