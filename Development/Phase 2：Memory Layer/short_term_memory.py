from config import STM_WindowSize, STM_SUMMARY_TRIGGER

class ShortTermMemory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.history: list[dict] = []
        self._summarize_count = 0

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        recent = self.history[-(STM_WindowSize * 2):]
        return [{"role": "system", "content": self.system_prompt}] + recent

    def needs_summarization(self) -> bool:
        """是否需要触发总结？（由外部 memory_manager 判断后调用）"""
        return len(self.history) >= STM_SUMMARY_TRIGGER * 2

    def get_slice_to_summarize(self) -> list[dict]:
        """
        取出需要被总结的旧消息（前 N 轮），并从 history 中裁掉它们。
        返回值是准备送给 LLM 做总结的消息列表。
        """
        keep_count = STM_WindowSize * 2
        old = self.history[:-keep_count] if len(self.history) > keep_count else []
        self.history = self.history[-keep_count:]
        self._summarize_count += 1
        return old

    def get_summary(self) -> str:
        user_msgs = [m["content"] for m in self.history if m["role"] == "user"]
        return " > ".join(user_msgs[-3:])