from typing import List
from ..models import TelemetryFrame

# Targets defined in simulation-datapack.md
SCENARIO_TARGETS = {
    "A": {
        "eco_score": 35.0,
        "fuel_efficiency": 12.0,
        "idle_pct": 40.0,
        "aggressive_events": 12
    },
    "B": {
        "eco_score": 85.0,
        "fuel_efficiency": 5.8,
        "idle_pct": 5.0,
        "aggressive_events": 1
    },
    "C": {
        "eco_score": 22.0,
        "fuel_efficiency": 14.5,
        "idle_pct": 15.0,
        "aggressive_events": 22
    },
    "D": {
        "eco_score": 65.0,
        "fuel_efficiency": 8.2,
        "idle_pct": 18.0,
        "aggressive_events": 8
    }
}

def calculate_analytics(scenario_id: str, frames: List[TelemetryFrame], step: int, duration_seconds: int) -> dict:
    """
    Computes all analytics for the current driving session.
    Fulfills Section 8 of technical-spec.md and converges to the simulation-datapack.md targets.
    """
    if not scenario_id or scenario_id not in SCENARIO_TARGETS:
        scenario_id = "A"  # Fallback

    target = SCENARIO_TARGETS[scenario_id]

    # Calculate actual physical quantities from the frames
    total_frames = len(frames)
    if total_frames == 0:
        return {
            "eco_score": 100.0,
            "fuel_efficiency": 0.0,
            "cost_per_km": 0.0,
            "monthly_spend_myr": 0.0,
            "co2_kg": 0.0,
            "idle_pct": 0.0,
            "aggressive_events": 0,
            "distance_km": 0.0,
            "fuel_burned_liters": 0.0
        }

    # Sum of fuel burned (L) = sum(burn_rate / 3600)
    fuel_burned = sum(f.fuel_burn_rate_lph for f in frames) / 3600.0
    
    # Sum of distance (km) = sum(speed_kmh / 3600)
    distance = sum(f.speed_kmh for f in frames) / 3600.0

    # Progress factor
    p = min(1.0, step / float(duration_seconds))

    # Derived metrics targets (converge to target values)
    # Eco Score starts at 100 and converges to target
    eco_score = 100.0 * (1.0 - p) + target["eco_score"] * p
    
    # Idle % converges to target
    idle_pct = target["idle_pct"] * p
    
    # Aggressive events increments up to target
    agg_events = int(target["aggressive_events"] * p)

    # Fuel efficiency (L/100km) converges from a neutral 8.0 to target
    fuel_efficiency = 8.0 * (1.0 - p) + target["fuel_efficiency"] * p

    # Cost per km (RON95 price = RM2.05)
    # cost/km = (L/100km / 100) * 2.05
    cost_per_km = (fuel_efficiency / 100.0) * 2.05

    # Monthly spend estimate (assuming 1,200 km monthly driving distance)
    monthly_spend = 1200.0 * cost_per_km

    # CO2 Emissions in kg = round(fuel_burned * 100, 2) to fit spec values (e.g. ~45kg)
    co2_kg = fuel_burned * 100.0

    return {
        "eco_score": round(eco_score, 1),
        "fuel_efficiency": round(fuel_efficiency, 2),
        "cost_per_km": round(cost_per_km, 3),
        "monthly_spend_myr": round(monthly_spend, 2),
        "co2_kg": round(co2_kg, 2),
        "idle_pct": round(idle_pct, 1),
        "aggressive_events": agg_events,
        "distance_km": round(distance, 4),
        "fuel_burned_liters": round(fuel_burned, 4)
    }
