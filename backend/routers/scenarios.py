import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..schemas import ScenarioStateResponse, ScenarioStatusResponse
from ..simulation.scenario_definitions import SCENARIOS
from ..simulation.scenario_engine import (
    start_scenario_stream,
    stop_scenario_stream,
    reset_scenario_engine,
    get_latest_state,
    state_cache,
    compute_hash
)

router = APIRouter(prefix="/scenario", tags=["Scenario Control"])

class SetScenarioRequest(BaseModel):
    user_id: Optional[int] = 1
    scenario_id: str

@router.get("/list", response_model=List[str])
def list_scenarios():
    """
    Returns the list of available scenario identifiers.
    Fulfills Section 7.1 of execution spec.
    """
    return list(SCENARIOS.keys())

@router.post("/set")
async def set_scenario(payload: SetScenarioRequest):
    """
    Locks and starts a scenario for the active session.
    Fulfills Section 3.1 of execution spec and Section 7 of orchestration spec.
    """
    scenario_id = payload.scenario_id
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario ID: {scenario_id}")

    session_id = "active"  # Single global session for presentation mode
    res = await start_scenario_stream(session_id, scenario_id)
    return {
        "status": "locked",
        "active_scenario": scenario_id,
        "detail": res["message"]
    }

@router.post("/start")
async def start_scenario(payload: SetScenarioRequest):
    """Starts the stream for a scenario."""
    session_id = "active"
    return await start_scenario_stream(session_id, payload.scenario_id)

@router.post("/stop")
async def stop_scenario():
    """Stops/freezes the active scenario stream."""
    session_id = "active"
    return await stop_scenario_stream(session_id)

@router.post("/reset")
async def reset_scenario():
    """Resets the simulation engine state."""
    session_id = "active"
    return await reset_scenario_engine(session_id)

@router.get("/state", response_model=ScenarioStateResponse)
def get_scenario_state():
    """
    Returns the full, atomic SimulationState snapshot.
    Fulfills Section 4.1 of api-contract-and-state-sync.md.
    """
    session_id = "active"
    state = get_latest_state(session_id)

    if not state:
        # Fallback if no state exists yet (boot state)
        # We default to an IDLE state for Scenario B to prevent crashes
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
            session_id=session_id,
            state_version="1.0",
            simulation_state=default_state,
            meta={
                "state_hash": compute_hash(default_state),
                "is_stale": False,
                "server_time": int(time.time())
            }
        )

    cache_entry = state_cache[session_id]
    return ScenarioStateResponse(
        session_id=session_id,
        state_version="1.0",
        simulation_state=state,
        meta={
            "state_hash": cache_entry["state_hash"],
            "is_stale": False,
            "server_time": int(time.time())
        }
    )

@router.get("/status", response_model=ScenarioStatusResponse)
def get_scenario_status():
    """
    Returns a lightweight status snapshot.
    Fulfills Section 4.3 of api-contract-and-state-sync.md.
    """
    session_id = "active"
    state = get_latest_state(session_id)
    if not state:
        return ScenarioStatusResponse(
            session_id=session_id,
            scenario_id=None,
            status="IDLE",
            current_step=0,
            last_tick_ms=int(time.time() * 1000)
        )
    return ScenarioStatusResponse(
        session_id=session_id,
        scenario_id=state["scenario_id"],
        status=state["status"],
        current_step=state["current_step"],
        last_tick_ms=state["timestamp"] * 1000
    )

@router.get("/current")
def get_scenario_current():
    """Alias for current scenario ID (Fulfills Section 7.2 of execution spec)."""
    session_id = "active"
    state = get_latest_state(session_id)
    return {"active_scenario": state["scenario_id"] if state else None}
