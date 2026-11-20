"""Shared data loaders for the Rates, Risk & Returns dashboard."""
from pathlib import Path

import pandas as pd
import streamlit as st
import wbgapi as wb
import yfinance as yf

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


# --- ETF prices for the portfolio panel ---

@st.cache_data(ttl=60 * 60 * 24)
def load_prices(
    tickers: tuple[str, ...],
    start: str = "2015-01-01",
) -> pd.DataFrame:
    """Return adjusted daily ETF prices, using a saved CSV if downloading fails."""
    if not tickers:
        raise ValueError("Choose at least one asset.")

    fallback_path = FALLBACK_DIR / "etf_prices.csv"

    try:
        downloaded = yf.download(
            tickers=list(tickers),
            start=start,
            auto_adjust=True,
            progress=False,
        )

        if downloaded is None or downloaded.empty:
            raise ValueError("No prices were downloaded.")

        prices = downloaded["Close"].copy()
        prices = prices.reindex(columns=list(tickers))
        prices = prices.dropna(how="all")

        missing = prices.columns[prices.isna().all()].tolist()
        if missing:
            raise ValueError(f"Missing prices for: {', '.join(missing)}")

        return prices

    except Exception as error:
        if not fallback_path.exists():
            raise RuntimeError(
                "Price download failed and no saved ETF data is available."
            ) from error

        prices = pd.read_csv(
            fallback_path,
            index_col=0,
            parse_dates=True,
        )

        missing = [
            ticker for ticker in tickers
            if ticker not in prices.columns
        ]
        if missing:
            raise ValueError(
                f"Saved data does not contain: {', '.join(missing)}"
            ) from error

        prices = prices.loc[
            prices.index >= pd.Timestamp(start),
            list(tickers),
        ].dropna(how="all")

        if prices.empty or prices.isna().all().any():
            raise ValueError(
                "Saved data does not cover the requested assets and dates."
            ) from error

        st.warning("Live prices unavailable. Using saved ETF prices.")
        return prices


if __name__ == "__main__":
    save_snapshot()
