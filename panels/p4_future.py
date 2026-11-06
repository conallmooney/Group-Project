"""Panel 4 - What could it become?

Shows how a monthly saver's money could grow over time, 
using 1,000 simulated futures and adjusted for inflation."""

def monthly_rate(annual_return: float) -> float:
    """Turn an annual return into the equivalent monthly return.

    Args:
        annual_return (float): The annual return as a decimal, e.g., 0.05 for 5%.  
    
    Returns:
        float: The monthly return as a decimal.
    """
    return (1 + annual_return) ** (1 / 12) - 1


if __name__ == "__main__":
    print(monthly_rate(0.065))
          