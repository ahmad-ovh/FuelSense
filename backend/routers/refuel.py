import asyncio
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TelemetryFrame
from ..simulation.scenario_engine import get_latest_state, publish_state, get_lock
from ..services.decision_engine import evaluate_decision
from ..services.fuel_price_service import get_price_context
from ..simulation.scenario_definitions import SCENARIOS

logger = logging.getLogger("refuel_router")

router = APIRouter(prefix="/refuel", tags=["Refuel Decision"])

@router.get("/{user_id}")
async def get_refuel_decision(user_id: str, db: Session = Depends(get_db)):
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

    # Calculate deterministic refuel decision immediately
    decision = evaluate_decision(fuel_level, tank_capacity, price_context)
    decision["is_ai_justified"] = False

    # Atomically update the refuel decision inside the active SimulationState with the immediate result
    state["refuel_decision"] = decision
    publish_state(session_id, state, state["current_step"])

    # Launch non-blocking background task to get AI justification shortly
    def fetch_refuel_ai_task(sid, sc_id, f_level, dec_copy, p_ctx, main_loop):
        try:
            from ..services.ai_service import get_refuel_ai_justification
            
            # 1. Fetch AI justification from DeepSeek
            ai_reason = get_refuel_ai_justification(sc_id, f_level, dec_copy, p_ctx)
            
            # 2. Acquire lock and update state cache atomically
            async def update_reason():
                async with get_lock(sid):
                    curr_state = get_latest_state(sid)
                    if curr_state and curr_state.get("refuel_decision"):
                        curr_state["refuel_decision"]["reason"] = ai_reason
                        curr_state["refuel_decision"]["is_ai_justified"] = True
                        publish_state(sid, curr_state, curr_state["current_step"])
            
            asyncio.run_coroutine_threadsafe(update_reason(), main_loop)
        except Exception as ex:
            logger.error(f"Error in background refuel AI task: {ex}")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, fetch_refuel_ai_task, session_id, scenario_id, fuel_level, decision.copy(), price_context, loop)

    return decision
