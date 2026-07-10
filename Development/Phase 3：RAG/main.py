from config import validate_config
from prompt_builder import sys_prompt_builder
from llm_client import chat_stream
from session_manger import create_session, save_message
from short_term_memory import ShortTermMemory
from memory_manager import MemoryManager
from long_term_memory import init_db, get_memory_count, rebuild_embedding_column, sync_all_to_vector_db
from retrieval_pipeline import build_retrieval_context
from knowledge_base import build_knowledge_base

def main():
    validate_config()

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
  │             Polaris  v3.0            │
  │   Personal AI Executive Assistant    │
  │     Phase 3 · RAG Knowledge System   │
  └──────────────────────────────────────┘
  """
    print("\n" + "=" * 50)
    print(BANNER)
    print("输入 /exit 退出  |  /save 手动存档  |  /kb 知识库  |  /help 查看帮助")
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
                      /help       - 显示此帮助
                    """)
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

        memory.add_user_message(user_input)
        save_message(session_file, "user", user_input)

        retrieval_context = build_retrieval_context(user_input)
        temp_extra = []
        if retrieval_context:
            temp_extra.append({
                "role": "system",
                "content": retrieval_context,
            })

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
