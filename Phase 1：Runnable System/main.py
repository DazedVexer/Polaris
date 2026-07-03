from prompt_builder import build_system_prompt
from llm_client import chat
from session_manager import create_session, save_message
from memory import ShortTermMemory

def main():
    # 1. 构建 system prompt
    print("[CompassY] 正在加载规则...")
    system_prompt = build_system_prompt()

    # 2. 初始化记忆
    memory = ShortTermMemory(system_prompt)

    # 3. 创建 session 文件
    session_file = create_session()
    print(f"[CompassY] Session 已创建：{session_file.name}")

    # 4. 对话循环
    print("\n" + "=" * 50)
    print("CompassY MVP Agent 已启动")
    print("输入 /exit 退出，/save 手动存档")
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
            print(f"[CompassY] 当前 session 已自动保存至 {session_file.name}")
            continue

        # 记录用户消息
        memory.add_user_message(user_input)
        save_message(session_file, "user", user_input)

        # 调用 LLM
        try:
            messages = memory.get_messages()
            response = chat(messages)
        except Exception as e:
            response = f"[错误] LLM 调用失败：{e}"

        # 记录 AI 回复
        memory.add_assistant_message(response)
        save_message(session_file, "assistant", response)

        print(f"\nCompassY: {response}\n")

    print(f"\n[CompassY] 对话结束。Session 已保存至 sessions/{session_file.name}")

if __name__ == "__main__":
    main()