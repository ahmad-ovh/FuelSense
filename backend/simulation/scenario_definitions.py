SCENARIOS = {
    "A": {
        "scenario_id": "A",
        "name": "Urban Congestion",
        "duration_seconds": 180,
        "vehicle": {
            "type": "compact_sedan",
            "tank_capacity_l": 40,
            "initial_fuel_pct": 72.0
        },
        "fuel_burn_rate_lph": 9.2,
        "telemetry_pattern": {
            "speed_kmh": [0, 0, 12, 18, 5, 0, 22, 30, 10, 0],
            "rpm": [800, 900, 1500, 2200, 1200, 850, 2600, 3000, 1800, 900],
            "throttle_pct": [0, 0, 35, 60, 20, 0, 70, 85, 40, 0],
            "engine_load_pct": [10, 12, 40, 65, 30, 8, 75, 88, 50, 10],
            "driving_mode": "city"
        }
    },
    "B": {
        "scenario_id": "B",
        "name": "Highway Efficiency",
        "duration_seconds": 180,
        "vehicle": {
            "type": "sedan",
            "tank_capacity_l": 40,
            "initial_fuel_pct": 68.0
        },
        "fuel_burn_rate_lph": 5.1,
        "telemetry_pattern": {
            "speed_kmh": [85, 90, 92, 95, 93, 88, 90, 94, 96, 92],
            "rpm": [1800, 1900, 1950, 2000, 1950, 1850, 1900, 1980, 2050, 1950],
            "throttle_pct": [30, 32, 35, 36, 34, 30, 31, 33, 35, 32],
            "engine_load_pct": [45, 48, 50, 52, 50, 46, 47, 49, 51, 48],
            "driving_mode": "highway"
        }
    },
    "C": {
        "scenario_id": "C",
        "name": "Aggressive Driving",
        "duration_seconds": 180,
        "vehicle": {
            "type": "sports_sedan",
            "tank_capacity_l": 45,
            "initial_fuel_pct": 60.0
        },
        "fuel_burn_rate_lph": 14.8,
        "telemetry_pattern": {
            "speed_kmh": [20, 45, 70, 110, 80, 40, 90, 120, 60, 30],
            "rpm": [2000, 3500, 5000, 6500, 4000, 3000, 5500, 7000, 4200, 2500],
            "throttle_pct": [40, 70, 95, 100, 60, 45, 85, 100, 55, 30],
            "engine_load_pct": [50, 80, 95, 100, 70, 55, 90, 100, 65, 40],
            "driving_mode": "city"
        }
    },
    "D": {
        "scenario_id": "D",
        "name": "Mixed Weekly Driving",
        "duration_seconds": 180,
        "vehicle": {
            "type": "family_car",
            "tank_capacity_l": 40,
            "initial_fuel_pct": 75.0
        },
        "fuel_burn_rate_lph": 7.3,
        "telemetry_pattern": {
            "speed_kmh": [0, 25, 55, 80, 60, 0, 40, 90, 70, 20],
            "rpm": [900, 1800, 2500, 3000, 2200, 850, 2000, 2800, 2400, 1500],
            "throttle_pct": [0, 40, 55, 65, 45, 0, 50, 70, 60, 35],
            "engine_load_pct": [10, 45, 60, 70, 50, 8, 55, 65, 58, 30],
            "driving_mode": "mixed"
        }
    }
}
