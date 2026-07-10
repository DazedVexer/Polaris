import json
from short_term_memory import ShortTermMemory
from long_term_memory import add_memory_with_embedding, search_memories_by_vector, log_mood, get_recent_mood
from config import LLM_MEMORY_EXTRACTION, LTM_RETRIEVAL_K, STM_SUMMARY_TRIGGER, MEMORY_RETRIEVAL_TOP_K

EXTRACTION_PROMPT = """你是一个记忆提取器。请阅读以下对话片段，提取出关于「用户」的重要信息。

要求：
1. 提取事实性信息（用户说了什么、喜欢什么、在做什么、有什么目标等）。
2. 同时注意用户的情绪状态和心理变化（压力、焦虑、动力、信心等），
   闲聊中的情绪线索也要提取（如"最近好累"→ content: "用户近期感到疲惫", category: "emotion"）。
3. 如果没有值得记住的信息，返回空数组 []。
4. 每条记忆用一句话概括，分类为 personal / learning / work / goal / preference / emotion / general。

返回格式（严格的 JSON 数组，不要包含其他文字）：
[
  {"content": "...", "category": "...", "importance": "high"},
  ...
]

对话片段：
---
{conversation}
---

请提取记忆（仅返回 JSON 数组）："""

RETRIEVAL_PROMPT = """你是一个记忆检索器。以下是用户的长期记忆列表和当前问题。请选出与用户当前问题最相关的记忆。

记忆列表：
{memories}

用户当前问题：{user_input}

要求：
- 只选择与问题直接相关的记忆
- 按相似度从高到低排序，最多返回 {top_k} 条
- 返回格式：一个 JSON 数组，每个元素是记忆的 id（整数）

仅返回 JSON 数组（如 [3, 7] 或 []）："""


SUMMARIZE_PROMPT = """你是一个对话总结器。请阅读以下对话记录，提取关键信息并总结。

要求：
1. 重点保留用户提供的事实信息（说了什么、做了什么决定、表达了什么偏好）。
2. 忽略闲聊和问候语。
3. 用 3~5 句话总结，中文输出。

对话记录：
---
{conversation}
---

总结："""

class MemoryManager:
    def __init__(self, short_term: ShortTermMemory, session_id: str):
        self.stm = short_term
        self.session_id = session_id
        self._turn_counter = 0

    # ---------- 提取 ----------

    def maybe_extract(self):
        """每轮对话后调用。当轮次达到提取间隔时，调 LLM 提取记忆。（Phase 3：写入带 embedding）"""
        self._turn_counter += 1
        if self._turn_counter % LLM_MEMORY_EXTRACTION != 0:
            return

        recent = self.stm.history[-(6 * 2):]
        if not recent:
            return

        conversation_text = self._format_messages(recent)
        prompt = EXTRACTION_PROMPT.format(conversation=conversation_text)

        try:
            response = self._call_llm_for_json(prompt)
            memories = json.loads(response)
            if not isinstance(memories, list):
                return

            for m in memories:
                content = m.get("content", "").strip()
                if content:
                    add_memory_with_embedding(
                        content=content,
                        category=m.get("category", "general"),
                        importance=m.get("importance", "medium"),
                        source="llm_extracted",
                        session_id=self.session_id,
                    )
        except (json.JSONDecodeError, Exception):
            pass

    # ---------- 情绪提取（BangBand） ----------

    def extract_emotion(self, user_message: str):
        """每轮对话后调用。从用户消息中提取情绪线索，写入 mood_log。
        BangBand 新增：静默运行，用户无感。"""
        from perception import analyze

        result = analyze(user_message)

        # 静默写入情绪日志
        log_mood(
            mood=result["mood"],
            intensity=result["intensity"],
            intent=result["intent"],
            context=user_message,
            session_id=self.session_id,
        )

        # 如果情绪强度高，同时写入长期记忆（方便后续检索）
        if result["intensity"] == "high":
            try:
                add_memory_with_embedding(
                    content=f"用户表达了{result['mood']}情绪：{user_message[:100]}",
                    category="emotion",
                    importance="high",
                    source="emotion_extracted",
                    session_id=self.session_id,
                )
            except Exception:
                pass

    # ---------- 检索 ----------

    def retrieve(self, user_input: str) -> list[dict]:
        """
        每轮对话前调用。使用 embedding 向量语义检索。
        Phase 3 升级版：不再依赖关键词匹配。
        """
        return search_memories_by_vector(user_input, top_k=MEMORY_RETRIEVAL_TOP_K)

    # ---------- 总结 ----------

    def maybe_summarize(self):
        """每轮对话后调用。如果短期记忆积累超过阈值，触发自动总结。（Phase 3：写入带 embedding）"""
        if not self.stm.needs_summarization():
            return

        old_messages = self.stm.get_slice_to_summarize()
        if not old_messages:
            return

        conversation_text = self._format_messages(old_messages)
        prompt = SUMMARIZE_PROMPT.format(conversation=conversation_text)

        try:
            summary = self._call_llm_for_text(prompt)
            if summary and len(summary.strip()) > 10:
                add_memory_with_embedding(
                    content=summary.strip(),
                    category="summary",
                    importance="medium",
                    source="auto_summary",
                    session_id=self.session_id,
                )
        except Exception:
            pass

    # ---------- 记忆注入 ----------

    def inject_memory_context(self, user_input: str) -> str:
        """生成需要注入的「记忆上下文」文本。（BangBand：增加情绪上下文）"""
        memories = self.retrieve(user_input)

        lines = []

        # BangBand：注入近期情绪
        try:
            recent_mood = get_recent_mood(limit=3)
            if recent_mood:
                mood_desc = " → ".join([
                    f"{m['mood']}({m['intensity']})" for m in recent_mood
                ])
                lines.append(
                    f"\n[用户近期情绪：{mood_desc}。请在回应时注意情绪状态，不要机械提示用户。]"
                )
        except Exception:
            pass

        if memories:
            lines.append("\n[以下是关于用户的长期记忆，请在对话中参考：]")
            for m in memories:
                lines.append(f"- {m['content']}")
            lines.append("[以上为长期记忆]\n")

        return "\n".join(lines) if lines else ""

    # ---------- 工具方法 ----------

    def _format_messages(self, messages: list[dict]) -> str:
        lines = []
        for m in messages:
            role = "用户" if m["role"] == "user" else "AI"
            lines.append(f"[{role}] {m['content']}")
        return "\n".join(lines)

    def _call_llm_for_json(self, prompt: str) -> str:
        from openai import OpenAI
        from config import LLM_CONFIG

        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=30.0,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[
                {"role": "system", "content": "你只输出 JSON，不要加任何解释。如果无法判断就输出 []。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content or "[]"

    def _call_llm_for_text(self, prompt: str) -> str:
        from openai import OpenAI
        from config import LLM_CONFIG

        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=30.0,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500,
        )
        return response.choices[0].message.content or ""
