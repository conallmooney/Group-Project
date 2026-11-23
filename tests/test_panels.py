"""Known-answer tests for other panels' models."""

import numpy as np
import pandas as pd
import pytest

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