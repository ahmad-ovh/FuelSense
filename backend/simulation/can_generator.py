from .scenario_definitions import SCENARIOS

def generate_can_frame(scenario_id: str, step: int, start_timestamp: int) -> dict:
    """
    Generates a deterministic telemetry frame for a given scenario and step t.
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario ID: {scenario_id}")

    scenario = SCENARIOS[scenario_id]
    pattern = scenario["telemetry_pattern"]
    vehicle = scenario["vehicle"]
    burn_rate = scenario["fuel_burn_rate_lph"]

    # Pattern cycles every 10 steps
    idx = step % 10

    speed = pattern["speed_kmh"][idx]
    rpm = pattern["rpm"][idx]
    throttle = pattern["throttle_pct"][idx]
    engine_load = pattern["engine_load_pct"][idx]
    driving_mode = pattern["driving_mode"]

    # Compute fuel decay deterministically: fuel_pct(t) = fuel_pct(0) - (t * burn_rate / 3600 / capacity) * 100
    initial_fuel_pct = vehicle["initial_fuel_pct"]
    capacity = vehicle["tank_capacity_l"]
    
    fuel_consumed = step * (burn_rate / 3600.0)
    fuel_consumed_pct = (fuel_consumed / capacity) * 100.0
    fuel_level_pct = max(0.0, initial_fuel_pct - fuel_consumed_pct)

    # Return a telemetry packet conforming to the schema
    return {
        "timestamp": start_timestamp + step,
        "speed_kmh": speed,
        "rpm": rpm,
        "throttle_pct": throttle,
        "engine_load_pct": engine_load,
        "fuel_level_pct": round(fuel_level_pct, 4),
        "driving_mode": driving_mode,
        "fuel_burn_rate_lph": burn_rate
    }
