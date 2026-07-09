from config import STM_WindowSize

class ShortTermMemory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.history: list[dict] = []

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        recent = self.history[-(STM_WindowSize * 2):]
        return [{"role": "system", "content": self.system_prompt}] + recent

    def get_summary(self) -> str:
        user_msgs = [m["content"] for m in self.history if m["role"] == "user"]
        return " > ".join(user_msgs[-3:])
