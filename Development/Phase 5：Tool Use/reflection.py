import json
from config import AGENT_REFLECT_TEMPERATURE, AGENT_MAX_RETRIES


REFLECTION_SYSTEM_PROMPT = """你是一个任务质量检查员。你会收到一个任务的原始计划、每一步的执行结果。

你的工作：检查每一步是否完成了预期的任务。

检查标准：
1. 输出是否与 expected_output 匹配？（不要求字面一致，但语义应相符）
2. 是否有明显的错误、遗漏或幻觉？
3. 如果某一步失败了，原因是什么？

返回格式（严格的 JSON）：
{
  "overall": "pass|fail|partial",
  "summary": "整体评估，一句话",
  "steps_check": [
    {
      "step": 1,
      "status": "pass|fail|retry",
      "reason": "通过/失败的原因",
      "suggestion": "如果失败，建议如何修正"
    }
  ],
  "next_action": "done|retry_step|replan|ask_user"
}"""


class Reflection:
    """反思模块：检查执行结果，决定下一步行动。"""

    def __init__(self):
        self.retry_counts: dict = {}   # step_num → retry count

    def reflect(
        self,
        plan_data: dict,
        step_results: list[dict],
        user_instruction: str,
    ) -> dict:
        """
        检查执行结果。

        返回:
        {
          "overall": "pass|fail|partial",
          "next_action": "done|retry_step|replan|ask_user",
          "failed_steps": [1, 3],  # 需要重试的步骤号
          "summary": "...",
        }
        """
        if not step_results:
            return {
                "overall": "fail",
                "next_action": "replan",
                "failed_steps": [],
                "summary": "没有执行结果",
            }

        # 简单任务跳过反思（节省 LLM 调用）
        if plan_data.get("complexity") == "simple":
            all_ok = all(r["status"] == "ok" for r in step_results)
            return {
                "overall": "pass" if all_ok else "partial",
                "next_action": "done" if all_ok else "retry_step",
                "failed_steps": [r["step"] for r in step_results if r["status"] != "ok"],
                "summary": "简单任务，快速检查通过" if all_ok else "部分步骤失败",
            }

        # 复杂任务：调 LLM 做深度反思
        reflection_prompt = self._build_reflection_prompt(
            plan_data, step_results, user_instruction
        )

        try:
            response = self._call_llm(reflection_prompt)
            reflection_data = json.loads(response)
        except (json.JSONDecodeError, Exception):
            # Fallback：默认通过
            return {
                "overall": "partial",
                "next_action": "done",
                "failed_steps": [],
                "summary": "反思模块解析失败，默认放行",
            }

        return self._parse_reflection(reflection_data, step_results)

    def _build_reflection_prompt(
        self,
        plan_data: dict,
        step_results: list[dict],
        user_instruction: str,
    ) -> str:
        """构建反思用的 prompt"""
        steps_text = "\n\n".join(
            f"--- 步骤 {r['step']} ---\n"
            f"action: {r.get('action', '')}\n"
            f"expected: {r.get('expected', '')}\n"
            f"status: {r.get('status', '')}\n"
            f"result: {r.get('result', '')[:800]}"
            for r in step_results
        )

        return f"""用户指令：{user_instruction}

任务目标：{plan_data.get('goal', '')}

执行结果：
{steps_text}

请评估以上执行结果的质量。"""

    def _parse_reflection(self, reflection_data: dict, step_results: list[dict]) -> dict:
        """解析 LLM 反思结果，合并重试计数"""
        overall = reflection_data.get("overall", "pass")
        steps_check = reflection_data.get("steps_check", [])
        next_action = reflection_data.get("next_action", "done")

        failed_steps = []
        for check in steps_check:
            step_num = check.get("step", 0)
            status = check.get("status", "pass")

            if status in ("fail", "retry"):
                # 检查是否超过最大重试次数
                self.retry_counts[step_num] = self.retry_counts.get(step_num, 0) + 1
                if self.retry_counts[step_num] <= AGENT_MAX_RETRIES:
                    failed_steps.append(step_num)
                else:
                    # 超过重试上限，不再重试
                    pass

        # 如果所有失败步骤都超了重试上限，转为 replan
        if not failed_steps and next_action == "retry_step":
            next_action = "replan"

        return {
            "overall": overall,
            "next_action": next_action,
            "failed_steps": failed_steps,
            "summary": reflection_data.get("summary", ""),
        }

    def _call_llm(self, prompt: str) -> str:
        from openai import OpenAI
        from config import LLM_CONFIG

        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=60.0,
            max_retries=1,
        )

        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=AGENT_REFLECT_TEMPERATURE,
            max_tokens=1000,
        )

        return response.choices[0].message.content or "{}"
