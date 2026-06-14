## FuelSense — Execution & Build Orchestration Specification

> **Purpose:** Ensure deterministic system execution in a controlled demo environment with zero dependency on live hardware or unstable inputs.
> This spec defines how all components are initialized, how scenarios are injected, and how the system behaves during runtime.

---

## 1. Runtime Philosophy

FuelSense runs in **two modes simultaneously**:

### 1.1 Presentation Mode (Primary)

* Used during judging/demo
* All CAN-bus + ESP32 inputs are simulated
* Scenario engine is the single source of truth
* System behaves as if hardware is real

### 1.2 Development Mode (Optional)

* Real ESP32 or external data source
* Not required for hackathon success

---

## 2. System Boot Order (CRITICAL)

System must always boot in this order:

### Step 1 — Backend Initialization

```bash
uvicorn backend.main:app --reload
```

Backend must:

* Load scenario registry
* Load mock CAN bus engine
* Initialize in-memory session store
* Expose `/scenario/set`

---

### Step 2 — Scenario Engine Activation

On backend startup:

```text
Load /scenarios/data_pack.json
Set default scenario = "balanced_city"
Initialize CAN_SIMULATOR = ACTIVE
```

---

### Step 3 — Frontend Boot

```bash
npm run dev
```

Frontend must:

* Fetch scenario list from backend
* Default to scenario `balanced_city`
* Start polling `/analytics`

---

### Step 4 — Demo Lock Mode (IMPORTANT)

Once scenario is selected:

* Backend locks scenario for session
* No random mutation allowed
* Only deterministic updates allowed

---

## 3. Scenario Injection System

### 3.1 API Endpoint

```http
POST /scenario/set
```

### Request

```json
{
  "scenario_id": "aggressive_highway"
}
```

### Response

```json
{
  "status": "locked",
  "active_scenario": "aggressive_highway"
}
```

---

## 4. Scenario Engine (Core System)

### 4.1 Purpose

Replaces real CAN bus input entirely during demo.

It outputs:

* speed
* rpm
* throttle
* fuel level
* driving mode
* derived behaviour signals

---

### 4.2 Internal Loop

Every 3 seconds:

```pseudo
scenario = active_scenario

frame = scenario.frames[t]

emit telemetry:
  speed = frame.speed
  rpm = frame.rpm
  throttle = frame.throttle
  fuel = frame.fuel
  mode = frame.mode
```

---

### 4.3 Scenario Behaviour Rules

Each scenario defines:

* driving intensity curve
* fuel consumption rate
* aggressiveness probability
* idle frequency

No randomness outside defined bounds.

---

## 5. Scenario Switching Rules

### Allowed:

* Switch only via UI FAB
* Switch only at frame boundary

### Not allowed:

* Mid-frame mutation
* Partial blending between scenarios

---

## 6. Backend Data Flow Override

During demo mode:

### Telemetry endpoint behaves as:

```text
IF scenario_engine_active:
    IGNORE ESP32 input
    USE scenario frame output
ELSE:
    ACCEPT real ESP32 input
```

---

## 7. API Contract Extensions

### 7.1 Scenario List

```http
GET /scenario/list
```

### Response

```json
[
  "idle_commute",
  "balanced_city",
  "aggressive_driver",
  "highway_long_trip"
]
```

---

### 7.2 Live Scenario State

```http
GET /scenario/current
```

---

## 8. Frontend Scenario Controller (FAB System)

### UI Behavior

Floating Action Button expands into:

```
[ Idle Commute ]
[ Balanced City ]
[ Aggressive Driver ]
[ Highway Trip ]
```

### On Click:

1. Send `/scenario/set`
2. Reset dashboard state
3. Clear old analytics cache
4. Restart polling cycle

---

## 9. Data Determinism Guarantee

To ensure stable judging demo:

* Same scenario → same output every time
* No external API dependency required
* Fuel prices preloaded in DB
* AI only consumes deterministic metrics

---

## 10. Failure Handling

If backend crashes:

Frontend fallback:

```
USE last cached scenario snapshot
SHOW “reconnecting…” overlay
DO NOT CLEAR UI STATE
```

---

## 11. Demo Mode Flag

Environment variable:

```env
DEMO_MODE=true
```

When enabled:

* Scenario engine overrides all inputs
* ESP32 ignored completely
* API becomes deterministic simulator

---

## 12. System Truth Statement

> The system does not “track real-world driving during demo mode.”
> It executes controlled scenario simulations designed to emulate real CAN-bus behavior for evaluation purposes.

---

## 13. Why This Exists (Critical for Judges)

This ensures:

* No WiFi dependency
* No hardware failure risk
* Perfect repeatability
* Clean storytelling
* Controlled intelligence demonstration

