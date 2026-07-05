from config import MAX_SHORT_TERM_TURNS


class ShortTermMemory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.history: list[dict] = []

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        recent = self.history[-(MAX_SHORT_TERM_TURNS * 2):]  # 活动窗口，最近 MAX_SHORT_TERM_TURNS 轮对话
        return [{"role": "system", "content": self.system_prompt}] + recent

    # 预设方法，后续Phase计划
    def get_summary(self) -> str:
        user_msgs = [m["content"] for m in self.history if m["role"] == "user"]
        return " > ".join(user_msgs[-3:])