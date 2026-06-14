from fastapi import APIRouter
from ..simulation.scenario_engine import get_latest_state

router = APIRouter(prefix="/refuel", tags=["Refuel Decision"])

@router.get("/{user_id}")
def get_refuel_decision(user_id: str):
    """
    Returns the latest refueling decision and details.
    Fulfills Section 12.3 of technical-spec.md.
    """
    session_id = "active"
    state = get_latest_state(session_id)

    if not state:
        # Fallback default decision
        return {
            "decision": "WAIT",
            "reason": "System is currently idle. Select a scenario.",
            "estimated_savings": 0.0
        }

    return state["refuel_decision"]
