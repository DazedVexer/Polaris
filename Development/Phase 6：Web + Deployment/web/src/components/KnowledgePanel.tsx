import { useState } from "react";

export default function KnowledgePanel() {
  const [status, setStatus] = useState<{ document_count: number; documents: unknown[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const resp = await fetch("http://localhost:8000/api/knowledge/status");
      const data = await resp.json();
      setStatus(data);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="knowledge-panel">
      <h3>📚 知识库</h3>
      <button
        onClick={fetchStatus}
        disabled={loading}
        style={{
          padding: "8px 16px",
          background: "#e94560",
          color: "#fff",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          marginBottom: "16px",
        }}
      >
        {loading ? "加载中..." : "刷新状态"}
      </button>
      {status && (
        <div>
          <p>文档数：{status.document_count}</p>
          {Array.isArray(status.documents) && status.documents.map((d: unknown, i: number) => {
            const doc = d as { file?: string; size?: number };
            return (
              <div key={i} className="memory-card">
                <div>{doc.file || "未知文件"}</div>
                <div className="meta">
                  <span>{doc.size ? `${doc.size} 字符` : ""}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
