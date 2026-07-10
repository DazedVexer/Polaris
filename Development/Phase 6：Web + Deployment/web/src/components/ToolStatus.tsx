import { useState, useEffect } from "react";
import { ToolInfo } from "../types";
import { fetchTools } from "../api";

export default function ToolStatus() {
  const [tools, setTools] = useState<ToolInfo[]>([]);

  useEffect(() => {
    fetchTools().then(setTools).catch(() => setTools([]));
  }, []);

  return (
    <div style={{ padding: "12px" }}>
      <h4 style={{ color: "#e94560", marginBottom: "8px" }}>🔧 可用工具</h4>
      {tools.length === 0 ? (
        <p style={{ color: "#888", fontSize: "0.85rem" }}>暂无工具</p>
      ) : (
        tools.map((t) => (
          <div key={t.name} style={{ fontSize: "0.8rem", marginBottom: "4px" }}>
            <span style={{ color: "#4caf50" }}>{t.name}</span>: {t.description}
          </div>
        ))
      )}
    </div>
  );
}
