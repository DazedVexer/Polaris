"""
对话 API：普通聊天 + Agent 任务 + 流式输出。
"""

import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from server.models import (
    ChatRequest, ChatResponse,
    StreamChatRequest,
    AgentTaskRequest, AgentTaskResponse,
)

router = APIRouter(prefix="/api/chat", tags=["对话"])

_sessions: dict[str, dict] = {}


def _get_or_create_session(session_id: str | None) -> str:
    """获取或创建一个对话 session"""
    import uuid
    if session_id and session_id in _sessions:
        return session_id
    new_id = session_id or str(uuid.uuid4())[:8]
    _sessions[new_id] = {"created_at": __import__("datetime").datetime.now().isoformat()}
    return new_id


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """普通对话（非流式，一次性返回）"""
    try:
        session_id = _get_or_create_session(request.session_id)

        from prompt_builder import sys_prompt_builder
        from short_term_memory import ShortTermMemory
        from memory_manager import MemoryManager
        from retrieval_pipeline import build_retrieval_context
        from llm_client import chat_stream as llm_chat_stream
        import io

        system_prompt = sys_prompt_builder()
        memory = ShortTermMemory(system_prompt)
        memory.add_user_message(request.message)

        retrieval_context = build_retrieval_context(request.message)
        temp_extra = []
        if retrieval_context:
            temp_extra.append({
                "role": "system",
                "content": retrieval_context,
            })

        messages = memory.get_messages()
        full_messages = [messages[0]] + temp_extra + messages[1:]

        from llm_client import _get_client
        from config import LLM_CONFIG

        client = _get_client()
        stream = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=full_messages,
            temperature=LLM_CONFIG["temperature"],
            max_tokens=LLM_CONFIG["max_tokens"],
            stream=True,
        )
        reply = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                reply += chunk.choices[0].delta.content

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            mode=request.mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: StreamChatRequest):
    """流式对话（SSE，逐字返回，打字机效果）"""

    async def generate():
        try:
            from prompt_builder import sys_prompt_builder
            from short_term_memory import ShortTermMemory
            from retrieval_pipeline import build_retrieval_context
            from llm_client import _get_client
            from config import LLM_CONFIG

            system_prompt = sys_prompt_builder()
            memory = ShortTermMemory(system_prompt)
            memory.add_user_message(request.message)

            retrieval_context = build_retrieval_context(request.message)
            temp_extra = []
            if retrieval_context:
                temp_extra.append({
                    "role": "system",
                    "content": retrieval_context,
                })

            messages = memory.get_messages()
            full_messages = [messages[0]] + temp_extra + messages[1:]

            client = _get_client()
            stream = client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=full_messages,
                temperature=LLM_CONFIG["temperature"],
                max_tokens=LLM_CONFIG["max_tokens"],
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    chunk_data = {"text": text}
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_chunk = {"error": str(e)}
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/agent", response_model=AgentTaskResponse)
async def agent_task(request: AgentTaskRequest):
    """Agent 任务执行"""
    try:
        from agent_loop import AgentLoop
        from retrieval_pipeline import build_retrieval_context

        context = build_retrieval_context(request.instruction)
        agent = AgentLoop()
        result = agent.run(request.instruction, context)

        steps = []
        for r in result.get("step_results", []):
            steps.append({
                "step": r["step"],
                "action": r.get("action", ""),
                "result": r.get("result", ""),
                "status": r.get("status", "ok"),
            })

        return AgentTaskResponse(
            task_id=result.get("plan", {}).get("task_id", "task_001"),
            success=result.get("success", False),
            summary=result.get("summary", ""),
            steps=steps,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/stream")
async def agent_task_stream(request: AgentTaskRequest):
    """Agent 任务流式输出（每步执行完推送一次）"""

    async def generate():
        try:
            from agent_loop import AgentLoop
            from retrieval_pipeline import build_retrieval_context
            import queue
            import threading

            context = build_retrieval_context(request.instruction)
            agent = AgentLoop()

            step_queue = queue.Queue()

            def on_step(step_num, result):
                step_queue.put({
                    "step": step_num,
                    "action": result.get("action", ""),
                    "result": result.get("result", "")[:500],
                    "status": result.get("status", "ok"),
                })

            def run_agent():
                result = agent.run(request.instruction, context, on_step=on_step)
                step_queue.put({"type": "done", "summary": result.get("summary", ""), "success": result.get("success", False)})

            thread = threading.Thread(target=run_agent)
            thread.start()

            while thread.is_alive() or not step_queue.empty():
                try:
                    item = step_queue.get(timeout=0.1)
                    if item.get("type") == "done":
                        yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                        break
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    await asyncio.sleep(0.1)

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
