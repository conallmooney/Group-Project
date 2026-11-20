"""Automated tests for data.py (run with: python -m pytest -v).

Author: Ciara Feeney (Person A, data lead)
These tests never contact the World Bank: they swap in fake data,
so they still work when the API is down.
"""
import numpy as np
import pandas as pd
import pytest

import data


def fake_fetch(empty_code: str | None = None):
    """Return a stand-in for data._fetch_series that makes up a tiny table.

    If empty_code is given, that indicator comes back completely empty,
    which imitates the World Bank silently leaving it out.
    """
    def _fake(code: str, start: int, end: int, tries: int = 3) -> pd.DataFrame:
        years = [f"YR{y}" for y in range(start, end + 1)]
        value = np.nan if code == empty_code else 1.0
        countries = pd.Index(["IRL", "FRA"], name="economy")
        return pd.DataFrame(value, index=countries, columns=years)
    return _fake


def fake_country_info(**kwargs) -> pd.DataFrame:
    """Stand-in for the World Bank's country list (names and regions)."""
    return pd.DataFrame({"name": ["Ireland", "France"], "region": ["ECS", "ECS"]},
                        index=["IRL", "FRA"])


def test_missing_indicator_raises_error(monkeypatch):
    """A download missing an indicator must raise an error, so the backup CSV is used.

    This is the 'silent failure' bug: the API once dropped inflation without any error.
    """
    monkeypatch.setattr(data, "_fetch_series", fake_fetch(empty_code="FP.CPI.TOTL.ZG"))
    monkeypatch.setattr(data.wb.economy, "DataFrame", fake_country_info)
    with pytest.raises(ValueError, match="inflation"):
        data._download_world_bank(2020, 2022)


def test_complete_download_is_reshaped(monkeypatch):
    """A complete download becomes one row per country per year, with readable names."""
    monkeypatch.setattr(data, "_fetch_series", fake_fetch())
    monkeypatch.setattr(data.wb.economy, "DataFrame", fake_country_info)
    tidy = data._download_world_bank(2020, 2022)
    assert len(tidy) == 2 * 3  # 2 countries x 3 years
    assert set(data.WB_SERIES.values()) <= set(tidy.columns)
    assert (tidy["region"] == "Europe & Central Asia").all()


def test_backup_csv_has_every_column():
    """The backup CSV shipped with the project must contain every column the panel needs."""
    backup = pd.read_csv(data.WB_FALLBACK)
    needed = list(data.WB_SERIES.values()) + ["economy", "year", "name", "region"]
    missing = [col for col in needed if col not in backup.columns]
    assert not missing, f"Backup CSV is missing: {missing}"