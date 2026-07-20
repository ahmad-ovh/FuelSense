import asyncio
import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import SessionStateModel, TelemetryFrame
from .can_generator import generate_can_frame
from .scenario_definitions import SCENARIOS
from ..services.analytics_engine import calculate_analytics
from ..services.decision_engine import evaluate_decision
from ..services.fuel_price_service import get_price_context
from ..services.ai_service import get_ai_insights, SCENARIO_INSIGHTS

logger = logging.getLogger("scenario_engine")

# Thread-safe global caches
state_cache: Dict[str, Dict[str, Any]] = {}
locks: Dict[str, asyncio.Lock] = {}
running_tasks: Dict[str, asyncio.Task] = {}

def get_lock(session_id: str) -> asyncio.Lock:
    if session_id not in locks:
        locks[session_id] = asyncio.Lock()
    return locks[session_id]

def compute_hash(state: dict) -> str:
    """Computes a unique hash for the state to detect updates."""
    state_str = f"{state.get('scenario_id')}_{state.get('current_step')}_{state.get('status')}"
    return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

def publish_state(session_id: str, state: dict, step: int):
    state_hash = compute_hash(state)
    state_cache[session_id] = {
        "session_id": session_id,
        "latest_state": state,
        "last_updated_step": step,
        "state_hash": state_hash
    }

def restore_state_from_db(session_id: str, db: Session, sess_model: SessionStateModel):
    scenario_id = sess_model.active_scenario
    if not scenario_id:
        return None

    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return None

    duration = scenario["duration_seconds"]
    target_step = sess_model.current_step
    start_time = sess_model.start_timestamp or int(time.time())

    all_frames = db.query(TelemetryFrame).filter_by(session_id=session_id).all()
    # Sort by timestamp
    all_frames.sort(key=lambda x: x.timestamp)

    if all_frames:
        last_frame = all_frames[-1]
        latest_telemetry = {
            "timestamp": last_frame.timestamp,
            "speed_kmh": last_frame.speed_kmh,
            "rpm": last_frame.rpm,
            "throttle_pct": last_frame.throttle_pct,
            "engine_load_pct": last_frame.engine_load_pct,
            "fuel_level_pct": last_frame.fuel_level_pct,
            "driving_mode": last_frame.driving_mode,
            "fuel_burn_rate_lph": last_frame.fuel_burn_rate_lph
        }
    else:
        latest_telemetry = generate_can_frame(scenario_id, target_step, start_time)

    latest_analytics = calculate_analytics(scenario_id, all_frames, target_step, duration)
    price_context = get_price_context(scenario_id)

    decision = evaluate_decision(latest_telemetry["fuel_level_pct"], scenario["vehicle"]["tank_capacity_l"], price_context)
    decision["is_ai_justified"] = False

    insight = SCENARIO_INSIGHTS.get(scenario_id, SCENARIO_INSIGHTS["A"])
    explanation = (
        f"Cause: {insight['explanation']}\n"
        f"Effect: Fuel efficiency is {latest_analytics['fuel_efficiency']} L/100km with an Eco Score of {latest_analytics['eco_score']}.\n"
        f"Action: {insight['actionable_suggestion']}"
    )
    ai_insights = {
        "explanation": explanation,
        "actionable_suggestion": insight["actionable_suggestion"],
        "status": "done"
    }

    simulation_state = {
        "scenario_id": scenario_id,
        "status": sess_model.status,
        "current_step": target_step,
        "timestamp": latest_telemetry["timestamp"],
        "telemetry": latest_telemetry,
        "analytics": latest_analytics,
        "refuel_decision": decision,
        "fuel_price_context": price_context,
        "ai_insights": ai_insights
    }

    publish_state(session_id, simulation_state, target_step)
    return simulation_state

def catch_up_simulation(session_id: str, db: Session):
    """
    Catch up telemetry frames and state cache in a stateless, serverless environment.
    Computes exact steps elapsed, populates DB, and updates cached simulation state.
    """
    sess_model = db.query(SessionStateModel).filter_by(session_id=session_id).first()
    if not sess_model:
        return

    # If the state is not cached, or the status is IDLE/STOPPED, we restore it
    is_cached = session_id in state_cache
    if sess_model.status != "RUNNING":
        if not is_cached:
            restore_state_from_db(session_id, db, sess_model)
        return

    # RUNNING state, catch up
    scenario_id = sess_model.active_scenario
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return

    duration = scenario["duration_seconds"]
    start_time = sess_model.start_timestamp
    if not start_time:
        return

    elapsed_seconds = int(time.time() - start_time)
    if elapsed_seconds < 0:
        elapsed_seconds = 0

    current_loop = elapsed_seconds // duration
    target_step = elapsed_seconds % duration

    # Handle loop boundary crossing
    if current_loop > 0:
        new_start_time = start_time + current_loop * duration
        sess_model.start_timestamp = new_start_time
        db.query(TelemetryFrame).filter_by(session_id=session_id).delete()
        db.commit()
        start_time = new_start_time
        elapsed_seconds = target_step

    # Find where the database telemetry is at
    latest_frame = db.query(TelemetryFrame).filter_by(session_id=session_id).order_by(TelemetryFrame.timestamp.desc()).first()
    if latest_frame:
        latest_step = latest_frame.timestamp - start_time
    else:
        latest_step = -1

    # Reset if clock issues or unexpected step bounds
    if latest_step > target_step:
        db.query(TelemetryFrame).filter_by(session_id=session_id).delete()
        db.commit()
        latest_step = -1

    # Bulk insert all missing telemetry frames sequentially
    if latest_step < target_step:
        frames_to_insert = []
        for step in range(latest_step + 1, target_step + 1):
            telemetry = generate_can_frame(scenario_id, step, start_time)
            frame = TelemetryFrame(
                session_id=session_id,
                timestamp=telemetry["timestamp"],
                speed_kmh=telemetry["speed_kmh"],
                rpm=telemetry["rpm"],
                throttle_pct=telemetry["throttle_pct"],
                engine_load_pct=telemetry["engine_load_pct"],
                fuel_level_pct=telemetry["fuel_level_pct"],
                driving_mode=telemetry["driving_mode"],
                fuel_burn_rate_lph=telemetry["fuel_burn_rate_lph"]
            )
            frames_to_insert.append(frame)
        if frames_to_insert:
            db.bulk_save_objects(frames_to_insert)
            db.commit()

    # Query all telemetry frames to run analytics
    all_frames = db.query(TelemetryFrame).filter_by(session_id=session_id).all()
    all_frames.sort(key=lambda x: x.timestamp)

    latest_analytics = calculate_analytics(scenario_id, all_frames, target_step, duration)
    price_context = get_price_context(scenario_id)

    # Retrieve existing state and its decisions/insights from the cache
    existing_entry = state_cache.get(session_id)
    existing_state = existing_entry.get("latest_state") if existing_entry else None

    latest_decision = None
    if existing_state and existing_state.get("refuel_decision"):
        latest_decision = existing_state["refuel_decision"]
    else:
        latest_fuel = all_frames[-1].fuel_level_pct if all_frames else 100.0
        latest_decision = evaluate_decision(latest_fuel, scenario["vehicle"]["tank_capacity_l"], price_context)
        latest_decision["is_ai_justified"] = False

    latest_ai = None
    if existing_state and existing_state.get("ai_insights"):
        latest_ai = existing_state["ai_insights"]
    else:
        insight = SCENARIO_INSIGHTS.get(scenario_id, SCENARIO_INSIGHTS["A"])
        explanation = (
            f"Cause: {insight['explanation']}\n"
            f"Effect: Fuel efficiency is {latest_analytics['fuel_efficiency']} L/100km with an Eco Score of {latest_analytics['eco_score']}.\n"
            f"Action: {insight['actionable_suggestion']}"
        )
        latest_ai = {
            "explanation": explanation,
            "actionable_suggestion": insight["actionable_suggestion"],
            "status": "done"
        }

    latest_telemetry = generate_can_frame(scenario_id, target_step, start_time)
    simulation_state = {
        "scenario_id": scenario_id,
        "status": "RUNNING",
        "current_step": target_step,
        "timestamp": latest_telemetry["timestamp"],
        "telemetry": latest_telemetry,
        "analytics": latest_analytics,
        "refuel_decision": latest_decision,
        "fuel_price_context": price_context,
        "ai_insights": latest_ai
    }

    publish_state(session_id, simulation_state, target_step)

    sess_model.current_step = target_step
    db.commit()

def get_latest_state(session_id: str) -> Optional[dict]:
    # Ensure state is caught up / restored from DB on every call
    db = SessionLocal()
    try:
        catch_up_simulation(session_id, db)
    except Exception as e:
        logger.error(f"Error catching up simulation in get_latest_state: {e}")
    finally:
        db.close()

    cache = state_cache.get(session_id)
    if cache:
        return cache.get("latest_state")
    return None

async def start_scenario_stream(session_id: str, scenario_id: str) -> dict:
    """
    Starts the scenario telemetry stream. Handles scenario switching rules.
    """
    async with get_lock(session_id):
        # 1. Abort any running task (legacy, though we don't start them anymore)
        if session_id in running_tasks:
            task = running_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del running_tasks[session_id]

        # 2. Reset database state & cached states
        db = SessionLocal()
        try:
            # Delete old telemetry frames
            db.query(TelemetryFrame).filter_by(session_id=session_id).delete()
            
            # Reset session state in DB
            sess_model = db.query(SessionStateModel).filter_by(session_id=session_id).first()
            if sess_model:
                sess_model.status = "RESETTING"
                sess_model.active_scenario = scenario_id
                sess_model.current_step = 0
                sess_model.start_timestamp = int(time.time())
            else:
                sess_model = SessionStateModel(
                    session_id=session_id,
                    status="RESETTING",
                    active_scenario=scenario_id,
                    current_step=0,
                    start_timestamp=int(time.time())
                )
                db.add(sess_model)
            db.commit()
        finally:
            db.close()

        # Update cache to show RESETTING status
        publish_state(session_id, {
            "scenario_id": scenario_id,
            "status": "RESETTING",
            "current_step": 0,
            "timestamp": int(time.time()),
            "telemetry": {"speed_kmh": 0, "rpm": 0, "throttle_pct": 0, "engine_load_pct": 0, "fuel_level_pct": 100.0, "driving_mode": "city", "fuel_burn_rate_lph": 0.0},
            "analytics": {"eco_score": 100.0, "fuel_efficiency": 0.0, "cost_per_km": 0.0, "monthly_spend_myr": 0.0, "co2_kg": 0.0, "idle_pct": 0.0, "aggressive_events": 0, "distance_km": 0.0, "fuel_burned_liters": 0.0},
            "refuel_decision": None,
            "fuel_price_context": {"current_price": 0.0, "rolling_30day_avg": 0.0, "trend": "NEUTRAL"},
            "ai_insights": {"explanation": "Reinitializing simulation...", "actionable_suggestion": "Wait for telemetry stream."}
        }, 0)

    # 3. fixed 1-second delay for reinitialization
    await asyncio.sleep(1.0)

    async with get_lock(session_id):
        # Update database to RUNNING
        db = SessionLocal()
        try:
            sess_model = db.query(SessionStateModel).filter_by(session_id=session_id).first()
            if sess_model:
                sess_model.status = "RUNNING"
                sess_model.start_timestamp = int(time.time())
                db.commit()
        finally:
            db.close()

    return {
        "status": "RUNNING",
        "active_scenario": scenario_id,
        "message": f"Scenario {scenario_id} started successfully"
    }

async def stop_scenario_stream(session_id: str) -> dict:
    """Stops the telemetry stream and freezes the state."""
    async with get_lock(session_id):
        if session_id in running_tasks:
            task = running_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del running_tasks[session_id]

        db = SessionLocal()
        try:
            sess_model = db.query(SessionStateModel).filter_by(session_id=session_id).first()
            if sess_model:
                sess_model.status = "STOPPED"
                db.commit()
        finally:
            db.close()

        # Update cache status to STOPPED
        state = get_latest_state(session_id)
        if state:
            state["status"] = "STOPPED"
            publish_state(session_id, state, state["current_step"])

    return {"status": "STOPPED", "message": "Simulation stream stopped."}

async def reset_scenario_engine(session_id: str) -> dict:
    """Resets the engine back to IDLE state."""
    async with get_lock(session_id):
        if session_id in running_tasks:
            task = running_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del running_tasks[session_id]

        db = SessionLocal()
        try:
            db.query(TelemetryFrame).filter_by(session_id=session_id).delete()
            sess_model = db.query(SessionStateModel).filter_by(session_id=session_id).first()
            if sess_model:
                sess_model.status = "IDLE"
                sess_model.active_scenario = None
                sess_model.current_step = 0
                db.commit()
        finally:
            db.close()

        # Reset cache
        if session_id in state_cache:
            del state_cache[session_id]

    return {"status": "IDLE", "message": "System has been reset."}
