import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import AgentPanel from "./components/AgentPanel";
import MemoryPanel from "./components/MemoryPanel";
import { ChatMode, Message } from "./types";
import { healthCheck } from "./api";
import "./App.css";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [mode, setMode] = useState<ChatMode>("chat");
  const [activePanel, setActivePanel] = useState<string>("chat");
  const [serverOnline, setServerOnline] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    healthCheck().then(setServerOnline);
  }, []);

  const addMessage = (msg: Message) => {
    setMessages((prev) => [...prev, msg]);
  };

  const updateLastAssistant = (content: string) => {
    setMessages((prev) => {
      const updated = [...prev];
      const lastIdx = updated.length - 1;
      if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
        updated[lastIdx] = { ...updated[lastIdx], content };
      }
      return updated;
    });
  };

  return (
    <div className="app-container">
      <Sidebar
        activePanel={activePanel}
        onPanelChange={setActivePanel}
        serverOnline={serverOnline}
        sessionId={sessionId}
      />
      <main className="main-content">
        {activePanel === "chat" && (
          <ChatWindow
            messages={messages}
            mode={mode}
            onModeChange={setMode}
            onAddMessage={addMessage}
            onUpdateAssistant={updateLastAssistant}
            sessionId={sessionId}
            onSessionChange={setSessionId}
          />
        )}
        {activePanel === "agent" && (
          <AgentPanel messages={messages} onAddMessage={addMessage} />
        )}
        {activePanel === "memory" && <MemoryPanel />}
      </main>
    </div>
  );
}

export default App;
