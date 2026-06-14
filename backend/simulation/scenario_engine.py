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
from ..services.ai_service import get_ai_insights

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

def get_latest_state(session_id: str) -> Optional[dict]:
    cache = state_cache.get(session_id)
    if cache:
        return cache.get("latest_state")
    return None

def publish_state(session_id: str, state: dict, step: int):
    state_hash = compute_hash(state)
    state_cache[session_id] = {
        "session_id": session_id,
        "latest_state": state,
        "last_updated_step": step,
        "state_hash": state_hash
    }

async def run_simulation_loop(session_id: str, scenario_id: str, tick_rate_ms: int = 1000):
    """
    Simulates the background loop of injecting CAN-bus telemetry.
    Applies the strict Tick Lifecycle.
    """
    db: Session = SessionLocal()
    try:
        # Load scenario configuration
        scenario = SCENARIOS.get(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found.")
            return

        duration = scenario["duration_seconds"]
        start_time = int(time.time())

        # Update Session State in Database
        sess_model = db.query(SessionStateModel).filter_by(session_id=session_id).first()
        if not sess_model:
            sess_model = SessionStateModel(
                session_id=session_id,
                status="RUNNING",
                active_scenario=scenario_id,
                current_step=0,
                start_timestamp=start_time
            )
            db.add(sess_model)
        else:
            sess_model.status = "RUNNING"
            sess_model.active_scenario = scenario_id
            sess_model.current_step = 0
            sess_model.start_timestamp = start_time
        db.commit()

        # Initial values for loop
        step = 0
        latest_analytics = None
        latest_decision = None
        latest_ai = None

        while True:
            # 1. Acquire Lock for tick mutation
            async with get_lock(session_id):
                # Check if scenario is still running or has been reset/stopped
                db.refresh(sess_model)
                if sess_model.status != "RUNNING":
                    logger.info(f"Session {session_id} is no longer RUNNING. Stopping simulation loop.")
                    break

                # 2. Input Generation & CAN Ingestion
                telemetry = generate_can_frame(scenario_id, step, start_time)

                # Commit frame to database
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
                db.add(frame)
                db.commit()

                # Get Price Context
                price_context = get_price_context(scenario_id)

                # 3. Analytics Calculation (run on step 0, and then every 5 steps)
                if step == 0 or step % 5 == 0 or latest_analytics is None:
                    # Fetch all telemetry for this session to compute stats
                    all_frames = db.query(TelemetryFrame).filter_by(session_id=session_id).all()
                    latest_analytics = calculate_analytics(scenario_id, all_frames, step, duration)

                # 4. Refuel Decision (updated with analytics)
                if step == 0 or step % 5 == 0 or latest_decision is None:
                    latest_decision = evaluate_decision(
                        telemetry["fuel_level_pct"],
                        scenario["vehicle"]["tank_capacity_l"],
                        price_context
                    )

                # 5. AI Explanation (updated every 15 steps)
                if step == 0 or step % 15 == 0 or latest_ai is None:
                    latest_ai = get_ai_insights(scenario_id, latest_analytics, latest_decision)

                # 6. Finalize SimulationState Schema
                simulation_state = {
                    "scenario_id": scenario_id,
                    "status": "RUNNING",
                    "current_step": step,
                    "timestamp": telemetry["timestamp"],
                    "telemetry": telemetry,
                    "analytics": latest_analytics,
                    "refuel_decision": latest_decision,
                    "fuel_price_context": price_context,
                    "ai_insights": latest_ai
                }

                # Publish state atomically to memory cache
                publish_state(session_id, simulation_state, step)

                # Update step in DB
                sess_model.current_step = step
                db.commit()

            # Wait for next tick
            await asyncio.sleep(tick_rate_ms / 1000.0)

            # Auto-loop or increment step
            step += 1
            if step >= duration:
                # auto-loop reset
                step = 0
                # Optionally clear telemetry from database to prevent unbounded growth
                async with get_lock(session_id):
                    db.query(TelemetryFrame).filter_by(session_id=session_id).delete()
                    db.commit()

    except asyncio.CancelledError:
        logger.info(f"Simulation loop for {session_id} was cancelled.")
    except Exception as e:
        logger.exception(f"Error in simulation loop for {session_id}: {e}")
    finally:
        db.close()

async def start_scenario_stream(session_id: str, scenario_id: str) -> dict:
    """
    Starts the scenario telemetry stream. Handles scenario switching rules.
    """
    async with get_lock(session_id):
        # 1. Abort any running task
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
            else:
                sess_model = SessionStateModel(
                    session_id=session_id,
                    status="RESETTING",
                    active_scenario=scenario_id,
                    current_step=0
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
            "refuel_decision": {"decision": "WAIT", "reason": "System resetting", "estimated_savings": 0.0},
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
                db.commit()
        finally:
            db.close()

        # 4. Start the background simulation loop task
        task = asyncio.create_task(run_simulation_loop(session_id, scenario_id))
        running_tasks[session_id] = task

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
