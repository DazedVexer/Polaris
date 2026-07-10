import { useState, useRef, useEffect } from "react";
import { ChatMode, Message } from "../types";
import { streamChat } from "../api";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: Message[];
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  onAddMessage: (msg: Message) => void;
  onUpdateAssistant: (content: string) => void;
  sessionId: string | null;
  onSessionChange: (id: string) => void;
}

export default function ChatWindow({
  messages,
  mode,
  onModeChange,
  onAddMessage,
  onUpdateAssistant,
  sessionId,
}: Props) {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };
    onAddMessage(userMsg);
    setInput("");
    setIsStreaming(true);

    // 添加一个空的 assistant 消息占位
    const assistantId = (Date.now() + 1).toString();
    onAddMessage({
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      isStreaming: true,
    });

    let fullContent = "";

    abortRef.current = streamChat(
      userMsg.content,
      mode,
      (chunk) => {
        fullContent += chunk;
        onUpdateAssistant(fullContent);
      },
      () => {
        setIsStreaming(false);
        onUpdateAssistant(fullContent);
      },
      (err) => {
        onUpdateAssistant(`[错误] ${err}`);
        setIsStreaming(false);
      },
    );
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
  };

  return (
    <div className="chat-window">
      {/* 模式切换 */}
      <div className="mode-toggle">
        <button
          className={mode === "chat" ? "active" : ""}
          onClick={() => onModeChange("chat")}
        >
          💬 对话
        </button>
        <button
          className={mode === "agent" ? "active" : ""}
          onClick={() => onModeChange("agent")}
        >
          🤖 Agent
        </button>
      </div>

      {/* 消息列表 */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>Polaris</h2>
            <p>你的个人 AI 执行助理。有什么我可以帮你的？</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* 输入区 */}
      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder={mode === "agent" ? "输入 Agent 任务指令..." : "输入消息..."}
          rows={2}
          disabled={isStreaming}
        />
        <div className="input-actions">
          {isStreaming ? (
            <button onClick={stopStreaming} className="btn-stop">
              ⏹ 停止
            </button>
          ) : (
            <button onClick={sendMessage} className="btn-send" disabled={!input.trim()}>
              发送
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
