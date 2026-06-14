def evaluate_decision(fuel_level_pct: float, tank_capacity_l: float, price_context: dict) -> dict:
    """
    Evaluates the refuel decision (BUY or WAIT) based on rules from technical-spec.md Section 9.
    """
    current_price = price_context["current_price"]
    avg_price = price_context["rolling_30day_avg"]
    trend = price_context["trend"]

    # Calculate fill capacity in liters
    fill_liters = tank_capacity_l * (100.0 - fuel_level_pct) / 100.0

    # Rule 1: Fuel critical override
    if fuel_level_pct < 15.0:
        return {
            "decision": "BUY",
            "reason": "Fuel critical (below 15%)",
            "estimated_savings": 0.0
        }

    # Rule 2: Price rising and below average
    if current_price < avg_price and trend == "RISING":
        # Savings = (future_price - current_price) * fill_liters
        # Estimate future price increase of RM0.10
        future_price = current_price + 0.10
        savings = (future_price - current_price) * fill_liters
        return {
            "decision": "BUY",
            "reason": "Price rising trend and below 30-day average",
            "estimated_savings": round(max(0.0, savings), 2)
        }

    # Rule 3: Price falling and fuel level > 40%
    if trend == "FALLING" and fuel_level_pct > 40.0:
        # Savings of waiting = (current_price - future_price) * fill_liters
        # Estimate future price drop of RM0.08
        future_price = current_price - 0.08
        savings = (current_price - future_price) * fill_liters
        return {
            "decision": "WAIT",
            "reason": "Price falling and fuel level stable above 40%",
            "estimated_savings": round(max(0.0, savings), 2)
        }

    # Rule 4: Otherwise
    # Savings by buying now before expected rise
    future_price = current_price + 0.05
    savings = (future_price - current_price) * fill_liters
    return {
        "decision": "BUY",
        "reason": "Standard refuel recommendation or rising price trend",
        "estimated_savings": round(max(0.0, savings), 2)
    }
