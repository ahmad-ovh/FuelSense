import logging

logger = logging.getLogger("ai_service")

# Predefined deterministic insights matching Section 4.5 of design-spec.md
SCENARIO_INSIGHTS = {
    "A": {
        "explanation": "Your fuel cost increased due to heavy stop-go congestion and excessive idling in city traffic.",
        "actionable_suggestion": "Avoid aggressive throttle spikes when pulling away and use start-stop to save RM30-50/month."
    },
    "B": {
        "explanation": "Optimal fuel efficiency achieved via stable highway cruising and low throttle variance.",
        "actionable_suggestion": "Maintain current cruising style; delay refueling as fuel prices are trending down."
    },
    "C": {
        "explanation": "Severe efficiency drop caused by aggressive acceleration bursts and high RPM spikes.",
        "actionable_suggestion": "Smooth out throttle inputs and reduce engine load spikes to save up to RM80/month."
    },
    "D": {
        "explanation": "Moderate efficiency reflects a standard mix of highway driving and city commute slowdowns.",
        "actionable_suggestion": "Optimize route timings to bypass peak traffic congestion and improve eco score."
    }
}

def get_ai_insights(scenario_id: str, analytics: dict, decision: dict) -> dict:
    """
    Generates a deterministic interpretation of the current metrics.
    Guarantees Cause, Effect, Action structural presentation without calculations.
    """
    insight = SCENARIO_INSIGHTS.get(scenario_id)
    if not insight:
        insight = SCENARIO_INSIGHTS["A"]

    # Build the structural explanation matching design-spec.md Section 4.5
    explanation = (
        f"Cause: {insight['explanation']}\n"
        f"Effect: Fuel efficiency is {analytics['fuel_efficiency']} L/100km with an Eco Score of {analytics['eco_score']}.\n"
        f"Action: {insight['actionable_suggestion']}"
    )

    return {
        "explanation": explanation,
        "actionable_suggestion": insight["actionable_suggestion"]
    }

def handle_ai_chat(message: str, current_state: dict) -> str:
    """
    Simulates a conversational chatbot grounded in the active simulation state.
    """
    if not current_state:
        return "I don't have active driving telemetry yet. Please start a driving session first."

    scenario_id = current_state.get("scenario_id", "A")
    analytics = current_state.get("analytics", {})
    decision = current_state.get("refuel_decision") or {}
    price_ctx = current_state.get("fuel_price_context", {})

    msg_lower = message.lower()

    if "eco" in msg_lower or "score" in msg_lower or "low" in msg_lower or "high" in msg_lower:
        if scenario_id == "A" or scenario_id == "C":
            return (
                f"Your Eco Score is low ({analytics.get('eco_score')}/100). "
                f"This is caused by high aggression levels (detected {analytics.get('aggressive_events')} throttle spikes) "
                f"and an idle time ratio of {analytics.get('idle_pct')}%. "
                "Adopting smoother acceleration and shutting off the engine during long stops will help raise your score."
            )
        else:
            return (
                f"Your Eco Score is excellent ({analytics.get('eco_score')}/100). "
                f"Your stable speed cruising has kept aggressive events minimal ({analytics.get('aggressive_events')}). "
                "Keep up this consistent driving style to maximize your range."
            )

    elif "refuel" in msg_lower or "buy" in msg_lower or "wait" in msg_lower or "price" in msg_lower:
        if not decision:
            return "I haven't analyzed your refuel timing for this session yet. Please click the 'Analyze Refuel Timing' button on the dashboard to calculate recommendations."
        
        rec = decision.get("decision", "BUY")
        reason = decision.get("reason", "")
        savings = decision.get("estimated_savings", 0.0)
        trend = price_ctx.get("trend", "NEUTRAL")
        
        if rec == "WAIT":
            return (
                f"I recommend that you WAIT to refuel. Reason: {reason}. "
                f"Fuel prices are currently {trend.lower()} (rolling average is RM{price_ctx.get('rolling_30day_avg')}), "
                f"and you still have {current_state.get('telemetry', {}).get('fuel_level_pct')}% fuel. "
                f"Waiting is projected to save you approximately RM{savings}."
            )
        else:
            return (
                f"I recommend that you BUY fuel now. Reason: {reason}. "
                f"The weekly price trend is {trend.lower()} (current price is RM{price_ctx.get('current_price')}), "
                f"and buying now will safeguard you against rising costs or low fuel levels."
            )

    elif "cost" in msg_lower or "spend" in msg_lower or "saving" in msg_lower or "money" in msg_lower:
        efficiency = analytics.get("fuel_efficiency", 0.0)
        monthly_spend = analytics.get("monthly_spend_myr", 0.0)
        return (
            f"Your current fuel cost index is RM{analytics.get('cost_per_km')}/km based on an efficiency of {efficiency} L/100km. "
            f"At this rate, your projected monthly spend is RM{monthly_spend}. "
            "To reduce this, try maintaining stable highway speeds and reducing heavy engine load spikes."
        )

    elif "emission" in msg_lower or "co2" in msg_lower or "carbon" in msg_lower:
        co2 = analytics.get("co2_kg", 0.0)
        return (
            f"Your estimated CO2 emission for this session is {co2} kg. "
            "Higher engine loads and stop-and-go driving increase emissions. "
            "Driving in high-efficiency modes (like Highway cruising) can drop emissions by up to 50%."
        )

    # General/Fallback response explaining the overall metrics
    status = current_state.get("status", "RUNNING")
    return (
        f"We are currently in a {status} driving session ({current_state.get('scenario_id')} profile). "
        f"Your active Eco Score is {analytics.get('eco_score')}, with a fuel consumption rate of {analytics.get('fuel_efficiency')} L/100km. "
        f"Our recommendation is to {decision.get('decision')} refuelling ({decision.get('reason')})."
    )
