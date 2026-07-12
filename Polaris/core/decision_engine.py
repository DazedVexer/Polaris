import json
from llm.llm_client import chat_completion

DECISION_PROMPT = """You are a decision engine for an AI agent. Based on the following information, determine what action to take.

User message: {user_message}
Perception: mood={mood}, intent={intent}, intensity={intensity}
Data anomalies: {anomalies}
User profile: {profile}

Available actions:
- chat          : Normal chat, no special handling needed
- suggest_agent : Propose using Agent mode to the user
- auto_agent    : Silently start Agent (read-only, low-risk tasks only)
- alert         : Proactively notify the user about something
- ask_user      : Need user confirmation before proceeding

Return JSON only (no markdown, no code fences):
{{"action": "chat", "reason": "brief reason in English", "agent_task": ""}}
"""


def decide(user_message: str, mood: str, intent: str, intensity: str,
           anomalies: list[dict] = None, profile: str = "") -> dict:

    if anomalies is None:
        anomalies = []

    if intensity == "high" and mood in ("anxious", "sad", "frustrated", "angry"):
        return {
            "action": "suggest_agent",
            "reason": "High intensity negative emotion detected",
            "agent_task": "Analyze recent emotional patterns and identify possible causes"
        }

    if len(anomalies) >= 2:
        anomaly_msgs = [a.get("message", "") for a in anomalies]
        return {
            "action": "suggest_agent",
            "reason": "Multiple data anomalies detected",
            "agent_task": f"Review the following anomalies and generate a summary: {'; '.join(anomaly_msgs)}"
        }

    if anomalies:
        return {
            "action": "suggest_agent",
            "reason": "Data anomaly detected",
            "agent_task": anomalies[0].get("message", "Review anomaly")
        }

    if intent in ("consulting", "planning"):
        prompt = DECISION_PROMPT.format(
            user_message=user_message,
            mood=mood,
            intent=intent,
            intensity=intensity,
            anomalies=json.dumps(anomalies, ensure_ascii=False) if anomalies else "none",
            profile=profile or "no profile data"
        )
        try:
            response = chat_completion(
                [{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result = json.loads(response.strip())
            return result
        except Exception:
            return {"action": "chat", "reason": "LLM fallback", "agent_task": ""}

    return {"action": "chat", "reason": "No trigger for agent mode", "agent_task": ""}
