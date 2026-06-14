# FuelSense — Technical Specification (System Architecture v1)

---

## 1. System Overview

FuelSense is a **scenario-driven decision intelligence system** that converts simulated CAN-bus driving environments into:

- Fuel consumption analytics
- Refueling decision intelligence (BUY / WAIT)
- Cost projection and trend analysis
- AI-generated behavioral explanations

The system is designed as a **deterministic backend pipeline + reactive mobile-first frontend dashboard**, driven by controlled scenario inputs.

---

## 2. High-Level Architecture

```

┌──────────────────────────────────────────────────────┐
│  Frontend (Mobile Web App - React)                  │
│  - Scenario selector (FAB)                          │
│  - Dashboard (Eco score, refuel, charts)           │
│  - AI chat + insights                               │
└──────────────────────┬───────────────────────────────┘
│ HTTP JSON API
┌──────────────────────▼───────────────────────────────┐
│  FastAPI Backend                                     │
│  - Scenario ingestion API                            │
│  - Analytics orchestration layer                    │
│  - Refuel decision engine                           │
│  - AI explanation layer (Claude/OpenAI)             │
└──────────────┬───────────────┬──────────────────────┘
│               │
┌─────────▼───────┐   ┌──▼────────────────────┐
│ Scenario Engine  │   │ Fuel Price Engine     │
│ (CAN simulator)  │   │ (Malaysia data)       │
└─────────┬───────┘   └──────────┬─────────────┘
│                      │
└──────────┬───────────┘
│ structured telemetry
┌────────▼─────────┐
│ Analytics Engine │
│ (math + rules)   │
└────────┬─────────┘
│ metrics
┌────────▼─────────┐
│ Decision Engine  │
│ BUY / WAIT logic │
└────────┬─────────┘
│ context
┌────────▼─────────┐
│ AI Insight Layer │
│ narrative engine │
└──────────────────┘

```

---

## 3. Core Design Principle

### Deterministic Core + AI Explanation Layer

| Layer | Role |
|------|-----|
| Scenario Engine | Generates driving data |
| Analytics Engine | Computes metrics (no AI) |
| Decision Engine | Rules-based BUY/WAIT |
| AI Layer | Explains results only |

AI is NOT allowed to compute metrics or decisions.

---

## 4. Backend Architecture (FastAPI)

### 4.1 Module Structure

```

backend/
├── main.py
├── routers/
│   ├── simulate.py
│   ├── analytics.py
│   ├── refuel.py
│   ├── ai.py
│   └── scenarios.py
├── simulation/
│   ├── scenario_engine.py
│   ├── scenario_definitions.py
│   ├── can_generator.py
│   └── stream_runner.py
├── services/
│   ├── analytics_engine.py
│   ├── decision_engine.py
│   ├── fuel_price_service.py
│   └── ai_service.py
├── models.py
└── database.py

````

---

## 5. Scenario Engine (CORE SYSTEM)

### 5.1 Purpose

Generates synthetic CAN-bus telemetry streams that mimic real driving behavior.

Each scenario produces:
- Speed
- RPM
- Throttle input
- Engine load
- Fuel level decay
- Driving mode tags

---

### 5.2 Scenario Definition Schema

```python
Scenario = {
    "id": str,
    "name": str,
    "duration_seconds": int,
    "driving_profile": {
        "speed_range": (min, max),
        "rpm_range": (min, max),
        "throttle_range": (min, max),
        "idle_probability": float,
        "aggressive_event_rate": float,
        "fuel_burn_rate_lph": float
    }
}
````

---

### 5.3 Scenario Set (4 Core Modes)

---

### ECONOMY DRIVER

```json
{
  "id": "ECONOMY",
  "speed": [40, 70],
  "rpm": [1500, 2500],
  "throttle": [10, 35],
  "idle_probability": 0.05,
  "fuel_burn_rate": 4.5
}
```

---

### CITY TRAFFIC

```json
{
  "id": "CITY",
  "speed": [0, 50],
  "rpm": [800, 3000],
  "throttle": [10, 60],
  "idle_probability": 0.35,
  "fuel_burn_rate": 8.0
}
```

---

### AGGRESSIVE DRIVER

```json
{
  "id": "AGGRESSIVE",
  "speed": [60, 140],
  "rpm": [3000, 6500],
  "throttle": [60, 100],
  "idle_probability": 0.02,
  "fuel_burn_rate": 14.5
}
```

---

### HIGHWAY CRUISE

```json
{
  "id": "HIGHWAY",
  "speed": [90, 120],
  "rpm": [1800, 2600],
  "throttle": [20, 45],
  "idle_probability": 0.01,
  "fuel_burn_rate": 5.2
}
```

---

## 6. Scenario Execution Engine

### Flow

1. Frontend selects scenario
2. Backend runs simulation batch
3. CAN packets generated
4. Stored in DB
5. Analytics triggered

---

### Endpoint

#### POST /simulate/run

```json
{
  "scenario_id": "CITY",
  "duration_seconds": 120
}
```

---

### Output

```json
{
  "run_id": "abc123",
  "status": "completed",
  "packets_generated": 240
}
```

---

## 7. CAN Packet Generator

Each packet represents 1 second of driving:

```json
{
  "timestamp": 1710000000,
  "speed_kmh": 62,
  "rpm": 2200,
  "throttle_pct": 40,
  "engine_load_pct": 55,
  "fuel_level_pct": 61,
  "scenario_id": "CITY"
}
```

---

## 8. Analytics Engine

### Purpose

Convert raw CAN packets into meaningful metrics.

---

### Outputs

* Eco Score (0–100)
* Fuel consumption (L)
* Cost per km
* CO₂ emissions
* Driving distribution

---

### Core Calculations

#### Fuel Consumption

```
fuel_liters = Σ (fuel_burn_rate / 3600)
```

#### Distance Estimate

```
distance_km = speed * time
```

#### Efficiency

```
L/100km = (fuel / distance) * 100
```

---

### Eco Score Model

```
eco_score =
  100
  - idle_penalty
  - aggression_penalty
  - inefficiency_penalty
```

---

## 9. Decision Engine (CRITICAL SYSTEM)

### Output: BUY / WAIT

---

### HARD RULE (NON-NEGOTIABLE)

```
IF fuel_level < 15%
→ BUY (override all logic)
```

---

### Decision Logic

| Condition                           | Action         |
| ----------------------------------- | -------------- |
| fuel < 15%                          | BUY (critical) |
| price < 30-day avg AND rising trend | BUY            |
| price falling AND fuel > 40%        | WAIT           |
| otherwise                           | BUY            |

---

### Savings Model

```
savings = (future_price - current_price) × fill_liters
```

---

## 10. Fuel Price Engine

### Source

Malaysia fuel pricing dataset (data.gov.my)

---

### Responsibilities

* Fetch historical prices
* Compute 30-day rolling average
* Detect trend direction
* Feed decision engine

---

## 11. AI Insight Layer

### Role

Transforms computed metrics into human-readable insights.

### Input

* Eco score
* fuel cost
* scenario type
* decision output

### Output

* Behavioral explanation
* Financial insight
* Action suggestion

---

### Example Prompt Structure

```
You are a driving analyst.
Explain why fuel cost increased.
Do not compute values.
Only interpret provided metrics.
```

---

## 12. API SPECIFICATION

---

### 12.1 Scenario Control

#### POST /simulate/run

Triggers scenario execution.

---

### 12.2 Analytics

#### GET /analytics/{user_id}

Returns:

```json
{
  "eco_score": 72,
  "fuel_cost_month": 180,
  "co2_kg": 45,
  "efficiency": 7.8,
  "refuel_decision": "BUY"
}
```

---

### 12.3 Refuel Decision

#### GET /refuel/{user_id}

Returns:

```json
{
  "decision": "BUY",
  "reason": "Price rising trend",
  "estimated_savings": 2.30
}
```

---

### 12.4 AI Chat

#### POST /ai/chat

```json
{
  "user_id": 1,
  "message": "Why is my eco score low?"
}
```

---

## 13. Frontend Integration Model

### Polling System

```
GET /analytics every 5 seconds
```

### Scenario Trigger

```
FAB → selects scenario → POST /simulate/run
```

### UI Reaction

* Eco score updates
* Refuel card updates
* Charts re-render
* AI insights refresh

---

## 14. System Constraints

* Deterministic simulation only
* No real hardware dependency
* No external latency dependency
* All outputs reproducible per scenario

---

## 15. Success Validation Criteria

System is valid if:

* Same scenario always produces similar results
* BUY/WAIT changes under fuel/price conditions
* Eco score reflects driving behavior correctly
* AI explanations match computed outputs
* UI responds instantly to scenario switching

---

## 16. Summary

FuelSense operates as a:

> Scenario-driven CAN-bus simulation system that transforms driving behavior and fuel pricing into financial decision intelligence through deterministic analytics and AI interpretation.
