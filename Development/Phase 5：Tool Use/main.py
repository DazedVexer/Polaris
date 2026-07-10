from config import validate_config
from prompt_builder import sys_prompt_builder
from llm_client import chat_stream
from session_manger import create_session, save_message
from short_term_memory import ShortTermMemory
from memory_manager import MemoryManager
from long_term_memory import init_db, get_memory_count, rebuild_embedding_column, sync_all_to_vector_db
from retrieval_pipeline import build_retrieval_context
from knowledge_base import build_knowledge_base
from tools import register_all_tools
from agent_loop import AgentLoop

def main():
    validate_config()

    register_all_tools()

    init_db()

    mem_count = get_memory_count()
    if mem_count > 0:
        print(f"[Polaris] 记忆库中共有 {mem_count} 条长期记忆")
        rebuild_embedding_column()
        sync_all_to_vector_db()

    print("[Polaris] 正在加载知识库...")
    kb_chunks = build_knowledge_base()
    if kb_chunks > 0:
        print(f"[Polaris] 知识库就绪：{kb_chunks} 个文本块")

    print("[Polaris] 正在加载规则...")
    system_prompt = sys_prompt_builder()

    memory = ShortTermMemory(system_prompt)

    session_file = create_session()
    session_id = session_file.stem

    mem_mgr = MemoryManager(memory, session_id)

    print(f"[Polaris] Session 已创建：{session_file.name}")
    if mem_count > 0:
        print(f"[Polaris] 已加载 {mem_count} 条长期记忆")

    BANNER = r"""
  ┌──────────────────────────────────────┐
  │             Polaris  v5.0              │
  │   Personal AI Executive Assistant    │
  │    Phase 5 · Tool Use & Function     │
  │              Calling                 │
  └──────────────────────────────────────┘
  """
    print("\n" + "=" * 50)
    print(BANNER)
    print("输入 /exit 退出  |  /save 手动存档  |  /kb 知识库  |  /agent 任务  |  /tools 工具  |  /help 查看帮助")
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

        if user_input.lower() == "/help":
            print("""
                    [Polaris 命令列表]
                    /exit       - 退出对话
                    /save       - 手动存档当前 session
                    /kb         - 查看知识库状态
                    /rebuild_kb - 重建知识库
                    /memory     - 查看最近记忆
                    /agent      - 进入 Agent 模式（多步任务执行）
                    /tools      - 查看可用工具
                    /help       - 显示此帮助

                    [Agent 模式用法]
                    /agent 分析我的睡眠数据，对比运动记录，然后给出下周计划
                    （Polaris 会自动拆解任务 → 逐步执行 → 反思修正）
                """)
            continue

        if user_input.lower() == "/tools":
            from tool_registry import get_tool_registry
            registry = get_tool_registry()
            tools_list = registry.list_tools()
            if not tools_list:
                print("[Tools] 没有注册任何工具。")
            else:
                print(f"[Tools] 已注册 {len(tools_list)} 个工具：")
                for name in tools_list:
                    t = registry.get(name)
                    print(f"  🔧 {name}: {t['description']}")
            continue

        if user_input.lower() == "/kb":
            from knowledge_base import load_documents
            docs = load_documents()
            if not docs:
                print("[Polaris] 知识库为空。请将 .md / .pdf 文件放入 kb/ 目录。")
            else:
                print(f"[Polaris] 知识库状态：{len(docs)} 个文档")
                for d in docs:
                    print(f"  - {d['file']} ({len(d['content'])} 字符)")
            continue

        if user_input.lower() == "/rebuild_kb":
            print("[Polaris] 正在重建知识库...")
            kb_chunks = build_knowledge_base(force_rebuild=True)
            print(f"[Polaris] 知识库重建完成：{kb_chunks} 个文本块")
            continue

        if user_input.lower().startswith("/agent"):
            instruction = user_input[6:].strip()
            if not instruction:
                instruction = input("请输入任务指令：").strip()

            if not instruction:
                print("[Agent] 指令为空，已取消。")
                continue

            retrieval_context = build_retrieval_context(instruction)

            def on_step(step_num, result):
                status_icon = "✅" if result["status"] == "ok" else "❌"
                print(f"\n  {status_icon} 第 {step_num} 步完成")
                print(f"  {result.get('result', '')[:300]}")
                print()

            agent = AgentLoop()
            result = agent.run(
                user_instruction=instruction,
                context=retrieval_context,
                on_step=on_step,
            )

            print("\n" + "=" * 50)
            print(result["summary"])
            print("=" * 50 + "\n")

            memory.add_assistant_message(result["summary"])
            save_message(session_file, "assistant", f"[Agent 模式] {result['summary']}")

            mem_mgr.maybe_extract()
            mem_mgr.maybe_summarize()
            continue

        # 记录用户消息
        memory.add_user_message(user_input)
        save_message(session_file, "user", user_input)

        retrieval_context = build_retrieval_context(user_input)
        temp_extra = []
        if retrieval_context:
            temp_extra.append({
                "role": "system",
                "content": retrieval_context,
            })

        # 调用 LLM
        try:
            messages = memory.get_messages()
            full_messages = [messages[0]] + temp_extra + messages[1:]
            print("Polaris: ", end="", flush=True)
            response = chat_stream(full_messages)
        except Exception as e:
            response = f"[错误] LLM 调用失败：{e}"
            print(f"\n{response}")
            save_message(session_file, "system", response)
            memory.add_assistant_message(response)
            save_message(session_file, "assistant", response)
            mem_mgr.maybe_extract()
            mem_mgr.maybe_summarize()
            continue

        # 记录 AI 回复
        memory.add_assistant_message(response)
        save_message(session_file, "assistant", response)

        mem_mgr.maybe_extract()
        mem_mgr.maybe_summarize()

    print(f"\n[Polaris] 对话结束。Session 已保存至 sessions/{session_file.name}")
    print(f"[Polaris] 记忆库中共有 {get_memory_count()} 条长期记忆")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(e)
    except KeyboardInterrupt:
        print()
