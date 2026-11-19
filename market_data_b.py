
"""Financial market data loader for Panel B."""

import pandas as pd
import streamlit as st
import yfinance as yf
from fredapi import Fred


DEFAULT_ETFS = ["SPY", "TLT", "GLD", "XLE", "XLU"]


@st.cache_data(ttl=60 * 60 * 24)
def load_etf_prices(
    tickers: tuple = tuple(DEFAULT_ETFS),
    start: str = "2015-01-01",
    end: str = "2025-01-01",
) -> pd.DataFrame:
    
    """
    Download historical adjusted closing prices for selected ETFs.

    Args:
        tickers: Tuple of ETF ticker symbols to download.
        start: Start date in YYYY-MM-DD format.
        end: End date in YYYY-MM-DD format (exclusive).

    Returns:
        DataFrame containing daily adjusted closing prices,
        with dates as the index and ETF tickers as columns.
    """


    prices = yf.download(
        list(tickers),
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    if prices.empty:
        raise ValueError("No ETF price data was downloaded.")

    return prices.sort_index()



@st.cache_data(ttl=60 * 60 * 24)
def load_treasury_yields(
    start: str = "2015-01-01",
    end: str = "2025-01-01",
) -> pd.DataFrame:
    
    """
    Download daily US 10-year Treasury yields from FRED.

    Args:
        start: Start date in YYYY-MM-DD format.
        end: End date in YYYY-MM-DD format.

    Returns:
        DataFrame containing DGS10 Treasury yields expressed
        as annual percentages, indexed by observation date.

    Notes:
        Requires a FRED_API_KEY in Streamlit secrets.
        Missing observations may occur on public holidays.
    """


    api_key = st.secrets["FRED_API_KEY"]
    fred = Fred(api_key=api_key)

    yields = fred.get_series(
        "DGS10",
        observation_start=start,
        observation_end=end,
    )

    if yields.empty:
        raise ValueError("No Treasury yield data was downloaded.")

    yields = yields.to_frame(name="DGS10")
    yields.index = pd.to_datetime(yields.index)

    return yields.sort_index()



def prepare_regression_data(
    prices: pd.DataFrame,
    yields: pd.DataFrame,
) -> pd.DataFrame:
    
    """
    Prepare aligned ETF returns and Treasury yield changes.

    Args:
        prices: DataFrame containing daily ETF closing prices.
        yields: DataFrame containing daily DGS10 Treasury yields.

    Returns:
        DataFrame containing ETF daily returns in percent
        and Treasury yield changes in percentage points,
        aligned by date.

    Notes:
        Dates with missing Treasury yield changes are removed.
        Missing ETF returns are retained for individual
        regression filtering.
    """


    # Calculate daily percentage returns for each ETF.
    returns = prices.pct_change(fill_method=None) * 100

    # Calculate daily changes in Treasury yields
    # measured in percentage points.
    yield_changes = yields["DGS10"].diff()

    # Combine both datasets using their dates.
    combined = returns.join(
        yield_changes.rename("yield_change"),
        how="inner"
    )

    # Remove dates with missing interest-rate changes.
    combined = combined.dropna(subset=["yield_change"])

    return combined
