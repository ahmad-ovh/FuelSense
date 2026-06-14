def evaluate_decision(fuel_level_pct: float, tank_capacity_l: float, price_context: dict) -> dict:
    """
    Evaluates the refuel decision (BUY or WAIT) with highly realistic reasoning.
    Covers all cases for fuel levels, price trends, and tank capacity.
    """
    current_price = price_context["current_price"]
    avg_price = price_context["rolling_30day_avg"]
    trend = price_context["trend"]

    # Calculate remaining fuel in liters and capacity needed to fill
    current_fuel_liters = tank_capacity_l * (fuel_level_pct / 100.0)
    fill_liters = tank_capacity_l - current_fuel_liters

    # Case 1: Critical low fuel level override (under 15%)
    if fuel_level_pct < 15.0:
        return {
            "decision": "BUY",
            "reason": f"CRITICAL: Fuel level is extremely low ({fuel_level_pct:.1f}% / {current_fuel_liters:.1f}L). Refuel immediately for safety, regardless of market pricing.",
            "estimated_savings": 0.0
        }

    # Case 2 & 3: Fuel is low-to-moderate (15% - 40%)
    if fuel_level_pct <= 40.0:
        if trend == "FALLING":
            # Price is falling but fuel is low. Safety risk to wait!
            return {
                "decision": "BUY",
                "reason": f"LOW FUEL WARNING: Fuel level is {fuel_level_pct:.1f}% ({current_fuel_liters:.1f}L remaining). Although weekly price is falling, waiting is risky as you may run out of fuel.",
                "estimated_savings": 0.0
            }
        else:
            # Price is rising and fuel is low. Buying now is highly recommended.
            future_price = current_price + 0.10
            savings = (future_price - current_price) * fill_liters
            return {
                "decision": "BUY",
                "reason": f"RECOMMENDED: Fuel is low ({fuel_level_pct:.1f}%) and weekly prices are rising. Refueling now safeguards against both reserve exhaustion and higher prices (saving ~RM{savings:.2f}).",
                "estimated_savings": round(max(0.0, savings), 2)
            }

    # Case 4 & 5: Fuel level is healthy (above 40%)
    else:
        if trend == "FALLING":
            # Price is falling and we have plenty of fuel. We should wait!
            future_price = current_price - 0.08
            savings = (current_price - future_price) * fill_liters
            return {
                "decision": "WAIT",
                "reason": f"OPTIMAL WINDOW: Fuel is healthy ({fuel_level_pct:.1f}% / {current_fuel_liters:.1f}L) and weekly prices are falling. Delaying refueling will let you buy at a lower rate (saving ~RM{savings:.2f}).",
                "estimated_savings": round(max(0.0, savings), 2)
            }
        else:
            # Price is rising but fuel is healthy. Buying now is recommended to lock in the lower price.
            # If current price is below 30-day average:
            if current_price < avg_price:
                future_price = current_price + 0.05
                savings = (future_price - current_price) * fill_liters
                return {
                    "decision": "BUY",
                    "reason": f"OPPORTUNE BUY: Fuel is healthy ({fuel_level_pct:.1f}%) but prices are rising. Current price (RM{current_price:.2f}) is below the 30-day average (RM{avg_price:.2f}). Lock in savings now.",
                    "estimated_savings": round(max(0.0, savings), 2)
                }
            else:
                # Price is rising and above average. Lock in now before it goes even higher.
                future_price = current_price + 0.05
                savings = (future_price - current_price) * fill_liters
                return {
                    "decision": "BUY",
                    "reason": f"LOCK IN PRICE: Prices are rising. Refueling now protects against further price hikes, though your current fuel level is stable at {fuel_level_pct:.1f}%.",
                    "estimated_savings": round(max(0.0, savings), 2)
                }
