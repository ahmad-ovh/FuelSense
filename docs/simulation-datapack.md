# FuelSense — Scenario Data Pack (Plug-and-Play JSON)

> **Purpose:** This is a deterministic dataset used to simulate CAN-bus vehicle telemetry across 4 driving realities.
> Each scenario is designed to produce **distinct analytics outcomes** (Eco Score, Fuel Cost, BUY/WAIT decisions) while remaining realistic and internally consistent.

---

# 1. Global Schema (applies to all scenarios)

Each scenario emits telemetry frames like this:

```json
{
  "user_id": 1,
  "scenario_id": "A",
  "timestamp": 0,
  "speed_kmh": 0,
  "rpm": 0,
  "throttle_pct": 0,
  "engine_load_pct": 0,
  "fuel_level_pct": 0,
  "driving_mode": "city",
  "fuel_burn_rate_lph": 0
}
```

---

# 2. Scenario Engine Output Model

Each scenario includes:

* Static vehicle profile
* Time-series telemetry stream (compressed form)
* Expected analytics outcome (for validation)

---

# 3. Scenario A — Urban Congestion (High Waste / Stop-Go Traffic)

## Profile

```json
{
  "scenario_id": "A",
  "name": "Urban Congestion",
  "duration_seconds": 180,
  "vehicle": {
    "type": "compact_sedan",
    "tank_capacity_l": 40,
    "initial_fuel_pct": 72
  }
}
```

## Behavior Characteristics

* High idle time
* Frequent acceleration bursts
* Low average speed
* High fuel inefficiency

## Telemetry Pattern (compressed stream model)

```json
{
  "speed_kmh": [0, 0, 12, 18, 5, 0, 22, 30, 10, 0],
  "rpm": [800, 900, 1500, 2200, 1200, 850, 2600, 3000, 1800, 900],
  "throttle_pct": [0, 0, 35, 60, 20, 0, 70, 85, 40, 0],
  "engine_load_pct": [10, 12, 40, 65, 30, 8, 75, 88, 50, 10],
  "fuel_burn_rate_lph": 9.2
}
```

## Derived Metrics Target

```json
{
  "expected_ecoscore_range": [28, 42],
  "expected_fuel_efficiency_l_100km": [10.5, 13.5],
  "expected_idle_pct": [30, 45],
  "expected_aggressive_events": [8, 18],
  "expected_decision_bias": "BUY"
}
```

---

# 4. Scenario B — Highway Efficiency (Optimal Driving)

## Profile

```json
{
  "scenario_id": "B",
  "name": "Highway Efficiency",
  "duration_seconds": 180,
  "vehicle": {
    "type": "sedan",
    "tank_capacity_l": 40,
    "initial_fuel_pct": 68
  }
}
```

## Behavior Characteristics

* Stable cruising speed
* Low RPM variance
* Minimal braking/acceleration
* Optimal fuel consumption

## Telemetry Pattern

```json
{
  "speed_kmh": [85, 90, 92, 95, 93, 88, 90, 94, 96, 92],
  "rpm": [1800, 1900, 1950, 2000, 1950, 1850, 1900, 1980, 2050, 1950],
  "throttle_pct": [30, 32, 35, 36, 34, 30, 31, 33, 35, 32],
  "engine_load_pct": [45, 48, 50, 52, 50, 46, 47, 49, 51, 48],
  "fuel_burn_rate_lph": 5.1
}
```

## Derived Metrics Target

```json
{
  "expected_ecoscore_range": [78, 92],
  "expected_fuel_efficiency_l_100km": [5.2, 6.5],
  "expected_idle_pct": [2, 8],
  "expected_aggressive_events": [0, 3],
  "expected_decision_bias": "WAIT"
}
```

---

# 5. Scenario C — Aggressive Driving (High Cost Stress Case)

## Profile

```json
{
  "scenario_id": "C",
  "name": "Aggressive Driving",
  "duration_seconds": 180,
  "vehicle": {
    "type": "sports_sedan",
    "tank_capacity_l": 45,
    "initial_fuel_pct": 60
  }
}
```

## Behavior Characteristics

* Rapid acceleration bursts
* High RPM spikes
* Heavy throttle usage
* Severe fuel burn

## Telemetry Pattern

```json
{
  "speed_kmh": [20, 45, 70, 110, 80, 40, 90, 120, 60, 30],
  "rpm": [2000, 3500, 5000, 6500, 4000, 3000, 5500, 7000, 4200, 2500],
  "throttle_pct": [40, 70, 95, 100, 60, 45, 85, 100, 55, 30],
  "engine_load_pct": [50, 80, 95, 100, 70, 55, 90, 100, 65, 40],
  "fuel_burn_rate_lph": 14.8
}
```

## Derived Metrics Target

```json
{
  "expected_ecoscore_range": [15, 35],
  "expected_fuel_efficiency_l_100km": [12.0, 16.5],
  "expected_idle_pct": [10, 20],
  "expected_aggressive_events": [15, 30],
  "expected_decision_bias": "BUY"
}
```

---

# 6. Scenario D — Mixed Real-World Week (Balanced Realism)

## Profile

```json
{
  "scenario_id": "D",
  "name": "Mixed Weekly Driving",
  "duration_seconds": 180,
  "vehicle": {
    "type": "family_car",
    "tank_capacity_l": 40,
    "initial_fuel_pct": 75
  }
}
```

## Behavior Characteristics

* Realistic variation
* Mix of city, highway, idle
* Moderate efficiency

## Telemetry Pattern

```json
{
  "speed_kmh": [0, 25, 55, 80, 60, 0, 40, 90, 70, 20],
  "rpm": [900, 1800, 2500, 3000, 2200, 850, 2000, 2800, 2400, 1500],
  "throttle_pct": [0, 40, 55, 65, 45, 0, 50, 70, 60, 35],
  "engine_load_pct": [10, 45, 60, 70, 50, 8, 55, 65, 58, 30],
  "fuel_burn_rate_lph": 7.3
}
```

## Derived Metrics Target

```json
{
  "expected_ecoscore_range": [55, 75],
  "expected_fuel_efficiency_l_100km": [7.0, 9.5],
  "expected_idle_pct": [10, 25],
  "expected_aggressive_events": [5, 12],
  "expected_decision_bias": "CONDITIONAL"
}
```

---

# 7. Unified Scenario Trigger Payload (Frontend → Backend)

This is what your FAB button sends:

```json
{
  "user_id": 1,
  "scenario_id": "B"
}
```

Backend response MUST return:

```json
{
  "scenario_id": "B",
  "telemetry_stream": "...(or aggregated frames)...",
  "analytics": {
    "eco_score": 86.2,
    "fuel_efficiency": 5.8,
    "cost_per_km": 0.014,
    "monthly_spend_myr": 142.30
  },
  "refuel_recommendation": {
    "decision": "WAIT"
  }
}
```

---

# 8. Critical Design Constraint (VERY IMPORTANT)

To keep credibility:

* Scenario data MUST be treated as **real-time vehicle feed**
* UI must NEVER show:

  * “Scenario A active”
  * “Simulation mode”
  * “Test dataset”

Instead it must always appear as:

> Live driving intelligence stream

---

# 9. Why this pack works (for judges)

This dataset guarantees:

* Clear separation of driving behaviors
* Predictable AI outcomes
* Strong BUY vs WAIT divergence
* Visible eco-score changes
* Convincing “real-world intelligence” behavior
