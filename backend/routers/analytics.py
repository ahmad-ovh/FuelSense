import time
from fastapi import APIRouter
from ..schemas import ScenarioStateResponse
from ..simulation.scenario_engine import get_latest_state, state_cache, compute_hash

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/{session_id}", response_model=ScenarioStateResponse)
def get_analytics(session_id: str):
    """
    Returns the SimulationState snapshot for a given session.
    Acts as an alias to /scenario/state as defined in Section 4.2 of api-contract-and-state-sync.md.
    """
    # Map any session_id (e.g. user_id or active) to the active global session
    active_session_id = "active"
    state = get_latest_state(active_session_id)

    if not state:
        # Initial boot state fallback
        default_state = {
            "scenario_id": "B",
            "status": "IDLE",
            "current_step": 0,
            "timestamp": int(time.time()),
            "telemetry": {
                "speed_kmh": 0, "rpm": 0, "throttle_pct": 0, "engine_load_pct": 0, 
                "fuel_level_pct": 68.0, "driving_mode": "highway", "fuel_burn_rate_lph": 0.0
            },
            "analytics": {
                "eco_score": 100.0, "fuel_efficiency": 5.8, "cost_per_km": 0.119, 
                "monthly_spend_myr": 142.30, "co2_kg": 0.0, "idle_pct": 0.0, 
                "aggressive_events": 0, "distance_km": 0.0, "fuel_burned_liters": 0.0
            },
            "refuel_decision": {
                "decision": "WAIT", "reason": "System idle", "estimated_savings": 0.0
            },
            "fuel_price_context": {
                "current_price": 2.05, "rolling_30day_avg": 2.10, "trend": "FALLING"
            },
            "ai_insights": {
                "explanation": "Select a scenario to start the telemetry feed.",
                "actionable_suggestion": "Use the FAB selector."
            }
        }
        return ScenarioStateResponse(
            session_id=active_session_id,
            state_version="1.0",
            simulation_state=default_state,
            meta={
                "state_hash": compute_hash(default_state),
                "is_stale": False,
                "server_time": int(time.time())
            }
        )

    cache_entry = state_cache[active_session_id]
    return ScenarioStateResponse(
        session_id=active_session_id,
        state_version="1.0",
        simulation_state=state,
        meta={
            "state_hash": cache_entry["state_hash"],
            "is_stale": False,
            "server_time": int(time.time())
        }
    )
