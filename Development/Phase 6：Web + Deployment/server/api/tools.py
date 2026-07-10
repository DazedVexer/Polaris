"""
工具管理 API：查看可用工具列表。
"""

from fastapi import APIRouter, HTTPException
from server.models import ToolListResponse, ToolInfo

router = APIRouter(prefix="/api/tools", tags=["工具"])


@router.get("", response_model=ToolListResponse)
async def list_tools():
    """列出所有可用工具"""
    try:
        from tool_registry import get_tool_registry

        registry = get_tool_registry()
        tools = []
        for name in registry.list_tools():
            t = registry.get(name)
            tools.append(ToolInfo(name=name, description=t["description"]))

        return ToolListResponse(tools=tools)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
