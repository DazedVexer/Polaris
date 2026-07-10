import { useState } from "react";
import { Message } from "../types";
import { runAgent } from "../api";

interface Props {
  messages: Message[];
  onAddMessage: (msg: Message) => void;
}

export default function AgentPanel({ onAddMessage }: Props) {
  const [instruction, setInstruction] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState("");

  const executeTask = async () => {
    if (!instruction.trim() || running) return;

    setRunning(true);
    setResult("正在执行 Agent 任务...");

    try {
      const taskResult = await runAgent(instruction);
      const summary = taskResult.summary;

      onAddMessage({
        id: Date.now().toString(),
        role: "user",
        content: `[Agent 任务] ${instruction}`,
        timestamp: new Date().toISOString(),
      });
      onAddMessage({
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: summary,
        timestamp: new Date().toISOString(),
      });

      setResult(summary);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "未知错误";
      setResult(`[错误] ${msg}`);
    } finally {
      setRunning(false);
      setInstruction("");
    }
  };

  return (
    <div className="agent-panel">
      <h3>🤖 Agent 任务执行</h3>
      <div className="agent-input-area">
        <input
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") executeTask();
          }}
          placeholder="输入复杂的多步任务指令..."
          disabled={running}
        />
        <button onClick={executeTask} disabled={running || !instruction.trim()}>
          {running ? "执行中..." : "执行"}
        </button>
      </div>
      {result && (
        <div className="message-bubble assistant">
          <div style={{ whiteSpace: "pre-wrap" }}>{result}</div>
        </div>
      )}
    </div>
  );
}
