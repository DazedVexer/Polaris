interface Props {
  activePanel: string;
  onPanelChange: (panel: string) => void;
  serverOnline: boolean;
  sessionId: string | null;
}

export default function Sidebar({ activePanel, onPanelChange, serverOnline }: Props) {
  return (
    <div className="sidebar">
      <button
        className={activePanel === "chat" ? "active" : ""}
        onClick={() => onPanelChange("chat")}
        title="对话"
      >
        💬
      </button>
      <button
        className={activePanel === "agent" ? "active" : ""}
        onClick={() => onPanelChange("agent")}
        title="Agent 任务"
      >
        🤖
      </button>
      <button
        className={activePanel === "memory" ? "active" : ""}
        onClick={() => onPanelChange("memory")}
        title="记忆"
      >
        🧠
      </button>
      <div
        className={`status-dot ${serverOnline ? "online" : "offline"}`}
        title={serverOnline ? "服务器在线" : "服务器离线"}
      />
    </div>
  );
}
