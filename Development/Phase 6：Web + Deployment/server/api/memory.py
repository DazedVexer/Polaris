"""
记忆管理 API：查看、搜索、删除记忆。
"""

from fastapi import APIRouter, HTTPException, Query
from server.models import MemoryListResponse, MemorySearchRequest, MemoryItem

router = APIRouter(prefix="/api/memory", tags=["记忆"])


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    limit: int = Query(20, ge=1, le=100),
    category: str = Query(None),
):
    """获取记忆列表"""
    try:
        from long_term_memory import get_recent_memories
        memories = get_recent_memories(limit)

        if category:
            memories = [m for m in memories if m.get("category") == category]

        return MemoryListResponse(
            total=len(memories),
            memories=[
                MemoryItem(
                    id=m["id"],
                    content=m["content"],
                    category=m.get("category", "general"),
                    importance=m.get("importance", "medium"),
                    created_at=m.get("created_at", ""),
                )
                for m in memories
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_memories(request: MemorySearchRequest):
    """语义搜索记忆"""
    try:
        from long_term_memory import search_memories_by_vector
        results = search_memories_by_vector(
            request.query,
            top_k=request.top_k,
            category_filter=request.category,
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int):
    """删除一条记忆"""
    try:
        from long_term_memory import delete_memory
        delete_memory(memory_id)
        return {"deleted": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
