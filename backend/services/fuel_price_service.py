def get_price_context(scenario_id: str) -> dict:
    """
    Returns the deterministic fuel price context for a given scenario.
    Provides Malaysia fuel prices, 30-day rolling average, and trend direction.
    """
    # Base weekly price in Malaysia for RON95 is typically around RM2.05
    # To satisfy the decision engine criteria and scenario biases:
    # - Scenario B (Highway Efficiency) expects WAIT bias.
    #   WAIT requires: trend == "FALLING" AND fuel > 40%
    # - Scenarios A, C, D expect BUY or CONDITIONAL bias.
    
    if scenario_id == "B":
        # Falling trend
        # Let's mock a series of 30 daily prices decreasing from 2.15 to 2.05
        # The rolling 30-day average will be higher than the current price
        return {
            "current_price": 2.05,
            "rolling_30day_avg": 2.10,
            "trend": "FALLING"
        }
    else:
        # Rising trend
        # Let's mock a series of 30 daily prices increasing from 1.95 to 2.05
        # The rolling 30-day average will be lower than the current price
        return {
            "current_price": 2.05,
            "rolling_30day_avg": 2.00,
            "trend": "RISING"
        }
