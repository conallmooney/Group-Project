
"""Interest-rate sensitivity regression model for Panel B."""

import pandas as pd
import numpy as np


def calculate_sensitivities(
    regression_data: pd.DataFrame,
) -> pd.DataFrame:
    """Estimate ETF sensitivity to Treasury yield changes."""

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
    """Calculate illustrative ETF impacts for a yield shock."""

    impacts = sensitivities.copy()

    impacts["Scenario_Impact"] = (
        impacts["Beta"] * shock_pp
    )

    return impacts
