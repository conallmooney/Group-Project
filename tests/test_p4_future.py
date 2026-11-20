"""Tests for Panel 4 (What could it become?)"""

import pytest
import numpy as np
import pandas as pd

from panel_d.model_d import (chance_of_reaching, fan_percentiles, monthly_rate, grow_savings, simulate_one_future, 
                              simulate_paths, to_todays_euros, fan_percentiles, chance_of_reaching, 
                              quiz_to_profile, paid_in_todays_euros, monthly_returns, mix_stats, bootstrap_paths, latest_inflation)


def test_monthly_rate_compounds_to_yearly():
    """Test that the monthly rate compounds to the expected yearly rate."""
    assert (1 + monthly_rate(0.065)) ** 12 == pytest.approx(1.065)


def test_one_year_no_contributions():
    """1,000 at 6.5% for one year with nothing added should grow to 1,065."""
    assert grow_savings(1000, 0, 0.065, 1) == pytest.approx(1065)

    
def test_zero_volatility_matches_fixed_return():
    """With zero volatility, the random growth should match the fixed growth."""
    random_version = simulate_one_future(1000, 150, 0.065, 0.0, 30)
    fixed_version = grow_savings(1000, 150, 0.065, 30)
    assert random_version == pytest.approx(fixed_version)

def test_paths_zero_volatility_all_match_fixed_return():
    """With no randomness, every future should end at the fixed_return value."""
    paths = simulate_paths(1000, 150, 0.065, 0.0, 30)
    assert paths.shape == (1000, 361)
    assert paths[:, -1] == pytest.approx(grow_savings(1000, 150, 0.065, 30))


def test_inflation_removes_price_growth():
    """1,000 that doesn't grow, after 10 years of 2% inflation, is worth 1,000 / 1.02^10 today."""
    paths = simulate_paths(1000, 0, 0.0, 0.0, 10)
    real = to_todays_euros(paths, 0.02)
    assert real[0, 0] == pytest.approx(1000)
    assert real[0, -1] == pytest.approx(1000 / 1.02 ** 10)


def test_fan_lines_are_in_order():
    """At every month, bad <= lower middle <= median <= upper middle <= good."""
    paths = simulate_paths(1000, 150, 0.065, 0.15, 30)
    fan = fan_percentiles(paths)
    assert len(fan[50]) == 361
    assert all(fan[5] <= fan[25])
    assert all(fan[25] <= fan[50])
    assert all(fan[50] <= fan[75])
    assert all(fan[75] <= fan[95])


def test_chance_of_reaching_goal():
    """Half of [10, 20, 30, 40] are at or above 25; all are above 0; none are above 1000."""
    finals = np.array([10, 20, 30, 40])
    assert chance_of_reaching(finals, 25) == 0.5
    assert chance_of_reaching(finals, 0) == 1.0
    assert chance_of_reaching(finals, 1000) == 0.0


def test_quiz_scoring():
    """Totals 0-2 are Cautious, 3-4 Balanced, 5-6 Adventurous, including the edges."""
    assert quiz_to_profile([0, 0, 0]) == "Cautious"
    assert quiz_to_profile([1, 1, 0]) == "Cautious"
    assert quiz_to_profile([1, 1, 1]) == "Balanced"
    assert quiz_to_profile([2, 1, 1]) == "Balanced"
    assert quiz_to_profile([2, 2, 1]) == "Adventurous"
    assert quiz_to_profile([2, 2, 2]) == "Adventurous"


def test_paid_in_with_no_inflation_is_simple_total():
    """With 0% inflation, paid in = start + monthly * months."""
    paid = paid_in_todays_euros(1000, 150, 0.0, 30)
    assert paid[-1] == pytest.approx(1000 + 150 * 360)


def test_inflation_makes_paid_in_worth_less():
    """With inflation, the same payments are worth less in today's money."""
    paid = paid_in_todays_euros(1000, 150, 0.025, 30)
    assert paid[-1] < 1000 + 150 * 360


def test_monthly_returns_known_answer():
    """Month-end prices 100, 110, 121 give two monthly returns of exactly 10%."""
    days = pd.date_range("2024-01-01", "2024-03-31", freq="D")
    values = [100 if d.month == 1 else 110 if d.month == 2 else 121 for d in days]
    prices = pd.DataFrame({"SPY": values}, index=days)
    result = monthly_returns(prices)
    assert len(result) == 2
    assert result["SPY"].tolist() == pytest.approx([0.10, 0.10])


def test_mix_stats_known_answer():
    """SPY always +2%, TLT always 0%: a 50/50 mix earns exactly 1% a month, with no volatility."""
    monthly = pd.DataFrame({"SPY": [0.02, 0.02, 0.02], "TLT": [0.0, 0.0, 0.0]})
    yearly_return, yearly_volatility = mix_stats(monthly, 0.5)
    assert yearly_return == pytest.approx(1.01 ** 12 - 1)
    assert yearly_volatility == pytest.approx(0.0)


def test_bootstrap_with_identical_months_matches_fixed_return():
    """If every real month was +1%, every bootstrapped future equals the fixed-return result."""
    history = pd.DataFrame({"SPY": [0.01] * 5, "TLT": [0.01] * 5})
    paths = bootstrap_paths(1000, 150, history, 0.6, 30)
    assert paths.shape == (1000, 361)
    assert paths[:, -1] == pytest.approx(grow_savings(1000, 150, 1.01 ** 12 - 1, 30))


def test_latest_inflation_skips_missing_year():
    """Takes Ireland's latest year that has a value (2023), skipping the blank 2024 and other countries."""
    wb = pd.DataFrame({
        "economy": ["IRL", "IRL", "IRL", "FRA"],
        "year": [2022, 2023, 2024, 2024],
        "inflation": [8.1, 6.3, None, 2.0],
    })
    rate, year = latest_inflation(wb, "IRL")
    assert rate == pytest.approx(0.063)
    assert year == 2023   