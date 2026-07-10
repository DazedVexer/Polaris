import json
import numpy as np
from pathlib import Path
from config import (
    VECTOR_DB_PROVIDER,
    CHROMA_PERSIST_DIR,
    FAISS_INDEX_PATH,
    FAISS_META_PATH,
    VECTOR_SIMILARITY_THRESHOLD,
)
from embedding import get_embedding_dim


class VectorStore:
    """
    向量数据库统一封装。
    根据 VECTOR_DB_PROVIDER 自动选择 Chroma 或 FAISS。

    使用示例：
        store = VectorStore("memories")
        store.add(ids=["m1"], vectors=[[0.1, 0.2, ...]], metadatas=[{"content": "..."}])
        results = store.search(query_vector=[0.1, 0.2, ...], top_k=5)
    """

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._provider = VECTOR_DB_PROVIDER
        self._dim = get_embedding_dim()

        if self._provider == "chroma":
            self._init_chroma()
        else:
            self._init_faiss()

    # =========== 公开 API ===========

    def add(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict] = None,
    ):
        """批量写入向量和元数据"""
        if not ids:
            return
        if self._provider == "chroma":
            self._add_chroma(ids, vectors, metadatas)
        else:
            self._add_faiss(ids, vectors, metadatas)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_meta: dict = None,
    ) -> list[dict]:
        """
        相似度搜索。
        返回格式: [{"id": "m1", "score": 0.92, "metadata": {...}}, ...]
        """
        if self._provider == "chroma":
            return self._search_chroma(query_vector, top_k, filter_meta)
        else:
            return self._search_faiss(query_vector, top_k, filter_meta)

    def delete(self, ids: list[str]):
        """删除指定 ID 的向量"""
        if not ids:
            return
        if self._provider == "chroma":
            self._delete_chroma(ids)
        else:
            self._delete_faiss(ids)

    def count(self) -> int:
        """返回向量总数"""
        if self._provider == "chroma":
            return self._collection.count()
        else:
            return self._index.ntotal if self._index else 0

    # =========== Chroma 实现 ===========

    def _init_chroma(self):
        import chromadb
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        self._chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR)
        )
        self._collection = self._chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _add_chroma(self, ids, vectors, metadatas):
        self._collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas or [{}] * len(ids),
        )

    def _search_chroma(self, query_vector, top_k, filter_meta):
        where_filter = filter_meta if filter_meta else None
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_filter,
            include=["metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                score = 1.0 - distance
                if score >= VECTOR_SIMILARITY_THRESHOLD:
                    output.append({
                        "id": doc_id,
                        "score": round(score, 4),
                        "metadata": results["metadatas"][0][i] or {},
                    })
        return output

    def _delete_chroma(self, ids):
        self._collection.delete(ids=ids)

    # =========== FAISS 实现 ===========

    def _init_faiss(self):
        import faiss
        import numpy as np

        FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 尝试加载已有索引
        if FAISS_INDEX_PATH.exists() and FAISS_META_PATH.exists():
            self._index = faiss.read_index(str(FAISS_INDEX_PATH))
            self._meta = json.loads(FAISS_META_PATH.read_text(encoding="utf-8"))
            self._id_to_idx = {m["id"]: i for i, m in enumerate(self._meta)}
        else:
            self._index = faiss.IndexIDMap(faiss.IndexFlatIP(self._dim))
            self._meta = []
            self._id_to_idx = {}
            self._next_faiss_id = 0

    def _add_faiss(self, ids, vectors, metadatas):
        import numpy as np

        vec_array = np.array(vectors, dtype=np.float32)
        faiss_ids = []

        for i, doc_id in enumerate(ids):
            fid = self._next_faiss_id
            self._next_faiss_id += 1
            faiss_ids.append(fid)
            self._meta.append({
                "id": doc_id,
                "metadata": metadatas[i] if metadatas else {},
            })
            self._id_to_idx[doc_id] = len(self._meta) - 1

        self._index.add_with_ids(vec_array, np.array(faiss_ids, dtype=np.int64))
        self._save_faiss()

    def _search_faiss(self, query_vector, top_k, filter_meta):
        import numpy as np

        if self._index.ntotal == 0:
            return []

        q = np.array([query_vector], dtype=np.float32)
        scores, faiss_ids = self._index.search(q, top_k)

        output = []
        for score, fid in zip(scores[0], faiss_ids[0]):
            if fid < 0 or score < VECTOR_SIMILARITY_THRESHOLD:
                continue
            if fid < len(self._meta):
                meta_entry = self._meta[fid]
                if filter_meta:
                    match = all(
                        meta_entry["metadata"].get(k) == v
                        for k, v in filter_meta.items()
                    )
                    if not match:
                        continue
                output.append({
                    "id": meta_entry["id"],
                    "score": round(float(score), 4),
                    "metadata": meta_entry["metadata"],
                })
        return output

    def _delete_faiss(self, ids):
        for doc_id in ids:
            if doc_id in self._id_to_idx:
                idx = self._id_to_idx.pop(doc_id)
                self._meta[idx] = None

        self._rebuild_faiss_index()

    def _rebuild_faiss_index(self):
        import faiss
        import numpy as np

        valid_entries = [(i, m) for i, m in enumerate(self._meta) if m is not None]
        self._meta = [m for _, m in valid_entries]

        new_index = faiss.IndexIDMap(faiss.IndexFlatIP(self._dim))
        self._next_faiss_id = 0
        self._id_to_idx = {}

        for m in self._meta:
            self._id_to_idx[m["id"]] = len(self._id_to_idx)

        self._index = new_index
        self._next_faiss_id = 0
        self._save_faiss()

    def _save_faiss(self):
        import faiss
        faiss.write_index(self._index, str(FAISS_INDEX_PATH))
        FAISS_META_PATH.write_text(
            json.dumps(self._meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
