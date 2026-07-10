import { Message } from "../types";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  return (
    <div className={`message-bubble ${message.role} ${message.isStreaming ? "streaming" : ""}`}>
      <div className="content">{message.content || (message.isStreaming ? "..." : "")}</div>
      <div className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</div>
    </div>
  );
}
