from config import RULES_DIR

def sys_prompt_builder(mode_hint: dict = None) -> str:
    """
    构建 system prompt。
    mode_hint 可选，用于 BangBand 动态注入情绪模式指令。
    格式：{"mood": "anxious", "intent": "consulting"}
    """
    if not RULES_DIR.exists():
        return "You are Polaris, a Personal AI Executive Assistant."

    prompt_list = []
    rule_files = sorted(RULES_DIR.glob("*.md"))
    for f in rule_files:
        prompt_list.append(f.read_text(encoding="utf-8"))

    base_prompt = ("\n---\n".join(prompt_list) +
                   "\n---\nYou are now interacting with users as Polaris. Please strictly adhere to all the rules above")

    # BangBand：动态注入情绪模式指令
    if mode_hint:
        mood = mode_hint.get("mood", "neutral")
        intent = mode_hint.get("intent", "chatting")
        dynamic_section = _build_emotion_guide(mood, intent)
        if dynamic_section:
            base_prompt = base_prompt + "\n---\n" + dynamic_section

    return base_prompt


def _build_emotion_guide(mood: str, intent: str) -> str:
    """根据 mood 和 intent 拼出当前轮次的行为指令（精简版）。"""
    lines = ["# 当前轮次行为指令（BangBand 动态注入）", ""]

    # 情绪模式
    if mood in ("anxious", "sad", "frustrated"):
        lines.append("- 用户当前情绪低落，优先共情和倾听，不要急于给解决方案")
        lines.append('- 避免空洞安慰（"别担心""会好起来的"）')
    elif mood == "angry":
        lines.append("- 用户当前有愤怒情绪，先确认感受，不要急着分析或辩解")
    elif mood in ("happy", "excited"):
        lines.append("- 用户心情不错，真诚回应这份能量，可以适当延伸思路")
    elif mood == "tired":
        lines.append("- 用户表达了疲惫，先确认感受，判断是需要休息还是调整节奏")

    # 意图模式
    if intent == "venting":
        lines.append("- 用户可能在发泄，核心是倾听和确认感受，不是解决问题")
        lines.append("- 等用户情绪缓和后，再判断是否需要切换模式")
    elif intent == "consulting":
        lines.append("- 用户正在咨询，按核心原则执行：数据驱动、方案可执行")
        lines.append("- 先确认理解是否正确，再展开分析")
    elif intent == "planning":
        lines.append("- 帮助用户结构化思考：目标 → 现状 → 差距 → 步骤")
    elif intent == "sharing":
        lines.append("- 用户在分享，表达兴趣，延伸对话方向")

    return "\n".join(lines)
