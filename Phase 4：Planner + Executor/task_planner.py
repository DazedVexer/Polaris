import json
from config import AGENT_PLAN_TEMPERATURE


PLANNER_SYSTEM_PROMPT = """你是一个任务规划器。你会收到用户的指令，你需要将它拆解为 3~7 个可执行步骤。

规则：
1. 每个步骤是「一个 LLM 调用能完成」的粒度。不要拆得太细（如"打开文件"），也不要太粗（如"完成整个分析"）。
2. 步骤按顺序排列，后一步可以引用前一步的结果。
3. 如果指令很简单（一问一答就能完成），返回 1 个步骤即可。
4. 为每个步骤指定 expected_output（预期产出），方便后续检查。

返回格式（严格的 JSON，不要包含其他内容）：
{
  "task_id": "task_001",
  "goal": "一句话概括任务目标",
  "complexity": "simple|medium|complex",
  "steps": [
    {
      "step": 1,
      "action": "要做什么",
      "reasoning": "为什么需要这一步",
      "expected_output": "这步完成后应该产出什么",
      "depends_on": []
    },
    {
      "step": 2,
      "action": "下一步做什么",
      "reasoning": "为什么需要这一步",
      "expected_output": "这步完成后应该产出什么",
      "depends_on": [1]
    }
  ]
}"""


def plan(user_instruction: str, context: str = "") -> dict:
    """
    将用户指令拆解为可执行步骤。

    参数:
        user_instruction: 用户原始指令
        context: 可选上下文（从记忆/知识库检索到的背景信息）

    返回:
        {"task_id": "...", "goal": "...", "steps": [...], "complexity": "..."}
    """
    from openai import OpenAI
    from config import LLM_CONFIG

    client = OpenAI(
        api_key=LLM_CONFIG["api_key"],
        base_url=LLM_CONFIG["base_url"],
        timeout=60.0,
        max_retries=1,
    )

    user_prompt = f"""用户指令：
---
{user_instruction}
---

背景信息：
---
{context if context else "（无额外背景信息）"}
---

请拆解任务步骤："""

    try:
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=AGENT_PLAN_TEMPERATURE,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content or "{}"

        # 清理 LLM 可能的 markdown 包裹
        raw = raw.strip()
        if raw.startswith("```"):
            # 去掉 ```json 和结尾的 ```
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        plan_data = json.loads(raw)

        # 校验必填字段
        if "steps" not in plan_data:
            raise ValueError("规划结果缺少 steps 字段")

        return plan_data

    except (json.JSONDecodeError, Exception) as e:
        # Fallback：如果规划失败，返回一个「直接执行」的兜底计划
        return {
            "task_id": "fallback",
            "goal": user_instruction[:100],
            "complexity": "simple",
            "steps": [
                {
                    "step": 1,
                    "action": user_instruction,
                    "reasoning": "规划失败，直接执行用户指令",
                    "expected_output": "用户的指令结果",
                    "depends_on": [],
                }
            ],
        }


def format_plan(plan_data: dict) -> str:
    """将计划格式化为人类可读文本（用于打印给用户确认）"""
    lines = [
        f"📋 任务目标：{plan_data.get('goal', '未知')}",
        f"📊 复杂度：{plan_data.get('complexity', 'simple')}",
        f"📝 共 {len(plan_data.get('steps', []))} 个步骤：",
    ]
    for s in plan_data.get("steps", []):
        deps = f"（依赖步骤 {s['depends_on']}）" if s.get("depends_on") else ""
        lines.append(f"  {s['step']}. {s['action']} {deps}")
        lines.append(f"     → 预期产出：{s.get('expected_output', '-')}")
    return "\n".join(lines)
