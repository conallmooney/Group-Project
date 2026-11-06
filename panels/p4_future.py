"""Panel 4 - What could it become?

Shows how a monthly saver's money could grow over time, 
using 1,000 simulated futures and adjusted for inflation."""

import numpy as np

def monthly_rate(annual_return: float) -> float:
    """Turn an annual return into the equivalent monthly return.

    Args:
        annual_return (float): The annual return as a decimal, e.g., 0.05 for 5%.  
    
    Returns:
        float: The monthly return as a decimal.
    """
    return (1 + annual_return) ** (1 / 12) - 1


def grow_savings(start: float, monthly: float, annual_return: float, years: int) -> float:
    """Grow savings month by month at a fixed return.

    Args:
        start (float): The initial money invested, in euros.
        monthly (float): The amount of money added each month, in euros.
        annual_return (float): The annual return as a decimal, e.g., 0.065.
        years (int): The number of years of saving.

    Returns:
        float: The total amount of money after the specified number of years.
    """
    rate = monthly_rate(annual_return)
    balance = start
    for month in range(years * 12):
        balance = balance * (1 + rate)
        balance = balance + monthly
    return balance


def random_monthly_returns(annual_return: float, volatility: float, months: int, seed: int = 42) -> np.ndarray:
    """Make a random sequence of monthly returns that average to the given annual return, with the given volatility.
    
    Args:
        annual_return (float): The average annual return as a decimal, e.g., 0.065.
        volatility (float): The standard deviation of the returns as a decimal, e.g., 0.15.
        months (int): How many monthly returns to generate.
        seed (int): Starting point for the random number generator, for reproducibility.
        
    Returns: 
        np.ndarray: An array of random monthly returns.
    """
    rng = np.random.default_rng(seed)
    monthly_vol = volatility/np.sqrt(12)
    return rng.normal(monthly_rate(annual_return), monthly_vol, months)


def simulate_one_future(start: float, monthly: float, annual_return: float, volatility: float, years: int, seed: int = 42) -> float:
    """Grow savings month by month using a different random return each month.
    
    Args:
        start (float): The initial money invested, in euros.
        monthly (float): The amount of money added at the end of each month, in euros.
        annual_return (float): The average annual return as a decimal, e.g., 0.065.
        volatility (float): The annual standard deviation of the returns as a decimal, e.g., 0.15.
        years (int): The number of years of saving.
        seed (int): Starting point for the random number generator, for reproducibility.
        
    Returns:
        float: The value of the savings at the end of this one possible future."""
    returns = random_monthly_returns(annual_return, volatility, years * 12, seed)
    balance = start
    for r in returns:
        balance = balance * (1 + r)
        balance = balance + monthly
    return balance

if __name__ == "__main__":
    print(monthly_rate(0.065))
    print(grow_savings(1000, 0, 0.065, 1))
    print(grow_savings(1000, 150, 0.065, 30))
    print(simulate_one_future(1000, 150, 0.065, 0.11, 30))
    print(simulate_one_future(1000, 150, 0.065, 0.0, 30))
    print(simulate_one_future(1000, 150, 0.065, 0.11, 30, seed=7))
          