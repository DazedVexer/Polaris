import numpy as np

from config import EMBEDDING_PROVIDER, EMBEDDING_MODEL, BGE_MODEL_NAME

# 延迟加载，不用时避免占用内存
_openai_client = None
_bge_model = None


def get_embedding_dim() -> int:
    """返回当前 embedding 模型的向量维度"""
    if EMBEDDING_PROVIDER == "openai":
        # text-embedding-3-small: 1536
        # text-embedding-3-large: 3072
        return 1536
    else:
        # bge-small-zh: 512
        return 512


def embed(texts: list[str]) -> list[list[float]]:
    """
    将文本列表转为 embedding 向量列表。

    参数:
        texts: 文本字符串列表，如 ["你好", "今天天气不错"]

    返回:
        向量列表，每个向量是 float 列表，如 [[0.01, 0.23, ...], [0.67, 0.12, ...]]
    """
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "openai":
        return _embed_openai(texts)
    else:
        return _embed_bge(texts)


def embed_single(text: str) -> list[float]:
    """单条文本转 embedding（便捷方法）"""
    results = embed([text])
    return results[0] if results else []


def _embed_openai(texts: list[str]) -> list[list[float]]:
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        from config import LLM_CONFIG
        _openai_client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=30.0,
            max_retries=2,
        )

    # 处理空字符串（OpenAI 不接受空字符串）
    clean_texts = [t if t.strip() else " " for t in texts]

    response = _openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=clean_texts,
    )
    return [d.embedding for d in response.data]


def _embed_bge(texts: list[str]) -> list[list[float]]:
    global _bge_model
    if _bge_model is None:
        from sentence_transformers import SentenceTransformer
        _bge_model = SentenceTransformer(BGE_MODEL_NAME)

    # bge 模型会自动处理空字符串
    embeddings = _bge_model.encode(
        texts,
        normalize_embeddings=True,   # L2 归一化，让余弦相似度 = 内积
        show_progress_bar=False,
    )
    return embeddings.tolist()
