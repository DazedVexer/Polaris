import sqlite3
from config import LTM_DB_PATH

def _get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建文件）"""
    conn = sqlite3.connect(str(LTM_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表（程序启动时调用一次）"""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            content     TEXT    NOT NULL,
            category    TEXT    DEFAULT 'general',
            importance  TEXT    DEFAULT 'medium',
            source      TEXT    DEFAULT 'llm_extracted',
            session_id  TEXT,
            embedding   TEXT,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS mood_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            mood         TEXT    NOT NULL,
            intensity    TEXT    DEFAULT 'medium',
            intent       TEXT    DEFAULT 'chatting',
            context      TEXT,
            session_id   TEXT,
            created_at   TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            section      TEXT    NOT NULL UNIQUE,
            content      TEXT    NOT NULL,
            updated_at   TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.commit()
    conn.close()

    _ensure_embedding_column()

def add_memory(content: str, category: str = "general",
               importance: str = "medium", source: str = "llm_extracted",
               session_id: str = None) -> int:
    """插入一条记忆，返回记忆 ID"""
    conn = _get_connection()
    cursor = conn.execute(
        """INSERT INTO memories (content, category, importance, source, session_id)
           VALUES (?, ?, ?, ?, ?)""",
        (content.strip(), category, importance, source, session_id)
    )
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()
    return memory_id


def search_memories(query: str, limit: int = 5) -> list[dict]:
    """关键词模糊搜索记忆"""
    conn = _get_connection()
    keywords = query.strip().split()
    if not keywords:
        conn.close()
        return []

    conditions = " OR ".join(["content LIKE ?" for _ in keywords])
    params = [f"%{kw}%" for kw in keywords]

    cursor = conn.execute(
        f"""SELECT id, content, category, importance, created_at
            FROM memories
            WHERE {conditions}
            ORDER BY created_at DESC
            LIMIT ?""",
        params + [limit]
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_memories(limit: int = 20) -> list[dict]:
    """获取最近存入的记忆"""
    conn = _get_connection()
    cursor = conn.execute(
        """SELECT id, content, category, importance, created_at
           FROM memories
           ORDER BY created_at DESC
           LIMIT ?""",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_memory(memory_id: int):
    """删除指定记忆"""
    conn = _get_connection()
    conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()


def get_memory_count() -> int:
    """返回记忆总数"""
    conn = _get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM memories")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def _ensure_embedding_column():
    """确保 memories 表有 embedding 列（从 Phase 2 升级时自动添加）"""
    conn = _get_connection()
    cursor = conn.execute("PRAGMA table_info(memories)")
    columns = [row[1] for row in cursor.fetchall()]
    if "embedding" not in columns:
        conn.execute("ALTER TABLE memories ADD COLUMN embedding TEXT")
        conn.commit()
    conn.close()


def add_memory_with_embedding(
    content: str,
    category: str = "general",
    importance: str = "medium",
    source: str = "llm_extracted",
    session_id: str = None,
) -> int:
    """
    插入一条记忆，同时自动生成 embedding 并存储。
    """
    from embedding import embed_single
    import json

    conn = _get_connection()

    try:
        vec = embed_single(content)
        embedding_json = json.dumps(vec) if vec else None
    except Exception:
        embedding_json = None

    cursor = conn.execute(
        """INSERT INTO memories (content, category, importance, source, session_id, embedding)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (content.strip(), category, importance, source, session_id, embedding_json)
    )
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()

    if vec:
        _sync_to_vector_db(memory_id, content, vec, category, importance, source, session_id)

    return memory_id


def _sync_to_vector_db(memory_id: int, content: str, vec: list[float],
                       category: str, importance: str, source: str, session_id: str):
    """将记忆向量同步写入向量数据库"""
    try:
        from vector_store import VectorStore
        store = VectorStore("memories")
        store.add(
            ids=[str(memory_id)],
            vectors=[vec],
            metadatas=[{
                "content": content,
                "category": category,
                "importance": importance,
                "source": source,
                "session_id": session_id or "",
                "memory_id": memory_id,
            }],
        )
    except Exception:
        pass


def search_memories_by_vector(
    query: str,
    top_k: int = 5,
    category_filter: str = None,
) -> list[dict]:
    """
    用 embedding 做语义搜索。

    参数:
        query: 用户输入的查询文本
        top_k: 返回最多 K 条
        category_filter: 可选，按分类过滤（如 "learning"）

    返回:
        [{"id": 1, "content": "...", "score": 0.93, ...}, ...]
    """
    from embedding import embed_single
    from vector_store import VectorStore

    store = VectorStore("memories")

    if store.count() == 0:
        return search_memories(query, limit=top_k)

    query_vec = embed_single(query)
    if not query_vec:
        return search_memories(query, limit=top_k)

    filter_meta = None
    if category_filter:
        filter_meta = {"category": category_filter}

    results = store.search(query_vec, top_k=top_k, filter_meta=filter_meta)

    output = []
    for r in results:
        meta = r["metadata"]
        output.append({
            "id": meta.get("memory_id", 0),
            "content": meta.get("content", ""),
            "category": meta.get("category", "general"),
            "importance": meta.get("importance", "medium"),
            "score": r["score"],
        })
    return output


def rebuild_embedding_column():
    """
    给所有没有 embedding 的旧记忆批量生成 embedding。
    """
    from embedding import embed

    conn = _get_connection()
    cursor = conn.execute(
        "SELECT id, content FROM memories WHERE embedding IS NULL OR embedding = ''"
    )
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        print("[Polaris] 所有记忆已有 embedding，无需重建。")
        return

    print(f"[Polaris] 正在为 {len(rows)} 条记忆生成 embedding...")

    batch_size = 20
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        texts = [row["content"] for row in batch]
        try:
            vectors = embed(texts)
        except Exception as e:
            print(f"[Polaris] embedding 生成失败（第 {i} 批）: {e}")
            continue

        for row, vec in zip(batch, vectors):
            import json
            vec_json = json.dumps(vec)
            conn.execute(
                "UPDATE memories SET embedding = ? WHERE id = ?",
                (vec_json, row["id"])
            )

        conn.commit()
        print(f"[Polaris] 已完成 {min(i + batch_size, len(rows))}/{len(rows)}")

    conn.close()
    print("[Polaris] embedding 重建完成。")


def sync_all_to_vector_db():
    """
    将 SQLite 中所有有 embedding 的记忆同步到向量数据库。
    """
    import json
    from vector_store import VectorStore

    conn = _get_connection()
    cursor = conn.execute(
        """SELECT id, content, category, importance, source, session_id, embedding
           FROM memories WHERE embedding IS NOT NULL AND embedding != ''"""
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[Polaris] 没有需要同步的记忆。")
        return

    print(f"[Polaris] 正在同步 {len(rows)} 条记忆到向量数据库...")

    store = VectorStore("memories")
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        ids = []
        vectors = []
        metadatas = []
        for row in batch:
            try:
                vec = json.loads(row["embedding"])
            except (json.JSONDecodeError, TypeError):
                continue
            ids.append(str(row["id"]))
            vectors.append(vec)
            metadatas.append({
                "content": row["content"],
                "category": row["category"],
                "importance": row["importance"],
                "source": row["source"],
                "session_id": row["session_id"] or "",
                "memory_id": row["id"],
            })
        if ids:
            store.add(ids=ids, vectors=vectors, metadatas=metadatas)

    print(f"[Polaris] 同步完成，向量库中现有 {store.count()} 条记忆。")


def log_mood(mood: str, intensity: str, intent: str,
             context: str, session_id: str):
    """记录一条情绪日志。每轮对话后由 memory_manager 调用。"""
    conn = _get_connection()
    conn.execute(
        """INSERT INTO mood_log (mood, intensity, intent, context, session_id)
           VALUES (?, ?, ?, ?, ?)""",
        (mood, intensity, intent, context[:300] if context else "", session_id)
    )
    conn.commit()
    conn.close()


def upsert_profile(section: str, content: str):
    """
    更新或插入用户画像的某个 section。
    如果该 section 已存在则更新内容，否则插入新行。
    """
    conn = _get_connection()
    conn.execute(
        """INSERT INTO user_profile (section, content, updated_at)
           VALUES (?, ?, datetime('now', 'localtime'))
           ON CONFLICT(section) DO UPDATE SET
               content = excluded.content,
               updated_at = excluded.updated_at""",
        (section, content)
    )
    conn.commit()
    conn.close()


def get_recent_mood(limit: int = 5) -> list[dict]:
    """获取最近的情绪记录，用于注入对话上下文。"""
    conn = _get_connection()
    cursor = conn.execute(
        """SELECT mood, intensity, intent, context, created_at
           FROM mood_log
           ORDER BY created_at DESC
           LIMIT ?""",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows][::-1]


def get_profile() -> dict:
    """获取完整用户画像，返回 {section: content} 字典。"""
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT section, content FROM user_profile ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["section"]: row["content"] for row in rows}


def get_mood_count() -> int:
    """返回情绪日志总数。"""
    conn = _get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM mood_log")
    count = cursor.fetchone()[0]
    conn.close()
    return count
