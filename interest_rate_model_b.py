
"""Interest-rate sensitivity regression model for Panel B."""

import pandas as pd
import numpy as np


def calculate_sensitivities(
    regression_data: pd.DataFrame,
) -> pd.DataFrame:
    
    """
    Estimate each ETF's sensitivity to Treasury yield changes.

    Fits a separate ordinary least squares regression for each ETF,
    using historical ETF percentage returns and changes in the
    US 10-year Treasury yield.

    Args:
        regression_data: DataFrame containing ETF returns in percent
            and a 'yield_change' column in percentage points.

    Returns:
        DataFrame containing ETF ticker, alpha, beta, R-squared
        and number of observations for each successful regression.

    Notes:
        Beta measures the estimated percentage-point change in an
        ETF's return for a 1 percentage-point change in Treasury
        yields. At least 30 valid observations are required.
        The relationship is historical and does not establish causation.
    """


    results = []

    # The independent variable is the change in Treasury yield.
    x_column = "yield_change"

    # Run a separate regression for each ETF.
    for ticker in regression_data.columns:

        if ticker == x_column:
            continue

        # Keep dates where both variables are available.
        clean_data = regression_data[
            [ticker, x_column]
        ].dropna()

        if len(clean_data) < 30:
            continue

        x = clean_data[x_column].to_numpy()
        y = clean_data[ticker].to_numpy()

        # Estimate slope (beta) and intercept (alpha).
        beta, alpha = np.polyfit(x, y, 1)

        # Predicted returns from the regression.
        predicted = alpha + beta * x

        # Calculate R-squared.
        ss_res = np.sum((y - predicted) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        r_squared = (
            1 - ss_res / ss_tot
            if ss_tot > 0
            else np.nan
        )

        results.append({
            "ETF": ticker,
            "Alpha": alpha,
            "Beta": beta,
            "R_squared": r_squared,
            "Observations": len(clean_data),
        })

    return pd.DataFrame(results)



def calculate_scenario_impacts(
    sensitivities: pd.DataFrame,
    shock_pp: float,
) -> pd.DataFrame:
    
    """
    Calculate illustrative ETF return impacts under a rate scenario.

    Multiplies each ETF's estimated interest-rate beta by the
    scenario's interest-rate shock.

    Args:
        sensitivities: DataFrame containing regression results,
            including a 'Beta' column.
        shock_pp: Change in the 10-year Treasury yield,
            measured in percentage points.

    Returns:
        Copy of the sensitivity results with an additional
        'Scenario_Impact' column containing estimated percentage
        returns associated with the specified yield shock.

    Notes:
        Assumes a linear relationship between ETF returns and
        Treasury yield changes. Scenario impacts are illustrative
        sensitivities, not guaranteed future returns.
    """


    impacts = sensitivities.copy()

    impacts["Scenario_Impact"] = (
        impacts["Beta"] * shock_pp
    )

    return impacts
