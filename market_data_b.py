
"""Financial market data loader for Panel B."""

import pandas as pd
import streamlit as st
import yfinance as yf


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
    Download daily US 10-year Treasury yields from FRED
    without requiring an API key.

    Returns:
        DataFrame containing DGS10 Treasury yields,
        expressed as annual percentages.
    """

    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"

    yields = pd.read_csv(
        url,
        parse_dates=["observation_date"],
        index_col="observation_date",
        na_values=["."],
    )

    yields.index = pd.to_datetime(yields.index)

    # Match the original function's date range.
    yields = yields.loc[
        (yields.index >= pd.Timestamp(start))
        & (yields.index <= pd.Timestamp(end))
    ]

    yields["DGS10"] = pd.to_numeric(
        yields["DGS10"],
        errors="coerce",
    )

    yields = yields.dropna(subset=["DGS10"])

    if yields.empty:
        raise ValueError("No Treasury yield data was downloaded.")

    return yields.sort_index()

def prepare_regression_data(
    prices: pd.DataFrame,
    yields: pd.DataFrame,
    frequency: str = "Monthly",
) -> pd.DataFrame:
    """
    Prepare ETF returns and Treasury yield changes for regression.

    Args:
        prices: Daily adjusted ETF closing prices.
        yields: Daily DGS10 Treasury yields in percent.
        frequency: 'Daily', 'Weekly', or 'Monthly'.

    Returns:
        DataFrame containing ETF percentage returns and
        Treasury yield changes in percentage points,
        aligned by date.

    Notes:
        Weekly data uses the last available observation each week.
        Monthly data uses the last available observation each month.
    """

    frequency_rules = {
        "Daily": None,
        "Weekly": "W-FRI",
        "Monthly": "ME",
    }

    if frequency not in frequency_rules:
        raise ValueError(
            "Frequency must be Daily, Weekly, or Monthly."
        )

    # Sort the data and remove missing Treasury yields.
    clean_prices = prices.sort_index()
    clean_yields = yields["DGS10"].dropna().sort_index()

    rule = frequency_rules[frequency]

    # Convert daily observations to weekly or monthly.
    if rule is not None:
        clean_prices = clean_prices.resample(rule).last()
        clean_yields = clean_yields.resample(rule).last()

    # Calculate ETF percentage returns.
    returns = clean_prices.pct_change(fill_method=None) * 100

    # Calculate Treasury yield changes in percentage points.
    yield_changes = clean_yields.diff()

    # Match the ETF returns with Treasury yield changes.
    combined = returns.join(
        yield_changes.rename("yield_change"),
        how="inner",
    )

    return combined.dropna(subset=["yield_change"])

