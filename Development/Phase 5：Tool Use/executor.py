import json
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
    Phase 5 升级版：支持工具调用（Function Calling）。
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
        """执行单个步骤（Phase 5 升级版：支持工具调用）"""
        step_num = step["step"]
        action = step.get("action", "")
        expected = step.get("expected_output", "")

        previous_context = self._build_previous_context(step)

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

请完成当前步骤。如果需要调用外部工具（天气、GitHub、文件操作），请直接调用。"""

        try:
            llm_result = self._call_llm_with_tools(prompt)

            max_tool_rounds = 3
            tool_round = 0

            while llm_result["type"] == "tool_call" and tool_round < max_tool_rounds:
                tool_round += 1
                tool_name = llm_result["tool_name"]
                tool_args = llm_result["tool_arguments"]

                print(f"  [Tools] 🔧 调用工具：{tool_name}({tool_args})")

                from tool_registry import get_tool_registry
                registry = get_tool_registry()
                tool_result = registry.execute(tool_name, tool_args)

                print(f"  [Tools] 📥 工具返回：{str(tool_result)[:200]}")

                from openai import OpenAI
                from config import LLM_CONFIG

                client = OpenAI(
                    api_key=LLM_CONFIG["api_key"],
                    base_url=LLM_CONFIG["base_url"],
                    timeout=120.0,
                    max_retries=2,
                )

                tools = registry.get_openai_tools()

                followup_response = client.chat.completions.create(
                    model=LLM_CONFIG["model"],
                    messages=[
                        {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args, ensure_ascii=False),
                                }
                            }]
                        },
                        {
                            "role": "tool",
                            "tool_call_id": "call_1",
                            "content": tool_result if isinstance(tool_result, str)
                                      else json.dumps(tool_result, ensure_ascii=False),
                        },
                    ],
                    temperature=AGENT_EXECUTE_TEMPERATURE,
                    max_tokens=2000,
                    tools=tools,
                )

                followup = followup_response.choices[0].message

                if followup.tool_calls:
                    tool_call = followup.tool_calls[0]
                    llm_result = {
                        "type": "tool_call",
                        "tool_name": tool_call.function.name,
                        "tool_arguments": json.loads(tool_call.function.arguments),
                    }
                else:
                    llm_result = {
                        "type": "text",
                        "content": followup.content or "",
                    }

            response_text = llm_result.get("content", "")

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
        depends_on = current_step.get("depends_on", [])

        if not depends_on:
            if len(self.step_results) >= 1:
                prev = self.step_results[-1]
                return self._truncate(
                    f"第 {prev['step']} 步结果：\n{prev['result']}"
                )
            return ""

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
        """基础 LLM 调用（无工具支持）"""
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

    def _call_llm_with_tools(self, prompt: str) -> dict:
        """
        调用 LLM，支持 Function Calling。

        返回格式:
        {
          "type": "text" | "tool_call",
          "content": "...",                          # type=text 时
          "tool_name": "get_weather",                # type=tool_call 时
          "tool_arguments": {"city": "Beijing"},     # type=tool_call 时
        }
        """
        from openai import OpenAI
        from config import LLM_CONFIG
        from tool_registry import get_tool_registry

        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=120.0,
            max_retries=2,
        )

        registry = get_tool_registry()
        tools = registry.get_openai_tools() if registry.list_tools() else None

        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=AGENT_EXECUTE_TEMPERATURE,
            max_tokens=2000,
            tools=tools,
        )

        message = response.choices[0].message

        # 检查是否有工具调用
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return {
                "type": "tool_call",
                "tool_name": tool_call.function.name,
                "tool_arguments": json.loads(tool_call.function.arguments),
            }
        else:
            return {
                "type": "text",
                "content": message.content or "",
            }
