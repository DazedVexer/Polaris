"""
中间件：CORS、日志、简单 Token 认证。
"""

import time
import logging
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, API_TOKEN

logger = logging.getLogger("polaris.server")


def setup_middleware(app):
    """注册所有中间件到 FastAPI app"""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration:.2f}s)"
        )
        return response

    if API_TOKEN:
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            if request.url.path in ("/health", "/docs", "/openapi.json", "/"):
                return await call_next(request)

            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if token != API_TOKEN:
                raise HTTPException(status_code=401, detail="无效的 API Token")

            return await call_next(request)
