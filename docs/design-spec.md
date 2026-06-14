# FuelSense — Design Specification (UI System + Layout + Component Hierarchy)

> **Purpose:** Defines the complete visual system, mobile-first layout, interaction patterns, and component architecture for FuelSense.
>
> **Product Reality:** The system behaves as a real-time intelligent fuel assistant using structured driving data streams (hardware-fed or scenario-fed). The UI must always present outputs as live vehicle intelligence, not “demo states” or “simulations”.

---

# 1. Design Philosophy

FuelSense UI is built around 4 principles:

### 1.1 Decision-First Interface

Users don’t browse data. They react to decisions:

* “BUY / WAIT”
* “Good / Bad driving behavior”
* “Efficient / Wasteful usage”

Everything else supports that.

### 1.2 One-Glance Intelligence

The most important insight must be visible in under 2 seconds:

* Refuel decision
* Eco score
* Cost impact

### 1.3 Mobile-Native Control

Desktop is secondary. Primary experience:

* One-thumb navigation
* Floating action access
* Vertical scroll narrative

### 1.4 Minimal Cognitive Load

No dashboards clutter. No raw telemetry emphasis. Only interpreted meaning.

---

# 2. Information Architecture

## 2.1 App Structure

```
Home Dashboard
│
├── Live Driving Intelligence
│   ├── Eco Score (centerpiece)
│   ├── Refuel Decision (BUY / WAIT)
│   ├── Cost Impact Summary
│
├── Behavioral Breakdown
│   ├── Idle %
│   ├── City / Highway split
│   ├── Aggressive driving events
│
├── Fuel Economy Insights
│   ├── L/100km
│   ├── RM/km
│   ├── Monthly estimate
│
├── AI Advisor
│   ├── Explanation layer
│   ├── Chat interface
│
└── Scenario Engine (FAB menu)
    ├── Scenario A: Urban Congestion
    ├── Scenario B: Highway Efficiency
    ├── Scenario C: Aggressive Driving
    ├── Scenario D: Mixed Realistic Week
```

---

# 3. Layout System

## 3.1 Mobile Canvas

* Base width: 360–430px
* Padding: 16px outer, 12px inner grid spacing
* Grid: 4-column flexible grid (used only for metric cards)
* Everything else: vertical stack

---

## 3.2 Visual Hierarchy (Top → Bottom)

### Level 1 — Decision Layer (Most Important)

* Refuel Decision Card (BUY / WAIT)
* High visual weight
* Color-coded urgency border

---

### Level 2 — Core Intelligence Layer

* Eco Score Gauge (centered, large)
* Cost per km
* Fuel efficiency

---

### Level 3 — Behavioral Layer

* Driving breakdown bars
* Aggressive event counters
* Idle vs highway ratio

---

### Level 4 — Financial Layer

* Monthly fuel estimate
* Fuel price trends
* Savings projection

---

### Level 5 — AI Layer

* Insight card
* Chat interface

---

### Level 6 — Scenario Control (Floating)

* FAB button (bottom-right)
* Expands into scenario selector

---

# 4. Core UI Components

## 4.1 EcoScoreGauge (Hero Component)

**Purpose:** Central metric representing driving efficiency.

**Design:**

* Circular arc gauge (270° sweep)
* Color logic:

  * Green: 70–100
  * Orange: 40–69
  * Red: 0–39
* Numeric score centered
* Sub-label: “Driving Efficiency Index”

---

## 4.2 RefuelDecisionCard (Critical Component)

**Purpose:** Primary decision output

**Displays:**

* BUY / WAIT (largest text on screen)
* Urgency badge:

  * Critical
  * Recommended
  * Neutral
* Reason explanation (1–2 lines max)
* Price trend indicator
* Estimated RM impact

**Rules:**

* Must always appear above fold
* Must never require scrolling

---

## 4.3 MetricCard (Reusable)

Used for:

* RM/km
* L/100km
* Monthly cost
* CO₂ output

Design:

* Minimal card
* Label small
* Value large
* No icons unless necessary

---

## 4.4 BehaviorBreakdownBar

Visualizes:

* Idle %
* City %
* Highway %

Rules:

* Must total 100%
* Animated fill on update
* No more than 3–4 categories

---

## 4.5 AIInsightPanel

Purpose:

* Converts raw metrics → explanation

Constraints:

* Max 5 lines per insight
* Must include:

  * Cause
  * Effect
  * Action

Example structure:

```
Your fuel cost increased due to higher aggressive driving in city traffic.
This raised consumption by ~18%.
Reduce throttle spikes to improve efficiency by RM20–30/month.
```

---

## 4.6 ScenarioFAB (Floating Action Button System)

### Location:

Bottom-right corner

### Default State:

Single circular button:

```
⚙️ or ⛽
```

### Expanded State:

Radial or vertical mini-menu:

* Urban Congestion
* Highway Efficiency
* Aggressive Driving
* Mixed Week Simulation

### Interaction Rules:

* Tap opens menu
* Selecting scenario:

  * closes menu
  * triggers API request
  * refreshes dashboard instantly

---

# 5. Component Hierarchy (React Structure)

```
App
└── Dashboard
    ├── RefuelDecisionCard
    ├── EcoScoreGauge
    ├── MetricGrid
    │   ├── MetricCard
    │   ├── MetricCard
    │   ├── MetricCard
    │   └── MetricCard
    ├── BehaviorBreakdown
    │   └── BehaviorBar ×3
    ├── FinancialSummary
    ├── AIInsightPanel
    ├── AIChat
    └── ScenarioFAB
        └── ScenarioMenu
```

---

# 6. Scenario Engine UX Contract

Each scenario acts as a **data injection event** into the system.

## 6.1 Scenario Behavior Model

When user selects a scenario:

```
Scenario Selection
→ Replace telemetry dataset
→ Backend recomputes analytics
→ Refuel engine recalculates BUY/WAIT
→ UI updates instantly
```

---

## 6.2 Scenario Definitions

### Scenario A — Urban Congestion

* High idle %
* Frequent stops
* Low speed variance
* High fuel waste per km

**Expected UI Outcome:**

* Low Eco Score
* BUY recommended due to inefficient consumption

---

### Scenario B — Highway Efficiency

* Stable speed
* Low RPM variance
* Low fuel burn rate

**Outcome:**

* High Eco Score
* WAIT more likely if fuel price trending down

---

### Scenario C — Aggressive Driving

* High throttle events
* High RPM spikes
* Rapid fuel drain

**Outcome:**

* Very low Eco Score
* BUY urgent due to high consumption risk

---

### Scenario D — Mixed Realistic Week

* Balanced distribution
* Moderate efficiency

**Outcome:**

* Neutral Eco Score
* Decision depends on price trend only

---

# 7. Data Visualization Rules

## 7.1 No Raw Data Exposure

Never show:

* RPM raw logs
* Timestamp streams
* Telemetry arrays

Everything must be aggregated.

---

## 7.2 Always Show Interpretation

Instead of:

* “Fuel burn rate: 7.2 L/h”

Show:

* “City driving increasing fuel cost by RM12/week”

---

## 7.3 Trend Priority

Trends > snapshots:

* Weekly change > current value
* Direction matters more than absolute numbers

---

# 8. Color System

## 8.1 Semantic Colors

| Meaning        | Color  |
| -------------- | ------ |
| BUY / Critical | Red    |
| WAIT / Good    | Green  |
| Neutral        | Gray   |
| Warning        | Orange |

---

## 8.2 Background System

* Primary background: soft white / off-white
* Cards: subtle gray elevation
* Decision cards: tinted backgrounds based on urgency

---

# 9. Motion System

## 9.1 Micro-interactions

* Gauge fills animate on update
* Bars slide horizontally
* Scenario switch fades content

---

## 9.2 Transition Rules

* Scenario switch: 300–500ms fade + scale
* Card updates: smooth value interpolation
* Avoid instant jumps for metrics

---

# 10. Accessibility Rules

* Minimum font size: 12px
* Decision labels always bold
* Color never used alone to convey meaning
* BUY/WAIT always includes text + color

---

# 11. Performance Constraints

* Dashboard refresh: 5s polling max
* Scenario switch: instant local UI update + async backend fetch
* No blocking UI loads

---

# 12. Key UX Outcome

At any moment, user should understand:

1. Am I wasting money?
2. Should I refuel now or later?
3. How bad is my driving behavior?
4. What exactly caused this?

Without reading more than a few lines.

---

# 13. Summary

FuelSense UI is not a data dashboard.

It is a **decision surface**.

Every screen exists to answer:

* “What should I do right now?”
* “How much is this costing me?”
* “What behavior caused it?”
* “Should I refuel now or wait?”

Everything else is supporting structure.
