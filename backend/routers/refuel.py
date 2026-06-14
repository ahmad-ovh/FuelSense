import asyncio
import logging
import queue
import threading
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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
    Computes the refueling decision dynamically on request.
    Returns a StreamingResponse yielding initial metadata followed by AI justification chunks.
    Updates the SimulationState cache on completion.
    """
    session_id = "active"
    state = get_latest_state(session_id)

    if not state:
        async def idle_generator():
            yield json.dumps({
                "type": "metadata",
                "decision": "WAIT",
                "estimated_savings": 0.0
            }) + "\n"
            yield json.dumps({
                "type": "chunk",
                "content": "System is currently idle. Please select a driving scenario first."
            }) + "\n"
        return StreamingResponse(idle_generator(), media_type="text/plain")

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

    # Stream generator for JSON-lines response
    async def event_generator():
        # 1. Yield initial decision metadata immediately
        yield json.dumps({
            "type": "metadata",
            "decision": decision["decision"],
            "estimated_savings": decision["estimated_savings"]
        }) + "\n"

        # 2. Spawn thread worker to fetch AI justification
        from ..services.ai_service import stream_refuel_ai_justification_worker
        q = queue.Queue()
        threading.Thread(
            target=stream_refuel_ai_justification_worker,
            args=(q, scenario_id, fuel_level, decision, price_context),
            daemon=True
        ).start()

        accumulated_reason = ""
        while True:
            try:
                item = q.get_nowait()
                if item is None:
                    break
                accumulated_reason += item
                yield json.dumps({"type": "chunk", "content": item}) + "\n"
            except queue.Empty:
                await asyncio.sleep(0.02)
            except Exception as e:
                logger.error(f"Error yielding refuel chunk: {e}")
                break

        # 3. Update the central cache with the finalized AI justification
        async with get_lock(session_id):
            curr_state = get_latest_state(session_id)
            if curr_state and curr_state.get("refuel_decision"):
                curr_state["refuel_decision"]["reason"] = accumulated_reason or decision["reason"]
                curr_state["refuel_decision"]["is_ai_justified"] = True
                publish_state(session_id, curr_state, curr_state["current_step"])

    return StreamingResponse(event_generator(), media_type="text/plain")
