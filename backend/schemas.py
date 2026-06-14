from pydantic import BaseModel
from typing import Optional, Dict, Any

class TelemetrySchema(BaseModel):
    speed_kmh: int
    rpm: int
    throttle_pct: int
    engine_load_pct: int
    fuel_level_pct: float
    driving_mode: str
    fuel_burn_rate_lph: float

class AnalyticsSchema(BaseModel):
    eco_score: float
    fuel_efficiency: float
    cost_per_km: float
    monthly_spend_myr: float
    co2_kg: float
    idle_pct: float
    aggressive_events: int
    distance_km: float
    fuel_burned_liters: float

class RefuelDecisionSchema(BaseModel):
    decision: str
    reason: str
    estimated_savings: float
    is_ai_justified: Optional[bool] = None

class FuelPriceContextSchema(BaseModel):
    current_price: float
    rolling_30day_avg: float
    trend: str

class AIInsightsSchema(BaseModel):
    explanation: str
    actionable_suggestion: str

class SimulationStateSchema(BaseModel):
    scenario_id: str
    status: str
    current_step: int
    timestamp: int
    telemetry: TelemetrySchema
    analytics: AnalyticsSchema
    refuel_decision: Optional[RefuelDecisionSchema] = None
    fuel_price_context: FuelPriceContextSchema
    ai_insights: AIInsightsSchema

class ScenarioStateResponse(BaseModel):
    session_id: str
    state_version: str = "1.0"
    simulation_state: Optional[SimulationStateSchema] = None
    meta: Dict[str, Any]

class ScenarioStatusResponse(BaseModel):
    session_id: str
    scenario_id: Optional[str] = None
    status: str
    current_step: int
    last_tick_ms: int

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    session_id: str
    status: str = "ERROR"
    error: ErrorDetail
    fallback_state: Optional[Any] = None
