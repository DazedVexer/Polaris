// ====== 消息 ======
export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

// ====== 对话模式 ======
export type ChatMode = "chat" | "agent";

// ====== Agent 任务 ======
export interface AgentStep {
  step: number;
  action: string;
  result: string;
  status: "ok" | "error" | "stopped";
}

export interface AgentTaskResult {
  task_id: string;
  success: boolean;
  summary: string;
  steps: AgentStep[];
}

// ====== 记忆 ======
export interface MemoryItem {
  id: number;
  content: string;
  category: string;
  importance: string;
  created_at: string;
}

// ====== 工具 ======
export interface ToolInfo {
  name: string;
  description: string;
}
