"""
BangBand 感知层：分析用户输入的情绪和意图。
每轮对话前调用一次，轻量 LLM 调用，静默运行（无 UI 输出）。
"""

PERCEPTION_PROMPT = """分析以下用户消息的情绪和意图。只返回 JSON，不要解释。

情绪标签（mood）：neutral / happy / anxious / sad / angry / frustrated / excited / tired
意图标签（intent）：venting（发泄）/ sharing（分享）/ consulting（咨询）/ planning（规划）/ chatting（闲聊）/ tasking（任务）
强度（intensity）：low / medium / high

用户消息：
---
{user_message}
---

仅返回 JSON："""


def analyze(user_message: str) -> dict:
    """
    分析一条用户消息，返回 mood / intent / intensity。

    返回示例：
        {"mood": "frustrated", "intent": "venting", "intensity": "high"}

    失败时兜底：
        {"mood": "neutral", "intent": "chatting", "intensity": "low"}
    """
    import json
    from openai import OpenAI
    from config import LLM_CONFIG

    client = OpenAI(
        api_key=LLM_CONFIG["api_key"],
        base_url=LLM_CONFIG["base_url"],
        timeout=10.0,
        max_retries=0,
    )

    prompt = PERCEPTION_PROMPT.format(user_message=user_message)

    try:
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": "你只输出 JSON，不要加任何解释。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        raw = response.choices[0].message.content or "{}"
        result = json.loads(raw)
        return {
            "mood": result.get("mood", "neutral"),
            "intent": result.get("intent", "chatting"),
            "intensity": result.get("intensity", "low"),
        }
    except Exception:
        return {"mood": "neutral", "intent": "chatting", "intensity": "low"}
