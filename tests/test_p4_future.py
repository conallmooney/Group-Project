"""Tests for Panel 4 (What could it become?)"""

import pytest

from panels.p4_future import monthly_rate, grow_savings, simulate_one_future


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