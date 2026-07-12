from .task_planner import plan, format_plan
from .executor import Executor
from .reflection import Reflection
from config import (
    AGENT_REFLECTION_ENABLED,
    AGENT_MAX_RETRIES,
)


class AgentLoop:
    """
    Agent 主循环：Plan → Execute → Reflect 直到任务完成或失败。

    使用示例：
        agent = AgentLoop()
        result = agent.run("分析我的睡眠数据并给出建议", context="...")
        print(result.summary)
    """

    def __init__(self):
        self.planner_steps = None
        self.executor = Executor()
        self.reflection = Reflection()
        self.plan_retry_count = 0

    def run(
        self,
        user_instruction: str,
        context: str = "",
        on_step: callable = None,
        silent: bool = False,
    ) -> dict:
        """
        执行 Agent 循环。

        参数:
            user_instruction: 用户指令
            context: 来自记忆库/知识库的上下文
            on_step: 可选回调，每步执行完调用 on_step(step_num, result)

        返回:
            {
                "success": True/False,
                "summary": "最终汇总",
                "plan": {...},
                "step_results": [...],
                "total_llm_calls": 5
            }
        """
        if not silent:
            print("\n[Agent] 🧠 正在规划任务...")
        plan_data = plan(user_instruction, context)
        self.planner_steps = plan_data.get("steps", [])

        if not silent:
            print(format_plan(plan_data))
            print(f"\n[Agent] 共 {len(self.planner_steps)} 步，开始执行...\n")

        # ===== Phase 2: Execute =====
        step_results = self.executor.execute_plan(
            plan_data, user_instruction, context
        )

        # 回调通知（用于流式显示进度）
        if on_step:
            for r in step_results:
                on_step(r["step"], r)

        # ===== Phase 3: Reflect =====
        if AGENT_REFLECTION_ENABLED:
            reflection_result = self.reflection.reflect(
                plan_data, step_results, user_instruction
            )
        else:
            reflection_result = {"overall": "pass", "next_action": "done"}

        # ===== Phase 4: 根据反思结果行动 =====
        while reflection_result.get("next_action") not in ("done", "ask_user"):
            action = reflection_result["next_action"]

            if action == "retry_step":
                failed_steps = reflection_result.get("failed_steps", [])
                if not silent:
                    print(f"\n[Agent] 重试失败步骤：{failed_steps}")

                for step_num in failed_steps:
                    step = self._find_step(plan_data, step_num)
                    if step:
                        retry_result = self.executor._execute_single_step(
                            step, plan_data["goal"], user_instruction, context
                        )
                        # 替换旧结果
                        for i, r in enumerate(step_results):
                            if r["step"] == step_num:
                                step_results[i] = retry_result
                                break

                        if on_step:
                            on_step(step_num, retry_result)

                # 再次反思
                reflection_result = self.reflection.reflect(
                    plan_data, step_results, user_instruction
                )

            elif action == "replan":
                self.plan_retry_count += 1
                if self.plan_retry_count > AGENT_MAX_RETRIES:
                    if not silent:
                        print(f"\n[Agent] 已重新规划 {AGENT_MAX_RETRIES} 次，放弃。")
                    break

                if not silent:
                    print(f"\n[Agent] 重新规划任务（第 {self.plan_retry_count} 次）...")
                failure_context = self._format_failure_context(step_results)
                plan_data = plan(user_instruction, context + "\n" + failure_context)
                self.planner_steps = plan_data.get("steps", [])

                if not silent:
                    print(format_plan(plan_data))

                # 重新执行
                self.executor = Executor()
                step_results = self.executor.execute_plan(
                    plan_data, user_instruction, context
                )

                if on_step:
                    for r in step_results:
                        on_step(r["step"], r)

                reflection_result = self.reflection.reflect(
                    plan_data, step_results, user_instruction
                )

            else:
                break

        # ===== 汇总 =====
        success = reflection_result.get("overall") == "pass"
        summary = self._build_summary(plan_data, step_results, success)

        return {
            "success": success,
            "summary": summary,
            "plan": plan_data,
            "step_results": step_results,
            "reflection": reflection_result,
        }

    def _find_step(self, plan_data: dict, step_num: int) -> dict | None:
        """在计划中找到指定步骤"""
        for s in plan_data.get("steps", []):
            if s["step"] == step_num:
                return s
        return None

    def _format_failure_context(self, step_results: list[dict]) -> str:
        """格式化失败上下文，用于重新规划"""
        failures = [r for r in step_results if r["status"] != "ok"]
        if not failures:
            return ""
        lines = ["[以下步骤执行失败，请在新计划中调整策略：]"]
        for r in failures:
            lines.append(f"- 步骤 {r['step']}（{r.get('action', '')}）失败：{r.get('result', '')[:200]}")
        return "\n".join(lines)

    def _build_summary(
        self,
        plan_data: dict,
        step_results: list[dict],
        success: bool,
    ) -> str:
        """构建最终摘要"""
        status = "✅ 成功" if success else "⚠ 部分完成"
        lines = [
            f"任务：{plan_data.get('goal', '未知')}",
            f"状态：{status}",
            f"执行步骤：{len(step_results)} 步",
            "",
            "--- 执行记录 ---",
        ]
        for r in step_results:
            flag = "✅" if r["status"] == "ok" else "❌"
            lines.append(f"{flag} 步骤 {r['step']}: {r.get('action', '')}")
            lines.append(f"   → {r.get('result', '')[:200]}")
            lines.append("")

        return "\n".join(lines)
