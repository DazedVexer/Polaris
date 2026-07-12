from config import RULES_DIR

def sys_prompt_builder(mode_hint: dict = None, anomalies: list[dict] = None) -> str:
    if not RULES_DIR.exists():
        return "You are Polaris, a Personal AI Executive Assistant."

    prompt_list = []
    rule_files = sorted(RULES_DIR.glob("*.md"))
    for f in rule_files:
        prompt_list.append(f.read_text(encoding="utf-8"))

    base_prompt = ("\n---\n".join(prompt_list) +
                   "\n---\nYou are now interacting with users as Polaris. Please strictly adhere to all the rules above")

    if mode_hint:
        mood = mode_hint.get("mood", "neutral")
        intent = mode_hint.get("intent", "chatting")
        dynamic_section = _build_emotion_guide(mood, intent, anomalies)
        if dynamic_section:
            base_prompt = base_prompt + "\n---\n" + dynamic_section

    return base_prompt


def _build_emotion_guide(mood: str, intent: str, anomalies: list[dict] = None) -> str:
    lines = ["# Current Round Behavior Guide (Dynamic Injection)", ""]

    if mood in ("anxious", "sad", "frustrated"):
        lines.append("- User mood is low. Prioritize empathy and listening. Do not rush to solutions.")
    elif mood == "angry":
        lines.append("- User is angry. Validate feelings first, avoid analysis or defense.")
    elif mood in ("happy", "excited"):
        lines.append("- User is in good spirits. Match their energy genuinely.")
    elif mood == "tired":
        lines.append("- User is tired. Acknowledge it and determine if rest or adjustment is needed.")

    if intent == "venting":
        lines.append("- User is venting. Core priority: listen and validate. Do not solve problems.")
        lines.append("- After user calms down, consider if switching to agent mode is appropriate.")
    elif intent == "consulting":
        lines.append("- User is consulting. Be data-driven and actionable.")
        lines.append("- If the question involves data analysis, proactively suggest using Agent mode.")
        lines.append('- Phrase suggestion naturally, e.g. "Shall I run a full analysis on this?"')
    elif intent == "planning":
        lines.append("- Help user structure thoughts: Goal → Current → Gap → Steps")
        lines.append("- If user mentions specific data points, suggest Agent mode for deeper analysis.")
    elif intent == "sharing":
        lines.append("- User is sharing. Show interest and extend the conversation.")

    if anomalies:
        lines.append("")
        lines.append("- User data anomalies detected. Consider mentioning in response if relevant:")
        for a in anomalies:
            lines.append(f"  · {a.get('message', '')}")
        lines.append("- If anomalies suggest a pattern, propose Agent mode for comprehensive review.")

    return "\n".join(lines)
