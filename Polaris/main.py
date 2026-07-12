from config import validate_config
from llm.prompt_builder import sys_prompt_builder
from llm.llm_client import chat_stream
from session.session_manger import create_session, save_message
from memory.short_term_memory import ShortTermMemory
from memory.memory_manager import MemoryManager
from memory.long_term_memory import init_db, get_memory_count, get_mood_count, rebuild_embedding_column, sync_all_to_vector_db
from retrieval.retrieval_pipeline import build_retrieval_context
from retrieval.knowledge_base import build_knowledge_base
from core.agent_loop import AgentLoop
from tools import register_all_tools
from perception.perception import analyze as perception_analyze
from core.monitor import DataMonitor
from core.decision_engine import decide as decision_decide

def main():
    validate_config()                                           # 验证 .env 配置

    # Phase 3：初始化数据库（含 embedding 迁移）
    init_db()                                                   # 初始化数据库连接

    # Phase 3：检查是否需要重建 embedding（Phase 2 → 3 迁移）
    mem_count = get_memory_count()                              # 获取长期记忆数量
    if mem_count > 0:                                           # 如果有长期记忆
        print(f"[Polaris] 记忆库中共有 {mem_count} 条长期记忆")     
        rebuild_embedding_column()    # 给旧记忆补充 embedding <long_term_memory.py>
        sync_all_to_vector_db()       # 同步到向量库 <long_term_memory.py>

    # Phase 3：构建知识库
    print("[Polaris] 正在加载知识库...")
    kb_chunks = build_knowledge_base()                          # 构建知识库 <knowledge_base.py>
    if kb_chunks > 0:                                           # 如果知识库构建成功
        print(f"[Polaris] 知识库就绪：{kb_chunks} 个文本块")

    # Phase 5：初始化工具注册中心
    register_all_tools()                                        # 注册所有工具 <tools.py>

    monitor = DataMonitor()

    print("[Polaris] 正在加载规则...")
    system_prompt = sys_prompt_builder()                        # 加载规则 Prompt

    memory = ShortTermMemory(system_prompt)                     # 创建短期记忆盒子

    session_file = create_session()                             # 创建 session JSON 文件
    session_id = session_file.stem                              # .stem去掉文件扩展名（后缀），只保留文件名主体

    mem_mgr = MemoryManager(memory, session_id)                 # 创建记忆管家

    print(f"[Polaris] Session 已创建：{session_file.name}")
    if mem_count > 0:
        print(f"[Polaris] 已加载 {mem_count} 条长期记忆")

    BANNER = r"""
  ┌──────────────────────────────────────┐
  │             Polaris  v6.0            │
  │   Personal AI Executive Assistant    │
  │      Phase 6 · Web + Deployment      │
  └──────────────────────────────────────┘
  """
    print("\n" + "=" * 50)
    print(BANNER)
    print("输入 /exit 退出  |  /save 手动存档  |  /kb 知识库  |  /agent 任务  |  /tools 工具  |  /help 查看帮助")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()                 # 获取用户输入，去掉首尾空格
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

        if user_input.lower() == "/tools":                      # 查看可用工具
            from tools.tool_registry import get_tool_registry    # 获取工具注册中心 <tools.py>
            registry = get_tool_registry()                      # 获取工具注册中心 <tools.py>
            tools_list = registry.list_tools()                  # 获取所有注册工具
            if not tools_list:
                print("[Tools] 没有注册任何工具。")
            else:
                print(f"[Tools] 已注册 {len(tools_list)} 个工具：")
                for name in tools_list:
                    t = registry.get(name)
                    print(f"  🔧 {name}: {t['description']}")
            continue

        if user_input.lower() == "/kb":
            from retrieval.knowledge_base import load_documents
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
            kb_chunks = build_knowledge_base(force_rebuild=True)  # 重建知识库 <knowledge_base.py>
            print(f"[Polaris] 知识库重建完成：{kb_chunks} 个文本块")
            continue

        if user_input.lower().startswith("/agent"):               # 分析我的睡眠数据并给出建议    
            instruction = user_input[6:].strip()                  # 去掉 /agent 前缀，去掉首尾空格
            if not instruction:
                instruction = input("请输入任务指令：").strip()

            if not instruction:
                print("[Agent] 指令为空，已取消。")
                continue

            
            retrieval_context = build_retrieval_context(instruction)    # 检索上下文 <knowledge_base.py>

            # 定义进度回调
            def on_step(step_num, result):
                status_icon = "✅" if result["status"] == "ok" else "❌"
                print(f"\n  {status_icon} 第 {step_num} 步完成")
                print(f"  {result.get('result', '')[:300]}")
                print()

            # 启动 Agent 循环
            agent = AgentLoop()
            result = agent.run(
                user_instruction=instruction,
                context=retrieval_context,
                on_step=on_step,
            )

            print("\n" + "=" * 50)
            print(result["summary"])
            print("=" * 50 + "\n")

            # 将 Agent 结果也记录到短期记忆
            memory.add_assistant_message(result["summary"])
            save_message(session_file, "assistant", f"[Agent 模式] {result['summary']}")

            # 记忆流程照常
            mem_mgr.maybe_extract()
            mem_mgr.maybe_summarize()
            continue

        # 记录用户消息
        memory.add_user_message(user_input)
        save_message(session_file, "user", user_input)

        perception_result = perception_analyze(user_input)
        mem_mgr.extract_emotion(user_input)
        memory.system_prompt = sys_prompt_builder(
            mode_hint=perception_result
        )

        anomalies = monitor.check()

        decision = decision_decide(
            user_message=user_input,
            mood=perception_result.get("mood", "neutral"),
            intent=perception_result.get("intent", "chatting"),
            intensity=perception_result.get("intensity", "low"),
            anomalies=anomalies,
            profile=monitor.get_mood_summary()
        )

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

        if decision["action"] in ("suggest_agent", "auto_agent", "alert"):
            if decision["action"] == "suggest_agent":
                task = decision.get("agent_task", "")
                if task:
                    response += f"\n\n[提议] 是否需要我进行深入分析？输入 /agent 加上你想做的任务即可。"
                    memory.history.append({"role": "system", "content": f"[Agent 提议] {task}"})
            elif decision["action"] == "auto_agent":
                agent = AgentLoop()
                agent_result = agent.run(
                    user_instruction=decision.get("agent_task", user_input),
                    context=retrieval_context,
                    on_step=None,
                    silent=True
                )
                summary = agent_result.get("summary", "")
                response += f"\n\n📊 [自主分析]\n{summary}"
            elif decision["action"] == "alert":
                response += f"\n\n⚠ [自动提醒] {decision.get('agent_task', '')}"

        memory.add_assistant_message(response)
        save_message(session_file, "assistant", response)

        mem_mgr.maybe_extract()
        mem_mgr.maybe_summarize()

    print(f"\n[Polaris] 对话结束。Session 已保存至 sessions/{session_file.name}")
    print(f"[Polaris] 记忆库中共有 {get_memory_count()} 条长期记忆")
    mood_c = get_mood_count()
    if mood_c > 0:
        print(f"[Polaris] 情绪日志中共有 {mood_c} 条记录")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(e)
    except KeyboardInterrupt:
        print()
