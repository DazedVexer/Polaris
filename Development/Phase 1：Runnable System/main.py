from config import validate_config
from prompt_builder import sys_prompt_builder
from llm_client import chat_stream
from session_manger import create_session, save_message
from memory import ShortTermMemory

def main():
    validate_config()

    print("[Polaris] 正在加载规则...")
    system_prompt = sys_prompt_builder()

    memory = ShortTermMemory(system_prompt)

    session_file = create_session()
    print(f"[Polaris] Session 已创建：{session_file.name}")

    BANNER = r"""
  ┌──────────────────────────────────────┐
  │             Polaris  v1.0            │
  │   Personal AI Executive Assistant    │
  │          Phase 1 · CLI Agent         │
  └──────────────────────────────────────┘
"""
    print("\n" + "=" * 50)
    print(BANNER)
    print("输入 /exit 退出  |  /save 手动存档  |  /help 查看帮助")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() == "/exit":
            break
        if user_input.lower() == "/save":
            print(f"[Polaris] 当前 session 已自动保存至 {session_file.name}")
            continue

        memory.add_user_message(user_input)
        save_message(session_file, "user", user_input)

        try:
            messages = memory.get_messages()
            print("Polaris: ", end="", flush=True)
            response = chat_stream(messages)
        except Exception as e:
            response = f"[错误] LLM 调用失败：{e}"
            print(f"\n{response}")
            save_message(session_file, "system", response)
            continue

        memory.add_assistant_message(response)
        save_message(session_file, "assistant", response)

    print(f"\n[Polaris] 对话结束。Session 已保存至 sessions/{session_file.name}")

if __name__ == "__main__":
    main()
