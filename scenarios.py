"""Macroeconomic scenario definitions for the Rates, Risk & Returns dashboard."""

from typing import Dict, List, Union

ScenarioDict = Dict[str, Union[str, float]]

# Preset scenarios matching the shared schema: name, shock_pp, inflation, rf
SCENARIOS: Dict[str, ScenarioDict] = {
    "Higher for longer": {
        "name": "Higher for longer",
        "shock_pp": 1.5,   # +1.5 percentage point rate shock
        "inflation": 3.5,  # 3.5% annual inflation
        "rf": 4.75,        # 4.75% risk-free rate
    },
    "Rate cuts": {
        "name": "Rate cuts",
        "shock_pp": -1.5,  # -1.5 percentage point rate shock
        "inflation": 2.0,  # 2.0% annual inflation
        "rf": 3.0,         # 3.0% risk-free rate
    },
    "Stagflation": {
        "name": "Stagflation",
        "shock_pp": 2.0,   # +2.0 percentage point rate shock
        "inflation": 6.0,  # 6.0% annual inflation
        "rf": 5.25,        # 5.25% risk-free rate
    },
    "Custom": {
        "name": "Custom",
        "shock_pp": 0.0,   # Updated dynamically when the user moves the slider
        "inflation": 2.5,  # Baseline inflation assumption
        "rf": 4.0,         # Baseline risk-free rate
    },
}


def get_scenario_names() -> List[str]:
    """Return the ordered list of available scenario names."""
    return list(SCENARIOS.keys())


def get_scenario(name: str) -> ScenarioDict:
    """Return a copy of the scenario dictionary matching the given name.

    Falls back to 'Custom' if an unrecognized scenario name is passed.
    """
    selected = SCENARIOS.get(name, SCENARIOS["Custom"])
    return selected.copy()