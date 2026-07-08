from config import MEMORY_RETRIEVAL_TOP_K, KB_RETRIEVAL_TOP_K


def retrieve_all(
    query: str,
    memory_top_k: int = MEMORY_RETRIEVAL_TOP_K,
    kb_top_k: int = KB_RETRIEVAL_TOP_K,
) -> dict:
    """
    统一检索入口：同时从记忆库和知识库检索。

    参数:
        query: 用户查询文本
        memory_top_k: 记忆检索条数
        kb_top_k: 知识库检索条数

    返回:
        {
            "memories": [
                {"id": 1, "content": "...", "score": 0.93, "source": "memory"},
            ],
            "knowledge": [
                {"id": "kb_notes.md_0", "score": 0.88, "source": "kb", "metadata": {...}},
            ],
            "all": [...]  # 合并 + 按 score 降序
        }
    """
    from long_term_memory import search_memories_by_vector
    from knowledge_base import search_knowledge_base

    # 并行检索两个来源
    memories = search_memories_by_vector(query, top_k=memory_top_k)
    knowledge = search_knowledge_base(query, top_k=kb_top_k)

    # 格式化记忆结果
    mem_results = []
    for m in memories:
        mem_results.append({
            "id": m["id"],
            "content": m["content"],
            "category": m.get("category", "general"),
            "importance": m.get("importance", "medium"),
            "score": m.get("score", 0),
            "source": "memory",
        })

    # 格式化知识库结果
    kb_results = []
    for k in knowledge:
        meta = k.get("metadata", {})
        kb_results.append({
            "id": k["id"],
            "content": meta.get("content", ""),
            "file": meta.get("file", ""),
            "score": k.get("score", 0),
            "source": "kb",
        })

    # 合并所有结果，按 score 降序排序
    all_results = mem_results + kb_results
    all_results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "memories": mem_results,
        "knowledge": kb_results,
        "all": all_results,
    }


def build_retrieval_context(query: str) -> str:
    """
    构建可注入 system prompt 的检索上下文文本。

    这是 main.py 中直接调用的便捷方法，
    替代 Phase 2 中的 inject_memory_context()。
    """
    result = retrieve_all(query)

    lines = []

    # 记忆部分
    if result["memories"]:
        lines.append("\n[以下是关于用户的长期记忆，请在对话中参考：]")
        for m in result["memories"]:
            importance_label = {"high": "⭐", "medium": "", "low": ""}.get(
                m.get("importance", ""), ""
            )
            lines.append(f"- {importance_label} {m['content']}")
        lines.append("")

    # 知识库部分
    if result["knowledge"]:
        lines.append("[以下是知识库中与当前问题相关的参考资料：]")
        for k in result["knowledge"]:
            file_info = f"（来源：{k['file']}）"
            lines.append(f"- {k['content'][:300]} {file_info}")
        lines.append("[以上为参考资料，请在回答时引用]\n")

    return "\n".join(lines) if len(lines) > 1 else ""
