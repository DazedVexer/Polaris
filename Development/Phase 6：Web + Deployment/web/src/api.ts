import { AgentTaskResult, MemoryItem, ToolInfo } from "./types";

const API_BASE = "http://localhost:8000";

export async function sendMessage(message: string, mode: "chat" | "agent"): Promise<string> {
  const resp = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode }),
  });
  const data = await resp.json();
  return data.reply;
}

export function streamChat(
  message: string,
  mode: "chat" | "agent",
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode }),
    signal: controller.signal,
  })
    .then(async (resp) => {
      const reader = resp.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.text) onChunk(parsed.text);
              if (parsed.error) onError(parsed.error);
            } catch {
              // 忽略解析错误
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError(err.message);
    });

  return controller;
}

export async function runAgent(instruction: string): Promise<AgentTaskResult> {
  const resp = await fetch(`${API_BASE}/api/chat/agent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction }),
  });
  return resp.json();
}

export async function fetchMemories(): Promise<MemoryItem[]> {
  const resp = await fetch(`${API_BASE}/api/memory?limit=50`);
  const data = await resp.json();
  return data.memories;
}

export async function fetchTools(): Promise<ToolInfo[]> {
  const resp = await fetch(`${API_BASE}/api/tools`);
  const data = await resp.json();
  return data.tools;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const resp = await fetch(`${API_BASE}/health`);
    return resp.ok;
  } catch {
    return false;
  }
}
