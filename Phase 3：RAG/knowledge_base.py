import re
from pathlib import Path
from config import KB_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from embedding import embed


def load_documents(kb_dir: Path = None) -> list[dict]:
    """
    加载 kb/ 目录下所有文档，返回结构化列表。

    返回格式:
    [
        {"file": "notes.md", "type": "md", "content": "全文内容..."},
        {"file": "paper.pdf", "type": "pdf", "content": "提取的文本..."},
    ]
    """
    if kb_dir is None:
        kb_dir = KB_DIR

    if not kb_dir.exists():
        print(f"[Polaris] 知识库目录 {kb_dir} 不存在，已自动创建。")
        kb_dir.mkdir(parents=True, exist_ok=True)
        return []

    docs = []
    for file_path in sorted(kb_dir.iterdir()):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        if suffix == ".md":
            content = _load_md(file_path)
            docs.append({"file": file_path.name, "type": "md", "content": content})
        elif suffix == ".pdf":
            content = _load_pdf(file_path)
            if content.strip():
                docs.append({"file": file_path.name, "type": "pdf", "content": content})
        else:
            # 跳过不支持的文件类型
            continue

    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    """
    将文档切分为文本块（chunk）。

    返回格式:
    [
        {"file": "notes.md", "chunk_index": 0, "content": "第1块内容...", "char_start": 0},
        {"file": "notes.md", "chunk_index": 1, "content": "第2块内容...", "char_start": 450},
    ]
    """
    chunks = []
    for doc in docs:
        doc_chunks = _split_text(
            text=doc["content"],
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        for i, chunk_text in enumerate(doc_chunks):
            chunks.append({
                "file": doc["file"],
                "type": doc["type"],
                "chunk_index": i,
                "content": chunk_text,
                "char_start": i * (CHUNK_SIZE - CHUNK_OVERLAP) if i > 0 else 0,
            })
    return chunks


def build_knowledge_base(force_rebuild: bool = False) -> int:
    """
    构建/更新知识库：加载文档 → 分块 → embedding → 存入向量数据库。

    参数:
        force_rebuild: 是否强制重建（清空旧数据）

    返回:
        入库的 chunk 数量
    """
    from vector_store import VectorStore

    store = VectorStore("knowledge_base")

    if force_rebuild:
        # 清空旧数据（Chroma 删 collection 重建）
        print("[Polaris] 正在清空旧知识库...")
        if store._provider == "chroma":
            store._chroma_client.delete_collection(store.collection_name)
            store._init_chroma()
        else:
            store._init_faiss()

    # 加载文档
    print("[Polaris] 正在加载知识库文档...")
    docs = load_documents()
    if not docs:
        print("[Polaris] 未发现文档（请在 kb/ 目录下放置 .md 或 .pdf 文件）")
        return 0

    print(f"[Polaris] 已加载 {len(docs)} 个文档：")
    for d in docs:
        print(f"  - {d['file']} ({len(d['content'])} 字符)")

    # 切分
    chunks = chunk_documents(docs)
    print(f"[Polaris] 共切分为 {len(chunks)} 个文本块")

    if not chunks:
        return 0

    # 批量生成 embedding
    print(f"[Polaris] 正在生成 embedding（共 {len(chunks)} 块，可能需要一些时间）...")
    chunk_texts = [c["content"] for c in chunks]
    vectors = embed(chunk_texts)

    # 写入向量数据库
    print("[Polaris] 正在写入向量数据库...")
    ids = [f"kb_{c['file']}_{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "file": c["file"],
            "type": c["type"],
            "chunk_index": c["chunk_index"],
            "content": c["content"],
            "char_start": c["char_start"],
        }
        for c in chunks
    ]
    store.add(ids=ids, vectors=vectors, metadatas=metadatas)

    print(f"[Polaris] 知识库构建完成！共 {len(chunks)} 个文本块入库。")
    return len(chunks)


def search_knowledge_base(
    query: str,
    top_k: int = 3,
    file_filter: str = None,
) -> list[dict]:
    """
    在知识库中语义搜索。

    参数:
        query: 查询文本
        top_k: 返回结果数
        file_filter: 可选，限定文件名（如 "notes.md"）

    返回:
        [{"id": "kb_notes.md_0", "score": 0.91, "metadata": {...}}, ...]
    """
    from embedding import embed_single
    from vector_store import VectorStore

    store = VectorStore("knowledge_base")
    if store.count() == 0:
        return []

    query_vec = embed_single(query)
    if not query_vec:
        return []

    filter_meta = None
    if file_filter:
        filter_meta = {"file": file_filter}

    results = store.search(query_vec, top_k=top_k, filter_meta=filter_meta)
    return results


# =========== 内部工具函数 ===========

def _load_md(file_path: Path) -> str:
    """读取 Markdown 文件"""
    return file_path.read_text(encoding="utf-8")


def _load_pdf(file_path: Path) -> str:
    """读取 PDF 文件（优先用 PyMuPDF，失败则用 pdfplumber）"""
    try:
        import fitz
        doc = fitz.open(str(file_path))
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        pass
    except Exception as e:
        print(f"[警告] PyMuPDF 读取 {file_path.name} 失败: {e}")

    # fallback: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
    except ImportError:
        print("[错误] 请安装 PDF 解析库：pip install pymupdf 或 pip install pdfplumber")
        return ""
    except Exception as e:
        print(f"[警告] 读取 PDF {file_path.name} 失败: {e}")
        return ""


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    智能分块：按段落 → 按句子 → 硬截断的优先级切分。

    分块策略：
    1. 先按空行（\n\n）分割成段落
    2. 长段落按句子（。！？\n）再切
    3. 仍超长的句子按 chunk_size 硬截断
    """
    # 第一步：按段落分割
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # 如果当前段落很短，尝试合并到当前 chunk
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            # 当前 chunk 已经满了，保存
            if current_chunk:
                chunks.append(current_chunk)

            # 如果新段落本身就超过 chunk_size，按句子切
            if len(para) > chunk_size:
                sub_chunks = _split_by_sentence(para, chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    # 如果有 overlap，用滑动窗口做重叠
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_end = chunks[i-1][-chunk_overlap:] if len(chunks[i-1]) > chunk_overlap else chunks[i-1]
            # 将前一块的尾部和当前块拼接（去重）
            combined = prev_end + chunks[i]
            # 去重：如果当前块开头就是前一块的结尾，不重复加
            if chunks[i].startswith(prev_end):
                overlapped.append(chunks[i])
            else:
                overlapped.append(combined[:chunk_size + chunk_overlap])
        return overlapped

    return chunks


def _split_by_sentence(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """按句子分割长段落"""
    # 中文句子分隔符：。！？；加上英文的 . ! ?
    sentences = re.split(r'(?<=[。！？；.!?])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) <= chunk_size:
            current += sent
        else:
            if current:
                chunks.append(current)
            # 如果单个句子超过 chunk_size，硬截断
            if len(sent) > chunk_size:
                for i in range(0, len(sent), chunk_size - chunk_overlap):
                    chunks.append(sent[i:i + chunk_size])
            else:
                current = sent

    if current:
        chunks.append(current)
    return chunks
