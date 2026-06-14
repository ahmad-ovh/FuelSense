import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.decision_engine import evaluate_decision
from backend.services.analytics_engine import calculate_analytics
from backend.models import TelemetryFrame

client = TestClient(app)

def test_scenario_list():
    """Verify that available scenarios list is returned correctly."""
    response = client.get("/scenario/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "A" in data
    assert "B" in data
    assert "C" in data
    assert "D" in data

def test_scenario_set():
    """Verify that setting a scenario initializes the session properly."""
    response = client.post("/scenario/set", json={"scenario_id": "B"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "locked"
    assert data["active_scenario"] == "B"

def test_scenario_status():
    """Verify that the status endpoint matches the schema contract."""
    response = client.get("/scenario/status")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "status" in data
    assert "current_step" in data

def test_scenario_state():
    """Verify that the scenario state endpoint returns the full SimulationState snapshot envelope."""
    response = client.get("/scenario/state")
    assert response.status_code == 200
    data = response.json()
    
    assert data["session_id"] == "active"
    assert data["state_version"] == "1.0"
    assert "meta" in data
    assert "state_hash" in data["meta"]
    
    # Check SimulationState content
    sim_state = data["simulation_state"]
    assert sim_state is not None
    assert "scenario_id" in sim_state
    assert "status" in sim_state
    assert "telemetry" in sim_state
    assert "analytics" in sim_state
    assert "refuel_decision" in sim_state
    assert "fuel_price_context" in sim_state
    assert "ai_insights" in sim_state

def test_simulate_run():
    """Verify that simulate/run is compatible and launches the simulation."""
    response = client.post("/simulate/run", json={"scenario_id": "CITY", "duration_seconds": 120})
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "active"
    assert data["status"] == "running"

def test_ai_chat():
    """Verify chatbot response streaming."""
    response = client.post("/ai/chat", json={"user_id": 1, "message": "Why is my eco score low?"})
    assert response.status_code == 200
    text = response.text
    assert len(text) > 0

def test_decision_engine_rules():
    """
    Verify decision engine rules:
    1. fuel < 15% -> BUY (override)
    2. price falling and fuel > 40% -> WAIT
    3. price rising and price < avg -> BUY
    """
    # 1. Critical override (fuel < 15%)
    res_crit = evaluate_decision(10.0, 40.0, {"current_price": 2.05, "rolling_30day_avg": 2.10, "trend": "FALLING"})
    assert res_crit["decision"] == "BUY"
    assert "critical" in res_crit["reason"].lower()

    # 2. Wait condition (price falling and fuel > 40%)
    res_wait = evaluate_decision(50.0, 40.0, {"current_price": 2.05, "rolling_30day_avg": 2.10, "trend": "FALLING"})
    assert res_wait["decision"] == "WAIT"
    assert "falling" in res_wait["reason"].lower()

    # 3. Buy condition (price rising and below avg)
    res_buy = evaluate_decision(50.0, 40.0, {"current_price": 2.01, "rolling_30day_avg": 2.05, "trend": "RISING"})
    assert res_buy["decision"] == "BUY"
    assert "rising" in res_buy["reason"].lower()

def test_analytics_formulas():
    """Verify calculations in the analytics engine."""
    # Build two mock frames
    frames = [
        TelemetryFrame(speed_kmh=60, fuel_burn_rate_lph=6.0),
        TelemetryFrame(speed_kmh=120, fuel_burn_rate_lph=12.0)
    ]
    
    # 2 frames represent 2 seconds
    # fuel = (6.0 + 12.0) / 3600 = 0.005 Liters
    # distance = (60 + 120) / 3600 = 0.05 km
    
    analytics = calculate_analytics("B", frames, 0, 180)
    assert analytics["fuel_burned_liters"] == 0.005
    assert analytics["distance_km"] == 0.05
