# State Sync & API Contract Spec (FuelSense)

## 1. Purpose

This document defines the **exact data exchange contract** between backend and frontend for the FuelSense simulation system.

It ensures:

* deterministic UI updates
* no partial or corrupted state rendering
* consistent behavior under rapid scenario switching
* strict alignment with `SimulationState` lifecycle

The frontend is treated as a **pure rendering layer**. It does not compute, infer, or reconstruct state.

---

## 2. Core Principle: Snapshot-Based Sync

The backend exposes the system as **immutable state snapshots per tick**.

Each API response represents:

> A complete, frozen SimulationState at a specific `scenario_id + current_step`

No incremental patches, diffs, or partial updates are allowed.

---

## 3. State Publishing Model

### 3.1 Snapshot Generation Rule

At the end of each tick lifecycle:

```
SimulationState is finalized → stored in memory cache → exposed via API
```

Only **fully computed states** are published.

---

### 3.2 State Cache Model

Backend maintains:

```json id="1a9p3m"
StateCache {
  session_id: string,
  latest_state: SimulationState,
  last_updated_step: number,
  state_hash: string
}
```

Rules:

* `latest_state` is overwritten atomically
* `state_hash` changes only when `current_step` changes
* stale states are never exposed

---

## 4. API Contract

### 4.1 GET /scenario/state

Returns the **latest SimulationState snapshot**

#### Response

```json id="k8q2vd"
{
  "session_id": "abc123",
  "state_version": "1.0",
  "simulation_state": {
    "scenario_id": "A",
    "status": "RUNNING",
    "current_step": 42,
    "timestamp": 1710000042,
    "telemetry": { ... },
    "analytics": { ... },
    "refuel_decision": { ... },
    "fuel_price_context": { ... },
    "ai_insights": { ... }
  },
  "meta": {
    "state_hash": "9f2a1c...",
    "is_stale": false,
    "server_time": 1710000042
  }
}
```

#### Rules:

* Always returns full object (never partial fields)
* If system is resetting → returns last valid state with `status = RESETTING`

---

### 4.2 GET /analytics/{session_id}

Alias endpoint for UI convenience.

Returns:

* same SimulationState
* but guaranteed recomputed analytics freshness

Use case:

* periodic UI polling fallback

---

### 4.3 GET /scenario/status

Lightweight endpoint for fast polling:

```json id="p0z7aa"
{
  "session_id": "abc123",
  "scenario_id": "B",
  "status": "RUNNING",
  "current_step": 42,
  "last_tick_ms": 1710000042
}
```

Used for:

* FAB UI updates
* loading indicators
* quick sync checks

---

## 5. Frontend Sync Rules

### 5.1 Polling Strategy

Frontend polls:

* `/scenario/state` every **3–5 seconds**
* `/scenario/status` every **1–2 seconds (optional lightweight loop)**

---

### 5.2 Render Rule

Frontend MUST:

> Render ONLY from `simulation_state`

Never:

* recompute Eco Score
* infer refuel decision
* calculate fuel usage
* estimate emissions

---

### 5.3 State Replacement Rule

On every poll:

```text
previous_state → fully replaced → new_state
```

No merging allowed.

---

### 5.4 Transition Behavior

If:

* `current_step` increases → animate update normally
* `scenario_id changes` → full UI reset animation
* `status = RESETTING` → show loading overlay
* `status = STOPPED` → freeze last frame

---

## 6. Stale State Protection

### 6.1 Staleness Definition

A state is stale if:

```
state.current_step < backend.latest_step
OR
state.timestamp < session_start_time
```

---

### 6.2 Handling Rule

If stale state is detected:

Frontend must:

* ignore update
* retry next poll cycle
* do NOT partially merge

---

## 7. Concurrency & Race Safety

### 7.1 Backend Locking Rule

Only one tick can mutate state at a time:

```text
asyncio.Lock() per session_id
```

Prevents:

* overlapping telemetry generation
* duplicate analytics computation
* corrupted scenario switch states

---

### 7.2 Scenario Switch Override Rule

If scenario switch occurs mid-tick:

1. current tick is aborted
2. state is discarded
3. new scenario initializes clean state
4. only new SimulationState is published

No mixed-state exposure allowed.

---

## 8. Versioning & Compatibility

### 8.1 State Version Field

```json id="v1n2qp"
"state_version": "1.0"
```

Rules:

* frontend must validate version
* backend may evolve schema safely only if version increments

---

### 8.2 Breaking Change Rule

If `state_version` changes:

* frontend must fallback to reload
* no partial compatibility assumed

---

## 9. Error Handling Contract

### 9.1 Backend Failure Response

```json id="r8k1lm"
{
  "session_id": "abc123",
  "status": "ERROR",
  "error": {
    "code": "SIMULATION_CORRUPTED",
    "message": "State unavailable"
  },
  "fallback_state": null
}
```

---

### 9.2 Frontend Behavior

If error received:

* freeze UI
* show error overlay
* do not retry aggressively (max 1 retry per 5 seconds)

---

## 10. Performance Guarantees

Backend must ensure:

* tick execution time ≤ 50ms
* state serialization ≤ 10ms
* API response ≤ 100ms (p95 target)

If exceeded:

* degrade to last cached state
* skip recomputation cycle (do NOT block UI)

---

## 11. System Integrity Guarantees

The system guarantees:

* deterministic outputs per `(scenario_id, current_step)`
* identical state returned across repeated calls
* no hidden computation outside SimulationState
* no frontend-side inference required

---

## 12. Summary Contract Rule (Most Important)

> The frontend is a renderer.
> The backend is the only source of truth.
> The SimulationState snapshot is the only allowed communication unit.
