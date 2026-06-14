from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..simulation.scenario_engine import start_scenario_stream
from ..simulation.scenario_definitions import SCENARIOS

router = APIRouter(prefix="/simulate", tags=["Simulation Control"])

class SimulateRunRequest(BaseModel):
    scenario_id: str
    duration_seconds: Optional[int] = 180

# Map technical-spec names to datapack IDs
SCENARIO_MAP = {
    "A": "A",
    "CITY": "A",
    "ECONOMY": "B",
    "HIGHWAY": "B",
    "B": "B",
    "AGGRESSIVE": "C",
    "C": "C",
    "MIXED": "D",
    "D": "D"
}

@router.post("/run")
async def run_simulation(payload: SimulateRunRequest):
    """
    Triggers scenario simulation execution.
    Fulfills Section 6 and Section 12.1 of technical-spec.md.
    """
    raw_id = payload.scenario_id.upper()
    mapped_id = SCENARIO_MAP.get(raw_id)
    if not mapped_id:
        raise HTTPException(status_code=400, detail=f"Unsupported scenario_id: {payload.scenario_id}")

    session_id = "active"
    # Starts the scenario stream asynchronously
    await start_scenario_stream(session_id, mapped_id)

    return {
        "run_id": session_id,
        "status": "running",
        "packets_generated": payload.duration_seconds
    }
