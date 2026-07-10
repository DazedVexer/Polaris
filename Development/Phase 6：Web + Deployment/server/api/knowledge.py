"""
知识库管理 API：上传文档、查看状态、搜索、重建。
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from server.models import KnowledgeBaseStatus, KnowledgeSearchRequest, KnowledgeSearchResult

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/status", response_model=KnowledgeBaseStatus)
async def knowledge_status():
    """知识库状态"""
    try:
        from knowledge_base import load_documents
        from vector_store import VectorStore

        docs = load_documents()
        try:
            store = VectorStore("knowledge_base")
            chunk_count = len(store.collection.get()["ids"])
        except Exception:
            chunk_count = 0

        return KnowledgeBaseStatus(
            document_count=len(docs),
            chunk_count=chunk_count,
            documents=[{"file": d["file"], "size": len(d["content"])} for d in docs],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_knowledge(request: KnowledgeSearchRequest):
    """搜索知识库"""
    try:
        from knowledge_base import search_knowledge_base
        results = search_knowledge_base(request.query, top_k=request.top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    try:
        from pathlib import Path
        from config import KB_DIR

        KB_DIR.mkdir(parents=True, exist_ok=True)
        save_path = KB_DIR / file.filename

        content = await file.read()
        save_path.write_bytes(content)

        # 增量重建知识库
        from knowledge_base import build_knowledge_base
        build_knowledge_base()

        return {
            "uploaded": file.filename,
            "size": len(content),
            "message": f"文件 {file.filename} 已上传并入库",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild")
async def rebuild_knowledge():
    """重建知识库"""
    try:
        from knowledge_base import build_knowledge_base
        count = build_knowledge_base(force_rebuild=True)
        return {"message": "知识库重建完成", "chunk_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
