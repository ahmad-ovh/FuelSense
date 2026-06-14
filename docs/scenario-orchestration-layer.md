# FuelSense — Scenario Execution & Demo Orchestration Spec

---

# 1. Purpose

This system defines the **runtime behavior layer** of FuelSense.

It ensures:

* Scenario data behaves like a real-time driving session
* Backend, AI, and frontend remain synchronized
* Demo is fully deterministic and judge-safe
* All outputs are reproducible under controlled conditions

---

# 2. Core Concept: “Driving Session State Machine”

FuelSense operates as a single global session:

```json id="session_model"
{
  "session_id": "active",
  "status": "IDLE | RUNNING | PAUSED | RESETTING",
  "active_scenario": null,
  "start_timestamp": null,
  "current_step": 0
}
```

---

# 3. Scenario Execution Model

Each scenario is NOT sent as a full dataset at once.

Instead, it is executed as:

> A timed telemetry stream that updates system state incrementally.

---

## 3.1 Execution Flow

```text
User selects scenario
        ↓
Backend loads scenario dataset
        ↓
Session state becomes RUNNING
        ↓
Telemetry stream begins (step-based injection)
        ↓
Analytics recalculates every step window
        ↓
AI updates context every N steps
        ↓
Frontend reflects live updates
```

---

# 4. Scenario Runner Engine (Backend Core)

## 4.1 New Service: `scenario_engine.py`

Responsibilities:

* Load scenario dataset
* Stream telemetry frames
* Control timing
* Reset or switch scenarios safely

---

## 4.2 Execution Config

```json id="exec_config"
{
  "tick_rate_ms": 1000,
  "analytics_update_interval": 5,
  "ai_update_interval": 15,
  "auto_loop": true
}
```

---

## 4.3 Runtime Behavior

Each scenario is executed as:

```python id="runtime_logic"
for frame in scenario.telemetry:
    wait(tick_rate)
    insert_into_database(frame)

    if step % analytics_interval == 0:
        recompute_analytics()

    if step % ai_interval == 0:
        refresh_ai_context()
```

---

# 5. Scenario Control API (CRITICAL MISSING LAYER)

## 5.1 Start Scenario

```http id="start_api"
POST /scenario/start
```

### Request:

```json
{
  "user_id": 1,
  "scenario_id": "A"
}
```

### Response:

```json
{
  "status": "RUNNING",
  "active_scenario": "A",
  "message": "Scenario A started"
}
```

---

## 5.2 Stop Scenario

```http id="stop_api"
POST /scenario/stop
```

Stops telemetry injection and freezes state.

---

## 5.3 Reset System

```http id="reset_api"
POST /scenario/reset
```

Resets:

* telemetry table (optional)
* analytics cache
* AI context memory
* session state

---

## 5.4 Get Session State

```http id="state_api"
GET /scenario/state
```

Returns:

```json
{
  "status": "RUNNING",
  "active_scenario": "B",
  "current_step": 42,
  "last_update": "2026-06-14T02:10:00Z"
}
```

---

# 6. Frontend Synchronization Model

Frontend does NOT control logic.

It only reacts to state:

## 6.1 Polling Model

Every 2–5 seconds:

```text
GET /analytics
GET /scenario/state
```

---

## 6.2 UI State Binding

| Backend State | UI Behavior                  |
| ------------- | ---------------------------- |
| RUNNING       | Live dashboard updates       |
| RESET         | UI clears + reload animation |
| STOPPED       | Freeze last values           |
| SWITCHING     | fade transition              |

---

# 7. Scenario Switching Rules (IMPORTANT FOR DEMO)

When switching scenarios:

### MUST happen in order:

1. Stop current stream
2. Clear pending telemetry queue
3. Reset analytics buffer
4. Load new scenario
5. Begin new stream after 1–2s delay

This prevents:

* mixed data corruption
* wrong AI interpretations
* unstable demo visuals

---

# 8. AI Synchronization Layer

AI is NOT real-time per frame.

Instead:

## 8.1 Trigger Points

AI updates only when:

* scenario starts
* major state shift occurs
* every N telemetry batches

---

## 8.2 AI Context Lock

AI context is frozen per cycle:

```text
Telemetry → Analytics snapshot → AI interpretation
```

AI never reads raw stream directly.

---

# 9. Deterministic Demo Mode (VERY IMPORTANT)

To guarantee judging success:

## 9.1 Demo Lock Flag

```json
{
  "demo_mode": true
}
```

When enabled:

* scenarios become deterministic
* delays are fixed
* AI responses are cached or pre-stabilized
* no API randomness allowed

---

## 9.2 Precomputed Outputs (Optional but powerful)

You may optionally preload:

* Eco score per scenario
* BUY/WAIT decision
* AI explanation text

This guarantees zero live failure risk.

---

# 10. System Timing Model

| Layer               | Frequency |
| ------------------- | --------- |
| Telemetry injection | 1s        |
| Analytics recompute | 5s        |
| AI update           | 15–30s    |
| Frontend refresh    | 3–5s      |

---

# 11. Critical System Guarantee

This layer ensures:

> “No matter what scenario is selected, the system always behaves predictably and synchronously.”
