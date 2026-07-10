"""
Polaris Web Server — FastAPI 入口
启动方式：
  python -m server.main
  或
  uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import WEB_DIR, SERVER_HOST, SERVER_PORT

from server.api.chat import router as chat_router
from server.api.memory import router as memory_router
from server.api.knowledge import router as knowledge_router
from server.api.tools import router as tools_router
from server.middleware import setup_middleware
from server.models import HealthResponse

app = FastAPI(
    title="Polaris API",
    description="Personal AI Executive Assistant — API",
    version="6.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_middleware(app)

app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(knowledge_router)
app.include_router(tools_router)


@app.get("/health", response_model=HealthResponse)
async def health():
    total_memories = 0
    total_tools = 0
    try:
        from long_term_memory import get_memory_count
        from tool_registry import get_tool_registry
        total_memories = get_memory_count()
        total_tools = len(get_tool_registry().list_tools())
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        version="6.0.0",
        tools_count=total_tools,
        memory_count=total_memories,
    )


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    from tools import register_all_tools
    from long_term_memory import init_db

    print("[Polaris Server] 正在初始化...")
    init_db()

    try:
        register_all_tools()
    except Exception as e:
        print(f"[Polaris Server] 工具初始化警告：{e}")

    print(f"[Polaris Server] 启动于 http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"[Polaris Server] API 文档：http://{SERVER_HOST}:{SERVER_PORT}/docs")

    uvicorn.run(
        "server.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info",
    )
