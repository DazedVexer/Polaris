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
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.commit()
    conn.close()

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