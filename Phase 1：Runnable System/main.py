from config import validate_config
from prompt_builder import build_system_prompt
from llm_client import chat_stream
from session_manager import create_session, save_message
from memory import ShortTermMemory

def main():
    validate_config()                                                   # config.py，验证配置文件

    print("[CompassY] 正在加载规则...")
    system_prompt = build_system_prompt()                               # prompt_builder.py，构建系统提示

    memory = ShortTermMemory(system_prompt)                             # memory.py，初始化记忆

    session_file = create_session()                                     # session_manager.py，创建会话文件
    print(f"[CompassY] Session 已创建：{session_file.name}")

    BANNER = r"""                                                       
      ┌──────────────────────────────────────┐
      │          CompassY  v1.0              │
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
            user_input = input("You: ").strip()                                 # 获取用户输入，去掉首尾空格
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:                                                      # 如果用户输入为空，跳过
            continue
        if user_input.lower() == "/exit":                                       # 如果用户输入是 /exit，退出循环
            break
        if user_input.lower() == "/save":                                       # 如果用户输入是 /save，手动存档
            print(f"[CompassY] 当前 session 已自动保存至 {session_file.name}")
            continue

        # 记录用户消息
        memory.add_user_message(user_input)
        save_message(session_file, "user", user_input)

        # 调用 LLM
        try:
            messages = memory.get_messages()
            print("CompassY: ", end="", flush=True)
            response = chat_stream(messages)
        except Exception as e:
            response = f"[错误] LLM 调用失败：{e}"
            print(f"\n{response}")
            save_message(session_file, "system", response)
            continue

        # 记录 AI 回复
        memory.add_assistant_message(response)
        save_message(session_file, "assistant", response)

    print(f"\n[CompassY] 对话结束。Session 已保存至 sessions/{session_file.name}")

if __name__ == "__main__":
    main()

