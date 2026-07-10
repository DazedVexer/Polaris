import { useState, useEffect } from "react";
import { MemoryItem } from "../types";
import { fetchMemories } from "../api";

export default function MemoryPanel() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMemories()
      .then(setMemories)
      .catch(() => setMemories([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="memory-panel">
      <h3>🧠 记忆管理</h3>
      {loading ? (
        <p>加载中...</p>
      ) : memories.length === 0 ? (
        <p>暂无记忆记录</p>
      ) : (
        memories.map((m) => (
          <div key={m.id} className="memory-card">
            <div>{m.content}</div>
            <div className="meta">
              <span>{m.category}</span>
              <span>{m.importance === "high" ? "⭐" : ""} {m.importance}</span>
              <span>{new Date(m.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
