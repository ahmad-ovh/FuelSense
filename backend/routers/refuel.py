from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TelemetryFrame
from ..simulation.scenario_engine import get_latest_state, publish_state
from ..services.decision_engine import evaluate_decision
from ..services.fuel_price_service import get_price_context
from ..simulation.scenario_definitions import SCENARIOS

router = APIRouter(prefix="/refuel", tags=["Refuel Decision"])

@router.get("/{user_id}")
def get_refuel_decision(user_id: str, db: Session = Depends(get_db)):
    """
    Computes the refueling decision dynamically on request (click).
    Fulfills Section 12.3 of technical-spec.md and updates the SimulationState cache.
    """
    session_id = "active"
    state = get_latest_state(session_id)

    if not state:
        return {
            "decision": "WAIT",
            "reason": "System is currently idle. Please select a driving scenario first.",
            "estimated_savings": 0.0
        }

    # Fetch latest telemetry frame from database to find actual current fuel level
    last_frame = db.query(TelemetryFrame).filter_by(session_id=session_id).order_by(TelemetryFrame.timestamp.desc()).first()
    if last_frame:
        fuel_level = last_frame.fuel_level_pct
    else:
        fuel_level = state["telemetry"]["fuel_level_pct"]

    scenario_id = state["scenario_id"]
    scenario = SCENARIOS[scenario_id]
    tank_capacity = scenario["vehicle"]["tank_capacity_l"]
    price_context = get_price_context(scenario_id)

    # Calculate refuel decision
    decision = evaluate_decision(fuel_level, tank_capacity, price_context)

    # Atomically update the refuel decision inside the active SimulationState
    state["refuel_decision"] = decision
    publish_state(session_id, state, state["current_step"])

    return decision
