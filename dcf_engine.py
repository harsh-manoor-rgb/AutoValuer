"""
AutoValuer DCF Engine
Handles all discounted cash flow calculations and valuation metrics.
"""

def calculate_dcf(fcf_base, cash, debt, shares, current_price, growth_rate, discount_rate, terminal_growth):
    """
    Calculates intrinsic value per share using Discounted Cash Flow (DCF).
    
    Inputs are expected in Crores for money metrics, and decimals for rates.
    """
    if discount_rate <= terminal_growth:
        raise ValueError("Discount rate must be strictly greater than terminal growth rate.")

    # Convert Crores to absolute values for precision
    fcf_abs = fcf_base * 10**7
    cash_abs = cash * 10**7
    debt_abs = debt * 10**7
    shares_abs = shares * 10**7

    fcf_forecast = []
    pv_fcf = []

    # 1. Project & Discount 5-Year Cash Flows
    for year in range(1, 6):
        fcf = fcf_abs * ((1 + growth_rate) ** year)
        pv = fcf / ((1 + discount_rate) ** year)
        fcf_forecast.append(fcf)
        pv_fcf.append(pv)

    sum_pv_5yr = sum(pv_fcf)

    # 2. Terminal Value Calculation
    terminal_value = (fcf_forecast[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** 5)

    # 3. Enterprise & Equity Value
    enterprise_value = sum_pv_5yr + pv_terminal_value
    equity_value = enterprise_value + cash_abs - debt_abs
    intrinsic_value = equity_value / shares_abs

    # Valuation Verdict & Percentage Difference
    diff = ((intrinsic_value - current_price) / current_price) * 100
    is_undervalued = intrinsic_value > current_price

    return {
        "intrinsic_value": intrinsic_value,
        "enterprise_value_cr": enterprise_value / 10**7,
        "equity_value_cr": equity_value / 10**7,
        "sum_pv_5yr_cr": sum_pv_5yr / 10**7,
        "pv_terminal_value_cr": pv_terminal_value / 10**7,
        "net_cash_cr": (cash_abs - debt_abs) / 10**7,
        "diff_percentage": diff,
        "is_undervalued": is_undervalued
    }
