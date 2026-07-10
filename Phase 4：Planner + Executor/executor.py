from config import (
    AGENT_MAX_STEPS,
    AGENT_EXECUTE_TEMPERATURE,
    AGENT_MAX_CONTEXT_LENGTH,
)


EXECUTOR_SYSTEM_PROMPT = """你是一个任务执行器。你会收到一个具体的执行步骤、任务的整体目标，以及前面步骤的执行结果。

要求：
1. 你只需要完成当前这一步，不要尝试做后续步骤。
2. 如果这一步需要用到前面步骤的结果，请在回答中引用。
3. 输出应该直接是这一步的「产出结果」，不要加"我来执行第 X 步"之类的前缀。
4. 如果你认为无法完成当前步骤（缺少信息或条件不满足），请说明原因并建议修正方案。

你的输出将作为下一步的输入或最终结果呈现给用户。"""


class Executor:
    """
    逐步执行器：逐步执行计划中的步骤。
    """

    def __init__(self):
        self.step_results: list[dict] = []   # 每一步的执行结果
        self.current_step = 0

    def execute_plan(
        self,
        plan_data: dict,
        user_instruction: str,
        extra_context: str = "",
    ) -> list[dict]:
        """
        执行整个计划，返回每一步的结果。

        返回格式:
        [
            {"step": 1, "action": "...", "result": "...", "status": "ok"},
            {"step": 2, "action": "...", "result": "...", "status": "ok"},
        ]
        """
        self.step_results = []
        steps = plan_data.get("steps", [])

        if not steps:
            return []

        for step in steps:
            if self.current_step >= AGENT_MAX_STEPS:
                self.step_results.append({
                    "step": step["step"],
                    "action": step.get("action", ""),
                    "result": "[系统] 已达到最大步数限制，任务中止。",
                    "status": "stopped",
                })
                break

            self.current_step = step["step"]
            result = self._execute_single_step(step, plan_data["goal"], user_instruction, extra_context)
            self.step_results.append(result)

        return self.step_results

    def _execute_single_step(
        self,
        step: dict,
        goal: str,
        user_instruction: str,
        extra_context: str,
    ) -> dict:
        """执行单个步骤"""
        step_num = step["step"]
        action = step.get("action", "")
        expected = step.get("expected_output", "")

        # 构建上下文：之前步骤的结果
        previous_context = self._build_previous_context(step)

        # 构建 prompt
        prompt = f"""任务目标：{goal}

用户原始指令：{user_instruction}

额外背景：{extra_context if extra_context else "（无）"}

之前步骤的结果：
{previous_context if previous_context else "（这是第一步，没有之前的结果）"}

---
当前步骤（第 {step_num} 步）：
{action}

预期产出：{expected}
---

请完成当前步骤，输出该步骤的结果："""

        try:
            response_text = self._call_llm(prompt)

            return {
                "step": step_num,
                "action": action,
                "result": response_text,
                "expected": expected,
                "status": "ok",
            }
        except Exception as e:
            return {
                "step": step_num,
                "action": action,
                "result": f"[执行失败] {str(e)}",
                "expected": expected,
                "status": "error",
            }

    def _build_previous_context(self, current_step: dict) -> str:
        """构建之前步骤的上下文（只包含当前步骤依赖的步骤结果）"""
        depends_on = current_step.get("depends_on", [])

        if not depends_on:
            # 没有显式依赖：传入上一步的结果
            if len(self.step_results) >= 1:
                prev = self.step_results[-1]
                return self._truncate(
                    f"第 {prev['step']} 步结果：\n{prev['result']}"
                )
            return ""

        # 有显式依赖：只传入被依赖步骤的结果
        lines = []
        for dep_step_num in depends_on:
            for r in self.step_results:
                if r["step"] == dep_step_num:
                    lines.append(f"第 {dep_step_num} 步结果（被当前步骤依赖）：\n{r['result']}")
                    break

        return self._truncate("\n\n".join(lines))

    def _truncate(self, text: str) -> str:
        """截断过长上下文"""
        if len(text) > AGENT_MAX_CONTEXT_LENGTH:
            return text[:AGENT_MAX_CONTEXT_LENGTH] + "\n...（上下文已截断）"
        return text

    def _call_llm(self, prompt: str) -> str:
        from openai import OpenAI
        from config import LLM_CONFIG

        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=120.0,
            max_retries=2,
        )

        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=AGENT_EXECUTE_TEMPERATURE,
            max_tokens=2000,
        )

        return response.choices[0].message.content or ""
