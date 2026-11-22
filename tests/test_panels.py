"""Known-answer tests for other panels' models."""

import numpy as np
import pandas as pd
import pytest

from interest_rate_model_b import calculate_sensitivities

from panel_c.model_c import portfolio_stats


def test_sharpe_ratio_single_asset_known_answer():
    """One asset, 10% return, 20% volatility, 2% risk-free rate: Sharpe = (0.10 - 0.02) / 0.20 = 0.4."""
    weights = np.array([1.0])
    annual_returns = pd.Series([0.10], index=["SPY"])
    annual_covariance = pd.DataFrame([[0.04]], index=["SPY"], columns=["SPY"])
    ret, vol, sharpe = portfolio_stats(weights, annual_returns, annual_covariance, 0.02)
    assert ret == pytest.approx(0.10)
    assert vol == pytest.approx(0.20)
    assert sharpe == pytest.approx(0.4)


def test_sensitivity_finds_known_beta():
    """An ETF built to move exactly -2 per 1-point yield rise should get beta -2."""
    yield_change = np.linspace(-1, 1, 40)
    data = pd.DataFrame({
        "yield_change": yield_change,
        "TEST": 0.5 - 2 * yield_change,
    })
    result = calculate_sensitivities(data)
    row = result.iloc[0]
    assert row["ETF"] == "TEST"
    assert row["Beta"] == pytest.approx(-2)
    assert row["Alpha"] == pytest.approx(0.5)
    assert row["R_squared"] == pytest.approx(1)
    assert row["Observations"] == 40


def test_sensitivity_skips_short_history():
    """With fewer than 30 rows, the ETF should be skipped rather than estimated."""
    yield_change = np.linspace(-1, 1, 10)
    data = pd.DataFrame({"yield_change": yield_change, "TEST": 2 * yield_change})
    result = calculate_sensitivities(data)
    assert result.empty