"""Tests for Panel 4 (What could it become?)"""

import pytest

from panels.p4_future import monthly_rate, grow_savings, simulate_one_future, simulate_paths, to_todays_euros, fan_percentiles


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