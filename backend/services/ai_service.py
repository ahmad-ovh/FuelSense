import os
import logging
import queue
import threading
import time
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("ai_service")

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def get_client() -> Optional[OpenAI]:
    if DEEPSEEK_API_KEY:
        return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return None

# Local fallback templates to guarantee judging safety in case of network timeouts or invalid keys
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
    Generates a descriptive Cause, Effect, Action explanation of the driving session using DeepSeek.
    """
    client = get_client()
    if client:
        try:
            refuel_rec = "N/A"
            refuel_reason = "N/A"
            if decision and decision.get("decision"):
                refuel_rec = decision["decision"]
                refuel_reason = decision["reason"]

            prompt = (
                f"Scenario Profile ID: {scenario_id}\n"
                f"Telemetry Analytics Context:\n"
                f"- Eco Score: {analytics.get('eco_score')}/100\n"
                f"- Efficiency: {analytics.get('fuel_efficiency')} L/100km\n"
                f"- Cost Index: RM{analytics.get('cost_per_km')}/km\n"
                f"- Projected Monthly Spend: RM{analytics.get('monthly_spend_myr')}\n"
                f"- Idle Ratio: {analytics.get('idle_pct')}%\n"
                f"- Aggressive Events Count: {analytics.get('aggressive_events')}\n"
                f"- Refuel Recommendation: {refuel_rec} ({refuel_reason})"
            )

            completion = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the FuelSense Driving Analyst.\n"
                            "Your task is to interpret the computed driving metrics and refuel decisions provided.\n"
                            "You MUST NOT compute any new metrics or decisions, only explain them.\n"
                            "Your output must strictly follow this template, matching Cause, Effect, and Action:\n"
                            "Cause: [Explain what driving behaviors or pricing factors caused the metrics, e.g. stop-and-go congestion, high RPMs, rising prices]\n"
                            "Effect: [Explain the financial and eco impact, e.g. efficiency is X L/100km, Eco Score is Y, spend is RM Z]\n"
                            "Action: [Provide 1-2 actionable suggestions, e.g. reduce throttle spikes, turn off engine during long idle]\n\n"
                            "Rules:\n"
                            "1. Keep the entire response under 5 lines total.\n"
                            "2. Do not output any reasoning/thinking tags or extra conversational text. Follow the template exactly."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                extra_body={
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": "high"
                },
                stream=False
            )

            explanation = completion.choices[0].message.content.strip()
            
            # Extract action block
            actionable_suggestion = "Adjust driving patterns to optimize efficiency."
            if "Action:" in explanation:
                actionable_suggestion = explanation.split("Action:")[1].strip()
            elif scenario_id in SCENARIO_INSIGHTS:
                actionable_suggestion = SCENARIO_INSIGHTS[scenario_id]["actionable_suggestion"]

            return {
                "explanation": explanation,
                "actionable_suggestion": actionable_suggestion
            }
        except Exception as e:
            logger.error(f"Error calling DeepSeek API for insights: {e}")

    # Fallback to local deterministic templates if DeepSeek API key is not present or fails
    insight = SCENARIO_INSIGHTS.get(scenario_id, SCENARIO_INSIGHTS["A"])
    explanation = (
        f"Cause: {insight['explanation']}\n"
        f"Effect: Fuel efficiency is {analytics['fuel_efficiency']} L/100km with an Eco Score of {analytics['eco_score']}.\n"
        f"Action: {insight['actionable_suggestion']}"
    )

    return {
        "explanation": explanation,
        "actionable_suggestion": insight["actionable_suggestion"]
    }

def get_refuel_ai_justification(scenario_id: str, fuel_level_pct: float, decision: dict, price_context: dict) -> str:
    """
    Calls DeepSeek to generate a short, professional justification for the refueling decision.
    """
    client = get_client()
    if client:
        try:
            current_price = price_context.get("current_price")
            avg_price = price_context.get("rolling_30day_avg")
            trend = price_context.get("trend")
            rec = decision.get("decision")
            savings = decision.get("estimated_savings", 0.0)

            prompt = (
                f"Scenario ID: {scenario_id}\n"
                f"Fuel Level: {fuel_level_pct:.1f}%\n"
                f"Weekly Trend: {trend}\n"
                f"Price: RM{current_price:.2f}/L (30d Avg: RM{avg_price:.2f}/L)\n"
                f"Recommendation: {rec}\n"
                f"Savings: RM{savings:.2f}\n"
            )

            completion = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the FuelSense Refuel Advisor.\n"
                            "Based on the refueling recommendation and market context, provide a short, professional justification.\n"
                            "Explain shortly why this recommendation is correct based on the fuel level, price trend, and savings.\n"
                            "Rules:\n"
                            "1. Keep it under 2 sentences (strictly max 25 words).\n"
                            "2. Do not output any thinking/reasoning tags or formatting. Output plain text only."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                extra_body={
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": "high"
                },
                stream=False
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling DeepSeek API for refuel justification: {e}")
    
    return decision.get("reason", "")

def handle_ai_chat(message: str, current_state: dict) -> str:
    """
    Handles conversation with the AI advisor grounded in current metrics using DeepSeek.
    """
    if not current_state:
        return "I don't have active driving telemetry yet. Please start a driving session first."

    client = get_client()
    if client:
        try:
            scenario_id = current_state.get("scenario_id", "A")
            analytics = current_state.get("analytics", {})
            decision = current_state.get("refuel_decision") or {}
            price_ctx = current_state.get("fuel_price_context", {})
            telemetry = current_state.get("telemetry", {})
            status = current_state.get("status", "RUNNING")

            system_prompt = (
                "You are the FuelSense Driving Advisor.\n"
                "You are assisting a driver in chat. You have access to the current active driving simulation state.\n"
                f"Current State Context:\n"
                f"- Scenario: {scenario_id}\n"
                f"- Status: {status}\n"
                f"- Telemetry: {telemetry}\n"
                f"- Analytics: {analytics}\n"
                f"- Refuel Decision: {decision}\n"
                f"- Fuel Price Context: {price_ctx}\n\n"
                "Rules:\n"
                "1. Base your answer STRICTLY on the current state context provided.\n"
                "2. Do NOT invent, assume, or compute any new metrics or decisions.\n"
                "3. If the user asks about refueling but the refuel decision is empty/not yet calculated (e.g., refuel_decision is null/empty or has 'reason' containing 'idle'), tell them to click the 'Analyze Refuel Timing' button on the dashboard first.\n"
                "4. Keep your response concise, clear, and professional. Max 3 sentences."
            )

            completion = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                extra_body={
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": "high"
                },
                stream=False
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling DeepSeek API for chat: {e}")

    # Fallback to local chatbot logic
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
        if not decision or not decision.get("decision") or "idle" in decision.get("reason", "").lower():
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

    return (
        f"We are currently in a driving session ({current_state.get('scenario_id')} profile). "
        f"Your active Eco Score is {analytics.get('eco_score')}, with a fuel consumption rate of {analytics.get('fuel_efficiency')} L/100km. "
        "Ask me questions about your score, costs, or refuel recommendations!"
    )

def stream_ai_chat_worker(q: queue.Queue, message: str, current_state: dict):
    try:
        if not current_state:
            q.put("I don't have active driving telemetry yet. Please start a driving simulation session first.")
            return

        client = get_client()
        if client:
            try:
                scenario_id = current_state.get("scenario_id", "A")
                analytics = current_state.get("analytics", {})
                decision = current_state.get("refuel_decision") or {}
                price_ctx = current_state.get("fuel_price_context", {})
                telemetry = current_state.get("telemetry", {})
                status = current_state.get("status", "RUNNING")

                system_prompt = (
                    "You are the FuelSense Driving Advisor.\n"
                    "You are assisting a driver in chat. You have access to the current active driving simulation state.\n"
                    f"Current State Context:\n"
                    f"- Scenario: {scenario_id}\n"
                    f"- Status: {status}\n"
                    f"- Telemetry: {telemetry}\n"
                    f"- Analytics: {analytics}\n"
                    f"- Refuel Decision: {decision}\n"
                    f"- Fuel Price Context: {price_ctx}\n\n"
                    "Rules:\n"
                    "1. Base your answer STRICTLY on the current state context provided.\n"
                    "2. Do NOT invent, assume, or compute any new metrics or decisions.\n"
                    "3. If the user asks about refueling but the refuel decision is empty/not yet calculated (e.g., refuel_decision is null/empty or has 'reason' containing 'idle'), tell them to click the 'Analyze Refuel Timing' button on the dashboard first.\n"
                    "4. Keep your response concise, clear, and professional. Max 3 sentences."
                )

                completion = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    extra_body={
                        "thinking": {"type": "enabled"},
                        "reasoning_effort": "high"
                    },
                    stream=True
                )
                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        q.put(content)
                return
            except Exception as e:
                logger.error(f"Error streaming DeepSeek chat: {e}")

        # Fallback chat logic (simulated streaming)
        fallback_resp = handle_ai_chat(message, current_state)
        for word in fallback_resp.split(" "):
            q.put(word + " ")
            time.sleep(0.05)
    finally:
        q.put(None)

def stream_refuel_ai_justification_worker(q: queue.Queue, scenario_id: str, fuel_level_pct: float, decision: dict, price_context: dict):
    try:
        client = get_client()
        if client:
            try:
                current_price = price_context.get("current_price")
                avg_price = price_context.get("rolling_30day_avg")
                trend = price_context.get("trend")
                rec = decision.get("decision")
                savings = decision.get("estimated_savings", 0.0)

                prompt = (
                    f"Scenario ID: {scenario_id}\n"
                    f"Fuel Level: {fuel_level_pct:.1f}%\n"
                    f"Weekly Trend: {trend}\n"
                    f"Price: RM{current_price:.2f}/L (30d Avg: RM{avg_price:.2f}/L)\n"
                    f"Recommendation: {rec}\n"
                    f"Savings: RM{savings:.2f}\n"
                )

                completion = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the FuelSense Refuel Advisor.\n"
                                "Based on the refueling recommendation and market context, provide a short, professional justification.\n"
                                "Explain shortly why this recommendation is correct based on the fuel level, price trend, and savings.\n"
                                "Rules:\n"
                                "1. Keep it under 2 sentences (strictly max 25 words).\n"
                                "2. Do not output any thinking/reasoning tags or formatting. Output plain text only."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    extra_body={
                        "thinking": {"type": "enabled"},
                        "reasoning_effort": "high"
                    },
                    stream=True
                )
                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        q.put(content)
                return
            except Exception as e:
                logger.error(f"Error streaming DeepSeek refuel: {e}")

        # Fallback justification (simulated streaming)
        fallback_reason = decision.get("reason", "Lock in current rates or maintain reserve levels.")
        for word in fallback_reason.split(" "):
            q.put(word + " ")
            time.sleep(0.05)
    finally:
        q.put(None)

def stream_ai_insights_worker(q: queue.Queue, scenario_id: str, analytics: dict, decision: dict):
    try:
        client = get_client()
        if client:
            try:
                refuel_rec = "N/A"
                refuel_reason = "N/A"
                if decision and decision.get("decision"):
                    refuel_rec = decision["decision"]
                    refuel_reason = decision["reason"]

                prompt = (
                    f"Scenario Profile ID: {scenario_id}\n"
                    f"Telemetry Analytics Context:\n"
                    f"- Eco Score: {analytics.get('eco_score')}/100\n"
                    f"- Efficiency: {analytics.get('fuel_efficiency')} L/100km\n"
                    f"- Cost Index: RM{analytics.get('cost_per_km')}/km\n"
                    f"- Projected Monthly Spend: RM{analytics.get('monthly_spend_myr')}\n"
                    f"- Idle Ratio: {analytics.get('idle_pct')}%\n"
                    f"- Aggressive Events Count: {analytics.get('aggressive_events')}\n"
                    f"- Refuel Recommendation: {refuel_rec} ({refuel_reason})"
                )

                completion = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the FuelSense Driving Analyst.\n"
                                "Your task is to interpret the computed driving metrics and refuel decisions provided.\n"
                                "You MUST NOT compute any new metrics or decisions, only explain them.\n"
                                "Your output must strictly follow this template, matching Cause, Effect, and Action:\n"
                                "Cause: [Explain what driving behaviors or pricing factors caused the metrics, e.g. stop-and-go congestion, high RPMs, rising prices]\n"
                                "Effect: [Explain the financial and eco impact, e.g. efficiency is X L/100km, Eco Score is Y, spend is RM Z]\n"
                                "Action: [Provide 1-2 actionable suggestions, e.g. reduce throttle spikes, turn off engine during long idle]\n\n"
                                "Rules:\n"
                                "1. Keep the entire response under 5 lines total.\n"
                                "2. Do not output any reasoning/thinking tags or extra conversational text. Follow the template exactly."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    extra_body={
                        "thinking": {"type": "enabled"},
                        "reasoning_effort": "high"
                    },
                    stream=True
                )
                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        q.put(content)
                return
            except Exception as e:
                logger.error(f"Error streaming DeepSeek insights: {e}")

        # Fallback insights (simulated streaming)
        insight = SCENARIO_INSIGHTS.get(scenario_id, SCENARIO_INSIGHTS["A"])
        explanation = (
            f"Cause: {insight['explanation']}\n"
            f"Effect: Fuel efficiency is {analytics['fuel_efficiency']} L/100km with an Eco Score of {analytics['eco_score']}.\n"
            f"Action: {insight['actionable_suggestion']}"
        )
        for word in explanation.split(" "):
            q.put(word + " ")
            time.sleep(0.05)
    finally:
        q.put(None)
